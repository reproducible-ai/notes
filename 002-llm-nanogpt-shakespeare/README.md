# 002 — nanoGPT `shakespeare_char`

**Verdict: REPRODUCED.** Zero patches. The published recipe ran exactly as
written, and the model it produces lands within **0.2 %** of the validation loss
the README advertises.

> Upstream: [`karpathy/nanoGPT`](https://github.com/karpathy/nanoGPT) ·
> recipe: `data/shakespeare_char/prepare.py` → `train.py config/train_shakespeare_char.py` ·
> fork: [`reproducible-ai/nanoGPT`](https://github.com/reproducible-ai/nanoGPT) @ `f4ed2cc` ·
> lineage: [`72ad9675…`](https://glaas.ai/dag/72ad9675f624563a018c0e76f81fea418edb268ab19002c404a793721f86fde2) ·
> artifact: [`reproducible-ai/nanogpt`](https://huggingface.co/reproducible-ai/nanogpt) ·
> AI-BOM **100/100**

## Summary

Two commands, three real dependencies, one 1.1 MB text file, 10.65 M parameters,
two and a half minutes on one GPU. `prepare.py` downloads the tiny-Shakespeare
corpus and turns it into a character-level token stream; `train.py` trains a
6-layer / 6-head / 384-dim GPT for 5000 iterations and keeps the checkpoint with
the best validation loss. Nothing was patched, nothing was pinned by hand,
nothing had to be worked around. The single deviation from the published command
line is `--compile=False`, a flag the README itself documents.

The best validation loss was **1.4666**, at iteration 1750. The README says
"the best validation loss is 1.4697". Those two numbers were produced on
different GPUs, years apart, and they agree to within 0.2%.

Better still: **four independent full runs of this recipe, launched separately
over the course of an afternoon, produced identical evaluation curves** — the
same four-decimal train and validation loss at all 21 eval points — and three of
them produced a **byte-identical 129 MB checkpoint** (blake3
`f4cc9b6ebb52a7f8…`). That is not luck. `train.py:106` calls
`torch.manual_seed(1337 + seed_offset)`, and every stochastic element here —
parameter init, the `torch.randint` batch sampler, dropout — draws from that
generator. The campaign only claims *reproduce*, not *replicate*; nanoGPT hands
you *replicate*, down to the byte, for the cost of one line. (The fourth run
differed only because it was the logging-enabled variant, which writes an extra
key into the checkpoint's embedded config — the weights matched.)

`prepare.py`'s output matched its own recorded expectations exactly:
1,115,394 characters, vocabulary of 65, 1,003,854 train tokens, 111,540 val
tokens.

### Evaluation history

Recorded here because the recipe persists nothing to disk (issue 6). Evaluated
every 250 iterations, 200 eval batches each:

| iter | train loss | val loss | | iter | train loss | val loss |
|---:|---:|---:|---|---:|---:|---:|
| 0 | 4.2874 | 4.2823 | | 2750 | 0.9121 | 1.5269 |
| 250 | 1.9652 | 2.0657 | | 3000 | 0.8653 | 1.5415 |
| 500 | 1.5290 | 1.7455 | | 3250 | 0.8209 | 1.5774 |
| 750 | 1.3648 | 1.5960 | | 3500 | 0.7790 | 1.5839 |
| 1000 | 1.2700 | 1.5243 | | 3750 | 0.7436 | 1.6129 |
| 1250 | 1.2036 | 1.4955 | | 4000 | 0.7085 | 1.6343 |
| 1500 | 1.1525 | 1.4842 | | 4250 | 0.6785 | 1.6606 |
| **1750** | **1.1015** | **1.4666** ← best | | 4500 | 0.6527 | 1.6773 |
| 2000 | 1.0559 | 1.4782 | | 4750 | 0.6375 | 1.6931 |
| 2250 | 1.0078 | 1.4846 | | 5000 | 0.6221 | 1.7146 |
| 2500 | 0.9604 | 1.4998 | | | | |

Validation loss bottoms out at iteration 1750 and rises monotonically thereafter
while train loss keeps falling — textbook overfitting, and entirely intended:
the config sets `dropout = 0.2` and comments "we expect to overfit on this small
dataset, so only save when val improves". The published checkpoint is therefore
the iteration-1750 model, not the iteration-5000 one. Sustained ~17 ms/iter at
~22 % MFU.

## Difficulty: 2 / 10 — Easy

This is the low-water mark for the campaign so far, and it is worth being
precise about *why*, because "it just worked" is not a finding.

* **The recipe is complete.** Data acquisition, preprocessing, hyperparameters,
  model definition and training loop are all in the repository, all reachable
  from two commands in the README. Nothing is behind a login, a paper appendix,
  or a "contact the authors".
* **The dependency closure is three packages.** `torch`, `numpy`, `requests`.
  A small closure is not a stylistic virtue — it is why the environment resolved
  on the first try, and why there was no version conflict to negotiate.
* **It is not a package.** There is no `setup.py`, no `pip install -e .`, no
  entry points. `train.py` imports `model` as a sibling file. Every path the
  recipe touches is a real file in the repository.
* **It self-checks.** `prepare.py` records the four numbers it should print;
  the README records the validation loss it should reach. Neither is *enforced*,
  but both make drift immediately visible, and both held.
* **It is honest about scale.** 5000 iterations on a 1 MB corpus. There is no
  hidden cluster, no undisclosed pretraining, no "we also trained on X".

Points deducted, and only these: the README's install line is a superset that
still manages to omit `requests` (issue 1); the corpus download is an unpinned
`master`-branch URL (issue 3); and `prepare.py` writes generated data into the
source tree with no way to redirect it, which is the one thing that genuinely
requires care when capturing the recipe (issue 2). All three are documentation-
or ergonomics-level. None of them blocked anything.

**The honest summary is that nanoGPT's reputation is deserved.** If every repo
on the campaign list looked like this, the campaign would not be interesting.

## What was hard, and where

Nothing in the *model* was hard. The recipe itself is a one-shot: it worked the
first time it was allowed to run, and every subsequent run reproduced it exactly.

Seven job launches were needed to land the published record, and none of what
consumed them was nanoGPT. Three failed in the machinery that installs capture
tooling onto the compute image. One re-ran with experiment logging enabled,
passed every completeness check, and was then **rejected**, because a
from-scratch rebuild check showed its recorded command needed a package its
recorded environment did not contain. Two more were bookkeeping, reconciling the
published artifact with the recorded commit after that reversal. The recipe
itself succeeded on every launch that reached it — four for four, identically.

That is the whole point of separating "the model is reproducible" from "we
successfully reproduced it": the first was true from the first run that got as
far as executing it; the second took seven attempts, for reasons entirely
outside the repository. It would be dishonest to let this row's attempt count
read as a comment on nanoGPT.

The genuinely instructive episode was the experiment-logging decision, which I
got wrong twice in opposite directions before a rebuild check settled it. It is
the most transferable thing in these notes: see **issue 6** in `issues.md`.

## Deviations from the published recipe

| Deviation | Why |
|---|---|
| `--compile=False` added to the train command | Documented upstream. Removes a multi-minute, host-specific `torch.compile` warm-up whose payoff on a 10 M-parameter, 5000-iteration run is negligible. Model, data and hyperparameters untouched. |

That is the complete list — one flag, already defined by upstream, altering
neither the model, the data, nor a single hyperparameter. `patches/` is empty.

We also *tried* `--wandb_log=True`, to record the learning curve via the repo's
own instrumentation, and then backed it out. Issue 6 explains why in detail; the
short version is that the flag makes `wandb` a hard runtime import, and a
rebuild from this row's recorded environment does not have it. A row that only
rebuilds under one particular toolchain is not the row we want to publish.

## Reproducing this row

```sh
roar reproduce 72ad9675f624563a018c0e76f81fea418edb268ab19002c404a793721f86fde2 \
    --lineage --run --no-puts
```

Or, without any of our tooling, from the fork:

```sh
git clone https://github.com/reproducible-ai/nanoGPT.git && cd nanoGPT
git checkout f4ed2cc871ec4462816cdd1a61ec8083575934ed
pip install torch numpy requests
python data/shakespeare_char/prepare.py
python train.py config/train_shakespeare_char.py --compile=False
```

Expect a best validation loss of 1.4666 at iteration 1750 — the seed is pinned
upstream, so on comparable hardware you should get that number, not merely one
near it — and `out-shakespeare-char/ckpt.pt` at the end. Expect the loss to keep improving on
train and get worse on validation after that — the config is deliberately set to
overfit, and `always_save_checkpoint = False` means the artifact you keep is the
best one, not the last one.

## Files

* `issues.md` — every obstacle, with root cause and whether it is upstream-worthy
* `commands.md` — the recipe, the true dependency closure, and the bare-clone check
* `costs.md` — per-attempt spend and what a clean rebuild costs
* `patches/` — empty; no patch was required
* `row.json` — the object published to the /models table
