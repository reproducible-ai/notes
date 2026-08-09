# 005 — exact commands

Fork: `reproducible-ai/pytorch-image-models` @ `81bbe92`
(upstream `huggingface/pytorch-image-models` @ `aa4b585`).
Recorded pipeline: [`.treqs/workflows/timm-resnet18-fashion-mnist.yaml`](https://github.com/reproducible-ai/pytorch-image-models/blob/main/.treqs/workflows/timm-resnet18-fashion-mnist.yaml).

Everything below is what the record contains. Nothing needed for a step lives
outside the step's own command line.

## Environment

```bash
python -m pip install -r requirements.txt        # torch, torchvision, pyyaml,
                                                 # huggingface_hub, safetensors, numpy
```

No `pip install -e .`. `train.py` and `validate.py` are run **from the
repository root** and import the checked-out `timm/` package directly. The
pipeline asserts this before training:

```bash
# no `timm` distribution may be visible, or the freeze would pin a PyPI timm
# that is not the code being run
python -c "import importlib.metadata as m,sys; \
  d=[x for x in m.distributions() if (x.metadata['Name'] or '').lower()=='timm']; \
  print('timm distributions visible:', [x.version for x in d]); sys.exit(1 if d else 0)"

# ...and the imported package must come from the checkout
python -c "import timm,os; p=os.path.abspath(timm.__file__); \
  print('timm package ->', p, timm.__version__); \
  assert p.startswith(os.getcwd()), 'timm resolved OUTSIDE the checkout'"
```

## 1. fetch_dataset — 18.3s

```bash
python reproduction/fetch_fashion_mnist.py --data-dir ./data
```

Downloads Fashion-MNIST (~30 MB) from the public torchvision mirror. No
credentials. 8 files under `data/FashionMNIST/raw/`. Kept as its own step so the
dataset is a recorded input to both training and evaluation rather than a side
effect of `train.py --dataset-download`.

## 2. train — 166.5s

```bash
python train.py \
  --data-dir ./data --dataset torch/fashion_mnist \
  --train-split train --val-split validation \
  --model resnet18 --num-classes 10 --in-chans 1 --img-size 28 \
  --mean 0.2860 --std 0.3530 \
  --batch-size 256 --epochs 5 --warmup-epochs 0 \
  --opt sgd --lr 0.05 --weight-decay 5e-4 --sched cosine \
  --workers 0 --seed 42 --save-last-only \
  --output ./output --experiment resnet18-fashion-mnist
```

Produces `output/resnet18-fashion-mnist/{last.pth.tar, summary.csv, args.yaml}`.

Three flags need explaining:

- `--mean 0.2860 --std 0.3530` — mandatory with `--in-chans 1`; without them the
  run dies broadcasting a 3-channel normalisation onto a 1-channel image
  (issues.md #2).
- `--workers 0` — single-process data loading, so the recorded environment is
  the environment the workload actually ran in with no DataLoader worker
  subprocesses in the way. Requires this fork's `persistent_workers` fix
  (issues.md #1).
- `--save-last-only` — this fork's flag; leaves one checkpoint file instead of
  three hardlinked names for one blob (issues.md, "Not a defect").

Result: `*** Best metric: 85.93 (epoch 4)`.

## 3. evaluate — 42.2s

```bash
python validate.py \
  --data-dir ./data --dataset torch/fashion_mnist --split validation \
  --model resnet18 --num-classes 10 --in-chans 1 --img-size 28 \
  --mean 0.2860 --std 0.3530 --crop-pct 1.0 \
  --batch-size 256 --workers 0 \
  --checkpoint ./output/resnet18-fashion-mnist/last.pth.tar \
  --results-file ./metrics/eval.json --results-format json
```

Scores the **published** checkpoint on the 10,000-image held-out split and
writes the metric as a file:

```json
{ "model": "resnet18", "top1": 85.67, "top1_err": 14.33,
  "top5": 99.73, "top5_err": 0.27, "param_count": 11.18,
  "img_size": 28, "crop_pct": 1.0, "interpolation": "bicubic" }
```

## Bare-clone check (before any GPU spend)

```bash
git clone https://github.com/reproducible-ai/pytorch-image-models.git bc && cd bc
# venv containing ONLY timm's declared runtime deps; PYTHONPATH unset
env -u PYTHONPATH python reproduction/fetch_fashion_mnist.py --data-dir ./data
env -u PYTHONPATH python train.py ... --epochs 1 --device cpu --no-prefetcher
env -u PYTHONPATH python validate.py ... --device cpu
```

All three steps completed on CPU with no `ModuleNotFoundError`; the 1-epoch CPU
checkpoint scored top-1 77.41. Nothing outside `requirements.txt` was needed.

## Independent re-run

```bash
roar reproduce 42b381d91f299d028c45ff043a71e34e6c9e1122574585f32c3b3d99b31f10c2 \
  --lineage --run --no-puts
```
