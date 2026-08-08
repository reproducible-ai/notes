# 007 LeRobot ACT — the recipe

Everything below is the actual command sequence. The three traced steps are the
recipe proper; the rest is setup and publication around them.

## 0. Repository

```
git clone https://github.com/reproducible-ai/lerobot.git      # fork of huggingface/lerobot
cd lerobot
treqs project use reproducible-ai/lerobot-act                 # bind BEFORE running, or the
treqs project status                                          # DAG publishes unattributed
```

Upstream base: `ff7cc3de1de830f5f3276918a013d04bdf9ea4be` (default branch `main`).
Captured at fork commit `b1d01f8c4ce4065915379280a3c50e884670061a`
(re-capture of 2026-08-08; the previous capture was `78c775d1`, same recipe).

## 1. Environment (untraced setup stage)

The order here is load-bearing; see `issues.md` §1.

```
export PATH=/opt/pytorch/bin:$PATH

# upstream's own declared dependency set, via its `training` extra
python -m pip install --constraint repro/constraints.txt -e ".[training]"

# then drop the self-install: an editable install registers the whole repository
# as package territory and the tracer stops recording reads under it
python -m pip uninstall -y lerobot

# ...and sweep what the uninstall leaves behind, or the framework reads back as
# an installed distribution from inside any process with src/ on sys.path
rm -rf ./*.egg-info src/*.egg-info

# gate the environment before anything is paid for
python repro/freeze_audit.py            # no `+cuNNN` local versions, no PEP-503 duplicates

# assert the trap is actually defused, WITH src/ on the path
python -c "import os,sys; sys.path.insert(0, os.path.abspath('src')); \
  import importlib.metadata as m; \
  d=[x.metadata['Name'] for x in m.distributions() if (x.metadata['Name'] or '').lower()=='lerobot']; \
  print('lerobot distributions visible to importlib.metadata:', d); sys.exit(1 if d else 0)"
```

`repro/constraints.txt` pins `torch==2.7.0`, `torchvision==0.22.0`,
`torchcodec==0.4.0` — versions LeRobot's own ranges already allow. The point is to
stop a future resolver from substituting a CUDA-index build carrying a `+cuNNN` local
version, which is absent from PyPI and would make the recorded environment
un-installable for everyone else.

## 2. The three recorded steps

```
# fetch — the public dataset, resolved anonymously (token=False)
python repro/fetch_dataset.py --repo-id lerobot/pusht_image --out-dir data/pusht_image

# train — upstream's own lerobot_train.main(), upstream's own arguments
python repro/train_act.py \
    --dataset.repo_id=lerobot/pusht_image --dataset.root=data/pusht_image \
    --dataset.eval_split=0.1 \
    --policy.type=act --policy.device=cuda --policy.push_to_hub=false \
    --steps=300 --batch_size=8 --num_workers=0 \
    --log_freq=25 --eval_steps=150 --env_eval_freq=0 --save_freq=-1 \
    --seed=1000 --output_dir=outputs/act_pusht --job_name=act_pusht_truncated

# evaluate — recompute the held-out metric from the saved checkpoint
python repro/evaluate_act.py \
    --checkpoint outputs/act_pusht/checkpoints/000300/pretrained_model \
    --repo-id lerobot/pusht_image --root data/pusht_image \
    --eval-split 0.1 --batch-size 8 --device cuda --out metrics/metrics.json
```

Why `python repro/<script>.py` rather than `lerobot-train`: the console script is
created by `pip install`, and the install happens in the untraced setup stage, so it
does not exist on a rebuild host. `PYTHONPATH=src python -m lerobot.scripts.lerobot_train`
would depend on an environment variable set *outside* the recorded command, which is
silently dropped from the record. The launchers do the `sys.path` insert in committed
code and call upstream's `main()` unchanged — nothing under `src/` is modified.

Why `--num_workers=0`: with DataLoader workers the traced step's recorded package set
collapses to the tracer's own closure instead of the workload's. Single-process
loading costs seconds on a 31 MB dataset and keeps the record complete.

Why `--policy.push_to_hub=false`: `PreTrainedConfig.push_to_hub` defaults to **`True`**
(`src/lerobot/configs/policies.py:70`), so every checkpoint save goes through
`HubMixin.save_pretrained(push_to_hub=True, repo_id=...)` and tries to upload to the
Hub mid-training. Publication here is a separate, explicit step, so the training run
must not push on its own.

## 3. Label and publish

```
roar label set artifact outputs/act_pusht/checkpoints/000300/pretrained_model/model.safetensors \
    model.name=lerobot-act-pusht model.version=1 \
    license.id=Apache-2.0 license.name='Apache License 2.0' \
    description='LeRobot ACT (Action Chunking Transformer, ResNet-18 backbone) trained on the public lerobot/pusht_image LeRobotDataset. TRUNCATED pipeline-viability run: 300 of the 100000 default training steps, NOT converged.' \
    documentation.url=https://github.com/huggingface/lerobot/blob/main/docs/source/act.mdx

roar put outputs/act_pusht/checkpoints/000300/pretrained_model/model.safetensors \
    hf://reproducible-ai/lerobot-act --public --yes --no-tag \
    -m "ACT policy ... 300 of the 100000 default training steps, batch size 8. TRUNCATED pipeline-viability run, NOT converged and not a quality result."
```

## 4. Launch

```
treqs run \
  --title "lerobot: train an ACT policy (Action Chunking Transformer, ResNet-18 backbone) on the public lerobot/pusht_image dataset — 300 steps, batch 8, truncated — producing model.safetensors and a held-out eval loss" \
  --workflow .treqs/workflows/lerobot-act-pusht.yaml \
  --target <gpu-target> --lineage public --source-commit HEAD --follow --yes
```

## 5. Rebuild

```
roar reproduce cc490321bbbf07fd270c8bd83d12967de0fb891d1265994c5cca134df57f0639 \
    --lineage --run --no-puts
```

## Observed output

```
fetch_dataset : codebase_version=v3.0 episodes=206 frames=25650 tasks=1 fps=10
                total bytes: 31621889   (7 files)
train         : num_learnable_params=51588994 (52M), effective batch size 8
                step:300 smpl:2K ep:19 epch:0.10 loss:2.976 grdn:93.317 lr:1.0e-05
                       l1_loss:0.559 kld_loss:0.242 mem_gb:0.95 smp/s:30
                step 150: eval_loss=0.5662
                step 300: eval_loss=0.5276
                → outputs/act_pusht/checkpoints/000300/pretrained_model/model.safetensors
evaluate      : held-out episodes: 21 of 206 (per-task, 1 task)
                held-out frames: 2742 · eval_batches: 343
                eval_loss = 0.5275466817026583
                action_l1 = 52.59283304075458
```

`eval_loss` from the standalone evaluation matches training's own step-300 number to
four decimal places (0.5362), which is the check that `repro/evaluate_act.py` really
does mirror upstream's eval branch rather than measuring something else.
