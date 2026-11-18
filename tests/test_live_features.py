import runpy
from pathlib import Path
import pandas as pd
from ufc_ai.features import PRODUCTION_V1_FEATURES
from ufc_ai.live_features import build_live_features


def test_future_results_do_not_change_earlier_features(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    pd.DataFrame(columns=["DATE"] + PRODUCTION_V1_FEATURES).to_csv(data / "training_data_with_sos.csv", index=False)
    pd.DataFrame([dict(FIGHTER=x, DOB="1990-01-01", HEIGHT="6' 0", REACH="72") for x in "AB"]).to_csv(data / "ufc_fighter_tott.csv", index=False)
    results = pd.DataFrame([dict(DATE=d, FIGHTER_A="A", FIGHTER_B="B", WINNER="A", ROUND=3, TIME="5:00") for d in ["2020-01-01", "2022-01-01"]])
    results.to_csv(data / "fight_results_clean.csv", index=False)
    stats = dict.fromkeys(["KD", "SIG_STR_LANDED", "SIG_STR_ATT", "TOTAL_STR_LANDED",
                          "TOTAL_STR_ATT", "TD_LANDED", "TD_ATT", "SUB_ATT", "CTRL_SECONDS"], 1)
    history = pd.DataFrame([dict(DATE=d, FIGHTER=a, OPPONENT=b, **stats)
                            for d in results.DATE for a, b in [("A", "B"), ("B", "A")]])
    history.to_csv(data / "fighter_history.csv", index=False)
    cards = pd.DataFrame([dict(DATE=d, EVENT="UFC fixture", FIGHTER_A="A", FIGHTER_B="B")
                          for d in ["2023-01-01", "2021-01-01"]])
    live, features, _ = build_live_features(tmp_path, cards)
    assert features == PRODUCTION_V1_FEATURES
    assert live.A_UFC_FIGHTS.tolist() == [2, 1]
    results.loc[1, "WINNER"] = "B"
    results.to_csv(data / "fight_results_clean.csv", index=False)
    changed, _, _ = build_live_features(tmp_path, cards)
    pd.testing.assert_series_equal(live.loc[1, features], changed.loc[1, features])
    assert live.loc[0, "DIFF_ELO"] != changed.loc[0, "DIFF_ELO"]
    runner = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/predict_v2_notebook.py"))
    embedded, _, _ = runner["_build_base"](tmp_path, cards)
    pd.testing.assert_frame_equal(changed, embedded)
