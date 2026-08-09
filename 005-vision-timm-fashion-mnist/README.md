# 005 — timm (ResNet-18 / Fashion-MNIST, truncated)

**Verdict: reproducible record (tier 1) — complete and green. Cold certification
(tier 2) has not been run yet.**

A ResNet-18 trained from scratch with timm's own `train.py`, then scored by
timm's own `validate.py`, rebuilds from published materials into a clean,
attributed, fully-scored lineage graph. Two upstream defects had to be worked
around first, and one of them is a plain bug that makes a documented command-line
option unusable.

Upstream: [`huggingface/pytorch-image-models`](https://github.com/huggingface/pytorch-image-models)
("timm") 1.0.29.dev0 at `aa4b585`, Apache-2.0 — the reference implementation
library for image models, 37.0k stars, very actively maintained (last push
2026-08-08, the day before this row ran).
Fork: [`reproducible-ai/pytorch-image-models`](https://github.com/reproducible-ai/pytorch-image-models)
at `81bbe92`.

- DAG: https://glaas.ai/dag/42b381d91f299d028c45ff043a71e34e6c9e1122574585f32c3b3d99b31f10c2
- AI-BOM: 100/100 (profile: Advanced)
- Artifact: https://huggingface.co/reproducible-ai/timm-classifier

---

## What was rebuilt

**ResNet-18 (11,175,370 parameters) trained from scratch on Fashion-MNIST at
28×28, single channel, 5 epochs, batch 256** — SGD (lr 0.05, Nesterov momentum
0.9, weight decay 5e-4), cosine schedule, no warmup, single-process data loading
(`-j 0`), seed 42. Then a separate `validate.py` pass over the 10,000-image
held-out split.

**This is a deliberately truncated run and the result is not converged.** timm's
published recipes train for hundreds of epochs on ImageNet-scale data. Five
epochs on Fashion-MNIST exists here to produce a *real* checkpoint and a *real*
held-out number in a few GPU-minutes, so the record has something honest to
rebuild. **Do not read the reported top-1 as a timm result.**

| | |
|---|---|
| training best val top-1 | 85.93 (epoch 4) |
| **`evaluate` step, held-out top-1** | **85.67** (top-5 99.73) |
| checkpoint | `last.pth.tar`, 89.5 MB (weights + optimizer state) |
| traced wall time | 3m47s (fetch 18.3s · train 166.5s · evaluate 42.2s) |

The two top-1 figures differ because the in-training validation crops at
`crop_pct` 0.95 while `validate.py` is run at `--crop-pct 1.0`. The published
number is the one the `evaluate` step computed against the published file.

Three steps, chained, all traced: `fetch_dataset` → `train` → `evaluate`. The
metric is computed in **its own step** against the **published checkpoint**, not
scraped out of the training log — `evaluate` reads `last.pth.tar` and writes
`metrics/eval.json`. `last.pth.tar` is the final-epoch checkpoint and is the
exact file published to Hugging Face, so the reported top-1 belongs to the
weights a reader can download.

## What made this row work

**Fashion-MNIST, not ImageNet.** timm's data path is built around large
ImageNet-style datasets, but `--dataset torch/fashion_mnist` routes through
torchvision, needs no credentials, downloads ~30 MB from a public mirror, and
still exercises the real `train.py` — the same argument parser, the same
`create_loader`, the same `CheckpointSaver`, the same AMP/scheduler machinery.

**No editable install.** Nothing runs `pip install -e .`. `train.py` and
`validate.py` are executed from the repository root and import the checked-out
`timm/` package directly, and the workflow asserts before training that **no
`timm` distribution is visible** to `importlib.metadata` — otherwise the
recorded package list would pin a PyPI `timm` that is not the code being run.

**A bare-clone check before spending anything.** A fresh `git clone` of the fork,
a virtualenv holding *only* timm's six declared runtime dependencies
(`torch`, `torchvision`, `pyyaml`, `huggingface_hub`, `safetensors`, `numpy`),
`PYTHONPATH` unset, CPU: all three steps ran to completion and produced a real
checkpoint and a real `eval.json` (top-1 77.41 after a single epoch). timm's
declared dependency set is **honest** — nothing had to be added by hand. That is
not the norm; it is the cleanest declared-dependency result in the campaign so
far.

## Upstream findings

Two, both in `issues.md`.

**#1 — `-j 0` / `--workers 0` is broken (real bug, patch included).**
`create_loader()` forwards `persistent_workers=True` unconditionally to
`torch.utils.data.DataLoader`, which rejects it when `num_workers == 0`:

```
ValueError: persistent_workers option needs num_workers > 0
```

Single-process data loading is a documented, ordinary choice — small datasets,
containers with little `/dev/shm`, and any run being profiled or traced — and it
fails before the first batch, in both `train.py` and `validate.py`. The fix is
one expression: `persistent_workers=persistent_workers and num_workers > 0`.
`patches/0001-gate-persistent_workers-on-num_workers-0.patch`. This is the only
upstream source file this fork modifies for correctness.

**#2 — `--in-chans 1` silently keeps 3-channel normalisation.**
`resolve_data_config()` derives `input_size` from `in_chans` but leaves
`mean`/`std` at the ImageNet 3-channel defaults, so a single-channel run dies on
the first batch with `RuntimeError: output with shape [1, 28, 28] doesn't match
the broadcast shape [3, 28, 28]`. Worked around from the command line
(`--mean 0.2860 --std 0.3530`) rather than patched, because the right upstream
behaviour is a judgement call — collapse the default to a scalar, or refuse the
combination with a clear message — not a one-liner.

**One thing that is *not* a defect.** `timm.utils.CheckpointSaver` writes each
epoch's state under up to three names — `last.pth.tar`, `checkpoint-<n>.pth.tar`
and `model_best.pth.tar` — using `os.link()`. They are hardlinks to one inode:
byte-identical by construction, one blob under three paths. A content-addressed
consumer that sees "three checkpoints, one hash" is seeing timm behaving
correctly, not a recording error. It is only wasteful bookkeeping for a short
run, so this fork adds a 3-line `--save-last-only` flag to `train.py` (plus 13
lines in `CheckpointSaver`) that skips both copies and leaves one checkpoint
file. Default behaviour is unchanged.

## Fork diff

`aa4b585...81bbe92`, **+247/-2 across 10 files**. Only two are upstream source:

| file | ± | why |
|---|---|---|
| `timm/data/loader.py` | +5/-1 | the `persistent_workers` bug fix (#1) |
| `train.py` | +3/-0 | `--save-last-only` argument |
| `timm/utils/checkpoint_saver.py` | +13/-0 | honour `save_last_only` |
| `.treqs/workflows/…yaml` | +106 | the recorded pipeline |
| `reproduction/README.md`, `reproduction/fetch_fashion_mnist.py` | +98 | row material |
| `.gitignore`, 3× `.gitkeep` | +23 | keep output dirs in a clean checkout |

**Zero lines of the model definition, the optimizer, the scheduler or the
training loop were changed.**

## Recorded environment

57 pins on the traced steps, `torch==2.7.0` / `torchvision==0.22.0` with **no
local-version (`+cu…`) pins** — the freeze is portable and resolvable from PyPI.
Cross-checked against the bare-clone venv: every package the workload actually
needed is either recorded directly or is a declared dependency of something
recorded.

## Honest limits

- **Truncated, not converged.** Five epochs. See above.
- **Not bit-reproducible on GPU.** Two runs at `--seed 42` on the same instance
  type gave epoch-0 val top-1 of 76.56 and 77.18. cuDNN algorithm selection is
  not pinned by `--seed` alone (timm exposes no `--deterministic`). We claim
  *reproduce*, not *replicate*: the pipeline rebuilds and a metric is computed.
  A CPU run is deterministic.
- **No experiment-tracker link.** Upstream's W&B logging (`--log-wandb`) exists
  but is optional and is not enabled here, so no tracker URL is recorded. None
  was bolted on.
- **Tier 2 not run.** This is a green *record*; a cold
  `roar reproduce … --lineage --run` on a host that has never seen the row has
  not been performed.
