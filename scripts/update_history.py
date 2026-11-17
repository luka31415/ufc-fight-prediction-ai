"""Incrementally refresh UFCStats history with validated completed events."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

RESULT_COLUMNS = ["EVENT", "BOUT", "OUTCOME", "WEIGHTCLASS", "METHOD", "ROUND", "TIME", "TIME FORMAT", "REFEREE", "DETAILS", "URL"]
TOTAL_COLUMNS = ["ROUND", "FIGHTER", "KD", "SIG.STR.", "SIG.STR. %", "TOTAL STR.", "TD", "TD %", "SUB.ATT", "REV.", "CTRL"]
SIGNIFICANT_COLUMNS = ["ROUND", "FIGHTER", "SIG.STR.", "SIG.STR. %", "HEAD", "BODY", "LEG", "DISTANCE", "CLINCH", "GROUND"]
BIO_COLUMNS = ["FIGHTER", "HEIGHT", "WEIGHT", "REACH", "STANCE", "DOB", "URL"]
CORE_STATS = ["KD", "SIG_STR_LANDED", "SIG_STR_ATT", "TOTAL_STR_LANDED", "TOTAL_STR_ATT", "TD_LANDED", "TD_ATT", "SUB.ATT", "CTRL_SECONDS"]


def regular_ufc(name):
    text = str(name).strip()
    return text.startswith(("UFC", "Noche UFC")) and not any(term in text.casefold() for term in ["contender", "road to"])


def name_key(value):
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", text.casefold())


def match_keys(frame):
    return pd.Series([
        f"{pd.Timestamp(d).date()}|{'|'.join(sorted([name_key(a), name_key(b)]))}"
        for d, a, b in zip(frame.DATE, frame.FIGHTER_A, frame.FIGHTER_B)
    ], index=frame.index)


def history_keys(frame):
    return pd.Series([
        f"{pd.Timestamp(d).date()}|{'|'.join(sorted([name_key(a), name_key(b)]))}"
        for d, a, b in zip(frame.DATE, frame.FIGHTER, frame.OPPONENT)
    ], index=frame.index)


def parse_index(soup):
    events = []
    for row in soup.select("tr"):
        link = row.select_one('a[href*="/event-details/"]')
        day = row.select_one(".b-statistics__date")
        if not link or not day:
            continue
        name = link.get_text(" ", strip=True)
        if not regular_ufc(name):
            continue
        events.append({"EVENT": name, "DATE": pd.to_datetime(day.get_text(strip=True)), "URL": link["href"]})
    if not events:
        raise ValueError("No UFC events found in UFCStats index; data was not changed")
    return pd.DataFrame(events).drop_duplicates("URL")


def aggregate_stats(raw):
    frame = raw.copy()
    for source, target in [("SIG.STR.", "SIG_STR"), ("TOTAL STR.", "TOTAL_STR"), ("TD", "TD"),
                           ("HEAD", "HEAD"), ("BODY", "BODY"), ("LEG", "LEG"),
                           ("DISTANCE", "DISTANCE"), ("CLINCH", "CLINCH"), ("GROUND", "GROUND")]:
        values = frame[source].astype(str).str.extract(r"^(\d+)\s+of\s+(\d+)$")
        if values.isna().any().any():
            raise ValueError(f"Missing or malformed completed-fight statistic: {source}")
        frame[target + "_LANDED"] = pd.to_numeric(values[0])
        frame[target + "_ATT"] = pd.to_numeric(values[1])
        if (frame[target + "_LANDED"] > frame[target + "_ATT"]).any():
            raise ValueError(f"Landed exceeds attempted: {source}")
    for col in ["KD", "SUB.ATT", "REV."]:
        frame[col] = pd.to_numeric(frame[col], errors="raise")
    def clock(value):
        value = str(value).strip()
        if value == "---":
            return 0
        if not re.fullmatch(r"\d+:\d{2}", value):
            raise ValueError(f"Malformed control clock: {value}")
        minutes, seconds = map(int, value.split(":"))
        if seconds >= 60:
            raise ValueError(f"Malformed control clock: {value}")
        return 60 * minutes + seconds
    frame["CTRL_SECONDS"] = frame.CTRL.map(clock)
    columns = [c for c in frame if c.endswith(("_LANDED", "_ATT"))] + ["KD", "SUB.ATT", "REV.", "CTRL_SECONDS"]
    return frame.groupby("FIGHTER", as_index=False)[columns].sum()


def convert_fight(result, stats, event_date, location, order):
    if len(result) != 1:
        raise ValueError("Expected one result per fight")
    row = result.iloc[0].to_dict()
    names = row["BOUT"].split(" vs. ")
    outcomes = str(row["OUTCOME"]).upper().split("/")
    if len(names) != 2 or len(outcomes) != 2 or any(x not in {"W", "L", "D", "NC"} for x in outcomes):
        raise ValueError("Unrecognized fighter/outcome format")
    if not re.fullmatch(r"\d+:\d{2}", str(row["TIME"]).strip()) or int(row["ROUND"]) < 1:
        raise ValueError("Missing completed-fight duration")
    row.update(DATE=pd.Timestamp(event_date).date().isoformat(), LOCATION=location,
               FIGHTER_A=names[0], FIGHTER_B=names[1], OUTCOME_A=outcomes[0], OUTCOME_B=outcomes[1],
               WINNER=names[0] if outcomes[0] == "W" else names[1] if outcomes[1] == "W" else None,
               EVENT_FIGHT_ORDER=order)
    totals = aggregate_stats(stats)
    if len(totals) != 2 or set(totals.FIGHTER.map(name_key)) != set(map(name_key, names)):
        raise ValueError("Expected statistics for exactly the two named fighters")
    histories = []
    for _, fighter in totals.iterrows():
        index = [name_key(n) for n in names].index(name_key(fighter.FIGHTER))
        record = fighter.to_dict()
        record.update(DATE=row["DATE"], OPPONENT=names[1-index], RESULT=outcomes[index],
                      EVENT_STATS=row["EVENT"], EVENT_RESULT=row["EVENT"], BOUT=row["BOUT"],
                      FIGHTER_A=names[0], FIGHTER_B=names[1], WINNER=row["WINNER"],
                      OUTCOME_A=outcomes[0], OUTCOME_B=outcomes[1], ROUND=row["ROUND"], TIME=row["TIME"],
                      METHOD=row["METHOD"], WEIGHTCLASS=row["WEIGHTCLASS"], SOURCE_URL=row["URL"])
        histories.append(record)
    return row, histories


def validate_rows(results, history):
    """Require one result and both opposing fighter records per incoming bout."""
    for frame, left, right in [(results, "FIGHTER_A", "FIGHTER_B"), (history, "FIGHTER", "OPPONENT")]:
        if frame[[left, right, "DATE"]].isna().any().any():
            raise ValueError("Missing fighter or date")
        a, b = frame[left].map(name_key), frame[right].map(name_key)
        if (a.eq("") | b.eq("") | a.eq(b)).any():
            raise ValueError("Invalid fighter pair")
    keys = match_keys(results)
    if keys.duplicated().any():
        raise ValueError("Duplicate incoming fight keys")
    directions = pd.DataFrame({"key": history_keys(history), "fighter": history.FIGHTER.map(name_key)})
    if (set(keys) != set(directions.key) or directions.duplicated().any()
            or not directions.key.value_counts().eq(2).all()):
        raise ValueError("Expected two opposing history rows for each result")
    if history[CORE_STATS].isna().any().any():
        raise ValueError("Missing required statistics")


def merge_new(old_results, old_history, result_rows, history_rows):
    if not result_rows:
        return old_results, old_history
    added = pd.DataFrame(result_rows)
    added_history = pd.DataFrame(history_rows)
    validate_rows(added, added_history)
    keys = match_keys(added)
    replace = set(keys)
    old_keys = match_keys(old_results)
    if "URL" in old_results and "URL" in added:
        touched = old_results.loc[old_keys.isin(replace)]
        identity_columns = ["DATE", "FIGHTER_A", "FIGHTER_B", "URL"]
        identities = pd.concat([touched[identity_columns], added[identity_columns]], ignore_index=True)
        urls = identities.URL.fillna("").str.strip().str.rstrip("/")
        # Distinct fight IDs can represent a same-day rematch.
        ids = urls.str.rsplit("/", n=1).str[-1].replace("", pd.NA)
        if ids.groupby(match_keys(identities)).nunique().gt(1).any():
            raise ValueError("Distinct fight IDs share a date and fighter pair")
    results = pd.concat([old_results.loc[~old_keys.isin(replace)], added], ignore_index=True)
    history = pd.concat([old_history.loc[~history_keys(old_history).isin(replace)], added_history], ignore_index=True)
    results.DATE = pd.to_datetime(results.DATE)
    history.DATE = pd.to_datetime(history.DATE)
    results = results.sort_values(["DATE", "EVENT"], kind="stable")
    history = history.sort_values(["DATE", "FIGHTER"], kind="stable")
    return results, history


class Fetcher:
    def __init__(self, cache):
        self.cache = cache
        cache.mkdir(parents=True, exist_ok=True)
        self.last_request = 0.

    def soup(self, url, refresh=False):
        from bs4 import BeautifulSoup
        import requests
        if urlparse(url).hostname not in {"ufcstats.com", "www.ufcstats.com"}:
            raise ValueError("Unexpected statistics source host")
        path = self.cache / (hashlib.sha256(url.encode()).hexdigest() + ".html")
        if not path.is_file() or refresh:
            # At most one request per second; completed-fight HTML is reused.
            time.sleep(max(0., 1. - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            response = requests.get(url, timeout=30, headers={"User-Agent": "UFCResearchProject/1.0"})
            response.raise_for_status()
            html = response.text
            if "b-content" not in html:
                raise ValueError("UFCStats returned no usable page")
            path.write_text(html, encoding="utf-8")
        return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def commit_csvs(files, run):
    """Stage all outputs, back up originals, restore all originals on error."""
    backup = run / "backup"
    staging = run / "staging"
    backup.mkdir()
    staging.mkdir()
    for i, (target, frame) in enumerate(files):
        frame.to_csv(staging / str(i), index=False)
        pd.read_csv(staging / str(i), low_memory=False)  # ensure each staged CSV is readable
        shutil.copy2(target, backup / str(i))
    try:
        for i, (target, _) in enumerate(files):
            local = target.with_name(target.name + ".updating")
            shutil.copy2(staging / str(i), local)
            os.replace(local, target)
    except Exception:
        for i, (target, _) in enumerate(files):
            shutil.copy2(backup / str(i), target)
        raise
    (run / "backup_paths.json").write_text(json.dumps([str(p) for p, _ in files], indent=2), encoding="utf-8")


def load_mirror(cache):
    import requests
    repo = "Greco1899/scrape_ufc_stats"
    response = requests.get(f"https://api.github.com/repos/{repo}/commits/main", timeout=30)
    response.raise_for_status()
    sha = response.json()["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Invalid source commit")
    cache = cache / sha
    cache.mkdir(parents=True, exist_ok=True)
    frames, sources = {}, []
    for name in ["ufc_event_details.csv", "ufc_fight_results.csv", "ufc_fight_stats.csv", "ufc_fighter_tott.csv"]:
        url = f"https://raw.githubusercontent.com/{repo}/{sha}/{name}"
        target = cache / name
        if not target.is_file():
            print(f"Downloading {name}", flush=True)
            data = requests.get(url, timeout=60)
            data.raise_for_status()
            target.write_bytes(data.content)
        frames[name] = pd.read_csv(target)
        sources.append({"name": name, "url": url, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    return frames, {"repository": repo, "commit": sha, "files": sources}


def mirror_rows(frames, since, today, known_keys, history_counts):
    events = frames["ufc_event_details.csv"].copy()
    events.DATE = pd.to_datetime(events.DATE, errors="raise")
    events = events.loc[(events.DATE >= since.normalize()) & (events.DATE < today)]
    events = events.loc[events.EVENT.map(regular_ufc)]
    events = events.drop_duplicates(["EVENT", "DATE"]).sort_values("DATE")
    if events.empty:
        raise ValueError("Mirror has no completed events in the requested period")
    all_results = frames["ufc_fight_results.csv"].copy()
    all_stats = frames["ufc_fight_stats.csv"].copy()
    for f in [all_results, all_stats]:
        f.EVENT = f.EVENT.astype(str).str.strip()
        f.BOUT = f.BOUT.astype(str).str.strip()
    rows, histories, audit = [], [], []
    for _, event in events.iterrows():
        result = all_results.loc[all_results.EVENT == str(event.EVENT).strip()]
        if result.empty or result.BOUT.duplicated().any():
            raise ValueError(f"Missing or duplicate results in mirror: {event.EVENT}")
        print(f"Checking {event.DATE.date()} — {event.EVENT} ({len(result)} fights)", flush=True)
        for order, (_, fight) in enumerate(result.iloc[::-1].iterrows(), 1):
            stats = all_stats.loc[(all_stats.EVENT == fight.EVENT) & (all_stats.BOUT == fight.BOUT)].copy()
            if stats.empty or stats.duplicated(["FIGHTER", "ROUND"]).any():
                raise ValueError(f"Missing or duplicated round statistics: {fight.BOUT}")
            row, hs = convert_fight(pd.DataFrame([fight]), stats, event.DATE, event.get("LOCATION", ""), order)
            key = match_keys(pd.DataFrame([row])).iloc[0]
            state = "ALREADY_PRESENT"
            if key not in known_keys or history_counts.get(key, 0) != 2:
                rows.append(row)
                histories.extend(hs)
                state = "ADDED_OR_REPAIRED"
            audit.append({"DATE": row["DATE"], "EVENT": row["EVENT"], "BOUT": row["BOUT"], "URL": row.get("URL", ""), "STATUS": state})
    names = {name_key(n) for row in audit for n in row["BOUT"].split(" vs. ")}
    bio = frames["ufc_fighter_tott.csv"]
    bio = bio.loc[bio.FIGHTER.map(name_key).isin(names)]
    ambiguous = bio.FIGHTER.map(name_key).duplicated(keep=False)
    if ambiguous.any():
        print("Biographies skipped for ambiguous names: " + ", ".join(bio.loc[ambiguous, "FIGHTER"].unique()), flush=True)
        bio = bio.loc[~ambiguous]
    return events, rows, histories, audit, bio.to_dict("records")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--since", type=pd.Timestamp, help="Optional earlier date for repairing missing recent events")
    parser.add_argument("--source", choices=["bundled", "mirror", "ufcstats"], default="bundled")
    parser.add_argument("--snapshot-dir", type=Path, help="Directory containing the extracted update snapshot")
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    lock = root / "data/.history-update.lock"
    with lock.open("x") as handle:
        handle.write(str(os.getpid()))
    try:
        return update(args, root)
    finally:
        lock.unlink()


def update(args, root):
    paths = [root / "data/fight_results_clean.csv", root / "data/fighter_history.csv"]
    old_results, old_history = [pd.read_csv(p, low_memory=False) for p in paths]
    cutoff = pd.to_datetime(old_results.DATE, errors="raise").max()
    since = args.since if args.since is not None else cutoff
    today = pd.Timestamp(datetime.now(timezone.utc).date())
    if pd.isna(since) or since >= today:
        raise ValueError("No earlier historical date available to refresh")
    run = root / "reports/history_updates" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    run.mkdir(parents=True, exist_ok=False)
    result_counts = match_keys(old_results).value_counts()
    known_keys = set(result_counts[result_counts == 1].index)
    history_counts = history_keys(old_history).value_counts()
    directions = pd.DataFrame({"key": history_keys(old_history), "fighter": old_history.FIGHTER.map(name_key)})
    distinct = directions.groupby("key").fighter.nunique()
    history_counts = history_counts.where(distinct.eq(2), 0)
    provenance = {}
    if args.source == "bundled":
        if since.normalize() < pd.Timestamp("2026-08-29"):
            raise ValueError("Bundled update starts after 2026-08-29. Use --source mirror for an older history.")
        snapshot = args.snapshot_dir or root / "UFC_Update_v2/snapshot"
        provenance = json.loads((snapshot / "provenance.json").read_text(encoding="utf-8"))
        for name in ("new_fight_results.csv", "new_fighter_history.csv", "new_fighter_bios.csv", "source_audit.csv"):
            expected = provenance["files"][name]
            if hashlib.sha256((snapshot / name).read_bytes()).hexdigest() != expected:
                raise ValueError(f"Bundled snapshot checksum mismatch: {name}")
        added = pd.read_csv(snapshot / "new_fight_results.csv")
        new_history = pd.read_csv(snapshot / "new_fighter_history.csv")
        validate_rows(added, new_history)
        added.DATE = pd.to_datetime(added.DATE)
        added = added.loc[(added.DATE >= since.normalize()) & (added.DATE < today)]
        if added.empty:
            raise ValueError("Bundled snapshot ends on 2026-10-03. Use --source mirror for newer data.")
        all_keys = match_keys(added)
        needed = all_keys.map(lambda k: k not in known_keys or history_counts.get(k, 0) != 2)
        selected = added.loc[needed]
        rows = selected.to_dict("records")
        histories = new_history.loc[history_keys(new_history).isin(set(match_keys(selected)))].to_dict("records")
        events = added[["EVENT", "DATE"]].drop_duplicates()
        audit = added[["DATE", "EVENT", "BOUT", "URL"]].copy()
        audit["STATUS"] = ["ADDED_OR_REPAIRED" if value else "ALREADY_PRESENT" for value in needed]
        audit = audit.to_dict("records")
        bios = pd.read_csv(snapshot / "new_fighter_bios.csv").to_dict("records")
    elif args.source == "mirror":
        frames, provenance = load_mirror(root / "data/ufcstats_mirror_cache")
        events, rows, histories, audit, bios = mirror_rows(frames, since, today, known_keys, history_counts)
    else:
        events, rows, histories, audit, bios = scrape_direct(root, since, today, known_keys, history_counts)
    pd.DataFrame(audit).to_csv(run / "fight_audit.csv", index=False)
    results, history = merge_new(old_results, old_history, rows, histories)
    files = list(zip(paths, [results, history])) if rows else []
    candidates = [root / "data/ufc_fighter_tott.csv", root / "scrape_ufc_stats/ufc_fighter_tott.csv", root / "scrape_ufc_stats/data/ufc_fighter_tott.csv", root / "external/scrape_ufc_stats/ufc_fighter_tott.csv"]
    bio_path = next((p for p in candidates if p.is_file()), None)
    changed_bios = 0
    if bios and bio_path is not None:
        old_bio = pd.read_csv(bio_path)
        incoming = pd.DataFrame(bios)
        bio_keys = incoming.FIGHTER.map(name_key)
        if bio_keys.duplicated().any():
            raise ValueError("Duplicate incoming fighter biographies")
        old_keys = old_bio.FIGHTER.map(name_key)
        # Multiple existing profiles can represent different people sharing a name.
        ambiguous = set(old_keys[old_keys.duplicated(keep=False)])
        incoming = incoming.loc[~bio_keys.isin(ambiguous)]
        current = old_bio.loc[~old_keys.isin(ambiguous)].set_index(
            old_keys.loc[~old_keys.isin(ambiguous)])
        changes = []
        for _, row in incoming.iterrows():
            key = name_key(row.FIGHTER)
            if key not in current.index or not row.fillna("").equals(
                    current.loc[key].reindex(row.index).fillna("")):
                changes.append(row)
        changed_bios = len(changes)
        if changes:
            changed = pd.DataFrame(changes)
            keep = ~old_keys.isin(changed.FIGHTER.map(name_key))
            files.append((bio_path, pd.concat([old_bio.loc[keep], changed], ignore_index=True)))
    if files:
        commit_csvs(files, run)
    metadata = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "previous_cutoff": str(cutoff.date()),
                "new_cutoff": str(pd.to_datetime(results.DATE).max().date()), "completed_events_checked": len(events),
                "new_or_repaired_fights": len(rows), "new_history_rows": len(histories), "retrained": False,
                "scope": "Regular completed UFC events only; event day strictly before current UTC date",
                "biographies_updated": changed_bios, "provenance": provenance,
                "not_updated": ["training_data_with_sos.csv", "model weights", "prior prediction snapshots"]}
    (run / "update.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    print(f"Backups and audit: {run}")


def scrape_direct(root, since, today, known_keys, history_counts):
    fetch = Fetcher(root / "data/ufcstats_update_cache")
    parser_paths = [root / directory / "scrape_ufc_stats_library.py"
                    for directory in ("external/scrape_ufc_stats", "scrape_ufc_stats", "UFC_Update_v2/vendor")]
    parser_path = next((p for p in parser_paths if p.is_file()), None)
    if parser_path is None:
        raise FileNotFoundError("Install the upstream scraper under external/scrape_ufc_stats or use --source mirror")
    spec = importlib.util.spec_from_file_location("ufcstats_parser", parser_path)
    lib = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lib)
    try:
        soup = fetch.soup("http://ufcstats.com/statistics/events/completed?page=all", refresh=True)
    except Exception:
        soup = fetch.soup("https://ufcstats.com/statistics/events/completed?page=all", refresh=True)
    events = parse_index(soup)
    events = events.loc[(events.DATE >= since.normalize()) & (events.DATE < today)].sort_values("DATE")
    if events.empty:
        raise ValueError("No completed events in requested period; not declaring an update")
    rows, histories, audit, bios = [], [], [], []
    for _, event in events.iterrows():
        page = fetch.soup(event.URL)
        links = list(dict.fromkeys(a["href"] for a in page.select('a[href*="/fight-details/"]')))
        if not links:
            links = list(dict.fromkeys(t["data-link"] for t in page.select('tr[data-link]') if "/fight-details/" in t["data-link"]))
        if not links:
            raise ValueError(f"No completed fights found: {event.EVENT}")
        print(f"Reading {event.DATE.date()} — {event.EVENT} ({len(links)} fights)", flush=True)
        for order, url in enumerate(reversed(links), 1):
            fight = fetch.soup(url)
            result, raw_stats = lib.parse_organise_fight_results_and_stats(fight, url, RESULT_COLUMNS, TOTAL_COLUMNS, SIGNIFICANT_COLUMNS)
            row, history_rows = convert_fight(result, raw_stats, event.DATE, "", order)
            key = match_keys(pd.DataFrame([row])).iloc[0]
            state = "ALREADY_PRESENT"
            if key not in known_keys or history_counts.get(key, 0) != 2:
                rows.append(row)
                histories.extend(history_rows)
                state = "ADDED_OR_REPAIRED"
            audit.append({"DATE": row["DATE"], "EVENT": row["EVENT"], "BOUT": row["BOUT"], "URL": url, "STATUS": state})
            for link in fight.select('a[href*="/fighter-details/"]'):
                profile_url = link["href"]
                if any(b["URL"] == profile_url for b in bios):
                    continue
                bio = lib.organise_fighter_tott(lib.parse_fighter_tott(fetch.soup(profile_url)), BIO_COLUMNS, profile_url)
                if len(bio) != 1 or not bio.FIGHTER.iloc[0]:
                    raise ValueError("Malformed fighter biography")
                bios.append(bio.iloc[0].to_dict())
    return events, rows, histories, audit, bios


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
