# Certification — tier 2, cold rebuild

**Result: PASS.** A host that had never seen this row rebuilt the pipeline from the
published record alone, exit **0**, **`Steps run: 3/3`**, with the recorded package set
reproduced **exactly** and every recorded output regenerated at the recorded byte size.

The certifying agent did not capture this row and did not read the capture agent's working
directory. Everything below was derived from the published DAG, this notes directory, and
the cold host.

## Verdict

| | |
|---|---|
| DAG | `f81176e64bf814489ec3296286e11c499a48ca28ef52569e10bc2675c0780782` |
| exit code (read from `/tmp/cert.exit`, not inferred) | **0** |
| steps | **`Steps run: 3/3`** — 3 run steps; the 1 `roar put` step skipped by `--no-puts` |
| recorded-pin diff | **41/41 EXACT** on the training step; **53/53 EXACT** on the union of all three steps; 81 distributions installed |
| outputs regenerated | yes, all three, at the recorded byte sizes |
| `numpy<2` self-heal | **yes** — `numpy==1.26.4` installed straight from the record |
| roar | `0.4.4rc6`, wheel sha256 `c7115b748886259b6a089e547404376acf84c3b81b4cbc8dc5610490ebea7199` |
| host | `g4dn.xlarge` (1x NVIDIA T4, 15,360 MiB), us-east-2, AMI `ami-0f07f1a0b382b48f7` |
| rebuild wall clock | **2 m 29 s** (21:47:51 → 21:50:19 UTC, 2026-08-11) |
| instance lifetime / spend | ~17 min ≈ **$0.15** at $0.526/hr |

Command, verbatim:

```sh
roar reproduce f81176e64bf814489ec3296286e11c499a48ca28ef52569e10bc2675c0780782 \
  --lineage --run --no-puts -y --step-timeout 21600
```

## Build identity

The wheel was installed by name and version from the published TestPyPI index, not from a
presigned URL:

```
roar_cli-0.4.4rc6-cp310-abi3-manylinux_2_34_x86_64.whl
sha256 c7115b748886259b6a089e547404376acf84c3b81b4cbc8dc5610490ebea7199   ← matches row.json
```

Verified twice: the digest of the downloaded wheel, and then the digests of the tracer
binaries *inside* that wheel against the ones actually on disk after installation —

```
f029b5050273103a64ab06710cad9abda609c1f9d5898e64eca7a8a5611b4bc0  roar/bin/libroar_tracer_preload.so
047e336b753cb7507cfb3b8462cacacacca05494379ebba0cf9e27642a54a4bd  roar/bin/roar-tracer-preload
```

— identical in both places, so the installed build is the build the record names. Six
tracer artefacts present. `roar --version` → `roar, version 0.4.4rc6`.

## Venv resolution

Installed under the **recorded** interpreter, and the steps ran against the rebuilt venv and
nothing else:

```
exe    /root/reproduce/Depth-Anything-V2/.venv/bin/python     (Python 3.12.10 — the recorded version)
numpy  1.26.4        .../.venv/lib/python3.12/site-packages/numpy/__init__.py
torch  2.7.0+cu126   .../.venv/lib/python3.12/site-packages/torch/__init__.py
sys.path: /usr/local/lib/python312.zip, /usr/local/lib/python3.12,
          /usr/local/lib/python3.12/lib-dynload,
          /root/reproduce/Depth-Anything-V2/.venv/lib/python3.12/site-packages
```

No host `site-packages` on the path. Before the run, `python` did not exist on the host at
all (`command -v python` → exit 127) and `python3` was 3.10.12; the recorded steps invoke
bare `python`, so the fact that they ran at all is itself evidence that the rebuilt venv was
the interpreter in use. No `PYTHON VERSION MISMATCH` warning was emitted.

## Package manifest

Enumerated two independent ways, which agree exactly:

```
uv pip freeze --python <venv>/bin/python | wc -l                 -> 81
<venv>/bin/python -c "importlib.metadata … len(distributions())" -> 81
```

Against the record: **41/41 exact** for the training step's manifest (no missing package, no
version mismatch), and **53/53 exact** for the union of all three steps — the three recorded
steps share no package at conflicting versions, so roar provisioned one venv of 53 pins. The
28 extras beyond the record are the ordinary transitive closure: 15 `nvidia-*` CUDA
libraries, `triton`'s and `tensorboard`'s dependencies (`grpcio`, `markdown`, `werkzeug`,
`tensorboard-data-server`), `jinja2`/`markupsafe`, `packaging`, `setuptools`, `cffi`,
`pycparser`, `pyasn1`, `pyasn1-modules`, `mdurl`, `markdown-it-py`.

## Artefacts regenerated

| file | bytes | recorded bytes | sha256 |
|---|---|---|---|
| `checkpoints/depth_anything_v2_vits.pth` (input) | 99,218,434 | 99,218,434 | `715fade13be8f229f8a70cc02066f656f2423a59effd0579197bbf57860e1378` |
| `metric_depth/exp/hypersim/latest.pth` | 297,116,466 | 297,116,466 | `4ca513305e8ac4e2c98bd3bca3e5e846f92c7dc89608f2f3067f853f62ed63a2` |
| `metric_depth/exp/hypersim/events.out.tfevents.*` | 1,264 | 1,264 | `5fc96e0f740b231fbeea75ec468c17ffea8a71d157e8da59733cb38921620345` |

The fetched encoder weights are **byte-identical to upstream**: `715fade1…` is the LFS oid
Hugging Face reports for `depth-anything/Depth-Anything-V2-Small/depth_anything_v2_vits.pth`.

`latest.pth` matches the published checkpoint's size to the byte but not its sha256
(published: `31a126b8ea…`). That is expected — the weights are the product of a
nondeterministic GPU training run on different hardware — and is a *replicate* question, not
a *reproduce* one. The size agreeing exactly is the meaningful signal: same architecture,
same optimizer state, same epoch/best-metric dict.

Data slice: **160 files** (80 `.jpg` + 80 `.hdf5`, plus the repo's own `.gitkeep`),
20,601,520 bytes = 19.65 MiB, fetched by HTTP range request in 38.8 s — matching the
recorded "160 files, 19.6 MB, 40.3 s" exactly. Split lists rebuilt at 64 and 16 lines.

## Step timings, cold host

| step | this rebuild (cold T4) | recorded (warm L40S) |
|---|---|---|
| `fetch_weights` | 6.3 s (trace 5.3 s) | 4.9 s traced |
| `prepare_data` | 40.8 s (trace 40.2 s) | 40.3 s traced |
| `train` | 51.2 s (trace 50.4 s) | 11.4 s traced |

Environment provisioning — clone, venv creation and 81 packages including a 825 MB torch and
~2 GB of CUDA libraries — took **~70 s** end to end.

Metrics computed on the 16 held-out frames:

```
      d1,       d2,       d3,  abs_rel,   sq_rel,     rmse, rmse_log,    log10,    silog
   0.316,    0.571,    0.752,    0.511,    1.237,    2.114,    0.591,    0.204,    0.545
```

against the record's `0.284, 0.548, 0.751, 0.650, 1.800, 2.203, 0.606, 0.211, 0.574`. Same
order of magnitude, different values — exactly what a one-epoch 64-frame fine-tune on
different hardware should give. The certification tests that the metric is *computed*, not
what it equals.

## Two claims in the record, tested

The record asks a certifier to expect two things. One held; one did not reproduce.

**`numpy<2` self-healed — confirmed.** The record's stated hard failure is
`AttributeError: module 'numpy' has no attribute 'RankWarning'` at `train.py` line 46. The
rebuild installed `numpy==1.26.4` directly from the recorded manifest and the trainer ran to
completion with no intervention. The constraint is carried by the record, exactly as claimed.

**The "~110 s cold CUDA warm-up" did not reproduce.** The record measures the training step
at 204 s cold and 13 s warm on an L40S and attributes ~110 s of that gap to first-CUDA-context
and kernel warm-up. On this cold T4 the same step took **51.2 s**; re-running the identical
command on the now-warm host took **40.0 s**. The cold-start penalty measured here is
therefore **~11 s, not ~110 s** — an order of magnitude smaller.

This matters beyond curiosity, because `~110 s` is one of the line items in this row's
`fixedCostUsd` basis. What the two measurements together suggest is that the 204 s figure was
dominated by something specific to that host and that moment rather than by a portable
property of a cold GPU, and it should not be carried forward as a general per-run fixed cost.
The steady-state work is genuinely slower on the smaller card (40 s warm on a T4 vs 13 s on an
L40S), which is the expected direction.

**Peak GPU memory: 9,831 MiB observed, against 5,245 MiB recorded.** Sampled from
`nvidia-smi` at 4 Hz across a full training step. The two numbers are almost certainly
measuring different things — 5,245 MiB reads like `torch.cuda.max_memory_allocated()`, which
counts live tensor allocations and excludes both the CUDA context and the caching allocator's
reserved-but-unused blocks; 9,831 MiB is what the device actually holds. **The record's
conclusion is still correct: this row does fit a T4, and this certification ran it on one.**
But the headroom is 36% of a 16 GB card, not the 66% the published figure implies, and the
record does not say which quantity it is quoting. Anyone sizing hardware from that number
should size from ~10 GB.

## Reproducibility gates, as reported by the rebuild itself

```
Reproducibility (as recorded) — 5/5
  [OK] code committed to git
  [OK] single git commit across all steps
  [OK] commit reachable on a remote
  [OK] all inputs sourced
  [OK] runtime captured (interpreter + packages)
```

Tier-1 pre-flight was re-run before spending anything: clean-DAG 13/13, AI-BOM 100/100,
all public URLs resolve with no credentials, freeze portable.

## Host lifecycle

Launched `i-00060b7f0eb4ab70f` (g4dn.xlarge, us-east-2a, subnet `subnet-07562bd32e9fc8d33`,
SG `sg-02d149ced3e370807`, profile `modelsandbox-instance-profile`, tagged
`campaign=reproducible-ai`). A `shutdown -h +75` watchdog was armed before anything else ran
— 75 minutes is roughly twice the expected cold wall clock for this row, which is dominated
by a ~2 GB CUDA download rather than by training. It was never needed; the rebuild finished
in 2 m 29 s. Instance terminated and termination verified.
