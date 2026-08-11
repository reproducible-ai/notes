# 005 — upstream findings (`huggingface/pytorch-image-models`)

Three findings, all hit while rebuilding a five-epoch ResNet-18 on Fashion-MNIST
from timm's own `train.py` / `validate.py` at `aa4b585` (1.0.29.dev0).

Per campaign policy **nothing here was reported upstream** — no issues, no pull
requests, no comments. The patch in `patches/` is published so the finding is
actionable by anyone who wants it.

---

## #1 — `--workers 0` / `-j 0` raises before the first batch

**Severity: real bug. A documented option is unusable.**

`timm/data/loader.py::create_loader()` builds its DataLoader kwargs with

```python
persistent_workers=persistent_workers      # default True
```

and forwards them to `torch.utils.data.DataLoader`, which rejects that
combination when there are no workers:

```
ValueError: persistent_workers option needs num_workers > 0
```

Reproduce (any timm checkout, any dataset):

```bash
python train.py --data-dir ./data --dataset torch/fashion_mnist \
    --model resnet18 --num-classes 10 --in-chans 1 --img-size 28 \
    --mean 0.2860 --std 0.3530 --workers 0 --epochs 1
```

`validate.py --workers 0` fails identically — it reaches the same helper.

Single-process loading is not an exotic request. It is the sane choice on a
small dataset, it is what you fall back to in a container with a small
`/dev/shm`, and it is required by most profilers and tracers, which cannot
follow work into forked DataLoader workers. `train.py --help` advertises
`-j, --workers N (default: 4)` with no lower bound and no warning.

**Fix** — one expression, no behaviour change on the default path (where
`num_workers > 0` is already True):

```python
persistent_workers=persistent_workers and num_workers > 0,
```

`patches/0001-gate-persistent_workers-on-num_workers-0.patch`.

---

## #2 — `--in-chans 1` keeps the 3-channel mean/std, then crashes

**Severity: sharp edge. Correct behaviour is a judgement call, so not patched.**

`timm.data.config.resolve_data_config()` derives `input_size` from `in_chans`,
so `--in-chans 1 --img-size 28` correctly yields `(1, 28, 28)`. But `mean` and
`std` keep the 3-channel ImageNet defaults unless passed explicitly. The
mismatch is not caught at configuration time; it surfaces in the transform on
the first batch:

```
RuntimeError: output with shape [1, 28, 28] doesn't match the broadcast shape [3, 28, 28]
```

This is the first thing anyone training a grayscale dataset with timm will hit,
and the traceback points at a normalisation tensor rather than at the flag that
caused it.

**Worked around, not patched.** This row passes `--mean 0.2860 --std 0.3530`
(Fashion-MNIST statistics) on the command line. Upstream has a genuine choice to
make — collapse the default mean/std to `in_chans` channels, or reject the
combination at parse time with a message naming `--mean`/`--std` — and either is
more than a one-line change, so we did not presume.

---

## #3 — `--log-wandb` degrades to a warning, so a run can train for hours logging nothing

**Severity: sharp edge. The failure is silent by design, and the exit code is 0.**

`--log-wandb` is the single switch gating every wandb call in `train.py`
(`train.py:397`, `default=False`). Ask for it without the package present and
timm does not stop:

```python
try:
    import wandb
    has_wandb = True
except ImportError:
    has_wandb = False
...
if args.log_wandb:
    if has_wandb:
        wandb.init(...)
    else:
        _logger.warning(
            "You've requested to log metrics to wandb but package not found. "
            "Metrics not being logged to wandb, try `pip install wandb`")
```

Then `utils.update_summary(..., log_wandb=args.log_wandb and has_wandb)` quietly
resolves to `False` for the rest of the run (`train.py:1190`).

We hit this for real. On a first pass the environment had no importable `wandb`,
and the run emitted exactly one WARNING line at startup — 4,000 characters
before the first loss — then trained happily to completion and exited **0** with
an empty dashboard. Nothing downstream can tell that apart from a successful
logging run: the checkpoint is fine, `summary.csv` is fine, the exit code is
fine. The only evidence is one warning scrolled off the top of the log.

The user typed a flag whose entire purpose is "send my metrics somewhere". When
that is impossible, treating it as advisory converts an explicit request into a
silent no-op. Nothing else in `train.py`'s argument surface behaves this way —
an unknown `--model` raises, an unreadable `--data-dir` raises.

**Suggested fix**, matching how the rest of the script treats an unsatisfiable
request:

```python
if args.log_wandb and not has_wandb:
    raise RuntimeError(
        "--log-wandb requires the wandb package; install it or drop the flag")
```

**Not patched** — unlike #1 this is a deliberate upstream choice about strictness
rather than an outright bug, and reasonable maintainers land either way. Recorded
because the cost is asymmetric: the warning is free to ignore and the lost run is
not.

### Interop note, not an upstream defect: `--wandb-project` is effectively required

`--wandb-project` defaults to `None` (`train.py:399`) and is forwarded verbatim
into `wandb.init(project=...)`. Real wandb accepts that and infers a project
name. **trackio does not** — its `init()` signature declares `project: str` as
required, so a `None` arrives and dies inside the call:

```
TypeError: 'NoneType' object is not iterable
```

That happens at logger construction, before the first batch, i.e. after the
accelerator is already paid for. Any wandb-compatible backend that does not
implement wandb's project-inference behaviour will hit it the same way.

Neither project is wrong on its own; the incompatibility only exists at the
seam. **Pass `--wandb-project` explicitly whenever you pass `--log-wandb`** and
it cannot arise. This row does.

---

## Not a defect: three checkpoint names, one blob

Recorded here because it looks like a recording error and is not.

`timm.utils.CheckpointSaver.save_checkpoint()` writes the epoch's state once and
then calls `os.link()` to create the other names: `last.pth.tar`,
`checkpoint-<epoch>.pth.tar`, and — when the eval metric improves —
`model_best.pth.tar` all point at **one inode**. A finished run therefore
advertises up to three checkpoint files that are byte-identical by construction.

Any content-addressed tool looking at such a run sees *N* paths and fewer
distinct hashes. That is timm behaving exactly as designed, not a lineage or
hashing fault, and it should not be filed as one.

It is still redundant bookkeeping for a short run, so this fork adds an opt-in
`--save-last-only` to `train.py` (3 lines in `train.py`, 13 in
`CheckpointSaver`) that skips both copies and leaves a single `last.pth.tar`.
Default behaviour is untouched. Not proposed upstream — it is a convenience for
this row, not a defect fix.

---

## What was clean

Worth stating, because it is unusual:

- **`requirements.txt` is honest.** A fresh clone plus exactly the six declared
  runtime dependencies (`torch`, `torchvision`, `pyyaml`, `huggingface_hub`,
  `safetensors`, `numpy`), with `PYTHONPATH` unset, ran `fetch_dataset`,
  `train` and `evaluate` to completion with **no `ModuleNotFoundError` and
  nothing added by hand**. Several other rows in this campaign needed
  undeclared packages installed before anything would start.

  Re-verified on the re-capture, which adds one package the six do not cover:
  an experiment-tracking backend for `--log-wandb`. That is correct — timm
  declares `wandb` nowhere in `requirements.txt` precisely because logging is
  opt-in — and installing it changed nothing else: `torch`, `torchvision`,
  `numpy` and `huggingface_hub` all kept the versions the six declared deps had
  already resolved to. **No conflict, no downgrade.** Optional integrations that
  quietly re-resolve the core stack are common; this one does not.
- **No editable install is required.** `train.py` and `validate.py` run from the
  repository root and import the checked-out `timm/` package directly, so the
  code under test is unambiguous.
- **`torch/*` dataset routing works as documented**, needs no credentials, and
  makes a small honest reproduction possible without an ImageNet download.
- **`validate.py` writes machine-readable results** (`--results-file … 
  --results-format json`), so the metric can be a first-class recorded artifact
  instead of a number scraped from stdout. Not every training repo offers this.
