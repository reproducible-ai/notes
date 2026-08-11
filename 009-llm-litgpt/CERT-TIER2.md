# 009 — litgpt (pretrain) · tier-2 certification

**Result: PASS.** A cold `roar reproduce --lineage --run --no-puts` on a freshly
launched host that had never seen this row exited **0** with **Steps run: 4/4**,
installed **62/62 recorded pins exactly**, and produced the same checkpoint and
the same validation loss as the capture.

| | |
|---|---|
| DAG hash | `3b9c6606967c1008bc75ef5d5c83b8df4e6ea6183967eaee596329e324f47647` |
| supersedes | `314f1eb9acbf26076c12b6893c1efc8e83f1b36f70034a7d8a0ceeb496b51403` |
| `roar --version` | `roar, version 0.4.4rc5` |
| wheel sha256 | `ed35ed6bda3b5698ab65a887e7390c2ac073123f6d94bfa27b8282285352219c` |
| wheel | `roar_cli-0.4.4rc5-cp310-abi3-manylinux_2_34_x86_64.whl` (TestPyPI) |
| exit code | **0** |
| `Steps run` | **4/4** |
| manifest diff | **62/62 EXACT** — 0 missing, 0 mismatched, 94 installed |
| recorded interpreter | Python 3.12.10 |
| rebuild venv interpreter | Python 3.12.10 |
| git commit rebuilt | `fe35987736e1163a6f91b7e67e64527f4c12dd1e` |
| instance | `i-0815b13f0beaa5171`, g4dn.xlarge (1× Tesla T4), us-east-2 |
| AMI | `ami-0f07f1a0b382b48f7` |
| wall clock | 01:16:56 → 01:38:59 UTC = 22m03s billed; the rebuild itself ~2m30s |
| spend | ~$0.19 at $0.526/h |
| watchdog | `shutdown -h +60` — expected ~23 min end to end (bootstrap + rebuild + evidence), ceiling set above 2× |
| terminated | yes, verified by `describe-instances` |

## The three mandatory identity lines

```
=== WHEEL SHA256 ===
ed35ed6bda3b5698ab65a887e7390c2ac073123f6d94bfa27b8282285352219c  /tmp/roar_cli-0.4.4rc5-cp310-abi3-manylinux_2_34_x86_64.whl
/tmp/roar_cli-0.4.4rc5-cp310-abi3-manylinux_2_34_x86_64.whl: OK

=== ROAR IDENTITY ===
/usr/local/bin/roar
roar, version 0.4.4rc5

=== TRACER ARTEFACTS (P0-10) ===
libroar_tracer_preload.so
roar-proxy
roar-tracer
roar-tracer-ebpf
roar-tracer-preload
roard
```

The P0-7 verification sweep (`find` for `roar_cli-*.dist-info`, `roar_inject.pth`
and stray `roar` binaries, run *after* the purge and *unpiped*) returned **empty**.

## P0-14 — roar under the recorded interpreter, and the venv closure

roar was installed with
`uv tool install --python 3.12.10 --force --with huggingface-hub <wheel>`, so
roar's own interpreter and the child's are the same:

```
=== interpreter roar runs under ===
#!/root/.local/share/uv/tools/roar-cli/bin/python
$ /root/.local/share/uv/tools/roar-cli/bin/python -V
Python 3.12.10
```

The rebuild venv:

```
=== pyvenv.cfg ===
home = /usr/local/bin
implementation = CPython
uv = 0.12.3
version_info = 3.12.10
include-system-site-packages = false

$ .venv/bin/python -V
Python 3.12.10
```

`sys.path` of the venv interpreter — **no `dist-packages`, no `/opt/pytorch`**:

```
(empty)
/usr/local/lib/python312.zip
/usr/local/lib/python3.12
/usr/local/lib/python3.12/lib-dynload
/root/reproduce/litgpt/.venv/lib/python3.12/site-packages
```

The three `/usr/local/lib/python3.12*` entries are the uv-provisioned CPython
3.12.10's own stdlib, not a host site-packages; the venv's site-packages is the
only package root, and `include-system-site-packages = false` excludes the base
interpreter's anyway. Spot-checked resolution:

```
torch      2.7.0+cu126  /root/reproduce/litgpt/.venv/lib/python3.12/site-packages/torch/__init__.py
lightning  2.6.5        /root/reproduce/litgpt/.venv/lib/python3.12/site-packages/lightning/__init__.py
```

No `PYTHON VERSION MISMATCH` warning was emitted (grep count: 0), which is the
expected outcome once `uv` is present.

## Manifest diff — 62/62 EXACT

Per the brief, **`pip freeze` was NOT used** — the reproduce venv is
uv-provisioned and ships no `pip`, so it would return empty and read exactly like
"nothing installed". Two independent enumerations were taken and required to
agree:

```
$ uv pip freeze --python .venv/bin/python        →  94 lines
$ .venv/bin/python -c "import importlib.metadata as m; print(len(list(m.distributions())))"
                                                 →  94
```

Diffed against the recorded manifest (the union of
`jobs/<uid>.metadata.packages.pip` across the five job records, 62 pins):

```
RECORDED pins : 62
INSTALLED     : 94
MISSING       : 0 []
MISMATCHED    : 0 []
VERDICT       : EXACT 62/62
extras (transitive closure): 32
```

roar's own log agrees: `Installing 62 packages from provenance...` →
`Installed 94 packages`. Key pins landed as recorded:

```
huggingface-hub==0.36.2   lightning==2.6.5      lightning-utilities==0.15.3
litdata==0.2.59           torch==2.7.0          torchmetrics==1.9.0
torchvision==0.22.0
```

`litgpt` itself is **absent** from the freeze, which is correct — the recipe
installs its dependencies with `pip install -e .` and then uninstalls litgpt, so
no editable self-distribution is recorded (trap ①).

## Steps

```
Running 4 pipeline step(s)...

[Step 1/4]  roar run python -m litgpt download EleutherAI/pythia-14m --tokenizer_only true   Success
[Step 2/4]  roar run curl -fsSL --create-dirs -o data_train/... -o data_val/...              Success
[Step 3/4]  roar run python -m reproduction.prepare_data ...                                 Success
[Step 4/4]  roar run python -m litgpt pretrain pythia-14m ... --logger_name csv ...          Success

==================================================
Reproduction Complete
==================================================
Repository: /root/reproduce/litgpt
Steps run: 4/4
EXITCODE=0
```

## Artefacts — size **and** sha256

| file | bytes | sha256 |
|---|---|---|
| `out/final/lit_model.pth` | 168,905,183 | `a4154cdce0982c02f1ff301eaecce92fd6ecc5c11f4419ca3521aaaf7091721b` |
| `out/final/model_config.yaml` | 1,126 | `8c32a15c1813f8c9299ca1877764ada60802e3b12cfeb4a011708ff82a894a96` |
| `out/final/hyperparameters.yaml` | 684 | `3353de1b8765d426788743fa985e8230b183603d3555ddab93c142555de4483b` |
| `out/logs/csv/version_0/metrics.csv` | 1,560 | `6a1f023544a18194887d5051a70cc594d09f3cb6db0832a544e4e8d1744fb67b` |

`out/final/` also carries `config.json`, `generation_config.json`,
`tokenizer.json` (2,114,042 B) and `tokenizer_config.json`.

**Metric recomputed, and identical to the capture:**

```
Final evaluation | val loss: 9.738 | val ppl: 16948.362
```

and from `metrics.csv`, `val_loss = 9.737926483154297`,
`val_ppl = 16948.36220649061`. The full loss trajectory also matches the capture
line for line (10.979, 10.681, 10.269, 10.465, 9.950, 10.128, 9.872, 9.884).

## Two caveats, stated rather than smoothed over

**1. `lit_model.pth` is not byte-stable across runs, and three sizes are now on
record for identical weights:**

| run | bytes | sha256 |
|---|---|---|
| this capture (published to HF) | 168,905,311 | `6eff054e0e964d76bf9548891fbe65b6f22251e9df4309d8edc04893cdb3f724` |
| this cold rebuild | 168,905,183 | `a4154cdce0982c02f1ff301eaecce92fd6ecc5c11f4419ca3521aaaf7091721b` |
| the 2026-08-07 rebuild of the superseded record | 168,905,247 | *(not recorded — sizes only)* |

A spread of 128 bytes across ~169 MB. **The tensors are demonstrably identical**:
the loss trajectory matches line for line and the final val loss agrees to all 16
recorded digits (`9.737926483154297`). What varies is the pickle/zip container
metadata that `torch.save` writes around them — litgpt checkpoints the whole
training state, including a hyperparameters mapping carrying `PosixPath` objects.

This is byte-drift in a *generated* artefact, which the campaign's semantic frame
explicitly does not treat as a defect: we claim **reproduce**, not **replicate**.
It is recorded rather than waved away because rows 004 and 006 hit exactly this
and could not settle it — they had recorded sizes with no hashes. Both of this
row's figures now carry a sha256, so the next run compares hashes instead of
re-opening the argument.

**2. `python` does not exist on this AMI — only `python3`.** Recorded before the
run:

```
PRE-RUN python: ABSENT | python3: /usr/bin/python3
```

Every recorded step is `python -m ...`, and they all succeeded, which means the
reproduce venv really is being activated and really is supplying `python`. That
is the desired evidence. **No symlink or alias was created** — doing so would
have manufactured a pass and destroyed the only signal that distinguishes "the
venv is in use" from "the host's packages are in use".

## Tier-1 pre-flight (free, before any spend)

```
Tier-1 bar — 3b9c6606967c1008 · reproducible-ai/litgpt
  [✅] clean-dag    Clean-DAG check — 13/13 passed  ·  3b9c6606967c1008 · 5 jobs (published DAG)
  [✅] ai-bom       AI-BOM score: 100/100  ·  profile: Advanced
  [✅] public-urls  RESULT: ALL PUBLIC
  [✅] freeze       RESULT: PORTABLE

RESULT: REPRODUCIBLE RECORD — tier 1 complete
```

Import-vs-freeze audit (the discriminator that a low pin count is *not*):

```
pins= 62   Tier-A missing = none   Tier-B missing = 0   verdict = THICK
```

Identical to the superseded record — this re-capture did not thin the freeze.
