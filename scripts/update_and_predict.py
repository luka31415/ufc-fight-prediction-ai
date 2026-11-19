"""Preflight local artifacts, update history, then run frozen V2 predictions.

Adapted from updated_type_shit.zip/UFC_Update_v2/update_and_predict.py.
V2.1 is experimental and requires explicit opt-in. No weights are downloaded.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys


def preflight(root, experimental=False):
    required = [f'data/{n}.csv' for n in (
        'training_data_with_sos', 'fighter_history', 'fight_results_clean',
        'ufc_fighter_tott', 'sherdog_preufc_features_full')]
    for suffix in ['v2_preufc'] + (['v21_uae_russia'] if experimental else []):
        required += [f'models/ufc_production_{suffix}_metadata.json',
                     f'models/ufc_logistic_production_{suffix}.joblib',
                     f'models/ufc_catboost_production_{suffix}.cbm']
    missing = [p for p in required if not (root / p).is_file() or (root / p).stat().st_size == 0]
    if missing:
        raise ValueError('Missing/empty local artifacts: ' + ', '.join(missing))
    for path in required:
        if path.endswith('_metadata.json'):
            metadata = json.loads((root / path).read_text())
            features = metadata.get('features', [])
            expected = 47 if 'v21_' in path else 46
            if (len(features) != expected or any(not isinstance(f, str) or not f for f in features)
                    or len(set(features)) != expected):
                raise ValueError('Invalid feature schema: ' + path)
    # Inventory hashes record actual inputs; they do not authenticate pickle files.
    inventory = {}
    for path in required:
        digest = hashlib.sha256()
        with (root / path).open('rb') as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(chunk)
        inventory[path] = digest.hexdigest()
    return inventory


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source', choices=['bundled', 'mirror', 'ufcstats'], default='bundled')
    parser.add_argument('--snapshot-dir', type=Path)
    parser.add_argument('--skip-history', action='store_true')
    parser.add_argument('--no-odds', action='store_true')
    parser.add_argument('--experimental-v21', action='store_true')
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--months', type=int, default=12)
    parser.add_argument('--bankroll', type=float, default=10000.)
    args = parser.parse_args(argv)
    if args.months <= 0 or not math.isfinite(args.bankroll) or args.bankroll <= 0:
        parser.error('months and bankroll must be finite and positive')
    root = args.project_root.resolve()
    inventory = preflight(root, args.experimental_v21)
    if args.check_only:
        print(json.dumps(inventory, indent=2))
        return inventory
    if not args.skip_history:
        command = [sys.executable, str(Path(__file__).with_name('update_history.py')),
                   '--project-root', str(root), '--source', args.source]
        if args.snapshot_dir:
            command += ['--snapshot-dir', str(args.snapshot_dir.resolve())]
        subprocess.run(command, check=True)
        inventory = preflight(root, args.experimental_v21)
    from predict_v2_notebook import predict_upcoming_v2
    live, folder = predict_upcoming_v2(root=root, months=args.months, bankroll=args.bankroll,
                                     fetch_prices=not args.no_odds, prefer_v21=args.experimental_v21)
    (folder / 'input_artifacts.json').write_text(json.dumps(inventory, indent=2) + '\n')
    return live, folder


if __name__ == '__main__':
    main()
