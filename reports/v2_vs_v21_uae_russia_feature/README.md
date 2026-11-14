# V2 and V2.1 annual walk-forward comparison

The four summary CSVs reproduce the supplied research export byte for byte. Rows in the overall comparison cover 3,339 held-out predictions in annual folds from 2020 through 2026. Each delta is V2.1 minus V2. Accuracy and AUC increase with better performance. Brier score and log loss decrease.

| Subset | Fights | V2 log loss | V2.1 log loss |
|---|---:|---:|---:|
| All | 3,339 | 0.645562 | 0.645086 |
| Nonzero regional feature | 51 | 0.560454 | 0.511275 |
| Zero regional feature | 3,288 | 0.646882 | 0.647161 |

The signal-year table includes only years with a nonzero regional feature. Across all fights the candidate correctly classified six more fights. The saved predictions show a small overall difference and slightly worse log loss outside the signal subset. See the [model cards](../../models/README.md) for training-population limitations.

## Provenance and verification

Source archive: `updated_type_shit.zip`. The four CSVs retain their archive paths. The larger prediction and bet ledgers listed below are the audit inputs. Offline verification recomputed counts, accuracy at 0.5, mean squared probability error, binary log loss, rank-based AUC and model deltas for every overall, yearly and signal-year row. The archived betting simulations were checked against each bet ledger for count, wins, stake, profit and ROI (profit divided by stake). Model training and the drawdown paths were outside this check.

| Archive member | SHA-256 of original bytes |
|---|---|
| `reports/v2_vs_v21_uae_russia_feature/v2_vs_v21_feature_summary.csv` | `240624b6f9e50650bbb9a48a69bcc2cdac6775ec4476c4980fb205ba481d04cf` |
| `reports/v2_vs_v21_uae_russia_feature/v2_vs_v21_feature_yearly.csv` | `6f3efa8901f9f1e7d8fb3d2dfea4fe7354f8a2d552e1dfcaf486612f410ede82` |
| `reports/v2_vs_v21_uae_russia_feature/v2_vs_v21_feature_signal_yearly.csv` | `80260a97d362ad07ee5d8bacd1d5f21fea9d4d40d6da9257d7c580afc07a1624` |
| `reports/v2_vs_v21_uae_russia_feature/v2_vs_v21_feature_betting_summary.csv` | `2f27123784dc2526439ae021209732f5fa3584c69ab9d0d1a9bc39f39f752877` |
| `reports/v2_vs_v21_uae_russia_feature/v2_vs_v21_feature_all_predictions.csv` | `986325e3508b4f961ca9f7ded9a9afb7fb35d3878c8b129374b16f94b33a2d55` |
| `reports/v2_vs_v21_uae_russia_feature/v2_feature_test_bets.csv` | `44dbf75dd7857dcdd22fc7d673c17a92600edf03a59413d819228cb7e3251447` |
| `reports/v2_vs_v21_uae_russia_feature/v21_true_feature_bets.csv` | `fd8de4651de684bac3165146a1010903b70ddaa11ca3b5578ceee36c93a4b531` |
