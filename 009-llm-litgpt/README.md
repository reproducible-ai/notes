# 009 — litgpt (pretrain)

**Verdict: reproduced, and independently certified.**

The `litgpt pretrain` path rebuilds from published materials, and the published
lineage re-runs on a machine that has never seen it. A cold
`roar reproduce --lineage --run --no-puts` on a freshly launched host cloned the
fork, built an environment from the recorded pins, ran **all four steps (exit 0,
4/4)** and produced the same 169 MB checkpoint and the same validation loss —
with **all 62 recorded pins present at the recorded versions**, 0 missing and 0
mismatched. Full evidence in `CERT-TIER2.md`.

Upstream: [`Lightning-AI/litgpt`](https://github.com/Lightning-AI/litgpt) 0.5.13
(`2685705`), Apache-2.0, 13.6k stars, actively maintained.
Fork: [`reproducible-ai/litgpt`](https://github.com/reproducible-ai/litgpt) at
`fe35987`. **No litgpt source file was modified** — the 298-line diff is a
workflow, `.gitignore` rules, four `.gitkeep` files and one additive helper
module.

---

## Summary

litgpt was picked deliberately as a *different shape* of LLM repository from
nanoGPT and minGPT, which are already rows: a heavier, more abstracted framework
built on Lightning Fabric, with a jsonargparse CLI, twenty-odd model
architectures, a config hub, and pluggable data modules and loggers. The
question was whether that abstraction reproduces as cleanly as a single-file
trainer.

The answer: **the training code reproduces very cleanly; the packaging around it
does not.** Nothing went wrong inside litgpt's model, optimizer or data
pipeline. At `--seed 42` the loss trajectory was bit-identical across
independent environments, and the only variation anywhere came from numeric
precision (fp16 on a T4 versus fp32 on CPU). Every obstacle in `issues.md` — all
seven — is a packaging, dependency-range or repository-hygiene problem, and
four of them are things a user hits before a single token is trained.

The sharpest is issue #1: `litgpt download`, the first command in every litgpt
tutorial, raises `AttributeError` on huggingface_hub >= 1.0, and litgpt's own
pin (`>=0.30,<1.4`) permits exactly that. A fresh `pip install litgpt` today
resolves a hub that cannot download a model. It is a three-line fix; a prepared
patch is in `patches/`.

The second theme is that the *documented* install does not match the *declared*
one. `torchmetrics` and `litdata` are imported unconditionally on the pretrain
path but declared only as optional extras (#2); `wandb` and `mlflow` are
advertised as logger choices in `_SUPPORTED_LOGGERS` and in every one of ~50
config files, yet appear in no dependency group at all, and `choose_logger()`
does not check the availability constants that sit right there in
`litgpt/constants.py` (#4). Meanwhile the pinned `litdata==0.2.59` pulls an
unbounded `torchvision`, and since every torchvision release hard-pins an exact
`torch==`, a plain `pip install 'litgpt[extra]'` quietly replaced a curated
PyTorch 2.7.0 with 2.13.0 and about 4 GB of `nvidia-*` wheels (#3). None of this
is exotic — it is what happens when a large framework's dependency ranges are
never tested from an empty environment.

## What was rebuilt

A truncated pretraining run, on purpose: **pythia-14m (14,067,712 parameters), 8
optimizer steps, 2,048 tokens** of WikiText-2 through litgpt's `TextFiles` data
module, the path `tutorials/pretrain.md` documents for custom corpora. We claim
*reproduce*, not *replicate* — the point is that the pipeline can be rebuilt and
a metric computed, not that a number is matched. It was matched anyway:

```
Epoch 1 | iter  2 step 1 | loss train: 10.979 | iter time: 3194.35 ms
Epoch 1 | iter 16 step 8 | loss train:  9.884 | iter time:   28.05 ms
Final evaluation | val loss: 9.738 | val ppl: 16948.362
```

The cold rebuild returned `val_loss = 9.737926483154297` — the same digits.

Artifact: `out/final/lit_model.pth` (169 MB — litgpt checkpoints the whole
training state, so weights plus AdamW moments), published to
[`reproducible-ai/litgpt`](https://huggingface.co/reproducible-ai/litgpt).

## What a full run would actually cost

The truncation here is not a rounding — it is **1.46 billion-fold**, and it is
worth being precise about why.

`litgpt pretrain` has a default token budget, and it is large:
`max_tokens=int(3e12)` in the `pretrain()` signature at `litgpt/pretrain.py:61`.
`validate_args()` makes `max_tokens` a *required* argument, so that default is
what runs when a caller does not override it — including with `--data TextFiles`,
because the data module is orthogonal to the budget and the loader is wrapped in
a `CycleIterator` that simply repeats the corpus.

Measuring the split rather than scaling the headline:

- **Fixed — 580.2 s, $0.085.** 156.4 s host provisioning, 121.8 s environment
  setup, 112.0 s tokenizer download, 2.4 s WikiText-2 fetch, 62.1 s litdata
  tokenization, 107.5 s of the pretrain step that is model construction,
  `torch.compile` and the final validation pass, 0.7 s labelling, 17.7 s
  checkpoint upload.
- **Variable — 26.900 ms per iteration**, the mean of the seven steady-state
  `iter_time` values in `metrics.csv`. The *first* logged iteration is 112.6 ms
  because it carries the `torch.compile` warm-up, which is a one-off, not a rate.
  At `micro_batch_size 1 × max_seq_length 128` that is 128 tokens per iteration,
  or **$3.07 × 10⁻⁸ per token**.

3e12 tokens is therefore 23.4 billion iterations ≈ **175,133 GPU-hours ≈ 20.0
years on one T4 ≈ $92,120**. The fixed part is rounding error at that scale.

The number is not advice to spend $92k; it is the honest statement that litgpt's
own default budget is nine orders of magnitude beyond what a single T4 can serve,
and that the truncation is what makes this row runnable at all. It holds every
other flag at this row's values — raising the block size or the batch would
change throughput substantially.

*(An earlier version of this row left the full-run estimate `null`, asserting
that litgpt defines no default budget for a from-scratch pretrain on custom
`TextFiles`. That assertion was wrong; the default is at `pretrain.py:61` and is
now used.)*

## Logging — the flag exists, and it still cannot reach a dashboard

litgpt ships experiment logging and it is switched on by a flag, so the usual
excuse ("upstream has no integration") does not apply to this row. It was
enabled, and it fails — for a reason that lives in Lightning rather than in
litgpt. The bridge from `wandb` to a hosted dashboard is a module alias
(`sys.modules["wandb"] = trackio`), and `WandbLogger` defeats an alias twice:

- `lightning/pytorch/loggers/wandb.py:312` gates on
  `RequirementCache("wandb>=0.12.10")`, which reads **installed distribution
  metadata**. A `sys.modules` entry is not a distribution, so the constructor
  raises `Requirement 'wandb>=0.12.10' not met`.
- Install the real `wandb` to get past that, and it dies one step later at
  `wandb.py:390` on `from wandb.sdk.lib import RunDisabled` — a **submodule**
  import, resolved through the aliased package's `__path__`, which now points at
  trackio: `No module named 'wandb.sdk'`.

Both were reproduced by direct execution against **lightning 2.6.5** — the exact
version this row's freeze records — with wandb 0.28.1 and trackio 0.20.2. The
path is unreachable rather than unlucky: `litgpt/pretrain.py:156` calls
`fabric.logger.log_hyperparams()`, and `WandbLogger.log_hyperparams`
(`wandb.py:435`) touches the `experiment` property before a single training step
runs; `log_metrics` does the same.

Making it work means patching Lightning, a *dependency* of the workload, which
would forfeit the zero-upstream-lines property this row rests on. So
`experimentUrl` is `null` and stays `null`. The computed metrics are published
instead as `out/logs/csv/version_0/metrics.csv` — a plain-text artifact, in the
lineage, readable by anyone. Manufacturing a link to an empty dashboard would
have been worse than having none. See `issues.md` #5.

## Files

| file | contents |
|---|---|
| `commands.md` | the exact recipe, the bare-clone check, and the cold-rebuild transcript |
| `issues.md` | all seven obstacles: symptom, root cause, fix, upstream-worthiness |
| `CERT-TIER2.md` | the tier-2 certification: exit code, step count, manifest diff, artefact hashes |
| `costs.md` | every cloud attempt and what it cost |
| `patches/` | prepared (not submitted) upstream fix for issue #1 |
| `row.json` | the object published to the /models table |
