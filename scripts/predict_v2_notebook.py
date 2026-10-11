"""V2 notebook prediction runner. Uses local saved models; never retrains them.
Fetches current scheduled UFC cards and optionally current ESPN moneylines.
Feature formulas come from the original 42-feature live builder.
"""
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
import json, math, re, hashlib, warnings, unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import numpy as np
import pandas as pd
import joblib
from catboost import CatBoostClassifier
API = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc"

def regular_ufc(name):
    return str(name).strip().startswith(("UFC", "Noche UFC")) and not any(term in str(name).casefold() for term in ["contender", "road to"])

def api_json(path, **params):
    request = Request(f"{API}/{path}?{urlencode(params)}", headers={"User-Agent": "UFCResearchProject/1.0"})
    with urlopen(request, timeout=45) as response:
        return json.load(response)

def parse_event(event, now):
    """Accept only explicitly scheduled, not started fightcards."""
    if not regular_ufc(event.get("name", "")):
        return []
    stamp = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError(f"Missing timezone for event {event.get('id')}")
    status = event.get("status", {}).get("type", {})
    if status.get("completed") or status.get("state") == "in" or stamp <= now or any(
        term in str(status.get("name", "")).upper() for term in ["CANCEL", "POSTPON"]
    ):
        return []
    rows = []
    for fight in event.get("competitions", []):
        fight_status = fight.get("status", {}).get("type", {})
        if fight_status.get("completed") or any(
            term in str(fight_status.get("name", "")).upper() for term in ["CANCEL", "POSTPON"]
        ):
            continue
        competitors = fight.get("competitors", [])
        if len(competitors) != 2:
            continue
        names = [c.get("athlete", {}).get("displayName", "").strip() for c in competitors]
        if not all(names) or any(n.upper() in {"TBD", "TBA", "TBC"} for n in names):
            continue
        rows.append({
            "DATE": stamp.date().isoformat(),
            "EVENT": event.get("name", event.get("shortName", event["id"])),
            "EVENT_ID": str(event["id"]),
            "FIGHT_ID": str(fight["id"]),
            "EVENT_START_UTC": stamp.isoformat(),
            "FIGHTER_A": names[0], "FIGHTER_B": names[1],
            "A_ESPN_ID": str(competitors[0]["id"]), "B_ESPN_ID": str(competitors[1]["id"]),
            "SOURCE_URL": f"https://www.espn.com/mma/fightcenter/_/id/{event['id']}",
        })
    return rows

def fetch_cards(start, end):
    events = {}
    cursor = start
    while cursor <= end:
        last = min(cursor + timedelta(days=27), end)
        payload = api_json("scoreboard", dates=f"{cursor:%Y%m%d}-{last:%Y%m%d}", limit=1000)
        if "events" not in payload:
            raise RuntimeError("ESPN response has no events field; cannot verify coverage.")
        for event in payload["events"]:
            if not isinstance(event, dict) or not event.get("id") or not event.get("date"):
                raise RuntimeError("Unexpected event schema; refusing incomplete output.")
            events[str(event["id"])] = event
        cursor = last + timedelta(days=1)
    now = datetime.now(timezone.utc)
    rows, coverage = [], []
    for event in sorted(events.values(), key=lambda e: e["date"]):
        if not regular_ufc(event.get("name", "")):
            continue
        if datetime.fromisoformat(event["date"].replace("Z", "+00:00")) <= now:
            continue
        # ESPN's MMA summary endpoint returns 404. The scoreboard enumerates fights.
        state = "SCOREBOARD_MATCHUPS; completeness not independently confirmed"
        card = parse_event(event, now)
        rows.extend(card)
        coverage.append({"EVENT_ID": str(event["id"]), "EVENT": event.get("name"),
                         "DATE": event["date"], "FIGHTS_FOUND": len(card), "STATUS": state})
    if not rows:
        raise RuntimeError("No scheduled matchups found. No predictions were created.")
    return rows, coverage

def decimal_odds(value, fmt):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Odds must be finite")
    if fmt == "decimal":
        if number <= 1:
            raise ValueError("Decimal odds must exceed 1")
        return number
    if abs(number) < 100:
        raise ValueError("American odds must be >= +100 or <= -100")
    return 1 + (number / 100 if number > 0 else 100 / abs(number))

def add_odds(live, path, fmt, bankroll):
    import numpy as np
    import pandas as pd
    live = live.copy()
    live["A_ODDS"] = np.nan
    live["B_ODDS"] = np.nan
    if path:
        odds = pd.read_csv(path, dtype={"EVENT_ID": str, "FIGHT_ID": str})
        required = ["EVENT_ID", "FIGHT_ID", "FIGHTER_A", "FIGHTER_B", "A_ODDS", "B_ODDS", "ODDS_AS_OF_UTC"]
        if any(c not in odds for c in required):
            raise ValueError("Odds CSV needs: " + ", ".join(required))
        if odds.duplicated(["EVENT_ID", "FIGHT_ID"]).any():
            raise ValueError("Duplicate fight IDs in odds CSV")
        by_id = odds.set_index(["EVENT_ID", "FIGHT_ID"])
        for i, row in live.iterrows():
            key = str(row.EVENT_ID), str(row.FIGHT_ID)
            if key not in by_id.index:
                continue
            quote = by_id.loc[key]
            if (row.FIGHTER_A, row.FIGHTER_B) != (quote.FIGHTER_A, quote.FIGHTER_B):
                raise ValueError(f"Fighter order changed for {key}; check the odds manually.")
            if pd.isna(quote.A_ODDS) and pd.isna(quote.B_ODDS):
                continue
            quote_time = pd.to_datetime(quote.ODDS_AS_OF_UTC, utc=True, errors="raise")
            if pd.isna(quote_time) or quote_time >= pd.Timestamp(row.EVENT_START_UTC):
                raise ValueError(f"Odds timestamp must precede event start: {key}")
            if quote_time > pd.Timestamp.now(tz="UTC"):
                raise ValueError(f"Future odds timestamp: {key}")
            for side in ["A", "B"]:
                if not pd.isna(quote[f"{side}_ODDS"]):
                    live.loc[i, f"{side}_ODDS"] = decimal_odds(quote[f"{side}_ODDS"], fmt)
            live.loc[i, "ODDS_AS_OF_UTC"] = quote_time.isoformat()
            for col in ["PROVIDER", "SOURCE_URL"]:
                if col in quote:
                    live.loc[i, "ODDS_" + col] = quote[col]
    live["PICK_ODDS_DECIMAL"] = np.where(live.P_A >= .5, live.A_ODDS, live.B_ODDS)
    live["MODEL_EV"] = live.PICK_PROB * live.PICK_ODDS_DECIMAL - 1
    live["ACTION"] = "NO BET"
    live.loc[live.PICK_ODDS_DECIMAL.isna(), "ACTION"] = "NO ODDS"
    eligible = (live.PICK_PROB >= .60) & (live.MODEL_EV >= .10)
    live.loc[eligible & (live.DATA_QUALITY != "NORMAL"), "ACTION"] = "BET — REVIEW DATA"
    live.loc[eligible & (live.DATA_QUALITY == "NORMAL"), "ACTION"] = "BET"
    fraction = (.25 * live.MODEL_EV / (live.PICK_ODDS_DECIMAL - 1)).clip(lower=0, upper=.03)
    live["SIM_STAKE"] = np.where(live.ACTION == "BET", fraction * bankroll, 0.)
    for _, group in live.groupby("EVENT_ID"):
        total = group.SIM_STAKE.sum()
        if total > .125 * bankroll:
            live.loc[group.index, "SIM_STAKE"] *= .125 * bankroll / total
    return live

def _build_base(ROOT, upcoming):
    # Extracted from your existing cell 122; feature formulas unchanged.
    import os
    import re
    import unicodedata
    from pathlib import Path
    import numpy as np
    import pandas as pd
    import joblib
    RANDOM_SEED = 42
    CAT_WEIGHT = 0.55
    LOG_WEIGHT = 0.45
    ELO_START = 1500.0
    ELO_K = 32.0
    
    def normalize_name(name):
        if pd.isna(name):
            return ''
        name = str(name).strip()
        name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
        name = name.casefold()
        name = re.sub('[^a-z0-9]+', ' ', name)
        return re.sub('\\s+', ' ', name).strip()
    RAW_ALIASES = {'Jose Miguel Delgado': 'Jose Delgado', 'Michael Aswell': 'Michael Aswell Jr.', 'Michael Venom Page': 'Michael Page', 'Waldo Cortes Acosta': 'Waldo Cortes-Acosta', 'Muhammadjon Naimov': 'Muhammad Naimov', 'Doo Ho Choi': 'Dooho Choi', 'Rongzhu': 'Rong Zhu', 'Joo Sang Yoo': 'JooSang Yoo', 'Osman Diaz': 'Ozzy Diaz', 'Weili Zhang': 'Zhang Weili', 'Cris Cyborg': 'Cristiane Justino', 'Ariane Lipski': 'Ariane da Silva', 'Lupita Godinez': 'Loopy Godinez', 'Josh Quinland': 'Josh Quinlan', 'Zhang Minyang': 'Zhang Mingyang', 'Zachary Reese': 'Zach Reese', 'Serghei Spivak': 'Serghei Spivac', 'Wuliji Buren': 'Wulijiburen', 'Bernardo Sopaj': 'Benardo Sopaj', 'Brianna Van Buren': 'Brianna Fortino'}
    ALIASES = {normalize_name(k): normalize_name(v) for k, v in RAW_ALIASES.items()}
    
    def fighter_key(name):
        key = normalize_name(name)
        return ALIASES.get(key, key)
    bio_candidates = [Path(str(ROOT / 'data/ufc_fighter_tott.csv')), Path(str(ROOT / 'scrape_ufc_stats/ufc_fighter_tott.csv')), Path(str(ROOT / 'scrape_ufc_stats/data/ufc_fighter_tott.csv'))]
    bio_path = None
    for candidate in bio_candidates:
        if candidate.exists():
            bio_path = candidate
            break
    if bio_path is None:
        matches = list(Path(ROOT).rglob('ufc_fighter_tott.csv'))
        if matches:
            bio_path = matches[0]
    if bio_path is None:
        raise FileNotFoundError('Could not find ufc_fighter_tott.csv')
    training = pd.read_csv(str(ROOT / 'data/training_data_with_sos.csv'), parse_dates=['DATE'])
    history = pd.read_csv(str(ROOT / 'data/fighter_history.csv'), parse_dates=['DATE'])
    results = pd.read_csv(str(ROOT / 'data/fight_results_clean.csv'), parse_dates=['DATE'])
    bio = pd.read_csv(bio_path)
    features = [c for c in training.columns if c.startswith('DIFF_')]
    if len(features) != 42:
        raise ValueError(f'Expected 42 DIFF features, found {len(features)}')
    BASE_FEATURES = [c.replace('DIFF_', '', 1) for c in features]
    
    def canonical_col(name):
        return re.sub('[^A-Z0-9]', '', str(name).upper())
    
    def find_column(df, candidates, required=False):
        lookup = {canonical_col(c): c for c in df.columns}
        for candidate in candidates:
            key = canonical_col(candidate)
            if key in lookup:
                return lookup[key]
        if required:
            raise KeyError('Could not find any of these columns: ' + str(candidates) + '\n\nAvailable columns:\n' + str(list(df.columns)))
        return None
    fighter_col = find_column(history, ['FIGHTER'], required=True)
    opponent_col = find_column(history, ['OPPONENT', 'OPP'], required=True)
    stat_candidates = {'KD': ['KD'], 'SIG_STR_LANDED': ['SIG_STR_LANDED', 'SIG.STR._LANDED', 'SIG STR LANDED'], 'SIG_STR_ATT': ['SIG_STR_ATT', 'SIG.STR._ATT', 'SIG STR ATT'], 'TOTAL_STR_LANDED': ['TOTAL_STR_LANDED', 'TOTAL.STR._LANDED', 'TOTAL STR LANDED'], 'TOTAL_STR_ATT': ['TOTAL_STR_ATT', 'TOTAL.STR._ATT', 'TOTAL STR ATT'], 'TD_LANDED': ['TD_LANDED', 'TD_L', 'TAKEDOWN_LANDED'], 'TD_ATT': ['TD_ATT', 'TD_A', 'TAKEDOWN_ATT'], 'SUB_ATT': ['SUB_ATT', 'SUB.ATT', 'SUB_ATTEMPTS'], 'CTRL_SECONDS': ['CTRL_SECONDS', 'CONTROL_SECONDS', 'CTRL_SEC']}
    stat_cols = {}
    for output_name, candidates in stat_candidates.items():
        stat_cols[output_name] = find_column(history, candidates, required=True)
    h = pd.DataFrame()
    h['DATE'] = pd.to_datetime(history['DATE'])
    h['FIGHTER'] = history[fighter_col].astype(str)
    h['OPPONENT'] = history[opponent_col].astype(str)
    h['FIGHTER_KEY'] = h['FIGHTER'].map(fighter_key)
    h['OPP_KEY'] = h['OPPONENT'].map(fighter_key)
    for output_name, source_col in stat_cols.items():
        h[output_name] = pd.to_numeric(history[source_col], errors='coerce')
    results['FIGHTER_A_KEY'] = results['FIGHTER_A'].map(fighter_key)
    results['FIGHTER_B_KEY'] = results['FIGHTER_B'].map(fighter_key)
    results['WINNER_KEY'] = results['WINNER'].map(fighter_key) if 'WINNER' in results.columns else ''
    
    def matchup_key(date, fighter_a, fighter_b):
        names = sorted([fighter_key(fighter_a), fighter_key(fighter_b)])
        return str(pd.Timestamp(date).date()) + '||' + names[0] + '||' + names[1]
    results['MATCH_KEY'] = [matchup_key(d, a, b) for d, a, b in zip(results['DATE'], results['FIGHTER_A'], results['FIGHTER_B'])]
    h['MATCH_KEY'] = [matchup_key(d, f, o) for d, f, o in zip(h['DATE'], h['FIGHTER'], h['OPPONENT'])]
    
    def parse_clock(value):
        if pd.isna(value):
            return np.nan
        text = str(value).strip()
        match = re.match('^(\\d+):(\\d+)$', text)
        if not match:
            return np.nan
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        return minutes * 60 + seconds
    results['ROUND_NUM'] = pd.to_numeric(results['ROUND'], errors='coerce')
    results['ROUND_TIME_SECONDS'] = results['TIME'].map(parse_clock)
    results['DURATION_SECONDS'] = (results['ROUND_NUM'] - 1) * 300 + results['ROUND_TIME_SECONDS']
    result_lookup = results[['MATCH_KEY', 'WINNER_KEY', 'DURATION_SECONDS']].drop_duplicates('MATCH_KEY', keep='last').set_index('MATCH_KEY')
    h['WINNER_KEY'] = h['MATCH_KEY'].map(result_lookup['WINNER_KEY'])
    h['DURATION_SECONDS'] = h['MATCH_KEY'].map(result_lookup['DURATION_SECONDS'])
    h['WIN'] = np.where(h['WINNER_KEY'] == '', np.nan, np.where(h['FIGHTER_KEY'] == h['WINNER_KEY'], 1.0, 0.0))
    missing_winner = h['WINNER_KEY'].isna() | (h['WINNER_KEY'] == '')
    h.loc[missing_winner, 'WIN'] = np.nan
    opp_stats = h[['MATCH_KEY', 'FIGHTER_KEY', 'SIG_STR_LANDED', 'SIG_STR_ATT', 'TD_LANDED', 'TD_ATT', 'CTRL_SECONDS']].copy()
    opp_stats = opp_stats.rename(columns={'FIGHTER_KEY': 'OPP_LOOKUP_KEY', 'SIG_STR_LANDED': 'OPP_SIG_STR_LANDED', 'SIG_STR_ATT': 'OPP_SIG_STR_ATT', 'TD_LANDED': 'OPP_TD_LANDED', 'TD_ATT': 'OPP_TD_ATT', 'CTRL_SECONDS': 'OPP_CTRL_SECONDS'})
    h = h.merge(opp_stats, left_on=['MATCH_KEY', 'OPP_KEY'], right_on=['MATCH_KEY', 'OPP_LOOKUP_KEY'], how='left')
    h = h.drop(columns=['OPP_LOOKUP_KEY'])
    elo_current = {}
    pre_elo = {}
    
    def get_elo(key):
        return elo_current.get(key, ELO_START)
    results_sorted = results.sort_values('DATE', kind='stable').copy()
    for _, row in results_sorted.iterrows():
        a = row['FIGHTER_A_KEY']
        b = row['FIGHTER_B_KEY']
        winner = row['WINNER_KEY']
        match = row['MATCH_KEY']
        if not a or not b:
            continue
        ra = get_elo(a)
        rb = get_elo(b)
        pre_elo[match, a] = ra
        pre_elo[match, b] = rb
        if not winner:
            continue
        expected_a = 1 / (1 + 10 ** ((rb - ra) / 400))
        if winner == a:
            score_a = 1.0
        elif winner == b:
            score_a = 0.0
        else:
            score_a = 0.5
        score_b = 1 - score_a
        expected_b = 1 - expected_a
        elo_current[a] = ra + ELO_K * (score_a - expected_a)
        elo_current[b] = rb + ELO_K * (score_b - expected_b)
    h['OPP_PRE_ELO'] = [pre_elo.get((match, opp), ELO_START) for match, opp in zip(h['MATCH_KEY'], h['OPP_KEY'])]
    bio_fighter_col = find_column(bio, ['FIGHTER'], required=True)
    dob_col = find_column(bio, ['DOB'], required=True)
    height_col = find_column(bio, ['HEIGHT'], required=True)
    reach_col = find_column(bio, ['REACH'], required=True)
    bio['FIGHTER_KEY'] = bio[bio_fighter_col].map(fighter_key)
    bio['DOB_PARSED'] = pd.to_datetime(bio[dob_col], errors='coerce')
    
    def parse_height(value):
        if pd.isna(value):
            return np.nan
        text = str(value).strip()
        try:
            x = float(text)
            if x > 40:
                return x
        except:
            pass
        match = re.search("(\\d+)\\s*['′]\\s*(\\d+)", text)
        if match:
            feet = int(match.group(1))
            inches = int(match.group(2))
            return feet * 12 + inches
        return np.nan
    
    def parse_reach(value):
        if pd.isna(value):
            return np.nan
        text = str(value).strip()
        number = re.search('(\\d+(?:\\.\\d+)?)', text)
        if not number:
            return np.nan
        return float(number.group(1))
    bio['HEIGHT_IN_PARSED'] = bio[height_col].map(parse_height)
    bio['REACH_IN_PARSED'] = bio[reach_col].map(parse_reach)
    bio_lookup = bio.drop_duplicates('FIGHTER_KEY', keep='last').set_index('FIGHTER_KEY')
    
    def safe_ratio(numerator, denominator):
        denominator = float(denominator)
        if denominator == 0 or np.isnan(denominator):
            return np.nan
        return float(numerator) / denominator
    
    def fighter_state(fighter_name, fight_date):
        key = fighter_key(fighter_name)
        past = h[(h['FIGHTER_KEY'] == key) & (h['DATE'] < fight_date)].sort_values('DATE').copy()
        n = len(past)
        wins = int((past['WIN'] == 1).sum())
        losses = int((past['WIN'] == 0).sum())
        win_pct = wins / n if n > 0 else np.nan
    
        def avg(col):
            if n == 0:
                return np.nan
            return pd.to_numeric(past[col], errors='coerce').mean()
    
        def total(col):
            if n == 0:
                return 0.0
            return pd.to_numeric(past[col], errors='coerce').sum(min_count=1)
        duration_seconds = total('DURATION_SECONDS')
        duration_minutes = duration_seconds / 60 if pd.notna(duration_seconds) else np.nan
        sig_landed = total('SIG_STR_LANDED')
        sig_att = total('SIG_STR_ATT')
        opp_sig_landed = total('OPP_SIG_STR_LANDED')
        opp_sig_att = total('OPP_SIG_STR_ATT')
        td_landed = total('TD_LANDED')
        td_att = total('TD_ATT')
        opp_td_landed = total('OPP_TD_LANDED')
        opp_td_att = total('OPP_TD_ATT')
        sub_att = total('SUB_ATT')
        ctrl = total('CTRL_SECONDS')
        opp_ctrl = total('OPP_CTRL_SECONDS')
        recent = past.tail(3).copy()
        recent_n = len(recent)
    
        def recent_total(col):
            if recent_n == 0:
                return 0.0
            return pd.to_numeric(recent[col], errors='coerce').sum(min_count=1)
        recent_duration_sec = recent_total('DURATION_SECONDS')
        recent_duration_min = recent_duration_sec / 60 if pd.notna(recent_duration_sec) else np.nan
        if n > 0:
            last_date = past['DATE'].max()
            days_since = (fight_date - last_date).days
        else:
            last_date = pd.NaT
            days_since = np.nan
        if key in bio_lookup.index:
            profile = bio_lookup.loc[key]
            if isinstance(profile, pd.DataFrame):
                profile = profile.iloc[-1]
            dob = profile['DOB_PARSED']
            height = profile['HEIGHT_IN_PARSED']
            reach = profile['REACH_IN_PARSED']
        else:
            dob = pd.NaT
            height = np.nan
            reach = np.nan
        age = (fight_date - dob).days / 365.25 if pd.notna(dob) else np.nan
        current_elo = elo_current.get(key, ELO_START)
        opp_elos = pd.to_numeric(past['OPP_PRE_ELO'], errors='coerce')
        prior_avg_opp_elo = opp_elos.mean() if n else np.nan
        prior_max_opp_elo = opp_elos.max() if n else np.nan
        recent3_avg_opp_elo = opp_elos.tail(3).mean() if n else np.nan
        r_sig_landed = recent_total('SIG_STR_LANDED')
        r_opp_sig_landed = recent_total('OPP_SIG_STR_LANDED')
        r_td_landed = recent_total('TD_LANDED')
        r_opp_td_landed = recent_total('OPP_TD_LANDED')
        r_sub_att = recent_total('SUB_ATT')
        r_ctrl = recent_total('CTRL_SECONDS')
        r_opp_ctrl = recent_total('OPP_CTRL_SECONDS')
        recent_win_rate = (recent['WIN'] == 1).sum() / recent_n if recent_n else np.nan
        state = {'PRIOR_FIGHTS': float(n), 'PRIOR_WINS': float(wins), 'PRIOR_LOSSES': float(losses), 'PRIOR_WIN_PCT': win_pct, 'PRIOR_AVG_KD': avg('KD'), 'PRIOR_AVG_SIG_STR_LANDED': avg('SIG_STR_LANDED'), 'PRIOR_AVG_SIG_STR_ATT': avg('SIG_STR_ATT'), 'PRIOR_AVG_TOTAL_STR_LANDED': avg('TOTAL_STR_LANDED'), 'PRIOR_AVG_TOTAL_STR_ATT': avg('TOTAL_STR_ATT'), 'PRIOR_AVG_TD_LANDED': avg('TD_LANDED'), 'PRIOR_AVG_TD_ATT': avg('TD_ATT'), 'PRIOR_AVG_SUB.ATT': avg('SUB_ATT'), 'PRIOR_AVG_CTRL_SECONDS': avg('CTRL_SECONDS'), 'PRIOR_SIG_STR_ACC': safe_ratio(sig_landed, sig_att), 'PRIOR_TD_ACC': safe_ratio(td_landed, td_att), 'DAYS_SINCE_LAST_FIGHT': days_since, 'ELO': current_elo, 'UFC_DEBUT': float(n == 0), 'AGE': age, 'HEIGHT_IN': height, 'REACH_IN': reach, 'RATE_SIG_STR_LANDED_PM': safe_ratio(sig_landed, duration_minutes), 'RATE_SIG_STR_ABSORBED_PM': safe_ratio(opp_sig_landed, duration_minutes), 'RATE_TD_LANDED_PER15': safe_ratio(td_landed, duration_minutes) * 15 if duration_minutes else np.nan, 'RATE_TD_ALLOWED_PER15': safe_ratio(opp_td_landed, duration_minutes) * 15 if duration_minutes else np.nan, 'RATE_SUB_ATT_PER15': safe_ratio(sub_att, duration_minutes) * 15 if duration_minutes else np.nan, 'RATE_SIG_STR_ACC': safe_ratio(sig_landed, sig_att), 'RATE_SIG_STR_DEF': 1 - safe_ratio(opp_sig_landed, opp_sig_att) if pd.notna(safe_ratio(opp_sig_landed, opp_sig_att)) else np.nan, 'RATE_TD_ACC': safe_ratio(td_landed, td_att), 'RATE_TD_DEF': 1 - safe_ratio(opp_td_landed, opp_td_att) if pd.notna(safe_ratio(opp_td_landed, opp_td_att)) else np.nan, 'RATE_CTRL_SHARE': safe_ratio(ctrl, ctrl + opp_ctrl), 'RECENT3_SIG_LANDED_PM': safe_ratio(r_sig_landed, recent_duration_min), 'RECENT3_SIG_ABSORBED_PM': safe_ratio(r_opp_sig_landed, recent_duration_min), 'RECENT3_TD_LANDED_PER15': safe_ratio(r_td_landed, recent_duration_min) * 15 if recent_duration_min else np.nan, 'RECENT3_TD_ALLOWED_PER15': safe_ratio(r_opp_td_landed, recent_duration_min) * 15 if recent_duration_min else np.nan, 'RECENT3_SUB_ATT_PER15': safe_ratio(r_sub_att, recent_duration_min) * 15 if recent_duration_min else np.nan, 'RECENT3_CTRL_SHARE': safe_ratio(r_ctrl, r_ctrl + r_opp_ctrl), 'RECENT3_WIN_RATE': recent_win_rate, 'RECENT3_FIGHT_COUNT': float(recent_n), 'PRIOR_AVG_OPP_ELO': prior_avg_opp_elo, 'PRIOR_MAX_OPP_ELO': prior_max_opp_elo, 'RECENT3_AVG_OPP_ELO': recent3_avg_opp_elo}
        return (state, {'KEY': key, 'UFC_FIGHTS': n, 'LAST_FIGHT': last_date, 'BIO_FOUND': key in bio_lookup.index})
    live_rows = []
    for _, fight in upcoming.iterrows():
        date = pd.Timestamp(fight['DATE'])
        fighter_a = fight['FIGHTER_A']
        fighter_b = fight['FIGHTER_B']
        state_a, info_a = fighter_state(fighter_a, date)
        state_b, info_b = fighter_state(fighter_b, date)
        row = {'DATE': date, 'EVENT': fight['EVENT'], 'FIGHTER_A': fighter_a, 'FIGHTER_B': fighter_b, 'A_UFC_FIGHTS': info_a['UFC_FIGHTS'], 'B_UFC_FIGHTS': info_b['UFC_FIGHTS'], 'A_LAST_FIGHT': info_a['LAST_FIGHT'], 'B_LAST_FIGHT': info_b['LAST_FIGHT'], 'A_BIO_FOUND': info_a['BIO_FOUND'], 'B_BIO_FOUND': info_b['BIO_FOUND']}
        for base in BASE_FEATURES:
            a = state_a.get(base, np.nan)
            b = state_b.get(base, np.nan)
            try:
                diff = float(a) - float(b)
            except:
                diff = np.nan
            row['DIFF_' + base] = diff
        live_rows.append(row)
    live = pd.DataFrame(live_rows)
    missing_features = [c for c in features if c not in live.columns]
    if missing_features:
        raise ValueError('Missing live features: ' + str(missing_features))
    live[features] = live[features].replace([np.inf, -np.inf], np.nan)
    
    def quality_label(row):
        a = int(row['A_UFC_FIGHTS'])
        b = int(row['B_UFC_FIGHTS'])
        if a == 0 or b == 0:
            return 'DEBUT / OUTSIDE-UFC DATA WARNING'
        if a <= 2 or b <= 2:
            return 'VERY LOW UFC DATA'
        if a <= 4 or b <= 4:
            return 'LOW UFC DATA'
        return 'NORMAL'
    live['DATA_QUALITY'] = live.apply(quality_label, axis=1)
    return live, features, fighter_key

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
        prices[ident] = number
    if str(a_id) not in prices or str(b_id) not in prices:
        return None
    return prices[str(a_id)], prices[str(b_id)]


def fetch_odds(cards):
    import pandas as pd
    def one(row):
        base = {c: str(row[c]) for c in ["EVENT_ID", "FIGHT_ID", "FIGHTER_A", "FIGHTER_B"]}
        url = f"{CORE}/events/{row.EVENT_ID}/competitions/{row.FIGHT_ID}/odds?lang=en&region=us"
        stamp = datetime.now(timezone.utc)
        if stamp >= pd.to_datetime(row.EVENT_START_UTC, utc=True).to_pydatetime():
            return None, {**base, "STATUS": "EVENT_ALREADY_STARTED"}
        try:
            payload = get_json(url)
            choices = payload.get("items", [])
            choices = sorted(choices, key=lambda x: (x.get("provider", {}).get("priority", 999), str(x.get("provider", {}).get("id", ""))))
            for item in choices:
                if item.get("$ref") and not any(k in item for k in ["homeAthleteOdds", "awayAthleteOdds"]):
                    item = get_json(item["$ref"])
                pair = parse_quote(item, row.A_ESPN_ID, row.B_ESPN_ID)
                if pair is None:
                    continue
                observed = datetime.now(timezone.utc)
                if observed >= pd.to_datetime(row.EVENT_START_UTC, utc=True).to_pydatetime():
                    return None, {**base, "STATUS": "EVENT_STARTED_DURING_REQUEST"}
                quote = {**base, "A_ODDS": pair[0], "B_ODDS": pair[1], "ODDS_AS_OF_UTC": observed.isoformat(),
                         "PROVIDER": item.get("provider", {}).get("name", "UNKNOWN"), "SOURCE_URL": url}
                return quote, {**base, "STATUS": "ODDS_FOUND", "PROVIDER": quote["PROVIDER"]}
            return None, {**base, "STATUS": "NO_MATCHED_CURRENT_MONEYLINES"}
        except (HTTPError, URLError, ValueError, TypeError, OSError) as exc:
            return None, {**base, "STATUS": "UNAVAILABLE: " + str(exc)}
    rows = list(cards.itertuples(index=False))
    # A series is needed for both keyed and attribute access in one().
    with ThreadPoolExecutor(max_workers=4) as pool:
        result = list(pool.map(one, [row for _, row in cards.iterrows()]))
    quotes = [quote for quote, _ in result if quote is not None]
    columns = ["EVENT_ID", "FIGHT_ID", "FIGHTER_A", "FIGHTER_B", "A_ODDS", "B_ODDS", "ODDS_AS_OF_UTC", "PROVIDER", "SOURCE_URL"]
    return pd.DataFrame(quotes, columns=columns), pd.DataFrame([audit for _, audit in result])


def _preufc_features(root, live, fighter_key, metadata):
    raw = pd.read_csv(root / 'data/sherdog_preufc_features_full.csv')
    required = [c.removeprefix('DIFF_') for c in metadata['preufc_features']]
    if any(c not in raw for c in ['FIGHTER'] + required):
        raise ValueError('Sherdog CSV is missing required columns')
    raw['_KEY'] = raw.FIGHTER.map(fighter_key)
    if raw['_KEY'].duplicated().any():
        raise ValueError('Ambiguous Sherdog fighter identities; resolve duplicate keys first')
    lookup = raw.set_index('_KEY')
    override_path = root / 'data/live_debut_preufc_features_final.csv'
    overrides = pd.read_csv(override_path) if override_path.is_file() else pd.DataFrame()
    if not overrides.empty:
        overrides['_KEY'] = overrides.FIGHTER.map(fighter_key)
        overrides['_DATE'] = overrides.DATE.map(pd.Timestamp)
        if 'MANUAL_ALIAS' in overrides:
            aliases = overrides.loc[overrides.MANUAL_ALIAS.notna()].copy()
            aliases['_KEY'] = aliases.MANUAL_ALIAS.map(fighter_key)
            overrides = pd.concat([overrides, aliases], ignore_index=True)
    result = live.copy()
    for i, row in result.iterrows():
        sides = {}
        for side in ['A', 'B']:
            key = fighter_key(row[f'FIGHTER_{side}'])
            source = lookup.loc[key] if key in lookup.index else None
            label = 'SHERDOG_FROZEN' if source is not None else 'MISSING'
            if source is None and not overrides.empty:
                matches = overrides[(overrides._KEY == key) & (overrides._DATE <= pd.Timestamp(row.DATE))]
                if not matches.empty:
                    matches = matches[matches.STATUS.isin(['RESOLVED_LIVE','VERIFIED_OVERRIDE_LIVE'])]
                    if not matches.empty:
                        last_date = matches._DATE.max()
                        matches = matches[matches._DATE == last_date]
                        if len(matches[required].drop_duplicates()) != 1:
                            raise ValueError('Ambiguous live Pre-UFC override: ' + key)
                        source = matches.iloc[-1]
                        label = 'VERIFIED_LIVE_OVERRIDE'
            sides[side] = {}
            for col in required:
                value = pd.to_numeric(source.get(col), errors='coerce') if source is not None else np.nan
                sides[side][col] = value
                result.loc[i, f'{side}_{col}'] = value
            result.loc[i, f'{side}_PREUFC_SOURCE'] = label
        for col in required:
            result.loc[i, 'DIFF_' + col] = sides['A'][col] - sides['B'][col]
    result['PREUFC_COMPLETE'] = result[metadata['preufc_features']].notna().all(axis=1)
    return result


def _predict_matrix(root, live, metadata):
    features = metadata['features']
    logistic = joblib.load(root / 'models/ufc_logistic_production_v2_preufc.joblib')
    cat = CatBoostClassifier()
    cat.load_model(str(root / 'models/ufc_catboost_production_v2_preufc.cbm'))
    if list(logistic.feature_names_in_) != features or cat.feature_names_ != features:
        raise ValueError('V2 feature order differs from metadata')
    if list(logistic.classes_) != [0, 1] or list(cat.classes_) != [0, 1]:
        raise ValueError('Unexpected model labels')
    matrix = live[features].replace([np.inf, -np.inf], np.nan)
    try:
        p = metadata['ensemble']['catboost_weight'] * cat.predict_proba(matrix)[:, 1]
        p += metadata['ensemble']['logistic_weight'] * logistic.predict_proba(matrix)[:, 1]
    except AttributeError as exc:
        raise RuntimeError('Saved models are incompatible with this sklearn version. Install scikit-learn==1.5.2 and numpy<2, restart the notebook kernel, then rerun.') from exc
    result = live.copy()
    result['P_A'], result['P_B'] = p, 1-p
    result['PICK'] = np.where(p >= .5, result.FIGHTER_A, result.FIGHTER_B)
    result['PICK_PROB'] = np.maximum(p, 1-p)
    return result


def predict_upcoming_v2(root=None, months=12, bankroll=10000., fetch_prices=True, cards=None):
    """Return fresh predictions and output folder; bankroll is fixed per card.

    Optional cards DataFrame supports offline verification. No model training,
    history updates or betting orders are performed.
    """
    if root is None:
        candidates = [Path.cwd(), *Path.cwd().parents]
        root = next((p for p in candidates if (p/'models/ufc_production_v2_preufc_metadata.json').is_file()), None)
        if root is None:
            raise FileNotFoundError('Set root to your UFC project directory')
    root = Path(root).resolve()
    if months <= 0 or bankroll <= 0:
        raise ValueError('months and bankroll must be positive')
    metadata = json.loads((root/'models/ufc_production_v2_preufc_metadata.json').read_text())
    if metadata['feature_count'] != 46 or metadata['production_version'] != 'v2_preufc':
        raise ValueError('Expected the 46-feature Pre-UFC V2 models')
    now = datetime.now(timezone.utc)
    if cards is None:
        print('Rufe aktuelle zukünftige UFC-Karten ab ...', flush=True)
        rows, coverage = fetch_cards(now.date(), now.date()+timedelta(days=int(months*31)))
        cards = pd.DataFrame(rows)
    else:
        cards = cards.copy()
        coverage = []
    live, base_features, fighter_key = _build_base(root, cards)
    if base_features != metadata['features'][:42]:
        raise ValueError('Base feature order differs from the saved V2 metadata')
    live = _preufc_features(root, live, fighter_key, metadata)
    live = _predict_matrix(root, live, metadata)
    for col in ['EVENT_ID','FIGHT_ID','EVENT_START_UTC','SOURCE_URL','A_ESPN_ID','B_ESPN_ID']:
        live[col] = cards[col].to_numpy()
    live['GENERATED_AT_UTC'] = now.isoformat()
    live['MODEL_VERSION'] = 'v2_preufc'
    results = pd.read_csv(root/'data/fight_results_clean.csv', usecols=['DATE'])
    history_date = pd.to_datetime(results.DATE).max().date()
    live['HISTORY_LAST_DATE'] = str(history_date)
    folder = root/'reports'/'v2_predictions'/now.strftime('%Y%m%dT%H%M%S_%fZ')
    folder.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(coverage).to_csv(folder/'event_coverage.csv', index=False)
    cards.to_csv(folder/'upcoming_cards.csv', index=False)
    price_path = None
    if fetch_prices:
        print('Rufe aktuelle Quoten ab ...', flush=True)
        quotes, audit = fetch_odds(cards)
        price_path = folder/'odds_snapshot.csv'
        quotes.to_csv(price_path, index=False)
        audit.to_csv(folder/'odds_coverage.csv', index=False)
    live = add_odds(live, price_path, 'american', bankroll)
    # Confidence and UFC-count filters remain identical to V1. Additional
    # source/missing-feature flags are displayed explicitly for V2.
    uncertainty = ~live.PREUFC_COMPLETE | ~live.A_BIO_FOUND | ~live.B_BIO_FOUND
    uncertain_bets = (live.ACTION == 'BET') & uncertainty
    live.loc[uncertain_bets, 'ACTION'] = 'BET — REVIEW DATA'
    live.loc[uncertain_bets, 'SIM_STAKE'] = 0.
    live.to_csv(folder/'predictions_v2.csv', index=False)
    live[['DATE','EVENT','FIGHTER_A','FIGHTER_B']+metadata['features']].to_csv(folder/'features_v2.csv', index=False)
    run = dict(generated_at_utc=now.isoformat(), model_version='v2_preufc', model_training_cutoff=metadata['training_end_date'], history_last_date=str(history_date), bankroll_per_event=bankroll, retrained=False, source='ESPN scoreboard; currently listed matchups; announcement coverage not guaranteed', model_sha256={n:hashlib.sha256((root/'models'/n).read_bytes()).hexdigest() for n in ['ufc_catboost_production_v2_preufc.cbm','ufc_logistic_production_v2_preufc.joblib']})
    (folder/'run.json').write_text(json.dumps(run, indent=2))
    print(f'V2: {len(live)} Picks | {live.EVENT.nunique()} Karten | Trainingsende {metadata["training_end_date"]} | lokale Kampfstatistiken bis {history_date}', flush=True)
    print(f'Gespeichert: {folder}', flush=True)
    print('Kelly-Einsätze sind Simulationen. Fehlende Pre-UFC-/Bio-Daten erfordern Prüfung. Der Lauf aktualisiert keine Kampfstatistiken.', flush=True)
    return live, folder
