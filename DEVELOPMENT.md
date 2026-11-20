# Development and offline checks

The reference development environment is CPython 3.12 on Linux. The pinned
`requirements-dev.txt` includes runtime and test dependencies, including the
NumPy 1.x / scikit-learn 1.5.2 combination expected by archived logistic models.
This is a version lock, not a cross-platform binary or cryptographic lock.
Other supported Python versions may need a separate dependency resolution.

```sh
python3.12 -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip install --no-build-isolation --no-deps -e .
python -m pip check
python -m pytest --disable-socket -q
python -m compileall -q src scripts
```

Installation requires package-index access; tests block socket access with
pytest-socket and use temporary synthetic inputs. They do not need downloaded
model weights, the source ZIP, private CSVs, ESPN access or scraper execution.
CI runs the same commands on pushes and pull requests with read-only repository
permissions. CI results validate the code and fixtures, not model performance.

To intentionally change dependencies, resolve in a fresh Python 3.12 environment,
run the full suite and dependency checks, then regenerate the lock with
`python -m pip freeze --all --exclude-editable > requirements-dev.txt`.
Do not freeze unrelated workspace packages into the lock.

Local inference is separate: follow [prediction setup](scripts/update_and_predict.md)
and [model cards](models/README.md). Only load model artifacts you trust;
joblib/pickle deserialization can execute code. The preflight's recorded hashes
identify the files actually used; compare them with the published archive-member
hashes before loading the original models. Edited portable metadata has different
bytes from the original archived metadata by design.

No raw caches, backups, ZIP archives, generated predictions, nested repositories
or model binaries belong in a source commit. The supplied research archive remains
the source of local inputs, not a replacement checkout. The UFCStats scraper is
an external dependency with its own attribution and GPL obligations; this repo
contains a provenance note, not the upstream source or a relicensing grant.
