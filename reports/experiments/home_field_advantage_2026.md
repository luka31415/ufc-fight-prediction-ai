# Home-field advantage experiment — rejected

Date: 23 October 2026

## Hypothesis

Test whether a fighter competing in the same country as the UFC event receives a measurable predictive advantage beyond Production v2.

The candidate feature was defined symmetrically as:

```text
DIFF_HOME_ADVANTAGE = HOME_A - HOME_B
```

with:

- `+1` = only Fighter A is home
- `0` = both or neither fighter is home
- `-1` = only Fighter B is home

Home status was based on fighter country versus event country.

## Geography coverage

The 2026 research ledger contained 429 fights.

Country-resolution work produced:

- 593 unique fighters in the 2026 universe
- 494 / 593 fighter countries resolved (83.3%)
- 308 / 429 fights with both fighter countries available (71.8%)
- event-country coverage: 100%

The geography-complete research sample contained 305 decided fights, including 137 fights where exactly one fighter was competing at home.

## Initial residual check

Among the 137 unique-home fights:

- actual home win rate: **54.01%**
- Production v2 expected home win rate: **49.30%**
- residual: **+4.72 percentage points**
- bootstrap 95% CI: **[-3.63%, +12.97%]**

The interval included zero, so this was treated as a possible but unconfirmed signal.

A naive residual probability shift changed Brier score on the home sample from:

- Production v2: **0.24268**
- shifted diagnostic: **0.24046**

This diagnostic was not used for promotion because it was in-sample.

## First walk-forward challenger

An initial chronological challenger recalibrated Production v2 using both its logit and home advantage.

This test was rejected as the final decision test because it also recalibrated neutral fights, so it did not isolate the home feature cleanly.

Across 238 walk-forward fights:

- accuracy: **65.55% -> 59.66%**
- Brier: **0.23190 -> 0.23651**
- log loss: **0.65715 -> 0.66898**

The test motivated a stricter frozen-v2 experiment.

## Final frozen-v2 test

The final test kept Production v2 completely fixed and learned only one parameter:

```text
logit(P_new)
    =
logit(P_v2)
    +
beta * DIFF_HOME_ADVANTAGE
```

This guarantees that neutral fights remain exactly unchanged.

### Walk-forward coverage

- evaluated fights: **238**
- evaluated events: **27**
- unique-home fights: **108**
- neutral/both-home fights: **130**
- neutral maximum probability shift: **0.000000000000**

### All walk-forward fights

| Metric | Frozen V2 | Home offset | Delta |
|---|---:|---:|---:|
| Accuracy | **65.55%** | 64.29% | -1.26 pp |
| Brier | **0.231896** | 0.232642 | +0.000746 |
| Log loss | **0.657151** | 0.658858 | +0.001707 |

### Unique-home fights only

| Metric | Frozen V2 | Home offset | Delta |
|---|---:|---:|---:|
| Accuracy | **57.41%** | 54.63% | -2.78 pp |
| Brier | **0.254422** | 0.256067 | +0.001645 |
| Log loss | **0.704983** | 0.708743 | +0.003761 |

### Later-half diagnostic

The later half was mildly better on probability metrics, but not strongly enough to override the full walk-forward result:

- late-half Brier: 0.223611 -> **0.221721**
- late-half log loss: 0.639731 -> **0.636035**
- late-half-home Brier: 0.245397 -> **0.241083**
- late-half-home log loss: 0.685060 -> **0.676623**

Accuracy still did not improve consistently.

## Bootstrap uncertainty

Challenger minus frozen-v2 deltas:

### All fights

- Brier delta: **+0.000765**
- 95% CI: **[-0.002084, +0.003604]**
- log-loss delta: **+0.001682**
- 95% CI: **[-0.004513, +0.008037]**

### Unique-home fights

- Brier delta: **+0.001663**
- 95% CI: **[-0.004475, +0.008091]**
- log-loss delta: **+0.003810**
- 95% CI: **[-0.009806, +0.017734]**

No robust improvement was established.

## Learned home coefficient

Across 27 chronological folds:

- mean beta: **+0.02444**
- median beta: **+0.01152**
- range: **-0.30315 to +0.23188**
- positive in **63.0%** of folds

The median beta corresponds to only about a **+0.29 percentage-point** probability shift for a 50/50 home fighter.

The sign and magnitude were not stable enough for production use.

## Decision

**REJECT.**

Do not add `DIFF_HOME_ADVANTAGE` to Production v2 based on the current evidence.

Reasons:

1. the clean frozen-v2 walk-forward test worsened full-sample accuracy, Brier and log loss;
2. the unique-home subset also worsened;
3. bootstrap intervals include zero;
4. the learned beta is small and unstable across folds;
5. the mild later-half improvement is not sufficient to justify promotion.

Production v2 remains unchanged.

## Local research artifacts

The local experiment generated:

- `v2_home_advantage_research_ledger.csv`
- `v2_home_advantage_research_summary.csv`
- `v2_home_advantage_by_country.csv`
- `v2_vs_home_challenger_predictions.csv`
- `v2_vs_home_challenger_summary.csv`
- `v2_vs_home_challenger_folds.csv`
- `v2_home_offset_predictions.csv`
- `v2_home_offset_summary.csv`
- `v2_home_offset_folds.csv`

These local generated-data files are not required for the production model and are not committed here.
