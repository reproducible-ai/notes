# 005 — exact commands

Fork: `reproducible-ai/pytorch-image-models` @ `f741a2b`
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

## 1. fetch_dataset — 17.3s

```bash
python reproduction/fetch_fashion_mnist.py --data-dir ./data
```

Downloads Fashion-MNIST (~30 MB) from the public torchvision mirror. No
credentials. 8 files under `data/FashionMNIST/raw/`. Kept as its own step so the
dataset is a recorded input to both training and evaluation rather than a side
effect of `train.py --dataset-download`.

## 2. train — 170.6s

```bash
python train.py \
  --data-dir ./data --dataset torch/fashion_mnist \
  --train-split train --val-split validation \
  --model resnet18 --num-classes 10 --in-chans 1 --img-size 28 \
  --mean 0.2860 --std 0.3530 \
  --batch-size 256 --epochs 5 --warmup-epochs 0 \
  --opt sgd --lr 0.05 --weight-decay 5e-4 --sched cosine \
  --workers 0 --seed 42 --save-last-only \
  --output ./output --experiment resnet18-fashion-mnist \
  --log-wandb --wandb-project resnet18-fashion-mnist
```

Produces `output/resnet18-fashion-mnist/{last.pth.tar, summary.csv, args.yaml}`.

Five flags need explaining:

- `--mean 0.2860 --std 0.3530` — mandatory with `--in-chans 1`; without them the
  run dies broadcasting a 3-channel normalisation onto a 1-channel image
  (issues.md #2).
- `--workers 0` — single-process data loading, so the recorded environment is
  the environment the workload actually ran in with no DataLoader worker
  subprocesses in the way. Requires this fork's `persistent_workers` fix
  (issues.md #1).
- `--save-last-only` — this fork's flag; leaves one checkpoint file instead of
  three hardlinked names for one blob (issues.md, "Not a defect").
- `--log-wandb` — the single switch gating every wandb call in `train.py`
  (`train.py:397`, `default=False`). Omit it and the run trains, exits 0, and
  logs **nothing**; this is why the previous capture of this row had no
  experiment dashboard. See issues.md #3.
- `--wandb-project` — required in practice alongside `--log-wandb`. timm
  defaults it to `None` (`train.py:399`) and forwards it verbatim; real wandb
  infers a name from it, a backend that declares `project` as a required string
  does not, and `wandb.init()` dies `TypeError: 'NoneType' object is not
  iterable` before epoch 0.

Result: `*** Best metric: 85.07 (epoch 4)`. Five metric rows
(`epoch, train_loss, eval_loss, eval_top1, eval_top5, lr`) are logged to the
experiment dashboard, one per epoch, via timm's own `update_summary()`.

## 3. evaluate — 33.9s

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
{ "model": "resnet18", "top1": 85.30, "top1_err": 14.70,
  "top5": 99.65, "top5_err": 0.35, "param_count": 11.18,
  "img_size": 28, "crop_pct": 1.0, "interpolation": "bicubic" }
```

## Bare-clone check (before any GPU spend)

```bash
git clone https://github.com/reproducible-ai/pytorch-image-models.git bc && cd bc
# venv containing ONLY timm's declared runtime deps; PYTHONPATH unset
env -u PYTHONPATH python reproduction/fetch_fashion_mnist.py --data-dir ./data
env -u PYTHONPATH python train.py ... --epochs 1 --device cpu \
    --log-wandb --wandb-project bareclone-preflight-005
env -u PYTHONPATH python validate.py ... --device cpu
```

All three steps completed on CPU with no `ModuleNotFoundError`; the 1-epoch CPU
checkpoint scored top-1 78.60. Nothing outside `requirements.txt` was needed
except the experiment-tracking backend, which timm deliberately does not declare
because logging is opt-in — and installing it downgraded nothing: `torch`,
`torchvision`, `numpy` and `huggingface_hub` all kept the versions the six
declared dependencies had already resolved to.

The bare clone is also where the `--wandb-project` trap was caught, for $0, by
replaying timm's exact `wandb.init(...)` call shape before any GPU was booked.

## Independent re-run

```bash
roar reproduce af56b02d6c041c931f03ccf643f2e0fee97bbddb0072f26b91a291f142850dfd \
  --lineage --run --no-puts
```
