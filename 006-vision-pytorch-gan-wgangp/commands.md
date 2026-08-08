# 006 — WGAN-GP / MNIST · commands

**Reconstructed** from the published DAG
`e812e9815b0934fa19a21be4f57c33349a462b5dee108b0fc9692f57b8f04f3a`, from the
workflow file committed in the fork at the recorded commit, and from the operator's
own in-fork `REPRODUCTION.md`. Every command below is either quoted from the DAG's
job records or from
[`.treqs/workflows/pytorch-gan-wgangp.yaml`](https://github.com/reproducible-ai/PyTorch-GAN/blob/b4c63045aead8024952f36cf7b664d8dcf1ee0c5/.treqs/workflows/pytorch-gan-wgangp.yaml)
at `b4c63045`. Nothing here is inferred.

Upstream: `eriklindernoren/PyTorch-GAN` @ `36d3c77e5f`, MIT.
Fork: `reproducible-ai/PyTorch-GAN` @ `b4c63045aead8024952f36cf7b664d8dcf1ee0c5`
("Reproducible AI: WGAN-GP reproduction workflow (row 006)", 2026-08-06 15:12:20
+0000). Working tree recorded **clean**, no uncommitted changes.

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

## 1. prepare — fetch MNIST

```bash
export TRACKIO_SPACE_ID=reproducible-ai/experiments PYTHONUNBUFFERED=1
roar run -n prepare --wandb-to-trackio -- \
  python implementations/wgan_gp/prepare_data.py --data_root data/mnist
```

`prepare_data.py` is **added by the fork** (38 lines). Upstream fetches MNIST as a
side effect of constructing the `DataLoader` inside the training script — which, as
the operator put it, "makes the dataset look like something *training* produced
rather than something it consumed." Splitting it out is what lets the lineage graph
state the dependency correctly.

Recorded: **exit 0**, 126.19 s, job `c22a45a8`, GPU not used. Eight artifacts:

| bytes | path |
|---|---|
| 47,040,016 | `data/mnist/MNIST/raw/train-images-idx3-ubyte` |
| 9,912,422 | `data/mnist/MNIST/raw/train-images-idx3-ubyte.gz` |
| 7,840,016 | `data/mnist/MNIST/raw/t10k-images-idx3-ubyte` |
| 1,648,877 | `data/mnist/MNIST/raw/t10k-images-idx3-ubyte.gz` |
| 60,008 | `data/mnist/MNIST/raw/train-labels-idx1-ubyte` |
| 28,881 | `data/mnist/MNIST/raw/train-labels-idx1-ubyte.gz` |
| 10,008 | `data/mnist/MNIST/raw/t10k-labels-idx1-ubyte` |
| 4,542 | `data/mnist/MNIST/raw/t10k-labels-idx1-ubyte.gz` |

## 2. train — 3 epochs

```bash
export TRACKIO_SPACE_ID=reproducible-ai/experiments PYTHONUNBUFFERED=1
roar run -n train --wandb-to-trackio -- \
  python implementations/wgan_gp/wgan_gp.py --n_epochs 3 --seed 42 \
         --data_root data/mnist --sample_dir samples --checkpoint out/wgangp.pt
```

Recorded: **exit 0**, 66.24 s, job `74d3e84d`, GPU used, peak 582 MB.
Reads exactly the two training-split artifacts from step 1 — images and labels — and
nothing else. The step also carries a recorded dataset fingerprint
(`b60ae3bb50760b12…`, blake3, confidence 0.55).

`--n_epochs 3` against an upstream default of **200** is the truncation. Every other
flag on this line is one the fork *added*, and each one's default reproduces upstream
behaviour exactly when omitted:

| flag | default (= upstream behaviour) | here |
|---|---|---|
| `--seed` | `-1` (unseeded) | `42` — upstream seeds nothing, so two runs of the same commit differ |
| `--data_root` | `../../data/mnist` (upstream's literal) | `data/mnist` |
| `--sample_dir` | `images` (upstream's literal) | `samples` |
| `--checkpoint` | `""` (save nothing) | `out/wgangp.pt` — **upstream saves no model at all** |

The last two exist because upstream hard-coded both paths *relative to the process
working directory*, so `wgan_gp.py` could only ever be launched from inside
`implementations/wgan_gp/`. Making them configurable is what lets the pipeline run
from the repository root and keep every artifact inside the repo where lineage can
see it.

Nine artifacts recorded:

| bytes | path | |
|---|---|---|
| 8,197,921 | `out/wgangp.pt` | ← the published artefact |
| 48,008 | `samples/0.png` | |
| 25,320 | `samples/400.png` | |
| 21,931 | `samples/800.png` | |
| 21,712 | `samples/1200.png` | |
| 20,608 | `samples/1600.png` | |
| 23,673 | `samples/2000.png` | |
| 21,605 | `samples/2400.png` | |
| 20,287 | `samples/2800.png` | |

Eight grids at `--sample_interval 400` (upstream's default) over three epochs.
`wgangp.pt` holds both `state_dict`s plus the parsed argparse config, `img_shape`,
`lambda_gp`, the epoch count and the batch count — enough for the evaluation step
to reconstruct the network without guessing.

## 3. evaluate — score the held-out test split

```bash
export TRACKIO_SPACE_ID=reproducible-ai/experiments PYTHONUNBUFFERED=1
roar run -n evaluate --wandb-to-trackio -- \
  python implementations/wgan_gp/eval_wgan_gp.py --checkpoint out/wgangp.pt \
         --data_root data/mnist --metrics metrics/metrics.json
```

`eval_wgan_gp.py` is **added by the fork** (194 lines). Recorded: **exit 0**, 6.64 s,
job `a94de43c`, GPU used. Reads the checkpoint plus the two **test**-split artifacts
— training used the train split, so the evaluation set is genuinely unseen. Writes
one artifact: `metrics/metrics.json`, 633 B.

Computed on the test split: mean critic score on real images, mean critic score on
generated images, the Wasserstein-distance estimate `E[D(real)] − E[D(fake)]`, and
the WGAN-GP gradient penalty. The file **self-tags `truncated_run: true`** — the
script correctly labelling a 3-epoch checkpoint. That flag is expected and is not a
failure signal.

A metric is *computed*; no claim is made about its value.

The `Generator` and `Discriminator` classes are copied into `eval_wgan_gp.py` rather
than imported, because upstream defines them at module scope beside the training
loop — importing them would also run training. `load_state_dict(..., strict=True)`
is used deliberately so that any future drift between the two copies fails loudly
instead of silently evaluating a different network.

## 4. label + publish

```bash
roar label set artifact out/wgangp.pt \
  model.name=pytorch-gan-wgangp model.version=1 \
  license.id=MIT license.name='MIT License' \
  description='WGAN-GP (Wasserstein GAN with gradient penalty), MLP generator + critic, trained on MNIST 28x28. Clean-room reproduction of implementations/wgan_gp from eriklindernoren/PyTorch-GAN (MIT). TRUNCATED 3-epoch run, not converged.' \
  documentation.url=https://github.com/reproducible-ai/PyTorch-GAN/blob/master/implementations/wgan_gp/REPRODUCTION.md

roar put out/wgangp.pt hf://reproducible-ai/pytorch-gan-wgangp --public --yes --no-tag \
  -m "TRUNCATED reproduction: WGAN-GP trained 3 epochs on MNIST (upstream default is 200). NOT converged - published as a provenance artifact, not a quality result."
```

The truncation is stated in the artifact's own publish message and label
description, so it travels with the model rather than living only in these notes.

## Output directories

All four output directories — `data/`, `samples/`, `out/`, `metrics/` — hold a
committed `.gitkeep` with their contents gitignored, so a clean checkout has
somewhere to write and the working tree stays clean between steps. The
repository-level `.gitignore` also needed a rule for `metrics/`, because upstream's
`.gitignore` contains a bare `*.json` that would otherwise silently swallow the
metrics file (see `issues.md`, finding 7).

## Recorded environment

Identical across all three traced steps.

| | |
|---|---|
| OS | Linux 6.8.0-1052-aws · Ubuntu 22.04 SMP · x86_64 |
| Cloud | AWS (hypervisor: amazon), host `ip-10-50-49-50` |
| CPU | AMD EPYC 7R13 — 4 vCPU (1 socket × 2 cores × 2 threads) |
| GPU | 1× NVIDIA L40S, 46,068 MB, compute capability 8.9 |
| CUDA | 13.0, driver 580.126.09 |
| Memory | 31,640 MB total |
| Python | 3.12.10 CPython |
| roar | 0.4.3 |
| Tracer | `preload` (pinned in the workflow) |
| Env | `LANG=C.UTF-8`, `DO_NOT_TRACK=1`, `TRACKIO_SPACE_ID=reproducible-ai/experiments` |
| Run modifiers | `wandb_to_trackio: true` |

**The L40S buys this row very little.** Peak GPU memory across the whole run is
582 MB, on a card with 46 GB, and the entire training step is 66 seconds. An MLP
generator and critic on 28×28 MNIST is a small workload; the hardware is what the
campaign's compute target happened to provide, not what the recipe requires.

## Recorded freeze — 45 pins

All 45 resolve on PyPI (`freeze` gate: PORTABLE). No local-version (`+cuNNN`) pins
and no PEP-503 duplicate names. This is byte-for-byte the **same 45-pin set** the
DCGAN row (004) recorded — same image, same day, same plain-PyPI torch family.

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

Worth contrasting with upstream's own `requirements.txt`, which is `torch>=0.4.0`
plus a handful of bare, unpinned names. That admits every PyTorch release from 2018
to the present and describes no environment that can actually be rebuilt — see
`issues.md`, finding 5.

## Rebuilding by hand (no roar)

From the operator's `REPRODUCTION.md`:

```bash
git clone https://github.com/reproducible-ai/PyTorch-GAN
cd PyTorch-GAN
python implementations/wgan_gp/prepare_data.py --data_root data/mnist
python implementations/wgan_gp/wgan_gp.py --n_epochs 3 --seed 42 \
    --data_root data/mnist --sample_dir samples --checkpoint out/wgangp.pt
python implementations/wgan_gp/eval_wgan_gp.py --checkpoint out/wgangp.pt \
    --data_root data/mnist --metrics metrics/metrics.json
```

## Independent cold rebuild

```bash
roar reproduce e812e9815b0934fa19a21be4f57c33349a462b5dee108b0fc9692f57b8f04f3a \
     --lineage --run --no-puts
```

`--no-puts` excludes step 4 (the `roar put`) by design, which is why the
certification reports **3/3** against a 4-job DAG. Result and evidence:
`CERTIFICATION.md`.
