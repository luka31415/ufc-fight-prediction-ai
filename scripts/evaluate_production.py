from pathlib import Path
import sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from ufc_ai.features import PRODUCTION_FEATURES
from ufc_ai.evaluation import walk_forward

df=pd.read_csv(ROOT/"data"/"training_data_with_odds.csv", parse_dates=["DATE"])
yearly,preds=walk_forward(df,PRODUCTION_FEATURES,range(2020,2027))
print(yearly.round(5).to_string(index=False))
yearly.to_csv(ROOT/"reports"/"production_walkforward_yearly.csv",index=False)
preds.to_csv(ROOT/"reports"/"production_walkforward_predictions.csv",index=False)
