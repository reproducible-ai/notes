# Tier 2 — cold rebuild certification · row 002 nanoGPT `shakespeare_char`

**Result: PASS.** A host that had never seen this row rebuilt the lineage from the
published record alone. Exit code `0`, `Steps run: 2/2`, all **57 recorded pins present
at the exact recorded version**, and every output artefact regenerated **byte-identically**.

**This supersedes the 2026-08-08 certification of `72ad9675…`, which passed for the wrong
reason.** That record carried 24 pins and was missing `tqdm` and `typing-extensions` —
two packages `import torch` actually loads — whose only path into the environment was the
experiment-tracking bridge's own dependency closure. Remove the bridge and the row would
have failed. The re-capture records 57 pins with both present, so the row now rebuilds off
its own declared package list.

| | |
|---|---|
| DAG | `19171777431d4ad91f91bd7ab64cbc52b706246f815e4d05b0812761a96808d3` |
| Supersedes | `72ad9675f624563a018c0e76f81fea418edb268ab19002c404a793721f86fde2` |
| HF repo | `reproducible-ai/nanogpt` (read from the DAG's own `put` step) |
| roar build | `roar, version 0.4.4rc5` |
| wheel | `roar_cli-0.4.4rc5-cp310-abi3-manylinux_2_34_x86_64.whl` |
| wheel sha256 | `ed35ed6bda3b5698ab65a887e7390c2ac073123f6d94bfa27b8282285352219c` |
| Instance | `i-0b17996d8d937d245` · g6e.xlarge · 1× NVIDIA L40S 46 GB · `ami-0f07f1a0b382b48f7` · us-east-2 |
| Recorded interpreter | Python 3.12.10 |
| Rebuild interpreter | Python 3.12.10 (exact match, no version-mismatch prompt) |
| Repo commit cloned | `0f02dbcff2d82b7a81d39b016a127b15475601ee` (matches the record) |
| Date | 2026-08-11 |

## Command

```
roar reproduce 19171777431d4ad91f91bd7ab64cbc52b706246f815e4d05b0812761a96808d3 \
    --lineage --run --no-puts -y --step-timeout 21600
```

`--pip-any-version` was **not** passed: the rebuild used the recorded pins, not "whatever
resolves today". `--no-puts` was mandatory — a cold host must not publish. The command was
started detached with `setsid` and its exit status written to a file, so the number below
is read from `/tmp/cert.exit`, not inferred from the log.

## Result

```
[Step 1/2]
  Command: roar run python data/shakespeare_char/prepare.py
  Success

[Step 2/2]
  Command: roar run --wandb-to-trackio env TRACKIO_SPACE_ID=reproducible-ai/experiments \
           PYTHONUNBUFFERED=1 python train.py config/train_shakespeare_char.py \
           --compile=False --wandb_log=True --wandb_project=nanogpt-shakespeare-char \
           --wandb_run_name=shakespeare-char-full-5000
  Success

Reproduction Complete
Steps run: 2/2
```

Literal process exit code: **0**.

`2/2`, not `3/3`: the lineage has three jobs and the third is the `roar put` publish step,
which `--no-puts` skips by design (`Skipping 1 publish (roar put) step(s) [--no-puts]`).

No `ModuleNotFoundError`, no `ImportError`, no `PYTHON VERSION MISMATCH` anywhere in the
log.

## The result that settles the previous row's open question

The superseded record's notes argued that switching on nanoGPT's own logging made the
recipe un-rebuildable, because `train.py:246` does `import wandb` under the flag while the
freeze records only `trackio`. **That is now measured to be false, and this rebuild is the
measurement.** `--wandb-to-trackio` is recorded in the job's `run_modifiers` and
`roar reproduce` re-emits it, so roar's alias is installed in the child interpreter
*before* `train.py` reaches its import. `import wandb` resolves to `trackio`, which the
freeze does pin, and the step ran to completion.

The earlier check reached the opposite conclusion because it ran `python train.py …`
directly — dropping `roar run --wandb-to-trackio`, which is part of the recorded command,
not scaffolding around it.

**The honest boundary:** a reader who rebuilds *by hand* from the 57 pins and types
`python train.py … --wandb_log=True` without that wrapper **will** hit
`ModuleNotFoundError: wandb`, because the record pins `trackio` and not `wandb`. Run it
without `--wandb_log`, or install `wandb`. `commands.md` says so explicitly.

## Output artefacts — stat'd **and hashed** on the host before termination

Sizes alone are not reconcilable later, so each carries a digest.

| Path | Bytes | blake3 | sha256 |
|---|---:|---|---|
| `out-shakespeare-char/ckpt.pt` | 128,985,500 | `ad112aa2216c7fdb4988cc1790228f05d9fb6be8259fc71402dd09d5e8d09105` | `d7b9a87df586ed447c55a12bb6d005332a7a40a6212cb9d2f29ef8ad83af4095` |
| `data/shakespeare_char/train.bin` | 2,007,708 | `471f608665c93f25230ba0252bf732d7fbac20c998686a9e3d34001e1ab86563` | `6ec305602a99ac2802745a134e1f5e33e2231b4855525b00b9aebb730ac2626f` |
| `data/shakespeare_char/val.bin` | 223,080 | `dec1fdaa9dd52da1e03040de93defa255a1f7576784cc8631febd7dc5c26f886` | `d37d30cc0c8327c270d493299c3dca54135f6d5f1c9ef60cda78076e311204b1` |
| `data/shakespeare_char/meta.pkl` | 703 | `696dfa9b973c9d83d9b1b0eb681f43be39193f598eb63b0cc0a41eb4326952e4` | `6ee5a37533af83b67fcbe6b93705fde9e15e78bafe895f54b2cb2cb32534526c` |
| `data/shakespeare_char/input.txt` | 1,115,394 | `5bd8f6749d3cda816828aabf1aebdc595f673de8102e521bbd8369ad4b7917e9` | `86c4e6aa9db7c042ec79f339dcb96d42b0075e16b8fc2e86bf0ca57e2dc565ed` |

**Every blake3 matches the capture's recorded artifact hash exactly** — the checkpoint
included. The campaign claims *reproduce*, not *replicate*; this row happens to deliver
replicate, because `train.py:106` pins `torch.manual_seed(1337 + seed_offset)` and both
runs used an L40S. The previous certification could not settle this: it ran on an A10G and
recorded only sizes plus a differing digest.

The 21-point evaluation curve is likewise identical to the capture at four decimals, best
validation loss **1.4666 at iteration 1750**.

## Manifest diff — 57/57 EXACT

`pip freeze` was **not** used. The reproduce venv is uv-provisioned and ships no `pip`
(`ModuleNotFoundError: No module named 'pip'` — verified), so `python -m pip freeze`
returns empty, which reads identically to "nothing was installed". Two independent methods
were used and required to agree:

```
uv pip freeze --python /root/repro/reproduce/nanoGPT/.venv/bin/python   ->  87 lines
.venv/bin/python -c "import importlib.metadata as m; print(len([...]))" ->  87
```

| | |
|---|---|
| Recorded pins | **57** |
| Present at the exact recorded version | **57** |
| Missing | **0** |
| Version-mismatched | **0** |
| Installed distributions | 87 |
| Extras (transitive closure) | 30 |

The 30 extras are what a resolver adds on top of the recorded set: 14 `nvidia-*` CUDA
runtime wheels plus their companions, and the usual `jinja2`/`markupsafe`/`setuptools`
tail. Full lists in `cert-evidence/recorded-requirements.txt` (57) and
`cert-evidence/rebuilt-freeze.txt` (87).

## Was the record sufficient? Almost — and the remaining gap is a new shape

Direct experiment, not inference. A second venv was built with `--no-deps` from exactly the
57 recorded pins, and the recorded commands run against it:

| Test | Superseded record (24 pins) | This record (57 pins) |
|---|---|---|
| recorded step 1 — `python data/shakespeare_char/prepare.py` | ❌ `ModuleNotFoundError: idna` | ✅ **exit 0**, prints all four expected dataset statistics |
| the logging path — roar's alias + `import wandb` | (not applicable; logging was off) | ✅ **exit 0**, `wandb -> trackio` |
| `import torch` | ❌ `ModuleNotFoundError: typing_extensions` | ❌ `ImportError: libcudnn.so.9: cannot open shared object file` |
| control — same import in the full rebuild venv | ✅ exit 0 | ✅ exit 0 (`2.7.0+cu126`, `cuda True`) |

**The two failures are not the same kind of failure, and the difference is the whole
point.** The old one was a missing *Python package* — and worse, `tqdm`'s only supplier in
that environment was `huggingface-hub` arriving under the tracking bridge, so the row's
greenness depended on our own plumbing being installed. The new one is a missing *native
shared library*: `libcudnn.so.9` ships inside the `nvidia-cudnn-cu12` wheel, which torch
loads with `dlopen` rather than `import`. A freeze assembled from loaded Python modules
cannot see it.

That gap is benign in practice and structural in cause. `nvidia-cudnn-cu12` is a declared
dependency of `torch==2.7.0`, so any resolver installing the recorded `torch` pin pulls it
in automatically — which is exactly what happened, and why the real rebuild is 57/57 exact
with a byte-identical checkpoint. It is worth recording anyway, because "the freeze is a
closed set" and "the freeze rebuilds" are different claims and only the second one is true
here.

The decisive imports-vs-freeze audit is clean: **Tier-A missing = 0** (was `tqdm`,
`typing-extensions`), **Tier-B hints = 0** (was 7).

## Did anything resolve from outside the recorded venv?

No. Four independent observations:

```
.venv/pyvenv.cfg:   version_info = 3.12.10
                    include-system-site-packages = false

sys.path:           ''
                    /usr/local/lib/python312.zip
                    /usr/local/lib/python3.12
                    /usr/local/lib/python3.12/lib-dynload
                    /root/repro/reproduce/nanoGPT/.venv/lib/python3.12/site-packages

HOST-SHADOW PATHS:  NONE          (no dist-packages, no /opt/pytorch, no /usr/lib/python3)

torch             2.7.0+cu126   .../.venv/lib/python3.12/site-packages/torch/__init__.py
numpy             2.4.4         .../.venv/lib/python3.12/site-packages/numpy/__init__.py
trackio           0.33.0        .../.venv/lib/python3.12/site-packages/trackio/__init__.py
tqdm              4.67.3        .../.venv/lib/python3.12/site-packages/tqdm/__init__.py
typing_extensions               .../.venv/lib/python3.12/site-packages/typing_extensions.py
```

The strongest single piece of evidence is negative: **the host has no bare `python` at
all** (`command -v python` → nothing; `python3` is 3.10.12), yet both recorded steps invoke
`python …` and both ran. Nothing was symlinked or aliased to make that work — the recorded
3.12.10 venv supplied the interpreter.

roar itself was installed **under the recorded interpreter**, not the host's:

```
uv tool install --python 3.12.10 --force --with huggingface-hub <wheel>
sudo ln -sf /root/.local/bin/roar /usr/local/bin/roar
```

The symlink is not optional: every recorded step is itself a `roar run …`, so
`roar reproduce` spawns a nested `roar` that must be resolvable on `PATH`.

## Substrate hygiene

```
roar, version 0.4.4rc5
ed35ed6bda3b5698ab65a887e7390c2ac073123f6d94bfa27b8282285352219c  roar_cli-0.4.4rc5-...whl
roar/bin: libroar_tracer_preload.so  roar-proxy  roar-tracer  roar-tracer-ebpf
          roar-tracer-preload  roard        (6 artefacts)
```

The wheel came from its published, immutable file URL and its sha256 was verified against
the index digest **before** installation — no presigned URL and no per-target shared secret
was involved, on either the capture or the certification host.

Stale-install purge ran, followed by an **unpiped** verification sweep (`find … -print`,
never piped into `head`, which would take SIGPIPE mid-list and report success anyway). The
sweep came back empty apart from the freshly-unpacked rc5 wheel inside uv's own cache.

Bootstrap touched only harness toolchain, never the recorded package set:
`apt-get update`, `python3.10-venv` (so `ensurepip` exists), `uv`. With `uv` present roar
provisioned the exact recorded interpreter and the version-mismatch prompt never fired.

## Watchdog

`sudo shutdown -h +60`, set before the run started. Basis: this row's traced compute is
~6 minutes on an L40S, so 60 minutes is well beyond 2× and still bounded. The run finished
45 minutes inside the ceiling, so no extension was needed and nothing healthy was killed.

## Cost and wall-clock

| Phase | Wall-clock |
|---|---|
| instance launch → SSM online | ~1.5 min |
| bootstrap (apt, uv, purge, roar install, assertions) | ~4 min |
| `roar reproduce` — clone + venv (87 pkgs) + prepare + full 5000-iter train | **3 m 21 s** |
| evidence collection + closed-set A/B | ~4 min |
| **billed instance lifetime** | **14 min** (03:02:23 → 03:16:23 UTC) |

g6e.xlarge on-demand ≈ $1.86/hr → **≈ $0.43**, first attempt, no retries.

`roar reproduce` is *faster* than the original capture's 5 m 45 s of traced compute for a
mundane reason worth stating: the capture had a working Hugging Face token and streamed
metrics to the hosted dashboard during training; the certification host deliberately has no
credentials, so trackio fails over to local buffering immediately instead of waiting on the
network. Training itself is the same speed on the same card.

Host terminated at 03:16:23 UTC and confirmed `terminated` by `describe-instances`; the
campaign-wide orphan sweep was clean.

## Evidence files

* `cert-evidence/recorded-requirements.txt` — the 57 pins the record carries
* `cert-evidence/rebuilt-freeze.txt` — the 87 distributions the rebuild venv ended up with
