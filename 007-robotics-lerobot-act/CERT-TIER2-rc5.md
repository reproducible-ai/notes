# Row 007 — tier-2 certification of the rc5 record

**Result: PASS.** Cold rebuild on a host that had never seen this row: exit **0**,
**3/3** steps, **98/98** recorded pins present at the exact recorded version, outputs
regenerated. First attempt, no retries.

This certifies `27064dbb…`, which supersedes the previously certified `cc490321…`.

| | |
|---|---|
| DAG | `27064dbb01d6fa6e241329f93deff5e224eba4400482790adaabf52955be91fb` |
| Command | `roar reproduce 27064dbb… --lineage --run --no-puts -y --step-timeout 21600` |
| roar | `0.4.4rc5` |
| Wheel | `roar_cli-0.4.4rc5-cp310-abi3-manylinux_2_34_x86_64.whl` |
| Wheel sha256 | `ed35ed6bda3b5698ab65a887e7390c2ac073123f6d94bfa27b8282285352219c` |
| Instance | `i-0bee5269b655f8231` · g6e.xlarge (1×L40S) · `ami-0f07f1a0b382b48f7` · us-east-2 |
| Wall clock | 15m54s billed (01:58:53 → 02:14:47 UTC); the rebuild itself 6m39s |
| Spend | ~$0.49 at $1.861/h |

## Pre-flight (free)

```
Tier-1 bar — 27064dbb01d6fa6e · reproducible-ai/lerobot-act
  [✅] clean-dag    Clean-DAG check — 13/13 passed  ·  4 jobs (published DAG)
  [✅] ai-bom       AI-BOM score: 100/100  ·  profile: Advanced
  [✅] public-urls  RESULT: ALL PUBLIC
  [✅] freeze       RESULT: PORTABLE
RESULT: REPRODUCIBLE RECORD — tier 1 complete
```

## Build identity (all three lines)

```
roar, version 0.4.4rc5
expected: ed35ed6bda3b5698ab65a887e7390c2ac073123f6d94bfa27b8282285352219c
actual:   ed35ed6bda3b5698ab65a887e7390c2ac073123f6d94bfa27b8282285352219c   SHA256 MATCH
roar/bin/ → libroar_tracer_preload.so, roar-proxy, roar-tracer, roar-tracer-ebpf,
            roar-tracer-preload, roard   (6 artefacts — P0-10 clear)
```

Stronger than the version+hash pair alone: all **6** installed tracer artefacts were
compared byte-for-byte against the members of the verified wheel and are identical, so
the running install provably came from the wheel whose hash was checked.

**P0-14 workaround applied:**
`uv tool install --python 3.12.10 --force --with huggingface-hub --index-url
https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/
--index-strategy unsafe-best-match roar-cli==0.4.4rc5`, then symlinked to
`/usr/local/bin/roar`. roar's own interpreter resolves to Python **3.12.10** — the
recorded interpreter.

**P0-7 purge** ran before the install and was verified with `find` (unpiped, never
through `head`): no `roar_inject.pth`, no `roar_cli-*.dist-info`, no stale `roar` /
`roar-worker` entrypoints, no leftover `roar/` package directory.

## Result

```
Steps run: 3/3
exit=0            ← read from /tmp/cert.exit, not inferred from the log
```

The 4th job in the lineage is the `roar put` publish step, excluded by `--no-puts` by
design.

## Manifest diff — EXACT

```
recorded union pins      : 98      (per step: fetch_dataset 23 · train 97 · evaluate 73)
installed distributions  : 135
PRESENT AT EXACT RECORDED VERSION: 98/98
MISSING   : none
MISMATCHED: none
EXACT DIFF: YES
extra (transitive closure): 37     (nvidia-*, jinja2/markupsafe, gitpython, protobuf, …)
```

Method: `uv pip freeze --python <venv>/bin/python` **and** an `importlib.metadata`
distribution count. Both returned **135** and agree. `pip freeze` was deliberately not
used — the reproduce venv is uv-provisioned and ships no `pip`, so it returns empty,
which reads identically to "nothing was installed".

## Venv closure (P0-14 evidence)

```
sys.path:  /usr/local/lib/python312.zip
           /usr/local/lib/python3.12
           /usr/local/lib/python3.12/lib-dynload
           /home/ubuntu/reproduce/lerobot/.venv/lib/python3.12/site-packages
include-system-site-packages = false

torch            .../.venv/lib/python3.12/site-packages/torch/__init__.py
huggingface_hub  .../.venv/lib/python3.12/site-packages/huggingface_hub/__init__.py
safetensors      .../.venv/lib/python3.12/site-packages/safetensors/__init__.py
numpy            .../.venv/lib/python3.12/site-packages/numpy/__init__.py
trackio          .../.venv/lib/python3.12/site-packages/trackio/__init__.py
wandb            .../.venv/lib/python3.12/site-packages/wandb/__init__.py
```

No `dist-packages`, no host `site-packages`. Nothing resolved from outside the venv.

**Which interpreter ran the steps.** Before the run: `command -v python` → **ABSENT**;
`command -v python3` → `/usr/bin/python3`, Python **3.10.12**. The recorded steps are
`python repro/…` and they ran. The venv's python is **3.12.10**. Bare `python` does not
exist on this AMI, so the recorded venv demonstrably supplied the interpreter — and
nothing was symlinked or aliased to make it so.

## Outputs regenerated (size **and** sha256)

| file | bytes | sha256 |
|---|---|---|
| `model.safetensors` | 206,666,968 | `6d4af6a36fd3bb6599ea0b75195475594c716d08680a3a52abc7825e7d9158a9` |
| `optimizer_state.safetensors` | 412,752,084 | `22635d9098ed53225e2351c5a236c9ca37462e24ac529b6dddddde4023e67d25` |
| `config.json` | 1,517 | `0462769efb173f44e384ec9d6d12245375efc8bc2ad74218dfd8820b9e3c16b0` |
| `train_config.json` | 6,929 | `c0baf12a1de82d7aa2336afe564faa2b904529e97e289c504434d1ca9404b665` |
| `metrics.json` | 520 | `726c0ecd68109c1c494cc3aafa9127672afce0424b36a60c90ae06ebe32a300b` |
| `train.log` | 35,007 | `a02e12de714b0d0611b16040b60dc2f3d14d03bad0b96e8ac54a286e7bc621e9` |

`eval_loss` **0.5289** over 2,742 held-out frames (capture: 0.5294). Weight sizes match
the capture exactly; the hashes differ, which is non-deterministic GPU training — we
claim *reproduce*, not *replicate*.

`metrics.json` is 520 B here and 519 B at capture — one byte, from float formatting of
a different loss value. Both hashes are on record, so this is a settled fact rather
than an unresolvable size discrepancy.

## Rebuild timings (used in the row's full-run cost basis)

| phase | seconds |
|---|---|
| cold start: clone + venv + install 98 pins | 44.0 |
| `fetch_dataset` | 4.5 |
| `train` | 267.5 |
| `evaluate` | 83.0 |
| **total** | **399 (6m39s)** |

Per-step training cost measured here (`step_s` 0.264 s/step) is identical to the
capture host's, on a separate machine — which is what makes the full-run estimate
defensible rather than a single-host artefact.

## What this rebuild does NOT prove

A rebuild host holds no upload token, so the wandb→trackio bridge falls back to local
logging and uploads nothing. That is by design and is exactly why the run still
completes. **The rebuild proves the logging code path executes on the recorded pins; it
does not produce a second dashboard.** The capture is what produced the published one.

This is also the reason the space id had to be inside the recorded command rather than
exported around it — see `CAPTURE-0.4.4rc5.md` §2. With it exported, this rebuild would
have failed in `WandBLogger.__init__` before training step 1.

## Not chased (semantic frame)

- `torchcodec` is a recorded pin but needs FFmpeg, an OS package no pip freeze captures.
  On a bare host `libavutil.so.56/57/58/59` are all absent, it fails to load, and
  LeRobot falls back to `pyav` — also a recorded pin. Did not affect the result (P1-11).
- Metric values differing run to run; which tracer ran; download byte-drift.

## Host

Terminated and verified: `i-0bee5269b655f8231` → `shutting-down` at 02:14:47 UTC, and a
campaign-wide sweep afterwards showed no remaining GPU hosts (only the two long-lived
`t3.large` boxes from 2026-07-24, which are not campaign spend).
