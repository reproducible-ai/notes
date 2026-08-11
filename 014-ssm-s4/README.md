# S4 — structured state-space sequence model, permuted sequential MNIST

Every sequence-model row in this campaign so far has been a transformer. S4 is not
one. It replaces attention with a *linear state-space* recurrence — a learned
continuous-time system `x' = Ax + Bu`, `y = Cx + Du`, discretised and evaluated as a
long convolution via FFT — so a 784-step sequence is processed in one `O(L log L)`
pass rather than an `O(L²)` attention matrix. This row trains upstream's own
`train.py` on **permuted sequential MNIST**: each 28×28 digit is flattened to a
784-step scalar sequence and the pixel order is shuffled by a fixed permutation, which
destroys every local image cue and leaves only long-range dependency. That is the
task S4 was built to win.

**One epoch reaches 94.1% validation accuracy** — 1,080 optimizer steps on a task
built to have no local structure at all. That is the interesting result here, and it
is also why the row is explicit about being truncated: upstream's configured run is
200 epochs, and this is one two-hundredth of it. The repo ships no permuted-MNIST
reference number of its own (`models/s4/experiments.md` documents LRA and sequential
CIFAR only), so no convergence target is quoted here.

## What was actually run

```
python -m train pipeline=mnist dataset.permute=True model=s4 model.n_layers=3 \
  model.d_model=128 model.norm=batch model.prenorm=True wandb=null \
  trainer.max_epochs=1 loader.num_workers=0 hydra.run.dir=./outputs/run
```

The first seven tokens are copied verbatim from upstream's README ("Configs and
Hyperparameters" → *An example experiment is …*). The last three are ours and are all
Hydra overrides, not edits: `trainer.max_epochs=1` is the truncation,
`loader.num_workers=0` keeps the workload in one process so the provenance tracer
records the real dependency set rather than a worker's, and `hydra.run.dir` pins the
output directory, which Hydra otherwise timestamps (`./outputs/2026-08-11/21-13-34-…`)
— a path no reproduction could ever predict.

Model: 3 S4 layers, `d_model=128`, `d_state=64`, batch-norm, pre-norm, **127,562
parameters**. Data: 54,000 train / 6,000 val / 10,000 test, batch 50, 1,080 optimizer
steps, AdamW at 1e-3 with a `ReduceLROnPlateau` schedule. Result after one epoch:

| metric | value |
|---|---|
| val/accuracy | 0.94083 |
| val/loss | 0.20117 |
| test/accuracy | 0.94230 |
| test/loss | 0.18875 |
| train/accuracy (epoch mean) | 0.87837 |
| train/loss (epoch mean) | 0.39262 |

**The run is bit-deterministic.** It was captured twice, on two different EC2
instances, hours apart, and both produced a checkpoint with sha256
`00a2841866…4323a1` and identical metrics to five decimal places. Upstream sets
`train.seed: 0` and the S4 kernel initialisation for this config is deterministic;
nothing here needed a `--deterministic` flag to get there.

## Zero lines of upstream code changed

The fork adds `.treqs/workflows/s4-smnist.yaml`, three files under `repro/`, and three
`.gitkeep` files. It changes **no upstream Python at all** — not `train.py`, not
`src/`, not `configs/`. The only upstream file modified is `.gitignore`, where three
lines are deleted: upstream dir-ignores `outputs/` and `data`, and git cannot
re-include a tracked placeholder inside an ignored *directory*, so the output
directories would not have survived a clean checkout and their contents would have
dropped out of lineage. They are replaced by the equivalent file-pattern form.

## What it takes to run a 2024 repo in 2026

Upstream's last push was July 2024 and its `requirements.txt` pins exactly one thing
(`pytorch-lightning==2.0.4`). On a current host nothing about that file works, and the
failures cascade from a single unavoidable import:

**`torchtext` pins the entire torch stack to 2.3.0.** `train.py` does
`from src.dataloaders import SequenceDataset`; `src/dataloaders/__init__.py` imports
`lra`; `src/dataloaders/lra.py` line 12 is `import torchtext`, at module level, with no
guard. It runs even though this row never touches an LRA dataset. torchtext was
archived, its final release is 0.18.0, and 0.18.0 ships `libtorchtext.so` linked
against libtorch 2.3. Against the AMI's torch 2.7.0 it dies with

```
OSError: .../torchtext/lib/libtorchtext.so: undefined symbol:
  _ZN5torch6detail10class_baseC2ERKSsS3_SsRKSt9type_infoS6_
```

so `torch`, `torchvision` and `torchaudio` all go back to the 2.3 line. That one
import is the single largest obstacle to running this repo today, and it is a
three-line fix upstream would have to make (guard the LRA import) — we did not make
it, because patching upstream would make this row a demo of our patch.

Three more, each a one-line pin:

- **numpy < 2.** torch 2.3.0 is built against numpy 1.x. But scipy ≥ 1.14 removed the
  `np.long` alias that numpy 1.26 still has, so `import scipy.signal` (reached through
  `torchmetrics`) explodes with `AttributeError: module 'numpy' has no attribute
  'long'`. numpy 1.26.4 + scipy 1.13.1 is the only pair that satisfies both.
- **rich < 14.** pytorch-lightning 2.0.4's `RichProgressBar.on_sanity_check_start`
  calls `Console.clear_live()` unconditionally; rich 14 replaced the single live
  display with a *stack*, so with no live display active the first sanity-check batch
  raises `IndexError: pop from empty list` — after the model is built, from inside a
  progress bar. rich 13.9.4 works.
- **setuptools < 81.** `lightning_fabric/__init__.py` calls
  `__import__("pkg_resources").declare_namespace(__name__)`; setuptools 81 removed
  `pkg_resources` entirely, so `import pytorch_lightning` fails with
  `ModuleNotFoundError: No module named 'pkg_resources'`.

None of this is discoverable from `requirements.txt`. All of it is written down, with
the symptom for each, in [`repro/requirements-lock.txt`](https://github.com/reproducible-ai/s4/blob/main/repro/requirements-lock.txt)
in the fork.

**No CUDA extension, no pykeops, and that is deliberate.** S4's Cauchy kernel has three
backends: a hand-written CUDA extension (`extensions/kernels`, needs compiling),
pykeops (needs `nvrtc` at runtime), and a naive PyTorch fallback. Installing either
fast path means compiling code *outside* the recorded environment into a cache
directory that no freeze describes. With neither installed, `src/models/sequence/
kernels/ssm.py` logs its own warning and falls back to `cauchy_naive`, which is what
this row records. It costs speed: 9.99 it/s, ~110 s per epoch on a T4. The record is
complete in exchange.

## Data

MNIST is auto-downloaded by `torchvision` into `./data/mnist` on first use — 11 MB, a
few seconds, and it happens *inside* the traced step, so the four raw IDX files are
outputs of the run rather than unsourced inputs a rebuild would have to conjure.
Worth knowing: torchvision still tries `http://yann.lecun.com/exdb/mnist/` first, that
host no longer serves the files, and it silently falls through to the
`ossci-datasets.s3.amazonaws.com/mnist/` mirror. The download works; it just logs a
dead URL first.

## Experiment logging: none, and it cannot be added

`experimentUrl` is `null`. This is a finding, not an omission, and it is more specific
than "Lightning repos can't log":

Upstream **does** ship WandB support — `configs/config.yaml` has a whole `wandb:`
block, and `train.py` defines a `CustomWandbLogger` subclass. So the flag exists and
the rule is normally "if the framework has the code, switch it on." It was tested
against the campaign's wandb→trackio bridge on CPU, for $0, before any GPU was booked.
It fails before step 0:

`pytorch_lightning/loggers/wandb.py:35-41` (PL 2.0.4) reads

```python
try:
    import wandb
    from wandb.sdk.lib import RunDisabled
    from wandb.wandb_run import Run
except ModuleNotFoundError:
    wandb, Run, RunDisabled = None, None, None
```

The bridge substitutes the top-level `wandb` module. It does not provide
`wandb.sdk.lib` or `wandb.wandb_run`, so the `except` branch fires, `wandb` is set to
`None` — discarding the working substitute — and `WandbLogger.__init__` raises at
`wandb.py:305`: *"You want to use `wandb` logger which is not installed yet."*
Upstream additionally calls `wandb.Settings(start_method="fork")` (`train.py:635`) and
`wandb._attach` (`train.py:100`), neither of which any drop-in replacement implements.

Making it work would mean editing `train.py`. That trade — a link on this page in
exchange for the "zero upstream lines changed" property that makes the page worth
reading — is not worth taking. The row runs with upstream's own documented
`wandb=null` instead.

Metrics are still *computed and recorded*: pytorch-lightning's CSVLogger writes
`outputs/run/lightning_logs/version_0/metrics.csv` (per-10-step loss, gradient norms,
`timer/step`, `timer/epoch`, and the final val/test figures), and that file is captured
in the lineage graph as a step output.

## Cost, and what a full run would cost

The published run is **1 of 200 epochs**. 200 is not a guess — it is
`max_epochs: 200` in `configs/trainer/default.yaml`, the trainer config this pipeline
inherits.

Measured, during the run, not reconstructed afterwards:

| phase | duration | scales with epochs? |
|---|---|---|
| provisioning (cold instance) | 2m45s | no |
| `setup` — roar + the pinned torch 2.3 stack + diagnostics | 3m34s | no |
| **`train` (traced)** | **2m17s** | partly |
|  └ fixed part of it: imports, MNIST download, dataset build, S4 kernel init | 18.0s | no |
|  └ the epoch itself (upstream's own `timer/epoch`) | 117.7s | **yes** |
| `label` + `publish` | 4s | no |

So the variable cost is 117.7 s per epoch and everything else — about 6m40s — is paid
once. 200 epochs is `200 × 117.7 s = 6 h 32 m` of training on top of that. At the
g4dn.xlarge on-demand rate of $0.526/h in us-east-2 that is **≈ $3.50**, of which
$3.44 is training and $0.06 is fixed. Scaling the row's headline cost by 200 instead
would have given $16 — a 4.5× error, entirely from treating a fixed cost as variable.

## What a rebuilder should know before starting

- **The freeze is a superset of the import closure.** 104 pins are recorded for a
  workload whose import graph is roughly 25 packages. Nothing needed is missing —
  `torch`, `torchtext`, `torchvision`, `torchaudio`, `pytorch-lightning`, `hydra-core`,
  `omegaconf`, `einops`, `scikit-learn`, `scipy`, `pandas`, `datasets`, `wandb`,
  `numpy`, `rich`, `setuptools`, `pillow` and `tqdm` are all present and pinned — but
  the set also carries packages this row never imports. They install cleanly; they just
  make the rebuild slower than it needs to be.
- **No local-version pins.** Nothing in the freeze carries a `+cu121`-style suffix, so
  every pin resolves on PyPI. (`torch.__version__` *prints* `2.3.0+cu121`; the
  distribution version is a plain `2.3.0`.)
- **Native libraries are largely invisible to the record.** Of 403 shared objects the
  process maps, only **7** are owned by a dpkg package and therefore recorded
  (`libssl3`, `libffi8`, `libfribidi0`, `libsqlite3-0`, `libstdc++6`, `libuuid1`, plus
  `libcrypto` from `libssl3`). The other 396 are not. Most of those are fine — they
  belong to pip wheels that *are* pinned (`nvidia-cublas-cu12`, `libtorch*`, numpy's
  bundled OpenBLAS). Three are not covered by anything: `libcuda.so.580.126.09`,
  `libnvidia-ml.so.580.126.09` and `libnvidia-ptxjitcompiler.so.580.126.09`. **The GPU
  driver version this ran against appears nowhere in the record**, and it is the one
  host property that decides whether the recorded cu121 build of torch runs at all.
  For the record: NVIDIA driver 580.126.09, Tesla T4, on `ami-0f07f1a0b382b48f7`.
- **`roar`'s own reproducibility self-check is 6/7**, flagging "all artifact paths in
  tracked directories" even after `outputs/run/checkpoints/val/.gitkeep` was committed
  and unignored level by level. The remaining unlisted directory is the Hydra/Lightning
  output tree (`outputs/run/.hydra`, `outputs/run/lightning_logs/version_0`), created
  at runtime. Both are created by the code before anything is written into them, so
  this is conservative rather than broken — but a rebuilder should expect the warning.

## Status

This is a **Tier 1 reproducible record**: the four record gates pass
(clean-DAG 13/13, AI-BOM 100/100, all URLs public anonymously, freeze PORTABLE), the
lineage is attributed to Reproducible AI, and the checkpoint is published and
downloadable without a login. **It is not a certified reproduction.** No cold host has
yet rebuilt this row from the published lineage; that is a separate exercise by a
different operator, and until it happens `certification.result` here is `null` rather
than `"PASS"`.
