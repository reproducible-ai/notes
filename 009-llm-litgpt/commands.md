# 009 — litgpt pretrain · commands

Upstream: `Lightning-AI/litgpt` 0.5.13 (`2685705`), Apache-2.0.
Fork: `reproducible-ai/litgpt`, default branch `main`, reproduction commit
`4375307`. **No litgpt source file was modified** — the fork adds only a
workflow, `.gitignore` rules, four `.gitkeep` files and one additive helper
module (`reproduction/prepare_data.py`).

The pipeline runs as **one** job: four named steps, then label and publish.
Workflow: `.treqs/workflows/litgpt-pretrain.yaml`.

## 0. Setup (untraced)

```bash
export PATH=/opt/pytorch/bin:$PATH
python -m pip install --quiet -e . \
    'huggingface-hub>=0.30,<1.0' 'litdata==0.2.59' 'torchmetrics>=1.3.1' \
    'torch==2.7.0' 'torchvision==0.22.0'
python -m pip uninstall -y -q litgpt
```

Three deliberate deviations from the documented `pip install 'litgpt[extra]'`,
each forced by a real defect (see `issues.md`):

| pin | why |
|---|---|
| `huggingface-hub<1.0` | `litgpt download` raises `AttributeError` on hub >= 1.0, and litgpt's own pin admits it (#1) |
| `torch==2.7.0` + `torchvision==0.22.0` | litgpt pins `litdata==0.2.59`, whose unbounded `torchvision` dep drags an exact `torch==` pin and silently replaces the host PyTorch (#3) |
| `torchmetrics>=1.3.1` | imported unconditionally by `litgpt/pretrain.py` but declared only in the optional `[extra]` group (#2) |

`-e .` followed by `pip uninstall litgpt` installs litgpt's own dependencies
without leaving an editable self-distribution. Every step then runs as
`python -m …` from the repository root, which is path-independent and needs no
installed `litgpt`.

## 1. Tokenizer

```bash
python -m litgpt download EleutherAI/pythia-14m --tokenizer_only true
```

## 2. Data

WikiText-2 as committed in `pytorch/examples` — 10.8 MB train, 1.1 MB
validation. Small on purpose: this row demonstrates the pipeline, not a corpus.

```bash
curl -fsSL --create-dirs \
  -o data_train/wikitext2_train.txt https://raw.githubusercontent.com/pytorch/examples/main/word_language_model/data/wikitext-2/train.txt \
  -o data_val/wikitext2_valid.txt   https://raw.githubusercontent.com/pytorch/examples/main/word_language_model/data/wikitext-2/valid.txt
```

## 3. Tokenize

```bash
python -m reproduction.prepare_data \
  --train_data_path data_train --val_data_path data_val \
  --tokenizer_dir checkpoints/EleutherAI/pythia-14m \
  --micro_batch_size 1 --max_seq_length 128
```

`litgpt pretrain --data TextFiles` would normally do this inline. It is split
out here so the training step runs in a single process (see `issues.md` #7).
The arguments must match the `litgpt pretrain` flags below, because litgpt calls
`data.connect(batch_size=train.micro_batch_size, max_seq_length=model.max_seq_length)`
and the cached chunks are laid out for exactly that block size.
`TextFiles.prepare_data()` is a no-op once the cache dirs exist, so step 4 skips
the tokenization.

## 4. Pretrain (truncated)

```bash
python -m litgpt pretrain pythia-14m \
  --tokenizer_dir checkpoints/EleutherAI/pythia-14m \
  --data TextFiles \
  --data.train_data_path data_train --data.val_data_path data_val \
  --data.num_workers 0 \
  --out_dir out --logger_name csv --devices 1 --seed 42 \
  --train.max_tokens 2048 --train.max_seq_length 128 \
  --train.micro_batch_size 1 --train.global_batch_size 2 \
  --train.lr_warmup_steps 1 --train.log_interval 1 \
  --train.save_interval 1000 --train.max_norm 1.0 \
  --eval.interval 1000 --eval.max_iters 2 --eval.final_validation true
```

`max_tokens 2048` ÷ (`micro_batch_size 1` × `max_seq_length 128`) = 16
iterations = **8 optimizer steps** at `global_batch_size 2`. A truncation, not a
training run: we claim *reproduce*, not *replicate*, so what matters is that the
loss is computed, not what it equals.

Outputs:

- `out/final/lit_model.pth` — the published artifact (169 MB: litgpt checkpoints
  the whole training state, so weights + AdamW moments for a 14 M-param model)
- `out/final/{model_config.yaml,hyperparameters.yaml,tokenizer.json,…}`
- `out/logs/csv/version_0/metrics.csv` — the computed metrics

## Observed values

Identical across three independent CPU runs at seed 42 (working clone, bare
clone, cold rebuild):

```
Epoch 1 | iter  2 step 1 | loss train: 11.000
Epoch 1 | iter 16 step 8 | loss train:  9.914
Final evaluation | val loss: 9.903 | val ppl: 19998.620
```

On the T4 (fp16, `16-mixed` — Turing has no bf16) the same recipe gives
`val loss: 9.738 | val ppl: 16948.362`, reproducibly. Precision, not
nondeterminism.

## Bare-clone check

From a fresh `git clone` of the fork, in a scratch venv containing only the pins
in §0, `PYTHONPATH` unset:

```bash
git clone https://github.com/reproducible-ai/litgpt.git bareclone && cd bareclone
python -m venv ../venv
../venv/bin/python -m pip install -e . 'huggingface-hub>=0.30,<1.0' \
    'litdata==0.2.59' 'torchmetrics>=1.3.1' 'torch==2.7.0' 'torchvision==0.22.0'
../venv/bin/python -m pip uninstall -y litgpt
env -u PYTHONPATH ../venv/bin/python -m litgpt download EleutherAI/pythia-14m --tokenizer_only true
curl -fsSL --create-dirs -o data_train/… -o data_val/…
env -u PYTHONPATH ../venv/bin/python -m litgpt pretrain pythia-14m …
```

Result: every step completed, no `ModuleNotFoundError`; 51 distributions
installed; `import litgpt` fails from outside the repo (no self-install);
`git status` stays clean; all four output directories survive the checkout;
losses matched the working clone exactly. No `wandb`, `trackio` or `mlflow` was
installed — this recipe needs none of them.

## Independent cold rebuild

```bash
roar reproduce 527fac009468d59a05e46973314d831ffba6d04ac582e1fe4728c97364911b84 \
     --lineage --run --no-puts
```

Run on a freshly launched host that had never seen this row. It cloned the fork
at `4375307`, provisioned the recorded Python 3.12 interpreter, installed the
recorded pins, and ran all four steps:

```
Steps run: 4/4          exit code: 0
```

It rebuilt `out/final/lit_model.pth` (168,905,247 B) and `metrics.csv` with
`val loss 9.737926 / val ppl 16948.362` — identical to the capture. All 67
recorded pins were present in the rebuilt environment at the recorded versions,
with no missing or mismatched package.
