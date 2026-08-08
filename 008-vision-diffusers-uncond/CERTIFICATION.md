# Tier 2 — Certified reproduction · row 008 diffusers unconditional (DDPM)

Cold rebuild on a host that had never seen this row. Second certification attempt: the
first attempt failed **0/1** and this run is the test of the fix that unblocked it.

| | |
|---|---|
| DAG | `c7e6843763c25d8036ff22e48ba43a12d0dd0051d016f1f1e0090a88a3e99453` |
| HF artefact | `hf://reproducible-ai/diffusers-uncond` |
| `roar --version` | `roar, version 0.4.4rc2` |
| Wheel sha256 | `3677618d4c42d66143baf42912c8ed932f9706d5511d032bb2898fda6a465471` |
| Wheel | `roar_cli-0.4.4rc2-cp310-abi3-manylinux_2_34_x86_64.whl` (TestPyPI, published) |
| **Result** | **`ROAR_REPRODUCE_EXIT_CODE=0` · `Steps run: 1/1`** |
| Environment | **85/85 recorded pins present at exact versions — 0 missing, 0 mismatched** |
| Instance | `g4dn.xlarge` (1× Tesla T4), `ami-0f07f1a0b382b48f7`, us-east-2 |
| Wall clock | ~24 min host lifetime, covering **two** full reproductions |
| Cost | ~$0.22 |

## Command

```
roar reproduce c7e6843763c25d8036ff22e48ba43a12d0dd0051d016f1f1e0090a88a3e99453 \
    --lineage --run --no-puts -y --step-timeout 21600
```

`--pip-any-version` was **not** passed. `--step-timeout 0` was **not** passed.

## Result, verbatim

```
[Step 1/1]
  Command: roar run --wandb-to-trackio sh -c 'PYTHONPATH=src:$PYTHONPATH exec python
           examples/unconditional_image_generation/train_unconditional.py ...'
  Success

==================================================
Reproduction Complete
==================================================
Steps run: 1/1
ROAR_REPRODUCE_EXIT_CODE=0
```

Traced step record from roar's own job DB (`.roar/roar.db`):

| run | job_uid | exit_code | duration | git_commit |
|---|---|---|---|---|
| 1 | `3960bff0` | **0** | 218.76 s | `0af4dfdfc2` |
| 2 | `a50a9560` | **0** | 209.64 s | `0af4dfdfc2` |

Recorded capture was 237.60 s on the same GPU model. Recorded and rebuilt
`gpu_peak_mem_mb` are both **4726**.

Training completed the full recorded epoch: `Epoch 0: 100%|██████████| 460/460
[03:07<00:00, 2.45it/s, ema_decay=0.99, loss=0.0305, lr=0, step=460]`.

## Artefacts regenerated (stat'd on the host before termination)

| bytes | path (relative to the reproduce clone) |
|---|---|
| 454,741,108 | `ddpm-out/unet/diffusion_pytorch_model.safetensors` ← the published artefact |
| 1,117 | `ddpm-out/unet/config.json` |
| 502 | `ddpm-out/scheduler/scheduler_config.json` |
| 186 | `ddpm-out/model_index.json` |
| 141,992,736 | `data/huggan___pokemon/.../pokemon-train.arrow` (dataset cache) |

Byte-identical output is **not** claimed and was not observed — the rebuilt
`diffusion_pytorch_model.safetensors` hashes
`4b2f545d868d5d0984dec658acf5029e0264bd9418363b2dcef9630f44fe943f` against the recorded
`cb4bf35302425ac16a900683ff5c94a801f1f016f6baa29663921c6ee869c365`. Same size, same
shape, nondeterministic training. We claim reproduce, not replicate.

Both runs produced identical file sizes for all four model artefacts.

## Environment verification (the guard that actually decides the row)

The rebuilt venv was enumerated with `importlib.metadata` and diffed against the 85
recorded pins from the job record (`jobs/895534e4….metadata.packages.pip`):

```
recorded=85  rebuilt=118
MISSING (recorded but not rebuilt): 0
MISMATCHED versions: 0
EXTRA (rebuilt only, transitive): 33
```

The 33 extras are transitive and expected — 16 of them are the `nvidia-*-cu12` CUDA
wheels that PyPI `torch==2.7.0` pulls in, which the capture host did not carry because it
had CUDA system-wide. Extras are not a mismatch; every recorded pin resolved at its exact
recorded version.

### P0-14 — packages resolved from inside the recorded venv

roar was installed under the **recorded** interpreter, and the rebuilt venv matches it
exactly:

```
recorded runtime.python : 3.12.10 CPython
roar tool venv          : Python 3.12.10
reproduce venv          : version_info = 3.12.10, include-system-site-packages = false
```

`sys.path` of the reproduce venv contains **no** host site-packages — no
`/usr/local/lib/python3.10/dist-packages`, no `/opt/pytorch/...`:

```
/usr/local/lib/python312.zip
/usr/local/lib/python3.12
/usr/local/lib/python3.12/lib-dynload
/root/cert008/reproduce/diffusers/.venv/lib/python3.12/site-packages
```

Every probed package resolved inside the venv:

```
torch       -> .venv/lib/python3.12/site-packages/torch/__init__.py
accelerate  -> .venv/lib/python3.12/site-packages/accelerate/__init__.py
datasets    -> .venv/lib/python3.12/site-packages/datasets/__init__.py
wandb       -> .venv/lib/python3.12/site-packages/wandb/__init__.py
trackio     -> .venv/lib/python3.12/site-packages/trackio/__init__.py
```

The traced step's own recorded `PATH` puts the venv first, confirming the venv was
actually active for the workload (this settles the "python PATH question" for this row):

```
PATH = /root/cert008/reproduce/diffusers/.venv/bin:/usr/local/bin:/root/.local/bin:...
```

No `PYTHON VERSION MISMATCH` warning was emitted.

### Host hygiene

Three stale roar installs and four entrypoints were purged before installing, and the
purge was verified with `find` (not piped):

```
=== PURGE VERIFY (must be empty) ===
ls: cannot access '/usr/local/bin/roar': No such file or directory
ls: cannot access '/opt/pytorch/bin/roar': No such file or directory
no roar on PATH (expected)
```

Tracer present in the installed wheel (six artefacts): `libroar_tracer_preload.so`,
`roar-proxy`, `roar-tracer`, `roar-tracer-ebpf`, `roar-tracer-preload`, `roard`.

## The wandb question — stated plainly

This row's previous certification failed **0/1** with `ValueError: wandb.__spec__ is None`.
It is worth being precise about what that was and was not.

**It was never a missing dependency.** `wandb==0.28.1` is carried by the recorded freeze,
and it installed cleanly into the rebuilt venv. Verified directly on the host with no roar
environment set:

```
$ .venv/bin/python -c "import wandb; print(wandb.__version__, wandb.__file__)"
0.28.1 /root/cert008/reproduce/diffusers/.venv/lib/python3.12/site-packages/wandb/__init__.py
```

The recorded step carries `run_modifiers: {"wandb_to_trackio": true}`, so reproduce
re-emits `roar run --wandb-to-trackio`. At run time that alias **shadows** the real,
installed `wandb==0.28.1` with an in-memory stub, because the capture host had
`TRACKIO_SPACE_ID` set (sync mode) and a cold reproduce host does not (no-op mode). The
log shows the substitution happening in both runs:

```
[wandb->trackio] wandb no-op (tracking disabled)
```

Under that stub the workload sees:

```
wandb.__file__     -> None
wandb.__version__  -> None
find_spec('wandb') -> ModuleSpec(name='wandb', loader=None)
import accelerate OK; is_wandb_available() -> True
```

So the honest summary: **the recorded package list is complete for this row.** The
substitution is behavioural (no external tracking, no credentials on a cold host), not a
dependency gap — and it is the same substitution the capture performed, differing only in
mode. Neither the capture nor the reproduction exercised real `wandb`; both ran through
the alias. A reproducer who wants the recorded `wandb` can simply not pass the modifier.

## Caveats recorded honestly

- **The row delta named the wrong HF repo.** It gave
  `reproducible-ai/ddpm-butterflies-uncond`; the DAG's put step publishes to
  `hf://reproducible-ai/diffusers-uncond`. Tier 1 reads 12/13 against the former and
  **13/13** against the latter. Certified against the repo the record actually names.
- **The reproduction recorded 4 outputs where the capture recorded 6.** The two dataset
  cache files (`pokemon-train.arrow`, `dataset_info.json`) were edges in the capture but
  not in the rebuild. Both files are present on disk; this is a tracer edge difference,
  not a missing artefact. The published artefact was regenerated.
- **No sample PNGs** were produced despite `--save_images_epochs=1`. The capture did not
  record any either, so capture and reproduction agree; this was not investigated further.
- **Two reproductions were run, not one.** The first detached launch did not capture the
  parent process's exit status, so the exact command was run a second time in a clean
  directory purely to record the literal exit code. This was **not** a retry of a failure
  — run 1 had already completed `1/1` with a traced step exit code of 0, and run 2 matched
  it in every respect. Both are reported above.
- **Extras are not audited.** 85/85 exact means every *recorded* pin resolved and
  installed. It says nothing about packages that never reached the record.
