import hashlib
import json
import runpy
from pathlib import Path

import pandas as pd
import pytest


updater = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/update_history.py"))


@pytest.fixture
def project(tmp_path):
    data = tmp_path / "data"
    snap = tmp_path / "snapshot"
    data.mkdir()
    snap.mkdir()
    result = dict(DATE="2026-09-05", EVENT="UFC example", FIGHTER_A="A", FIGHTER_B="B",
                  BOUT="A vs. B", URL="https://ufcstats.com/fight-details/one")
    latest = pd.DataFrame([result])
    previous = latest.assign(DATE="2026-08-29", URL="https://ufcstats.com/fight-details/earlier")
    history = pd.DataFrame([dict(DATE=result["DATE"], FIGHTER=a, OPPONENT=b,
                                 **dict.fromkeys(updater["CORE_STATS"], 0))
                            for a, b in [("A", "B"), ("B", "A")]])
    previous.to_csv(data / "fight_results_clean.csv", index=False)
    history.assign(DATE="2026-08-29").to_csv(data / "fighter_history.csv", index=False)
    latest.to_csv(snap / "new_fight_results.csv", index=False)
    history.to_csv(snap / "new_fighter_history.csv", index=False)
    pd.DataFrame({"FIGHTER": ["A"]}).to_csv(snap / "new_fighter_bios.csv", index=False)
    latest.to_csv(snap / "source_audit.csv", index=False)
    seal(snap)
    return data, snap


def seal(snap):
    sums = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in snap.glob("*.csv")}
    (snap / "provenance.json").write_text(json.dumps({"files": sums}))


def refresh(data, snap):
    updater["main"](["--project-root", str(data.parent), "--snapshot-dir", str(snap)])


def contents(data):
    return {p.name: p.read_bytes() for p in data.glob("*.csv")}


def test_retry_and_repair_duplicated_fighter_side(project):
    data, snap = project
    refresh(data, snap)
    expected = contents(data)
    refresh(data, snap)
    assert contents(data) == expected
    path = data / "fighter_history.csv"
    history = pd.read_csv(path)
    history.iloc[-1] = history.iloc[-2]
    history.to_csv(path, index=False)
    refresh(data, snap)
    assert contents(data) == expected


@pytest.mark.parametrize("error", ["result duplicate", "same side", "wrong opponent", "checksum"])
def test_reject_bad_snapshot_without_mutation(project, error):
    data, snap = project
    before = contents(data)
    if error == "result duplicate":
        path = snap / "new_fight_results.csv"
        frame = pd.read_csv(path)
        pd.concat([frame, frame]).to_csv(path, index=False)
    else:
        path = snap / "new_fighter_history.csv"
        frame = pd.read_csv(path)
        if error == "same side":
            frame.iloc[1] = frame.iloc[0]
        else:
            frame.loc[0, "OPPONENT"] = "C"
        frame.to_csv(path, index=False)
    if error != "checksum":
        seal(snap)
    with pytest.raises(ValueError):
        refresh(data, snap)
    assert contents(data) == before
    assert not (data / ".history-update.lock").exists()


def test_distinct_fight_ids_are_preserved(project):
    data, snap = project
    path = data / "fight_results_clean.csv"
    existing = pd.read_csv(snap / "new_fight_results.csv").assign(URL="https://ufcstats.com/fight-details/other")
    pd.concat([pd.read_csv(path), existing]).to_csv(path, index=False)
    before = contents(data)
    with pytest.raises(ValueError, match="Distinct fight IDs"):
        refresh(data, snap)
    assert contents(data) == before
