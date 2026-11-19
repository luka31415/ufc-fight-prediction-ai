# Settle saved prediction snapshots

Adapted from `updated_type_shit.zip/UFC_Update_v2/settle_picks.py`. Install the
repository package first (`pip install -e .`). Use the exact saved prediction
CSV with ESPN event/fight/athlete IDs, `P_A`, saved decimal odds and `SIM_STAKE`:

```sh
python scripts/settle_picks.py --predictions reports/v21_predictions/RUN/predictions_v21.csv
python scripts/settle_picks.py --predictions predictions_v21.csv --events-json scoreboard.json
```

The offline JSON has the ESPN scoreboard shape `{"events": [...]}`. The online
path queries each snapshot date and fails on an unusable response. The input
snapshot is never changed; a new timestamped settlement directory contains the
fight ledger and event summary. Repeating the same input/results gives the same
ledger, not cumulative P&L. Duplicate fight records or invalid stakes/probabilities/
prices fail validation. IDs are read as strings, including leading zeroes.

Athlete IDs must exactly match both saved opponents. Replacements, missing
results, incomplete fights and completed fights without one explicit winner
remain unresolved with missing P&L. Explicit cancellations, completed draws and
no contests void this **two-way moneyline simulation**, with zero P&L and no
accuracy result. Bookmaker rules may differ; this does not settle real wagers.
Void and unresolved rows do not enter settled-bet ROI denominators. Missing
odds do not become zero-profit bets; positive stakes without saved odds fail.
Flat-stake and strategy P&L use saved prices, never current odds. Settlement
revisions require a fresh result snapshot and may change a prior ledger.
