# 002 — nanoGPT `shakespeare_char`

**Verdict: REPRODUCED, and certified by cold rebuild.** Zero patches. The
published recipe ran exactly as written, the model it produces lands within
**0.2 %** of the validation loss the README advertises, and a machine that had
never seen this row rebuilt it from the published record alone — regenerating the
129 MB checkpoint **byte for byte**.

> Upstream: [`karpathy/nanoGPT`](https://github.com/karpathy/nanoGPT) ·
> recipe: `data/shakespeare_char/prepare.py` → `train.py config/train_shakespeare_char.py` ·
> fork: [`reproducible-ai/nanoGPT`](https://github.com/reproducible-ai/nanoGPT) @ `0f02dbc` ·
> lineage: [`19171777…`](https://glaas.ai/dag/19171777431d4ad91f91bd7ab64cbc52b706246f815e4d05b0812761a96808d3) ·
> artifact: [`reproducible-ai/nanogpt`](https://huggingface.co/reproducible-ai/nanogpt) ·
> learning curve: [experiments dashboard](https://huggingface.co/spaces/reproducible-ai/experiments?project=nanogpt-shakespeare-char) ·
> AI-BOM **100/100**

## Summary

Two commands, three real dependencies, one 1.1 MB text file, 10.65 M parameters,
under six minutes on one GPU. `prepare.py` downloads the tiny-Shakespeare corpus
and turns it into a character-level token stream; `train.py` trains a 6-layer /
6-head / 384-dim GPT for 5000 iterations and keeps the checkpoint with the best
validation loss. Nothing was patched, nothing was pinned by hand, nothing had to
be worked around. The deviations from the published command line are
`--compile=False` — a flag the README itself documents — and three config keys
that switch on the repository's *own* metric logging.

The best validation loss was **1.4666**, at iteration 1750. The README says "the
best validation loss is 1.4697". Those two numbers were produced on different
GPUs, years apart, and they agree to within 0.2 %.

Better still: **six independent full runs of this recipe, across two weeks and
three GPU models, produced identical evaluation curves** — the same four-decimal
train and validation loss at all 21 eval points — and the capture and its cold
rebuild produced a **byte-identical 129 MB checkpoint** (blake3
`ad112aa2216c7fdb…`). That is not luck. `train.py:106` calls
`torch.manual_seed(1337 + seed_offset)`, and every stochastic element here —
parameter init, the `torch.randint` batch sampler, dropout — draws from that
generator. The campaign only claims *reproduce*, not *replicate*; nanoGPT hands
you *replicate*, down to the byte, for the cost of one line.

`prepare.py`'s output matched its own recorded expectations exactly:
1,115,394 characters, vocabulary of 65, 1,003,854 train tokens, 111,540 val
tokens.

### Evaluation history

Evaluated every 250 iterations, 200 eval batches each. Now also published as a
[live dashboard](https://huggingface.co/spaces/reproducible-ai/experiments?project=nanogpt-shakespeare-char)
(run `shakespeare-char-full-5000`), which the previous version of this row could
not offer — see below.

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
the iteration-1750 model, not the iteration-5000 one. Sustained ~16.9 ms/iter at
~22 % MFU on an L40S.

## Certification — and why this row was re-captured

This row was already published, already certified, and already passing every
completeness check we have. It was re-captured anyway, because **the previous
certification passed for the wrong reason and said so on its own public page.**

That record's package list held 24 pins and did not include `tqdm` or
`typing-extensions`. Both are loaded by `import torch` — one line proves it:

```
$ python -c "import sys, torch; print('tqdm' in sys.modules, 'typing_extensions' in sys.modules)"
True True
```

The rebuild nevertheless succeeded, because each missing package happened to
arrive as a transitive dependency of something that *was* recorded. Worse,
`tqdm`'s only supplier in that environment was `huggingface-hub`, pulled in by
our own experiment-tracking bridge. **The row's greenness depended on our
plumbing being installed** — which is precisely the class of unearned pass this
project exists to criticise.

The re-capture records **57 pins**, with both packages present and the decisive
imports-vs-freeze audit clean (Tier-A missing: 0, was 2). The cold rebuild then:

| | |
|---|---|
| exit code | **0** |
| steps | **2/2** (the 3rd job is the publish step, skipped by `--no-puts`) |
| manifest diff | **57/57 exact** — 0 missing, 0 version-mismatched, 87 distributions installed |
| interpreter | 3.12.10 recorded, 3.12.10 rebuilt, no host packages on `sys.path` |
| `ckpt.pt` | 128,985,500 bytes, blake3 `ad112aa2…` — **identical to the capture's** |

Full evidence, including hashes for every artefact, is in `CERT-TIER2.md`.

**One honest residual.** The recorded 57 pins are still not a *closed* set: install
them alone with `--no-deps` and `import torch` fails — but now on
`libcudnn.so.9`, a native shared library inside the `nvidia-cudnn-cu12` wheel,
which torch loads with `dlopen` rather than `import`. A package record built from
loaded Python modules structurally cannot see it. That is a different and much
smaller problem than a missing Python dependency: `nvidia-cudnn-cu12` is a
declared dependency of `torch==2.7.0`, so any resolver installing the recorded
`torch` pin fetches it automatically. The distinction is worth keeping, because
"the record is a closed set" and "the record rebuilds" are different claims and
only the second is true here.

For contrast, the same `--no-deps` experiment on the old 24-pin record killed
step 1 outright with `ModuleNotFoundError: idna`. Step 1 now runs standalone and
prints all four of its expected dataset statistics.

## The learning curve, and a correction

The previous version of this row shipped with `experimentUrl: null` and a note
explaining that enabling nanoGPT's built-in logging made the recipe harder to
rebuild. **That explanation was wrong, and this row corrects it.**

`train.py:245` imports `wandb` only under the `wandb_log` flag, so switching
logging on does promote `wandb` to a hard runtime dependency. The earlier check
built an environment from the recorded pins, ran the recorded *training script*
against it, and got `ModuleNotFoundError: No module named 'wandb'`. Decisive —
except that what it ran was

```sh
python train.py … --wandb_log=True
```

when what the record actually contains is

```sh
roar run --wandb-to-trackio -- env TRACKIO_SPACE_ID=… python train.py … --wandb_log=True
```

The tracker flag is **part of the recorded command**, not scaffolding around it,
and it installs a `wandb` alias in the child interpreter before `train.py` reaches
the import. Trimming it from the test trimmed a recorded component of the command,
and threw away a valid record on the strength of it.

The corrected result is the certification above: the logging-enabled command ran
to exit 0 on a cold host with nothing installed beyond the record. The dashboard
link is real and was verified by downloading the metrics back out of the remote
store — 21 rows whose losses match the training log line for line — rather than by
checking that a URL returns 200. It returns 200 for any query string, including
ones naming projects that do not exist.

**The boundary that is still real, and is upstream's:** if you rebuild by hand and
type `--wandb_log=True` yourself, you do need a `wandb` the recorded pin list does
not contain. `commands.md` says so. The clean fix is upstream and small — see
issue 6.

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
* **Its configurator is a joke that works.** `configurator.py` is 40 lines that
  `exec` a config file and then `literal_eval` `--key=value` pairs with a type
  assertion. Its own docstring calls it "probably a terrible idea". It is also
  why enabling logging on this row required **zero source changes** — three
  config keys on the command line and nothing else.

Points deducted, and only these: the README's install line is a superset that
still manages to omit `requests` (issue 1); the corpus download is an unpinned
`master`-branch URL (issue 3); `prepare.py` writes generated data into the source
tree with no way to redirect it, which is the one thing that genuinely requires
care when capturing the recipe (issue 2); and the learning curve is discarded
unless you opt into a third-party tracking service (issue 6). All four are
documentation- or ergonomics-level. None of them blocked anything.

**The honest summary is that nanoGPT's reputation is deserved.** If every repo
on the campaign list looked like this, the campaign would not be interesting.

## What was hard, and where

Nothing in the *model* was hard, at any point, across either capture. The recipe
is a one-shot: it worked the first time it was allowed to run, and every
subsequent run reproduced it exactly — six for six now, byte-identically on
matched hardware.

The original record took seven job launches to land, none of them spent on
nanoGPT: three died in the harness that installs capture tooling, two were
bookkeeping, and one was a green run that was deliberately discarded. This
re-capture took **one** launch and one certification host, $0.82 all in, because
everything that could be checked for free on a CPU was checked first — the
tracker shim replayed against nanoGPT's exact `wandb.init` call shape, the full
recorded command run from a fresh clone with `PYTHONPATH` unset, and the
one-line `import torch` audit that justified the whole exercise.

That is the whole point of separating "the model is reproducible" from "we
successfully reproduced it". The first was true from the first run that got as
far as executing it. It would be dishonest to let either attempt count read as a
comment on nanoGPT.

## Deviations from the published recipe

| Deviation | Why |
|---|---|
| `--compile=False` | Documented upstream. Removes a multi-minute, host-specific `torch.compile` warm-up whose payoff on a 10 M-parameter, 5000-iteration run is negligible. |
| `--wandb_log=True` | Switches on logging the repository already implements. The config ships it as `False`. |
| `--wandb_project=nanogpt-shakespeare-char` | Names the dashboard project explicitly instead of relying on any default. |
| `--wandb_run_name=shakespeare-char-full-5000` | Names the run, so the published link resolves to *this* run and not a sibling. |

That is the complete list — four flags, all defined by upstream's own
configurator, altering neither the model, the data, nor a single hyperparameter.
`max_iters` is untouched, so **this row is not truncated**: upstream's config ran
in full at 5000 iterations and the recorded cost is the full-run cost.
`patches/` is empty.

## Reproducing this row

```sh
roar reproduce 19171777431d4ad91f91bd7ab64cbc52b706246f815e4d05b0812761a96808d3 \
    --lineage --run --no-puts
```

Measured: 3 m 21 s on an L40S, including cloning the repository and provisioning
an 87-package virtualenv from scratch. ≈ $0.43 of instance time all in.

Or, without any of our tooling, from the fork:

```sh
git clone https://github.com/reproducible-ai/nanoGPT.git && cd nanoGPT
git checkout 0f02dbcff2d82b7a81d39b016a127b15475601ee
pip install torch numpy requests
python data/shakespeare_char/prepare.py
python train.py config/train_shakespeare_char.py --compile=False
```

Add `wandb` to that install line and `--wandb_log=True` to the train command if
you want the learning curve as well.

Expect a best validation loss of 1.4666 at iteration 1750 — the seed is pinned
upstream, so on comparable hardware you should get that number, not merely one
near it — and `out-shakespeare-char/ckpt.pt` at the end. Expect the loss to keep
improving on train and get worse on validation after that: the config is
deliberately set to overfit, and `always_save_checkpoint = False` means the
artifact you keep is the best one, not the last one.

## Files

* `CERT-TIER2.md` — the cold-rebuild certification, in full
* `issues.md` — every obstacle, with root cause and whether it is upstream-worthy
* `commands.md` — the recipe, the true dependency closure, and the bare-clone check
* `costs.md` — per-attempt spend and what a clean rebuild costs
* `cert-evidence/` — the 57 recorded pins and the 87 the rebuild installed
* `patches/` — empty; no patch was required
* `row.json` — the object published to the /models table
