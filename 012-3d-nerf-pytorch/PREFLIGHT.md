# Pre-flight evidence — row 012 (nerf-pytorch)

Everything here was produced on a **CPU-only control host** before any GPU was
booked. It is recorded because two of the four findings below would otherwise
have been discovered by a failing paid run, and because the third — the
pip-closure boundary — is the most interesting thing about this row and is not
visible from the recorded package list.

Upstream: `github.com/yenchenlin/nerf-pytorch` @ `63a5a630c9abd62b0f21c08703d0ac2ea7d4b9dd`
(default branch `master`, MIT).

---

## 1. Bare-clone check — import closure

Fresh clone of the fork, scratch venv containing only the distributions this
recipe expects to be recorded, `PYTHONPATH` unset:

```
$ git clone https://github.com/reproducible-ai/nerf-pytorch.git bareclone2
$ env -u PYTHONPATH <venv>/bin/python -c "import run_nerf"
run_nerf imported OK -- every module-level import resolved
```

`run_nerf.py` imports `numpy`, `imageio`, `torch`, `tqdm`, `matplotlib.pyplot`,
and its four sibling data loaders at module scope; `load_blender.py` and
`load_LINEMOD.py` each `import cv2`; `configargparse` is imported inside
`config_parser()`. No `ModuleNotFoundError` in any of them.

The scratch venv (26 distributions, CPU torch):

```
configargparse==1.7.5   contourpy==1.3.3   cycler==0.12.1   filelock==3.29.0
fonttools==4.63.0       fsspec==2026.4.0   imageio==2.37.4  imageio-ffmpeg==0.6.0
jinja2==3.1.6           kiwisolver==1.5.0  markupsafe==3.0.3 matplotlib==3.11.1
mpmath==1.3.0           networkx==3.6.1    numpy==2.5.2     opencv-python==5.0.0.93
packaging==26.3         pillow==12.3.0     pyparsing==3.3.2 python-dateutil==2.9.0.post0
setuptools==78.1.0      six==1.17.0        sympy==1.14.0    torch==2.13.0+cpu
tqdm==4.70.0            typing-extensions==4.15.0
```

## 2. Both recorded entry points reach upstream's own CUDA line

Running the two traced commands verbatim in that bare clone:

```
$ env -u PYTHONPATH <venv>/bin/python repro/train_truncated.py \
      --train-iters 1 --config configs/lego.txt --i_weights 1
  ...
  torch.set_default_tensor_type("torch.cuda.FloatTensor")
TypeError: type torch.cuda.FloatTensor not available. Torch not compiled with CUDA enabled.

$ env -u PYTHONPATH <venv>/bin/python run_nerf.py \
      --config configs/lego.txt --render_only --render_test --render_factor 8
  ...
  torch.set_default_tensor_type('torch.cuda.FloatTensor')
TypeError: type torch.cuda.FloatTensor not available. Torch not compiled with CUDA enabled.
```

That is the *correct* result for this check. The failure is a missing GPU on the
control host, not a missing package — the import closure is complete, and the
run gets all the way to `run_nerf.py`'s own first executable line before
stopping.

It also states a property of this repository worth knowing before you clone it:
**nerf-pytorch cannot run on CPU at all.** `run_nerf.py:876` sets the global
default tensor type to `torch.cuda.FloatTensor` unconditionally, and it has to,
because `raw2outputs()` and `render_rays()` build bare `torch.Tensor(...)` and
`torch.linspace(...)` values with no device argument and then concatenate them
with GPU tensors. There is no `--device cpu` and no fallback path.

## 3. Full pipeline exercised end-to-end on CPU

Not the recorded command — upstream's `train()` called directly, with the same
truncation rebinding and without the CUDA default-tensor line, on the real
`lego` data:

```
Loaded blender (138, 400, 400, 4) torch.Size([40, 4, 4]) [400, 400, 555.5555] ./data/nerf_synthetic/lego
[truncation] 1..200000 -> 1..3
[Config] Center cropping of size 200 x 200 is enabled until iter 500
[TRAIN] Iter: 1 Loss: 0.48108595609664917  PSNR: 4.453463554382324
[TRAIN] Iter: 2 Loss: 0.3321981728076935   PSNR: 6.8940043449401855
[TRAIN] Iter: 3 Loss: 0.21928703784942627  PSNR: 9.668449401855469
Saved checkpoints at ./logs/blender_paper_lego/000003.tar     (14,349,945 bytes)
```

then upstream's `--render_only --render_test --render_factor 16`, which reloaded
that checkpoint, rendered the 25 held-out test poses and wrote
`renderonly_test_000002/{000..024}.png` plus a `video.mp4` (ISO Media, MP4 Base
Media v1) through the bundled ffmpeg.

So: data loading, the truncation, the loss, the PSNR metric, the checkpoint
write, the checkpoint reload and the video encode were all known to work before
a GPU was booked. 17.2 s/iteration on CPU, which is why the row is truncated.

## 4. The pip-closure boundary — `opencv-python` vs `imageio-ffmpeg`

`requirements.txt` lists both. Both are Python distributions, both appear in a
pip freeze, and a reader of that freeze would reasonably conclude the
environment is fully described. For one of them that is true and for the other
it is not.

**`imageio-ffmpeg` 0.6.0 is pip-closed.** The wheel contains a statically linked
FFmpeg:

```
ffmpeg exe: <site-packages>/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2
bundled inside the wheel (pip-closed): True
ffmpeg version 7.0.2-static https://johnvansickle.com/ffmpeg/
```

Installing the wheel installs FFmpeg. Nothing else is needed for the mp4 the
render step writes.

**`opencv-python` 5.0.0.93 is not.** It vendors a great deal into
`opencv_python.libs/` — Qt5, libav*, OpenBLAS, libpng, libvpx, ~30 objects — but
`cv2.abi3.so` still carries unbundled `NEEDED` entries that resolve to system
paths:

```
OS-PKG   libGL.so.1         => /usr/lib/x86_64-linux-gnu/libGL.so.1
OS-PKG   libGLdispatch.so.0 => /usr/lib/x86_64-linux-gnu/libGLdispatch.so.0
OS-PKG   libGLX.so.0        => /usr/lib/x86_64-linux-gnu/libGLX.so.0
OS-PKG   libglib-2.0.so.0   => /usr/lib/x86_64-linux-gnu/libglib-2.0.so.0
OS-PKG   libgthread-2.0.so.0=> /usr/lib/x86_64-linux-gnu/libgthread-2.0.so.0
```

Those come from `libgl1` / `libglx0` / `libglvnd0` / `libglib2.0-0`, which **no
pip freeze can express**. On an image without them, `import cv2` fails at load
time with `ImportError: libGL.so.1: cannot open shared object file`, and because
`run_nerf.py` imports `load_blender.py` at module scope, and `load_blender.py`
imports `cv2` at module scope, the failure lands at *import of the training
script* — before a single argument is parsed.

This control host happened to have the GL stack, so `import cv2` succeeded and
the boundary was invisible until it was looked for. `repro/native_deps_probe.py`
runs in every setup stage so the boundary is written into the run's own log
rather than left for a rebuilder to hit.

The recipe deliberately keeps `opencv-python` rather than switching to
`opencv-python-headless`, which has no GL dependency: swapping it would make the
row rebuild more easily by no longer reproducing what upstream declares.

## 5. `requirements.txt` divergences

| line | status in this row |
|---|---|
| `torch==1.11.0` | **not installed.** March 2022; publishes no wheel for this image's Python and no build for a modern CUDA runtime. The image's own torch is used and recorded, so a rebuild installs the version this run actually ran on. |
| `torchvision>=0.9.1` | **not installed.** `grep -r torchvision` over the repository finds only this line — it is never imported. |
| `tensorboard>=2.0` | installed, **never imported.** The one `SummaryWriter` line is commented out (`run_nerf.py:708`) and every `tf.contrib.summary` call sits inside a triple-quoted block (`run_nerf.py:830-870`). |
| everything else | installed as listed. |

A related curiosity that *does* reach the record: `run_nerf.py:12` does
`import matplotlib.pyplot as plt` and `plt` is never referenced anywhere in the
repository. It is a dead import, but it is a dead import that executes, so
matplotlib (and pillow, fonttools, kiwisolver, contourpy, cycler, pyparsing) are
genuinely loaded and belong in the recorded environment. A pin list is a record
of what was loaded, not of what was needed.

## 6. No experiment logging exists to enable

`grep -ri "wandb\|mlflow\|comet_ml\|neptune"` over the entire tree returns
nothing. The training metric — PSNR, computed every `--i_print` iterations at
`run_nerf.py:768` — is written to stdout by `tqdm.write` at `run_nerf.py:829`
and nowhere else. `tensorboard` is declared and dead, as above.

So there is no framework logging flag to switch on, and the row publishes
`experimentUrl: null`. Adding `wandb.init()` to `run_nerf.py` would have
produced a link at the cost of the one property that makes this row worth
reading, so it was not done.
