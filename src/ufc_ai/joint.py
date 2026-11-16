"""Validate conditional winner/method probabilities in the project's CSV exports."""
import argparse

import numpy as np
import pandas as pd

OUTCOMES = tuple(f"{side}_{method}" for side in "AB"
                 for method in ("DECISION", "KO_TKO", "SUBMISSION"))
SCHEMAS = {"historical": ("COND_P_", "P_A_WIN"), "live": ("P_", "P_A_LIVE_DEBUT")}


def validate_joint_predictions(frame, schema):
    """Check the six outcomes, their total, and both winner marginals per fight."""
    prefix, winner = SCHEMAS[schema]
    columns = [prefix + outcome for outcome in OUTCOMES] + [winner]
    missing = set(columns).difference(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    if frame.empty or frame.columns.duplicated().any():
        raise ValueError("Expected nonempty predictions with unique column names")
    values = frame[columns].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    valid = (np.isfinite(values) & (values >= 0) & (values <= 1)).all(axis=1)
    probs, p_a = values[:, :6], values[:, 6]
    for actual, expected in [(probs.sum(axis=1), 1), (probs[:, :3].sum(axis=1), p_a),
                             (probs[:, 3:].sum(axis=1), 1 - p_a)]:
        valid &= np.isclose(actual, expected, atol=1e-8, rtol=0)
    if not valid.all():
        rows = frame.index[~valid].tolist()
        raise ValueError(f"Inconsistent probabilities in {len(rows)} row(s), first indices {rows[:5]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv")
    parser.add_argument("--schema", choices=SCHEMAS, required=True)
    args = parser.parse_args()
    predictions = pd.read_csv(args.csv)
    try:
        validate_joint_predictions(predictions, args.schema)
    except ValueError as error:
        parser.exit(1, f"{error}\n")
    print(f"Validated {len(predictions)} {args.schema} predictions")
