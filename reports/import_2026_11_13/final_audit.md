# Final integration audit — 20 November 2026

The finite integration is complete with this documentation commit: 16 meaningful
commits across 13–20 November, two per day, including the initial two commits.
All seven follow-up batches are done. No additional automatic work is planned.

## Scope and provenance

Reviewed current main at `f834f21603b7cf5c7c013e49d41a547451ec073a`, the integration plan,
recent commits and the current repository tree. No AGENTS.md files were present.
Source: the retained user-provided `updated_type_shit.zip`, SHA-256
`8b8c4c6a9035f97104f1570c5aba6ae8583a9ef9d6f35ea9360f22835f289f18`.
The archive was not copied wholesale into Git. Existing main files were
preserved except the explicit documentation/setup changes in this batch.
The original source ZIP remains necessary for local research inputs.

## Completion record

| No. | Commit | Scope |
|---|---|---|
| 1 | [373842d](https://github.com/luka31415/ufc-fight-prediction-ai/commit/373842d7f2ca55792bccf1a3ec662b325ac20467) | feat: add validated experimental UAE Russia feature |
| 2 | [6bdcaee](https://github.com/luka31415/ufc-fight-prediction-ai/commit/6bdcaee06878642e00e44d855b87f0c0aa9f38cf) | docs: audit uploaded research and plan seven daily integration batches |
| 3 | [7dc5fbf](https://github.com/luka31415/ufc-fight-prediction-ai/commit/7dc5fbfd3e80c0855b69e3a6eeeac8c40d378ff3) | Document V2 and V2.1 winner models with portable bundle metadata |
| 4 | [2e36871](https://github.com/luka31415/ufc-fight-prediction-ai/commit/2e368711133c96875ea1897e00dcc42c071447e2) | Publish audited V2 and V2.1 walk-forward summaries with source checksums |
| 5 | [67ec006](https://github.com/luka31415/ufc-fight-prediction-ai/commit/67ec006788201bc1a8b10de9920a34bc57d98bb6) | Publish regional leave-one-event-out evidence and uncertainty |
| 6 | [9ffe3a6](https://github.com/luka31415/ufc-fight-prediction-ai/commit/9ffe3a67cede342ee2899ec5728305b4f9629eaa) | Validate country mappings and preserve V2 fallback for unknown identities |
| 7 | [995e1d7](https://github.com/luka31415/ufc-fight-prediction-ai/commit/995e1d78db087f0074907b2127c92608458cc236) | Document the conditional winner and method model and its portable metadata |
| 8 | [e18bda4](https://github.com/luka31415/ufc-fight-prediction-ai/commit/e18bda418c3de82eb522021f0a95c8ad369f9780) | Validate six-outcome distributions and winner marginals in archived and live exports |
| 9 | [83e22fa](https://github.com/luka31415/ufc-fight-prediction-ai/commit/83e22fa9788aeb000242eb8532f00f0f18b6b69a) | Integrate incremental fight history updates with checked snapshots and repair handling |
| 10 | [f472a47](https://github.com/luka31415/ufc-fight-prediction-ai/commit/f472a479702eb1468b1b8f6297e8c010f8879431) | Test repeat imports, duplicate fight histories and failed snapshot validation |
| 11 | [f7ca6f1](https://github.com/luka31415/ufc-fight-prediction-ai/commit/f7ca6f1ecbb2a7bb54616e8a6a343c398c655924) | Package live feature generation with per-date history cutoffs and regression coverage |
| 12 | [384560e](https://github.com/luka31415/ufc-fight-prediction-ai/commit/384560ec6f7ae81e6bc5859bea3a5bff1991e749) | Package athlete-matched live odds with offline parser and coverage tests |
| 13 | [ac649d9](https://github.com/luka31415/ufc-fight-prediction-ai/commit/ac649d970ca7798a87cb99b15d29d443f17b22a2) | Add artifact-checked V2 prediction orchestration with offline tests |
| 14 | [f834f21](https://github.com/luka31415/ufc-fight-prediction-ai/commit/f834f21603b7cf5c7c013e49d41a547451ec073a) | Add snapshot settlement with void, unresolved and idempotence tests |
| 15 | [12181b6](https://github.com/luka31415/ufc-fight-prediction-ai/commit/12181b65463040effdeb400b98c9b0c8ce8eb398) | Pinned development environment and offline CI |
| 16 | This commit | README commands, artifact instructions and final audit |

## Final verification

A clean Python 3.12 virtual environment was populated with the pinned runtime
and test packages. The project was installed editable with no dependency
resolution or build isolation. From the repository root:

- `python -m pip check`: no broken requirements.
- `python -m pytest --disable-socket -q`: **75 passed**.
- `python -m compileall -q src scripts`: passed.
- One existing pandas FutureWarning in history-update concatenation; no failures.
- Source inventory checked for binaries, raw data, backups and nested Git
  metadata; none added. Private absolute-path patterns reviewed with no private
  path found in the tracked source/documents.
- Workflow actions resolved to commit SHAs; permissions limited to contents read.
  The local equivalent was run; a hosted Actions success is not claimed here.

No tests require real weights or private input CSVs. Model deserialization,
training, live ESPN behavior and fresh betting returns were not validated.
The retained archive's historical metrics remain historical evidence rather
than a fresh reproduction of training.

## Limitations and final documentation corrections

V2.1 remains experimental; the orchestration CLI defaults to V2 while the old
notebook still prefers available V2.1 artifacts. Both behaviors are documented.
The 8,705/8,683 counts reconcile numerically with 22 duplicate excess rows in the
supplied data; the exact fitted row selection still requires a training manifest.
This does not establish an isolated regional-feature benefit.

Model cards record archive-member checksums. Portable metadata formatting differs
from original bytes. The development version lock supports reproducible code
checks, but is not a fully reproduced model-training environment or an artifact
download service. Legacy train/evaluate scripts use unversioned filenames and do
not recreate the frozen bundles automatically.

README directory listings now reflect tracked contents. Notebook archives and
thematic workflows remain external. The UFCStats provenance note explicitly
states that upstream source is not bundled; retain attribution and GPL terms
when obtaining it separately. No upstream scraper code was relicensed.

No deviation from the 16-commit scope. Remaining planned batches: **0**.
