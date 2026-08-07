# Commands — nanoGPT `shakespeare_char`

The recipe is two commands, exactly as published in the upstream README's
"quick start" section. Nothing was added to them.

## The published recipe

```sh
# 1. build the character-level dataset (downloads the 1.1 MB tiny-Shakespeare
#    corpus, writes train.bin / val.bin / meta.pkl next to prepare.py)
python data/shakespeare_char/prepare.py

# 2. train to convergence — 5000 iters, batch 64, block 256, 6L/6H/384d
python train.py config/train_shakespeare_char.py
```

Upstream also documents `--compile=False` (README, "I only have a macbook"). We
pass it on the GPU run as well; see `issues.md` issue 4 for why.

```sh
python train.py config/train_shakespeare_char.py --compile=False
```

We additionally pass `--wandb_log=True`, which turns on the wandb instrumentation
`train.py` already contains (it logs iteration, train loss, val loss, learning
rate and MFU) and which this config ships switched off. It changes nothing about
what is trained; see `issues.md` issue 6.

Those two flags are the **complete** list of deviations from the published
command line, and upstream defines both.

## Dependencies actually required

The README's install line is a superset:

```sh
pip install torch numpy transformers datasets tiktoken wandb tqdm
```

For `shakespeare_char` specifically, the true closure is much smaller —
established by running the recipe in an empty virtualenv (see below):

| Package | Needed by | Notes |
|---|---|---|
| `numpy` | `prepare.py`, `train.py` | works on numpy 2.x |
| `requests` | `prepare.py` | corpus download only |
| `torch` | `train.py`, `model.py` | 2.7.0 used here |

`transformers` is imported only inside `GPT.from_pretrained` (loading OpenAI
GPT-2 weights) and is never reached when training from scratch. `tiktoken` is
only used by the GPT-2 BPE `data/shakespeare` recipe and by `sample.py --start=FILE`.
`datasets` is only for OpenWebText. `tqdm` is only used by the OpenWebText
prepare script. `wandb` is imported only when `wandb_log=True`, which the
`shakespeare_char` config ships as `False`.

## Bare-clone verification (run before spending anything)

Fresh clone, a virtualenv containing only the three packages above, `PYTHONPATH`
unset:

```sh
git clone --depth 1 https://github.com/reproducible-ai/nanoGPT.git repo
uv venv --python 3.10 venv
uv pip install --python venv/bin/python torch==2.7.0 numpy requests \
    --index-url https://download.pytorch.org/whl/cpu \
    --extra-index-url https://pypi.org/simple
cd repo
env -u PYTHONPATH venv/bin/python data/shakespeare_char/prepare.py
env -u PYTHONPATH venv/bin/python train.py config/train_shakespeare_char.py \
    --compile=False --device=cpu --max_iters=2 --eval_iters=2 --eval_interval=2 \
    --block_size=64 --batch_size=4 --n_layer=2 --n_head=2 --n_embd=64
```

Both complete with no `ModuleNotFoundError`; `out-shakespeare-char/ckpt.pt` is
written. Output of the first: `vocab size: 65`, `train has 1,003,854 tokens`,
`val has 111,540 tokens` — matching the values `prepare.py` records in its own
trailing comment, which is a nice built-in self-check.

## Provenance-captured form

The two steps above were run as one two-stage traced pipeline. The stage
commands are byte-identical to the recipe; the only wrapper is the tracer:

```sh
roar run -n prepare -- python data/shakespeare_char/prepare.py
roar run -n train   -- python train.py config/train_shakespeare_char.py --compile=False --wandb_log=True
```

Both output directories are declared, so `prepare`'s `train.bin` / `val.bin` /
`meta.pkl` are recorded as artifacts and chain into `train` as inputs rather
than appearing as unsourced files. That chaining is the whole reason the recipe
is two steps and not one.

## Reproducing this row

```sh
roar reproduce 8da40ae10248123746605dc8c1e5a1ca6ce4677544bec7f6d3fc4df7c582eab6 \
    --lineage --run --no-puts
```
