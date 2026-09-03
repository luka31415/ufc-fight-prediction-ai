from pathlib import Path
import sys
import joblib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from ufc_ai.features import PRODUCTION_FEATURES
from ufc_ai.modeling import fit_ensemble

DATA=ROOT/"data"/"training_data_with_odds.csv"
OUT=ROOT/"models"; OUT.mkdir(exist_ok=True)
df=pd.read_csv(DATA)
missing=[c for c in PRODUCTION_FEATURES if c not in df.columns]
if missing: raise ValueError(f"Missing production features: {missing}")
models=fit_ensemble(df[PRODUCTION_FEATURES], df["A_WIN"].astype(int))
logistic,cat=models
joblib.dump(logistic, OUT/"ufc_logistic_production.joblib")
cat.save_model(OUT/"ufc_catboost_production.cbm")
print(f"Trained production ensemble on {len(df)} fights with {len(PRODUCTION_FEATURES)} features.")
