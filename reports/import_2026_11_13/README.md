# ZIP comparison and staged integration

Compared on 2026-11-13 with main at d05ceff4e1a173d3328893b8380d303fbdba9cdd.
Source: user-provided `updated_type_shit.zip`. This is a research workspace,
not a replacement checkout: files absent from the ZIP must not be deleted.

## Findings

The repository already documents Production V2 (46 features), the rejected
country-wide home-advantage experiment, October 11 results, and a V2 notebook
prediction entry point. The ZIP additionally supplies:

- `src/ufc_v21_uae_russia_feature.py`: a distinct UAE/Russia interaction feature.
- V2.1 candidate metadata and saved model weights (47 features).
- Conditional finish/KO models and metadata for six winner/method outcomes.
- `UFC_Update_v2`: history updates, live features/odds, predictions and settlement.
- Detailed UAE regional robustness, country resolution and V2/V2.1 comparisons.
- Large raw data, caches, backups and exploratory notebooks.

Saved V2.1 metadata reports annual walk-forward accuracy 0.625636 -> 0.627433,
log loss 0.645562 -> 0.645086, and Brier 0.227168 -> 0.226917. The signal
subset has 51 fights. These are supplied historical results, not independently
rerun results or evidence of future betting returns. V2.1 remains experimental.
The metadata has 8683 training rows versus V2's 8705: reconcile the training
universe before claiming an isolated feature improvement.

The initial integration ports the regional helper into `ufc_ai.regional` and
adds regression tests. It rejects missing country information at UAE events,
parses False/0 correctly, rejects invalid flags and avoids substring location
matches. Production V2 is unchanged.

## Finite rollout: 16 planned commits over 8 days

Two commits on November 13 and two per day November 14–20 (Europe/Berlin).
Future counts are targets: failed validation or upstream conflicts must be
reported, never replaced by empty commits. Check commit history before retrying.

| Date | Commit scope 1 | Commit scope 2 |
|---|---|---|
| Nov 13 | Regional feature with regression tests | ZIP comparison and integration plan |
| Nov 14 | Portable V2/V2.1 metadata and model cards | V2/V2.1 summary CSVs with provenance |
| Nov 15 | Regional robustness evidence and limitations | Country-map validation with tests |
| Nov 16 | Conditional-method metadata and model card | Six-outcome probability validation with tests |
| Nov 17 | History updater adapted to repo paths | Idempotence and duplicate-history tests |
| Nov 18 | Live feature generation adapted to repo package | Live odds parsing with offline fixture tests |
| Nov 19 | Prediction orchestration with explicit artifact checks | Settlement handling with void/unresolved tests |
| Nov 20 | CI and reproducible development setup | README commands, artifact instructions and final audit |

## Execution requirements

Use the source ZIP retained with the request, then inspect current main and
existing entry points before each change. Never overwrite concurrent user work.
Keep related tests in the same commit as the implementation except the separate
history validation package above. Run appropriate offline tests for each batch.
Record actual validation and any blockers in each day's report/commit.

Do not import raw caches, notebook outputs, nested Git metadata, backup copies,
or trained binaries into ordinary Git. Document model/data prerequisites and
checksums. Model weights need an explicit reproducible artifact workflow before
an end-to-end prediction claim is made. Preserve upstream license/attribution
if importing scraper code; prefer the existing external dependency boundary.
Avoid copying private local absolute paths into public metadata.

Priority additions: consistent feature schemas; pre-event-only chronology;
training-universe reconciliation; calibration/uncertainty; event exposure caps;
missing/duplicate odds checks; settlement idempotence; offline fixtures; CI.
