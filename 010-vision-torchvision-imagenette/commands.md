# 010 — torchvision classification · commands

Upstream: `pytorch/vision` at `34572106`, BSD-3-Clause.
Fork: `reproducible-ai/vision`, default branch `main`, reproduction commit
`5fb94ce`. **No upstream file was modified** — the fork adds a workflow,
`.gitignore` rules, two `.gitkeep` files, two additive scripts next to
`train.py`, and one document.

Everything runs from the **repository root**, invoking scripts **by path**. That
is not a stylistic choice: `python -m references.classification.train` imports
the in-tree `torchvision/` source package instead of the installed
distribution and fails on the missing C extensions (`issues.md` #4). Invoking by
path also puts `references/classification/` on `sys.path`, which is how the
sibling imports (`presets`, `utils`, `transforms`, `sampler`) resolve.

## 0. Setup

No install of torchvision is needed or wanted — the host image already carries a
working `torch` + `torchvision`. The one required hygiene step:

```bash
rm -rf *.egg-info src/*.egg-info
```

A leftover `torchvision.egg-info/` makes `importlib.metadata` report version
`0.29.0a0`, which exists on no index (`issues.md` #5).

## 1. Fetch the dataset

```bash
python references/classification/fetch_imagenette.py --root data --size 320px
```

Additive helper. Wraps `torchvision.datasets.Imagenette(download=True)`, which
fetches the fast.ai archive, verifies its MD5, and extracts to exactly the
`ImageFolder` layout `train.py` expects — 9,469 train / 3,925 val images across
10 classes. No credentials, no gated access.

## 2. Train

```bash
python references/classification/train.py \
    --data-path data/imagenette2-320 \
    --model resnet18 \
    --epochs 4 --batch-size 64 --workers 0 \
    --lr 0.05 --lr-scheduler cosineannealinglr \
    --lr-warmup-epochs 1 --lr-warmup-method linear \
    --output-dir out --device cuda
```

Unmodified upstream `train.py`. 592 optimizer steps, 3 m 43 s on one L40S.

Two flag notes:

- `--epochs 4` is the practical floor with `--lr-warmup-epochs 1`. `--epochs 1`
  gives `T_max = epochs - lr_warmup_epochs = 0` and the cosine schedule cannot be
  built (`issues.md` #2), so the obvious "does it run?" smoke command crashes.
- `--workers 0` is deliberate. It keeps the traced process tree single-process so
  the recorded environment is the environment the workload actually imported.
  It costs nothing here: throughput is bound by JPEG decode, ~219 img/s.

This writes **five** checkpoints — `model_0.pth` … `model_3.pth` plus
`checkpoint.pth`, 448 MB total — and there is no flag to ask for fewer
(`issues.md` #3).

## 3. Evaluate

```bash
python references/classification/evaluate_checkpoint.py \
    --data-path data/imagenette2-320 --split val \
    --model resnet18 --checkpoint out/checkpoint.pth \
    --metrics-out out/metrics.json \
    --batch-size 64 --workers 0 --device cuda
```

Additive helper that imports and calls `train.evaluate` **unchanged**. It exists
for two reasons, both upstream limitations:

1. `train.py --test-only --resume out/checkpoint.pth` cannot read the file
   `train.py` just wrote — `UnpicklingError` on `argparse.Namespace` under
   `weights_only=True` (`issues.md` #1, patch in `patches/`). The helper
   allow-lists `argparse.Namespace` for that one load.
2. `--test-only` only *prints* the accuracy. A record needs it as a durable
   artefact, so the helper writes `metrics.json`.

Result: **top-1 55.31 %**, top-5 92.23 % on the held-out split.

## 4. Publish

```bash
roar put out/checkpoint.pth hf://reproducible-ai/vision-classifier --public --yes --no-tag
```

→ [huggingface.co/reproducible-ai/vision-classifier](https://huggingface.co/reproducible-ai/vision-classifier)
(`checkpoint.pth`, 89,551,113 B).

## Bare-clone check

Run before any GPU was provisioned: a fresh clone, a scratch venv containing only
`torch`, `torchvision` and `pillow`, `PYTHONPATH` unset, on CPU with a
tiny subset. The full four-step sequence above completed and produced a
`checkpoint.pth` and a `metrics.json` with no `ModuleNotFoundError`. That check is
what surfaced issues #1, #2 and #4 — all three would otherwise have been found
on a GPU at ~30× the cost per iteration.
