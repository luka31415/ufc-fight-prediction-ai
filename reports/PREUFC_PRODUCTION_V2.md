# Production v2 — Sherdog Pre-UFC Features

## Why I built this branch

After several weeks of working on the UFC prediction system, one of the clearest remaining weaknesses was the cold-start problem. My original production model was based entirely on UFC history, so debutants and fighters with only a small number of UFC fights naturally had less useful information available.

I therefore built a second external-data branch using Sherdog professional fight histories. The rule was strict: I only use fights that happened before the fighter's first UFC appearance.

## Sherdog identity resolution

I built a resumable scraper and identity resolver rather than trusting fighter-name matches blindly.

Final coverage:

- UFC fighter universe: 2,725
- resolved fighters: 2,530 (92.8%)
- review cases: 195 (7.2%)
- scraper errors: 0
- strict pre-UFC history rows: 33,845

Identity validation was strong:

- exact 0-day UFC-debut-date matches: 2,495
- 1-day matches: 35
- 2-day matches: 0
- 3-day matches: 0
- maximum accepted resolved difference: 1 day

I left 177 no-candidate cases and 18 large date-mismatch cases unresolved instead of forcing questionable matches.

## Pre-UFC coverage

Among the 2,530 resolved fighters:

- 96.4% had at least one pre-UFC professional fight
- 94.6% had at least three
- 91.2% had at least five
- 67.8% had at least ten
- median pre-UFC professional fights: 12
- mean pre-UFC professional fights: 13.38

The four features I selected for the first production test were:

1. `DIFF_PREUFC_PRO_FIGHTS`
2. `DIFF_PREUFC_WIN_PCT`
3. `DIFF_PREUFC_FINISH_RATE`
4. `DIFF_PREUFC_RECENT5_WIN_PCT`

The model therefore moved from 42 to 46 features.

## Predictive evaluation

I kept the production architecture unchanged:

- 55% CatBoost
- 45% Logistic Regression
- chronological walk-forward evaluation
- no random train/test split

### 2020–2024

| Model | Accuracy | Log Loss | Brier | AUC |
|---|---:|---:|---:|---:|
| Baseline 42 | 0.61302 | 0.65183 | 0.23007 | 0.66156 |
| Pre-UFC 46 | 0.62434 | 0.64865 | 0.22853 | 0.66853 |

### 2025–2026

| Model | Accuracy | Log Loss | Brier | AUC |
|---|---:|---:|---:|---:|
| Baseline 42 | 0.65428 | 0.63730 | 0.22313 | 0.69187 |
| Pre-UFC 46 | 0.65090 | 0.63287 | 0.22109 | 0.69905 |

The most important robustness result was that log loss and Brier score improved in every evaluated year from 2020 through 2026.

The effect was especially strong in the low-UFC-history subgroup.

### Low-UFC-history fights, 2020–2024

- Log loss: -0.00513
- Brier: -0.00240
- AUC: +0.01137

### Low-UFC-history fights, 2025–2026

- Log loss: -0.00682
- Brier: -0.00301
- AUC: +0.01014

## Locked betting backtest

I deliberately did not tune the betting rules for this feature branch. I reused the locked system:

- confidence >= 0.60
- EV >= 0.10
- quarter Kelly
- maximum 3% bankroll per fight
- maximum 12.5% bankroll per event

### 2020–2024

| Model | Bets | Win Rate | Flat ROI | Kelly ROI | Max Drawdown |
|---|---:|---:|---:|---:|---:|
| Baseline 42 | 289 | 57.44% | 10.37% | 6.53% | 24.61% |
| Pre-UFC 46 | 289 | 58.13% | 9.73% | 6.13% | 22.32% |

This period was roughly neutral to slightly worse on return, although drawdown improved.

### 2025–2026

| Model | Bets | Win Rate | Flat ROI | Kelly ROI | Max Drawdown |
|---|---:|---:|---:|---:|---:|
| Baseline 42 | 81 | 59.26% | 26.22% | 19.79% | 10.43% |
| Pre-UFC 46 | 83 | 63.86% | 36.55% | 24.38% | 16.95% |

This later period was materially better for the Pre-UFC model.

The bet-set analysis was also encouraging. In 2025–2026, the 14 bets removed by Pre-UFC had a -12.54% flat ROI, while the 15 bets newly added by Pre-UFC had a +38.78% flat ROI.

## Production decision

I promoted this branch to **Production v2**.

Production v1 remains the 42-feature fallback/reference model.

Production v2 uses:

- the original 42 UFC-derived features
- 4 Sherdog-derived pre-UFC features
- the same 55/45 CatBoost/Logistic blend
- the same locked betting rules

I saved the trained v2 models locally under separate filenames so Production v1 was not overwritten.

## Current status

The model-training and evaluation side of Production v2 is complete. The next engineering step is live integration: upcoming fight feature matrices need to receive the four frozen Sherdog features before inference so the 46-feature model can be used automatically for live cards.

As with every betting result in this project, these are historical backtests and not guarantees of future profit.
