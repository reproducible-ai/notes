# 009 — litgpt pretrain · issues

Every obstacle met rebuilding the `litgpt pretrain` path from published
materials, at `Lightning-AI/litgpt` 0.5.13 (`2685705`). Symptom → root cause →
fix → upstream-worthy?

litgpt is a large, well-maintained framework rather than a single-file trainer,
and that shows in the shape of the problems: none of these are algorithmic. All
seven are packaging, dependency-range or repository-hygiene issues — the kind of
thing that only surfaces when you install from scratch rather than from a
working checkout.

---

## 1. `litgpt download` is broken on huggingface_hub >= 1.0, which litgpt's own pin allows — BLOCKER

**Symptom.** The first command in every litgpt tutorial fails immediately:

```
$ litgpt download EleutherAI/pythia-14m --tokenizer_only true
AttributeError: module 'huggingface_hub.constants' has no attribute
                'HF_HUB_ENABLE_HF_TRANSFER'
```

**Root cause.** `litgpt/scripts/download.py:77` reads and later writes
`huggingface_hub.constants.HF_HUB_ENABLE_HF_TRANSFER` to opt into `hf_transfer`.
That constant was removed in huggingface_hub 1.0. litgpt's pin is
`huggingface-hub>=0.30,<1.4`, so a fresh resolve happily picks 1.3.7 and the
download path dies. Nothing guards the attribute.

**Fix / workaround.** Pinned `huggingface-hub>=0.30,<1.0` (0.36.2 resolved) in
the setup step. A prepared upstream patch that guards the attribute instead is
in `patches/0001-download-guard-HF_HUB_ENABLE_HF_TRANSFER.patch`.

**Upstream-worthy?** Yes — highest value of anything here. It breaks the
documented entry point on a dependency version the project itself permits, and
it is a three-line fix.

---

## 2. `torchmetrics` is required by the pretrain path but is an optional extra

**Symptom.** `ModuleNotFoundError: No module named 'torchmetrics'` on a base
`pip install litgpt`.

**Root cause.** `litgpt/pretrain.py:19` does
`from torchmetrics.aggregation import RunningMean` at module import — an
unconditional, top-level import on the pretraining code path. `torchmetrics` is
declared only in `optional-dependencies.extra`. Same for `litdata`, which every
pretraining data module needs.

**Fix / workaround.** Install `torchmetrics` and `litdata` explicitly.
`tutorials/pretrain.md` does say to run `pip install "litgpt[all]"` first, so
this is documented — but the *code* gives no hint, and the base install of a
package whose headline feature is pretraining cannot pretrain.

**Upstream-worthy?** Moderate. Either move the pretrain-only deps into a
`pretrain` extra with a clear error, or guard the import with the
`RequirementCache` pattern `litgpt/constants.py` already uses everywhere else.

---

## 3. `litdata==0.2.59` drags an exact `torch==` pin through `torchvision`

**Symptom.** `pip install 'litgpt[extra]'` on a host with a curated PyTorch
build replaced `torch 2.7.0` with `torch 2.13.0`, pulling roughly 4 GB of
`nvidia-*` wheels nobody asked for.

**Root cause.** litgpt hard-pins `litdata==0.2.59`. litdata declares an
**unbounded** `torchvision` dependency. Every torchvision release hard-pins an
exact `torch==X.Y.Z`, so the resolver takes the newest torchvision and drags its
torch with it. litgpt's own `torch>=2.7` is satisfied either way, so nothing
warns.

**Fix / workaround.** Pin `torch` and `torchvision` to the host pair
(`2.7.0` / `0.22.0`) in the install command.

**Upstream-worthy?** Yes, though the fix belongs partly in litdata (bound
torchvision, or make it an extra — litdata needs it only for image decoding,
which a token pipeline never touches). litgpt could also relax its exact
`litdata==` pin.

---

## 4. `wandb` and `mlflow` are offered logger choices with no dependency declaration

**Symptom.** `--logger_name wandb` or `--logger_name mlflow` fails with a
Lightning-level `ModuleNotFoundError` and no litgpt-level hint.

**Root cause.** `_SUPPORTED_LOGGERS` in `litgpt/constants.py` is
`("csv", "tensorboard", "wandb", "mlflow", "litlogger")`, and every one of the
~50 config files in `config_hub/` advertises all five. But `pyproject.toml`
declares only `tensorboard` and `litlogger`; neither `wandb` nor `mlflow`
appears in *any* dependency group. `litgpt/constants.py` defines
`_WANDB_AVAILABLE` and `_MLFLOW_AVAILABLE` — and `choose_logger()` never
consults them, unlike the `litlogger` branch immediately below, which does check
`_LITLOGGER_AVAILABLE` and raises a helpful error.

**Fix / workaround.** Used `--logger_name csv`, which needs no extra dependency
and writes `out/logs/csv/version_0/metrics.csv`.

**Upstream-worthy?** Yes, and it is a two-line fix: `choose_logger()` already has
the availability constants imported; it just needs the same guard the
`litlogger` branch has.

---

## 5. Lightning's `WandbLogger` cannot be satisfied by a `sys.modules["wandb"]` shim

**Symptom.** With a wandb-compatible tracker aliased in as
`sys.modules["wandb"] = <tracker>` — the drop-in method those trackers document —
litgpt dies at the first hyperparameter log:

```
ModuleNotFoundError: No module named 'wandb.sdk'
```

**Root cause.** `lightning/pytorch/loggers/wandb.py`, inside the `experiment`
property, performs runtime **submodule** imports:

```python
import wandb
from wandb.sdk.lib import RunDisabled
from wandb.wandb_run import Run
```

A module-object alias satisfies `import wandb` but not `wandb.sdk.lib` or
`wandb.wandb_run`, which are resolved through the aliased package's `__path__`.
`litgpt/pretrain.py:155` calls `fabric.logger.log_hyperparams(hparams)` for the
`wandb` logger, so it hits this on the first use, before training starts.
Gating on `importlib.metadata` compounds it: `_WANDB_AVAILABLE =
RequirementCache("wandb>=0.12.10")` reads *distribution metadata*, so a shim
also has to be accompanied by a real `pip install wandb` to get that far.

**Fix / workaround.** None available. Used `--logger_name csv`.

**Upstream-worthy?** Yes, but against Lightning, not litgpt. The two symbols are
used only for an `isinstance` check guarding `define_metric`; `getattr(exp,
"define_metric", None)` is already checked on the same line, so the imports are
removable. Worth noting for anyone assuming the wandb ecosystem is
alias-compatible: for Lightning it is not.

---

## 6. `.gitignore` directory-ignores every output directory of the documented workflow

**Symptom.** Output directories do not survive a clean checkout, so a
provenance/CI system that expects declared output dirs to exist finds none of
them, and `!checkpoints/.gitkeep`-style re-includes silently do nothing.

**Root cause.** litgpt's `.gitignore` ignores the bare directory names `data`,
`checkpoints` and `out` (lines 17–19). Git cannot re-include a file whose parent
**directory** is excluded, so any later negation for a file inside them is
unreachable. Verified with `git check-ignore -v`:

```
checkpoints/.gitkeep: .gitignore:18:checkpoints   checkpoints/.gitkeep
out/final/.gitkeep:   .gitignore:19:out           out/final/.gitkeep
```

**Fix / workaround.** Re-include the directories before re-ignoring their
contents:

```gitignore
!checkpoints/
checkpoints/*
!checkpoints/.gitkeep
!out/
out/*
!out/final/
out/final/*
!out/final/.gitkeep
```

**Upstream-worthy?** Low. It is correct for litgpt's own use (nobody wants
checkpoints in git); it is only a hazard for downstream automation. Worth a note
rather than a PR.

---

## 7. `TextFiles` tokenization always spawns worker processes, and `--data.num_workers` does not control it

**Symptom.** The tokenization inside `litgpt pretrain --data TextFiles` runs in
child processes, whatever `--data.num_workers` says.

**Root cause.** Two separate worker counts share a confusingly similar name.
`--data.num_workers` reaches only the `StreamingDataLoader` in
`TextFiles.train_dataloader()`. `TextFiles.prepare_data()` computes its own:

```python
num_workers = os.cpu_count() - 1
use_workers = min(num_workers, len(train_files))
optimize(..., num_workers=use_workers, ...)
```

and litdata's `DataProcessor` treats a falsy value as "use the default"
(`num_workers or (os.cpu_count() or 1) * 4`), so even `0` cannot make it run
in-process. There is no flag, anywhere, that makes litgpt tokenize in a single
process.

**Fix / workaround.** Moved the tokenization into its own step
(`reproduction/prepare_data.py`), which calls `TextFiles.prepare_data()` with
the same parameters `litgpt pretrain` would. `prepare_data()` is a no-op once
its output directories exist, so the training step then runs single-process.

**Upstream-worthy?** Moderate. `TextFiles` should either honour
`--data.num_workers` for the optimize call or expose a separate
`--data.prepare_num_workers`; silently ignoring a user-supplied worker count is
surprising.

---

## Non-issues worth recording

- **`torch.compile(model)` is unconditional** in `litgpt/pretrain.py` (~line 205)
  with no flag to disable it. It costs about a minute on every run, including
  the 8-step debug runs `config_hub/pretrain/debug.yaml` exists to support. Not
  a defect, but a fixed tax on short runs.
- **jsonargparse deprecation noise.** Every invocation prints
  `JsonargparseDeprecationWarning` for `set_docstring_parse_options` and
  `set_config_read_mode` (deprecated in 4.39, removed in 5.0). litgpt's
  `jsonargparse[signatures]>=4.37,<=4.41` pin contains it for now, but the CLI
  is noisy and the 5.0 bump will break `litgpt/__main__.py:68-69`.
- **`TextFiles` needs at least two `.txt` files** when `val_data_path` is unset,
  and the assertion prints the file list rather than explaining the rule.
  Supplying an explicit `--data.val_data_path` avoids it.
- **Determinism was excellent.** At `--seed 42` the loss trajectory was
  bit-identical across three independent CPU environments. The only variation
  came from precision (fp16 on a T4 vs fp32 on CPU), which is expected.
