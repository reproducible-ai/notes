# Tier 1 — capture evidence · row 007 lerobot · re-capture on roar `0.4.4rc2`

**This is not a tier-2 certification.** No cold `roar reproduce --lineage --run` has been
executed against this lineage. Everything below inspects the *record* plus one
locally-executed subset of it. The row's `row.json` still carries `"verified": false`.

This row was re-captured as the campaign's spot check on roar **#274** (P0-18): it was the
worst observed thin-freeze case, so it gives the clearest signal.

| | |
|---|---|
| DAG (attributed) | `cc490321bbbf07fd270c8bd83d12967de0fb891d1265994c5cca134df57f0639` |
| Supersedes | `023d15ffb248254a2955d46a513c57a485a78587701d43a1053819f96ad50ed8` (2026-08-07) |
| roar build | `0.4.4rc2`, installed from TestPyPI, wheel sha256 `3677618d4c42d66143baf42912c8ed932f9706d5511d032bb2898fda6a465471` |
| Fork commit | `b1d01f8c4ce4065915379280a3c50e884670061a` |
| Target / AMI | `e4d609eb` `reproai-g6e1x-plaintorch-b` · `ami-0f07f1a0b382b48f7` · g6e.xlarge, 1×L40S |
| Job / TR | `0e8306b5-157e-4a9a-b1a9-67c2e3a6061c` / `c2d774be-39cb-4015-b8f6-cb91c8e31254` |
| Result | **13/13 clean-DAG · BOM 100/100 · URLs all public · freeze PORTABLE (`--check-pypi` + `--solve`)** |
| Spend | ≈ $0.47–0.78 |

```
Tier-1 bar — cc490321bbbf07fd · reproducible-ai/lerobot-act
  [OK] clean-dag    Clean-DAG check — 13/13 passed  ·  cc490321bbbf07fd · 4 jobs (published DAG)
  [OK] ai-bom       AI-BOM score: 100/100  ·  profile: Advanced
  [OK] public-urls  RESULT: ALL PUBLIC
  [OK] freeze       RESULT: PORTABLE

RESULT: REPRODUCIBLE RECORD — tier 1 complete
```

---

## 1. The headline: 57 → 80 pins, Tier-A misses zero

| step | pins on `023d15ff` (0.4.4.dev0 @ `c5c553b`) | pins on `cc490321` (0.4.4rc2) |
|---|---|---|
| `@1 fetch_dataset` | **2** — `brotli`, `zstandard` | **23** |
| `@2 train` | — | 79 |
| `@3 evaluate` | — | 73 |
| union across the lineage | **57** | **80** |

Every package the delta named as missing is now present:

| package | `023d15ff` | `cc490321` |
|---|---|---|
| `huggingface_hub` | absent | **1.25.1** |
| `tqdm` | absent | **4.67.3** |
| `typing_extensions` | absent | **4.15.0** |
| `packaging` | absent | **25.0** |
| `PyYAML` | absent | **6.0.3** |
| `certifi` | absent | **2026.4.22** |
| `filelock` | absent | **3.29.0** |
| `fsspec` | absent | **2026.2.0** |

Also absent from the record, correctly: `roar-cli` (P0-11), `lerobot` (P0-12 / the
egg-info trap), and every `sagemaker-*` package (see §4).

### `tools/imports_vs_freeze_audit.py`, re-run

`007b` is this capture; `007` is kept alongside it so the before/after is one table.

```
001 cleanrl    pins= 69  A-miss=[]  B-miss=2
002 nanogpt    pins= 24  A-miss=['tqdm', 'typing-extensions']  B-miss=7
003 mingpt     pins= 43  A-miss=[]  B-miss=3
004 dcgan      pins= 45  A-miss=[]  B-miss=3
006 wgan-gp    pins= 45  A-miss=[]  B-miss=3
007 lerobot    pins= 57  A-miss=['huggingface-hub', 'tqdm', 'typing-extensions']  B-miss=7
007b lerobot   pins= 80  A-miss=[]  B-miss=0
008 diffusers  pins= 85  A-miss=[]  B-miss=0
009 litgpt     pins= 62  A-miss=[]  B-miss=0
```

**Tier-A misses: 0. Tier-B misses: 0. Verdict THICK.** Row 007 moves from the worst
result in the table to a clean one, alongside 008 and 009.

The usual caveat still applies and is worth repeating: the audit only finds gaps it
knows to look for. "No detected miss" is not "verified complete".

---

## 2. Executed evidence — the download step now installs closed

The audit reads the record. This runs it. All three of the following were executed on a
CPU box against a **fresh clone** of the fork, with `PYTHONPATH` unset.

**(a) The new record, installed CLOSED (`--no-deps` — exactly the 23 recorded pins, no
resolver help at all):**

```
$ uv venv --python 3.12.10 .venv-closed
$ uv pip install --python .venv-closed/bin/python --no-deps -r fetch_dataset.pins.txt
$ .venv-closed/bin/python -c "import importlib.metadata as m; print(len(list(m.distributions())))"
23
$ cd clone && env -u PYTHONPATH ../.venv-closed/bin/python repro/fetch_dataset.py \
      --repo-id lerobot/pusht_image --out-dir ../data_check2
  ...
  total bytes: 31621889
EXIT=0
```

**(b) The previous record, same treatment:**

```
$ uv pip install --python .venv-old/bin/python --no-deps -r fetch_dataset.OLD.pins.txt   # brotli, zstandard
$ cd clone && env -u PYTHONPATH ../.venv-old/bin/python repro/fetch_dataset.py ...
Traceback (most recent call last):
  File ".../repro/fetch_dataset.py", line 18, in <module>
    from huggingface_hub import snapshot_download
ModuleNotFoundError: No module named 'huggingface_hub'
EXIT=1
```

That is the P0-18 harm made concrete. The earlier record for this step was not merely
*thin*; taken on its own terms it was **unrunnable**. It survived only because a rebuild
installs the union of the lineage's pins and lets the resolver supply the rest.

**(c) The same 23 pins installed WITH transitive resolution** — for completeness, since
that is what a rebuild actually does — also exits 0, and pulls in six packages the record
does not pin: `cffi`, `fsspec`, `markdown-it-py`, `mdurl`, `packaging`, `pycparser`. All
six are genuine transitives of pinned packages (`cffi`/`pycparser`←`cryptography`,
`markdown-it-py`/`mdurl`←`rich`, `fsspec`/`packaging`←`huggingface_hub`), and `fsspec` and
`packaging` **are** recorded elsewhere in the lineage, so the row-level audit sees them.
Worth noting only because it shows the audit's union view can hide a per-step gap.

---

## 3. ⚠ The stated root cause does not hold on this host

**#274 is in the artefact and the row is fixed — but `dist-packages` cannot be the
mechanism here.** This is the finding I would most want challenged.

P0-18's root cause is recorded as: roar's freeze pass matched only `site-packages`, so
packages under the AMI's system `dist-packages` were dropped. #274 adds `dist-packages`
to `_PACKAGE_ROOT_MARKERS`, which is present and correct in the rc2 wheel:

```python
# roar/execution/runtime/inject/tracker.py
_PACKAGE_ROOT_MARKERS = ("site-packages/", "dist-packages/")
```

But the workload interpreter on this AMI **has no `dist-packages` root at all**. Measured
in-run, in the untraced setup stage, by `repro/substrate_probe.py`:

```
=== package roots visible to this interpreter ===
executable: /opt/pytorch/bin/python
   312  /opt/pytorch/lib/python3.12/site-packages   [site-packages]

=== distributions under the system root(s) ===
  (none -- this interpreter has no dist-packages root)
```

One root, 312 distributions, all under `site-packages`. Independently corroborated by the
setup stage's own gate (`freeze audit: 312 distributions`) and by the recorded runtime
(`python 3.12.10`, matching the probe's interpreter). The AMI (`ami-0f07f1a0b382b48f7`)
and the compute target are the same ones the 2026-08-07 capture used, so the layout was
the same then.

`brotli` and `zstandard` — the only two packages the earlier capture kept — are in that
same single `site-packages` root today. The explanation on record ("they survived because
the download pulled them into the venv, everything else lived in `dist-packages`") cannot
be right if there is no `dist-packages` for anything to live in.

**So: the fix is real and measured, but the mechanism is not the one written down.**
Something else between `c5c553b` and `0.4.4rc2` is doing the work. I did not have the
earlier wheel on hand to diff, so I am not going to guess in an evidence file beyond
noting where I would look first: `get_installed_packages(excluded_paths)` filters out
distributions under "runtime paths", and `get_used_packages` only keeps a name that is
already in `installed_packages`. An over-broad `excluded_paths` would drop nearly
everything while leaving behind exactly the packages installed somewhere unusual — which
is the shape of the 2-pin result.

**Why this matters beyond this row.** P0-18b marks 002 as decisively thin and 001/003/004/
006 as weakly thin, all on the assumption that the cause is location-based. If the real
cause is something else, the cross-row prediction ("`filelock`/`fsspec`/`typing-extensions`
recorded on 003/008 but missing on 002/007 at identical torch/python is location-based")
loses its footing. **The re-captures are still worth doing — this row proves they help —
but the reason they help is not established.**

---

## 4. The RED case did not fire

The delta anticipated that with `dist-packages` newly visible, the AMI's `sagemaker-*`
stack might be recorded and the pin set become jointly unsatisfiable, failing loudly at
`--solve`. It did not happen, and the reason is visible:

```
=== cloud-SDK substrate INSTALLED on this host ===
  sagemaker-core==2.9.0, sagemaker-mlflow==0.3.0, sagemaker-mlops==1.9.0,
  sagemaker-schema-inference-artifacts==0.0.5, sagemaker-serve==1.9.0,
  sagemaker-train==1.9.0, sagemaker==3.9.0, transformer_engine==2.7.0,
  transformer_engine_cu12==2.7.0, transformer_engine_torch==2.7.0

=== does the workload's own import graph load it? ===
  imported: lerobot + lerobot.policies.make_policy + accelerate
  substrate modules in sys.modules: none
```

The substrate is **installed** (10 distributions) but **not loaded** by this workload's
import graph, including `accelerate`, which is the component suspected of probing for it.
The P0-13 fix's aliased-only name pass is explicitly scoped to exclude merely-probed
optional imports, and it held: `freeze_audit --check-pypi --solve` returns **PORTABLE**,
and no `sagemaker-*` pin appears anywhere in the lineage.

This is **not** evidence that P0-18c (stripping the substrate from the cert AMI) is
unnecessary. It shows the hazard is latent on this AMI and that this particular workload
does not trip it. A row whose stack does genuinely import any of it would still be
recorded and would still fail at `--solve`, correctly and loudly.

---

## 5. Build identity

P0-20 (the `ROAR_WHEEL_URL` per-target shared secret) is **retired for this row**: the
workflow no longer declares that secret and no presigned URL is involved. The build is
installed by name and version from a public index, and identity is established by wheel
sha256 rather than by version string — four distinct builds have shipped as `0.4.4.dev0`
in this campaign, so the version string is not an identity.

`repro/verify_roar_wheel.py` asserts, on-target and before any paid step: the index
publishes exactly one linux/x86_64 wheel for the version; its published digest equals the
expected one; the bytes served match that digest; and every hashed file in that wheel's
RECORD is present on disk with the identical hash. Output from the run:

```
recorded interpreter: 3.12.10
selected: roar_cli-0.4.4rc2-cp310-abi3-manylinux_2_34_x86_64.whl
  published sha256: 3677618d4c42d66143baf42912c8ed932f9706d5511d032bb2898fda6a465471
  expected  sha256: 3677618d4c42d66143baf42912c8ed932f9706d5511d032bb2898fda6a465471
  served    sha256: 3677618d4c42d66143baf42912c8ed932f9706d5511d032bb2898fda6a465471
installed RECORD: /root/.local/share/uv/tools/roar-cli/lib/python3.12/site-packages/roar_cli-0.4.4rc2.dist-info/RECORD
  wheel entries with a hash: 422
  installed entries:         424
roar wheel verification: PASS
roar, version 0.4.4rc2
```

The two extra installed entries are the generated console scripts, which the wheel does
not carry — hence an entry-wise subset comparison rather than byte equality of RECORD.

The P0-14 workaround is applied and is now derived rather than hard-coded: the interpreter
version is read off the workload's own `python` (`3.12.10`) and passed to
`uv tool install --python`, so it cannot drift from the recorded interpreter.

**One correction to the prescribed install command.** As written it fails:

```
uv tool install --python <v> --force --with huggingface-hub \
    --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ \
    roar-cli==0.4.4rc2

  x No solution found: Because there is no version of roar-cli==0.4.4rc2 ...
  hint: `roar-cli` was found on https://pypi.org/simple/, but not at the requested version
```

uv gives `--extra-index-url` **priority over** `--index-url`, and its default first-match
strategy then locks `roar-cli` to the main index, where this version does not exist.
`--index-strategy unsafe-best-match` is required. Caught locally before launch, at no
cost. The sha256 verification above is what makes that strategy safe to use.

Two other fixes confirmed present in the artefact rather than taken from the release note:
`integrations/wandb_trackio.py` sets `mod.__spec__ = ModuleSpec("wandb", loader=None)`
(P0-15), and `huggingface-hub>=0.20.0` is a real `Requires-Dist`, not `extra == 'dev'`
(P0-19).

---

## 6. What is still unproven

- **No cold rebuild.** Tier 2 is untouched. The only executed evidence here is step `@1`
  in isolation on a CPU box; `train` and `evaluate` were not rebuilt from their recorded
  pins.
- **The per-step sets are not all closed.** `fetch_dataset` is. `train` (79) and
  `evaluate` (73) were checked only by `freeze_audit --solve`, which proves the set
  *resolves*, not that it is *sufficient*.
- **"No detected miss" is not "complete".** The audit's Tier-A list is measured for
  `import torch`; it cannot know what else this workload touches.
- **The mechanism behind the fix is not established** (§3), which means the campaign's
  model of P0-18 predicts less than it appears to.
