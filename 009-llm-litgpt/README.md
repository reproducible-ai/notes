# 009 — litgpt (pretrain)

**Verdict: rebuilt, held short of a full published record.**

The `litgpt pretrain` path rebuilds from published materials, and the rebuilt
lineage re-runs independently: a cold `roar reproduce --lineage --run` on a
different machine with no GPU and no prior litgpt install cloned the fork, built
an environment from the recorded pins, ran all four steps and produced the same
checkpoint and the same validation loss. What is *not* yet settled is one
campaign-internal record check on the tokenization step; the row is held pending
that, not for anything wrong with litgpt.

Upstream: [`Lightning-AI/litgpt`](https://github.com/Lightning-AI/litgpt) 0.5.13
(`2685705`), Apache-2.0, 13.6k stars, actively maintained.
Fork: [`reproducible-ai/litgpt`](https://github.com/reproducible-ai/litgpt) at
`c657973`. **No litgpt source file was modified.**

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
pipeline. At `--seed 42` the loss trajectory was bit-identical across three
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

A truncated pretraining run, on purpose: **pythia-14m, 8 optimizer steps, 2,048
tokens** of WikiText-2 through litgpt's `TextFiles` data module, the path
`tutorials/pretrain.md` documents for custom corpora. We claim *reproduce*, not
*replicate* — the point is that the pipeline can be rebuilt and a metric
computed, not that a number is matched. litgpt's default `max_tokens` is 3e12,
nine orders of magnitude more.

```
Epoch 1 | iter  2 step 1 | loss train: 11.000
Epoch 1 | iter 16 step 8 | loss train:  9.914
Final evaluation | val loss: 9.903 | val ppl: 19998.620
```

Artifact: `out/final/lit_model.pth` (169 MB — litgpt checkpoints the whole
training state, so weights plus AdamW moments), published to
[`reproducible-ai/litgpt`](https://huggingface.co/reproducible-ai/litgpt).

## Logging

litgpt does ship experiment logging, so the question was live. It could not be
made to reach a public dashboard, and the reason is worth recording rather than
papering over:

- **mlflow** — litgpt's `mlflow` logger is Lightning's `MLFlowLogger`, which
  writes to a local `mlruns/` store. Nothing in the toolchain available here
  bridges that to a hosted, publicly viewable dashboard.
- **wandb** — the usual trick of aliasing a wandb-compatible tracker in as
  `sys.modules["wandb"]` does not work with Lightning, which performs runtime
  *submodule* imports (`from wandb.sdk.lib import RunDisabled`) that no
  module-object alias can satisfy. It fails identically whether the alias is a
  real tracker or a no-op stub, and it fails at
  `fabric.logger.log_hyperparams()`, before training starts. See issue #5.

So the run uses litgpt's `csv` logger, which is equally in-tree, needs no extra
dependency, and writes `out/logs/csv/version_0/metrics.csv` — a plain-text
artifact carrying the computed metrics, which is in the lineage and readable by
anyone. There is no experiment-dashboard link for this row, and it would have
been dishonest to manufacture one.

## Files

| file | contents |
|---|---|
| `commands.md` | the exact recipe, the bare-clone check, and the cold-rebuild transcript |
| `issues.md` | all seven obstacles: symptom, root cause, fix, upstream-worthiness |
| `costs.md` | four cloud attempts, $0.10 total |
| `patches/` | prepared (not submitted) upstream fix for issue #1 |
| `row.json` | the object published to the /models table |
