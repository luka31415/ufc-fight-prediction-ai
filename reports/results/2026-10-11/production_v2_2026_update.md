# Production v2 — 2026 follow-up evaluation

Date: 11 October 2026

This report documents a follow-up evaluation of the **46-feature Production v2 winner model** and a limited historical moneyline backtest using archived BestFightOdds pages.

## Model

Production v2 uses:

- 42 UFC prefight features
- 4 frozen Sherdog pre-UFC features
- 55% CatBoost
- 45% Logistic Regression

The saved production model has a training cutoff of **29 August 2026**.

For the 2026 evaluation, fights through the cutoff were evaluated with chronological walk-forward retraining. Fights after the cutoff used the frozen Production v2 artifacts.

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

The first historical odds attempt used ESPN, but it produced no usable prices:

- 429 fights checked
- 411 matched fights had missing athlete IDs
- 18 fights were not matched
- 0 priced fights

The backtest was therefore switched to archived **BestFightOdds** event pages.

A parser self-test on UFC 300 successfully recovered real moneyline quotes for Alex Pereira, Jamahal Hill, Yan Xiaonan and Zhang Weili from multiple sportsbooks, including FanDuel, Caesars, BetRivers, BetWay, Unibet and BetMGM.

## BestFightOdds coverage in the 2026 test

The existing validated BFO event map covered only:

- **7 / 34 events**
- **81 / 429 ledger fights** on mapped events
- **56 / 429 fights with both moneyline sides available** (13.1%)
- **472 raw sportsbook quotes**

Books observed in the 2026 scrape:

| Sportsbook | Quotes |
|---|---:|
| Caesars | 118 |
| BetWay | 118 |
| FanDuel | 116 |
| BetRivers | 116 |
| Unibet | 4 |

Mapped 2026 cards:

| Date | Event | Fights | Fights with both sides | Coverage |
|---|---|---:|---:|---:|
| 2026-01-24 | UFC 324: Gaethje vs. Pimblett | 11 | 2 | 18.2% |
| 2026-03-07 | UFC 326: Holloway vs. Oliveira 2 | 12 | 2 | 16.7% |
| 2026-04-11 | UFC 327: Prochazka vs. Ulberg | 12 | 10 | 83.3% |
| 2026-05-09 | UFC 328: Chimaev vs. Strickland | 13 | 13 | 100.0% |
| 2026-06-14 | UFC Freedom 250 | 7 | 6 | 85.7% |
| 2026-07-11 | UFC 329: McGregor vs. Holloway 2 | 14 | 12 | 85.7% |
| 2026-08-15 | UFC 330: Makhachev vs. Machado Garry | 12 | 11 | 91.7% |

Most Fight Night cards were not yet mapped to BestFightOdds, which is the main remaining coverage problem.

## Betting rules

The same locked betting rules were used:

- model confidence >= 0.60
- estimated EV >= 0.10
- both fighters >= 5 prior UFC fights
- quarter Kelly sizing
- max 3% bankroll per fight
- max 12.5% bankroll per event
- 10,000 starting bankroll

Two archived-price scenarios were evaluated:

- **BEST_AVAILABLE** — best displayed American price across recognized books
- **ROBUST_MEDIAN** — median displayed American price across the available books

These BestFightOdds values are treated as **archived displayed prices**, not guaranteed closing lines or proof that a particular price was executable at a specific timestamp.

## Limited 2026 betting result

| Scenario | Period | Priced fights | Bets | W-L | Stake | Net P&L | ROI on stake | Ending bankroll | Return | Max drawdown |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Best available | 2026 | 59 | 5 | **4-1** | 1,566.48 | **+1,066.89** | **68.11%** | 11,066.89 | **+10.67%** | 3.00% |
| Robust median | 2026 | 59 | 5 | **4-1** | 1,563.25 | **+963.43** | **61.63%** | 10,963.43 | **+9.63%** | 3.00% |

There were **no priced fights after the 29 August training cutoff**, so this odds dataset does not yet support a post-cutoff Production v2 betting evaluation.

## Interpretation

The prediction results are substantially more informative than the current betting result because the winner evaluation covers 425 decided fights, while the moneyline backtest is based on only five qualifying bets.

The 4-1 result is encouraging, and the fact that both best-available and median-price scenarios remain profitable reduces the chance that the result is purely a best-book artifact. However, **five bets and 13.1% fight-level odds coverage are far too small to establish durable profitability**.

The next data task is to resolve the missing 2026 BestFightOdds event URLs, especially Fight Night cards, before drawing stronger conclusions from the betting backtest.

## Files generated locally

The local evaluation generated:

- `v2_fight_ledger.csv`
- `predictive_metrics_v2.csv`
- `period_summary_v2.csv`
- `v2_historical_moneyline_bfo_quotes.csv`
- `v2_historical_moneyline_bfo_prices.csv`
- `v2_fight_ledger_bfo_moneyline.csv`
- `v2_betting_summary_bfo.csv`
- `v2_event_betting_bfo.csv`

The large raw ledgers and local generated-data caches are not published in this commit.

## Disclaimer

This is a historical research simulation. It is not evidence of guaranteed future profit and is not financial advice.
