from __future__ import annotations
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss, roc_auc_score
from .modeling import fit_ensemble, predict_ensemble

def metrics(y, p):
    return {
        "ACC": accuracy_score(y, p >= 0.5),
        "LOGLOSS": log_loss(y, p),
        "BRIER": brier_score_loss(y, p),
        "AUC": roc_auc_score(y, p),
    }

def walk_forward(data: pd.DataFrame, features: list[str], years=range(2020, 2027)):
    data = data.copy(); data["DATE"] = pd.to_datetime(data["DATE"])
    yearly, predictions = [], []
    for year in years:
        train = data[data.DATE.dt.year < year]
        val = data[data.DATE.dt.year == year]
        if val.empty: continue
        models = fit_ensemble(train[features], train["A_WIN"].astype(int))
        p = predict_ensemble(models, val[features])
        yearly.append({"YEAR": year, "N": len(val), **metrics(val["A_WIN"], p)})
        out = val[["DATE","FIGHTER_A","FIGHTER_B","A_WIN"]].copy(); out["P_A_WIN"] = p
        predictions.append(out)
    return pd.DataFrame(yearly), pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame()
