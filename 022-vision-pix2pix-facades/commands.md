# Commands and recorded facts — row 022

## Reproduce this row

```
roar reproduce 14df351c56d65be8181299f225e5c266f35e6aded43dc8068b5f0e2e76ac622b --lineage --run --no-puts
```

## The two recorded (traced) commands

```
roar run -n fetch_dataset -- bash ./datasets/download_pix2pix_dataset.sh facades

roar run -n train -- python train.py --dataroot ./datasets/facades --name facades_pix2pix \
    --model pix2pix --direction BtoA --n_epochs 1 --n_epochs_decay 1 \
    --save_epoch_freq 1 --num_threads 0
```

Both use bare, relocatable executables (`bash`, `python`); neither embeds the capture host's venv
path or `PATH`.

## Workload environment (isolated venv, pinned explicitly)

```
torch==2.4.0 torchvision==0.19.0 numpy==1.26.4 scikit-image==0.25.2 \
pillow==11.3.0 dominate==2.9.1 wandb==0.21.1
```

51 distributions were installed from those 7 declarations. Interpreter CPython 3.12.

## What the DAG records

3 jobs: `fetch_dataset` (1 input → 606 outputs), `train` (400 inputs → 15 outputs), and the
`roar put` publish step (2 inputs).

`fetch_dataset` recorded **0 pip pins**, which is correct — it runs a bash script driving `wget` and
`tar`, and loads no Python.

`train` recorded **25 pip pins** and 6 dpkg entries:

```
GitPython==3.1.59        certifi==2026.7.22        dominate==2.9.1
backports.tarfile==1.2.0 charset-normalizer==3.5.0 gitdb==4.0.12
idna==3.18               more-itertools==10.8.0    mpmath==1.3.0
numpy==1.26.4            packaging==26.3           pillow==11.3.0
platformdirs==4.11.3     protobuf==6.33.6          pydantic==2.13.4
requests==2.34.2         sentry-sdk==2.68.0        setuptools==84.0.0
smmap==5.0.3             sympy==1.14.0             torch==2.4.0
torchvision==0.19.0      triton==3.0.0             urllib3==2.7.0
wandb==0.21.1
```

dpkg: `libffi8`, `libssl3`, `libuuid1`, `libstdc++6`, `libfribidi0`, `libsqlite3-0`.

Every one of the 25 is explainable as the torch stack, the wandb stack (wandb is imported
unconditionally by `util/visualizer.py:7`) or `dominate` — there is no foreign ecosystem in the
record. No pin carries a local-version (`+`) suffix, so all 25 resolve from PyPI.

**Omissions worth knowing:** `typing-extensions` and `tqdm` are loaded but not recorded — see the
`issues.md` entry. `scikit-image` is absent and that is correct: it is imported only by
`models/colorization_model.py`, which this recipe never loads. The 12 `nvidia-*` CUDA libraries are
also absent because torch loads them by `dlopen` rather than by Python import; a rebuild picks them
up as torch's declared dependencies.

## Measured timings

| phase | measured | source |
|---|---|---|
| whole job | 207.6 s | `startedAt` 18:59:41.495Z → `completedAt` 19:03:09.074Z |
| `fetch_dataset` (traced) | 13.3 s | roar (trace 11.3 s + post 2.0 s) |
| `train` (traced) | 67.5 s | roar (trace 65.5 s + post 2.0 s) |
| epoch 1 | 28 s | upstream's own per-epoch timer |
| epoch 2 | 22 s | upstream's own per-epoch timer |
| steady-state per iteration | 0.055 s | 22 s / 400 iterations |
| setup + label + publish | 126.8 s | 207.6 − 13.3 − 67.5 |

Instance boot and agent registration were **not** measured: the host was already warm when this job
was queued.

## Peak GPU memory

**9,157 MiB — nvidia-smi at 1 Hz from the stage shell, 69 samples.**

Whole-device usage, including the CUDA context and the allocator reserve. Not comparable to
`torch.cuda.max_memory_allocated()`, which counts live tensors only and typically reads about half
as much. Obtaining that second figure would require editing `train.py`, which this row does not do.

## Dataset as fetched

400 train / 106 test / 100 val paired images, from
`http://efrosgans.eecs.berkeley.edu/pix2pix/datasets/facades.tar.gz` (30,168,306 bytes). No checksum
is published upstream, so this size is recorded here as the only integrity reference available.

## Published artifacts

| file | bytes | sha256 |
|---|---|---|
| `latest_net_G.pth` | 217,727,886 | `dba5bcb7c9e7079b9e23390035f0173876b1d7be4f310f57347449c9beee8358` |
| `latest_net_D.pth` | 11,089,494 | `899ebe4a71cfd561c03907ddbf447707423d7e2b03444a5a088b12d6573b5a50` |

Both were named on a single `roar put` so the discriminator is part of the same published graph.

## Tier-1 gate output

```
Tier-1 bar — 14df351c56d65be8 · reproducible-ai/pix2pix-facades
  [OK] clean-dag    Clean-DAG check — 14/14 passed  ·  3 jobs (published DAG)
  [OK] ai-bom       AI-BOM score: 100/100  ·  profile: Advanced
  [OK] public-urls  RESULT: ALL PUBLIC
  [OK] freeze       RESULT: PORTABLE

RESULT: REPRODUCIBLE RECORD — tier 1 complete (NOT yet a Certified reproduction)
```

Attribution asserted while the record was live: `owner_name = "Reproducible AI"`, `project_name =
null` (expected), `gitCommit = 750f61d686adf84defe9e586c0a069b461d97770`.
