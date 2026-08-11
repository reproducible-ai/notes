# NeRF (nerf-pytorch) — lego scene, 2,000 of 200,000 iterations

The campaign had no 3D row. Everything through 011 is a classifier, a language
model, a diffusion sampler or a policy — architectures that consume a batch and
emit a label, a token or an action. NeRF is none of those. It has no dataset in
the usual sense: the "training set" is 100 photographs of a plastic digger and
the camera poses they were taken from, and the model being fitted is not a
classifier over those images but a *scene* — a small MLP that maps a 3D point and
a viewing direction to a colour and a density, optimised until integrating it
along camera rays reproduces the photographs. One model, one scene, no
generalisation.

`yenchenlin/nerf-pytorch` is the PyTorch port of the original NeRF release, MIT,
last touched in 2022. It is 5 Python files and 16 config files. That smallness is
the interesting part: with so little code there is nowhere for a hidden
dependency to hide, and yet the two most consequential facts about rebuilding it
are both invisible in the recorded package list.

## What ran

Three traced steps on a single T4, 11m16s of traced work inside a 12m44s job:

1. **`fetch_data`** (38.9 s) — upstream's own `download_example_data.sh` URL,
   fetched as a sha256-pinned step. The 370 MB archive holds exactly the two
   scenes the README's quick start uses: `nerf_synthetic/lego` and
   `nerf_llff_data/fern`. Making the fetch its own step is what turns the dataset
   into a provenance *edge* — the train step's reads of
   `data/nerf_synthetic/lego/**` resolve to files this step wrote, rather than
   appearing as inputs from nowhere. 874 outputs, all distinct.
2. **`train`** (615.0 s) — upstream's `configs/lego.txt` verbatim: coarse and
   fine 8-layer 256-wide MLPs, 64 coarse + 128 fine samples per ray, 1,024 rays
   per step, 400×400 (`half_res`), 500 iterations of centre-cropping first.
   Stopped at 2,000 iterations, running at 3.35 it/s. PSNR climbs 9.77 → 21.21.
3. **`render_novel_views`** (21.9 s) — upstream's own entry point and upstream's
   own flags, no wrapper: `--render_only --render_test --render_factor 8` reloads
   the checkpoint, renders the 25 held-out test poses and writes them plus an mp4.

The artefact is `002000.tar`, 14,352,633 bytes, sha256
`94fae5fb916f536037bf94658904e406801e067d326f4780189b0d1f2637d649`.
PSNR, computed every 100 iterations and printed by `tqdm.write`, is the only
metric this repository produces.

## The 25 novel views are 3 distinct images

This is the most honest thing this row has to say about truncation, and it is not
visible from any summary of the run.

At 1% of upstream's schedule and `--render_factor 8` (50×50 instead of 400×400),
the radiance field has not yet resolved enough view-dependent structure to make
the test poses differ. The step writes twenty-five PNGs; they hold **three
distinct images** between them. Twenty-two of the twenty-five files are
byte-identical to one of the other three. In an earlier run of this same recipe
that trained less well, all twenty-five were byte-identical to each other.

So the render step is a genuine end-to-end exercise of the reload → render →
video-encode path, and it is *not* a picture of a digger. Anyone reading "renders
25 novel views" and expecting 25 different views should raise `--render_factor`
to 0 and the iteration count with it. Both are one number on the command line.

## The finding: two declared dependencies, one pip closure

`requirements.txt` lists `imageio-ffmpeg` and `opencv-python`. Both are Python
distributions. Both appear in a pip freeze. A reader of that freeze would
reasonably conclude the environment is fully described by it. For one of them
that is true and for the other it is not.

**`imageio-ffmpeg` is pip-closed.** The wheel ships a statically linked
`ffmpeg-linux-x86_64-v7.0.2` binary inside `site-packages`. Installing the wheel
installs FFmpeg. The mp4 the render step writes needs nothing else.

**`opencv-python` is not.** It vendors ~30 shared objects into
`opencv_python.libs/`, but `cv2`'s extension module still resolves unbundled
`NEEDED` entries against system paths. Traced on the run host, `cv2.abi3.so`
loads `libGL.so.1`, `libGLX.so.0`, `libGLdispatch.so.0`, `libglib-2.0.so.0`,
`libgthread-2.0.so.0`, `libX11.so.6`, `libXext.so.6`, `libxcb.so.1`,
`libXau.so.6`, `libXdmcp.so.6`, `libbsd.so.0` and `libmd.so.0` from
`/lib/x86_64-linux-gnu`. Those come from OS packages, which **no pip freeze can
express**. Because `run_nerf.py` imports `load_blender.py` at module scope and
`load_blender.py` imports `cv2` at module scope, a missing one lands at *import
of the training script*, before a single argument is parsed.

The record does carry an OS-package list, and it is better than nothing: it names
`libglib2.0-0`, `libx11-6`, `libxcb1`, `libxext6`, `libxau6`, `libxdmcp6`,
`libbsd0`, `libmd0`, `libstdc++6` and three more. It does **not** name the OpenGL
trio — `libgl1`, `libglx0`, `libglvnd0` — even though `libGL.so.1`,
`libGLX.so.0` and `libGLdispatch.so.0` are demonstrably loaded. Every other
system library `cv2` pulls is on the list; exactly the GL ones are absent. **If
you rebuild this row on a bare image, install those three by hand.** On the AMI
this ran on they were already present, so nothing had to be installed outside the
recorded environment, and the gap stayed invisible until it was looked for.

This row keeps `opencv-python` rather than switching to the drop-in
`opencv-python-headless`, which has no GL dependency. Swapping it would make the
row rebuild more easily by no longer reproducing what upstream declares.

## The truncation, and why it needed a wrapper

`run_nerf.py:701` reads `N_iters = 200000 + 1`. It is a local variable inside
`train()`, and `config_parser()` exposes no flag for it. Every other knob this row
touches is an upstream argument on the command line; the training length is the
one thing that cannot be.

`repro/train_truncated.py` leaves `run_nerf.py` byte-identical and caps the
iterator instead: `run_nerf.py` loops `for i in trange(start, N_iters)`, `trange`
is a module-level name, and rebinding it to a version that lowers its stop value
changes how many times upstream's loop body runs and nothing else.
`--train-iters 2000` sits inside the recorded argv, so the lineage states the
truncation on its face. `repro/assert_upstream_unmodified.py` proves the claim by
git blob hash on every run — 28 of 29 upstream files byte-identical, the single
declared exemption being `.gitignore`, whose full diff it prints.

One upstream flag *is* passed that the config does not set: `--i_weights 2000`.
Its default is 10,000 — larger than this entire run — so without it the job would
have finished having written no checkpoint at all. That is a small, real trap for
anyone shortening this repository.

## Other divergences from what upstream declares

`torch==1.11.0` (March 2022) is **not installed**: it publishes no wheel for this
image's Python and no build for a modern CUDA runtime. The image's torch (2.7.0,
CUDA 12.6) is used and recorded, so a rebuild installs the version this run
actually ran on. `torchvision>=0.9.1` is not installed either — `grep -r
torchvision` finds only the requirements line. `tensorboard>=2.0` *is* declared
and is never imported: the one `SummaryWriter` line is commented out
(`run_nerf.py:708`) and every `tf.contrib.summary` call sits inside a
triple-quoted block.

That last one is why this row has no experiment link. There is no wandb, mlflow,
comet or neptune anywhere in the tree, and the only tracker upstream names is dead
code. There was no flag to switch on; adding `wandb.init()` would have bought a
dashboard at the cost of the one property that makes the row worth reading.

A related curiosity does reach the record. `run_nerf.py:12` does `import
matplotlib.pyplot as plt`, and `plt` is never referenced anywhere in the
repository — but the import executes, so matplotlib and its tail are genuinely
loaded and genuinely belong in the recorded environment. The two model steps
differ by exactly one package for the same reason: `imageio-ffmpeg` is in the
render step's 34 pins and not in the train step's 33, because only the render
step writes an mp4. A pin list records what was loaded, not what was needed.

## If you clone this repository

It cannot run on CPU. `run_nerf.py:876` sets the global default tensor type to
`torch.cuda.FloatTensor` unconditionally, and it has to: `raw2outputs()` and
`render_rays()` build bare `torch.Tensor(...)` and `torch.linspace(...)` values
with no device argument and concatenate them with GPU tensors. There is no
`--device` flag and no fallback. The bare-clone check for this row therefore ends
at that line — which is the correct result, because it proves the import closure
is complete and the only thing missing was a GPU.

Relatedly, `run_nerf.py:686` calls `torch.load(ckpt_path)` with no
`map_location`, so a checkpoint trained on a GPU cannot be reloaded anywhere
without one. Moot for a repository that needs a GPU regardless, but it is there.

## Status

Tier 1: the record is green on the AI-BOM (100/100), on anonymous URL resolution,
and on freeze portability, with the workload's import closure fully covered
(Tier-A misses: zero across 34 pins). **No cold rebuild has certified this row** —
that is a separate exercise by a different operator, and until it happens the
certification result stays `null` rather than being inferred from a run that
exited 0.
