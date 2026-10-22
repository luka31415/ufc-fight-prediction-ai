# Production v2 — 2026 follow-up evaluation

Updated: 22 October 2026

This report documents a follow-up evaluation of the **46-feature Production v2 winner model**, expanded historical BestFightOdds coverage, a locked V1-vs-V2 post-cutoff comparison, and a fresh upcoming-fight inference run.

## Model

Production v2 uses:

- 42 UFC prefight features
- 4 frozen Sherdog pre-UFC features
- 55% CatBoost
- 45% Logistic Regression

The saved production model has a training cutoff of **29 August 2026**.

For the 2026 historical evaluation, fights through the cutoff were evaluated with chronological walk-forward retraining. Fights after the cutoff used the frozen Production v2 artifacts.

## Predictive performance

| Period | Fights | Decided | Correct | Accuracy | Brier | Log Loss | Avg. confidence | >=60% fights | >=60% accuracy | >=65% fights | >=65% accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Last available cards | 26 | 26 | 22 | **84.62%** | 0.1947 | 0.5785 | 0.6189 | 17 | 76.47% | 8 | 87.50% |
| 2026 | 429 | 425 | 275 | **64.71%** | 0.2261 | 0.6439 | 0.6190 | 222 | 70.72% | 141 | 75.18% |
| After 2026-08-29 | 65 | 65 | 44 | **67.69%** | 0.2356 | 0.6672 | 0.6233 | 41 | 63.41% | 23 | 69.57% |

The "last available cards" slice contains the two cards present in the local result universe for the requested last-three-card window:

- 2026-09-26 — UFC Fight Night: Rosas Jr. vs. Barcelos: **11/12**
- 2026-10-03 — UFC 332: Silva vs. Wang: **11/14**

The 10 October card was not present in this reconstructed V2 result universe, so the 26-fight slice should not be interpreted as a complete three-card sample.

## Historical moneyline source

The first historical odds attempt used ESPN, but it produced no usable prices. The backtest was therefore switched to archived **BestFightOdds** event pages.

A parser self-test on UFC 300 successfully recovered real moneyline quotes for multiple sportsbooks. Archived BestFightOdds values are treated as **displayed historical prices**, not guaranteed closing lines and not proof that a particular price was executable at a specific timestamp.

## BestFightOdds event mapping progress

The original map covered only 7 of 34 2026 events. The automatic finder was then expanded in two stages.

### V8

- 22 / 34 events resolved
- 276 / 429 fights on mapped events
- 225 / 429 fights with both moneyline sides available
- 1,903 raw sportsbook quotes

### V9

Targeted full-card searching resolved six more events:

- UFC Fight Night: Sterling vs. Zalal
- UFC Fight Night: Du Plessis vs. Usman
- UFC Fight Night: Hernandez vs. Rodrigues
- UFC Fight Night: Nurmagomedov vs. Song
- UFC 331: Van vs. Pantoja 2
- UFC Fight Night: Rosas Jr. vs. Barcelos

Final V9 event coverage:

- **28 / 34 events resolved (82.4%)**
- **351 / 429 ledger fights on mapped events**
- **318 / 429 fights with at least one side priced (74.1%)**
- **286 / 429 fights with both sides priced (66.7%)**
- **2,423 raw sportsbook quotes**

All five post-cutoff events in the 65-fight Production v2 evaluation universe are mapped.

Six earlier Fight Night cards remain unresolved/review-only:

- Bautista vs. Oliveira
- Strickland vs. Hernandez
- Moreno vs. Kavanagh
- Adesanya vs. Pyfer
- Burns vs. Malott
- Allen vs. Costa

## Locked betting rules

The historical betting tests use:

- model confidence >= 0.60
- estimated EV >= 0.10
- both fighters >= 5 prior UFC fights
- quarter Kelly sizing
- max 3% bankroll per fight
- max 12.5% bankroll per event
- 10,000 starting bankroll

Two archived-price scenarios are evaluated:

- **BEST_AVAILABLE** — best displayed American price across recognized books
- **ROBUST_MEDIAN** — median displayed American price across the available books

## V9 historical betting result

| Scenario | Period | Bets | W-L | Stake | Net P&L | ROI on stake | Ending bankroll | Return | Max drawdown | Unknown potential bets |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Best available | 2026 | 16 | **11-5** | 5,192.89 | **+1,469.15** | **28.29%** | 11,469.15 | **+14.69%** | 5.91% | 26 |
| Robust median | 2026 | 14 | **9-5** | 4,472.67 | **+938.05** | **20.97%** | 10,938.05 | **+9.38%** | 5.91% | 26 |
| Best available | After 2026-08-29 | 3 | **2-1** | 882.00 | **+66.98** | **7.59%** | 10,066.98 | **+0.67%** | 3.00% | 3 |
| Robust median | After 2026-08-29 | 2 | **1-1** | 591.00 | **-142.70** | **-24.15%** | 9,857.30 | **-1.43%** | 3.00% | 3 |

The three remaining post-cutoff potential bets without archived BFO moneylines are all from UFC 332:

- Ismail Naurdiev over Marvin Vettori
- Alexander Hernandez over Rafael Dos Anjos
- Mick Parkin over Johnny Walker

The archived UFC 332 page did not expose usable moneyline rows for those three targets, so they remain unknown rather than being imputed.

The post-cutoff sample is still too small to establish profitability. In particular, the difference between best-available and median-price results shows that the current P&L is sensitive to price selection.

## Locked V1 vs. V2 post-cutoff comparison

A direct comparison was run on fights for which stored V1 predictions and V2 predictions were both available, using the **same fights, same BFO prices, same history filter and same betting rules**.

V1 coverage was 37 of the 65 post-cutoff V2 fights. The selected V1 source rows were classified as **LIVE_OR_SAVED**.

### Predictive metrics on the 37 common fights

| Model | Accuracy | Brier | Log Loss |
|---|---:|---:|---:|
| V1 | 54.05% | 0.2692 | 0.7432 |
| V2 | **56.76%** | **0.2652** | **0.7316** |

V2 was slightly better on all three predictive metrics.

The models selected the same winner on **36 of 37 fights**. The only disagreement was Tim Elliott vs. Edgar Chairez, where V2 selected Elliott and the result favored V2.

### Betting on the same 37-fight universe

| Model | Odds | Bets | W-L | Stake | Net P&L | ROI |
|---|---|---:|---:|---:|---:|---:|
| V1 | Best available | 4 | **3-1** | 1,199.14 | **+363.50** | **30.31%** |
| V2 | Best available | 3 | **2-1** | 882.00 | **+66.98** | **7.59%** |
| V1 | Robust median | 3 | **2-1** | 899.57 | **+147.64** | **16.41%** |
| V2 | Robust median | 2 | **1-1** | 591.00 | **-142.70** | **-24.15%** |

The betting difference is mostly a calibration/threshold effect rather than a difference in picked winners. For example, V1 assigned Brandon Moreno 63.03% at -105 and placed a bet, while V2 assigned 53.95% and did not pass the EV threshold; Moreno won.

Because only 37 of 65 post-cutoff fights have matched stored V1 predictions, this is not yet a complete V1-vs-V2 comparison.

## Fresh upcoming Production v2 snapshot — 22 October 2026

The locked Production v2 runner was executed without retraining against the currently scheduled upcoming UFC cards.

Run summary:

- **65 picks**
- **6 cards**
- model version: **v2_preufc**
- model training cutoff: **2026-08-29**
- local fight-history data available through: **2026-10-03**

Upcoming cards in the snapshot:

- 2026-10-24 — UFC 333: Volkanovski vs. Evloev
- 2026-10-31 — UFC Fight Night: Moicano vs. Nolan
- 2026-11-07 — UFC Fight Night: Bonfim vs. Brady
- 2026-11-14 — UFC 334: Gane vs. Hokit
- 2026-11-21 — UFC Fight Night: Prochazka vs. Stirling
- 2026-12-12 — UFC 335: Oliveira vs. Lopes

Examples of higher-confidence predictions with normal UFC data quality include:

- Luana Santos over Yana Santos — **80.19%**
- Chris Duncan over Drew Dober — **75.19%**
- Francis Marshall over Gaston Bolanos — **72.81%**
- Ikram Aliskerov over Jared Cannonier — **71.48%**
- Brandon Moreno over Charles Johnson — **67.14%**
- Terrance McKinney over Jim Miller — **66.27%**
- Navajo Stirling over Jiri Prochazka — **63.48%**
- Tatiana Suarez over Virna Jandiroba — **62.34%**
- Brian Ortega over Dan Hooker — **61.65%**
- Uros Medic over Kevin Holland — **61.43%**
- Charles Radtke over Stephen Thompson — **61.26%**
- Maycee Barber over Carli Judice — **60.75%**
- Piera Rodriguez over Talita Alencar — **60.59%**

For UFC 333 specifically, the model currently has:

- Movsar Evloev over Alexander Volkanovski — **56.97%**
- Merab Dvalishvili over Petr Yan — **55.78%**
- Daniel Santos over Bolaji Oki — **59.88%**

### Live-runner caveat

The current live runner can label low-data fights as `BET — REVIEW DATA` based on confidence and EV even when one fighter has fewer than five prior UFC fights.

For UFC 333, the four review bets were:

- Colby Thicknesse vs. Asaf Chopurov — 3 / 0 prior UFC fights
- Abubakar Vagaev vs. Jacob Malkoun — 1 / 9
- Abus Magomedov vs. Cam Rowston — 8 / 3
- Alexander Volkov vs. Rizvan Kuniev — 19 / 3

Therefore **none of those four satisfies the locked historical >=5-prior-UFC-fights rule for both fighters**. Under the locked betting policy, the current UFC 333 snapshot has **zero qualifying bets**.

This inconsistency should be fixed in the live runner before live betting outputs are treated as policy-compliant.

## Interpretation

Production v2 remains slightly stronger than V1 on the currently matched post-cutoff predictive sample, but the betting sample is still much too small for a profitability claim.

The expanded BestFightOdds mapping materially improves historical evaluation quality, especially after the training cutoff, but 26 full-year potential bets and three post-cutoff potential bets still lack prices.

The next engineering priorities are:

1. enforce the >=5-prior-UFC-fights rule directly in the live runner,
2. update local UFC fight history through at least 10 October 2026,
3. rerun the upcoming-card snapshot,
4. expand the stored V1 post-cutoff comparison beyond the current 37 common fights.

## Local generated files

Recent local work generated files including:

- `historical_method_event_map_v9_2026_targeted.csv`
- `v2_historical_moneyline_bfo_quotes_v9.csv`
- `v2_historical_moneyline_bfo_prices_v9.csv`
- `v2_betting_summary_bfo_v9.csv`
- `v1_vs_v2_post_cutoff_locked_summary.csv`
- `v1_vs_v2_post_cutoff_locked_fight_comparison.csv`
- `v1_vs_v2_post_cutoff_locked_bets.csv`
- `v1_post_cutoff_prediction_sources_used.csv`
- fresh `reports/v2_predictions/.../predictions_v2.csv`
- fresh `reports/v2_predictions/.../upcoming_v2_compact.csv`

The large raw ledgers, quote caches and generated local data are not published in this report commit.

## Disclaimer

This is a historical and forward-looking research simulation. It is not evidence of guaranteed future profit and is not financial advice.
