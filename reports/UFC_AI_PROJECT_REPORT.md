# UFC Fight Prediction & Betting AI — Research and Engineering Report

## Introduction

I have been working on this project for several weeks. What started as one very long Jupyter notebook gradually became a much larger research project around UFC fight prediction, probability calibration, data engineering, betting backtests, external data collection, and model experimentation.

My original goal was simple: predict the winner of a UFC fight. Very quickly, however, I realized that raw winner accuracy is not enough. If I want to use a model for betting, I need probabilities that are reasonably calibrated, I need to compare those probabilities to market odds, and I need to test whether any apparent edge survives chronological out-of-sample evaluation.

The project therefore evolved into two related systems:

1. a fight-probability model;
2. a betting layer that converts those probabilities into filtered, bankroll-sized wagers.

This report documents the full development process: the data pipeline, leakage prevention, feature engineering, models I tested, betting experiments, external data projects, ideas that failed, bugs I found, and the current production architecture.

---

## 1. Research philosophy

The most important rule I developed during this project is that every feature must be available before the fight being predicted. UFC datasets are particularly easy to leak because statistics are stored as completed-fight records, and cumulative fighter summaries can accidentally include the fight being predicted.

I therefore build fighter state chronologically. For each fight, I first take the fighter's state from previous fights, create the prefight feature row, and only then update that state with the current result and statistics.

The same idea applies to Elo, recent form, strength of schedule, media-history experiments, and the pre-UFC record branch.

I also avoid random train/test splits for final evaluation. My mature validation procedure is walk-forward by year: train on all years before a validation year, predict that year, then move forward. I use 2020–2024 as the main development period and 2025–2026 as a later confirmation period.

My model-selection priorities are:

1. lower log loss;
2. lower Brier score;
3. higher ROC AUC;
4. accuracy as a secondary metric;
5. betting performance as the final gate for any model intended for wagering.

A key lesson from this project is that a model can improve global predictive metrics and still make worse betting decisions.

---

## 2. Main data sources

### UFCStats

UFCStats is the core source for fight results, fighter information, events, and detailed round statistics.

The raw fight-result history contains about 8,885 fights. After removing draws/no-contests from winner-model training, the decisive matchup dataset contains 8,705 fights.

The round-statistics table contains more than 41,000 round rows. I aggregate those into fighter-fight records and then into chronological prefight fighter state.

### Fighter metadata

I use available fighter metadata such as date of birth, height, reach, and stance. Age, height, and reach turned out to be much more useful than stance.

### Betting odds

I matched historical moneyline odds to the training database so I could compare model probabilities against market prices and simulate betting strategies.

### California / Bellator fight-night weights

I collected commission/published fight-night weight observations in order to investigate rehydration and cage-weight effects. The descriptive data was interesting, but the resulting features did not improve the production model reliably.

### MMA Decisions

I built a direct scraper for MMA Decisions media scorecards to investigate whether controversial official decisions should be treated differently in training or Elo updates.

### Sherdog

My newest research branch uses Sherdog professional histories to recover a fighter's record before entering the UFC. This is aimed at the weakest-information case in the current system: UFC debutants and fighters with very little UFC history.

---

## 3. Core data pipeline

The raw fight result table is cleaned, linked to event dates, sorted chronologically, and expanded into fighter-level histories.

I create one prefight snapshot per fighter before every fight. These snapshots contain only historical information.

I then convert each matchup into Fighter A minus Fighter B differences. To avoid learning source-order artifacts, I randomized matchup orientation with a fixed seed. Of 8,705 decisive fights, 4,380 were flipped. The resulting A-win target is almost perfectly balanced.

The main intermediate datasets I created during development include:

- cleaned fight results;
- fighter-fight statistics;
- fighter chronological history;
- leakage-safe prefight features;
- randomized matchup training data;
- versions augmented with Elo, biography, rates, recent form, strength of schedule, odds, media information, and experimental features.

---

## 4. Early baseline

My first serious model was a logistic regression on a relatively small historical feature set.

The early 16-feature baseline achieved approximately:

| Period | Accuracy | Log Loss | Brier | AUC |
|---|---:|---:|---:|---:|
| 2024 validation | 0.6004 | 0.6620 | 0.2348 | 0.6440 |
| 2025+ test | 0.5957 | 0.6632 | 0.2355 | 0.6363 |

This was useful as a reference point, but clearly not strong enough.

---

## 5. Elo

I added a chronological Elo system to represent fighter strength.

Elo by itself did not immediately transform performance in the early model. However, I retained it because it represents a different concept from raw fight statistics and later became useful inside the mature feature set.

One lesson here was that a feature can be weak in an early under-specified model yet still contribute when combined with better rate, recency, and opponent-quality features.

---

## 6. Age, height and reach

Adding physical/biographical matchup information produced one of the first clear improvements.

Approximate results after this step were:

| Period | Accuracy | Log Loss | AUC |
|---|---:|---:|---:|
| 2024 | 0.6140 | 0.6553 | 0.6537 |
| 2025+ | 0.6329 | 0.6436 | 0.6825 |

Age became particularly important. Height and reach also contributed, although reach coverage is incomplete for some fighters.

---

## 7. Rate and defensive features

Raw career averages are not always comparable because fighters have different fight lengths and styles. I therefore added rate-based features, including significant strikes landed and absorbed per minute, takedowns landed and allowed per 15 minutes, submission attempts per 15, striking accuracy/defense, takedown accuracy/defense, and control share.

This was another strong improvement. Around this stage, later-period AUC moved into the high 0.68 range and log loss improved meaningfully.

These rate/defense features stayed in production.

---

## 8. Recent form

I created recent-three-fight features to capture current form rather than only career averages.

The recent bundle includes recent striking rates, wrestling rates, submission attempts, control share, win rate, and number of available recent fights.

The improvements were small but coherent, including a modest reduction in log loss/Brier and an AUC gain. Because the signal was directionally consistent and leakage-safe, I kept it.

---

## 9. Strength of schedule

A fighter's statistics depend heavily on opponent quality. I therefore added opponent-Elo features:

- prior average opponent Elo;
- prior maximum opponent Elo;
- recent-three average opponent Elo.

This completed the current 42-feature production set and produced another meaningful improvement.

---

## 10. Current production feature set

The current model uses 42 Fighter-A-minus-Fighter-B prefight features. They cover:

### Career record

- prior fights;
- wins;
- losses;
- win percentage.

### Historical fight statistics

- knockdowns;
- significant strikes landed/attempted;
- total strikes landed/attempted;
- takedowns landed/attempted;
- submission attempts;
- control time;
- striking accuracy;
- takedown accuracy.

### Context

- days since last fight;
- Elo;
- UFC debut indicator/experience context;
- age;
- height;
- reach.

### Rate/defense

- significant strikes landed per minute;
- significant strikes absorbed per minute;
- takedowns landed per 15;
- takedowns allowed per 15;
- submissions per 15;
- striking accuracy;
- striking defense;
- takedown accuracy;
- takedown defense;
- control share.

### Recent-three form

- recent significant strikes landed/absorbed per minute;
- recent takedowns landed/allowed per 15;
- recent submission attempts per 15;
- recent control share;
- recent win rate;
- recent fight count.

### Strength of schedule

- average prior opponent Elo;
- maximum prior opponent Elo;
- recent-three average opponent Elo.

---

## 11. Logistic regression and CatBoost

Logistic regression remained useful because it is stable, simple, and generally well behaved for probabilities after scaling.

My locked logistic pipeline is:

- median imputation;
- StandardScaler;
- LogisticRegression(max_iter=3000, random_state=42).

CatBoost captured nonlinear interactions better. My locked CatBoost settings are:

- 420 iterations;
- depth 5;
- learning rate 0.03;
- Logloss objective;
- random seed 42.

Rather than replacing logistic regression, I found the best production approach was to blend them.

---

## 12. Production ensemble

My current production probability is:

**55% CatBoost + 45% Logistic Regression**.

The exact same architecture is used for walk-forward comparisons so challengers are tested against a consistent baseline.

Representative current walk-forward performance is approximately:

| Period | Accuracy | Log Loss | Brier | AUC |
|---|---:|---:|---:|---:|
| 2020–2024 | 0.6130 | 0.6518 | 0.2301 | 0.6616 |
| 2025–2026 | 0.6543 | 0.6373 | 0.2231 | 0.6919 |

The exact baseline can vary slightly between experiments depending on the exact dataset cutoff, which is why I compare baseline and challenger inside the same code run.

---

## 13. Betting system

Initially I looked at betting every model pick. That produced some interesting underdog results but was too broad.

I then moved toward selective betting based on probability edge.

The locked betting rules are:

- confidence >= 0.60;
- estimated EV >= 0.10;
- quarter Kelly sizing;
- maximum 3% bankroll per fight;
- maximum 12.5% bankroll per event;
- all bets on the same event are sized from the bankroll at the start of that event.

This event-start sizing rule matters because otherwise later bets on a card can unrealistically compound on results that have not occurred yet.

A representative later-period baseline backtest produced:

- 81 bets;
- 48 wins;
- 59.26% win rate;
- about 29.80% flat-stake ROI;
- ending bankroll around $16,379.65 from $10,000 in that run;
- about 10.43% maximum drawdown.

These are historical simulations, not guarantees of future performance.

---

## 14. Momentum and durability experiment

I tested additional momentum/durability-style features. The idea was reasonable, but the probability improvements were too weak relative to the added complexity and some headline metrics worsened.

I rejected this branch for production.

---

## 15. Stance, division and contextual matchup features

I tested stance and broader contextual matchup bundles. Stance looked intuitively attractive, but the effect was weak and did not survive later validation strongly enough.

I rejected stance/context expansion rather than adding complexity for a tiny unstable gain.

---

## 16. Fight-night weight and rehydration

This became a fairly large side project.

I collected commission/published fight-night weight observations, matched fighters across sources, cleaned name collisions, and added Bellator observations to increase sample size.

I then tested estimated cage weight, rehydration percentage, prior personal rehydration behavior, and related variants.

The data itself was interesting, but the predictive experiments generally worsened development-period log loss or produced tiny later-period effects that were not robust.

I rejected rehydration as a production feature.

This was an important lesson: a variable can be physically meaningful and descriptively interesting without adding useful incremental predictive signal once the existing model already knows weight class, size, age, performance rates, and history.

---

## 17. Money-first / profit-weighted training

I investigated whether the model should be trained directly toward betting profitability rather than probability quality.

The problem is that the odds-covered dataset is smaller and market-specific, which creates a strong overfitting risk. The experiments did not show a sufficiently stable advantage.

I kept probability modeling and betting selection as separate stages.

---

## 18. Hyperparameter alternatives

I tested alternative model hyperparameters. None produced a robust enough improvement to justify replacing the simple locked configuration.

I therefore froze the current architecture rather than repeatedly tuning on the same later data.

---

## 19. Residual neural network

I built a residual MLP experiment in PyTorch. Walk-forward early stopping generally selected very few epochs, suggesting limited extra signal beyond the tabular ensemble.

Neural blending did not produce a convincing robust advantage. I rejected it for production.

---

## 20. Leakage-safe stacking

I also tested stacking with proper out-of-fold training to avoid leakage.

The methodology was valid, but the performance gain was not convincing enough. I rejected stacking rather than adding another model layer.

---

## 21. XGBoost challenger and veto logic

XGBoost was tested as both a challenger and a confirmation/veto model. I wanted to know whether agreement between models could identify safer bets or whether XGBoost could replace part of the production blend.

The improvements were not robust. I rejected both the challenger and veto approaches.

---

## 22. TD-stuffed / last-method branch

I investigated additional fight-context features involving takedown stuffing and last-fight method information. A candidate version was interesting enough to keep as a shadow research branch, but it did not earn promotion to the locked 42-feature model.

---

## 23. MMA Decisions / robbery project

This became one of the most detailed research branches.

### Motivation

Official decision labels are sometimes controversial. I wanted to test whether heavily disputed wins/losses should influence training less, whether media consensus should adjust Elo, or whether a fighter's historical relationship to media scorecards contains predictive information.

### Initial limited dataset

My first media dataset had incomplete historical coverage. Some early results looked interesting but were not reliable enough because of missing decisions.

### Direct MMA Decisions scraper

I built a direct scraper for thousands of MMA Decisions pages and parsed only the media-scorecard block, not fan votes.

The first parser failed a known sanity case: Khabib Nurmagomedov vs. Gleison Tibau. I expected six classified media cards with one favoring Khabib and five favoring Tibau. The parser initially classified none.

That failure prevented a long scrape and forced a parser redesign. The V3 parser then passed the sanity test exactly.

### Matching bug

A later experiment appeared to match only 147 clean media decisions to 8,705 training fights. This turned out to be a merge-column bug: I was using a post-merge `DATE` field instead of the correct MMA Decisions date (`DATE_x` / `MMA_DATE`).

After repairing date+pair matching, unique-pair fallback, and rematch chronology, I matched 3,097 clean media decisions to the training data.

### Continuous robbery weights

I downweighted disputed historical decisions while leaving the official target unchanged.

The full-V3 experiment produced a tiny development improvement, but 2025–2026 worsened on all priority metrics and changed picks were net negative.

I rejected robbery-aware sample weighting.

### Media-adjusted Elo

I tested whether media consensus should alter Elo updates. The effect was too inconsistent and later changed-pick performance was poor.

I rejected media-adjusted Elo.

### Media-history features

I then tried a different idea: do not modify the current fight label at all. Instead, let previous controversial decisions become part of a fighter's future state.

The strongest bundle, Media C, used recent media-adjusted form/residual information.

It improved global probability metrics:

- 2020–2024 log loss improved by about 0.00059;
- Brier improved by about 0.00032;
- AUC improved by about 0.00202;
- 2025–2026 also improved log loss, Brier and AUC.

This was the first robbery-derived feature idea that genuinely passed the predictive probability gate.

However, the betting test failed badly.

On 2025–2026, compared with the baseline:

- flat ROI fell from about 29.80% to 23.09%;
- ending bankroll fell from about $16,379.65 to $12,724.87;
- Kelly ROI fell substantially;
- max drawdown increased from about 10.43% to 23.38%.

This experiment taught me one of the most important lessons in the entire project: **better average probability metrics do not automatically mean better decisions in the high-edge betting tail**.

I rejected Media C for production and kept the 42-feature model unchanged.

---

## 24. Sherdog pre-UFC professional record

The current research direction is pre-UFC professional strength.

The problem I am trying to solve is straightforward: the current model becomes information-poor when one or both fighters have little UFC history. A debutant may have ten or twenty professional fights elsewhere, but the UFC-only feature set sees almost none of that experience.

### Pilot

I tested a small mixed group of fighters. Correctly resolved profiles produced sensible pre-UFC records, including examples such as:

- Khabib Nurmagomedov: 16-0 before the UFC;
- Islam Makhachev: 11-0;
- Justin Gaethje: 17-0;
- Michael Chandler: 21-5;
- Tom Aspinall: 7-2;
- Dricus Du Plessis: 14-2.

### Identity problem

Sherdog search can return multiple profiles with exactly the same fighter name. I therefore do not automatically accept the first name match.

My resolver validates candidate profiles by checking whether the professional history contains a fight on or very close to the fighter's known UFC debut date.

This successfully disambiguated duplicate profiles for Alex Pereira, Charles Oliveira, and Jiri Prochazka with a 0-day difference.

Jon Jones was not surfaced properly by Fight Finder, so I added a verified override URL. His profile validated with a 0-day difference and the expected 6-0 pre-UFC record.

### Full design

The planned full scraper covers approximately 2,725 UFC fighters and includes:

- strict debut-date validation;
- verified manual overrides only where necessary;
- per-fighter cache;
- checkpointing after every fighter;
- retries;
- unresolved review queue;
- strict filtering to fights before the first UFC date.

I consider this a more promising research direction than continuing to tune robbery/media ideas, because it fills a real information gap rather than perturbing data the model already sees.

---

## 25. What worked

The most successful engineering and modeling choices were:

- strict chronological feature construction;
- randomized A/B orientation;
- walk-forward validation;
- same-run baseline/challenger comparison;
- Elo as part of the mature model;
- age/height/reach;
- rate and defensive features;
- recent-three form;
- strength of schedule;
- CatBoost + logistic probability blending;
- selective EV filtering;
- fractional Kelly sizing;
- per-fight and per-event bankroll caps;
- sanity tests before long scraping jobs;
- conservative fighter identity matching.

---

## 26. What I rejected

I explicitly rejected or shelved the following after testing:

- momentum/durability expansion;
- stance/context bundle;
- fight-night cage-weight features;
- rehydration features;
- profit-weighted training;
- alternative hyperparameter configurations without stable gains;
- residual neural network;
- stacking;
- XGBoost challenger;
- XGBoost veto logic;
- robbery-aware sample weighting;
- media-adjusted Elo;
- media-history features for production.

I keep these failures documented because they prevent me from repeating the same experiments later and because they show the difference between plausible ideas and robust incremental signal.

---

## 27. Important bugs and lessons

### Relative paths

The original notebook lived inside `notebooks/`, so many paths were written as `../data/...`. Running code from a different working directory caused repeated path errors.

### Notebook hidden state

The giant notebook depended heavily on variables defined many cells earlier. This made reproducibility difficult and is the main reason for the refactor.

### VS Code output limits

Several large cells exceeded VS Code's notebook output limit. Long pipeline jobs should write files/logs instead of dumping huge tables into notebook output.

### Name collisions

Simple normalized-name matching is dangerous. Fight-night weight data and Sherdog both exposed duplicate/collision problems. I now prefer aliases, pair matching, known dates, and conservative review queues.

### Known-case scraper tests

The Khabib/Tibau parser failure saved me from running a broken scraper over thousands of pages. I now consider known-case sanity tests mandatory before large scraping jobs.

### Same-run baselines

Small dataset/cutoff differences can change benchmark metrics. I therefore compare a challenger only against a baseline generated in the same experimental run.

---

## 28. Why I refactored the notebook

The original notebook contains 153 code cells and roughly 3.17 MB of notebook JSON. It mixes:

- data exploration;
- data cleaning;
- feature engineering;
- scrapers;
- model training;
- evaluation;
- betting simulations;
- live prediction tools;
- dream-fight tools;
- rejected experiments.

The problem is not only file size. The bigger problem is hidden execution state.

I am replacing that with a Python package, explicit configuration, scripts, tests, reports, and an experiment registry.

The notebook remains useful as a historical archive, but it should no longer be the application itself.

---

## 29. Refactored project structure

The new project separates production code from historical research:

```text
ufc-fight-prediction-ai/
├── config/
├── data/
├── external/
├── models/
├── reports/
├── scripts/
├── src/ufc_ai/
├── tests/
├── workflows/
└── archive/
```

`src/ufc_ai/` contains reusable production modules.

`workflows/` is intended to preserve larger historical research pipelines by topic.

`reports/` contains this report and the experiment registry.

`archive/` preserves the original notebook for traceability.

---

## 30. Current production decision

My current production baseline remains the **42-feature, 55% CatBoost / 45% logistic ensemble**.

I have not found sufficient evidence to promote stance, rehydration, neural networks, XGBoost, robbery weighting, media-adjusted Elo, or media-history features.

The current betting rules remain unchanged.

The next major research question is whether **pre-UFC professional strength** improves the model specifically for debutants and low-UFC-experience fighters.

---

## 31. Rules I want to follow going forward

To reduce accidental holdout overfitting, I want future experiments to follow these rules:

1. develop features primarily on 2020–2024;
2. treat 2025–2026 as a later confirmation period;
3. do not repeatedly tune thresholds after inspecting later results;
4. generate baseline and challenger in the same run;
5. require probability-quality improvement before betting evaluation;
6. require betting preservation/improvement before production promotion;
7. record every experiment, including failed ones;
8. keep production configuration versioned and explicit;
9. keep notebooks lightweight and use them mainly for analysis/visualization.

---

## Final assessment

After several weeks of work, I consider the project much more mature than the original notebook structure suggested. The strongest parts are the chronological approach, leakage awareness, willingness to reject attractive ideas, and separation of probability modeling from betting decisions.

The biggest weakness was software organization: too much validated logic lived inside one stateful notebook. Refactoring that logic into explicit modules and workflows is now as important as adding new features.

The main lesson I take from the research so far is simple:

**small apparent improvements are common; improvements that survive chronological validation, later data, and betting evaluation are rare.**

That is the standard I want every future feature or model to meet before I change production.
