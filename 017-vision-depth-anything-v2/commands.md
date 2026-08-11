# Commands — Depth Anything V2 (metric depth)

The recipe as recorded. Fork:
[`reproducible-ai/Depth-Anything-V2`](https://github.com/reproducible-ai/Depth-Anything-V2)
at `02dc493d42843827f8a1af1a3d4e447bc03721ac`; upstream base
`a561b849ebae10a6f5ef49e26c83cbbcd36c71bf`.

## 0 · Environment

Ubuntu 22.04, Python 3.12.10, 1x NVIDIA L40S (46 GB, compute 8.9), 4 vCPU AMD EPYC 7R13,
driver 580.126.09 / CUDA 13.0, AMI `ami-0f07f1a0b382b48f7`.

```sh
python -m pip install "numpy<2" h5py opencv-python-headless tensorboard remotezip
```

- `numpy<2` is required — see issues #1.
- `h5py` and `tensorboard` are missing from `metric_depth/requirements.txt` — issues #3.
- `opencv-python-headless` rather than `opencv-python`: the workload only decodes images
  and the GUI build pulls system OpenGL.
- `remotezip` is used by the data-slice step below, not by upstream.

Recorded versions on the training step (41 distributions): `torch==2.7.0`,
`torchvision==0.22.0`, `numpy==1.26.4`, `h5py==3.16.0`,
`opencv-python-headless==4.11.0.86`, `tensorboard==2.21.0`, `pillow==12.2.0`,
`triton==3.3.0`. No local-version (`+cu…`) pins anywhere.

## 1 · Pretrained encoder

`dist_train.sh` fine-tunes from the released *relative*-depth weights and keeps only the
encoder tensors:

```sh
env -C metric_depth python repro_fetch_pretrained.py --encoder vits
# -> checkpoints/depth_anything_v2_vits.pth   99,218,434 bytes, 4.9 s
```

Equivalent by hand: download
`https://huggingface.co/depth-anything/Depth-Anything-V2-Small/resolve/main/depth_anything_v2_vits.pth`
into `checkpoints/`.

## 2 · Dataset slice

```sh
env -C metric_depth python repro_prepare_hypersim_slice.py --train-frames 64 --val-frames 16
# -> data/hypersim/ai_001_001/... (64 train pairs)
# -> data/hypersim/ai_003_010/... (16 val pairs)
# -> dataset/splits/hypersim/{train,val}.txt
# 160 files, 19.6 MB, 40.3 s
```

The script takes the first N entries of `upstream_train.txt` / `upstream_val.txt` (the
manifests upstream ships, kept verbatim under those names — issues #2), resolves each to a
member of the official Apple scene archive
`https://docs-assets.developer.apple.com/ml-research/datasets/hypersim/v1/scenes/<scene>.zip`,
and reads **only those members** over HTTP range requests. The two archives touched are
2.2 GB and 2.2 GB; 19.6 MB is transferred.

## 3 · Train — upstream's `train.py`, unmodified

```sh
env -C metric_depth \
  RANK=0 WORLD_SIZE=1 LOCAL_RANK=0 MASTER_ADDR=127.0.0.1 MASTER_PORT=29500 \
  python train.py \
    --epochs 1 --encoder vits --bs 4 --lr 0.000005 \
    --save-path exp/hypersim --dataset hypersim \
    --img-size 518 --min-depth 0.001 --max-depth 20 \
    --pretrained-from ../checkpoints/depth_anything_v2_vits.pth --port 29500
```

Every flag except `--epochs` is what `dist_train.sh` passes (with `--encoder vits` in place
of its `vitl`). The five environment variables are the single-GPU requirement from
issues #4; they are inside the recorded command line, not exported around it, so the
record carries them.

Output: `metric_depth/exp/hypersim/latest.pth` (297,116,466 bytes — model + optimizer
state + epoch + best-metric dict) and a TensorBoard event file.

Log, end to end:

```
Iter: 0/16, LR: 0.0000050, Loss: 1.069
      d1,       d2,       d3,  abs_rel,   sq_rel,     rmse, rmse_log,    log10,    silog
   0.284,    0.548,    0.751,    0.650,    1.800,    2.203,    0.606,    0.211,    0.574
```

Peak GPU memory 5,245 MiB.

## 4 · Verify without a GPU

The whole path except CUDA/DDP runs on CPU in about 13 s, which is worth doing before
booking anything — it exercises the manifests, the HDF5 depth read, the transforms, the
encoder load, the loss and the metric:

```python
from dataset.hypersim import Hypersim
from depth_anything_v2.dpt import DepthAnythingV2
from util.loss import SiLogLoss
from util.metric import eval_depth
# build Hypersim('dataset/splits/hypersim/train.txt','train',size=(518,518)),
# load {k:v for k,v in torch.load(ckpt).items() if 'pretrained' in k} with strict=False
# -> 175 tensors loaded, forward/backward through SiLogLoss, eval_depth on a val frame
```

## 5 · Artifact

```
https://huggingface.co/reproducible-ai/depth-anything-v2/resolve/main/latest.pth
297,116,466 bytes
sha256 31a126b8ea3650b443573beab4887cf90242ad23ebce5a0b8c0ea5c279a35cfa
```

## 6 · Rebuild

```sh
roar reproduce f81176e64bf814489ec3296286e11c499a48ca28ef52569e10bc2675c0780782 \
  --lineage --run --no-puts
```
