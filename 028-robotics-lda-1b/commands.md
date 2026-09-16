# Commands and recipe

## Recorded execution context

TReqs executed the [seven-stage workflow at candidate `b55c26dad419064089f588837c5048843537577a`](https://github.com/reproducible-ai/LDA-1B/blob/b55c26dad419064089f588837c5048843537577a/.treqs/workflows/robocasa-demo-canary.yaml). This is the recorded recipe, not a newly tested standalone replay. It assumes a fresh Linux GPU workspace, an existing compatible compute target, brokered GLaaS credentials, an HF credential with the required input/write access, and a supervisor-owned private destination and dollar cap. The model command itself is ordinary Python; TReqs wraps the training stage because its `trace` setting is `run`.

The following workflow excerpt preserves command order, pins, timeouts and trace settings. Two values are deliberately replaced by documentation placeholders: `<HF_CACHE>` is the node-local Hugging Face cache, and `<PRIVATE_HF_DESTINATION>` is the supervisor-bound private artifact destination. Do not execute the placeholders literally. The pinned source link retains the exact original workflow; a future run needs its own authorized private destination.

```yaml
name: LDA RoboCasa demo one-step reproduction
secrets:
- HF_TOKEN

setup:
  command: |
    set -euo pipefail
    export PATH="$(python3 -m site --user-base)/bin:${PATH}"
    timeout --signal=TERM --kill-after=30 90 python3 .treqs/scripts/check_hf_access.py
    GPU_COUNT="$(timeout --signal=TERM --kill-after=30 30 nvidia-smi --list-gpus | wc -l | tr -d ' ')"
    test "${GPU_COUNT}" = "1"
    timeout --signal=TERM --kill-after=30 180 python3 -m pip install --user --disable-pip-version-check uv==0.12.3
    command -v uv >/dev/null
    timeout --signal=TERM --kill-after=30 1200 bash .treqs/scripts/install_roar_source.sh
    export PATH="/usr/local/bin:${PATH}"
    rm -rf .venv
    timeout --signal=TERM --kill-after=30 180 uv venv --python 3.11 .venv
    timeout --signal=TERM --kill-after=30 3000 uv pip install --python .venv/bin/python --index-strategy unsafe-best-match -r requirements.txt
    timeout --signal=TERM --kill-after=30 180 uv pip install --python .venv/bin/python pytest==8.4.2 pyyaml==6.0.3
    timeout --signal=TERM --kill-after=30 180 uv pip install --python .venv/bin/python --no-deps -e .
    ROAR_VERSION="$(timeout --signal=TERM --kill-after=30 60 env PATH=/usr/local/bin:/usr/bin:/bin roar --version)"
    test "${ROAR_VERSION}" = "roar, version 0.4.7"
    timeout --signal=TERM --kill-after=30 60 roar tracer use preload
    timeout --signal=TERM --kill-after=30 60 roar tracer
    timeout --signal=TERM --kill-after=30 60 roar init --no-gitignore
    timeout --signal=TERM --kill-after=30 180 .venv/bin/python -m pytest -q tests/treqs
  trace: "off"

fetch:
  command: |
    set -euo pipefail
    export PATH="$PWD/.venv/bin:/usr/local/bin:/opt/pytorch/bin:$PATH"
    timeout --signal=TERM --kill-after=30 5400 roar run -n fetch -- env PYTHONUNBUFFERED=1 HF_HOME=<HF_CACHE> python .treqs/scripts/prepare_robocasa_canary.py
  trace: "off"

train:
  command: |
    set -euo pipefail
    export PATH="$PWD/.venv/bin:/usr/local/bin:/opt/pytorch/bin:$PATH"
    timeout --signal=TERM --kill-after=30 3600 env PYTHONUNBUFFERED=1 HF_HOME=<HF_CACHE> WANDB_MODE=disabled python .treqs/scripts/run_robocasa_canary.py
  trace: "run"

evaluate:
  command: |
    set -euo pipefail
    export PATH="$PWD/.venv/bin:/usr/local/bin:/opt/pytorch/bin:$PATH"
    timeout --signal=TERM --kill-after=30 1800 roar run -n evaluate -- env PYTHONUNBUFFERED=1 python .treqs/scripts/verify_robocasa_canary.py
  trace: "off"

package:
  command: |
    set -euo pipefail
    export PATH="$PWD/.venv/bin:/usr/local/bin:/opt/pytorch/bin:$PATH"
    timeout --signal=TERM --kill-after=30 600 roar run -n package -- env PYTHONUNBUFFERED=1 python .treqs/scripts/package_robocasa_canary.py
  trace: "off"

label:
  command: |
    set -euo pipefail
    export PATH="$PWD/.venv/bin:/usr/local/bin:/opt/pytorch/bin:$PATH"
    SOURCE_COMMIT="$(git rev-parse HEAD)"
    MODEL=artifacts/lda-robocasa-canary/release/checkpoints/LDA-robocasa-treqs-canary.pt
    test -s "$MODEL"
    timeout --signal=TERM --kill-after=30 180 roar label set artifact "$MODEL" model.name=lda-robocasa-demo-canary model.version=0.0.1 license.id=LicenseRef-LDA-Composite license.name='Component-specific: CC BY-NC 4.0; Apache 2.0; DINOv3 License' description='LDA RoboCasa one-step TReqs fine-tuning canary' documentation.url="https://github.com/reproducible-ai/LDA-1B/blob/${SOURCE_COMMIT}/.treqs/README.md"
  trace: "off"

publish:
  glaas_creds: true
  command: |
    set -euo pipefail
    export PATH="$PWD/.venv/bin:/usr/local/bin:/opt/pytorch/bin:$PATH"
    RELEASE=artifacts/lda-robocasa-canary/release
    for document in README.md LICENSE CC-BY-NC-4.0.md APACHE-2.0.txt DINOv3-LICENSE.md NOTICE evaluation.json input-manifest.json publication.json; do
      test -s "$RELEASE/checkpoints/loader/$document"
    done
    test -s "$RELEASE/checkpoints/LDA-robocasa-treqs-canary.pt"
    timeout --signal=TERM --kill-after=30 180 roar status --untracked-dirs
    test -s "$RELEASE/checkpoints/artifact-manifest.json"
    test -s "$RELEASE/checkpoints/result.json"
    roar put artifacts/lda-robocasa-canary/release/checkpoints --private --yes --no-tag -m "private reproducibility canary" <PRIVATE_HF_DESTINATION>
  trace: "off"
```

## Training arguments and source-built Roar

The [training wrapper](https://github.com/reproducible-ai/LDA-1B/blob/b55c26dad419064089f588837c5048843537577a/.treqs/scripts/run_robocasa_canary.py) invokes `accelerate launch --config_file .treqs/assets/accelerate-zero2-cpu.yaml --num_processes 1 lda/training/train_LDA.py` with the pinned checkpoint config and explicit overrides. These include one step, batch four, accumulation one, both encoders frozen, policy-only training, one diffusion repeat, zero warmup, base/action learning rates of 1e-6, SDPA and strict checkpoint loading. `row.json.parameters` records the differences from the checkpoint's published config. Despite the legacy `cpu` filenames, the [DeepSpeed JSON](https://github.com/reproducible-ai/LDA-1B/blob/b55c26dad419064089f588837c5048843537577a/.treqs/assets/deepspeed-zero2-cpu.json) explicitly disables optimizer offload.

The [source installer](https://github.com/reproducible-ai/LDA-1B/blob/b55c26dad419064089f588837c5048843537577a/.treqs/scripts/install_roar_source.sh) fetches Roar commit `61e5e98ca823a25c19522870cb81d3ce730c391d`, runs its development installer to build both Python and native components, pins huggingface-hub 0.36.0, checks the imported source/native hashes and selects the preload tracer. It never follows a moving branch during a run. Using only `pip install` from Git would omit the separately built native tracer binaries.

## Inspect the recorded source and patches

These are read-only inspection commands for an existing clone containing the two commits, not commands recorded as part of GPU execution:

```bash
git show b55c26dad419064089f588837c5048843537577a:.treqs/workflows/robocasa-demo-canary.yaml
git diff --stat 06e6a274a9086cc26635a9fe663866335eb30fc5 b55c26dad419064089f588837c5048843537577a
git diff 06e6a274a9086cc26635a9fe663866335eb30fc5 b55c26dad419064089f588837c5048843537577a -- lda/ requirements.txt pyproject.toml
git diff 06e6a274a9086cc26635a9fe663866335eb30fc5 b55c26dad419064089f588837c5048843537577a -- .treqs/ tests/treqs/ .gitignore
```

The [complete pinned comparison](https://github.com/reproducible-ai/LDA-1B/compare/06e6a274a9086cc26635a9fe663866335eb30fc5...b55c26dad419064089f588837c5048843537577a) is the full patch reference. This report also includes the exact [runtime/dependency patch](patches/runtime-and-dependencies.patch), with its scope and digest in the [patch inventory](patches/README.md). Workflow, regression-test and operational-note changes remain separately inspectable at the pinned source.

## Verification actually performed

Remote setup ran `.venv/bin/python -m pytest -q tests/treqs`: **38 passed**. The `evaluate` command above checked input hashes, step count, checkpoint keys and finite tensors, and proved a trainable action tensor changed. After private upload, the harness independently downloaded the release, verified its inventory and hashes, compared the result sidecar to the logged receipt, compared published lineage topology with capture, and obtained the independent lineage auditor's PASS.

Before launch, the final operator's dependency-free recipe checks passed. Its `python3 -m pytest -q tests/treqs` command failed before collection because pytest was absent from that interpreter; no local full-suite pass is inferred from that command. The full recipe suite ran in remote setup as recorded above. These checks are supporting development evidence, not additional model-training runs.

No `roar reproduce` cold replay was executed for this record. The public reproduction command remains empty because this report does not publish the private lineage address or claim replay certification.
