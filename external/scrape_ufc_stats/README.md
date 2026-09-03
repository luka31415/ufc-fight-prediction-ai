# Scrape UFC Stats

This subdirectory documents the UFCStats scraper source I used as the starting point for the raw UFCStats ingestion layer.

The scraper collects UFC event data, fight details, fight results, fight statistics, fighter details, and fighter tale-of-the-tape information from `ufcstats.com` and stores the results as CSV files.

The upstream project was created by Russell Chan. I keep its attribution and license with the source rather than presenting the scraper as original work.

Expected raw files include:

```text
ufc_event_details.csv
ufc_fight_details.csv
ufc_fight_results.csv
ufc_fight_stats.csv
ufc_fighter_details.csv
ufc_fighter_tott.csv
```

My project then performs its own chronological cleaning, aggregation, leakage-safe feature construction, model training, evaluation, and betting research on top of these raw files.
