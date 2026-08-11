# Tier 2 — cold rebuild certification · row 005 timm ResNet-18 / Fashion-MNIST

**Result: PASS.** A host that had never seen this row rebuilt it from the
published lineage alone: exit **0**, **3/3** steps, **67/67** recorded pins
present at the recorded version, and the checkpoint regenerated at **exactly**
the published byte size.

This row was predicted to reproduce *because of* its record rather than despite
it (13/13 clean-DAG, BOM 100/100, `imports_vs_freeze_audit` Tier-A misses zero).
It did, on the first attempt, with nothing installed by hand and nothing relaxed.

_The predecessor record `42b381d9…` was separately certified on 2026-08-10; that
transcript is preserved alongside this one as
`CERT-TIER2-superseded-42b381d9.md`. This certification covers the current
record, which adds the experiment dashboard._

| | |
|---|---|
| DAG certified | `af56b02d6c041c931f03ccf643f2e0fee97bbddb0072f26b91a291f142850dfd` |
| date | 2026-08-11 |
| HF repo | `reproducible-ai/timm-classifier` |
| fork commit | `f741a2b0a1a189a4ecb94793fa54deb9912a7c2c` |
| command | `roar reproduce <dag> --lineage --run --no-puts -y --step-timeout 21600` |
| exit code | **0** |
| steps | **3/3** (`fetch_dataset` · `train` · `evaluate`) |
| manifest diff | **67/67 EXACT** — 0 missing, 0 mismatched; 98 distributions installed |
| host | `i-0e16cfff386a839e6`, g4dn.xlarge (1× Tesla T4), us-east-2, `ami-0f07f1a0b382b48f7` |
| wall clock | 12m59s instance life (01:57:26 → 02:10:25 UTC) |
| spend | ~$0.11 at $0.526/h |
| roar | `0.4.4rc5` |
| wheel sha256 | `ed35ed6bda3b5698ab65a887e7390c2ac073123f6d94bfa27b8282285352219c` |

The wheel digest was verified against the index **before** installing, not after.
No commit SHA is embedded in the artefact and several distinct builds have
reported the same version string, so the sha256 — not the version, not the
filename — is the build identity.

## Guards

`--pip-any-version` was **not** passed: the certification runs against the
recorded pins or it does not run. No `PYTHON VERSION MISMATCH` warning appeared —
the recorded interpreter (**3.12.10**) was provisioned exactly, so nothing had to
be waved through.

The instance carried a self-terminating watchdog set to **45 minutes**, roughly
3× this row's ~13-minute expected wall clock. A flat ceiling is not safe across
rows (some rows' training stage alone runs over an hour), so it was sized from
this row. The run finished well inside it, the host was terminated explicitly,
and termination was **confirmed** by `describe-instances` rather than assumed.

## Steps

```
Running 3 pipeline step(s)...

[Step 1/3]  roar run --wandb-to-trackio python reproduction/fetch_fashion_mnist.py --data-dir ./data
  Success                          roar: done · 17.6s (trace 16.5s + post 1.1s, exit 0)

[Step 2/3]  roar run --wandb-to-trackio python train.py … --epochs 5 … --log-wandb --wandb-project resnet18-fashion-mnist
  Success                          roar: done · 159.2s (trace 158.3s + post 0.8s, exit 0)

[Step 3/3]  roar run --wandb-to-trackio python validate.py … --results-file ./metrics/eval.json
  Success                          roar: done · 13.0s (trace 12.2s + post 0.8s, exit 0)

==================================================
Reproduction Complete
==================================================
Steps run: 3/3
```

## Outputs regenerated — size **and** sha256

Sizes alone are not reconcilable later, so both are recorded.

| file | bytes | sha256 |
|---|---|---|
| `output/resnet18-fashion-mnist/last.pth.tar` | **89,506,383** | `c9771aa87b589d274011f047e12e167c4d3149014dda945e3cd2d84743d3951c` |
| `output/resnet18-fashion-mnist/summary.csv` | 406 | `33a6c218811e2bc008d98f843748b83121828642bc671b35e01f8827c1997017` |
| `output/resnet18-fashion-mnist/args.yaml` | 3,358 | `6d7915429008b442103c6619f1f9fee01ce6fb487e8c161cf0124f2c34c28178` |
| `metrics/eval.json` | 209 | `db37b14c09573bbedf2a9bbf6c9278ed1131b1d02ba55ffca0200ba3e5743f0c` |

`last.pth.tar` came back at **89,506,383 bytes — byte-for-byte the same size as
the published artifact**, whose content hash is
`ff663730cd015c80ef873b0a6f21dcfbe8d48f62f40d9c50fabbc2bd33e835ef`. The **sizes
match and the hashes do not**, which is the expected and correct outcome: the
tensor *shapes* are fully determined by the recipe while the tensor *values* are
not (see "Not bit-reproducible" below). Size match plus hash mismatch is exactly
the signature of "same model, different arithmetic".

`link count = 1` on the checkpoint, confirming this fork's `--save-last-only`
behaves as documented. Stock timm would show 3 — `os.link()` hardlinks to one
inode, not copies; see `issues.md`, "Not a defect".

Held-out metrics recomputed by the `evaluate` step against the rebuilt
checkpoint:

```json
{ "model": "resnet18", "top1": 85.47, "top1_err": 14.53,
  "top5": 99.65, "top5_err": 0.35, "param_count": 11.18,
  "img_size": 28, "crop_pct": 1.0, "interpolation": "bicubic" }
```

against the record's **85.30 / 99.65**. A 0.17-point top-1 difference is GPU
nondeterminism, not a defect.

## Manifest diff — 67/67 EXACT

The reproduce venv was enumerated with **two independent methods that had to
agree**, and they did — 98 and 98:

```
uv pip freeze --python <venv>/bin/python        → 98
<venv>/bin/python  importlib.metadata count     → 98
```

Diffed against the row's recorded pins, taken from the **job** records
(`metadata.packages.pip`), not the session endpoint:

```
recorded distinct pins : 67
installed distributions: 98
MISSING  : none
MISMATCH : none
RESULT   : 67/67 recorded pins present at the recorded version
extras   : 31  (the transitive closure — nvidia-*, jinja2/markupsafe, setuptools …)
```

Installed exceeding recorded is expected and correct: the freeze records what the
workload **loaded**, while the installer must also materialise their
dependencies.

> ### ⚠️ `pip freeze` is a false-pass path on this venv — do not use it
>
> The reproduce venv is uv-provisioned and **ships no pip**:
>
> ```
> $ <venv>/bin/python -m pip freeze
> /root/reproduce/pytorch-image-models/.venv/bin/python: No module named pip
> ```
>
> It returns nothing, which reads identically to "nothing was installed" — so a
> broken rebuild would present as a clean diff. This was first caught on this
> row's earlier certification and re-confirmed here. Use `uv pip freeze` **and**
> an `importlib.metadata` count, and require that the two agree.

## The venv is genuinely the one that ran

The failure mode guarded against here is roar prepending a *host* interpreter's
`site-packages` onto a child running the recorded interpreter, so host packages
silently shadow recorded pins and the row certifies green against the wrong
substrate. Evidence it did not happen:

```
pyvenv.cfg:  version_info = 3.12.10      ← exactly the recorded interpreter
             include-system-site-packages = false
             uv = 0.12.3

sys.path site/dist-packages entries:
  ['/root/reproduce/pytorch-image-models/.venv/lib/python3.12/site-packages']
  ← one entry, and it is the venv's

every installed distribution's location:
  inside venv : 98
  OUTSIDE venv: 0
  offenders   : NONE

torch        2.7.0+cu126   …/.venv/lib/python3.12/site-packages/torch
torchvision  0.22.0+cu126  …/.venv/lib/python3.12/site-packages/torchvision
```

roar itself was installed under the **recorded** interpreter
(`uv tool install --python 3.12.10 --force --with huggingface-hub …`), so roar's
interpreter and the child's are the same, and then symlinked onto `PATH` — every
recorded step in this campaign is itself a `roar run …`, so `roar reproduce`
spawns a *nested* `roar` that must be resolvable or the step dies exit 127 before
Python starts.

The sharpest single piece of evidence: **the host has no bare `python` at all**
(`/usr/bin/python3` is 3.10.12; `command -v python` returns nothing), yet all
three recorded `python …` commands ran. The `python` they used could only have
come from the reproduce venv. Nothing was symlinked or aliased to make this work.

Tracer binaries were confirmed present before the run — a wheel built the wrong
way installs and reports a correct version while containing no tracer at all:

```
libroar_tracer_preload.so   roar-proxy   roar-tracer
roar-tracer-ebpf            roar-tracer-preload   roard
```

Stale roar installs were purged first (the AMI ships one, and leftovers from
other builds have been observed winning a reinstall and reporting a third,
older version). The purge was run unpiped and then verified with `find` — piping
a removal into `head` makes `rm` take SIGPIPE and die mid-list while still
reporting success.

## What the rebuild does *not* do: publish to the dashboard

The train step logged nothing to the experiment Space, by design:

```
[wandb->trackio] wandb no-op (tracking disabled)
```

Without a credential the wandb→tracking shim aliases `wandb` to a silent stub, so
timm's `import wandb` succeeds, `has_wandb` is true, `wandb.init()` returns a
no-op run, and training completes untracked. That is the correct behaviour for a
third-party reproduction — a stranger rebuilding this row should not need, and
must not get, write access to our dashboard — and it is why the experiment link
on this row is evidence about the **capture**, not about the rebuild.

It is also the one place where the rebuild is not a faithful re-execution of the
recorded command, and it is worth stating plainly rather than letting a green
exit code imply otherwise.

## Not bit-reproducible, and that is in scope

We claim **reproduce** (recreate the pipeline from the recorded package list),
not **replicate** (byte-identical output). GPU training here is not
bit-reproducible at `--seed 42`: cuDNN algorithm selection is unpinned and timm
exposes no `--deterministic`. Differing metric values and a differing checkpoint
hash are therefore expected and are **not** failures. What tier 2 tests is
whether the recorded package list is complete enough to rebuild and re-run the
pipeline — and on this row it is, exactly: 67/67.

## Caveat on this PASS

One thing a reader should not over-read: the freeze grew from 57 pins on the
superseded record to 67 here purely because enabling experiment logging loaded a
web-server stack (`starlette`, `uvicorn`, `httpx`, `pydantic`, …) into the traced
processes. That is the freeze being honest about what ran, not the row acquiring
new requirements. timm's own dependency footprint is unchanged.
