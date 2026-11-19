"""Settle a saved prediction snapshot using ESPN winner IDs.

Adapted from updated_type_shit.zip/UFC_Update_v2/settle_picks.py.
Two-way moneyline simulation: explicit cancellations, draws and no contests void.
This is not a bookmaker statement; unknown outcomes require review.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import json
import math
import re
from urllib.parse import urlencode
from ufc_ai.live_odds import get_json


def api_json(path, **params):
    return get_json('https://site.api.espn.com/apis/site/v2/sports/mma/ufc/'
                    + path + '?' + urlencode(params))


def validate(snapshot, flat_stake):
    required = ['EVENT_ID', 'FIGHT_ID', 'A_ESPN_ID', 'B_ESPN_ID', 'DATE',
                'EVENT', 'FIGHTER_A', 'FIGHTER_B', 'P_A', 'PICK_ODDS_DECIMAL', 'SIM_STAKE']
    if any(c not in snapshot for c in required):
        raise ValueError('Missing prediction snapshot columns')
    if not math.isfinite(flat_stake) or flat_stake <= 0:
        raise ValueError('Flat stake must be finite and positive')
    for column in ['EVENT_ID', 'FIGHT_ID', 'A_ESPN_ID', 'B_ESPN_ID']:
        if snapshot[column].isna().any() or snapshot[column].astype(str).str.strip().eq('').any():
            raise ValueError('Missing identifier: ' + column)
    if snapshot.duplicated(['EVENT_ID', 'FIGHT_ID']).any():
        raise ValueError('Duplicate snapshot fight')
    if snapshot.A_ESPN_ID.astype(str).eq(snapshot.B_ESPN_ID.astype(str)).any():
        raise ValueError('Identical athlete IDs')
    for p, price, stake in snapshot[['P_A', 'PICK_ODDS_DECIMAL', 'SIM_STAKE']].itertuples(index=False, name=None):
        if not math.isfinite(p) or not 0 <= p <= 1:
            raise ValueError('Invalid probability')
        if not math.isfinite(stake) or stake < 0:
            raise ValueError('Invalid stake')
        if pd.notna(price) and (not math.isfinite(price) or price <= 1):
            raise ValueError('Invalid decimal odds')
        if stake > 0 and pd.isna(price):
            raise ValueError('Positive stake without saved odds')


def settle(snapshot, events, flat_stake=100.):
    validate(snapshot, flat_stake)
    result = snapshot.copy().reset_index(drop=True)
    competitions = {}
    for event in events:
        for fight in event.get("competitions", []):
            key = (str(event['id']), str(fight['id']))
            if key in competitions:
                raise ValueError('Duplicate result fight')
            competitions[key] = fight
    result["RESULT_STATUS"] = "PENDING"
    result["WINNER"] = None
    result["PICK_CORRECT"] = None
    result["FLAT_PNL"] = float("nan")
    result["STRATEGY_PNL"] = float("nan")
    for i, row in result.iterrows():
        fight = competitions.get((str(row.EVENT_ID), str(row.FIGHT_ID)))
        if not fight:
            result.loc[i, "RESULT_STATUS"] = "RESULT_NOT_FOUND"
            continue
        status = fight.get("status", {}).get("type", {})
        competitors = fight.get("competitors", [])
        ids = {str(c.get("id")) for c in competitors}
        expected = {str(row.A_ESPN_ID), str(row.B_ESPN_ID)}
        if len(competitors) != 2 or ids != expected:
            result.loc[i, "RESULT_STATUS"] = "MATCHUP_CHANGED_REVIEW"
            continue
        description = " ".join(str(fight.get(k, "")) for k in ["status", "result", "type"])
        cancelled = bool(re.search(r'\bCANCEL(?:ED|LED|LATION)\b', description.upper()))
        void = cancelled or (status.get('completed') is True and bool(
            re.search(r'\b(?:NO[ -]CONTEST|DRAW)\b', description.upper())))
        if void:
            result.loc[i, "RESULT_STATUS"] = "VOID"
            result.loc[i, ["FLAT_PNL", "STRATEGY_PNL"]] = 0.
            continue
        if status.get("completed") is not True:
            continue
        winners = [c for c in competitors if c.get("winner") is True]
        if len(winners) != 1:
            result.loc[i, "RESULT_STATUS"] = "COMPLETED_WITHOUT_WINNER_REVIEW"
            continue
        winner_id = str(winners[0]["id"])
        pick_id = str(row.A_ESPN_ID) if row.P_A >= .5 else str(row.B_ESPN_ID)
        won = winner_id == pick_id
        result.loc[i, "WINNER"] = row.FIGHTER_A if winner_id == str(row.A_ESPN_ID) else row.FIGHTER_B
        result.loc[i, "PICK_CORRECT"] = won
        result.loc[i, "RESULT_STATUS"] = "SETTLED"
        price = row.PICK_ODDS_DECIMAL
        stake = row.SIM_STAKE
        if pd.notna(price):
            multiplier = price - 1 if won else -1
            result.loc[i, "FLAT_PNL"] = flat_stake * multiplier
            result.loc[i, "STRATEGY_PNL"] = stake * multiplier
        elif stake == 0:
            result.loc[i, "STRATEGY_PNL"] = 0.
    return result


def summarize(ledger, flat_stake):
    validate(ledger, flat_stake)
    rows = []
    for event, frame in ledger.groupby("EVENT_ID", sort=False):
        settled = frame.RESULT_STATUS == "SETTLED"
        priced = settled & frame.PICK_ODDS_DECIMAL.notna()
        bets = settled & (frame.SIM_STAKE > 0)
        flat_pnl = frame.loc[priced, "FLAT_PNL"].sum() if priced.any() else None
        strategy_pnl = frame.loc[bets, "STRATEGY_PNL"].sum() if bets.any() else None
        flat_exposure = priced.sum() * flat_stake
        strategy_exposure = frame.loc[bets, "SIM_STAKE"].sum()
        rows.append({"EVENT_ID": event, "EVENT": frame.EVENT.iloc[0], "DATE": frame.DATE.iloc[0],
                     "SNAPSHOT_PICKS": len(frame), "SETTLED_FIGHTS": int(settled.sum()),
                     "VOID": int((frame.RESULT_STATUS == "VOID").sum()),
                     "UNRESOLVED": int((~frame.RESULT_STATUS.isin(["SETTLED", "VOID"])).sum()),
                     "SETTLED_WITHOUT_ODDS": int((settled & frame.PICK_ODDS_DECIMAL.isna()).sum()),
                     "FLAT_BETS": int(priced.sum()), "FLAT_STAKE": flat_exposure, "FLAT_NET_PNL": flat_pnl,
                     "FLAT_ROI": flat_pnl / flat_exposure if flat_exposure else None,
                     "STRATEGY_BETS": int(bets.sum()), "STRATEGY_STAKE": strategy_exposure,
                     "STRATEGY_NET_PNL": strategy_pnl,
                     "STRATEGY_ROI": strategy_pnl / strategy_exposure if strategy_exposure else None})
    return pd.DataFrame(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--flat-stake", type=float, default=100.)
    parser.add_argument('--events-json', type=Path, help='Offline ESPN scoreboard JSON fixture')
    args = parser.parse_args(argv)
    if args.flat_stake <= 0:
        parser.error("Flat stake must be positive")
    snapshot = pd.read_csv(args.predictions, dtype={c: str for c in ["EVENT_ID", "FIGHT_ID", "A_ESPN_ID", "B_ESPN_ID"]})
    validate(snapshot, args.flat_stake)
    if args.events_json:
        events = json.loads(args.events_json.read_text())['events']
    else:
        events = []
        for day in sorted(pd.to_datetime(snapshot.DATE).dt.strftime('%Y%m%d').unique()):
            payload = api_json('scoreboard', dates=day, limit=1000)
            if 'events' not in payload:
                raise ValueError('No usable event response')
            events.extend(payload['events'])
    ledger = settle(snapshot, events, args.flat_stake)
    summary = summarize(ledger, args.flat_stake)
    out = args.predictions.resolve().parent / ("settlement_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ"))
    out.mkdir(exist_ok=False)
    ledger.to_csv(out / "fight_ledger.csv", index=False)
    summary.to_csv(out / "event_pnl.csv", index=False)
    print(summary.to_string(index=False))
    print(f"Saved to {out}. Unresolved fights and absent odds are not scored as losses or zero-profit bets.")


if __name__ == "__main__":
    main()
