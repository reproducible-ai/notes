# 016 — Kronos: a foundation model for financial K-lines

**Upstream** [`shiyu-coder/Kronos`](https://github.com/shiyu-coder/Kronos) · MIT ·
default branch **`master`** ·
**fork** [`reproducible-ai/Kronos`](https://github.com/reproducible-ai/Kronos) @ `a6ba0bd` ·
**artifact** [`reproducible-ai/kronos`](https://huggingface.co/reproducible-ai/kronos) ·
**DAG** [`847b359a…`](https://glaas.ai/dag/847b359a9f1a0ae3a31a621f9901f57e5387f37610adabc9e7bd24f4ecdae97d)

This is the campaign's first time-series row and its first financial one. Kronos
is a decoder-only foundation model for K-line (candlestick) sequences,
pre-trained across 45 exchanges, released at AAAI 2026. Its distinctive claim is
a two-stage design: a learned tokenizer quantises continuous OHLCV bars into
hierarchical discrete tokens, and an autoregressive transformer is trained on
those tokens. That means "fine-tuning Kronos" is genuinely two trainings, and
the second consumes the first's output — which makes it an unusually good shape
for a lineage record.

## What was run

Upstream publishes two fine-tuning pipelines. `finetune/` trains from a Qlib
data directory that is not published, so an outsider cannot run it at all.
`finetune_csv/` takes a CSV of your own — and ships one, a 93,912-row 5-minute
K-line series for Alibaba HK 09988 covering 2019-11-26 to 2025-09-17, right
there in the repository. That is the pipeline this row reproduces, and the
shipped CSV is the data, so **nothing about the dataset has to be taken on
trust**: it is 5.6 MB of MIT-licensed text in the tree being cloned.

Three recorded steps:

| step | command | measured |
|---|---|---|
| `fetch_pretrained` | `python repro/fetch_pretrained.py` | **4.5 s** |
| `finetune_tokenizer` | `env -C finetune_csv python train_sequential.py --config configs/config_repro_kronos-small_1epoch.yaml --skip-basemodel` | **984.2 s** |
| `finetune_predictor` | `env -C finetune_csv python train_sequential.py --config configs/config_repro_kronos-small_1epoch.yaml --skip-tokenizer` | **2918.0 s** |

Both training commands are upstream's own, from `finetune_csv/README.md` §3
"Method 1 (Recommended)", `--skip-basemodel` / `--skip-tokenizer` included. The
tokenizer step adapts `Kronos-Tokenizer-base` (3,958,042 params) and writes a new
tokenizer; the predictor step loads **that** tokenizer — not the pre-trained one
— and adapts `Kronos-small` (24,741,376 params) on the tokens it emits. The
dependency is real and visible in the DAG: `finetune_predictor` takes
`finetuned/…/tokenizer/best_model/model.safetensors` as an input.

Data: 83,960 training windows and 8,832 validation windows of 512 lookback + 48
predict, from upstream's own 0.9/0.1 config ratios, at upstream's `batch_size:
32` — 2,623 optimizer steps per epoch per stage.

Metrics, computed by upstream's code at the end of each epoch:

- tokenizer validation loss (MSE reconstruction) **0.0022**, epoch time 16m17s
- predictor training loss **1.9415**, validation loss **1.8362**, epoch time 2910.78 s

`model.safetensors` published at **98,980,656 bytes**, sha256
`108c4fef6a5c30e43491a104f593604c44b76a0535553fbf8a69f9fc3314862e`.

**Truncated: 1 epoch per stage, against upstream's 30 and 20.** Read from
upstream's own template, `configs/config_ali09988_candle-5min.yaml`, not guessed.
The full recipe is about **24.5 hours and $12.9** on the same T4 — see
`row.json` → `rebuild.fullRunEstimateBasis` for the arithmetic, which is built
from the two measured per-epoch numbers rather than from scaling the total.

## Zero upstream lines changed

The fork adds two files and edits none. The config is upstream's own template
with the `/xxxx/Kronos/...` placeholder paths made relative and the epoch counts
cut; `repro/fetch_pretrained.py` is a `snapshot_download` call pinned to the two
model revisions that **upstream's own regression test pins**
(`tests/test_kronos_regression.py`, `TOKENIZER_REVISION` and `MODEL_REVISION`),
so the weights fine-tuned here are the weights upstream tests against.

`Kronos-small` rather than the template's `Kronos-base` is the one substantive
choice. It is the checkpoint upstream's README quickstart and its regression test
both use, it shares the 512-token context of `Kronos-Tokenizer-base`, and at
102.3M params `Kronos-base` would have cost roughly four times as much per epoch
on a T4.

## Five upstream findings

Full detail in `issues.md`; the important one:

**Two of the three documented entry points do not run.** `finetune_csv/README.md`
documents "Method 2: Individual Component Training" as
`python finetune_tokenizer.py` then `python finetune_base_model.py`. Both die
before loading any data:

```
File "finetune_csv/finetune_tokenizer.py", line 296, in main
  os.makedirs(config.tokenizer_save_path, exist_ok=True)
UnboundLocalError: local variable 'os' referenced before assignment
```

`os` is imported at module level, but `main()` also does `import json, os` inside
an `else:` branch (`finetune_tokenizer.py:310`, `finetune_base_model.py:394` and
`:421`). A function-local binding anywhere makes the name local for the *whole*
function, so the earlier `os.makedirs()` resolves against an unassigned local.
The branch that would run that import is the `pre_trained_*: false` path, so the
crash fires on the default, documented path and no configuration avoids it.

This was found by the bare-clone check, on CPU, for $0, before any GPU was
booked. The row routes around it by using upstream's recommended
`train_sequential.py`, whose in-branch imports are `import json` only. The
one-word-per-site fix is in `patches/` and is deliberately **not** applied — the
value of this row is that it runs upstream's code, not our repair of it.

The others: `requirements.txt` omits PyYAML although `config_loader.py` imports
it; the README quickstart reads `./data/XSHG_5min_600977.csv`, which does not
exist in the repository; the working directory is load-bearing and undocumented
(`sys.path.append('../')` in every entry point, so the scripts import only from
inside `finetune_csv/`); and `use_comet` is dead config in the CSV pipeline —
read into the config dict, never used to construct a logger.

## Why there is no experiment link

**Upstream ships no wandb-compatible logging at all.** Verified, not assumed: a
grep for `wandb`, `mlflow`, `trackio`, `tensorboard`, `neptune` and `report_to`
across every file in the tree returns no hit outside our own workflow file. The
only integration Kronos has is Comet, and only in the `finetune/` (Qlib)
pipeline this row does not run. Adding logging would modify the workload and
forfeit the property that makes the row worth anything.

So `--wandb-to-trackio` and `TRACKIO_SPACE_ID` were **removed** from the run
stages rather than left in as harmless scaffolding. They are not harmless: with
no `wandb.init()` to intercept, the bridge forwards nothing, and its import
attempt alone has previously been enough to attribute `trackio` and
`gradio_client` into a recorded freeze.

## What a certifier should know

Tier 1 is green — clean-DAG 13/13, AI-BOM 100/100 (profile Advanced), all URLs
public anonymously, freeze PORTABLE — and `imports_vs_freeze_audit` reports
**Tier-A missing zero** on both training steps, with `fsspec` the only Tier-B
hint. All seven packages Kronos actually imports are in the freeze: `torch`,
`numpy`, `pandas`, `PyYAML`, `einops`, `huggingface-hub`, `safetensors`.

Two caveats, and neither is Kronos's fault.

**The recorded torch is another row's leftover.** The compute target reuses
on-demand instances warm between jobs. The host handed to this row still carried
a previous occupant's downgrade of the shared `/opt/pytorch` interpreter, so the
freeze records `torch==2.3.0` and `numpy==1.26.4` where this AMI family ships
2.7.0 and numpy 2.x. The set is plain, PyPI-resolvable and mutually consistent,
so it should rebuild — but it rebuilds against another row's environment, not
against the image.

Worth knowing precisely, because both obvious ways of checking for the
non-portable `+cuNNN` local-version trap are wrong on this image:

- `torch.__version__` read `2.3.0+cu121` — a **false positive**. That string is
  the build tag, and it is not what gets recorded.
- `pip list --format=freeze | grep '+'` returned **empty** — a **false
  negative**. `pip list` reports nothing at all in this environment, so the
  prescribed check passes silently whatever is installed.
- `importlib.metadata` is the only correct source: the distribution version is a
  plain `2.3.0`, and that is what roar records and what a rebuild resolves.

The setup stage now asserts this from `importlib.metadata`, repairs with the
plain PyPI build if a local version is ever found, and hard-fails before the
first traced step. One run was cancelled mid-training on the false positive
before the distinction was understood — that cost about 10 minutes of GPU and
was the right call on the information available.

**Eight recorded packages are the base image, not the workload.** `onnx`,
`onnxruntime`, `onnxscript`, `onnx-ir`, `ml_dtypes`, `protobuf`, `pyarrow` and
`google-auth` appear in the freeze; Kronos imports none of them. They are loaded
at interpreter start by the SageMaker-derived AMI — `onnxruntime` announces
itself in the training log with a GPU device discovery warning — and the rest of
the non-Kronos pins (`blake3`, `click`, `cryptography`, `pydantic`, `brotli`,
`zstandard`, `dill`, `cloudpickle`) are roar's own stack. They are recorded
because they were genuinely loaded, and all resolve from PyPI.

## The pre-flight that paid for itself

The bare-clone check ran the exact recorded commands from a fresh clone in a
33-package venv built from 7 direct packages, with `PYTHONPATH` unset, on CPU.
All three steps exit 0. It caught the `UnboundLocalError` above, and then a
second thing that would have produced a green record and an unrebuildable row.

The first draft of the recipe reached the `model` package with
`env PYTHONPATH=. python finetune_csv/train_sequential.py`. Replayed under roar
0.4.4rc6 itself — the whole recorded command, not a trimmed subset — that step
recorded **zero packages**. File inputs and outputs were traced correctly; the
freeze was simply empty. An A/B isolated it precisely:

| recorded command | pins |
|---|---|
| `python -c "import pandas,yaml,einops"` | 3 |
| `env python -c "import pandas,yaml,einops"` | 3 |
| `env PYTHONPATH=. python -c "import pandas,yaml,einops"` | **0** |
| `env PYTHONPATH=<repo> python -c "import pandas,yaml,einops"` | **0** |
| `env -C finetune_csv python -c "import pandas,yaml,einops"` | 3 |

Setting `PYTHONPATH` inside the recorded argv at all — relative or absolute —
wipes package attribution while leaving file tracing intact. The fix is better
than the workaround: `env -C finetune_csv` puts the working directory upstream
actually requires **inside** the recorded argv, so the recipe becomes literally
the command in upstream's README, and nothing depends on an unrecorded `cd`.

## Reproduce

```
roar reproduce 847b359a9f1a0ae3a31a621f9901f57e5387f37610adabc9e7bd24f4ecdae97d --lineage --run --no-puts
```

Captured on roar **0.4.4rc6**, installed from TestPyPI by version — no presigned
wheel, no per-target shared secret. The published linux x86_64 wheel digest
`c7115b748886259b6a089e547404376acf84c3b81b4cbc8dc5610490ebea7199` is asserted
in the setup stage before anything is installed. Tracer `preload`,
`ami-0f07f1a0b382b48f7`, 1× Tesla T4 (g4dn.xlarge), us-east-2.
