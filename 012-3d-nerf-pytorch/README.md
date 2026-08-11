# NeRF (nerf-pytorch) — lego scene, 2,000 of 200,000 iterations

The campaign had no 3D row. Everything through 011 is a classifier, a language
model, a diffusion sampler or a policy — architectures that consume a batch and
emit a label, a token or an action. NeRF is none of those. It has no dataset in
the usual sense: the "training set" is 100 photographs of a plastic digger and
the camera poses they were taken from, and the model being fitted is not a
classifier over those images but a *scene* — a small MLP that maps a 3D point and
a viewing direction to a colour and a density, optimised until integrating it
along camera rays reproduces the photographs. One model, one scene, no
generalisation. Reproducing it stresses different parts of the record than
anything before it.

`yenchenlin/nerf-pytorch` is the PyTorch port of the original NeRF release, MIT,
last touched in 2022. It is 5 Python files and 16 config files. That smallness is
the interesting part: with so little code there is nowhere for a hidden
dependency to hide, and yet the two most consequential facts about rebuilding it
are both invisible in the recorded package list.

## What ran

Three traced steps, one `treqs run`, on a single T4:

1. **`fetch_data`** — upstream's own `download_example_data.sh` URL, fetched as a
   sha256-pinned step. The 370 MB archive holds exactly the two scenes the
   README's quick start uses: `nerf_synthetic/lego` and `nerf_llff_data/fern`.
   Making the fetch its own step is what turns the dataset into a provenance
   *edge* — the train step's reads of `data/nerf_synthetic/lego/**` resolve to
   files this step wrote, rather than appearing as inputs from nowhere.
2. **`train`** — upstream's `configs/lego.txt` verbatim: coarse and fine 8-layer
   256-wide MLPs, 64 coarse + 128 fine samples per ray, 1,024 rays per step,
   400×400 (`half_res`), 500 iterations of centre-cropping first. Stopped at
   2,000 iterations.
3. **`render_novel_views`** — upstream's own entry point and upstream's own
   flags, no wrapper: `--render_only --render_test --render_factor 8` reloads the
   checkpoint, renders the 25 held-out test poses and writes them plus an mp4.

PSNR is computed every 100 iterations and printed. It is the only metric this
repository produces.

## The truncation, and why it needed a wrapper

`run_nerf.py:701` reads:

```python
N_iters = 200000 + 1
```

It is a local variable inside `train()`, and `config_parser()` exposes no flag
for it. Every other knob this row touches — `--config`, `--i_weights`,
`--render_factor` — is an upstream argument on the command line. The training
length is the one thing that cannot be. Upstream's README puts a full `lego` run
at about four hours on a 2080 Ti at 100k iterations; the file's own default is
200k.

So truncating meant choosing between editing `run_nerf.py` to add an `--N_iters`
argument, and leaving it untouched. `repro/train_truncated.py` does the latter:
`run_nerf.py` loops `for i in trange(start, N_iters)`, `trange` is a module-level
name, and rebinding it to a version that lowers its stop value changes how many
times upstream's loop body runs and nothing else. The model, sampler, loss,
optimiser, learning-rate schedule, checkpoint writer and logging are all
upstream's, seeing exactly the arguments upstream's own parser produced.
`--train-iters 2000` sits inside the recorded argv, so the lineage states the
truncation on its face and a reader who wants the full run raises one number.

`repro/assert_upstream_unmodified.py` proves the claim rather than asserting it:
it compares every path in the upstream commit against HEAD by git blob hash and
fails on any difference. It runs in the setup stage of every capture. 28 of 29
upstream files are byte-identical; the single declared exemption is `.gitignore`,
which gains the `!data/.gitkeep` / `!logs/.gitkeep` negations that let the output
directories survive a clean checkout, and whose full diff the script prints.

One upstream flag *is* passed that the config does not set: `--i_weights 2000`.
Its default is 10,000 — larger than this entire run — so without it the job would
have finished having written no checkpoint at all and there would have been
nothing to publish. That is a small, real trap for anyone shortening this
repository.

## The finding: two declared dependencies, one pip closure

`requirements.txt` lists `imageio-ffmpeg` and `opencv-python`. Both are Python
distributions. Both appear in a pip freeze. A reader of that freeze would
reasonably conclude the environment is fully described by it. For one of them
that is true and for the other it is not, and nothing in the record distinguishes
them.

**`imageio-ffmpeg` is pip-closed.** The wheel ships a statically linked
`ffmpeg-linux-x86_64-v7.0.2` binary inside `site-packages`. Installing the wheel
installs FFmpeg. The mp4 the render step writes needs nothing else.

**`opencv-python` is not.** It vendors ~30 shared objects into
`opencv_python.libs/` — Qt5, libav\*, OpenBLAS, libpng, libvpx — but `cv2`'s
extension module still carries unbundled `NEEDED` entries for `libGL.so.1`,
`libGLdispatch.so.0`, `libGLX.so.0`, `libglib-2.0.so.0` and
`libgthread-2.0.so.0`. Those come from OS packages — `libgl1`, `libglx0`,
`libglvnd0`, `libglib2.0-0` — that **no pip freeze can express**. On an image
without them, `import cv2` fails at load time, and because `run_nerf.py` imports
`load_blender.py` at module scope and `load_blender.py` imports `cv2` at module
scope, that failure lands at *import of the training script*, before a single
argument is parsed.

This row keeps `opencv-python` rather than switching to the drop-in
`opencv-python-headless`, which has no GL dependency. Swapping it would make the
row rebuild more easily by no longer reproducing what upstream declares, which is
the wrong trade for this project. Instead `repro/native_deps_probe.py` runs in
every setup stage and writes the boundary into the run's own log, and the setup
stage installs the OS packages in the open, by name, if `import cv2` fails.

## Other divergences from what upstream declares

`torch==1.11.0` (March 2022) is **not installed**: it publishes no wheel for this
image's Python and no build for a modern CUDA runtime, and installing it would
replace a working GPU torch with something that cannot address the GPU. The
image's torch is used and recorded, so a rebuild installs the version this run
actually ran on rather than a pin that has not been installable for years.
`torchvision>=0.9.1` is not installed either — `grep -r torchvision` over the
repository finds only the requirements line. `tensorboard>=2.0` *is* installed
and is never imported: the one `SummaryWriter` line is commented out
(`run_nerf.py:708`) and every `tf.contrib.summary` call sits inside a
triple-quoted block.

That last one is why this row has no experiment link. There is no wandb, mlflow,
comet or neptune anywhere in the tree, and the only tracker upstream names is
dead code. There was no flag to switch on; adding `wandb.init()` would have
bought a dashboard at the cost of the one property that makes the row worth
reading.

A related curiosity does reach the record. `run_nerf.py:12` does `import
matplotlib.pyplot as plt`, and `plt` is never referenced anywhere in the
repository — but the import executes, so matplotlib and its whole tail
(pillow, fonttools, kiwisolver, contourpy, cycler, pyparsing) are genuinely
loaded and genuinely belong in the recorded environment. A pin list records what
was loaded, not what was needed.

## If you clone this repository

It cannot run on CPU. `run_nerf.py:876` sets the global default tensor type to
`torch.cuda.FloatTensor` unconditionally, and it has to: `raw2outputs()` and
`render_rays()` build bare `torch.Tensor(...)` and `torch.linspace(...)` values
with no device argument and concatenate them with GPU tensors. There is no
`--device` flag and no fallback. The bare-clone check for this row therefore ends
at that line — which is the correct result, because it proves the import closure
is complete and the only thing missing was a GPU.
