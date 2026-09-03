from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_UFC_DIR = PROJECT_ROOT / "scrape_ufc_stats"
MODEL_DIR = PROJECT_ROOT / "models"
REPORT_DIR = PROJECT_ROOT / "reports"

def ensure_dirs():
    for p in (DATA_DIR, MODEL_DIR, REPORT_DIR):
        p.mkdir(parents=True, exist_ok=True)
