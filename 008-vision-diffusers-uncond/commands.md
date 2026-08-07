# 008 — the recipe

Upstream: `huggingface/diffusers` @ `9c6a68c32b3b2a64db91800b624d33cec6e25ab8`
Fork:     `reproducible-ai/diffusers` @ `8b7b6d99e3855aefa5e124e8fd4d008d76b79741`

## 0. Fork and clone

```bash
gh repo fork huggingface/diffusers --org reproducible-ai        # default branch: main
git clone --filter=blob:none --single-branch --branch main \
    https://github.com/reproducible-ai/diffusers.git
cd diffusers
```

`--filter=blob:none` matters here: the repo is ~106 MB with a long history and
~900 branches; a treeless single-branch clone takes ~4 s instead of minutes.

## 1. Fix the output directories in the fork

Replace the `/data` directory ignore in `.gitignore` with a file-pattern ignore,
and add the same shape for every directory the run writes to, each with a tracked
`.gitkeep`. See `issues.md` §3 and
`patches/0001-gitignore-replace-data-directory-ignore.patch`.

Output directories declared for this row: `data` (dataset cache), `ddpm-out`
(pipeline root), `ddpm-out/unet` (weights), `ddpm-out/scheduler` (scheduler config).

## 2. Environment

`diffusers` is deliberately **not** installed — see `issues.md` §1.

```bash
pip install --upgrade-strategy only-if-needed \
    "accelerate>=0.16.0" datasets safetensors trackio wandb
python -c "import torchvision" || pip install torchvision
```

`safetensors` and `wandb` are the two the example's `requirements.txt` omits.
`torchvision` is installed only if absent, so a prebuilt CUDA `torch` is never
displaced by a resolver picking a different wheel.

## 3. Train

The recorded command. `PYTHONPATH` is set *inside* it, not around it, so the
recipe is self-contained; `sh -c` is used rather than `env` so that the assignment
**appends to** the ambient `PYTHONPATH` instead of replacing it.

```bash
sh -c 'PYTHONPATH=src:$PYTHONPATH exec python \
  examples/unconditional_image_generation/train_unconditional.py \
  --dataset_name=huggan/pokemon \
  --cache_dir=data \
  --resolution=64 --center_crop --random_flip \
  --output_dir=ddpm-out \
  --train_batch_size=16 \
  --num_epochs=1 \
  --save_images_epochs=1 --save_model_epochs=1 \
  --gradient_accumulation_steps=1 \
  --use_ema \
  --learning_rate=1e-4 --lr_warmup_steps=10 \
  --mixed_precision=no \
  --logger=wandb \
  --dataloader_num_workers=0 \
  --ddpm_num_inference_steps=10 \
  --eval_batch_size=4 \
  --checkpointing_steps=100000'
```

### Deltas from the README's Pokémon command, and why

| Flag | README | Here | Why |
|---|---|---|---|
| `--num_epochs` | 100 | **1** | Truncation. This is a *reproduce* row: the pipeline is demonstrated, convergence is not claimed. |
| `--lr_warmup_steps` | 500 | 10 | With 460 total steps a 500-step warmup never leaves warmup. |
| `--ddpm_num_inference_steps` | 1000 | 10 | End-of-epoch sampling only; dominates wall-clock otherwise. |
| `--eval_batch_size` | 16 | 4 | Same. |
| `--logger` | (default `tensorboard`) | `wandb` | The repo ships wandb support; enabling it puts a live metrics URL in the record. TensorBoard writes only local event files. |
| `--cache_dir` | unset | `data` | Keeps the dataset cache in-tree and in lineage instead of in a global home cache. |
| `--checkpointing_steps` | 500 | 100000 | Suppresses resume-checkpoint directories, which are not part of the published artifact. |
| `--dataloader_num_workers` | 0 (default) | 0 (explicit) | Pinned deliberately: worker subprocesses distort what the run records as its environment. |
| launcher | `accelerate launch` | `python` | Single device; avoids the interactive `accelerate config` step. Identical behaviour — see `issues.md` §5. |

Unchanged from the README: `--resolution=64 --center_crop --random_flip`,
`--train_batch_size=16`, `--gradient_accumulation_steps=1`, `--use_ema`,
`--learning_rate=1e-4`, `--mixed_precision=no`, and the dataset itself.

`--push_to_hub` is *not* used; publication is a separate, explicit step so that
the upload is its own node in the lineage graph.

## 4. Artifact

```
ddpm-out/model_index.json
ddpm-out/scheduler/scheduler_config.json
ddpm-out/unet/config.json
ddpm-out/unet/diffusion_pytorch_model.safetensors     <- published (455 MB)
```

Published to <https://huggingface.co/reproducible-ai/diffusers-uncond>.

## 5. Rebuild it yourself

```bash
roar reproduce e985e6320cb2b7b4b28cd8ded97b80fc9859824f3a49dc24e00f4deb66afd4d3 \
    --lineage --run --no-puts
```

## Pre-flight check worth copying

Before spending anything, from a **fresh clone** in a scratch virtualenv holding
only the packages above, with `PYTHONPATH` cleared:

```bash
env -u PYTHONPATH sh -c 'PYTHONPATH=src:$PYTHONPATH exec python -c "
import importlib
for m in [\"accelerate\",\"datasets\",\"torch\",\"torchvision\",\"huggingface_hub\",
          \"packaging\",\"tqdm\",\"diffusers\",\"safetensors\",\"trackio\",\"wandb\"]:
    importlib.import_module(m)
from diffusers.utils import check_min_version; check_min_version(\"0.40.0.dev0\")
print(\"ok\")"'
```

This is what caught finding §1 and §2 before any GPU time was bought. It costs
seconds. The full run was then rehearsed end-to-end on CPU at `--resolution=32`
(29 minutes, free) before the paid GPU attempt, which succeeded first try.
