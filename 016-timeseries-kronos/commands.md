# Commands — row 016, Kronos

Everything below was run from a clone of the fork
`github.com/reproducible-ai/Kronos` (default branch **`master`**, matching
upstream — a mismatch here is row-fatal).

## Setup

```sh
gh repo fork shiyu-coder/Kronos --org reproducible-ai --clone=false
git clone https://github.com/reproducible-ai/Kronos.git
cd Kronos

treqs project init --owner reproducible-ai --name "Kronos" --slug kronos \
  --visibility public --default-branch master --code-access-mode public
treqs project status          # -> reproducible-ai/kronos, owner "Reproducible AI"
```

Then `tools/scaffold_row.py` generated `.treqs/workflows/kronos-hk09988-5min.yaml`,
the `.gitignore` rules and the `.gitkeep` files:

```sh
python3 tools/scaffold_row.py \
  --name kronos-hk09988-5min --repo reproducible-ai/Kronos \
  --project reproducible-ai/kronos --hf reproducible-ai/kronos \
  --license-id MIT --license-name "MIT License" \
  --description "Kronos-small (24.7M) fine-tuned on HK 09988 5-minute K-lines: upstream tokenizer + predictor CSV recipe, 1 epoch per stage" \
  --doc-url "https://github.com/reproducible-ai/Kronos/blob/master/finetune_csv/README.md" \
  --tracer preload --roar-version 0.4.4rc6 --roar-python 3.12.10 \
  --step "fetch_pretrained:python repro/fetch_pretrained.py" \
  --step "finetune_tokenizer:..." --step "finetune_predictor:..." \
  --out-dir pretrained --out-dir finetune_csv/finetuned \
  --output finetune_csv/finetuned/HK_ali_09988_kline_5min_all/basemodel/best_model/model.safetensors \
  --dir <clone>
```

Two hand-edits to the generated workflow, both explained in `README.md`:
the setup stage installs roar `0.4.4rc6` from **TestPyPI by version** rather
than from a presigned wheel URL, and asserts the published wheel digest first;
and the two training stages use `env -C finetune_csv` (see below).

## The three recorded steps

```sh
roar run -n fetch_pretrained --wandb-to-trackio -- \
  python repro/fetch_pretrained.py

roar run -n finetune_tokenizer --wandb-to-trackio -- \
  env -C finetune_csv python train_sequential.py \
    --config configs/config_repro_kronos-small_1epoch.yaml --skip-basemodel

roar run -n finetune_predictor --wandb-to-trackio -- \
  env -C finetune_csv python train_sequential.py \
    --config configs/config_repro_kronos-small_1epoch.yaml --skip-tokenizer
```

The two training commands are upstream's own, from `finetune_csv/README.md` §3
"Method 1 (Recommended)", including the `--skip-basemodel` / `--skip-tokenizer`
flags. The only addition is `env -C finetune_csv`, which puts the required
working directory **inside the recorded argv** instead of in an unrecorded `cd`.

## Launch

```sh
treqs run --title "Kronos: fine-tune Kronos-small (24.7M) on 93,912 HK-09988 5-minute K-lines ..." \
  --workflow .treqs/workflows/kronos-hk09988-5min.yaml \
  --target 6cced7e9 --lineage public --source-commit HEAD --follow --yes
```

## Bare-clone check (run BEFORE any GPU spend, on CPU, for $0)

```sh
git clone https://github.com/reproducible-ai/Kronos.git bareclone/Kronos
uv venv --python 3.10 bareclone/venv
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install numpy pandas pyyaml einops huggingface_hub safetensors
# 7 direct packages -> 33 in the resolved closure

cd bareclone/Kronos
env -u PYTHONPATH ../venv/bin/python repro/fetch_pretrained.py
env -u PYTHONPATH ../venv/bin/python finetune_csv/train_sequential.py \
    --config <cpu-probe-config> --skip-basemodel
env -u PYTHONPATH ../venv/bin/python finetune_csv/train_sequential.py \
    --config <cpu-probe-config> --skip-tokenizer
```

All three exit 0, no `ModuleNotFoundError`. The probe config is the real config
with `train_ratio`/`val_ratio` cut to 0.0075, `batch_size` 8 and `use_cuda:
false`, so the whole code path runs in minutes on 4 vCPU.

The same three commands were then replayed **under roar 0.4.4rc6 itself**, with
the full recorded prefix (`roar run -n <name> --wandb-to-trackio -- ...`), not a
trimmed subset. That is what caught the `PYTHONPATH` defect described in
`README.md`.
