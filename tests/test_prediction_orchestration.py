import json
from pathlib import Path
import runpy
import subprocess
import sys
import types
import pytest

ns = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/update_and_predict.py'))
main = ns['main']


def artifacts(root, experimental=False):
    for name in ['training_data_with_sos', 'fighter_history', 'fight_results_clean',
                 'ufc_fighter_tott', 'sherdog_preufc_features_full']:
        path = root / 'data' / (name + '.csv')
        path.parent.mkdir(exist_ok=True)
        path.write_text('fixture\n')
    for version, count in [('v2_preufc', 46)] + ([('v21_uae_russia', 47)] if experimental else []):
        (root / 'models').mkdir(exist_ok=True)
        (root / 'models' / f'ufc_production_{version}_metadata.json').write_text(json.dumps({'features': [str(i) for i in range(count)]}))
        for kind, ext in [('logistic', 'joblib'), ('catboost', 'cbm')]:
            (root / 'models' / f'ufc_{kind}_production_{version}.{ext}').write_bytes(b'not a real model')


def test_missing_artifacts_stop_before_history(tmp_path, monkeypatch):
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: pytest.fail('history called'))
    with pytest.raises(ValueError, match='Missing/empty'):
        main(['--project-root', str(tmp_path)])


def test_check_only_does_not_load_weights(tmp_path):
    artifacts(tmp_path)
    hashes = main(['--project-root', str(tmp_path), '--check-only'])
    assert len(hashes) == 8 and all(len(h) == 64 for h in hashes.values())
    with pytest.raises(ValueError, match='v21'):
        main(['--project-root', str(tmp_path), '--experimental-v21', '--check-only'])
    (tmp_path / 'models/ufc_production_v2_preufc_metadata.json').write_text('{"features": ["bad"]}')
    with pytest.raises(ValueError, match='schema'):
        main(['--project-root', str(tmp_path), '--check-only'])


def test_history_failure_stops_prediction(tmp_path, monkeypatch):
    artifacts(tmp_path)
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0])
    monkeypatch.setattr(subprocess, 'run', fail)
    monkeypatch.setitem(sys.modules, 'predict_v2_notebook', types.SimpleNamespace(
        predict_upcoming_v2=lambda **kw: pytest.fail('prediction called')))
    with pytest.raises(subprocess.CalledProcessError):
        main(['--project-root', str(tmp_path)])


def test_success_order_and_flags(tmp_path, monkeypatch):
    artifacts(tmp_path, True)
    calls = []
    def update(command, check):
        assert check and '--snapshot-dir' in command
        calls.append('history')
    def predict(**kwargs):
        calls.append('prediction')
        assert kwargs['prefer_v21'] and not kwargs['fetch_prices']
        folder = tmp_path / 'output'
        folder.mkdir()
        return 'live', folder
    monkeypatch.setattr(subprocess, 'run', update)
    monkeypatch.setitem(sys.modules, 'predict_v2_notebook', types.SimpleNamespace(predict_upcoming_v2=predict))
    main(['--project-root', str(tmp_path), '--snapshot-dir', str(tmp_path), '--experimental-v21', '--no-odds'])
    assert calls == ['history', 'prediction']
    assert len(json.loads((tmp_path / 'output/input_artifacts.json').read_text())) == 11


@pytest.mark.parametrize('value', ['nan', 'inf', '0', '-1'])
def test_invalid_bankroll(tmp_path, value):
    with pytest.raises(SystemExit):
        main(['--project-root', str(tmp_path), '--bankroll', value])
