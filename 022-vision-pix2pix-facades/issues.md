# Issues — row 022, pix2pix / CMP Facades

Ranked. **P0** = following the published materials literally fails. **P1** = it runs, but a
published claim cannot be verified. **P2** = it works; it costs time or clarity.

There are **no P0s**. Upstream's published command ran unmodified against upstream's published
dataset and produced a checkpoint. That is the headline finding for this repo.

---

## P1 — The Facades dataset is fetched over plain HTTP with no published checksum

`datasets/download_pix2pix_dataset.sh`:

```sh
URL=http://efrosgans.eecs.berkeley.edu/pix2pix/datasets/$FILE.tar.gz
```

Three problems, in increasing order of consequence:

1. **No integrity reference exists anywhere in the repository.** Neither the script,
   `docs/datasets.md`, nor the README publishes a hash for any dataset archive. A reproducer cannot
   confirm they received the same 400 training images the authors trained on. For a project whose
   entire claim is about paired image-to-image translation, the pairing *is* the experiment.
2. **The transfer is unencrypted.** Plain HTTP over an open channel, executed by a shell script that
   then untars the result.
3. **Single point of failure.** One third-party academic host, no mirror. When
   `efrosgans.eecs.berkeley.edu` eventually goes away, every pix2pix dataset recipe in this
   repository stops working, and there is no documented alternative.

As fetched on 2026-08-14: `facades.tar.gz`, 30,168,306 bytes, yielding 400 train / 106 test /
100 val images. Recorded here because it is the only integrity reference that now exists.

**Fix:** publish a sha256 per archive and verify it in the script; serve over HTTPS.
**Upstream action:** warranted.

---

## P2 — A run shorter than five epochs writes no checkpoint and still reports success

`train.py` has exactly two save paths:

```python
if total_iters % opt.save_latest_freq == 0:     # save_latest_freq default 5000
    ...
if epoch % opt.save_epoch_freq == 0:            # save_epoch_freq default 5
    model.save_networks('latest'); model.save_networks(epoch)
```

With the published defaults, a 1–4 epoch run reaches neither. `save_latest_freq` is 5000
iterations, which 4 epochs of Facades (1,600 iterations) does not reach; `save_epoch_freq` is 5,
which `epoch % 5` never satisfies. The run prints `End of epoch`, exits 0, and leaves
`checkpoints/<name>/` containing only `loss_log.txt` and `train_opt.txt`.

A short trial run is the first thing most people do with an unfamiliar trainer, and this one
succeeds while producing nothing. This row had to set `--save_epoch_freq 1` to have an artifact at
all.

**Fix:** always write a final checkpoint when the last epoch completes, independent of
`save_epoch_freq`.
**Upstream action:** warranted.

---

## P2 — `util/visualizer.py` calls a private wandb API, so `--use_wandb` requires the real wandb

`util/visualizer.py:69-70`:

```python
self.wandb_run = wandb.init(project=self.wandb_project_name, name=opt.name, config=opt) if not wandb.run else wandb.run
self.wandb_run._label(repo="CycleGAN-and-pix2pix")
```

`_label` is private, undocumented wandb internals with no stability guarantee. Two consequences:

- The flag is fragile against wandb's own releases — a rename or removal breaks training, not just
  logging, because the call is unguarded on the hot path of `Visualizer.__init__`.
- It is unusable against any wandb-compatible substitute, which raises
  `AttributeError: '_Run' object has no attribute '_label'` and ends the run. Confirmed by replaying
  this exact call shape.

Compounding it, `util/visualizer.py:7` does a bare top-level `import wandb`, so wandb is a hard
import-time dependency of training even when `--use_wandb` is not passed. `environment.yml` does
list wandb, so this is declared rather than hidden — but a user who wants no telemetry dependency
at all has no path.

Also worth noting: `wandb.init(..., config=opt)` passes an `argparse.Namespace`, not a mapping.

**Fix:** drop the `_label` call or guard it with `hasattr`; move the import inside the `use_wandb`
branch.
**Upstream action:** warranted.

---

## P2 — No `requirements.txt`; the only manifest is a conda `environment.yml`

The repository root ships `environment.yml` (conda: python 3.11, pytorch 2.4.0, torchvision 0.19.0,
pytorch-cuda 12.1, numpy 1.24.3, scikit-image, plus a pip section for dominate/Pillow/wandb) and no
pip manifest.

Anyone building with pip, uv, or a container base image translates it by hand, and `pytorch-cuda`
has no pip equivalent at all. The translation is not hard here — this row's seven pins came
straight out of it — but it is unstated work every non-conda reproducer repeats, and the
`numpy=1.24.3` pin is only valid under the `python=3.11` that the same file pins. On CPython 3.12
numpy 1.24.3 publishes no wheel, so a reader who takes the numpy pin without the python pin gets a
source build that fails.

**Fix:** ship a `requirements.txt` alongside `environment.yml`.
**Upstream action:** warranted.

---

## P2 — `wget -N` combined with `-O` in the dataset download script

```sh
wget -N $URL -O $TAR_FILE
```

`-N` (timestamping) does nothing when combined with `-O`, and wget warns as much. The intended
skip-if-current behaviour never happens; the full 30 MB archive is re-downloaded on every
invocation.

**Fix:** drop `-N`, or drop `-O`.
**Upstream action:** warranted.

---

## P2 — Recorded dependency set omits two packages the workload loads

Not an upstream defect — a property of this row's own published record, noted so a certifier is not
surprised by it.

The `train` step recorded **25 pins** where **51 distributions** were installed. Two omissions are
packages the workload demonstrably loads:

- **`typing-extensions`** — torch 2.4.0 declares `typing-extensions>=4.8.0` as a hard runtime
  requirement and imports it during `import torch`.
- **`tqdm`**.

Both are transitive dependencies of packages that *are* recorded, so the recorded set remains
jointly solvable and a cold rebuild will very likely succeed by letting the resolver supply them.
That is precisely why it is worth stating: **a green rebuild here would demonstrate that the
recorded set resolves, not that it is complete.**

Two absences that are *correct* and should not be filed as the same thing:

- `scikit-image` — imported only by `models/colorization_model.py`, which this recipe never loads.
- the 12 `nvidia-*` CUDA libraries — torch loads them via `dlopen`, not Python import; a rebuild
  resolves them as torch's declared dependencies.

**Fix:** none available to the operator.
**Upstream action:** none.
