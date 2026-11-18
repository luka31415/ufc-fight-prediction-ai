"""ESPN moneylines matched by athlete ID, always one provider per matchup."""
from __future__ import annotations
import json
import math
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

CORE = "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc"


def get_json(url):
    if urlparse(url).hostname not in {"sports.core.api.espn.com", "site.api.espn.com"}:
        raise ValueError("Unexpected odds host")
    url = re.sub(r"^http:", "https:", url)
    with urlopen(Request(url, headers={"User-Agent": "UFCResearchProject/1.0"}), timeout=25) as response:
        return json.load(response)


def athlete_id(obj):
    if obj.get("id") is not None:
        return str(obj["id"])
    match = re.search(r"/athletes/(\d+)", obj.get("$ref", ""))
    return match.group(1) if match else None


def parse_quote(item, a_id, b_id):
    """Never infer red/blue/home/away ordering from array position."""
    if str(a_id) == str(b_id) or a_id is None or b_id is None:
        raise ValueError("Expected two distinct athlete IDs")
    prices = {}
    for field in ["homeAthleteOdds", "awayAthleteOdds"]:
        side = item.get(field, {})
        ident = athlete_id(side.get("athlete", {}))
        value = side.get("current", {}).get("moneyLine", {}).get("american")
        if value is None:
            value = side.get("moneyLine")
        if ident is None or value is None:
            continue
        number = float(value)
        if not math.isfinite(number) or abs(number) < 100:
            raise ValueError("Invalid current Moneyline")
        if ident in prices:
            raise ValueError("Duplicate athlete ID in quote")
        prices[ident] = number
    if str(a_id) not in prices or str(b_id) not in prices:
        return None
    return prices[str(a_id)], prices[str(b_id)]


def fetch_odds(cards):
    import pandas as pd
    def one(row):
        base = {c: str(row[c]) for c in ["EVENT_ID", "FIGHT_ID", "FIGHTER_A", "FIGHTER_B"]}
        url = f"{CORE}/events/{row.EVENT_ID}/competitions/{row.FIGHT_ID}/odds?lang=en&region=us"
        start = pd.to_datetime(row.EVENT_START_UTC, utc=True, errors="coerce")
        if pd.isna(start):
            return None, {**base, "STATUS": "INVALID_EVENT_START"}
        stamp = datetime.now(timezone.utc)
        if stamp >= start.to_pydatetime():
            return None, {**base, "STATUS": "EVENT_ALREADY_STARTED"}
        try:
            payload = get_json(url)
            choices = payload.get("items", [])
            choices = sorted(choices, key=lambda x: (x.get("provider", {}).get("priority", 999), str(x.get("provider", {}).get("id", ""))))
            for item in choices:
                if item.get("$ref") and not any(k in item for k in ["homeAthleteOdds", "awayAthleteOdds"]):
                    item = get_json(item["$ref"])
                try:
                    pair = parse_quote(item, row.A_ESPN_ID, row.B_ESPN_ID)
                except (ValueError, TypeError, AttributeError):
                    continue
                if pair is None:
                    continue
                observed = datetime.now(timezone.utc)
                if observed >= start.to_pydatetime():
                    return None, {**base, "STATUS": "EVENT_STARTED_DURING_REQUEST"}
                quote = {**base, "A_ODDS": pair[0], "B_ODDS": pair[1], "ODDS_AS_OF_UTC": observed.isoformat(),
                         "PROVIDER": item.get("provider", {}).get("name", "UNKNOWN"), "SOURCE_URL": url}
                return quote, {**base, "STATUS": "ODDS_FOUND", "PROVIDER": quote["PROVIDER"]}
            return None, {**base, "STATUS": "NO_MATCHED_CURRENT_MONEYLINES"}
        except (HTTPError, URLError, ValueError, TypeError, OSError) as exc:
            return None, {**base, "STATUS": "UNAVAILABLE: " + str(exc)}
    if cards.duplicated(["EVENT_ID", "FIGHT_ID"]).any():
        raise ValueError("Duplicate fight IDs in cards")
    # A series is needed for both keyed and attribute access in one().
    with ThreadPoolExecutor(max_workers=4) as pool:
        result = list(pool.map(one, [row for _, row in cards.iterrows()]))
    quotes = [quote for quote, _ in result if quote is not None]
    columns = ["EVENT_ID", "FIGHT_ID", "FIGHTER_A", "FIGHTER_B", "A_ODDS", "B_ODDS", "ODDS_AS_OF_UTC", "PROVIDER", "SOURCE_URL"]
    return pd.DataFrame(quotes, columns=columns), pd.DataFrame([audit for _, audit in result])
