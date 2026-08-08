# Tier 2 — cold rebuild certification · row 007 lerobot ACT

**Result: PASS.** A host that had never seen this row rebuilt the lineage from the
published record alone. Exit code `0`, all pipeline steps succeeded, and every one of
the 80 recorded pins was present in the rebuilt environment at the exact recorded
version.

| | |
|---|---|
| DAG | `cc490321bbbf07fd270c8bd83d12967de0fb891d1265994c5cca134df57f0639` |
| HF repo | `reproducible-ai/lerobot-act` |
| roar build | `roar, version 0.4.4rc2` (TestPyPI) |
| wheel sha256 | `3677618d4c42d66143baf42912c8ed932f9706d5511d032bb2898fda6a465471` |
| wheel filename | `roar_cli-0.4.4rc2-cp310-abi3-manylinux_2_34_x86_64.whl` |
| Instance | `i-0c2b37e68aa8339c3` · g6e.xlarge · 1×L40S 46 GB · `ami-0f07f1a0b382b48f7` · us-east-2a |
| Recorded interpreter | Python 3.12.10 |
| Rebuild interpreter | Python 3.12.10 (exact match, no version-mismatch prompt) |
| Date | 2026-08-08 |

## Command

```
roar reproduce cc490321bbbf07fd270c8bd83d12967de0fb891d1265994c5cca134df57f0639 \
    --lineage --run --no-puts -y --step-timeout 21600
```

`--pip-any-version` was **not** passed: the rebuild used the recorded pins, not
"whatever resolves today". `--no-puts` was mandatory (a cold host must not publish).

## Result

```
Reproduction Complete
Steps run: 3/3
```

Literal process exit code: **0**.

`3/3`, not `4/4`: the lineage has four jobs, and the fourth is the `roar put` publish
step, which `--no-puts` deliberately excludes. All three *executable* steps ran:

| step | command | exit | duration |
|---|---|---|---|
| 1 | `python repro/fetch_dataset.py --repo-id lerobot/pusht_image …` | 0 | 4.5 s |
| 2 | `python repro/train_act.py … --steps=300 --batch_size=8 …` | 0 | 262.3 s |
| 3 | `python repro/evaluate_act.py --checkpoint … --out metrics/metrics.json` | 0 | 85.0 s |

Per-step exit codes read back from the rebuild's own job database, not just from stdout.

## Environment verification — the check that actually decides the row

"Environment ready" proves nothing on its own, so the rebuilt venv was enumerated and
diffed against the recorded per-job manifests.

```
step 1: 23 pins -> missing 0, mismatched 0
step 2: 79 pins -> missing 0, mismatched 0
step 3: 73 pins -> missing 0, mismatched 0
union recorded pins: 80
installed distributions: 104
MISSING   : NONE
MISMATCHED: NONE
```

The 24 extra distributions are the transitive closure (the `nvidia-*` CUDA libraries
pulled by `torch`, plus `jinja2`, `markupsafe`, `setuptools`, `cffi`, `pycparser`,
`psutil`, `toml`, `tzdata`, `mdurl`, `markdown-it-py`). Extras are not a failure; a
missing or mismatched recorded pin would have been.

**This is the row's headline claim, now executed rather than solved.** The re-capture
grew the lineage from 57 to 80 pins, but before this run only step 1 had ever been
executed off its recorded pins — `train` (79) and `evaluate` (73) had been checked by
`--solve` only, which proves a set *resolves*, not that it is *sufficient*. Both now
run to exit 0 off the recorded set on a cold host. No `ModuleNotFoundError` anywhere
in either run.

## The environment is genuinely the recorded one

The rebuild venv was confirmed to be closed against the host:

```
/root/reproduce/lerobot/.venv/pyvenv.cfg:
  version_info = 3.12.10
  include-system-site-packages = false

sys.path:
  /usr/local/lib/python312.zip
  /usr/local/lib/python3.12
  /usr/local/lib/python3.12/lib-dynload
  /root/reproduce/lerobot/.venv/lib/python3.12/site-packages

HOST-SHADOW PATHS: NONE
```

Every package checked resolves inside the venv, none from a host root:

```
torch              /root/reproduce/lerobot/.venv/lib/python3.12/site-packages/torch/__init__.py
huggingface_hub    …/.venv/lib/python3.12/site-packages/huggingface_hub/__init__.py
safetensors        …/.venv/lib/python3.12/site-packages/safetensors/__init__.py
numpy              …/.venv/lib/python3.12/site-packages/numpy/__init__.py
tqdm, yaml, certifi, filelock, fsspec, packaging, typing_extensions — all inside .venv
```

Worth stating explicitly: the host interpreter is Python **3.10.12**, and bare `python`
does not exist on this AMI at all. The recorded steps invoke `python`. They ran, which
means the recorded venv — not the host — supplied the interpreter. Nothing was
symlinked or aliased to make that work.

The tracer binaries shipped in the installed build were checked byte-for-byte against
the wheel of the expected sha256; all six match
(`libroar_tracer_preload.so`, `roar-proxy`, `roar-tracer`, `roar-tracer-ebpf`,
`roar-tracer-preload`, `roard`), so the artefact that ran is provably the named build.

## Artefacts regenerated

Checked on the host before termination:

| bytes | path |
|---|---|
| 206,666,968 | `outputs/act_pusht/checkpoints/000300/pretrained_model/model.safetensors` |
| 6,891 | `outputs/act_pusht/checkpoints/000300/pretrained_model/train_config.json` |
| 1,517 | `outputs/act_pusht/checkpoints/000300/pretrained_model/config.json` |
| 1,145 | `outputs/act_pusht/checkpoints/000300/pretrained_model/policy_preprocessor.json` |
| 660 | `outputs/act_pusht/checkpoints/000300/pretrained_model/policy_postprocessor.json` |
| 4,204 | `…/policy_preprocessor_step_3_normalizer_processor.safetensors` |
| 4,204 | `…/policy_postprocessor_step_0_unnormalizer_processor.safetensors` |
| 412,752,084 | `outputs/act_pusht/checkpoints/000300/training_state/optimizer_state.safetensors` |
| 15,708 | `outputs/act_pusht/checkpoints/000300/training_state/rng_state.safetensors` |
| 3,263 | `outputs/act_pusht/checkpoints/000300/training_state/optimizer_param_groups.json` |
| 223 | `outputs/act_pusht/checkpoints/000300/training_state/training_step.json` |
| 519–520 | `metrics/metrics.json` |

`model.safetensors` regenerates at exactly the published size, 206,666,968 bytes.

The dataset step re-fetched 31,621,889 bytes across 7 files
(`data/chunk-000/file-000.parquet` 31,496,298 B, `meta/info.json`, `meta/stats.json`,
`meta/tasks.parquet`, `meta/episodes/chunk-000/file-000.parquet`, `README.md`,
`.gitattributes`) and reported `codebase_version=v3.0 episodes=206 frames=25650 tasks=1 fps=10`.

`metrics.json` was computed, which is the row's claim — the values themselves are not
part of it:

```json
{"eval_loss": 0.5369285314232546, "action_l1": 53.508902430186815,
 "eval_batches": 343, "eval_samples": 2742, "held_out_episodes": 21}
```

## Two independent rebuilds

The pipeline was rebuilt twice from scratch on the same cold host. This was not a retry
of a failure — the first rebuild already succeeded; the second was run because the first
invocation was not wrapped to capture its literal process exit code, and the
certification bar requires that number rather than an inference from stdout.

| | run 1 | run 2 |
|---|---|---|
| result | `Steps run: 3/3`, all Success | `Steps run: 3/3`, all Success |
| exit code | not captured (harness omission) | **0** |
| `eval_loss` | 0.5369285314232546 | 0.5311163418407691 |
| `action_l1` | 53.508902430186815 | 53.06043956578647 |
| `model.safetensors` size | 206,666,968 | 206,666,968 |
| `model.safetensors` sha256 | `cbcf5b83…5d070` | `53a5465b…8b2eb` |

The weights are **not** bit-identical between runs and the metrics differ in the third
decimal. That is expected for non-deterministic GPU training and is not a defect against
the claim this campaign makes: we claim *reproduce* (rebuild the pipeline from the
recorded environment), not *replicate* (byte-identical output). Both runs produce a
model of identical size and a computed metric of the same magnitude.

## One finding worth recording: a system dependency outside the pip freeze

Both rebuilds emit this warning during `train` and `evaluate`:

```
Could not load libtorchcodec …
FFmpeg version 7: libavutil.so.59: cannot open shared object file: No such file or directory
FFmpeg version 6: libavutil.so.58: cannot open shared object file: No such file or directory
FFmpeg version 5: libavutil.so.57: cannot open shared object file: No such file or directory
FFmpeg version 4: libavutil.so.56: cannot open shared object file: No such file or directory
'torchcodec' is installed but cannot be loaded … Falling back to 'pyav' as a default decoder.
```

`torchcodec==0.4.0` is a recorded pin and it installs correctly, but it is a Python
wrapper over FFmpeg shared libraries, and **FFmpeg is an OS package that a pip freeze
cannot capture.** On a host without it, `torchcodec` imports and then fails to load its
native library.

**This did not fail the row**, and it is not a missing Python dependency: LeRobot
degrades gracefully to the `pyav` decoder, and `av==15.1.0` *is* in the recorded pin set,
so the fallback path is itself covered by the freeze. For this row the decode path is
also not load-bearing — `pusht_image` stores frames in parquet, not video.

It is recorded because it marks the edge of what a pip-level freeze can promise: this
row is closed at the Python level but not at the OS level, and a sibling row whose
dataset *is* video-backed could take the same warning as a hard failure rather than a
fallback. Capturing the OS package set (`--package-sync` territory) is what would close
it.

## Cost and wall clock

| | |
|---|---|
| Instance up | 17:15:21 UTC |
| Rebuild 1 | 17:29:48 → 17:37 (~7.5 min incl. clone + venv build) |
| Rebuild 2 | 17:40:37 → ~17:47 (~6.5 min) |
| Instance terminated | ~17:55 UTC |
| Total host time | ~40 min on g6e.xlarge @ ~$1.86/hr |
| Spend | ≈ **$1.25** (two full rebuilds), against an NTE of $10 |

A watchdog (`shutdown -h +120`, verified scheduled for 19:26:01 UTC) was armed before any
work began. Ceiling set at 120 min = expected wall clock (~35 min: setup + venv build +
~7 min train + eval) with roughly 2× headroom on a slower host. It never needed to fire;
the instance was terminated explicitly and the termination confirmed.

## What this certification does and does not establish

- It **does** establish that the recorded 80-pin environment is sufficient to run the
  whole pipeline — fetch, train and evaluate — on a machine that had never seen the row,
  producing the recorded artefacts. That is the product claim, and it holds.
- It **does not** establish bit-identical reproduction, and does not attempt to; see the
  two-run comparison above.
- It **does not** cover the `put` step, which `--no-puts` excludes by design.
- It **does not** establish OS-level closure; see the FFmpeg finding.
