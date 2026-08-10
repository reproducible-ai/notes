# Tier 2 — cold rebuild certification · row 005 timm ResNet-18 / Fashion-MNIST

**Result: PASS.** A host that had never seen this row rebuilt the published lineage from
the record alone. Exit code `0`, `Steps run: 3/3`, and every one of the **57** recorded
pins was present in the rebuilt environment at the exact recorded version — **0 missing,
0 mismatched, the diff is EXACT**.

This row was predicted to reproduce *because of* its record rather than despite it
(13/13 clean-DAG, BOM 100, `imports_vs_freeze_audit` Tier-A misses ZERO). It did.

| | |
|---|---|
| DAG | `42b381d91f299d028c45ff043a71e34e6c9e1122574585f32c3b3d99b31f10c2` |
| HF repo | `reproducible-ai/timm-classifier` |
| Upstream fork commit | `81bbe92e07c48e15fff34e2dffb0198549f867b4` |
| roar build | `roar, version 0.4.4rc2` (TestPyPI) |
| wheel sha256 | `3677618d4c42d66143baf42912c8ed932f9706d5511d032bb2898fda6a465471` |
| wheel filename | `roar_cli-0.4.4rc2-cp310-abi3-manylinux_2_34_x86_64.whl` (10,380,047 B) |
| Instance | `i-0b890ed5cb2a1038c` · g4dn.xlarge · 1×Tesla T4 15360 MiB · `ami-0f07f1a0b382b48f7` · us-east-2a |
| Recorded interpreter | Python 3.12.10 |
| Rebuild interpreter | Python 3.12.10 (exact match; no `PYTHON VERSION MISMATCH` prompt) |
| Host interpreter | Python 3.10.12 — bare `python` **absent** (`command -v python` → rc 127) |
| Date | 2026-08-10 |

## Tier-1 pre-flight (free, run before spending)

```
Tier-1 bar — 42b381d91f299d02 · reproducible-ai/timm-classifier
  [OK] clean-dag    Clean-DAG check — 13/13 passed  ·  4 jobs (published DAG)
  [OK] ai-bom       AI-BOM score: 100/100  ·  profile: Advanced
  [OK] public-urls  RESULT: ALL PUBLIC
  [OK] freeze       RESULT: PORTABLE
RESULT: REPRODUCIBLE RECORD — tier 1 complete
```

## Command

```
roar reproduce 42b381d91f299d028c45ff043a71e34e6c9e1122574585f32c3b3d99b31f10c2 \
    --lineage --run --no-puts -y --step-timeout 21600
```

`--pip-any-version` was **not** passed — the rebuild used the recorded pins, not
"whatever resolves today". `--no-puts` is mandatory (a cold host must not publish);
`-y` because a detached run is never a tty. `--step-timeout 21600`, never `0`.

## Result

```
Reproduction Complete
Repository: /root/cert005/reproduce/pytorch-image-models
Steps run: 3/3
```

Literal process exit code: **0** (captured by wrapping the invocation, not inferred
from stdout).

`3/3`, not `4/4`: the lineage has four jobs and the fourth is the `roar put` publish
step, which `--no-puts` deliberately excludes.

| step | command | exit | duration |
|---|---|---|---|
| 1 | `python reproduction/fetch_fashion_mnist.py --data-dir ./data` | 0 | 16.3 s |
| 2 | `python train.py … --model resnet18 --in-chans 1 --img-size 28 --epochs 5 --batch-size 256 --seed 42 --save-last-only …` | 0 | 2 m 35 s |
| 3 | `python validate.py … --checkpoint ./output/resnet18-fashion-mnist/last.pth.tar --results-file ./metrics/eval.json` | 0 | 12.4 s |

Per-step exit codes read back from the rebuild's own job database (`roar log`), not
just from stdout.

Negative greps over the whole log came back clean:
`ModuleNotFoundError` · `PYTHON VERSION MISMATCH` · `No tracer binary` ·
`command not found` · `Traceback` → **NONE FOUND**.

## Environment verification — the check that decides the row

`Environment ready` proves nothing on its own, so the rebuilt venv was enumerated and
diffed against the recorded per-job manifests (`jobs/<uid>.metadata.packages.pip` on the
**job** record).

```
step 1: 44 pins -> missing 0, mismatched 0
step 2: 45 pins -> missing 0, mismatched 0
step 3: 57 pins -> missing 0, mismatched 0
step 4:  0 pins  (roar put — excluded by --no-puts)

union recorded pins : 57
installed dists     : 84
MISSING   : NONE
MISMATCHED: NONE

PINS: 57/57   EXACT = True
```

roar's own installer line agrees: `Installing 57 packages from provenance`.

The 27 extras are the transitive closure — the 15 `nvidia-*` CUDA libraries pulled by
`torch`, plus `cffi`, `hf-xet`, `httptools`, `jinja2`, `markupsafe`, `markdown-it-py`,
`mdurl`, `pycparser`, `python-dotenv`, `setuptools`, `tzdata`, `uvloop`, `websockets`.
Extras are not a failure; a missing or mismatched recorded pin would have been.

Note the venv is built by `uv` and therefore ships **no `pip`** — `pip freeze` returns
empty. Distributions were enumerated with `importlib.metadata` and cross-checked with
`uv pip freeze --python <venv>`; both agree at 84.

## The environment is genuinely the recorded one (P0-14)

roar was installed under the **recorded** interpreter, so roar's interpreter and the
child's are the same:

```
uv tool install --python 3.12.10 --force --with huggingface-hub \
    /root/roar_cli-0.4.4rc2-cp310-abi3-manylinux_2_34_x86_64.whl
ln -sf /root/.local/bin/roar /usr/local/bin/roar
```

```
/root/cert005/reproduce/pytorch-image-models/.venv/pyvenv.cfg:
  version_info = 3.12.10
  include-system-site-packages = false
  uv = 0.12.3

sys.path:
  /usr/local/lib/python312.zip
  /usr/local/lib/python3.12
  /usr/local/lib/python3.12/lib-dynload
  /root/cert005/reproduce/pytorch-image-models/.venv/lib/python3.12/site-packages

HOST-SHADOW PATHS: NONE
```

Every package checked resolves **inside the venv**, none from a host root:

```
torch            …/.venv/lib/python3.12/site-packages/torch/__init__.py
torchvision      …/.venv/lib/python3.12/site-packages/torchvision/__init__.py
numpy            …/.venv/lib/python3.12/site-packages/numpy/__init__.py
yaml             …/.venv/lib/python3.12/site-packages/yaml/__init__.py
PIL              …/.venv/lib/python3.12/site-packages/PIL/__init__.py
safetensors      …/.venv/lib/python3.12/site-packages/safetensors/__init__.py
huggingface_hub  …/.venv/lib/python3.12/site-packages/huggingface_hub/__init__.py
trackio          …/.venv/lib/python3.12/site-packages/trackio/__init__.py
timm             /root/cert005/reproduce/pytorch-image-models/timm/__init__.py   ← the checked-out repo, as intended
```

`timm` resolving to the cloned working tree rather than site-packages is correct: the
recorded commands run timm's own `train.py`/`validate.py` from the repo root, and `timm`
is not a recorded pin — the row reproduces timm *from source at the recorded commit*.

Worth stating explicitly: the host interpreter is Python **3.10.12** and bare `python`
does not exist on this AMI (`command -v python` → rc 127). The recorded steps invoke
`python`. They ran, which means the recorded 3.12.10 venv demonstrably supplied the
interpreter. Nothing was symlinked or aliased to make that work.

### Build identity

The wheel sha256 was verified **before** installing, against the digest published on
TestPyPI for `roar-cli==0.4.4rc2`:

```
3677618d4c42d66143baf42912c8ed932f9706d5511d032bb2898fda6a465471  roar_cli-0.4.4rc2-…-x86_64.whl
10380047 bytes
```

Installing from the published TestPyPI build means no presigned S3 URL and no
overwrite-in-place ambiguity (P0-20). `roar --version` → `roar, version 0.4.4rc2`,
matching the build the row was captured on.

The tracer is present in the installed build (P0-10 clear) — six artefacts under
`…/roar-cli/lib/python3.12/site-packages/roar/bin/`:
`libroar_tracer_preload.so` (361,256) · `roar-proxy` (14,212,800) · `roar-tracer`
(675,472) · `roar-tracer-ebpf` (3,335,352) · `roar-tracer-preload` (807,248) ·
`roard` (3,092,768).

P0-7 purge was run unpiped and verified with `find`: no `roar_inject.pth`, no stale
`roar_cli-*.dist-info`, no stale `roar`/`roar-worker` entrypoints remained.

## Artefacts regenerated

Checked on the host before termination. **sha256 alongside every stat**, per
certifier-brief §2e.

| bytes | sha256 | path |
|---|---|---|
| 89,506,319 | `8b6741cf4f5c20321b796901098ad48ff506144e1005aa7583bdd081bb7b54ae` | `output/resnet18-fashion-mnist/last.pth.tar` |
| 400 | `0fc9c866709421980c18b231634fe3e3530667e38bd18ee317c3bf52bfad944d` | `output/resnet18-fashion-mnist/summary.csv` |
| 3,341 | `e1331bc2f986a3a77cd575a2cca3df3e650748e1f217b3e2c968a0d5fa88ddea` | `output/resnet18-fashion-mnist/args.yaml` |
| 209 | `a720fc4400d5f671d607aa13b94f327f10d6cad02451efa464c0e6e1e918ddf6` | `metrics/eval.json` |

**`last.pth.tar` regenerates at exactly the published size, 89,506,319 bytes** — the
`x-linked-size` on
`https://huggingface.co/reproducible-ai/timm-classifier/resolve/main/last.pth.tar` is
the same number. The **content** is not bit-identical, which is expected and documented
for this row (GPU training is not bit-reproducible at `--seed 42`; cuDNN algorithm
selection is unpinned and timm exposes no `--deterministic`). We claim *reproduce*, not
*replicate*.

`last.pth.tar` has **link count 1** on this rebuild, because the recorded command carries
`--save-last-only`. The "three names, one inode" hardlink behaviour recorded against the
original capture is timm's `CheckpointSaver` working correctly and is not a defect; it
simply does not arise under `--save-last-only`.

Step 1 re-fetched Fashion-MNIST (60,000 train / 10,000 validation) into
`data/FashionMNIST/raw/` — 8 files, `train-images-idx3-ubyte.gz` 26,421,880 B,
`t10k-images-idx3-ubyte.gz` 4,422,102 B, `train-labels-idx1-ubyte.gz` 29,515 B,
`t10k-labels-idx1-ubyte.gz` 5,148 B plus their decompressed forms.

The metric was **computed**, which is the row's claim; the values themselves are not
part of it:

```json
{"model": "resnet18", "top1": 85.56, "top1_err": 14.44,
 "top5": 99.57, "top5_err": 0.43, "param_count": 11.18,
 "img_size": 28, "crop_pct": 1.0, "interpolation": "bicubic"}
```

Recorded capture reported top-1 **85.67** / top-5 **99.73**; this rebuild gives
**85.56 / 99.57**. Same magnitude, differing in the second decimal — exactly the drift
the row already documents, not a defect.

Training summary (`summary.csv`), 5 epochs, converging as recorded:

```
epoch,train_loss,eval_loss,eval_top1,eval_top5,lr
0,1.5266704335171952,0.633612437915802,78.36,99.28,0.05
1,1.2209299079373352,0.5740737833976746,81.39,99.24,0.04522542485937369
2,1.1507881676029956,0.5225296738147736,82.71,99.42,0.032725424859373686
3,1.1035562335935414,0.48526961998939516,84.76,99.52,0.017274575140626316
4,1.068778628976936,0.45469011054039,86.0,99.54,0.004774575140626317
```

Model built as recorded: `Model resnet18 created, param count:11175370`, input_size
`(1, 28, 28)`, mean `(0.286,)`, std `(0.353,)` — i.e. the `--in-chans 1` grayscale path
worked because `--mean`/`--std` are passed explicitly, and the `--workers 0` single-process
loader ran without the `persistent_workers` `ValueError`. Both known upstream landmines
are already handled by the recorded command and the fork's patch; neither bit.

## Watchdog and cost

A watchdog was armed **before any work began**: `sudo shutdown -h +60`, verified
scheduled in `/run/systemd/shutdown/scheduled` (`MODE=poweroff`). Ceiling set at 60 min
= this row's expected wall clock (~25–30 min: apt + uv + roar install + venv build from
57 pins + ~3 min traced compute) with roughly 2× headroom on a slower host. It never
needed to fire; the instance was terminated explicitly.

| | |
|---|---|
| Instance up | 13:10:50 UTC |
| Reproduce started | ~13:15 UTC |
| Reproduce finished | 13:19:44 UTC (~4.5 min wall, of which 3 m 04 s is traced compute) |
| Terminated | 13:24 UTC |
| Total host time | ~14 min on g4dn.xlarge @ $0.526/hr |
| Spend | ≈ **$0.13**, against a budget of $0.50–1.00 |

First attempt. No retries.

## Friction encountered

1. **The uv-built reproduce venv has no `pip`.** `.venv/bin/python -m pip freeze` returns
   empty, so the brief's step 5b recipe ("`pip freeze` the reproduce venv") does not work
   as written on a uv-provisioned venv. Enumerating with `importlib.metadata` or
   `uv pip freeze --python <venv>` does. Worth folding into the standing brief; a certifier
   who reads the empty output as "no packages" could mis-call a row.
2. **`shutdown --show` is unavailable** on this AMI's util-linux (`unrecognized option`).
   Read `/run/systemd/shutdown/scheduled` instead to confirm the watchdog is armed.
3. Cosmetic, already on record: roar's reproduce progress output is block-buffered, so in
   a redirected log the `Creating virtual environment… / Installing 57 packages…` banner
   (lines 209–358) appears *after* the training output of the steps it describes. Read the
   log only after exit.

None of these are row defects.

## What this certification does and does not establish

- It **does** establish that the recorded 57-pin environment is sufficient to run the whole
  pipeline — fetch, train and evaluate — on a machine that had never seen the row,
  producing the recorded artefacts at the recorded sizes. That is the product claim, and
  it holds. This row passes **because of** its record, not despite it.
- It **does not** establish bit-identical reproduction, and does not attempt to.
- It **does not** cover the `put` step, which `--no-puts` excludes by design.
