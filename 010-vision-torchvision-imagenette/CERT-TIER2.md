# Tier-2 certification — cold rebuild — PASS

Row 010, `pytorch/vision` `references/classification`: resnet18 trained from scratch on
Imagenette (320px), 4 epochs, then evaluated against the checkpoint it just wrote.

A tier-2 certification is not an inspection of the record. It is an attempt to rebuild the
pipeline on a host that has never seen this row, from nothing but the published lineage, and
a report of what happened. This is that report.

---

## Verdict

| | |
|---|---|
| **Result** | **PASS** |
| Exit code | **0** (literal, captured from the process) |
| Steps run | **3/3** |
| Manifest diff | **44/44 EXACT** — 0 missing, 0 mismatched |
| Outputs regenerated | yes — 6 artefacts, all listed below with size **and** sha256 |
| Date | 2026-08-11 |

The record carries **four** jobs. The fourth is `roar put`, which publishes to Hugging Face;
`--no-puts` excludes it by design, because a cold host cannot and must not write to the
project's model repo. `3/3` is therefore every step that a rebuild is meant to execute, not
a step short of the graph.

---

## What was rebuilt

| | |
|---|---|
| Attributed DAG | `6a5cc35cdb0212b929d80998787902455bd0d7b2fb65a860f4f0db5c92fa630a` |
| Repository | `https://github.com/reproducible-ai/vision` @ `032ac1b7583ea3db1e21cadbd5156580a9e48c07` |
| Artifact repo | `https://huggingface.co/reproducible-ai/vision-classifier` (resolved from the record's own `put` destination, not guessed) |
| Command | `roar reproduce 6a5cc35c… --lineage --run --no-puts -y --step-timeout 21600` |

The three executed steps, exactly as the record holds them:

```
1. python references/classification/fetch_imagenette.py --root data --size 320px
2. python references/classification/train.py --data-path data/imagenette2-320 --model resnet18 \
     --epochs 4 --batch-size 64 --workers 0 --lr 0.05 --lr-scheduler cosineannealinglr \
     --lr-warmup-epochs 1 --lr-warmup-method linear --output-dir out --device cuda
3. python references/classification/evaluate_checkpoint.py --data-path data/imagenette2-320 \
     --split val --model resnet18 --checkpoint out/checkpoint.pth --metrics-out out/metrics.json \
     --batch-size 64 --workers 0 --device cuda
```

Nothing was added, relaxed or substituted. `--pip-any-version` was **not** used, so the
rebuild ran against the recorded pins rather than whatever resolves today.

---

## Tier-1 pre-flight (free, before any GPU spend)

```
Tier-1 bar — 6a5cc35cdb0212b9 · reproducible-ai/vision-classifier
  [✅] clean-dag    Clean-DAG check — 13/13 passed  ·  6a5cc35cdb0212b9 · 4 jobs (published DAG)
  [✅] ai-bom       AI-BOM score: 100/100  ·  profile: Advanced
  [✅] public-urls  RESULT: ALL PUBLIC
  [✅] freeze       RESULT: PORTABLE

RESULT: REPRODUCIBLE RECORD — tier 1 complete
```

Attribution on the published graph is intact: 4 jobs, `owner_name = "Reproducible AI"`,
`project_name = null` (correct — the scope resolves to the organization). All four steps are
present and numbered 1–4; no step is missing from the attributed graph.

An independent imports-vs-freeze audit reports **Tier-A misses: 0** — every distribution the
recipe is measured to import is in the recorded freeze, including `tqdm` and
`typing-extensions`.

---

## Environment the rebuild actually ran in

The interesting question about any rebuild is not whether it exited 0 — it is *what it ran
against*. A rebuild that quietly picks up the host's own packages proves nothing about the
record. So this was checked directly rather than assumed:

```
pyvenv.cfg:  version_info = 3.12.10
             include-system-site-packages = false
venv python: Python 3.12.10          (== the recorded interpreter)
sys.path:    ['', /usr/local/lib/python312.zip, /usr/local/lib/python3.12,
              /usr/local/lib/python3.12/lib-dynload,
              /opt/cert/run/reproduce/vision/.venv/lib/python3.12/site-packages]
HOST_SHADOW_PATHS: []
torch        2.7.0+cu126  → …/.venv/lib/python3.12/site-packages/torch/__init__.py
torchvision  0.22.0+cu126 → …/.venv/lib/python3.12/site-packages/torchvision/__init__.py
```

No host package root appears on `sys.path`, and both heavyweight dependencies resolve from
inside the rebuilt environment. The strongest single piece of evidence: the host's own
interpreter is **Python 3.10.12** and the host has **no bare `python` at all** — yet every
recorded step is a `python …` command and all three ran. The interpreter can only have come
from the rebuilt environment. Nothing was symlinked or aliased to make that work.

## Manifest diff — 44/44 EXACT

The reproduce environment ships no `pip`, so it was enumerated two independent ways and the
two were required to agree:

```
uv pip freeze --python <venv>/bin/python    → 70
<venv>/bin/python -c "…importlib.metadata…" → IMPORTLIB_COUNT: 70
```

Diffed against the 44 pins on the job records:

```
recorded pins: 44   installed dists: 70
MISSING (recorded but not installed): NONE
MISMATCHED versions:                  NONE
MANIFEST DIFF: 44/44 EXACT
```

The 26 extras are the transitive closure — the CUDA runtime wheels (`nvidia-*`), plus
`jinja2`, `markupsafe`, `setuptools`, `cffi`, `pycparser`, `hf-xet`, `httptools`, `uvloop`,
`websockets`, `python-dotenv`, `markdown-it-py`, `mdurl`. An installed set larger than the
recorded set is expected and correct; a *smaller* one would be the problem.

**No `ModuleNotFoundError` occurred at any point.** That is the finding tier 2 exists to
produce: the recorded package list is not merely portable and not merely resolvable, it is
*sufficient* — it actually runs the recipe on a machine that has never seen it.

---

## Artefacts regenerated

Every output stated with size **and** sha256, because sizes alone cannot settle a later
question.

**Run 1**

| bytes | sha256 | file |
|---|---|---|
| 89,553,609 | `c6e180c304daeaeee46c37560f86c9a2badb1eebeb9438b4bba11cc92a8ed755` | `out/checkpoint.pth` |
| 89,552,527 | `64fa6ba5c49166c2338957fd1d96d516c361a0a079f96c66f316aaf97662534f` | `out/model_0.pth` |
| 89,552,527 | `3726633bcb47391fec4b502fbdbf228cdfae19dd589b99096a0dec847b2df4f7` | `out/model_1.pth` |
| 89,552,527 | `bebbab43ac299d66d9532d51d4dfd6892e4a58abde37650db04d3133888ca075` | `out/model_2.pth` |
| 89,552,527 | `5acc578c991ed4a86bfde32403bedf36e59c469bff15f5ae22e285cd9b186693` | `out/model_3.pth` |
| 356 | `eddca7632f414f5e85f5114abbea9bbe3b9fb30557fb026a7d679ef6737aede1` | `out/metrics.json` |

**Run 2**

| bytes | sha256 | file |
|---|---|---|
| 89,553,609 | `8d6a31f0a6761cdae427c5683995777f11bb71c509ab38cd6d74365f97c471cf` | `out/checkpoint.pth` |
| 89,552,527 | `80b182b3876d5909a51a7f23e2c9358d91fe3a2d043105ea78cb905486e3db41` | `out/model_0.pth` |
| 89,552,527 | `92ad0c9e95d425f205ca805ff5f900ca1d29b50c8435831b27f1b56751ac5c15` | `out/model_1.pth` |
| 89,552,527 | `458ee10fc62e3c6a62b6af53d88486bcdc2099f8c9773d49db3f0fc3b692d642` | `out/model_2.pth` |
| 89,552,527 | `71460babad78305924073f4e745e635a8e5d7fee3ea1d5790fecad5cc176cc2a` | `out/model_3.pth` |
| 356 | `3337acce6d52c4cd4270be2b8f2c665bea6eb134b4f154615d60cdf5adfdc0e0` | `out/metrics.json` |

**Published artefact, for comparison** — `checkpoint.pth` on Hugging Face is
**89,553,609 B**, sha256 `d78326dda05260c3d2df549ef41af02622ca2acfc3927c2a57c9d6f09d4a1c54`.

So the checkpoint regenerates at **exactly the published byte size**, three times over —
once at capture and once in each cold rebuild — while the three sha256s all differ. That is
the expected shape for this workload. Training on a GPU is not bit-deterministic here (cuDNN
algorithm selection is unpinned and the reference script exposes no deterministic mode), so
the *weights* differ run to run while the *structure* of the file does not. We claim
reproduce, not replicate; matching bytes were never the bar, and the matching size is a
stronger signal than it may look, since it shows the same architecture, the same optimizer
state and the same serialisation path every time.

The dataset step also regenerated its input in full: **13,394 JPEGs, 686 MB**, on both runs.

## Metrics were computed — and the values drift, as expected

| | top-1 |
|---|---|
| recorded capture | 55.36 % |
| cold rebuild, run 1 | 55.2866 % |
| cold rebuild, run 2 | 56.0255 % |

The bar is that a metric is *computed* from the regenerated checkpoint by a separate
evaluation step, not that a number is hit. It was, both times, over the full 3,925-image
held-out split. Earlier runs of this recipe have landed at 55.31 % and 60.13 %; the spread
is the recipe's, not the record's.

---

## How it was run

| | |
|---|---|
| Host | `i-020a6dcfc4ca76e8b`, g4dn.xlarge, 1× Tesla T4, 4 vCPU, us-east-2a |
| AMI | `ami-0f07f1a0b382b48f7` |
| roar | **0.4.4rc2** — the same build the row was captured on |
| Wheel sha256 | `3677618d4c42d66143baf42912c8ed932f9706d5511d032bb2898fda6a465471` — verified against the index digest **before** installing, since a version string cannot distinguish builds |
| Tracer | `preload` |
| Instance lifetime | 00:32:02 → 01:00:50 UTC (28m48s), terminated and verified `terminated` |
| Spend | ≈ **$0.27** (0.48 h × $0.526/h list price, plus a few cents of EBS) |

Per-step timings from the second run: fetch **28.3 s**, train **312.1 s**, evaluate
**24.1 s** — each reporting `exit 0` individually. The T4 sustained ~378 img/s; this workload
is JPEG-decode bound on 4 vCPU, so a larger accelerator buys nothing.

roar was installed under the **recorded** 3.12.10 interpreter rather than the host's 3.10.12,
so that roar and the traced child share an interpreter, and it was placed on `PATH` for the
nested calls the recorded steps make. Before installing, the three stale roar copies on the
AMI and their entrypoints were removed, and the removal was verified with a follow-up sweep
rather than trusted. The installed build reported `roar, version 0.4.4rc2` and carried all
six tracer artefacts.

### Disclosure: the rebuild was run twice

The first run completed **3/3** with every step reporting `Success`, but it was launched
detached in a way that discarded the process's exit status, so no literal exit code was
captured. Rather than report an exit code inferred from a log, the rebuild was run a second
time from scratch in a clean directory with the status captured explicitly: `EXIT_CODE=0`,
`Steps run: 3/3`. The re-run was not an attempt to turn a failure into a pass — the first run
did not fail — and it has the useful side effect that every number in this document is backed
by two independent cold rebuilds rather than one.

### One environment warning, and why it is not a defect

`roar reproduce` noted `CUDA required (version 13.0) but not available`: the capture host ran
CUDA 13.0 and this one does not. Training then ran on the GPU normally (~378 img/s, 4,037 MB
peak) and all three steps exited 0. The package list is the substrate we claim to reproduce;
the driver stack underneath it belongs to the host, and portability across AMIs is explicitly
out of scope. Recorded here so nobody has to rediscover that the warning is benign.

No `PYTHON VERSION MISMATCH` warning fired, which is the expected outcome when the exact
recorded interpreter is provisioned.

---

## What this certification does and does not claim

It claims: on a machine that had never seen this row, the published lineage alone rebuilt the
environment to the exact recorded pin set, ran all three recorded steps to exit 0, and
regenerated every output artefact — including a checkpoint of exactly the published size —
with a fresh accuracy figure computed from it.

It does not claim byte-identical weights, a converged model, or an ImageNet result. The run
is four epochs on a ten-class subset and says so everywhere.
