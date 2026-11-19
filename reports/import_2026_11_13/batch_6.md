# Batch 6 — prediction orchestration and settlement (2026-11-19)

Base main: `384560ec6f7ae81e6bc5859bea3a5bff1991e749`. Inspected the current
integration plan and recent commits; batches 1–5 were already present.

Two changes adapted from the retained user ZIP's `UFC_Update_v2` scripts:

1. `scripts/update_and_predict.py`: explicit local artifact preflight, default
   frozen V2, opt-in experimental V2.1, stop on history failure, input hashes.
2. `scripts/settle_picks.py`: snapshot-preserving, ID-based settlement, separate
   void/unresolved outcomes, strict duplicate and numeric validation, offline
   scoreboard input and event summaries.

Validation: `PYTHONPATH=src python -m pytest -q tests` on the current main source
plus these additions: **75 passed**, including **28 new offline cases**. Two
warnings: environment pytest/anyio deprecation and existing pandas history
concatenation FutureWarning. Checks cover orchestration ordering and failure,
artifact omissions, experimental opt-in, ID matching, repeat settlement,
void/pending/unknown results, absent odds and snapshot-preserving CLI output.
Model files in orchestration tests are deliberately inert fixtures; predictions
are stubbed. No training, real-model end-to-end inference, live ESPN response or
actual betting returns were verified. No raw data, binaries or backups imported.

This brings the planned total to 14 of 16 commits once both changes are published.
Remaining: batch 7, CI/development setup and README/final audit (two commits).
