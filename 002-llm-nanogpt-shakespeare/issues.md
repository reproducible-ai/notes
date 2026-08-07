# Issues — nanoGPT `shakespeare_char`

Obstacles hit while rebuilding the published `shakespeare_char` recipe from
`karpathy/nanoGPT`, in the order they were met. Findings here are about the
**upstream repository and its published materials** only.

---

## 1. The install line is a superset of what the recipe needs

**Symptom.** The README's single install instruction is

```
pip install torch numpy transformers datasets tiktoken wandb tqdm
```

Four of those seven packages are not reachable by the `shakespeare_char` recipe
at all.

**Root cause.** The README has one install line for a repo that contains four
independent data recipes (`shakespeare_char`, `shakespeare`, `openwebget`,
plus GPT-2 finetuning) and a sampling script. The union of their dependencies is
presented as the dependency list for all of them.

* `transformers` — imported only inside `GPT.from_pretrained` (`model.py:212`),
  reached only when loading OpenAI GPT-2 weights.
* `datasets`, `tqdm` — only `data/openwebtext/prepare.py`.
* `tiktoken` — only the BPE `data/shakespeare` recipe and `sample.py --start=FILE`.
* `wandb` — only when `wandb_log=True`, which this config ships as `False`.

**Verified closure** for prepare + train: `torch`, `numpy`, `requests`. Note
that `requests` is used by `data/shakespeare_char/prepare.py` and is **not in
the README's install line at all** — so following the README literally and then
running the very first quick-start command fails with
`ModuleNotFoundError: No module named 'requests'` on a clean machine. In
practice `requests` is nearly always already present as a transitive dependency,
which is exactly why the omission has survived.

**Impact.** Low for a human, real for an automated rebuild: the published
dependency list is simultaneously too big (four unreachable packages, one of
which — `datasets` — drags in a large tree) and too small (missing `requests`).

**Upstream-worthy?** Yes, and it is a two-line change: add `requests` to the
install line, and split the "everything" list from a per-recipe minimum. A
`requirements.txt` next to each `data/<recipe>/prepare.py` would be cleaner
still. Not filed — campaign policy is no external contact.

**Fix applied here.** None to the repo. The captured environment simply contains
the real closure.

---

## 2. `prepare.py` writes its outputs into the source tree

**Symptom.** `data/shakespeare_char/prepare.py` writes `input.txt`, `train.bin`,
`val.bin` and `meta.pkl` **next to itself**, inside the cloned repository, using
`os.path.dirname(__file__)`. There is no `--out-dir`, no env var, no argument —
the destination is not configurable.

**Root cause.** Deliberate simplicity: `train.py` later resolves its data as
`os.path.join('data', dataset)`, so both sides hard-code the same in-tree path.

**Impact.** Two concrete consequences for anyone capturing this recipe:

1. **The data directory is an output directory.** It is easy to see
   `out-shakespeare-char/` as *the* output of this recipe and miss that
   `data/shakespeare_char/` is one too. Any tooling that is told about only the
   checkpoint directory will silently lose the dataset half of the lineage —
   `train.bin`/`val.bin`/`meta.pkl` then look like files that just happened to
   be lying around rather than artifacts the first step produced, and the
   prepare→train chain does not connect.
2. **Generated data is indistinguishable from source by path.** The repo's
   `.gitignore` handles this with blanket `*.bin`, `*.pkl`, `input.txt` rules,
   which works but is coarse — it ignores those extensions everywhere in the
   tree, not just under `data/`.

**Fix applied here.** Both `out-shakespeare-char/` and `data/shakespeare_char/`
were declared as output directories, so prepare's three files are recorded as
artifacts and appear as inputs to train. No repo change.

**Upstream-worthy?** Marginal. An optional `--out-dir` on the prepare scripts
(defaulting to today's behaviour) would help, but the in-tree convention is
load-bearing for how simple `train.py` stays, which is the repo's whole point.

---

## 3. The corpus download is unpinned and conditional

**Symptom.** `prepare.py` fetches the corpus from

```
https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt
```

— a `master` branch URL, with no commit pin, no checksum, and no recorded
content length. It is also fetched only `if not os.path.exists(input_file_path)`,
so a stale or hand-edited `input.txt` in the tree is used silently and forever.

**Root cause.** A 2015-era companion repo used as a CDN.

**Mitigating factor, and it is a good one.** `prepare.py` ends with a comment
block recording the expected values:

```
# length of dataset in characters:  1115394
# vocab size: 65
# train has 1,003,854 tokens
# val has 111,540 tokens
```

Those are printed by every run, so a drifted corpus is loudly visible even
though nothing enforces it. Our run reproduced all four numbers exactly, which
is the strongest single piece of evidence that the data half of this recipe is
intact. It is worth naming this as a *good* practice: four printed integers cost
nothing and turn an unpinned download into a checkable one.

**Impact.** Low today, unbounded later — `karpathy/char-rnn` is archived but a
branch URL is still a moving target, and if it ever 404s the recipe's first
command breaks with a network error rather than a clear message.

**Upstream-worthy?** Yes — asserting the four values instead of commenting them,
or publishing a sha256, would close it. A one-line `assert len(data) == 1115394`
would be enough.

---

## 4. `torch.compile` is on by default with no documented GPU opt-out

**Symptom.** `train.py` defaults `compile = True`. The README documents
`--compile=False` only in the "I only have a macbook" (CPU) section, so on the
GPU path the flag reads as CPU-specific advice.

**Impact.** `torch.compile` adds a multi-minute, machine-specific warm-up whose
generated kernels depend on the exact GPU, driver and Triton version. For a
*reproduction* that is pure variance with no benefit — the recipe is 5000 iters
of a 10.7M-parameter model, so compile's payback is small in absolute terms.

**Fix applied here.** We pass `--compile=False`. This is the only deviation from
the published command line and it uses a flag the README itself documents. The
model, data, hyperparameters and iteration count are untouched.

**Upstream-worthy?** Documentation only: note in the GPU section that
`--compile=False` is a supported way to trade a little throughput for a much
shorter time-to-first-step.

---

## 5. Minor: a deprecated torch API warns on every run

**Symptom.**

```
train.py:196: FutureWarning: `torch.cuda.amp.GradScaler(args...)` is deprecated.
Please use `torch.amp.GradScaler('cuda', args...)` instead.
```

**Impact.** Cosmetic on torch 2.7.0. It is a one-line change and it will become
an error whenever the shim is removed.

**Upstream-worthy?** Yes, trivially. Not filed (no external contact).

---

## 6. Experiment logging ships present but switched off, and opting in costs more than it looks

**Symptom.** `train.py` has first-class Weights & Biases support —
`wandb_log` / `wandb_project` / `wandb_run_name` config keys, a `wandb.init`,
and a `wandb.log` of iteration, train loss, val loss, learning rate and MFU. The
`shakespeare_char` config ships it as `wandb_log = False`. So the published
recipe, run exactly as published, produces **no machine-readable record of the
metrics it computes** — only stdout.

**Root cause.** A sensible default: logging on by default would demand a W&B
account and an interactive login for the repo's own quick-start, which would be
a terrible first experience. The cost is that the recipe's *only* durable output
is the checkpoint; the learning curve that justifies it is thrown away.

**Impact, and the decision this forced.** A reproduction wants the metrics
recorded, so enabling `--wandb_log=True` is tempting. Two things make it a worse
trade than it appears:

1. **It is not a free flag.** Turning it on introduces `wandb` as a hard
   requirement of the recipe (it is imported only under that branch), which
   grows a three-package closure into a large one, and it requires an account
   and credentials that a third-party reproducer will not have. A recipe that
   needs a login is less reproducible, not more.
2. **Silence is the failure mode.** Any wandb-compatible shim that cannot reach
   a backend will satisfy `import wandb`, accept every `log()` call, and let the
   run finish green with nothing recorded anywhere. We verified this on CPU
   before spending anything: the training run completes, exit code 0, and no
   metrics exist. There is no error to notice. Had we flipped the flag on faith
   and only checked the exit code, we would have shipped a run that looked
   logged and was not.

**Fix applied here.** We ran the recipe with logging at its shipped default —
off — and treat that as the honest reproduction of what is published. Metrics
are recorded in this row as the training log (see the loss table in `README.md`
and `costs.md`); every metric the recipe computes was computed. We did **not**
bolt on logging the recipe does not enable.

**Upstream-worthy?** A genuine improvement exists and is small: write the eval
history to a CSV or JSONL in `out_dir` unconditionally, independent of wandb.
`train.py` already has every value in hand at the eval step. That would give
every reproducer a durable learning curve with no account, no credentials and no
new dependency — and it would make "did this rebuild match?" answerable from the
artifact alone rather than from scrollback. Of everything in this file, this is
the change I would most want upstream.

---

## What did *not* go wrong

Worth recording, because the campaign's usual failure modes were all absent:

* **No patch was needed.** The repo ran as published. `patches/` is empty.
* **No editable install.** nanoGPT has no `setup.py`/`pyproject.toml` and is not
  a package; `train.py` imports `model` as a sibling module, so running from the
  repo root is all that is required. Nothing shadows or blinds file-level tracing.
* **No pinning conflicts.** The dependency closure is three packages wide.
* **Deterministic-enough.** No seed is set anywhere in `train.py`, so loss values
  differ run to run; the campaign claims *reproduce*, not *replicate*, and every
  metric the recipe computes (train loss, val loss, MFU) was computed. The
  checkpoint-on-val-improvement logic (`always_save_checkpoint = False`) means
  the published artifact is the best-val checkpoint, not the last one — which is
  a nice property for a reproduction, since it is defined by a criterion rather
  than by where you stopped.
* **The recipe is honest about its scale.** 5000 iters, ~10.7M parameters, a
  1.1 MB corpus. Nothing is hidden behind a cluster.
