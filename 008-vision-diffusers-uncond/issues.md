# 008 — obstacles

Upstream-repo findings only. Each entry: symptom → root cause → fix → is it
worth sending upstream?

---

## 1. The example rejects every released version of its own library

**Symptom.** `pip install diffusers` (0.39.0, the newest release) followed by the
README's training command aborts immediately:

```
ImportError: This example requires a source install from HuggingFace diffusers
(see `https://huggingface.co/docs/diffusers/installation#install-from-source`),
but the version found is 0.39.0.
```

**Root cause.** `examples/unconditional_image_generation/train_unconditional.py`
line 32 calls `check_min_version("0.40.0.dev0")`. `0.40.0.dev0` is the in-development
version on `main`; it has never been published. The examples directory tracks
`main`, so the floor is always one unreleased version ahead of PyPI. This is
deliberate and the README says so — "we highly recommend **installing from
source**" — but the practical effect is that the example and the distributed
library can never be used together.

**Why it matters for reproducibility.** Both obvious routes produce a record that
cannot be rebuilt:

- install from PyPI → the example refuses to start;
- `pip install .` from the checkout → the environment now contains
  `diffusers==0.40.0.dev0`, a version string that resolves on no index, so anyone
  restoring the recorded environment fails at dependency resolution.

**Fix used.** Do not install `diffusers` at all. Take it from the checked-out
commit by putting `src/` on `sys.path` from inside the run command:

```
sh -c 'PYTHONPATH=src:$PYTHONPATH exec python examples/.../train_unconditional.py ...'
```

`check_min_version` then reads `0.40.0.dev0` straight out of `src/diffusers/__init__.py`
and passes, the recorded environment contains no unresolvable pin, and the library
version is pinned by the recorded git commit instead of by a version string.
(`PYTHONPATH` is set *inside* the command, not around it, so it is part of the
recorded recipe rather than an invisible property of the operator's shell.)

**Upstream-worthy?** Yes, as a documentation issue rather than a bug. The README's
"install from source" box could state the consequence explicitly — that the
example is pinned to `main` and cannot be run against a release — and could
mention the `PYTHONPATH=src` route as an alternative to `pip install .` for anyone
who needs a reproducible environment record. Patch not prepared; no source change
is warranted.

---

## 2. The example's `requirements.txt` under-declares its dependencies

**Symptom.** A virtualenv built from
`examples/unconditional_image_generation/requirements.txt` cannot complete the run.

**Root cause.** The file is three lines:

```
accelerate>=0.16.0
torchvision
datasets
```

Missing:

- **`safetensors`** — `DDPMPipeline.save_pretrained()` writes
  `diffusion_pytorch_model.safetensors`, i.e. the final model artifact. It is a
  hard runtime requirement of the example's happy path, not an optional extra.
  It is declared in the *library's* `install_requires`, so a `pip install .` user
  gets it by accident and never notices; a reader who follows the "cd in the
  example folder and run `pip install -r requirements.txt`" instruction does not.
- **`wandb`** — required by the documented `--logger=wandb` mode. The README
  mentions it only in prose ("To be able to use Weights and Biases (`wandb`) as a
  logger you need to install the library"), several sections below the command
  that uses it.
- **`torch`** — not declared anywhere in the example's requirements, only implied.

**Fix used.** Installed `safetensors` and `wandb` alongside the declared three.

**Upstream-worthy?** Yes — adding `safetensors` (and arguably `wandb` as an extra)
to the example's `requirements.txt` is a one-line change that makes the file
actually describe the example's environment. Worth sending.

---

## 3. `.gitignore` directory-ignores `/data`

**Symptom.** With `--cache_dir=data` (the natural place to put the dataset cache
so it sits beside the run rather than in a global home-directory cache), the whole
directory is invisible to git, and nothing placed in it can be tracked.

**Root cause.** `.gitignore` line 149:

```
# data
/data
```

This is a **directory** ignore. Git does not descend into an excluded directory,
so a negation for anything inside it — `!data/.gitkeep` — has no effect. The
conventional way to keep an output/cache directory in the repo while ignoring its
contents (ignore the contents by file pattern, track a placeholder) is therefore
impossible for `data/`, and the directory does not survive a clean checkout at
all.

The same shape bites nested output directories: `DDPMPipeline.save_pretrained()`
writes into `ddpm-out/unet/` and `ddpm-out/scheduler/`, and a rule of
`ddpm-out/*` + `!ddpm-out/.gitkeep` silently swallows both subdirectories for the
same reason — the parent directory has to be re-included with `!ddpm-out/unet/`
before its own file-pattern rule can apply.

**Fix used.** In the fork, replaced the directory ignore with a file-pattern
ignore plus a tracked placeholder, and applied the same shape to every output
directory the run writes to. See
`patches/0001-gitignore-replace-data-directory-ignore.patch`.

```
data/*
!data/.gitkeep
ddpm-out/*
!ddpm-out/.gitkeep
!ddpm-out/unet/
ddpm-out/unet/*
!ddpm-out/unet/.gitkeep
!ddpm-out/scheduler/
ddpm-out/scheduler/*
!ddpm-out/scheduler/.gitkeep
```

**Upstream-worthy?** Marginal. `/data` is a long-standing catch-all inherited from
the transformers-era `.gitignore` and changing it upstream would be churn for
little benefit to most users. Recorded here because any fork that wants
reproducible, in-tree outputs has to deal with it, and because the failure is
silent — git reports nothing, the directory simply is not there.

---

## 4. Truncation granularity is one full epoch

**Symptom.** There is no way to stop training after N steps.

**Root cause.** `train_unconditional.py` exposes `--num_epochs` but no
`max_train_steps`. Sibling examples in the same repo (e.g. the text-to-image and
DreamBooth trainers) do expose `--max_train_steps`; this one does not. The
smallest possible run is therefore one complete pass over the dataset — 460 steps
for `huggan/pokemon` at batch 16.

**Consequence.** Anyone verifying the pipeline rather than the result pays for a
full epoch. It also couples the truncation knob to the dataset: `--num_epochs=1`
means 460 steps on Pokémon and 12 000+ on a larger set.

**Fix used.** None needed — one epoch on this dataset is ~4 minutes on a T4.
Sampling was truncated separately via `--ddpm_num_inference_steps=10` (from the
1000 default), which is a real knob and does most of the wall-clock saving at
epoch end.

**Upstream-worthy?** Yes, and it is a small, self-contained change: add
`--max_train_steps` matching the sibling examples' semantics. Patch not prepared
(out of scope for this row).

---

## 5. Cosmetic: `accelerate config` is presented as mandatory

**Symptom.** The README's setup sequence ends with "initialize an 🤗Accelerate
environment with: `accelerate config`", which is interactive and blocks any
non-interactive rebuild.

**Root cause.** All the example's commands are written as `accelerate launch
train_unconditional.py …`, which is the right advice for multi-GPU. For a
single-device run neither step is required: `python train_unconditional.py …`
constructs the same `Accelerator` and produces the same result.

**Fix used.** Ran the script directly with `python`. No `accelerate config`, no
`accelerate launch`, one less process layer. Verified identical behaviour.

**Upstream-worthy?** Low priority. A parenthetical noting that `accelerate config`
is only needed for distributed runs would save automation authors a detour.

---

## Non-issues, checked and cleared

- **The training script needed no source changes at all.** The only files changed
  in the fork are `.gitignore` and added scaffolding — 0 lines of upstream Python
  touched.
- Dataset `huggan/pokemon` is live and public (7357 images, single parquet).
- The run's recorded environment contains no local-version (`+cuNNN`) pins and no
  PEP-503 duplicate spellings; all 85 recorded pins resolve on PyPI.
- `--dataloader_num_workers` already defaults to `0`, so the recorded package set
  is the real environment rather than a worker subprocess's.
