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
| Tracer artefacts | `site-packages/roar/bin/` — 6 files (`libroar_tracer_preload.so`, `roar-proxy`, `roar-tracer`, `roar-tracer-ebpf`, `roar-tracer-preload`, `roard`) — not a P0-10 tracerless wheel |
| Tracer selected | eBPF (capture used preload; instrumentation, not the artifact) |
| Instance | `i-0ded3145b761f5536`, g4dn.xlarge (1× Tesla T4, driver 580.126.09), us-east-2, `ami-0f07f1a0b382b48f7` |
| Rebuilt commit | `b7647e3a785c244c56de9ce7afeb9d17012cbc3d` (matches the record) |

Installed from TestPyPI's published rc6 artefact rather than an S3 presigned URL, which
retires P0-20 for this row: there is no per-target wheel secret in the loop, and the
digest still pins the build identity.

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

## 3. P0-14 — roar ran under the recorded interpreter, and nothing resolved from outside the venv

```
/root/.local/bin/roar            → #!/root/.local/share/uv/tools/roar-cli/bin/python
roar-cli's interpreter           → Python 3.12.10
.venv/bin/python                 → Python 3.12.10
                                   → /root/.local/share/uv/python/cpython-3.12.10-linux-x86_64-gnu/bin/python3.12
recorded interpreter (record)    → 3.12.10
```

roar was installed with
`uv tool install --python 3.12.10 --force --with huggingface-hub <wheel>` and symlinked
to `/usr/local/bin/roar` so the nested `roar run` in each recorded step resolves (the
exit-127 failure mode). `huggingface_hub 1.27.0` is present (P0-19).

Three stale roar installs and both `roar_inject.pth` files were purged before install
(P0-7); the removal was run unpiped and the `find` verification sweep afterwards
returned **empty**, with no `roar` on PATH until the clean install.

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
NVIDIA driver bundle (all three dated 27 Apr, outside apt). The 13 libraries that *were*
recorded — `libx11-6`, `libxext6`, `libglib2.0-0` and the rest — are all genuinely
dpkg-owned. So roar's OS layer is dpkg-shaped: it resolves a loaded `.so` to its owning
package, and when no package owns the file it drops the dependency **silently**, with no
"unowned file" entry to signal the gap. No amount of care during capture would have put
`libgl1` in this record, because `libgl1` was never installed on the capture host either.

Practical consequence, unchanged: on a bare image without a driver-installed libglvnd,
`import cv2` fails at import of the training script and the record gives the rebuilder no
pointer to what is missing. This is the pip-closure boundary (P1-11) one layer down —
the closure of a *pip* wheel reaches into system libraries a freeze cannot express, and
the OS record that is supposed to cover that gap can only name things apt knows about.
Worth a defect: **record unowned `.so` dependencies by path when dpkg resolution fails,
rather than dropping them.**

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

The check itself is sound and should not be relaxed — it exists because a LeRobot capture
recorded 10 packages for a step that needed 74, and it is exactly the kind of tier-2
killer every other gate misses. It is simply blind to the legitimate case of a
**stdlib-only step**, where "packages ⊆ roar's closure" is the correct answer rather than
a symptom. The rebuild settles it empirically: step 1 ran on a cold host, from a
9-package environment, and exited 0 in 50.1 s.

Suggested refinement, so the check keeps its teeth without this false positive: when a
step's packages are a subset of roar's closure, parse the imports of the script named in
its argv; flag only if that script imports something outside the standard library. The
DAG already carries the commit and the argv needed to do it.

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
  was re-verified on the host immediately before install (P1-7).

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
