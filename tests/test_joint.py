import pandas as pd
import pytest

from ufc_ai.joint import OUTCOMES, validate_joint_predictions


@pytest.mark.parametrize("schema,prefix,winner", [
    ("historical", "COND_P_", "P_A_WIN"), ("live", "P_", "P_A_LIVE_DEBUT"),
])
def test_six_outcomes_preserve_winner_marginals(schema, prefix, winner):
    frame = pd.DataFrame([[1, 0, 0, 0, 0, 0, 1], [.2, .1, .1, .3, .2, .1, .4]],
                         columns=[prefix + key for key in OUTCOMES] + [winner])
    validate_joint_predictions(frame, schema)
    frame.loc[1, winner] = .6
    with pytest.raises(ValueError, match="indices .*1"):
        validate_joint_predictions(frame, schema)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -0.1, 1.1, .2, "missing"])
def test_invalid_outcome(bad):
    frame = pd.DataFrame([dict.fromkeys(("P_" + key for key in OUTCOMES), 0)])
    frame["P_A_DECISION"] = 1
    frame["P_A_LIVE_DEBUT"] = 1
    frame["P_B_DECISION"] = bad
    with pytest.raises(ValueError, match="Inconsistent"):
        validate_joint_predictions(frame, "live")


def test_missing_outcome_column():
    with pytest.raises(ValueError, match="P_B_SUBMISSION"):
        validate_joint_predictions(pd.DataFrame(), "live")
