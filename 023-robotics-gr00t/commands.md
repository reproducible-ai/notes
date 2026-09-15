# Commands and recipe

## Selected run recipe

Attempt `c1d5947f-ef2a-4e27-b071-94f6cc95e7c9`; committed workflow `.treqs/workflows/droid-canary.yaml`.

Recorded commands below retain their outcomes; failed commands are not recipe steps.

Inspect local candidate files and source revision.

``````sh
git status --short; rg --files; git rev-parse HEAD
``````

Validate offline workflow and receipt contracts.

``````sh
python3 -m unittest discover -s tests/treqs -p test_droid_canary_offline.py -v
``````

Format changed Python files.

``````sh
ruff format .treqs/scripts/package_droid_canary.py .treqs/scripts/verify_droid_canary.py tests/treqs/test_droid_canary_contract.py tests/treqs/test_droid_canary_offline.py
``````

Fix the import-spacing lint finding.

``````sh
ruff check --fix tests/treqs/test_droid_canary_offline.py
``````

Validate changed Python files after formatting.

``````sh
ruff check .treqs/scripts/package_droid_canary.py .treqs/scripts/verify_droid_canary.py tests/treqs/test_droid_canary_contract.py tests/treqs/test_droid_canary_offline.py
``````

Check Python syntax without importing training dependencies.

``````sh
python3 -m compileall -q .treqs/scripts tests/treqs
``````

Check patch whitespace.

``````sh
git diff --check
``````

The pinned workflow is retained privately because it contains private references.

## Other observed commands

Attempt `c1d5947f-ef2a-4e27-b071-94f6cc95e7c9` — failed: Check local test dependencies.

``````sh
python3 -c "import torch, pytest, yaml, safetensors, huggingface_hub; print('local test dependencies available')"
``````

Reproduction scripts, when included, are exact Roar output. Availability is recorded in [the capture summary](evidence/capture-summary.json).
