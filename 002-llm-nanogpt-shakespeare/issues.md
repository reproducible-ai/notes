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

## 6. Turning on the built-in experiment logging makes the recipe harder to rebuild

**Symptom.** `train.py` has first-class Weights & Biases support —
`wandb_log` / `wandb_project` / `wandb_run_name` config keys, a `wandb.init`,
and a `wandb.log` of iteration, train loss, val loss, learning rate and MFU. The
`shakespeare_char` config ships it as `wandb_log = False`. So the published
recipe, run exactly as published, produces **no machine-readable record of the
metrics it computes** — only stdout, which is thrown away.

**Root cause.** A sensible default: logging on by default would demand an account
and an interactive login for the repo's own quick-start. The cost is that the
recipe's only durable output is the checkpoint; the learning curve that justifies
it is discarded.

**Impact.** Flipping the flag looks free and is not, because of where the import
sits (`train.py:246`):

```python
if wandb_log and master_process:
    import wandb
```

`wandb` is imported **only under the flag**. So `--wandb_log=True` silently
promotes `wandb` from "not used by this recipe" to a hard runtime dependency —
turning a three-package closure into a large one, and requiring credentials a
third-party reproducer does not have.

**What we did, and the two ways I got it wrong first.** This is the most
transferable thing in these notes, so the full sequence:

1. A first check, run in a stripped virtualenv, reported that the logging path
   was inert — anything wandb-compatible that cannot reach a backend still
   satisfies `import wandb`, still accepts every `log()` call, and still exits 0.
   On that basis we captured with logging off. **That conclusion was right for
   the wrong reason**: the virtualenv was not the environment the real job uses.
2. Re-checked against the environment the job actually runs in, logging *did*
   work and produced a live dashboard. So we re-captured with `--wandb_log=True`.
   That capture passed every completeness check we have.
3. Then the from-scratch rebuild check — fresh clone, an environment containing
   only what the run recorded, nothing else — ran the recorded command and got:

   ```
   File ".../train.py", line 246, in <module>
       import wandb
   ModuleNotFoundError: No module named 'wandb'
   ```

   The logging-enabled capture recorded `trackio` in its environment but never
   `wandb`, because on that host `wandb` was satisfied by a compatibility alias
   rather than by an installed package. The run was real; the recipe for
   repeating it was not self-contained.

**Fix applied here.** The published row is the run **with logging at its shipped
default (off)**, whose recorded command runs against its own recorded
environment with nothing else present — verified, not assumed. The learning
curve is preserved in `README.md` instead, where it costs no dependency at all.

**The lesson, stated generally.** A record that passes every completeness check
can still fail to rebuild, and only actually attempting the rebuild tells you
which. Three checks disagreed here, and the one that settled it was the one that
ran the real command in a from-scratch environment. It is also the cheapest of
the three. Run it last, and believe it over the others.

**Upstream-worthy?** Yes, and the fix removes the whole dilemma: write the eval
history to a CSV or JSONL in `out_dir` unconditionally, independent of wandb.
`train.py` already holds every value at the eval step. That gives every
reproducer a durable learning curve with no account, no credentials and no extra
dependency — and makes "did this rebuild match?" answerable from the artifact
rather than from scrollback. Of everything in this file, this is the change I
would most want upstream.

---

## What did *not* go wrong

Worth recording, because the campaign's usual failure modes were all absent:

* **No patch was needed.** The repo ran as published. `patches/` is empty.
* **No editable install.** nanoGPT has no `setup.py`/`pyproject.toml` and is not
  a package; `train.py` imports `model` as a sibling module, so running from the
  repo root is all that is required. Nothing shadows or blinds file-level tracing.
* **No pinning conflicts.** The dependency closure is three packages wide.
* **Deterministic, and demonstrably so.** `train.py:106` calls
  `torch.manual_seed(1337 + seed_offset)` before anything stochastic happens, and
  every source of randomness in this recipe — parameter init, the `torch.randint`
  batch sampler in `get_batch`, and dropout — draws from that generator. The
  campaign only claims *reproduce*, not *replicate*, so this was not required;
  we got it anyway. **Four independent full runs, launched separately, produced
  identical evaluation curves at all 21 eval points** (see the table in
  `README.md`) — not "close", identical to four decimal places at every
  checkpoint — and three of them emitted a **byte-identical 129 MB checkpoint**
  (blake3 `f4cc9b6ebb52a7f8…`, confirmed against the published artifact).
  Seeding costs one line and it is the difference between a rebuild you can
  compare and a rebuild you can only eyeball.
* The checkpoint-on-val-improvement logic (`always_save_checkpoint = False`) means
  the published artifact is the best-val checkpoint, not the last one — which is
  a nice property for a reproduction, since it is defined by a criterion rather
  than by where you stopped.
* **The recipe is honest about its scale.** 5000 iters, ~10.7M parameters, a
  1.1 MB corpus. Nothing is hidden behind a cluster.
