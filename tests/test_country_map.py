import runpy
from pathlib import Path

import pandas as pd
import pytest


runner = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/predict_v2_notebook.py"))


def fighter_key(name):
    return name.strip().casefold()


def save_map(root, content):
    path = root / "reports/uae_regional_home_full_timeline/fighter_country_map_espn_enriched.csv"
    path.parent.mkdir(parents=True)
    path.write_text(content)
    return path


def test_unresolved_countries_use_map_or_v2(tmp_path):
    save_map(tmp_path, "FIGHTER_KEY,COUNTRY\nAlpha,RUS\nALPHA,Russia\nBeta,Default\n")
    live = pd.DataFrame({
        "FIGHTER_A": ["Alpha", "Alpha"], "FIGHTER_B": ["Beta", "Beta"],
        "A_COUNTRY_ESPN": [float("nan"), pd.NA], "B_COUNTRY_ESPN": ["default", "Brazil"],
        "IS_UAE_EVENT": [True, True],
    })
    result = runner["_add_v21_feature"](tmp_path, live, fighter_key)
    assert result["V21_FALLBACK_TO_V2"].tolist() == [True, False]
    assert result["DIFF_UAE_RUSSIA_HOME"].tolist() == [0.0, 1.0]


@pytest.mark.parametrize("content, message", [
    ("Fighter,Country\nAlpha,Russia\nALPHA,Brazil\n", "Conflicting"),
    ("Fighter,Source\nAlpha,ESPN\n", "requires"),
    ("Fighter,Country Std,COUNTRY_STD\nAlpha,Russia,Brazil\n", "Ambiguous"),
])
def test_invalid_country_map(tmp_path, content, message):
    with pytest.raises(ValueError, match=message):
        runner["_read_country_map"](save_map(tmp_path, content), fighter_key)
