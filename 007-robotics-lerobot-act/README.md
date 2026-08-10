# 007 — LeRobot ACT on `lerobot/pusht_image`

**Verdict: reproduced (truncated).** Difficulty: **hard** — materially harder than a
single-file row.

`huggingface/lerobot`'s ACT policy (Action Chunking Transformer, ResNet-18 backbone)
trains end to end from published materials with **zero changes to upstream source**:
`git diff` against upstream touches 0 lines under `src/` or `tests/`. Everything the
reproduction needed was additive harness — a workflow file, four small launcher/
utility scripts under `repro/`, and `.gitignore` rules. The pipeline fetches the
public `lerobot/pusht_image` LeRobotDataset (206 episodes, 25 650 frames, 31.6 MB),
trains for **300 of the 100 000 default steps** at batch size 8 on one L40S, and then
recomputes a held-out metric from the saved checkpoint as its own step. The run is a
**pipeline-viability truncation, not a converged policy** — the published weights are
not a quality result and should not be used as one.

| | |
|---|---|
| Upstream | `huggingface/lerobot` @ `ff7cc3de1de830f5f3276918a013d04bdf9ea4be` (Apache-2.0) |
| Fork | `reproducible-ai/lerobot` @ `b1d01f8c4ce4065915379280a3c50e884670061a` |
| Dataset | `lerobot/pusht_image` (public, anonymous fetch, 31 621 889 bytes over 7 files) |
| Artifact | `hf://reproducible-ai/lerobot-act` → `model.safetensors` (207 MB, public) |
| Lineage | [`cc490321…0639`](https://glaas.ai/dag/cc490321bbbf07fd270c8bd83d12967de0fb891d1265994c5cca134df57f0639) — 4 jobs |
| Metric | held-out `eval_loss` **0.5275**, unnormalised action L1 **52.59**, over 2 742 frames / 21 held-out episodes |
| Upstream source patched | **0 lines** |

## What made this row hard

Three things, none of which appear in a single-file row.

**1. LeRobot is a framework, so it wants to be installed — and installing it is the
trap.** The documented entry point is the `lerobot-train` console script, which only
exists after `pip install -e .`. But an editable self-install is the single most
destructive thing you can do to a provenance capture: the tracer treats everything
under the editable distribution's source directory as package territory, and
`pip install -e .` registers *the whole repository* as that directory. Every read of
`data/` and `outputs/` then vanishes and the lineage lands as disconnected nodes.
The remedy is to install the dependency set and then remove the self-install —
`pip install -e ".[training]"` followed by `pip uninstall -y lerobot` — and to make
the recorded commands import `lerobot` from the checkout instead of from
site-packages. `repro/train_act.py` and `repro/evaluate_act.py` exist only to do that
`sys.path` insert *in committed code*, so a rebuild host needs no environment
variable and no install; each then calls upstream's own `main()` with upstream's own
arguments.

**2. `pip uninstall` does not undo `pip install -e .`.** This is the finding that
cost the most to pin down, and it is upstream-shaped rather than tool-shaped.
LeRobot uses a setuptools `src/` layout, so the editable install writes
`src/lerobot.egg-info/`, and **pip leaves it behind on uninstall**. That directory is
inert *until* something puts `src/` on `sys.path` — which is exactly what the fix in
(1) does. Measured directly:

```
$ python -c "import importlib.metadata as m; print(m.version('lerobot'))"
PackageNotFoundError                      # after pip uninstall, src/ not on path

$ python -c "import sys; sys.path.insert(0,'src'); \
             import importlib.metadata as m; print(m.version('lerobot'))"
0.6.2                                     # same interpreter, same moment
```

So inside the traced steps, `lerobot 0.6.2` reads as an **installed distribution**
and lands in the recorded environment. `lerobot==0.6.2` is not published on PyPI
(latest release: 0.6.1), so that one pin would have made the recorded environment
un-installable and the row un-rebuildable — while every gate that inspects the
*shape* of the record still passed. The fix is one line, but it has to run **after**
the uninstall: `rm -rf src/*.egg-info`. Verified on-target: the setup stage asserts
`lerobot distributions visible to importlib.metadata: []` with `src/` on the path,
and the published freeze contains no `lerobot` pin.

**3. Upstream's experiment logging is wandb-shaped, not wandb-*compatible*-shaped.**
LeRobot ships wandb support behind `--wandb.enable=true`, so the honest thing would be
to enable it and let it mirror to a hosted dashboard. It does not survive substitution.
`WandBLogger` is written against wandb's exact API surface rather than the subset that
wandb-API-compatible trackers implement, and it trips on three separate points — the
first two of which kill the run outright:

| where | what LeRobot does | why a substitute rejects it |
|---|---|---|
| `wandb_utils.py:110` | forwards wandb's `resume=None` default into `init()` | wandb treats `None` as "don't resume"; substitutes take only `"must"`/`"allow"`/`"never"` and raise on `None` |
| `wandb_utils.py:202` | `wandb.log(data=…, step=…)` | wandb's first parameter is *named* `data`; substitutes name it `metrics`, so the keyword form is a `TypeError` |
| `wandb_utils.py:122` | `wandb.run.get_url()`, unguarded | `get_url` is a wandb-only method with no equivalent on the substitute's `Run` |

None of this is a bug in LeRobot — it is what "we use wandb" means in practice. But it
is exactly the coupling that makes an experiment link expensive to reproduce: enabling
logging here needs *real wandb credentials on the training host*, which this campaign
declines to place there. Rather than patch upstream to suit a tracker, this row runs
with logging **off** and computes the held-out metric as its own pipeline step instead,
publishing it as `metrics/metrics.json`. See `issues.md`.

## What a full-length run costs

This row is truncated to **300 of LeRobot's own default 100 000 steps**
(`TrainPipelineConfig.steps`, `src/lerobot/configs/train.py:142`) — 0.3 %. The raw
6m01s / $0.60 of the captured run therefore answers a different question from *"what am
I in for if I rebuild this?"*, and the split matters because most of the captured run is
**fixed cost that does not scale**:

| step | duration (from the lineage) | scales with `--steps`? |
|---|---|---|
| `fetch_dataset` | 6.3 s | no |
| `train` — dataset + policy construction, and the two held-out eval passes `--eval_steps=150` triggers | 191.3 s | no |
| `train` — 300 optimizer steps at 3.72 steps/s | 80.6 s | **yes** |
| `evaluate` | 83.2 s | no |
| provisioning + setup (dependency install, environment gates) | ~150 s | no |

So **only 80.6 s of the 361.4 s traced run is variable** — 22 %. Fixed ≈ 430.8 s ≈
0.120 h ≈ **$0.22** at $1.861/h (`g6e.xlarge` on-demand, us-east-2); variable ≈
**$0.000139 per step**. A full 100 000-step run is therefore ≈ 26 882 s of optimizer
time (7 h 28 m) plus the fixed portion — **≈ 7 h 36 m and ≈ $14.12** on the same
instance.

Two caveats a reader should apply before trusting that number. It holds the *number* of
held-out evaluations at two, i.e. it assumes `--eval_steps` is scaled with the run
length; leaving `--eval_steps=150` fixed would add 666 held-out passes and roughly
double the figure. And it excludes the ResNet-18 ImageNet weight download, which is
fixed, unmetered here, and outside the captured lineage.

## Shape of the pipeline

Three traced steps, deliberately split so the dataset and the checkpoint are each
real provenance edges rather than side effects of one monolithic command:

```
fetch_dataset  →  7 files  →  train  →  9 files  →  evaluate  →  metrics.json
```

`evaluate` is not redundant with training's inline `--eval_steps`. Training's
held-out loss exists only in the log; recomputing it from the saved checkpoint in a
separate job makes the metric a first-class artifact produced by a step that
*consumes* the model. `repro/evaluate_act.py` mirrors upstream's own eval branch —
the same per-task episode hold-out rule as `make_train_eval_datasets`, the same
uint8→float image conversion, the same `loss, _ = policy(preprocessor(batch))` call —
so `eval_loss` here means what `eval_loss` means there. No simulator is involved:
this is offline behaviour-cloning error on held-out demonstrations, **not** a task
success rate.

## Reproducing it

```
roar reproduce cc490321bbbf07fd270c8bd83d12967de0fb891d1265994c5cca134df57f0639 \
    --lineage --run --no-puts
```

Held constants: roar 0.4.4rc2 · `preload` tracer · Python 3.12.10 · torch 2.7.0 ·
AMI `ami-0f07f1a0b382b48f7` · one NVIDIA L40S (46 GB) · seed 1000.

Two environment notes for anyone rebuilding:

* **`torchcodec` will warn and fall back to PyAV.** The wheel cannot load
  `libtorchcodec` without system FFmpeg (`libavutil.so.5x` missing). This is
  harmless here — `pusht_image` is an image dataset stored as parquet, so nothing is
  video-decoded — but the warning is alarming and appears in both the training and
  evaluation logs.
* **Training downloads ResNet-18 ImageNet weights** from `download.pytorch.org` at
  policy-construction time. The rebuild host needs that reachable; it is not part of
  the captured lineage.

## Re-captured 2026-08-08 — what changed, and what did not

Nothing about the recipe changed. The recorded commands, the dataset, the 300-step
truncation, the seed, the host class and the upstream base commit are all identical to
the 2026-08-07 capture; the fork moved only because the untraced setup stage now
installs its provenance tooling from a public package index instead of a presigned URL.
The metric moved from `eval_loss` 0.5362 to 0.5275, which is ordinary run-to-run
variation — this row claims *reproduce*, not *replicate*, so the claim is that the
metric is computed, not that it lands on the same number.

What did change is the completeness of the recorded environment, and it is worth
stating plainly because it is the difference between a row that rebuilds and a row that
rebuilds *by luck*:

| | 2026-08-07 | 2026-08-08 |
|---|---|---|
| pins recorded across the whole lineage | 57 | **80** |
| pins recorded for the `fetch_dataset` step | 2 (`brotli`, `zstandard`) | **23** |
| `huggingface-hub` in the record | absent | **present** (1.25.1) |
| `tqdm`, `typing-extensions`, `packaging`, `pyyaml`, `certifi`, `filelock`, `fsspec` | absent | **present** |

`fetch_dataset` is a single `huggingface_hub.snapshot_download` call, so the earlier
record was missing the one library the step exists to call. That is now checkable
rather than arguable — from a fresh clone, with `PYTHONPATH` unset:

```
# the new record, installed CLOSED (--no-deps): nothing but the 23 recorded pins
$ uv pip install --no-deps -r fetch_dataset.pins.txt && \
  env -u PYTHONPATH python repro/fetch_dataset.py --repo-id lerobot/pusht_image --out-dir /tmp/d
...
total bytes: 31621889
EXIT=0

# the earlier record, same treatment
$ uv pip install --no-deps brotli==1.2.0 zstandard==0.25.0 && \
  env -u PYTHONPATH python repro/fetch_dataset.py --repo-id lerobot/pusht_image --out-dir /tmp/d
ModuleNotFoundError: No module named 'huggingface_hub'
EXIT=1
```

The earlier row was never *wrong* about what it ran — it ran exactly what it says it
ran. It was incomplete about what that needed, and every structural check passed
anyway, because each missing package happens to be a transitive dependency of one that
was recorded. A rebuild would have installed them by resolver accident rather than by
record. The re-capture removes the accident for the download step: the 23 recorded pins
are a closed set that runs on their own.

**Update, 2026-08-08 — this row has since been certified.** The paragraph above was
written before the cold rebuild and described the state at capture time.

A complete record is a *precondition* for a rebuild, not a demonstration of one — that
distinction still holds, and it is why the record and the certification are tracked
separately. This row now has both. A cold agent rebuilt it from the published lineage:
**exit 0, 3/3 steps, 80/80 recorded pins present at recorded versions** (0 missing, 0
mismatched), with a clean venv closure — no `dist-packages` and no host `site-packages`
on `sys.path`. `row.json` carries `"verified": true` and the full evidence is in
`CERT-TIER2.md`.

One caveat survives certification and is worth stating plainly: `torchcodec` reaches
FFmpeg through `libavutil.so.*`, an **OS-package** edge that a pip freeze cannot see
(P1-11). The pip closure is complete; the closure below pip is not, and no gate we run
would catch that.

_A note on comparing pin counts: this row was captured on roar `0.4.4rc2`. Later rows
captured on `0.4.4rc3` show **fewer** pins because rc3 strips roar's own dependency
footprint from the freeze. A smaller freeze on a newer row is that fix, not a
regression — read each write-up's pin numbers against the roar version that produced
them._
