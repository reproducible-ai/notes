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

## What this row actually ran

```sh
python data/shakespeare_char/prepare.py

python train.py config/train_shakespeare_char.py --compile=False \
    --wandb_log=True \
    --wandb_project=nanogpt-shakespeare-char \
    --wandb_run_name=shakespeare-char-full-5000
```

Four config overrides, **zero source changes**, all of them keys upstream's own
`configurator.py` already accepts:

| Override | Why |
|---|---|
| `--compile=False` | documented upstream; drops a host-specific `torch.compile` warm-up |
| `--wandb_log=True` | switches on the repo's own metric logging, which the config ships as `False` (issue 6) |
| `--wandb_project=…` | names the dashboard project; also avoids relying on any inference of a default |
| `--wandb_run_name=…` | names the run, so the published link resolves to *this* run and not a sibling |

`max_iters` is untouched, so upstream's config runs in full at **5000 iterations**.
**This row is not truncated** — the recorded cost is the full-run cost.

An earlier version of this row deliberately left `--wandb_log` off, on the belief
that it made the recipe un-rebuildable. That belief was tested and is wrong; the
correction, and the reasoning error behind it, are in `issues.md` issue 6.

## Dependencies actually required

The README's install line is a superset:

```sh
pip install torch numpy transformers datasets tiktoken wandb tqdm
```

For `shakespeare_char` specifically, the true closure of the *published* recipe is
much smaller — established by running it in an empty virtualenv (see below):

| Package | Needed by | Notes |
|---|---|---|
| `numpy` | `prepare.py`, `train.py` | works on numpy 2.x |
| `requests` | `prepare.py` | corpus download only |
| `torch` | `train.py`, `model.py` | 2.7.0 used here |

`transformers` is imported only inside `GPT.from_pretrained` (loading OpenAI
GPT-2 weights) and is never reached when training from scratch. `tiktoken` is
only used by the GPT-2 BPE `data/shakespeare` recipe and by `sample.py --start=FILE`.
`datasets` is only for OpenWebText. `tqdm` is only used by the OpenWebText
prepare script — though note it arrives anyway, because `import torch` loads it.

⚠️ **`--wandb_log=True` adds one more.** `train.py:245` imports `wandb` only under
the flag. In this row's capture that import is satisfied by the tracker's
`wandb → trackio` alias, so the recorded package list pins `trackio` and not
`wandb`. **If you rebuild by hand and want the dashboard, `pip install wandb` (or
`trackio`) as well.** If you just want the model, leave `--wandb_log` off and the
three-package closure above is complete.

## Bare-clone verification (run before spending anything)

Fresh clone, `PYTHONPATH` unset, a virtualenv containing only the packages the
record is expected to carry. Both halves were run on CPU, for $0, before any GPU
was booked.

**Step 1 — the published recipe, three packages:**

```sh
git clone https://github.com/reproducible-ai/nanoGPT.git bareclone
uv venv --python 3.12 venv
uv pip install --python venv/bin/python numpy requests
cd bareclone
env -u PYTHONPATH ../venv/bin/python data/shakespeare_char/prepare.py
```

Exit 0. Output: `vocab size: 65`, `train has 1,003,854 tokens`, `val has 111,540
tokens` — matching the values `prepare.py` records in its own trailing comment,
which is a nice built-in self-check. `train.bin` came out at 2,007,708 bytes,
the same size the record carries.

**Step 2 — the *full recorded command*, including the logging path:**

```sh
uv pip install --python venv/bin/python torch trackio \
    --index-url https://download.pytorch.org/whl/cpu
env -u PYTHONPATH roar run -n train --wandb-to-trackio -- \
    env TRACKIO_SPACE_ID=reproducible-ai/experiments \
    python train.py config/train_shakespeare_char.py --compile=False \
      --wandb_log=True --wandb_project=probe-002-bareclone \
      --device=cpu --max_iters=20 --eval_interval=10 --eval_iters=2
```

Exit 0 in 235 s on CPU. `[wandb->trackio] active` printed, three eval points
logged, `out-shakespeare-char/ckpt.pt` written. Running the *whole* recorded
command — tracker flags included — rather than just `python train.py …` is the
part that matters: see `issues.md` issue 6 for what happens when you trim it.

A third, cheaper check settled the question this row exists to answer, and is
worth copying: in that same isolated venv,

```sh
python -c "import sys, torch; print('tqdm' in sys.modules, 'typing_extensions' in sys.modules)"
# True True
```

`import torch` really does load both, so both belong in any honest package
record for this recipe. The superseded record was missing them.

## Provenance-captured form

The two steps above were run as one two-stage traced pipeline. The stage
commands are byte-identical to the recipe; the only wrapper is the tracer:

```sh
roar run -n prepare-shakespeare-char-data -- \
    python data/shakespeare_char/prepare.py

roar run -n train-shakespeare-char-gpt --wandb-to-trackio -- \
    env TRACKIO_SPACE_ID=reproducible-ai/experiments PYTHONUNBUFFERED=1 \
    python train.py config/train_shakespeare_char.py --compile=False \
      --wandb_log=True --wandb_project=nanogpt-shakespeare-char \
      --wandb_run_name=shakespeare-char-full-5000
```

Both output directories are declared, so `prepare`'s `train.bin` / `val.bin` /
`meta.pkl` are recorded as artifacts and chain into `train` as inputs rather
than appearing as unsourced files. That chaining is the whole reason the recipe
is two steps and not one.

Note the `env VAR=… ` **inside** the traced command rather than an `export`
above it. The tracker records argv and nothing else, so a variable exported
around the command is simply absent from the record; putting it in argv makes it
travel. `env` is `exec`, not a shell, so the traced process tree is unchanged.

## Reproducing this row

```sh
roar reproduce 19171777431d4ad91f91bd7ab64cbc52b706246f815e4d05b0812761a96808d3 \
    --lineage --run --no-puts
```

Certified: this exact command, on a host that had never seen the row, exits 0 at
2/2 steps and regenerates `ckpt.pt` byte for byte. See `CERT-TIER2.md`.

Or, without any of our tooling, from the fork:

```sh
git clone https://github.com/reproducible-ai/nanoGPT.git && cd nanoGPT
git checkout 0f02dbcff2d82b7a81d39b016a127b15475601ee
pip install torch numpy requests
python data/shakespeare_char/prepare.py
python train.py config/train_shakespeare_char.py --compile=False
```

(Note the absence of `--wandb_log=True` in the hand-rolled form — add `wandb` or
`trackio` to the `pip install` line if you want it.)

Expect a best validation loss of **1.4666 at iteration 1750** — the seed is
pinned upstream, so on comparable hardware you should get that number, not
merely one near it — and `out-shakespeare-char/ckpt.pt` at the end. Expect the
loss to keep improving on train and get worse on validation after that: the
config is deliberately set to overfit, and `always_save_checkpoint = False` means
the artifact you keep is the best one, not the last one.
