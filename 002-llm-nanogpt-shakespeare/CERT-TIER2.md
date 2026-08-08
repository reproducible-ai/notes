# Tier 2 — cold rebuild certification · row 002 nanoGPT shakespeare_char

**Result: PASS, with a documented caveat.** A host that had never seen this row rebuilt
the lineage from the published record alone. Exit code `0`, `Steps run: 2/2`, and all
24 recorded pins present at the exact recorded version.

**The caveat, stated plainly: this row rebuilt *despite* its recorded package set, not
because of it.** The 24 recorded pins are not a closed, runnable set. The rebuild
succeeded only because `pip` pulled the genuinely-required packages in as transitive
dependencies of the 24. This was verified by direct experiment, not inferred — see
"Was the record sufficient?" below.

| | |
|---|---|
| DAG | `72ad9675f624563a018c0e76f81fea418edb268ab19002c404a793721f86fde2` |
| HF repo | `reproducible-ai/nanogpt` (read from the DAG's own `put` step) |
| roar build | `roar, version 0.4.4rc2` (TestPyPI) |
| wheel sha256 | `3677618d4c42d66143baf42912c8ed932f9706d5511d032bb2898fda6a465471` |
| wheel filename | `roar_cli-0.4.4rc2-cp310-abi3-manylinux_2_34_x86_64.whl` |
| Instance | `i-07cff20bd1931292f` · g5.xlarge · 1×A10G 23 GB · `ami-0f07f1a0b382b48f7` · us-east-2a |
| Recorded interpreter | Python 3.12.10 |
| Rebuild interpreter | Python 3.12.10 (exact match, no version-mismatch prompt) |
| Repo commit cloned | `f4ed2cc871ec4462816cdd1a61ec8083575934ed` (matches the record) |
| Date | 2026-08-08 |

## Command

```
roar reproduce 72ad9675f624563a018c0e76f81fea418edb268ab19002c404a793721f86fde2 \
    --lineage --run --no-puts -y --step-timeout 21600
```

`--pip-any-version` was **not** passed: the rebuild used the recorded pins, not
"whatever resolves today". `--no-puts` was mandatory (a cold host must not publish).

## Result

```
Reproduction Complete
Steps run: 2/2
```

Literal process exit code: **0**.

`2/2`, not `3/3`: the lineage has three jobs, and the third is the `roar put` publish
step, which `--no-puts` deliberately excludes. Both *executable* steps ran:

| step | command | result |
|---|---|---|
| 1 | `python data/shakespeare_char/prepare.py` | Success (exit 0, 3.7 s) |
| 2 | `python train.py config/train_shakespeare_char.py --compile=False` | Success (exit 0) |

Full 5000-iteration recipe, all 21 eval points. Best val loss **1.4735** at step 1750
(record: 1.4666). No `ModuleNotFoundError`, no timeout, no unsatisfiable pin, no
`PYTHON VERSION MISMATCH` prompt.

## Output artefacts (stat'd on the host before termination)

| file | bytes |
|---|---|
| `out-shakespeare-char/ckpt.pt` | **128,985,500** |
| `data/shakespeare_char/train.bin` | 2,007,708 |
| `data/shakespeare_char/val.bin` | 223,080 |
| `data/shakespeare_char/meta.pkl` | 703 |

`ckpt.pt` sha256 `955dfb202451cc0a47149102f23b67980f55f2b7017897cb024628f4031f336e`,
blake3 `8f8683e8e65f832246b4ffc2a93a90ccc660205628a90a857b82a17b804e5254`.

The size matches the published checkpoint exactly (128,985,500 B), but the digest does
**not** match the record's `f4cc9b6e…`. That is expected and is not a defect: the record
was produced on an L40S and this rebuild on an A10G, and GPU kernel selection differs
between them. We claim *reproduce* (recreate the pipeline from the recorded package
list), not *replicate* (byte-identical). Byte-identity for this row has only ever been
observed **within** a single GPU model.

## Environment verification — the check that actually decides the row

"Environment ready" proves nothing on its own, so the rebuilt venv was enumerated
(`uv pip freeze`) and diffed against the recorded manifest.

```
recorded pins (whole DAG, union of both jobs): 24
  step 1 (prepare): 15 pins
  step 2 (train):   21 pins
installed distributions in the rebuilt venv:   60

missing:    0
mismatched: 0
extras:    36
```

**24/24 exact.** Every recorded pin is present at the recorded version.

The 36 extras are the transitive closure pip computed for the 24: the 14-package
`nvidia-*` CUDA runtime stack plus `jinja2`/`markupsafe` (dependencies of `torch`),
and `huggingface-hub`, `tqdm`, `pyyaml`, `packaging`, `typing-extensions`, `filelock`,
`fsspec`, `certifi`, `idna`, `anyio`, `httpx`, `httpcore`, `h11`, `hf-xet`, `click`,
`python-dotenv`, `uvloop`, `httptools`, `websockets`, `setuptools`.

## Was the record sufficient? No — and here is the experiment

The recorded 24 omit several packages the recorded commands demonstrably load. Two
tests were run on the rebuild host.

**Test 1 — are the omitted packages actually loaded?** Importing `torch` in the rebuilt
venv, then checking `sys.modules`:

| package | in the recorded 24? | loaded by `import torch`? |
|---|---|---|
| `tqdm` | ❌ no | ✅ **yes** |
| `typing-extensions` | ❌ no | ✅ **yes** |
| `numpy` | ✅ yes | ✅ yes |
| `filelock` | ❌ no | no (lazy) |
| `fsspec` | ❌ no | no (lazy) |
| `packaging` | ❌ no | no (lazy) |
| `pyyaml` | ❌ no | no (lazy) |
| `certifi` | ❌ no | no (used by `requests` at call time) |
| `idna` | ❌ no | no (used by `requests` at call time) |

**Test 2 — do the recorded 24 run as a closed set?** A second venv was built from the
exported `recorded-requirements.txt` with `--no-deps`, so exactly the 24 pins and
nothing else were installed. Both recorded commands were then run against it:

```
python -c "import torch"                       -> exit 1
    ModuleNotFoundError: No module named 'typing_extensions'

python data/shakespeare_char/prepare.py        -> exit 1
    ModuleNotFoundError: No module named 'idna'     (raised from requests/packages.py)

python train.py config/train_shakespeare_char.py --compile=False   -> exit 1
    ModuleNotFoundError: No module named 'typing_extensions'
```

Control: the same `import torch` in the real rebuild venv (full transitive closure)
exits **0**.

**Conclusion: the recorded pin set is not closed.** Installed literally, it cannot run
either recorded step. The row rebuilds because `pip install` of those 24 also installs
their dependency graph, and that graph happens to cover the gaps.

### Which recorded pin covers each gap

`uv pip show` / `uv pip tree --invert` on the rebuilt venv:

| omitted package | pulled in by | ultimately guaranteed by |
|---|---|---|
| `typing-extensions` | `torch`, `anyio`, `gradio-client`, `huggingface-hub`, `starlette` | **`torch==2.7.0`** — a load-bearing recorded pin |
| `filelock` | `torch`, `huggingface-hub` | **`torch==2.7.0`** |
| `fsspec` | `torch`, `gradio-client`, `huggingface-hub` | **`torch==2.7.0`** |
| `certifi` | `requests`, `httpx`, `httpcore` | **`requests==2.33.1`** |
| `idna` | `requests`, `httpx`, `anyio` | **`requests==2.33.1`** |
| `jinja2` | `torch` | **`torch==2.7.0`** |
| `tqdm` | `huggingface-hub` **only** | `gradio_client==2.5.0` / `trackio==0.33.0` |
| `pyyaml` | `huggingface-hub` **only** | `gradio_client==2.5.0` / `trackio==0.33.0` |
| `packaging` | `gradio-client`, `huggingface-hub` | `gradio_client==2.5.0` / `trackio==0.33.0` |
| `huggingface-hub` | `gradio-client`, `trackio` | `gradio_client==2.5.0` / `trackio==0.33.0` |

This split is the finding worth keeping. Six of the gaps (`typing-extensions`,
`filelock`, `fsspec`, `jinja2`, `certifi`, `idna`) are underwritten by `torch` and
`requests` — pins that are genuinely part of this workload, so those gaps are stable
and would survive any re-capture.

But **`tqdm` is underwritten by nothing in this workload.** Its only path into the
environment is `huggingface-hub`, which is present only because `gradio_client` and
`trackio` are in the freeze — the experiment-tracking bridge, not nanoGPT. `tqdm` is
one of the two packages `import torch` actually loads. Remove the tracking bridge from
the recorded set and `tqdm`, `pyyaml`, `packaging` and `huggingface-hub` all leave the
closure with it.

**Verdict: this row rebuilt *despite* its record, not because of it — and the load-
bearing coincidence is an experiment-tracking dependency, which is the least stable
part of the recorded set.** The rebuild is real and the exit code is honest, but the
margin is luck. This row should be re-captured against a freeze that records the full
import closure before it is treated as evidence that a thin record suffices.

## P0-14 — did anything resolve from outside the recorded venv?

**No.** roar was installed under the recorded interpreter
(`uv tool install --python 3.12.10 …`), so roar's interpreter and the child's are the
same, and nothing was prepended onto the child's path.

```
pyvenv.cfg:  version_info = 3.12.10
             include-system-site-packages = false

sys.path of the step interpreter:
  /usr/local/lib/python312.zip
  /usr/local/lib/python3.12
  /usr/local/lib/python3.12/lib-dynload
  /root/cert-002/reproduce/nanoGPT/.venv/lib/python3.12/site-packages

torch  -> …/.venv/lib/python3.12/site-packages/torch/__init__.py   (2.7.0+cu126)
numpy  -> …/.venv/lib/python3.12/site-packages/numpy/__init__.py   (2.4.4)
sys.executable -> …/.venv/bin/python
```

The three `/usr/local/lib/python3.12*` entries are the **stdlib** of the 3.12.10 base
interpreter, not a third-party package root: `/usr/local/lib/python3.12/site-packages`
contains only `pip`, its `.dist-info`, and a `README.txt` (3 entries), and it is not on
`sys.path` at all. The host's own package roots — `/usr/local/lib/python3.10/dist-packages`
(host python is **3.10.12**) and `/opt/pytorch/lib/python3.12/site-packages` — appear
nowhere on `sys.path`.

Corroborating: **the host has no bare `python`** (`command -v python` → none; only
`/usr/bin/python3` at 3.10.12), yet both recorded steps invoke `python …` and both ran.
The venv demonstrably supplied the interpreter. Nothing was symlinked or aliased to make
this work.

## Substrate hygiene

The AMI ships stale roar installs, all purged before installing 0.4.4rc2 (a pre-purge
`roar --version` reported **0.4.0**):

```
removed: /usr/local/lib/python3.10/dist-packages/roar_cli-0.4.0.dist-info  + roar/
         /opt/pytorch/lib/python3.12/site-packages/roar_cli-0.4.3.dist-info + roar/
         /usr/local/bin/roar, /usr/local/bin/roar-worker
         /opt/pytorch/bin/roar, /opt/pytorch/bin/roar-worker
         /usr/local/lib/python3.10/dist-packages/roar_inject.pth
         /opt/pytorch/lib/python3.12/site-packages/roar_inject.pth
post-purge find sweep: empty; command -v roar -> NONE
```

Then one clean install, symlinked onto PATH, version asserted **after** the symlink:

```
sha256(roar_cli-0.4.4rc2-cp310-abi3-manylinux_2_34_x86_64.whl)
  = 3677618d4c42d66143baf42912c8ed932f9706d5511d032bb2898fda6a465471   [matches]
roar --version -> roar, version 0.4.4rc2
ls …/site-packages/roar/bin/ -> 6 artefacts (libroar_tracer_preload.so, roar-proxy,
   roar-tracer, roar-tracer-ebpf, roar-tracer-preload, roard)   [tracer present]
```

## Watchdog

Ceiling set to **150 minutes** (`sudo shutdown -h +150`), with
`instance-initiated-shutdown-behavior=terminate`. Sizing: on this A10G the row was
expected at roughly 60 min end to end (the ~68 min train figure is from a T4 reference),
so ~2× expected plus bootstrap headroom. Actual run was 7 min, so the ceiling was never
approached and never needed extending. Worst-case cost bound was 2.5 h × $1.006 = $2.52,
inside the $10 NTE.

## Cost and wall-clock

| | |
|---|---|
| Instance launched | 2026-08-08 21:47:08 UTC |
| `roar reproduce` start | 21:53:47 UTC |
| `roar reproduce` end | 22:00:46 UTC |
| **Reproduce wall-clock** | **6 min 59 s** |
| Instance terminated | 22:09 UTC (~22 min total) |
| Rate | g5.xlarge on-demand $1.006/hr |
| **Estimated spend** | **~$0.38** (≈$0.37 compute + ~$0.01 EBS) |

Instance `i-07cff20bd1931292f` terminated and verified.

## Evidence files

- `cert-evidence/recorded-requirements.txt` — the 24 recorded pins, as exported by
  `roar reproduce --lineage --export-requirements`
- `cert-evidence/rebuilt-freeze.txt` — the 60 distributions in the rebuilt venv
