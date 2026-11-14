# Winner model cards

Both ensembles predict the probability that fighter A wins. Inputs are ordered A-minus-B pre-fight differences. Use the exact feature sequence in the matching JSON file. Both bundles combine logistic regression (45%) and CatBoost (55%) and report training from March 11, 1994 through August 29, 2026.

| Model | Inputs | Archived training rows | Use |
|---|---|---:|---|
| [V2](ufc_production_v2_preufc_metadata.json) | 42 base features and four pre-UFC career features | 8,705 | Baseline and fallback |
| [V2.1](ufc_production_v21_uae_russia_metadata.json) | The V2 schema followed by `DIFF_UAE_RUSSIA_HOME` | 8,683 | Experimental regional candidate |

V2.1 encodes direction at UAE events as +1 for A only from Russia, −1 for B only, and zero for both or neither. Live inference uses the actual event location. The notebook runner loads the V2 bundle and can select V2.1 when its weights are present. It falls back to V2 for unresolved UAE fighter identity. Pass `prefer_v21=False` to select the baseline explicitly.

## Training population

The supplied training CSV has 8,705 rows and 8,683 distinct combinations of date, unordered fighter keys and method. The archived canonical audit records 22 duplicate excess rows and 22 missing decisive fights relative to its canonical universe. This accounts for the difference in reported counts. Establishing which row was retained for each duplicate in each fitted model requires the training selection or a row manifest. Interpret historical comparisons with that limitation.

## Local artifacts

Place the matching logistic and CatBoost weights from the project archive at the paths below. The existing notebook runner also requires the local project data and live feature helpers described in the project README. The JSON files here preserve the original settings and feature order. The candidate's training and country-map paths are relative to the project root. The hashes identify the original archive members, before metadata formatting and path normalization.

| Archive member | SHA-256 of original bytes |
|---|---|
| `models/ufc_production_v2_preufc_metadata.json` | `902c9289a9c2da6bcf514bf21b3cc16c9dda4f0e4ccf78bfb939f44444697371` |
| `models/ufc_logistic_production_v2_preufc.joblib` | `8ae3c9c7417f50057b535151cadcfab8d57f0ce46d338b4aab3930b6ba6ec775` |
| `models/ufc_catboost_production_v2_preufc.cbm` | `520c675a65092e75e5aa9a0dc49eb623f26f8791b3d37ca5d330e1645a50f6a6` |
| `models/ufc_production_v21_uae_russia_metadata.json` | `e2f23eae91254a5643b60f67e2e7c85cea2d54c6a0503be203799a9486d1c3ec` |
| `models/ufc_logistic_production_v21_uae_russia.joblib` | `3c01066a6f21c015afda3fc5e99b852b09e5efcea5aaefe573d87304efd06c32` |
| `models/ufc_catboost_production_v21_uae_russia.cbm` | `9bb824ce6bab400cfe804b262ee5c64b886612af15a60663415b91f5fa1e01d3` |
| `data/training_data_with_odds_v2_preufc.csv` | `37babeba36e14498f474cb89dc59d00496f7cf8ccdb7d5beef5b3a109a706454` |
| `data/canonical_training_universe_audit.csv` | `374ef794225dcacc7584dcc3ccce3eba5300d3371713592a47e4e9032c5c7ffd` |
