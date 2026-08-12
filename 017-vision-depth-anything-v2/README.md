# Depth Anything V2 — metric depth on Hypersim

**Verdict: reproduced and independently certified, heavily truncated.** Upstream's own metric-depth
trainer runs end to end from published materials with **zero lines of upstream Python
changed**, and it computes upstream's own depth metrics on held-out frames. Everything that
had to be solved before the first batch was an ecosystem gap — a dataset that cannot be
addressed by the manifests as shipped, two missing requirements, a NumPy-2 break, and a
distributed-only entry point.

This is the campaign's first monocular depth-estimation row.

## What ran

One pipeline, six stages, one GPU:

| stage | what it did | wall clock |
|---|---|---|
| `setup` | environment + capture tool | 15 s (46 s on a cold host) |
| `fetch_weights` | released ViT-S relative-depth weights, 99.2 MB | 4.9 s traced |
| `prepare_data` | 160 Hypersim files (19.6 MB) + both split lists | 40.3 s traced |
| `train` | upstream `metric_depth/train.py`, 1 epoch, batch 4, 518 px | 11.4 s traced |
| `label` + `publish` | artifact metadata, then 297 MB checkpoint upload | 1 s + 7 s |

`train.py` was run exactly as upstream wrote it: `--epochs 1 --encoder vits --bs 4
--lr 0.000005 --img-size 518 --min-depth 0.001 --max-depth 20 --dataset hypersim
--pretrained-from ../checkpoints/depth_anything_v2_vits.pth`, the same flags
`dist_train.sh` passes, with the epoch count and the split reduced.

Evaluation is upstream's `util/metric.py::eval_depth`, computed inside the same step on 16
held-out frames from a scene that appears only in upstream's validation list:

```
      d1,       d2,       d3,  abs_rel,   sq_rel,     rmse, rmse_log,    log10,    silog
   0.284,    0.548,    0.751,    0.650,    1.800,    2.203,    0.606,    0.211,    0.574
```

Those are the numbers a *one-epoch, 64-image* fine-tune produces. They are evidence that the
metric is computed, nothing more. Peak GPU memory was **5,245 MiB**, which means this
configuration would fit a 16 GB T4 comfortably; it was run on an L40S only because that was
the free target.

## The four obstacles

**1. The shipped Hypersim manifests are unusable outside the authors' filesystem.**
`train.py` reads `dataset/splits/hypersim/train.txt` and `val.txt`. Both are shipped — 59,543
and 7,386 lines — and every line is an absolute path of the form
`/mnt/bn/liheyang/DepthDatasets/HyperSim/all/ai_001_001/images/...`. There is no root-directory
argument and the paths are not relative, so *nobody* outside the lab can use them directly.
They are still valuable, because they define the split. This fork keeps them verbatim as
`upstream_train.txt` / `upstream_val.txt` and generates the real lists from them: take the
first 64 train and first 16 val entries, fetch exactly those frames, rewrite the paths. The
slice is therefore a strict subset of upstream's own split, and the train scene
(`ai_001_001`) and val scene (`ai_003_010`) stay disjoint exactly as upstream defined them.

**2. Getting the data is the expensive part, and it does not have to be.** Hypersim is
distributed by Apple as per-scene zip archives of about 2.2 GB each. The prepare step reads
the archives over HTTP range requests and pulls only the 160 members it needs — **19.6 MB
transferred instead of 4.4 GB**, in 40 seconds. Anyone truncating this row should do the
same; downloading whole scenes to use 64 frames is the single largest avoidable cost here.

**3. `requirements.txt` is missing two packages the trainer needs.**
`metric_depth/requirements.txt` lists `matplotlib`, `opencv-python`, `open3d`, `torch`,
`torchvision`. It does not list `h5py`, which `dataset/hypersim.py` imports to read the depth
files, or `tensorboard`, which `train.py` needs for `SummaryWriter`. Conversely `open3d` is
listed but only `depth_to_pointcloud.py` imports it. Following the README exactly gives you
`ModuleNotFoundError` twice before you reach a batch.

**4. NumPy 2 breaks the trainer at line 46.** `train.py` calls
`warnings.simplefilter('ignore', np.RankWarning)`. `np.RankWarning` was removed in NumPy 2.0,
so on any current default environment the run dies with
`AttributeError: module 'numpy' has no attribute 'RankWarning'` before anything else happens.
Rather than patch upstream, this record constrains the environment to `numpy<2` — which is
what the recorded package set then pins. The one-line upstream fix would be to delete the
line or use `np.exceptions.RankWarning`.

**And one shape, not a bug:** the entry point is distributed-only. `train.py` calls
`setup_distributed()` unconditionally, which reads `RANK` and `WORLD_SIZE` from the
environment, and reads `LOCAL_RANK` itself; `dist_train.sh` only ever launches it under
`torch.distributed.launch` with 8 GPUs. A single-GPU run is perfectly possible — but you have
to supply `RANK=0 WORLD_SIZE=1 LOCAL_RANK=0 MASTER_ADDR=127.0.0.1 MASTER_PORT=29500`
yourself. No flag does it, and nothing in the README mentions it. The recorded command carries
all five variables inside the command line, so the record reproduces them.

## What is truncated, and what a full run would cost

Upstream's own `dist_train.sh` is **120 epochs, ViT-L, batch 4 per GPU, 8 GPUs, all 59,543
training frames** (the argparse default of 40 epochs is overridden by the shipped script).
This record is 1 epoch, ViT-S, 64 frames, 1 GPU. The published checkpoint is **not converged**
and is not a substitute for the authors' released weights.

Scaling only what was measured: the epoch processed 80 frames in 4.63 s, of which ~2.0 s was
one-off cuDNN autotuning, giving ~0.0325 s per frame. One full epoch over 66,929 train+val
frames is then ~36 minutes, and 120 epochs ~72.5 GPU-hours — **about $135** on the same
instance at $1.861/hr. That figure covers the ViT-S single-GPU configuration actually
measured, not upstream's larger ViT-L 8-GPU job, and it excludes acquiring the full dataset:
the full split spans 411 scene archives, roughly 900 GB, which nothing measured here supports
pricing.

One number worth carrying forward for anyone rebuilding: the *same* training step took
**204 s on a freshly booted host and 13 s on the same host once warm**. Roughly 110 s of any
cold rebuild is first-CUDA-context and kernel warm-up, not training.

## Certified — tier 2, cold rebuild: PASS

All four tier-1 gates pass and the AI-BOM scores 100/100, but nothing in tier 1 executes
anything, so a separate agent — one that did not capture this row and did not see this
working directory — rebuilt it on a host that had never seen it. Exit **0**,
**`Steps run: 3/3`**, recorded package set reproduced **41/41 exact** on the training step,
all three outputs regenerated at the recorded byte sizes, in **2 m 29 s** on a **T4** for
about **$0.15**. Full evidence, with hashes: [`CERT-TIER2.md`](CERT-TIER2.md).

Two things this page told a certifier to expect. The `numpy<2` constraint **did** self-heal
from the record — `numpy==1.26.4` installed straight from the recorded manifest and the
trainer ran past line 46 untouched. The **~110 s cold CUDA warm-up did not reproduce**: the
same step measured 51.2 s cold and 40.0 s warm on the certification host, a penalty of ~11 s
rather than ~110 s, so the 204 s figure behind that estimate looks specific to the capture
host rather than a portable property of a cold GPU. The 5,245 MiB memory figure is also
narrower than it reads — `nvidia-smi` showed **9,831 MiB** actually resident during a step.
The row does fit a T4, and the certification proved it by running on one; but size hardware
from ~10 GB, not 5.2 GB.

## No experiment link

There is nothing to switch on. The repository contains no `wandb`, `mlflow`, `trackio` or
`comet_ml` integration anywhere — `train.py` writes TensorBoard scalars and nothing else, and
TensorBoard is not bridged. Adding a logging call would have made this a demonstration of our
patch rather than a reproduction of their work, so `experimentUrl` is null and this paragraph
is the reason.
