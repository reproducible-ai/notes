# Commands and recipe

## Selected public run

The selected job is `f282527c-4573-4a28-afae-29033e75c4c6` at source `c084d6eab090a2b5822db474d790a00dfe7fae5d`. Inspect the [exact workflow](https://github.com/reproducible-ai/Isaac-GR00T/blob/c084d6eab090a2b5822db474d790a00dfe7fae5d/.treqs/workflows/droid-canary.yaml) and [recipe documentation](https://github.com/reproducible-ai/Isaac-GR00T/blob/c084d6eab090a2b5822db474d790a00dfe7fae5d/.treqs/README.md). These are the executed source records; a new run requires its own credentials, compatible GPU, budget and publication destination.

## Cold replay is unvalidated

The website displays the following candidate replay command for the public lineage:

```bash
roar reproduce 01c4225ca5c1df31c72153671041cd530fa338dac02259384855b56e0c540c15 --lineage --run --no-puts
```

This command has not been executed as an independent cold replay. The site's generic `pip install roar-cli` instruction does not establish the pinned source/native-tracer environment used here. Follow the pinned recipe's environment setup before attempting a new run. Public downloads and lineage checks are the verification performed; they do not establish replay success or model quality.

## Earlier private capture command record

Everything below describes the historical private capture and retains its original command outcomes. Private publication destinations remain redacted.

### Historical selected run recipe

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

Reproduction scripts, when included, are exact Roar output. Availability is recorded in [the capture summary](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/evidence/capture-summary.json).
