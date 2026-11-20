# UFC Fight Prediction & Betting AI

I have been working on this project for several weeks. What started as one large Jupyter notebook gradually turned into a full research pipeline for UFC fight prediction, probability calibration, betting backtesting, data scraping, and experiment tracking.

My goal is not just to predict which fighter wins. I want to estimate **well-calibrated win probabilities** and then test whether those probabilities contain enough edge over betting markets to produce a robust betting strategy.

This repository is the cleaned-up version of that work. I refactored the original notebook into reusable Python modules, command-line workflows, reports, tests, and an experiment registry so I no longer have to execute one giant stateful notebook in the correct order.

## Current production model

My current primary production candidate is **Production v2**, which uses **46 leakage-safe prefight features** and blends two models:

- **55% CatBoost**
- **45% Logistic Regression**

Production v2 keeps the original 42-feature UFC model and adds four strictly pre-UFC Sherdog features:

- pre-UFC professional fight count
- pre-UFC win percentage
- pre-UFC finish rate
- pre-UFC recent-five win percentage

The Logistic model uses median imputation, standard scaling, and `LogisticRegression(max_iter=3000, random_state=42)`.

The CatBoost model uses:

- 420 iterations
- depth 5
- learning rate 0.03
- Logloss objective
- random seed 42

I evaluate everything chronologically with walk-forward validation rather than random train/test splits. My development period is 2020–2024, while 2025–2026 is treated as a later confirmation period.

I retain the original **42-feature Production v1** as a fallback/reference model instead of overwriting it.

## Current betting rules

The betting system that survived my tests uses:

- model confidence >= **0.60**
- estimated EV >= **0.10**
- **quarter Kelly** sizing
- maximum **3% of bankroll per fight**
- maximum **12.5% of bankroll per event**
- every bet on the same event is sized from the bankroll at the start of that event

One of the main lessons from this project is that a model can improve global metrics such as log loss or AUC while still make worse betting decisions. Because of that, I use betting performance as a final promotion gate for any model intended for wagering.

## Production v2 results

The four Pre-UFC features improved the probability model across both my development and later confirmation periods.

| Period | Model | Accuracy | Log Loss | Brier | AUC |
|---|---|---:|---:|---:|---:|
| 2020–2024 | Baseline 42 | 0.61302 | 0.65183 | 0.23007 | 0.66156 |
| 2020–2024 | Pre-UFC 46 | 0.62434 | 0.64865 | 0.22853 | 0.66853 |
| 2025–2026 | Baseline 42 | 0.65428 | 0.63730 | 0.22313 | 0.69187 |
| 2025–2026 | Pre-UFC 46 | 0.65090 | 0.63287 | 0.22109 | 0.69905 |

The probability improvements were unusually consistent: log loss and Brier score improved in **all seven evaluated years** from 2020 through 2026.

The locked betting backtest was also strong enough to justify promotion to Production v2:

| Period | Model | Bets | Win Rate | Flat ROI | Kelly ROI | Max Drawdown |
|---|---|---:|---:|---:|---:|---:|
| 2020–2024 | Baseline 42 | 289 | 57.44% | 10.37% | 6.53% | 24.61% |
| 2020–2024 | Pre-UFC 46 | 289 | 58.13% | 9.73% | 6.13% | 22.32% |
| 2025–2026 | Baseline 42 | 81 | 59.26% | 26.22% | 19.79% | 10.43% |
| 2025–2026 | Pre-UFC 46 | 83 | 63.86% | 36.55% | 24.38% | 16.95% |

These are historical backtests, not guarantees of future profit.

## Sherdog Pre-UFC data

I built a resumable Sherdog scraper and strict identity resolver to reconstruct fighter records before their UFC debut.

Current coverage:

- UFC fighter universe: **2,725**
- resolved Sherdog fighters: **2,530 (92.8%)**
- exact 0-day debut-date matches: **2,495**
- 1-day matches: **35**
- review cases: **195**
- scraper errors: **0**
- strict pre-UFC professional fight-history rows: **33,845**

I intentionally leave unresolved or date-mismatched profiles out rather than forcing questionable identity matches.

## What is in this repository

```text
config/       # production settings
data/         # local input location; only documentation is tracked
external/     # scraper provenance and dependency boundary
models/       # portable metadata and model cards; weights stay local
reports/      # historical evidence, summaries and integration audit
scripts/      # history, prediction, settlement and research entry points
src/ufc_ai/   # reusable Python package
tests/        # offline regression tests
```

Original notebooks, caches and thematic research workflows remain in the source
archive; they are not shipped in this cleaned repository.

## Main research areas

Over the last several weeks I tested a large number of ideas, including:

- historical UFCStats features
- Elo ratings
- age, height, and reach
- striking/wrestling rates and defense
- recent-three-fight form
- strength of schedule
- CatBoost / Logistic ensembles
- alternative CatBoost hyperparameters
- XGBoost challengers and veto systems
- residual neural networks and stacking
- stance and matchup context
- fight-night weight / rehydration
- betting-optimized training objectives
- MMA Decisions robbery/media information
- media-adjusted Elo and media-history state
- Sherdog pre-UFC professional records
- home-field / same-country event advantage

I kept experiments that produced stable out-of-sample improvements and rejected ideas that looked attractive but failed later validation or betting tests. I document both the successful and failed work because the failures are useful evidence, not wasted work.

## Some ideas that did not make production

I deliberately rejected several ideas after testing them:

- stance/context features
- momentum/durability expansions
- fight-night weight and rehydration features
- profit-weighted training
- residual neural networks
- leakage-safe stacking
- XGBoost challenger/veto logic
- robbery-aware sample weighting
- media-adjusted Elo
- media-history features
- home-field advantage

A particularly useful example was the media-history experiment. It slightly improved global probability metrics, but the locked betting strategy became substantially worse, so I rejected it for production.

## Installation and tests

Use Python 3.12 for the pinned development environment:

```bash
python -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip install --no-build-isolation --no-deps -e .
python -m pip check
python -m pytest --disable-socket -q
```

See [development setup](DEVELOPMENT.md) for CI, dependency updates and validation
limits. Tests use synthetic fixtures and require no private data or model files.

## Prediction and settlement

Supply the trusted local weights and CSVs described in the [model cards](models/README.md)
and [orchestration guide](scripts/update_and_predict.md). Their archive-member
checksums are documented; neither weights nor raw datasets are fetched by setup.

```bash
# Local preflight only; no model loading or network requests:
python scripts/update_and_predict.py --project-root . --check-only
# Use existing local history; fetch currently listed cards and odds:
python scripts/update_and_predict.py --project-root . --skip-history
# Settle an unchanged saved snapshot:
python scripts/settle_picks.py --predictions reports/v21_predictions/RUN/predictions_v21.csv
```

Replace `RUN` with the generated run directory. V2 is the orchestration default;
`--experimental-v21` opts into the regional candidate and requires both bundles.
The notebook entry point retains its legacy V2.1 preference when artifacts exist;
pass `prefer_v21=False` there for V2. No models are retrained by prediction.
`--no-odds` disables quotes but still fetches cards. For a history refresh, follow
[update_history.md](scripts/update_history.md) and provide the checked snapshot.
[Settlement](scripts/settle_picks.md) supports `--events-json scoreboard.json` for
offline result input; unresolved fights never become losses.

The six-outcome distribution validator is independent of model inference:

```bash
python -m ufc_ai.joint predictions.csv --schema live
```

## Research training and evaluation

`python scripts/train_production.py` and `python scripts/evaluate_production.py`
require the local `data/training_data_with_odds.csv` with the full production
feature schema. They write legacy model/report filenames and do not recreate the
versioned frozen V2/V2.1 bundles or their exact training-row selection. Keep new
training artifacts separate from the trusted saved bundles.

## Results update — 11 October 2026

See the [latest results report](reports/results/2026-10-11/UFC_Ergebnisbericht.md) and [aggregate period summary](reports/results/2026-10-11/period_summary.csv) for the last three cards, 2026, and the period after the saved model's training cutoff (29 August 2026).

This update evaluates the available **42-feature Production v1/beta artifacts**, not the 46-feature Sherdog Production v2 described above. It separates saved pre-event picks, retrospective reconstructions and archived yearly walk-forward predictions. The P&L totals are incomplete simulations because 58 potentially eligible fights lack odds in 2026, including one after the cutoff. Individual probability ledgers and raw supporting data are not published in this update.

## Production v2 follow-up — updated 22 October 2026

The Production v2 follow-up has now been expanded with automatic BestFightOdds event mapping, a larger historical moneyline sample, a locked V1-vs-V2 post-cutoff comparison, and a fresh upcoming-card inference run.

Key historical results:

- 2026 prediction accuracy: **275 / 425 (64.71%)**
- Brier score: **0.2261**
- Log loss: **0.6439**
- After the 29 August training cutoff: **44 / 65 correct (67.69%)**
- BestFightOdds mapping: **28 / 34 events resolved**
- Both-side moneyline coverage: **286 / 429 fights (66.7%)**
- 2026 best-available backtest: **11-5, +1,469.15 simulated P&L**
- 2026 robust-median backtest: **9-5, +938.05 simulated P&L**
- Post-cutoff best-available sample: **2-1, +66.98**
- Post-cutoff robust-median sample: **1-1, -142.70**

A locked V1-vs-V2 comparison on 37 common stored post-cutoff predictions gave V2 slightly better predictive metrics:

- Accuracy: **54.05% -> 56.76%**
- Brier: **0.2692 -> 0.2652**
- Log loss: **0.7432 -> 0.7316**

V1 nevertheless produced the stronger betting result in this very small common sample because small probability-calibration differences changed which fights crossed the fixed EV threshold.

A fresh Production v2 run on 22 October produced **65 picks across six upcoming cards** without retraining. The local fight-history snapshot used by that run still ends on **3 October 2026**.

At the time of the October report, the live runner had one policy inconsistency: it can display `BET — REVIEW DATA` on low-data fights even when one fighter has fewer than five prior UFC fights. Those review bets are not considered qualifying bets under the locked historical betting policy and that historical output should not be treated as policy-compliant. The current runner checks both prior-fight counts when provided and gives review-data rows zero simulated stake; this integration did not rerun the October snapshot.

See the full follow-up report:

[`reports/results/2026-10-11/production_v2_2026_update.md`](reports/results/2026-10-11/production_v2_2026_update.md)


## Home-field advantage experiment — rejected

I tested whether fighting in the same country as the event adds predictive value beyond Production v2. The clean final test froze the existing V2 probability and learned only a single chronological home logit offset, so neutral fights were mathematically unchanged.

Across 238 walk-forward fights, the home-offset challenger slightly worsened accuracy, Brier score and log loss. On 108 unique-home fights it also worsened all three metrics. The median learned home coefficient was very small (+0.0115) and was positive in only 63% of chronological folds. A later-half slice showed mild probability-metric improvement, but the full out-of-sample evidence was not robust enough for promotion.

Decision: **REJECT**. Production v2 remains unchanged.

See: [`reports/experiments/home_field_advantage_2026.md`](reports/experiments/home_field_advantage_2026.md)

## Detailed report

For the complete technical history—including data engineering, leakage prevention, important experiments, betting results, bugs, rejected ideas, and the current roadmap—see:

[`reports/UFC_AI_PROJECT_REPORT.md`](reports/UFC_AI_PROJECT_REPORT.md)

I also keep a machine-readable experiment registry here:

[`reports/EXPERIMENT_REGISTRY.csv`](reports/EXPERIMENT_REGISTRY.csv)

## Integration completed — 20 November 2026

The finite [integration plan](reports/import_2026_11_13/README.md) covers 16 commits:
regional validation, portable metadata, comparison provenance, conditional-method
probability checks, history updates, live features/odds, orchestration, settlement,
CI and documentation. See the [final audit](reports/import_2026_11_13/final_audit.md)
for completion evidence and remaining research limitations.

V2.1 remains experimental. V2 reports 8,705 training rows versus V2.1's 8,683;
the supplied data has 22 duplicate excess rows, but exact fitted row selection
still needs a manifest. No isolated regional-feature advantage is established.
Historical metrics above were not rerun during integration, and there is no new
live prediction or profitability claim. Further research would require explicitly
chosen work rather than additional automatic commits.

## Disclaimer

This is a personal machine-learning and quantitative-research project. The betting results are historical simulations and should not be interpreted as guaranteed future returns or financial advice.
