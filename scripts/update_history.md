# Refresh the local UFC history

Run the updater from a checkout with the historical CSVs in `data/fight_results_clean.csv` and `data/fighter_history.csv`. It uses the project containing the script by default. Use `--project-root PATH` to update a different local dataset.

    python scripts/update_history.py --source bundled --snapshot-dir /path/to/UFC_Update_v2/snapshot
    python scripts/update_history.py --source mirror

The bundled source checks the four files against the supplied provenance manifest. The October snapshot covers five events after August 29 through October 3, 2026. The mirror uses a single upstream commit for each refresh. Use `--since YYYY-MM-DD` to revisit an earlier date. For direct UFCStats mode, install Russell Chan's scraper with its original GPL-3.0 license under `external/scrape_ufc_stats/`; see that directory's README.

Each run writes its fight audit and counts under `reports/history_updates/`. Changed CSVs are staged and backed up there before replacement. A concurrent updater is excluded by `data/.history-update.lock`. If the process is killed during a write, inspect the latest backup and confirm the writer has stopped before removing the lock. The result and fighter-history files are replaced individually. A repeated import of a complete snapshot leaves these CSVs intact.
