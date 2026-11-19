# Frozen-model prediction orchestration

Adapted from the user-provided `updated_type_shit.zip`,
`UFC_Update_v2/update_and_predict.py`; uses the repository's V2 notebook runner
instead of the archive's older prediction entry point. No scraper source or
model binaries are imported. Existing external scraper licensing still applies.

From a development installation (`pip install -e .`):

```sh
python scripts/update_and_predict.py --project-root . --check-only
python scripts/update_and_predict.py --project-root . --snapshot-dir /path/to/snapshot --no-odds
python scripts/update_and_predict.py --project-root . --skip-history
```

`--check-only` checks nonempty local input files and metadata feature schemas,
then prints relative paths and SHA-256 hashes without deserializing models or
fetching network data. Required CSVs under `data/`: `training_data_with_sos`,
`fighter_history`, `fight_results_clean`, `ufc_fighter_tott`, and
`sherdog_preufc_features_full`. Canonical biography placement is required by
this wrapper even though the notebook supports legacy fallback directories.
V2 metadata, logistic joblib and CatBoost CBM must be present under `models/`.
See `models/README.md` for model provenance and runtime requirements.
Only use trusted model files: recorded hashes identify inputs, not authenticity.
Actual model/schema compatibility is additionally checked by the prediction runner.

The default history source is the bundled snapshot; supply its directory or use
an existing local snapshot layout documented in `update_history.md`. History
failure stops prediction. `--skip-history` explicitly uses the existing local
history. `--no-odds` disables quotes, but the live card lookup still uses ESPN.
Prediction output includes `input_artifacts.json` recording post-update inputs.
Avoid concurrent history/model edits during a run; this wrapper does not provide
transactional isolation across prediction and external file changes.

Production V2 is the wrapper default. `--experimental-v21` requires all V2.1
artifacts as well as V2 fallback artifacts; V2.1 remains experimental. The
notebook's existing default behavior is unchanged. No feature advantage is
inferred from the unequal original training populations (8683 versus 8705).
