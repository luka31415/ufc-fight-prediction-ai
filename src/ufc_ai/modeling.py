from __future__ import annotations
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from catboost import CatBoostClassifier

CAT_WEIGHT = 0.55
LOG_WEIGHT = 0.45
SEED = 42

def make_logistic() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=3000, random_state=SEED)),
    ])

def make_catboost() -> CatBoostClassifier:
    return CatBoostClassifier(
        iterations=420, depth=5, learning_rate=0.03, loss_function="Logloss",
        random_seed=SEED, verbose=False, allow_writing_files=False,
    )

def fit_ensemble(X, y):
    logistic = make_logistic(); cat = make_catboost()
    logistic.fit(X, y); cat.fit(X, y)
    return logistic, cat

def predict_ensemble(models, X) -> np.ndarray:
    logistic, cat = models
    p_log = logistic.predict_proba(X)[:, 1]
    p_cat = cat.predict_proba(X)[:, 1]
    return CAT_WEIGHT * p_cat + LOG_WEIGHT * p_log
