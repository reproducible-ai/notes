# 005 — timm (ResNet-18 / Fashion-MNIST, truncated)

**Verdict: certified reproduction (tier 2).** The record is green *and* a host
that had never seen this row rebuilt it from the published lineage alone.

A ResNet-18 trained from scratch with timm's own `train.py`, then scored by
timm's own `validate.py`, rebuilds from published materials into a clean,
attributed, fully-scored lineage graph with a live metrics dashboard. Three
upstream sharp edges had to be worked around first, and one of them is a plain
bug that makes a documented command-line option unusable.

Upstream: [`huggingface/pytorch-image-models`](https://github.com/huggingface/pytorch-image-models)
("timm") 1.0.29.dev0 at `aa4b585`, Apache-2.0 — the reference implementation
library for image models, 37.0k stars, very actively maintained.
Fork: [`reproducible-ai/pytorch-image-models`](https://github.com/reproducible-ai/pytorch-image-models)
at `f741a2b`.

- DAG: https://glaas.ai/dag/af56b02d6c041c931f03ccf643f2e0fee97bbddb0072f26b91a291f142850dfd
- AI-BOM: 100/100 (profile: Advanced)
- Artifact: https://huggingface.co/reproducible-ai/timm-classifier
- Experiment: https://huggingface.co/spaces/reproducible-ai/experiments?project=resnet18-fashion-mnist

This record **supersedes** `42b381d9…`, an otherwise-equivalent capture that
carried no experiment link. Why it was re-run is the most useful thing on this
page, so it is the next section.

---

## The re-capture: a flag that nobody passed

The first capture of this row had every gate green — clean DAG 13/13, AI-BOM
100/100, all URLs public, a portable freeze, and a passing cold rebuild — and it
published **no experiment dashboard at all**. Not a broken one. None.

The cause was one missing command-line flag. timm gates *every* wandb call behind
`--log-wandb` (`train.py:397`, `default=False`). The pipeline had experiment
tracking fully wired at every other layer — the tracking backend installed, the
destination configured, the credential present — and the training script simply
never called it, because nobody passed the switch that turns it on. Nothing
failed. No gate has an opinion about a dashboard that was never written to.

This was not a one-row slip. Across the campaign's first ten rows only two
carried an experiment link, and six of the eight misses had the plumbing armed
and produced nothing for exactly this reason. **A tracking integration that is
configured but not enabled looks identical, from the outside, to one that
works.** The only difference is whether a specific flag appears in the recorded
command — which is precisely the kind of thing a lineage record is supposed to
make checkable, and which no automated check in this campaign was looking at.

So this row was re-captured with `--log-wandb` on, and the link above now
resolves to five epochs of real metrics.

### Verifying the link, and why a 200 is worthless

The obvious check — fetch the dashboard URL, confirm HTTP 200 — is **not a
check**. The dashboard is a Gradio app that returns 200 for any query string,
including projects that do not exist. Worse, the tracking client writes the
destination into its local database even when the upload *fails*, so a run that
logged nothing still yields a URL that returns 200.

The link on this page was verified by reading the run back out of the dashboard's
own API:

| metric | data points |
|---|---|
| `epoch`, `train_loss`, `eval_loss`, `eval_top1`, `eval_top5`, `lr` | 5 each |

Five points per metric, one per epoch, with timestamps matching the training
step's own clock. Those six names are exactly what timm's `update_summary()`
emits, so they could not exist unless timm's logging path really ran. That is the
standard this row holds itself to: **the run carries metrics, not the URL
resolves.**

---

## What was rebuilt

**ResNet-18 (11,175,370 parameters) trained from scratch on Fashion-MNIST at
28×28, single channel, 5 epochs, batch 256** — SGD (lr 0.05, Nesterov momentum
0.9, weight decay 5e-4), cosine schedule, no warmup, single-process data loading
(`-j 0`), seed 42. Then a separate `validate.py` pass over the 10,000-image
held-out split.

**This is a deliberately truncated run and the result is not converged.** timm's
default is `--epochs 300` (`train.py:245`); this row runs 5. timm's published
recipes train for hundreds of epochs on ImageNet-scale data. Five epochs on
Fashion-MNIST exists here to produce a *real* checkpoint and a *real* held-out
number in a few GPU-minutes, so the record has something honest to rebuild.
**Do not read the reported top-1 as a timm result.**

| | |
|---|---|
| training best val top-1 | 85.07 (epoch 4) |
| **`evaluate` step, held-out top-1** | **85.30** (top-5 99.65) |
| checkpoint | `last.pth.tar`, 89,506,383 B (weights + optimizer state) |
| checkpoint sha256 | `ff663730cd015c80ef873b0a6f21dcfbe8d48f62f40d9c50fabbc2bd33e835ef` |
| traced wall time | 3m42s (fetch 17.3s · train 170.6s · evaluate 33.9s) |

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
The assertion fired green on this run: `timm distributions visible: []`, and
`timm package -> …/repository/timm/__init__.py 1.0.29.dev0`.

**A bare-clone check before spending anything.** A fresh `git clone` of the fork,
a virtualenv holding *only* timm's six declared runtime dependencies
(`torch`, `torchvision`, `pyyaml`, `huggingface_hub`, `safetensors`, `numpy`)
plus the tracking backend, `PYTHONPATH` unset, CPU: all three steps ran to
completion and produced a real checkpoint and a real `eval.json` (top-1 78.60
after a single epoch). timm's declared dependency set is **honest** — nothing had
to be added by hand. That is not the norm; it is the cleanest declared-dependency
result in the campaign so far.

The bare clone also caught the thing that would have wasted a GPU run. Replaying
timm's exact `wandb.init(...)` call shape against the tracking backend on a CPU
box, for zero cost, produced:

```
TypeError: 'NoneType' object is not iterable
```

`--log-wandb` on its own is **not sufficient** — see "Upstream findings" #3.
Finding that on a laptop cost nothing; finding it on the GPU would have cost a
whole run, because it raises inside `init()` before epoch 0, after the
accelerator is already paid for.

## Upstream findings

Three, all in `issues.md`.

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

**#3 — `--log-wandb` degrades to a warning, so a run can train for hours logging
nothing.** If the tracking package is not importable, timm prints one WARNING
line and carries on; `update_summary(..., log_wandb=args.log_wandb and
has_wandb)` then silently resolves to `False` for the rest of the run. We hit
this for real: one warning 4,000 characters before the first loss, then a
complete run, exit 0, empty dashboard. Nothing downstream can distinguish that
from success. An explicit request to send metrics somewhere is treated as
advisory, which nothing else in `train.py`'s argument surface does.

Alongside it, an interop note that is **not** an upstream defect:
`--wandb-project` defaults to `None` and is forwarded verbatim into
`wandb.init(project=...)`. Real wandb accepts that and infers a name; a
wandb-compatible backend that declares `project` as a required string does not,
and dies with the `TypeError` above. Neither project is wrong on its own — the
incompatibility lives only at the seam. **Pass `--wandb-project` whenever you
pass `--log-wandb`** and it cannot arise. This row does.

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

`aa4b585...f741a2b`, **+271/-2 across 10 files**. Only three are upstream source,
and the re-capture added **zero** further upstream lines — its entire diff is in
the workflow file:

| file | ± | why |
|---|---|---|
| `timm/data/loader.py` | +5/-1 | the `persistent_workers` bug fix (#1) |
| `train.py` | +3/-0 | `--save-last-only` argument |
| `timm/utils/checkpoint_saver.py` | +13/-0 | honour `save_last_only` |
| `.treqs/workflows/…yaml` | +130 | the recorded pipeline |
| `reproduction/README.md`, `reproduction/fetch_fashion_mnist.py` | +98 | row material |
| `.gitignore`, 3× `.gitkeep` | +23 | keep output dirs in a clean checkout |

**Zero lines of the model definition, the optimizer, the scheduler or the
training loop were changed** — and, deliberately, zero lines of logging code.
Enabling `--log-wandb` is a flag, not a patch. Sprinkling tracking calls into
someone else's training script would have made this row a demo of our patch
rather than a reproduction of their work; a dashboard is not worth that.

## Recorded environment

The freeze records the **loaded** package set per step: 44 pins on
`fetch_dataset`, 56 on `train`, 57 on `evaluate` — 67 distinct across the row,
`torch==2.7.0` / `torchvision==0.22.0`, with **no local-version (`+cu…`) pins**,
so the freeze is portable and resolvable from PyPI.

The count is up from 57 on the superseded record, and the increase is real rather
than noise: enabling the tracking backend genuinely pulls a web-server stack
(`starlette`, `uvicorn`, `httpx`, `pydantic`, …) into the traced processes, and a
freeze that records what was loaded is correct to include it.

An imports-vs-freeze audit reports **Tier-A misses: zero** — nothing the workload
demonstrably imports is missing from the record. Its Tier-B heuristic flags
`requests` and `urllib3`; both are **false positives here**, checked rather than
assumed: torchvision downloads through the standard library's `urllib`, and the
Hub client on this substrate uses `httpx`. Neither module appears in
`sys.modules` after the fetch step runs.

## Cold rebuild (tier 2)

See `CERT-TIER2.md` for the full transcript. A host that had never seen this row
installed the recorded pins from the lineage and re-ran every step.

## Honest limits

- **Truncated, not converged.** 5 of timm's default 300 epochs. See above.
- **Not bit-reproducible on GPU.** Two runs at `--seed 42` on the same instance
  type gave different epoch-0 validation top-1. cuDNN algorithm selection is not
  pinned by `--seed` alone (timm exposes no `--deterministic`). We claim
  *reproduce*, not *replicate*: the pipeline rebuilds and a metric is computed.
  A CPU run is deterministic.
- **The dashboard is ours, not the rebuild's.** The cold rebuild deliberately
  does **not** publish to the experiment Space: without a credential the tracking
  shim falls back to a no-op and the run completes untracked. That is the correct
  behaviour for a third-party reproduction — it should not need, or get, write
  access to our dashboard — but it does mean the link on this page is evidence
  about *our* capture, not about the rebuild.
- **The superseded record is still a valid record.** `42b381d9…` was certified
  and is not withdrawn. It is superseded only because it lacks the experiment
  link.
