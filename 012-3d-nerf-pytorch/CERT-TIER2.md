# Row 012 — NeRF / nerf-pytorch · Tier-2 certification (cold rebuild)

**Result: PASS.** A host that had never seen this row rebuilt the lineage from the
published record alone: exit **0**, **Steps run: 3/3**, every recorded pin matched
exactly, and every recorded output artefact was regenerated.

The certifier was deliberately a stranger to the row: it was given the DAG hash and the
row name and worked from the published fork, the published DAG and the published notes.
It did not read the capture agent's working directory.

---

## 1. Identity of the build under test

| | |
|---|---|
| DAG | `0c119a28e8d9d48dc2fa9ec8714a266109bd45dce6b2e70527fa6b2772d5fd3e` |
| `roar --version` | `roar, version 0.4.4rc6` |
| Wheel | `roar_cli-0.4.4rc6-cp310-abi3-manylinux_2_34_x86_64.whl` |
| Wheel sha256 | `c7115b748886259b6a089e547404376acf84c3b81b4cbc8dc5610490ebea7199` (verified on the host before install; the version string alone cannot distinguish builds) |
| Tracer artefacts | `site-packages/roar/bin/` — 6 files (`libroar_tracer_preload.so`, `roar-proxy`, `roar-tracer`, `roar-tracer-ebpf`, `roar-tracer-preload`, `roard`) — a wheel built without them installs and reports a correct version while containing no tracer at all, so this is checked rather than assumed |
| Tracer selected | eBPF (capture used preload; instrumentation, not the artifact) |
| Instance | `i-0ded3145b761f5536`, g4dn.xlarge (1× Tesla T4, driver 580.126.09), us-east-2, `ami-0f07f1a0b382b48f7` |
| Rebuilt commit | `b7647e3a785c244c56de9ce7afeb9d17012cbc3d` (matches the record) |

Installed from the published rc6 artefact on TestPyPI rather than from a presigned build
URL, so no per-target secret sits in the loop; the digest above, not the filename or the
version string, is what pins the build identity.

## 2. The command, and the exit code read from a file

```
roar reproduce 0c119a28e8d9d48dc2fa9ec8714a266109bd45dce6b2e70527fa6b2772d5fd3e \
  --lineage --run --no-puts -y --step-timeout 21600
```

Detached with `setsid` (not `nohup`), exit code written to `/tmp/cert.exit`:

```
$ cat /tmp/cert.exit
0
$ grep "Steps run:" /tmp/cert.log
Steps run: 3/3
```

`3/3`, not `4/4`, is correct: the DAG's fourth job is the `roar put`, which `--no-puts`
suppresses by design. All three producing steps report `Success`; the log contains no
`Traceback`, no `ModuleNotFoundError`, and no `PYTHON VERSION MISMATCH`.

Per-step wall clock, from roar's own accounting:

| Step | Command | Time |
|---|---|---|
| 1 | `python repro/fetch_example_data.py --out-dir data` | 50.1 s (exit 0) |
| 2 | `python repro/train_truncated.py --train-iters 2000 --config configs/lego.txt --i_weights 2000` | 624.6 s (exit 0) |
| 3 | `python run_nerf.py --config configs/lego.txt --render_only --render_test --render_factor 8` | 20.6 s (exit 0) |

Reproduce wall-clock **12 m 17 s** (18:30:43 → 18:43:00 UTC), against the capture's
recorded 12 m 44 s.

The dataset fetch re-verified its own pinned digest on a cold host:
`expected sha256: ce4e94e031…` / `actual sha256: ce4e94e031…` over 370,385,516
downloaded bytes. The input is content-addressed, not merely URL-named, and the URL
still serves those bytes.

Training converged on the same trajectory: PSNR **21.31** at iteration 2000, against
the capture's **21.2**. (We claim reproduce, not replicate; the point is that the
metric is *computed* and lands in the same place.)

## 3. roar ran under the recorded interpreter, and nothing resolved from outside the venv

```
/root/.local/bin/roar            → #!/root/.local/share/uv/tools/roar-cli/bin/python
roar-cli's interpreter           → Python 3.12.10
.venv/bin/python                 → Python 3.12.10
                                   → /root/.local/share/uv/python/cpython-3.12.10-linux-x86_64-gnu/bin/python3.12
recorded interpreter (record)    → 3.12.10
```

roar was installed under the **recorded** 3.12.10 interpreter rather than the host's
3.10.12, so that roar and the traced child share an interpreter and host packages cannot
shadow recorded pins, and it was placed on `PATH` for the nested `roar run` each recorded
step makes. `huggingface_hub 1.27.0` was included.

The three stale roar copies on the AMI and both injection `.pth` files were purged before
installing; the removal was run unpiped and the `find` verification sweep afterwards
returned **empty**, with no `roar` on `PATH` until the clean install.

Independent evidence that the steps ran against the *recorded* freeze and not the host:
**`python` does not exist on this AMI** — only `python3` (3.10.12). Every recorded step
invokes bare `python`. All three succeeded, which is only possible from inside the
provisioned venv. Nothing was symlinked or aliased to make that happen.

## 4. Manifest diff — 34/34, EXACT

Enumerated two independent ways, as required, and they agree:

```
uv pip freeze --python <venv>/bin/python        → 56 lines
python -c "…len(list(m.distributions()))"       → 56
```

(`pip freeze` was **not** used: the venv is uv-provisioned and ships no pip, so it would
have returned empty and read as "nothing installed".)

Diffed against `jobs/<uid>.metadata.packages.pip` on the **job** record for step 3 — the
34-pin step, a superset of step 2's 33:

```
recorded pins: 34   installed in venv: 56
MATCHED EXACT: 34/34
MISSING   : NONE
MISMATCHED: NONE
DIFF IS EXACT: YES
```

The 22 extras are the expected transitive closure: 12 `nvidia-*` CUDA runtime wheels,
`triton`'s and `torch`'s support packages (`fsspec`, `jinja2`, `markupsafe`,
`setuptools`), matplotlib's (`contourpy`, `fonttools`), and `cffi`/`pycparser`.

## 5. Artefacts regenerated — size **and** sha256

All paths relative to the rebuilt repository.

| Artefact | Size (bytes) | sha256 |
|---|---|---|
| `logs/blender_paper_lego/002000.tar` | 14,352,633 | `642b424dc9a2ce222f229e249d1abf6d2a1e7b86a2de49f61e875378ddc14e9c` |
| `logs/blender_paper_lego/config.txt` | 289 | `8bccd6326560109aa66c337f3ec4fadbf06a44a5b864a4de740ef16d040886c4` |
| `logs/blender_paper_lego/args.txt` | 767 | `81bc4dd6458f936442bb28daf2ce6787fb02520a4bfa64581fa3e0d792d4b4dc` |
| `…/renderonly_test_001999/000.png` | 134 | `7c728d2863fc3db6dc242c5e611e3a9818429db590ca91f95243e2f9e58c6e44` |
| `…/renderonly_test_001999/020.png` | 134 | `7c728d2863fc3db6dc242c5e611e3a9818429db590ca91f95243e2f9e58c6e44` |
| `…/renderonly_test_001999/021.png` | 240 | `387b23a40b572e117c622aa535f02db038ef0f3110e41f2f88e2668363df7c56` |

Every output edge named in the DAG was produced. The render step wrote all 25 PNGs plus
`video.mp4` (2,276 B).

One honest discrepancy against the row's own write-up, reported rather than smoothed
over. The summary says the 25 novel views "contain only three distinct images between
them" — which matches the DAG, where the render step records exactly three distinct PNG
artefacts (`000.png`, `020.png`, `021.png`) because roar content-addresses its outputs.
On this rebuild there are **two**:

```
$ md5sum …/renderonly_test_001999/*.png | awk '{print $1}' | sort | uniq -c
     24 0b982f492ade3f8cc46772d11b3ed82f
      1 410f91616ca113ecad4ec0d0d9c3708c
```

At 1% of upstream's schedule the model is not converged, and at `--render_factor 8` the
views are 50×50; almost all of them collapse to the same near-uniform 134-byte image, and
how many survive as distinct is a property of where that run's noise landed, not of the
record. It is the same class as a metric differing between runs and is **not** a rebuild
failure — the step ran, exited 0, and produced every artefact the record names. It is
noted because the "three distinct images" sentence in `row.json`'s summary is stated as a
property of the row, and on a cold rebuild it reads two. If that observation is meant to
be a durable finding it should be phrased as what the capture run produced.

**The checkpoint's size is exactly the published one.** The artefact at
`hf://reproducible-ai/nerf-pytorch-lego/002000.tar` is **14,352,633 bytes**; the cold
rebuild produced **14,352,633 bytes**. The content hashes differ
(published `94fae5fb…`, rebuilt `642b424d…`), which is expected and is not a defect —
CUDA training is not bit-deterministic. But the byte-for-byte size agreement is a real
structural check passing: same module tree, same optimizer state, same tensor shapes and
dtypes. Recording the hash alongside the size is what makes that statement possible
instead of "probably benign".

## 6. Caveat 1 — the OpenGL packages: a recorder limitation, not a capture oversight

The record captures 13 dpkgs for the training and render steps (the X11 and glib stacks)
but not `libgl1` / `libglx0` / `libglvnd0`, while `opencv-python==5.0.0.93` loads
`libGL.so.1`, `libGLX.so.0` and `libGLdispatch.so.0`.

**This host already had the GL stack, and nothing was installed outside the recorded
environment.** `import cv2` succeeded, and so did the training step, which imports it
before parsing a single argument.

```
cv2 5.0.0  →  .venv/lib/python3.12/site-packages/cv2/cv2.abi3.so
  libGL.so.1         => /lib/x86_64-linux-gnu/libGL.so.1
  libGLX.so.0        => /lib/x86_64-linux-gnu/libGLX.so.0
  libGLdispatch.so.0 => /lib/x86_64-linux-gnu/libGLdispatch.so.0
mapped in the live process:
  libGL.so.1         -> /usr/lib/x86_64-linux-gnu/libGL.so.1.7.0
  libGLX.so.0        -> /usr/lib/x86_64-linux-gnu/libGLX.so.0
  libGLdispatch.so.0 -> /usr/lib/x86_64-linux-gnu/libGLdispatch.so.0
```

The independent finding is *why* they are missing, and it is sharper than "the capture
forgot three packages":

```
$ dpkg -S /usr/lib/x86_64-linux-gnu/libGL.so.1.7.0
dpkg-query: no path found matching pattern …
$ dpkg-query -W libgl1 libglx0 libglvnd0
dpkg-query: no packages found matching libgl1 / libglx0 / libglvnd0
```

**These files are owned by no dpkg.** They are libglvnd shipped inside the AMI by the
NVIDIA driver bundle (all three dated 27 Apr, installed outside apt). The 13 libraries
that *were* recorded — `libx11-6`, `libxext6`, `libglib2.0-0` and the rest — are all
genuinely dpkg-owned.

That reframes the caveat. An OS-package record is a list of *packages*, so it can only
describe the libraries a package manager knows about; a library installed as loose files
by a driver bundle is invisible to it, and nothing done during capture could have put
`libgl1` into this record, because `libgl1` was never installed on the capture host
either. The gap is structural, not an oversight.

The practical consequence is unchanged: on a bare image without a driver-installed
libglvnd, `import cv2` fails at import of the training script and the record does not
name what is missing. This is the row's own pip-closure finding one layer further down.
`opencv-python` is a pip package whose closure reaches out of the wheel into system
libraries that no freeze can express — and the OS-package list that is meant to cover
that gap can itself only reach as far as the package manager does. Two different
inventories, and the dependency falls through the seam between them. Anyone rebuilding
`opencv-python` workloads on a minimal base image should expect to supply the GL stack
themselves; a GPU AMI with the NVIDIA driver installed already has it, which is why this
rebuild never noticed.

## 7. Caveat 2 — clean-dag 12/13 is a genuine false positive, verified independently

The failing check is `workload_env_recorded`:

> step(s) recorded only roar's own dependency closure … @1 `python repro/fetch_example_data.py` (9 pkgs)

The capture record asserts this is a false positive because that file imports nothing
outside the standard library. **That assertion was not taken on trust.** The file was
fetched from the published fork at the recorded commit and parsed:

```
repro/fetch_example_data.py @ b7647e3a78
sha256 184b27059b1a2f7fcf6ce0d98739bdd7011514b9465fea0a454c6003baeca009

ast top-level imports : __future__, argparse, hashlib, os, pathlib, sys, time,
                        urllib, zipfile
NON-STDLIB            : NONE
dynamic / exec / subprocess constructs: NONE
```

Checked for the ways an AST scan can be fooled — `__import__`, `importlib.import_module`,
`exec`/`eval`, `subprocess`, relative imports into the repository — and there are none.
The claim holds: this step's real dependency set is empty, so a 9-package freeze is a
*complete* record of it, not a truncated one.

The check is worth keeping as it stands. A thin package list on a step that needs a fat
one is a real way for a record to look complete and still fail a rebuild, and this check
is the one that catches it. What it cannot see is the legitimate case underneath: a step
that genuinely depends on nothing, where a thin list is the *correct* answer rather than
a symptom. Distinguishing the two needs the step's source, not its package count.

The rebuild settles this instance empirically. Step 1 ran on a cold host from that
9-package environment, downloaded 370,385,516 bytes, matched its pinned digest and exited
0 in 50.1 s. Nothing was missing from it, because nothing was needed.

## 8. Guards observed

* `--pip-any-version` **not** passed. The recorded pins solved and installed as recorded.
* `--export-requirements` **never** combined with `--run` — `Steps run: 3/3` is present
  in the log, which is the only proof that anything executed.
* `--step-timeout 21600` passed explicitly; never `0`.
* `--no-puts` and `-y` both passed; no HF write was attempted and no org token was needed.
* Watchdog: `shutdown -h +75`, armed at 18:28:45 UTC before the run started, confirmed
  scheduled for 19:43:45 UTC. Set from measured expectation × 2: the row's own record
  puts the traced compute at 12 m 44 s, and the full host session (bootstrap, uv
  provisioning of a 56-package venv including torch, the run itself, and evidence
  collection) was expected at ~35 minutes; ×2 → 70, rounded to 75. The run finished
  61 minutes inside the ceiling, so it never needed extending.
* Privileged scripts were written to a per-agent unique directory, and the wheel digest
  was re-verified on the host immediately before install.

## 9. Cost

| | |
|---|---|
| Instance | g4dn.xlarge @ $0.526/hr on-demand, us-east-2 |
| Host uptime | 18:24:59 → 18:55 UTC ≈ 30 min |
| Reproduce wall-clock | 12 m 17 s |
| **Spend** | **≈ $0.27** |

Terminated and confirmed terminated by instance-ID.

---

_Certified on a host that had never seen this row, from the published fork, the published
DAG and this notes directory. Exit code read from `/tmp/cert.exit`, not inferred from the
log._
