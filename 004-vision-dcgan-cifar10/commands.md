# 004 — DCGAN / CIFAR-10 · commands

**Reconstructed** from the published DAG
`3a8ff4c4c89b4cf796fa568b773e4d482fe1fde848b8baf1805ce6a47b800ba0` and from the
workflow file committed in the fork at the recorded commit. Every command below is
either quoted from the DAG's own job records or from
[`.treqs/workflows/dcgan-cifar10.yaml`](https://github.com/reproducible-ai/examples/blob/6012a42715634b149bce107fbf77c80d87062791/.treqs/workflows/dcgan-cifar10.yaml)
at `6012a427`. Nothing here is inferred.

Upstream: `pytorch/examples` @ `acc295dc7b`, BSD-3-Clause.
Fork: `reproducible-ai/examples` @ `6012a42715634b149bce107fbf77c80d87062791`
("Reproducible AI: re-capture DCGAN/CIFAR-10 row on a plain-PyPI torch image",
2026-08-06 17:05:01 +0000). Working tree recorded **clean**, no uncommitted changes.

**No upstream source file was modified.** `dcgan/main.py` is byte-for-byte upstream.

## 0. Setup (untraced)

```bash
export PATH=/opt/pytorch/bin:$PATH
python -m pip install --quiet requests || true
roar --version
roar tracer use preload
roar tracer
roar init || true
```

`roar tracer use preload` is why this row's `tracer` field reads `preload`: the
tracer is pinned explicitly rather than left to auto-selection, so a reader
reproducing the row uses the same one. `preload` needs no extra capabilities,
unlike the eBPF tracer.

## 1. prepare — fetch CIFAR-10

```bash
export TRACKIO_SPACE_ID=reproducible-ai/experiments PYTHONUNBUFFERED=1
roar run -n prepare --wandb-to-trackio -- \
  python -c 'import torch, torchvision, torchvision.datasets as d; print("torch", torch.__version__, "torchvision", torchvision.__version__); d.CIFAR10(root="cifar10-data", download=True)'
```

The download is deliberately its own traced step rather than a side effect of the
training script. Under a `DataLoader` the dataset looks like something *training
produced*; split out, it is something training *consumed*, which is what the
lineage graph should say.

Recorded: **exit 0**, 1,497.22 s, job `f4ce119f`, GPU not used.

Nine artifacts recorded:

| bytes | path |
|---|---|
| 170,498,071 | `cifar10-data/cifar-10-python.tar.gz` |
| 31,035,704 | `cifar10-data/cifar-10-batches-py/data_batch_1` |
| 31,035,320 | `cifar10-data/cifar-10-batches-py/data_batch_2` |
| 31,035,999 | `cifar10-data/cifar-10-batches-py/data_batch_3` |
| 31,035,696 | `cifar10-data/cifar-10-batches-py/data_batch_4` |
| 31,035,623 | `cifar10-data/cifar-10-batches-py/data_batch_5` |
| 31,035,526 | `cifar10-data/cifar-10-batches-py/test_batch` |
| 158 | `cifar10-data/cifar-10-batches-py/batches.meta` |
| 88 | `cifar10-data/cifar-10-batches-py/readme.html` |

**This step took 24 minutes 57 seconds, and that is the download, not a hang.**
170,498,071 B over 1,497.17 s is an average of ~114 kB/s sustained; the campaign
ledger records the observed instantaneous rate as a steady ~110–128 kB/s
throughout. `cs.toronto.edu` throttles. Anyone rebuilding this row should expect
to wait roughly this long on step 1 and should not treat it as a stall.

## 2. train — one epoch

```bash
export TRACKIO_SPACE_ID=reproducible-ai/experiments PYTHONUNBUFFERED=1
roar run -n train --wandb-to-trackio -- \
  python dcgan/main.py --dataset cifar10 --dataroot cifar10-data --outf out \
                       --niter 1 --accel --workers 2 --manualSeed 42
```

Recorded: **exit 0**, 101.98 s, job `a37eae73`, GPU used, peak 1,480 MB.
Reads 8 of step 1's artifacts (the `.tar.gz` is not re-read once unpacked).

This is upstream's own documented CIFAR-10 invocation with three deviations, all
of them arguments — no code:

| flag | upstream default | here | why |
|---|---|---|---|
| `--niter` | `25` | `1` | **truncation.** One epoch = 782 iterations at batch 64 over CIFAR-10's 50,000 training images. Reproduce, not replicate. |
| `--manualSeed` | random 1–10000 | `42` | upstream seeds from `random.randint` when unset, so two runs of the same commit differ. Fixed so the recipe is a recipe. |
| `--outf` | `.` | `out` | keeps artifacts inside a tracked, gitignored output directory instead of the repo root. |

`--accel` and `--workers 2` are upstream's own flags at their documented meanings
(`--workers` is already 2 by default; it is passed explicitly so the recorded
command is self-describing).

Four artifacts recorded:

| bytes | path | |
|---|---|---|
| 14,323,315 | `out/netG_epoch_0.pth` | ← the published artifact |
| 11,076,841 | `out/netD_epoch_0.pth` | |
| 546,896 | `out/fake_samples_epoch_000.png` | |
| 379,915 | `out/real_samples.png` | |

`main.py` writes the two sample grids every 100 iterations (overwriting) and both
state dicts once per epoch. Only the generator is published; the discriminator is
recorded in lineage but not uploaded.

## 3. label + publish

```bash
roar label set artifact out/netG_epoch_0.pth \
  model.name=dcgan-cifar10 model.version=1 \
  license.id=BSD-3-Clause license.name='BSD 3-Clause License' \
  description='DCGAN (Radford et al. 2015) from pytorch/examples, trained on CIFAR-10. TRUNCATED pipeline-viability run: 1 epoch, NOT converged.' \
  documentation.url=https://github.com/pytorch/examples/blob/main/dcgan/README.md

roar put out/netG_epoch_0.pth hf://reproducible-ai/dcgan --public --yes --no-tag \
  -m "TRUNCATED pipeline-viability run: DCGAN on CIFAR-10, --niter 1 (one epoch, ~782 iters). NOT converged and not a quality result; published to demonstrate end-to-end provenance capture. Re-capture of the row on a plain-PyPI torch image so the recorded pip freeze is portable (no +cuNNN local-version pins)."
```

The truncation is stated in the artifact's own publish message and in its label
description, so it travels with the model rather than living only in these notes.

## The `.gitignore` change, and why it is a real finding

Upstream `.gitignore` ignores output paths as **directories**. A directory-ignore
does not survive `git clone`: the directory is simply absent from a fresh
checkout, so a cold rebuild either fails to write or writes somewhere untracked,
and the artifacts never become lineage edges. The fork replaces the
directory-ignore with a contents-ignore plus a committed `.gitkeep`:

```gitignore
cifar10-data/*
!cifar10-data/.gitkeep
out/*
!out/.gitkeep
```

Same twelve added lines also ignore `.roar/`, because the generated setup stage
runs `roar init`, which would otherwise leave the worktree dirty and block the
first traced run.

## Recorded environment

Identical across both traced steps.

| | |
|---|---|
| OS | Linux 6.8.0-1052-aws · Ubuntu 22.04 SMP · x86_64 |
| Cloud | AWS (hypervisor: amazon), host `ip-10-50-63-161` |
| CPU | Intel Xeon Platinum 8259CL @ 2.50 GHz — 4 vCPU (1 socket × 2 cores × 2 threads) |
| GPU | 1× Tesla T4, 15,360 MB, compute capability 7.5 |
| CUDA | 13.0, driver 580.126.09 |
| Memory | 15,788 MB total |
| Python | 3.12.10 CPython |
| roar | 0.4.3 |
| Tracer | `preload` (pinned in the workflow) |
| Env | `LANG=C.UTF-8`, `DO_NOT_TRACK=1`, `TRACKIO_SPACE_ID=reproducible-ai/experiments` |
| Run modifiers | `wandb_to_trackio: true` |

## Recorded freeze — 45 pins

All 45 resolve on PyPI (`freeze` gate: PORTABLE). No local-version (`+cuNNN`)
pins, no PEP-503 duplicate names — both of which had blocked the superseded first
capture of this row; the re-capture on a plain-PyPI torch image is what fixed it,
and is why the recorded commit message says "plain-PyPI torch image".

```
PyYAML==6.0.3               anyio==4.13.0               huggingface_hub==1.25.1     python-multipart==0.0.32
Pygments==2.20.0            blake3==1.0.9               idna==3.13                  rich==14.3.4
annotated-types==0.7.0      brotli==1.2.0               mpmath==1.3.0               roar-cli==0.4.3
certifi==2026.4.22          click==8.4.2                networkx==3.6.1             starlette==1.0.0
cryptography==46.0.7        defusedxml==0.7.1           numpy==2.4.4                sympy==1.14.0
dill==0.4.1                 filelock==3.29.0            nvidia-ml-py==13.595.45     tabulate==0.10.0
fsspec==2026.3.0            gradio_client==2.5.0        orjson==3.11.9              torch==2.7.0
h11==0.16.0                 httpcore==1.0.9             packaging==26.2             torchvision==0.22.0
httpx==0.28.1               pillow==12.2.0              pydantic==2.13.3            tqdm==4.67.3
pydantic_core==2.46.3       trackio==0.33.0             triton==3.3.0               typing-inspection==0.4.2
typing_extensions==4.15.0   uvicorn==0.46.0             watchfiles==1.2.0           wcwidth==0.6.0
zstandard==0.25.0
```

## Independent cold rebuild

```bash
roar reproduce 3a8ff4c4c89b4cf796fa568b773e4d482fe1fde848b8baf1805ce6a47b800ba0 \
     --lineage --run --no-puts
```

`--no-puts` excludes step 3 (the `roar put`) by design, which is why the
certification reports **2/2** against a 3-job DAG. Result and evidence:
`CERTIFICATION.md`.
