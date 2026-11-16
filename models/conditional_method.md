# Conditional winner and method model

The model assigns a probability to each of six outcomes: decision, KO/TKO or submission for fighter A or B. For each possible winner, it estimates the finish probability and the chance that a finish is a KO/TKO. Multiplying each resulting method probability by the V2 winner probability produces the joint distribution. Draws and no contests are outside these six classes.

The [metadata](ufc_joint_conditional_method_v1_metadata.json) lists the feature order and project-relative weight paths. Each conditional stage blends logistic regression (45%) with CatBoost (55%) and uses 91 method features plus 46 winner-oriented features. The archive reports 8,660 training rows from March 1994 through August 2026.

| Walk-forward period | Exact winner and method accuracy | Conditional log loss | Independence baseline log loss |
|---|---:|---:|---:|
| 2020–2024 | 32.86% | 1.620848 | 1.641811 |
| 2025–2026 | 33.37% | 1.590947 | 1.623440 |

The figures above come from the archived model metadata. The live export uses the winner probability recorded for that fight. Each side's three joint probabilities must sum to its winner probability.

## Source files

SHA-256 checksums refer to the original members of the supplied archive. Weight paths in the portable JSON resolve from the project root.

| Archive member | SHA-256 |
|---|---|
| `models/ufc_joint_conditional_method_v1_metadata.json` | `2b941c48785d795cfef7b2b8ab56ea9ea4f06a52e7e1fb2fce3027249d60b59f` |
| `models/ufc_joint_cond_finish_logistic_v1.joblib` | `7c003671e3ec8f62878d4102d5f1fc97093ccfe67ce956fb140f3bad05c85fdb` |
| `models/ufc_joint_cond_finish_catboost_v1.cbm` | `300b6a93b621d9edf10a8a58356e12f4bb6bb9e526944515511c662431c45472` |
| `models/ufc_joint_cond_ko_logistic_v1.joblib` | `ed60c4cf23631e7b4daa464c71b751c85b0a8d1b74110d49c43b235333b30ada` |
| `models/ufc_joint_cond_ko_catboost_v1.cbm` | `e79f7edfb6ae79c5bafd6679473c2e82525853ed4db8b2c83e58d27239d6deaf` |
