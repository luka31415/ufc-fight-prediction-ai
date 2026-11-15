# UAE/Russia regional robustness

This archive experiment fits a signed offset to the V2 log odds for UAE fights with exactly one Russian fighter. Each fold estimates the offset using the other event dates, then scores fights on the held-out date. The 51 fights span 17 dates in 2020–2025.

| Fight-weighted held-out metric | Frozen V2 | V2 plus offset |
|---|---:|---:|
| Brier score | 0.186951 | 0.155661 |
| Log loss | 0.560454 | 0.487025 |

Log loss improved on 12 of 17 dates and Brier score on 13. All 17 fitted offsets were positive (0.567–0.794). The archived 5,000 event permutations yielded one-sided empirical p-values of 0.0060 for Brier and 0.0068 for log loss, with a plus-one correction.

Holding out an event still allows later events in its training fold. The year-stability export uses earlier years only for its pre-year column and shows worse scores in 2022 (two fights). The small, selected regional sample limits generalization. The [annual V2.1 evaluation](../v2_vs_v21_uae_russia_feature/README.md) evaluates a separately trained 47-feature model. V2.1 remains experimental.

## Source and offline checks

The CSVs are byte-for-byte copies from the same directory in the supplied research ZIP. Per-event and pooled scores were recalculated from the saved predictions. Permutation tail probabilities were checked against the archived null draws. The fitting and permutations themselves were not rerun.

| Source filename | SHA-256 |
|---|---|
| `russia_uae_final_robustness_summary.csv` | `3e0be70590e96cd239f512599ee258aaa7c6cebd4e59f89ba1e580c445ba80df` |
| `russia_uae_leave_one_event_out.csv` | `1b5eefcd79343a2cb20222fb10a187546faae0c45d84417c7dbe4a0072911192` |
| `russia_uae_year_stability.csv` | `d446268a89e62d80b5bae49f24ff446dcbe184285c99298d33aca145a9267f23` |
| `russia_uae_leave_one_event_out_predictions.csv` | `0ee555bc0406ada5c902d027102e04bc16feb7a75db4e02bd2b3a063d711f00a` |
| `russia_uae_event_permutation_null.csv` | `d3d22b000ab52c713271b712744b62ae249a4b45b77d41df299718650b29fcc7` |
