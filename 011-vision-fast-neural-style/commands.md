# Commands — 011 fast_neural_style

## Current-stack retry — 2026-09-01

Fork: `reproducible-ai/examples` at full commit
`4902d7199692c8707edb54759cfc1d627ce94225`, based on upstream
`acc295dc7b90714f1bf47f06004fc19a7fe235c4`. That is the commit behind the
Tier-1 record.

The isolated Python environment contains exact plain-PyPI distributions:
`numpy==2.2.6`, `pillow==11.3.0`, `torch==2.7.0`, and
`torchvision==0.22.0`. The three recorded workload commands are:

```sh
sh -c 'set -eu; mkdir -p fast_neural_style/out-data; curl -fL \
  -o fast_neural_style/out-data/imagenette2-320.tgz \
  https://s3.amazonaws.com/fast-ai-imageclas/imagenette2-320.tgz; \
  echo "569b4497c98db6dd29f335d1f109cf315fe127053cedf69010d047f0188e158c  fast_neural_style/out-data/imagenette2-320.tgz" | sha256sum -c -; \
  tar -xzf fast_neural_style/out-data/imagenette2-320.tgz -C fast_neural_style/out-data'

env -C fast_neural_style python neural_style/neural_style.py train \
  --dataset out-data/imagenette2-320/train \
  --style-image images/style-images/mosaic.jpg \
  --save-model-dir out-model --checkpoint-model-dir out-ckpt \
  --epochs 1 --batch-size 4 --checkpoint-interval 2368 --accel

env -C fast_neural_style python neural_style/neural_style.py eval \
  --content-image images/content-images/amber.jpg \
  --model out-ckpt/ckpt_epoch_0_batch_id_2368.pth \
  --output-image out-stylized/amber-mosaic.jpg --accel
```

The checkpoint and stylized JPEG are named together in one publish operation. No
pipeline sink creates either file; the training and evaluation processes write them
directly.

The follow-up at commit `4902d7199692c8707edb54759cfc1d627ce94225`
replaced only the first recorded command with direct shell tools:

```sh
sh -c 'set -eu; mkdir -p fast_neural_style/out-data; \
  curl -fL -o fast_neural_style/out-data/imagenette2-320.tgz \
    https://s3.amazonaws.com/fast-ai-imageclas/imagenette2-320.tgz; \
  echo "569b4497c98db6dd29f335d1f109cf315fe127053cedf69010d047f0188e158c  fast_neural_style/out-data/imagenette2-320.tgz" | sha256sum -c -; \
  tar -xzf fast_neural_style/out-data/imagenette2-320.tgz \
    -C fast_neural_style/out-data'
```

The first execution of that follow-up completed the workload and uploaded both artifacts
but produced no lineage hash. An immutable retry produced the Tier-1 record.

## August capture recipe

The recipe, in the order it runs. Everything below is scoped to
`fast_neural_style/` inside the `pytorch/examples` monorepo; no sibling example
directory is read, written or installed.

Fork: `reproducible-ai/examples` @ `3a7a01cc2d1b0d91f2c9795152fdbcbf5c944b83` — the
commit recorded in the published DAG.
Upstream: `pytorch/examples` @ `6012a427` (the fork point; `fast_neural_style/` is
unmodified from it).
Provenance CLI: `roar-cli==0.4.4rc6`, installed by name and version from a public index
and verified by wheel sha256
`c7115b748886259b6a089e547404376acf84c3b81b4cbc8dc5610490ebea7199`
(`roar_cli-0.4.4rc6-cp310-abi3-manylinux_2_34_x86_64.whl`).

---

## 0. Setup — untraced, nothing here reaches the lineage

Runs on the compute host before any recorded step. In full it: installs the
provenance CLI from a public index by name+version and verifies it by wheel sha256;
pins the tracer to `preload`; then gates the environment. The gates are the part
worth copying:

```sh
# Pillow is imported by neural_style/utils.py:2 but is NOT in requirements.txt.
# Fail here, untraced, rather than mid-training.
python -c "import PIL; print('pillow', PIL.__version__)"

# torch.accelerator (neural_style.py:33, under --accel) landed in torch 2.6,
# which is exactly why requirements.txt says torch>=2.6.
python -c "import torch; assert hasattr(torch, 'accelerator'); print(torch.__version__)"

# A '+cuNNN' local-version pin or a PEP-503 duplicate makes the recorded freeze
# un-installable from PyPI, so the lineage could never be rebuilt. Fail before
# spending, not at verification.
python fast_neural_style/repro/freeze_audit.py

# HF_TOKEN is needed by the publish stage only. Prove it reached the task env
# before paying for training, rather than discovering it after every traced step
# has already succeeded. Length only; the value is never printed.
python -c "import os,sys; t=os.environ.get('HF_TOKEN') or ''; print('present:', bool(t), 'len:', len(t)); sys.exit(0 if t else 1)"
```

### The one measurement that makes the cost model defensible

`Vgg16.__init__` (`neural_style/vgg.py:10`) constructs
`models.vgg16(weights=VGG16_Weights.IMAGENET1K_V1)`, so the first thing training does
on a cold host is pull a ~528 MB ImageNet checkpoint from `download.pytorch.org`.
That is a **fixed** cost — paid once, whether you run one epoch or twenty — and
scaling a wall-clock that contains it is how a full-run estimate ends up wrong by an
order of magnitude. So it is timed separately, into a throwaway `TORCH_HOME` so the
real cache stays cold and the train step still pays what a fresh machine pays:

```sh
rm -rf /var/tmp/torchhome-probe
TORCH_HOME=/var/tmp/torchhome-probe python -c "
import time, torchvision, os
t0 = time.time(); torchvision.models.vgg16(weights='VGG16_Weights.IMAGENET1K_V1')
dt = time.time() - t0
tot = sum(os.path.getsize(os.path.join(d,f)) for d,_,fs in os.walk('/var/tmp/torchhome-probe') for f in fs)
print('VGG16_IMAGENET_WEIGHTS_DOWNLOAD_SECONDS %.2f BYTES %d' % (dt, tot))"
rm -rf /var/tmp/torchhome-probe
```

Measured on this run: **4.10 s, 553,433,881 bytes** (4.10 / 3.75 / 3.85 s
across three cold hosts, identical byte count each time).

---

## 1. `fetch_dataset` — traced

```sh
python fast_neural_style/repro/fetch_dataset.py \
    --url https://s3.amazonaws.com/fast-ai-imageclas/imagenette2-320.tgz \
    --out-dir fast_neural_style/out-data \
    --expect-train-images 9469
```

New file, standard library only. Upstream ships no downloader — its README points a
human at COCO 2014 train (13 GB) and stops — and a recorded pipeline cannot start
from a manual browser download.

`--expect-train-images` is not decoration. The training step's
`--checkpoint-interval` is derived from this count (see step 2), so a dataset that
silently changed size would train for ~8 GPU-minutes and then write a file no later
step knows the name of. This exits non-zero first.

Measured: 342 MB in 6.3 s, extract 5.8 s, **50 s for the whole traced step**
(20.8 s of it recorded as the job's own duration; the rest is the tracer hashing
13,396 extracted files).
Archive sha256 `569b4497c98db6dd29f335d1f109cf315fe127053cedf69010d047f0188e158c` —
identical to the copy fetched independently on the control host, so the dataset has a
stable identity.

## 2. `train` — traced, the only expensive step

```sh
python fast_neural_style/neural_style/neural_style.py train \
    --dataset fast_neural_style/out-data/imagenette2-320/train \
    --style-image fast_neural_style/images/style-images/mosaic.jpg \
    --save-model-dir fast_neural_style/out-models \
    --checkpoint-model-dir fast_neural_style/out-ckpt \
    --checkpoint-interval 2368 \
    --epochs 1 \
    --batch-size 4 \
    --image-size 256 \
    --seed 42 \
    --log-interval 200 \
    --accel
```

Upstream's own entry point, upstream's own flags, zero lines changed under
`neural_style/`.

Three of these need explaining:

**`--checkpoint-interval 2368`** — this is the whole reason the pipeline can name its
own artifact. Upstream's *final* model filename embeds a wall-clock timestamp
(`neural_style.py:119-122`), so it is unknowable until after the run; its
*checkpoint* filename is `ckpt_epoch_{e}_batch_id_{n}.pth` (`:112`), which is fully
determined by the recipe. 2368 = ceil(9469 / 4) = the number of batches in the epoch,
so the checkpoint fires exactly once, on the last batch, after that batch's
`optimizer.step()`. Same weights as the timestamped final model; a nameable path.

**`--epochs 1`** — upstream's default is 2 (`neural_style.py:196`). This is the
truncation, and it is the axis a reader edits to run the thing in full.

**Neither `--style-size` nor `--content-scale` is passed, anywhere.** Both route into
`utils.load_image`, which calls `Image.ANTIALIAS` — removed in Pillow 10.0. Passing
either raises `AttributeError` on any current Pillow. Left unset, `load_image` skips
the resize branch and the example runs clean. See `issues.md` §3.

There is no `--num_workers` to get wrong: `neural_style.py:49` builds
`DataLoader(train_dataset, batch_size=args.batch_size)` with no workers argument at
all, so loading is single-process by construction.

Measured: **9m12s** for 9,469 images / 2,368 batches ≈ **19.26 images/s** on one T4
(that step wall-clock includes the ~4 s VGG-16 weight download and process startup;
see `costs.md` for the fixed/variable split). Running-mean total loss fell from
10,715,696 at the first log line (800 images) to 3,024,145 at the last one (8,800
images). Note that upstream prints only every
`--log-interval` batches and 2,368 is not a multiple of 200, so **there is no
end-of-epoch loss line** — the last printed value is at 8,800 of 9,469 images.

## 3. `stylize` — traced

```sh
python fast_neural_style/neural_style/neural_style.py eval \
    --content-image fast_neural_style/images/content-images/amber.jpg \
    --model fast_neural_style/out-ckpt/ckpt_epoch_0_batch_id_2368.pth \
    --output-image fast_neural_style/out-stylized/amber-mosaic.jpg \
    --accel
```

Upstream's own `eval` subcommand on upstream's own bundled content image, applying
the model the previous step produced. This is the only evaluation this example ships
— it renders an image; there is no held-out metric to compute. Measured: **11 s**.

## 4. `label`, then `publish` — untraced

Both artifacts are labelled, because both are published and an artifact that reaches the
record unlabelled is a hole in the AI-BOM:

```sh
roar label set artifact fast_neural_style/out-ckpt/ckpt_epoch_0_batch_id_2368.pth \
    model.name=fast-neural-style model.version=1 \
    license.id=BSD-3-Clause license.name='BSD 3-Clause License' \
    description='…TRUNCATED pipeline-viability run: 1 of upstream'"'"'s default 2 epochs, over Imagenette-320 (9,469 images) instead of the README'"'"'s COCO-2014-train (82,783). NOT converged.' \
    documentation.url=https://github.com/pytorch/examples/blob/main/fast_neural_style/README.md

roar label set artifact fast_neural_style/out-stylized/amber-mosaic.jpg \
    model.name=fast-neural-style model.version=1 \
    license.id=BSD-3-Clause license.name='BSD 3-Clause License' \
    description='Output of the stylize step … the ONLY evaluation fast_neural_style ships …' \
    documentation.url=https://github.com/pytorch/examples/blob/main/fast_neural_style/README.md
```

The upload itself is a plain `huggingface_hub.HfApi.upload_file` of the two files to
`hf://reproducible-ai/fast-neural-style`, run from the provenance CLI's own tool venv so
that nothing is installed into the workload interpreter and no traced step's recorded
package set is affected by it. The commit message is recorded verbatim and permanently,
so it states the truncation rather than implying a finished model.

The run that produced the published DAG did not execute this stage; the files now in the
Hugging Face repo come from a later execution of the same recipe. `README.md` gives both
sets of sha256 values so the difference is visible rather than implied.

---

## Rebuilding this row

```
roar reproduce 63edfd1d69128bf4032d089ace64aa301c1a44e0b60d48abfe83b619d4e6e377 \
    --lineage --run --no-puts
```

**To run it untruncated**, take `roar reproduce --script`, change `--epochs 1` to
`--epochs 2` in the train step, and change `--checkpoint-interval 2368` to `4736`
(2 × 2368) so the single checkpoint still lands on the final batch of the final
epoch. Both edits are in the same command; nothing else changes. See `costs.md` for
what that costs.

---

## The bare-clone check, run before any of the above

From a fresh clone, in a scratch venv containing only the three declared dependencies
(`numpy`, `torch`, `torchvision` — Pillow arriving transitively, per `issues.md` §2),
with `PYTHONPATH` unset:

```sh
python3 -m venv bare-venv
./bare-venv/bin/pip install numpy torch torchvision   # CPU wheels, for speed
env -u PYTHONPATH ./bare-venv/bin/python fast_neural_style/repro/fetch_dataset.py --out-dir …
env -u PYTHONPATH ./bare-venv/bin/python fast_neural_style/neural_style/neural_style.py train …
env -u PYTHONPATH ./bare-venv/bin/python fast_neural_style/neural_style/neural_style.py eval …
```

No `ModuleNotFoundError` on any of the three. This is the check that costs cents and
saves a GPU rebuild; it is also where the `Image.ANTIALIAS` breakage, the
`python -m` failure and the timestamped-filename problem were all found, before a
single cent of GPU time was spent.
