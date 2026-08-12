# Row 014 — S4 (permuted sequential MNIST): tier-2 certification

**Result: PASS.** A host that had never seen this row rebuilt it from the published
lineage alone, exit **0**, **Steps run: 1/1**, and regenerated the published
checkpoint **byte-for-byte**.

Certified by an independent agent that did not capture this row and did not read the
capture's working directory. Everything below was obtained from the published record
(`glaas.ai` lineage, the fork on GitHub, TestPyPI) and from the certification host.

---

## The command

```
roar reproduce fd445b9abb32632e4b3c6ca4c97a1e8a868233c4abb794d2ed94af1ce2f920b2 \
    --lineage --run --no-puts -y --step-timeout 21600
```

Run detached under `setsid`, exit code written to a file and read back:

| | |
|---|---|
| exit code (read from file, not inferred) | **0** |
| `Steps run:` | **1/1** |
| skipped | `Skipping 1 publish (roar put) step(s) [--no-puts]` — as intended |
| wall clock, `roar reproduce` start → exit | **3m39s** (01:45:11.6 → 01:48:51.0 UTC) |
| traced step itself | `roar: done · 152.4s (trace 150.8s + post 1.6s, exit 0)` |

## Substrate

| | |
|---|---|
| instance | `i-0f68f7fe6ffd635a4`, g4dn.xlarge, us-east-2a |
| AMI | `ami-0f07f1a0b382b48f7` |
| GPU | 1× Tesla T4, driver **580.126.09**, CUDA 13.0 runtime |
| host Python | 3.10.12 (`/usr/bin/python3`); **no `python` on PATH before the run** |
| roar | **0.4.4rc6** |
| roar wheel | `roar_cli-0.4.4rc6-cp310-abi3-manylinux_2_34_x86_64.whl`, sha256 `c7115b748886259b6a089e547404376acf84c3b81b4cbc8dc5610490ebea7199` |

The wheel was installed **by name and version from the published TestPyPI index**
(`roar-cli==0.4.4rc6`, `--index-strategy unsafe-best-match`), under the *recorded*
interpreter (`uv tool install --python 3.12.10`). The digest was verified before
install, and — because a version string cannot distinguish two builds — the six tracer
artefacts inside the downloaded wheel were hashed and compared to the six installed
under `site-packages/roar/bin/`. All six match:

```
f029b5050273103a64ab06710cad9abda609c1f9d5898e64eca7a8a5611b4bc0  roar/bin/libroar_tracer_preload.so
4428c8740e9fb0c81e703c1c302157625141071ef500494529011db238a79d5b  roar/bin/roar-proxy
333f1cd9778cf85bde50b0ee7a59af2c2f016f3333c7f833da96479b2b8ade7f  roar/bin/roar-tracer
6e1ad703fe740d47d56e4c7f3932784629796c0999715e8ed3f177d7625f37fd  roar/bin/roar-tracer-ebpf
047e336b753cb7507cfb3b8462cacacacca05494379ebba0cf9e27642a54a4bd  roar/bin/roar-tracer-preload
4c25fb6c9cb5ffdab086b533707710643f9c85fd2c4399afde124bc41079d86e  roar/bin/roard
```

`roar --version` → `roar, version 0.4.4rc6`, resolved from `/root/.local/bin/roar`
(symlinked to `/usr/local/bin/roar` so the nested `roar run` in the recorded step could
find it). Three pre-existing roar installations on the AMI were removed first and the
removal verified with a `find` sweep.

## The environment the rebuild produced

`Installing 104 packages from provenance` → `Resolved 134 packages in 1.82s` →
`All pip packages installed successfully`.

**Pin diff: 104/104 EXACT.** No package missing, no version mismatched.

The venv was enumerated **twice**, by two independent mechanisms that must agree:

```
uv pip freeze --python /root/reproduce/s4/.venv/bin/python      → 134 lines
.venv/bin/python -c "import importlib.metadata as m; print(len(list(m.distributions())))"
                                                                → 134
```

(`.venv/bin/python -m pip freeze` is not usable here: the venv is uv-provisioned and
ships no `pip`, so it answers `No module named pip`.)

The 30 distributions installed beyond the 104 recorded pins are the transitive closure
and nothing else: 12 `nvidia-*` CUDA libraries, `jinja2`/`markupsafe`/`networkx`/
`sympy` support for torch, `cffi`/`pycparser`, `contourpy`/`fonttools` for matplotlib,
`grpcio`/`markdown`/`werkzeug`/`tensorboard-data-server` for tensorboard,
`pyasn1`/`pyasn1-modules`, `hf-xet`, `flatbuffers`, `markdown-it-py`/`mdurl`,
`sentry-sdk`.

### The torch 2.3.0 pin self-heals

This is the row's central claim and it holds. The AMI ships torch 2.7; the record pins
`torch==2.3.0` because `src/dataloaders/lra.py` imports `torchtext` at module level and
torchtext 0.18.0's `libtorchtext.so` is ABI-incompatible with torch 2.7. The rebuild
installed the recorded stack and used it:

```
torch      2.3.0+cu121   /root/reproduce/s4/.venv/lib/python3.12/site-packages/torch/__init__.py
torchtext  0.18.0+cpu    /root/reproduce/s4/.venv/lib/python3.12/site-packages/torchtext/__init__.py
torch.cuda.is_available() → True      torch.cuda.get_device_name(0) → 'Tesla T4'
```

### The over-broad freeze installs cleanly

The recorded freeze is a superset of the import closure — 104 pins for a ~25-package
import graph. Every one of the nine packages this row never imports installed at the
exact recorded version and none of them caused a resolution failure:

`librosa==0.9.2`, `soundfile==0.14.0`, `audioread==3.1.0`, `resampy==0.4.3`,
`numba==0.65.1`, `llvmlite==0.47.0`, `tensorboard==2.21.0`, `boto3==1.42.96`,
`paramiko==4.0.0`.

**One of them is load-bearing for the output set.** `tensorboard` being importable is
what makes PyTorch-Lightning select `TensorBoardLogger` rather than `CSVLogger`, so the
metrics artefact this row produces is `events.out.tfevents.*`, not a `metrics.csv`.
That matches the recorded output list exactly. A future "cleanup" of the freeze that
dropped `tensorboard` would silently change which artefact the run emits.

### Every package resolved from inside the venv

```
sys.path[0:6] = ['', '/usr/local/lib/python312.zip', '/usr/local/lib/python3.12',
                 '/usr/local/lib/python3.12/lib-dynload',
                 '/root/reproduce/s4/.venv/lib/python3.12/site-packages',
                 '.../site-packages/setuptools/_vendor']
```

No host `site-packages`/`dist-packages` directory is on the path. Sixteen workload
packages (`torch`, `torchtext`, `torchvision`, `pytorch_lightning`, `hydra`,
`omegaconf`, `einops`, `numpy`, `scipy`, `rich`, `setuptools`, `pandas`, `sklearn`,
`torchmetrics`, `tqdm`, `PIL`) were each imported and their `__file__` checked: all 16
resolve under `/root/reproduce/s4/.venv/`, none outside.

Venv interpreter is **Python 3.12.10**, exactly the recorded version; no
`PYTHON VERSION MISMATCH` prompt fired. The host has no `python` binary at all, only
`python3` — so the recorded `python -m train` step could only have run against the
rebuilt venv, and the run would have died `exit 127` otherwise.

## Artefacts regenerated

All sizes and sha256 taken on the certification host before it was terminated.

| path | bytes | sha256 |
|---|---|---|
| `outputs/run/checkpoints/val/accuracy.ckpt` | **1,618,650** | **`00a284186647f73d00e90a9e73348a2c37f5c000975a7b4c0f65fd55e44323a1`** |
| `outputs/run/checkpoints/last.ckpt` | 1,618,714 | `dd5a22506fa690642eefe75d0d4534489ce21063e632d137e2f21edaf0f3c804` |
| `outputs/run/config_tree.txt` | 13,130 | `c71b4ecf1511bf13b78da50a3fa3025826fe7a088b00af5195909be03c25aed5` |
| `outputs/run/train.log` | 2,561 | `f56aea62a40aaa146681e1af60e037778232442a8db6fb1577d3a0b2df811a1e` |
| `outputs/run/.hydra/config.yaml` | 2,834 | `01bfa7d3a693a6224b28fb05d822509f834ff94fa32bd5a2248b2b7bad05d64a` |
| `outputs/run/.hydra/hydra.yaml` | 3,851 | `d6c4dab514f1fd8329a22647a72380d9b8fbbc854c692875f62f771b2a5450f8` |
| `outputs/run/.hydra/overrides.yaml` | 189 | `777d89a76da62ef4af6e06aa969650dddb599dc990593b83dbbef4e70ff289dc` |
| `outputs/run/lightning_logs/version_0/events.out.tfevents.…` | 41,567 | `045a55f756828a3c6013e131527361fb2f968542ea568b875c92e744147469a6` |
| `outputs/run/lightning_logs/version_0/hparams.yaml` | 62 | `caa852e0fc9308c4e7c4faaf54d1ad5b8929a9cc528ad4deb2ecaad35a44692e` |
| `data/mnist/MNIST/raw/train-images-idx3-ubyte.gz` | 9,912,422 | `440fcabf73cc546fa21475e81ea370265605f56be210a4024d2ca8f203523609` |
| `data/mnist/MNIST/raw/train-labels-idx1-ubyte.gz` | 28,881 | `3552534a0a558bbed6aed32b30c495cca23d567ec52cac8be1a0730e8010255c` |
| `data/mnist/MNIST/raw/t10k-images-idx3-ubyte.gz` | 1,648,877 | `8d422c7b0a1c1c79245a5bcf07fe86e33eeafee792b84584aec276f5a2dbc4e6` |
| `data/mnist/MNIST/raw/t10k-labels-idx1-ubyte.gz` | 4,542 | `f7ae60f92e00ec6debd23a6088c31dbd2371eca3ffa0defaefb259924204aec6` |

Every one of the 17 recorded step outputs was regenerated. The only name that differs
is the TensorBoard event file, whose filename embeds the wall-clock, hostname and PID
of the writing process by design.

### `accuracy.ckpt` is byte-identical on a third independent host

The record documents two captures on two EC2 instances producing the same checkpoint.
This certification is the third host, on a different day, from a clean install, and
lands on the same 1,618,650 bytes and the same
`00a284186647f73d00e90a9e73348a2c37f5c000975a7b4c0f65fd55e44323a1`. `train.seed: 0`
plus a deterministic S4 initialisation and the `cauchy_naive` fallback appear to be
genuinely sufficient — nothing about this needed a `--deterministic` flag.

### Metrics reproduce to five decimal places

Read back out of the regenerated event file:

| metric | rebuilt | recorded |
|---|---|---|
| val/accuracy | 0.94083 | 0.94083 |
| val/loss | 0.20117 | 0.20117 |
| test/accuracy | 0.94230 | 0.94230 |
| test/loss | 0.18875 | 0.18875 |

## Two things the published record should say and does not

1. **There is no `metrics.csv`.** `row.json` (`experimentUrlNote`) and the README both
   state that PyTorch-Lightning's `CSVLogger` writes
   `outputs/run/lightning_logs/version_0/metrics.csv` and that this file is a recorded
   step output. It is not: the recorded output list contains
   `events.out.tfevents.…` and no CSV, and the rebuild likewise produced only the event
   file. Because `experimentUrl` is `null`, that sentence is the record's *only*
   pointer to where the metrics live, and it points at a file that does not exist. The
   metrics are all present — 17 scalar series including `val/accuracy`, `test/accuracy`,
   `timer/epoch`, `train/loss` and the four gradient norms — just in TensorBoard's
   binary format, which needs `tensorboard` installed to read.

2. **The rebuild's environment install is far faster than the record's cost model
   implies.** The record attributes 3m34s to "the pinned-environment install" as a
   fixed cost. On this host the same 104 pins resolved in 1.82s and the whole
   `roar reproduce` — clone, venv, 134 packages, and the full traced training step —
   finished in **3m39s** end to end. The row's fixed-cost estimate is therefore
   conservative; the $3.50 full-run figure is if anything slightly high.

Neither affects the verdict.

## Cost

| | |
|---|---|
| instance | g4dn.xlarge @ $0.526/h on-demand, us-east-2 |
| host lifetime | 01:37:28 → 02:01 UTC ≈ 24 min |
| **spend** | **≈ $0.21** |

A `shutdown -h +75` watchdog was armed on the host before anything else was run — this
row's expected rebuild is ~6 minutes, and 75 minutes covers bootstrap, the rebuild,
evidence collection and a wide margin without ever risking an unattended GPU. It was
not needed: the instance was terminated deliberately at the end and the termination
verified with `describe-instances`.
