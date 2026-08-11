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
| Fork | `reproducible-ai/lerobot` @ `8cdbf8c226b80293d1692feb11cc767e1d4df531` |
| Dataset | `lerobot/pusht_image` (public, anonymous fetch, 31 621 889 bytes over 7 files) |
| Artifact | `hf://reproducible-ai/lerobot-act` → `model.safetensors` (207 MB, public) |
| Lineage | [`27064dbb…91fb`](https://glaas.ai/dag/27064dbb01d6fa6e241329f93deff5e224eba4400482790adaabf52955be91fb) — 4 jobs · 98 pins · Tier-A 0 |
| Experiment | [live dashboard](https://huggingface.co/spaces/reproducible-ai/experiments?project=lerobot-act-pusht) — upstream's own logging, 0 lines changed |
| Metric | held-out `eval_loss` **0.5294**, unnormalised action L1 **52.59**, over 2 742 frames / 21 held-out episodes |
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
LeRobot ships wandb support behind `--wandb.enable=true`. It does not survive
substitution unmodified: `WandBLogger` is written against wandb's exact API surface
rather than the subset that wandb-API-compatible trackers implement, and it trips on
three separate points — the first two of which kill the run outright.

| where | what LeRobot does | why a substitute rejects it |
|---|---|---|
| `wandb_utils.py:110` | forwards wandb's `resume=None` default into `init()` | wandb treats `None` as "don't resume"; substitutes take only `"must"`/`"allow"`/`"never"` and raise on `None` |
| `wandb_utils.py:202` | `wandb.log(data=…, step=…)` | wandb's first parameter is *named* `data`; substitutes name it `metrics`, so the keyword form is a `TypeError` |
| `wandb_utils.py:122` | `wandb.run.get_url()`, unguarded | `get_url` is a wandb-only method with no equivalent on the substitute's `Run` |

None of this is a bug in LeRobot — it is what "we use wandb" means in practice. For
this row's first three captures it meant no experiment link at all: not merely missing,
but impossible without patching upstream, which would have cost the zero-lines-changed
property that makes the row worth reading.

All three gaps are now bridged, so **the logging upstream already shipped is simply
switched on** — three of its own flags, no source change:

```
--wandb.enable=true --wandb.project=lerobot-act-pusht --wandb.disable_artifact=true
```

The third flag is not cosmetic. With logging on, `log_policy()` calls
`wandb.log_artifact()` at every checkpoint save and the tracker implements it for real,
so without the flag the run would push the 207 MB `model.safetensors` to the dashboard
on each save. `log_policy()` returns early when it is set (`wandb_utils.py:126`).

### The part that would have passed capture and failed every rebuild

This is the finding worth carrying to any other row that wants a link.

The bridge decides what to do from an environment variable, `TRACKIO_SPACE_ID`. Set, it
aliases `wandb` to the real tracker, whose `Run` has `get_url()`. Unset — which is every
credential-free rebuild host — it aliases `wandb` to a silent no-op stub whose `Run`
implements only `summary`, `config`, `id`, `name`, `log`, `finish`, `watch` and
`log_code`. **No `get_url`.** And LeRobot calls `wandb.run.get_url()` unguarded during
logger construction, before training step 1.

A tracked run records **argv only**. So exporting that variable on the line above the
command — the obvious thing to do — produces a run that succeeds at capture and dies on
every rebuild with:

```
AttributeError: '_Run' object has no attribute 'get_url'
```

Nothing warns about it. The capture is green, the gates are green, and the row is
un-rebuildable. Both branches were checked against the installed bridge before any GPU
was booked, which is why this row never spent money on that failure.

The fix is to put the assignment **inside** the recorded command, so the requirement
travels with the lineage:

```
roar run -n train --wandb-to-trackio -- env TRACKIO_SPACE_ID=… python repro/train_act.py …
```

`env` is `exec`, not a shell, so the tracer keeps its view of the Python process —
measured identically (`in:0 out:1`) for `env VAR=v python probe.py` and bare
`python probe.py` — and the replay does not rewrite `argv[0]`, so the `python` that
`env` resolves is still the recorded interpreter. The cold rebuild that certified this
row exercised exactly that path.

### Verifying the link, given that a 200 proves nothing

The dashboard is a Gradio app and returns **HTTP 200 for any query string**, and the
tracker writes its space id to its own database even when sync fails — so a run that
logged nothing still publishes a link that 200s. Four checks were used instead: the
traced child logged that the bridge took the real-tracker branch rather than the stub;
the upload token was asserted present in the task environment before any paid step; a
deliberately token-less control run of the same code path is loud about failure and
none of its warnings appear here; and the backing store's own `updatedAt`
(01:51:04 UTC) lands three seconds after this run flushed. A held-out `evaluate` step
still publishes `metrics/metrics.json`, so the metric never depends on the dashboard
being reachable. See `issues.md`.

## What a full-length run costs

This row is truncated to **300 of LeRobot's own default 100 000 steps**
(`TrainPipelineConfig.steps`, `src/lerobot/configs/train.py`) — 0.3 %. The raw
5m59s / $0.57 of the captured run therefore answers a different question from *"what am
I in for if I rebuild this?"*. Every term below is **measured**, on two separate hosts;
the previous version of this section carried two caveats and both have now been closed
by measurement rather than argument.

| component | measured | scales with `--steps`? |
|---|---|---|
| cold start: clone + venv + install of all 98 recorded pins | 44.0 s | no |
| `fetch_dataset` | 4.5 s | no |
| `train` — imports, dataset + policy construction, checkpoint save, tracker flush | 24.3 s | no |
| `train` — ResNet-18 ImageNet backbone download (46 830 571 B) | 0.34 s | no |
| `train` — 300 optimizer steps at `step_s` 0.264 s/step | 79.2 s | **yes** |
| `train` — 2 held-out eval passes at 82 s | 164 s | **yes, via `--eval_steps`** |
| `evaluate` | 83.0 s | no |

The cold-start figure comes from this row's **own cold rebuild on a fresh host**, not
from the capture host's provisioning, because that is the path a reader actually takes:
`roar reproduce --script`, edit out the truncation, run.

**Fixed** = 155.8 s = 0.0433 h = **$0.08** at $1.861/h (`g6e.xlarge` on-demand,
us-east-2). **Variable** has two terms, and this is the part earlier estimates for this
row got wrong:

- the optimizer loop, `step_s` 0.264 s/step — 100 000 steps = 26 400 s;
- the held-out eval pass, 82 s, which `--eval_steps=150` fires
  `floor(100000/150) = 666` times = 54 612 s.

**Total ≈ 81 168 s ≈ 22 h 32 m ≈ $41.96**, i.e. $0.000 419 per step.

That is nearly three times the figure this row used to publish, and the reason is worth
stating plainly, because it is the same class of error as multiplying a headline that is
mostly download. The **eval term is larger than the training term**. It is also a
property of *this recipe*, not of LeRobot: upstream's own default is `eval_steps=0` —
no held-out passes at all — and `--eval_steps=150` was added here purely so that a
300-step run would still compute a metric. Restore that default and the same 100 000
steps cost **26 556 s ≈ 7 h 23 m ≈ $13.73**.

Both numbers are published because the reader's edit determines which one applies:
changing only `--steps=300` to `100000` gives $41.96; also restoring `--eval_steps` to
its upstream default gives $13.73. The earlier $14.12 estimate quietly assumed the
second while describing the first.

The ResNet-18 download was previously excluded as an unquantified caveat. ACT's default
backbone is `resnet18` with
`pretrained_backbone_weights="ResNet18_Weights.IMAGENET1K_V1"`
(`configuration_act.py:98-99`), so first policy construction fetches
`resnet18-f37072fd.pth` from `download.pytorch.org`. The workflow now times that fetch
into a throwaway `TORCH_HOME`, so the real cache stays cold and the train step still
pays what a fresh machine pays; the probe only *sizes* the component. It is **0.34 s** —
negligible, and now counted rather than waved at.

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
roar reproduce 27064dbb01d6fa6e241329f93deff5e224eba4400482790adaabf52955be91fb \
    --lineage --run --no-puts
```

Held constants: roar 0.4.4rc5 · `preload` tracer · Python 3.12.10 · torch 2.7.0 ·
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

**Update, 2026-08-11 — re-captured for the experiment link, and re-certified.**
Everything above about the 57→80 pin repair still stands; this section records what
happened after it.

The record of this row is now `27064dbb…`, which supersedes the certified `cc490321…`.
The recipe is unchanged except that **upstream's own experiment logging is switched on**
— see *Upstream's experiment logging* above. That was the one deliverable this row could
never produce: not merely missing, but blocked, because enabling it crashed the run.

The pin count went **up**, not down:

| | `cc490321…` | `27064dbb…` |
|---|---|---|
| pins across the lineage | 80 | **98** |
| `train` step | 79 | **97** |
| imports-vs-freeze Tier-A missing | 0 | **0** |
| imports-vs-freeze Tier-B missing | 0 | **0** |

The capture toolchain now records the *loaded* package set rather than the whole
environment, so a **smaller** freeze would have been the correct outcome here. It did
not shrink: the 18 extra pins in the train step are the tracker and its transitive
closure, genuinely loaded now that logging is on. Both audit tiers stay at zero, so the
new record is at least as complete as the certified one it replaces on every axis.

A cold agent then rebuilt it from the published lineage on a host that had never seen
the row: **exit 0, 3/3 steps, 98/98 recorded pins present at the exact recorded
version** (0 missing, 0 mismatched; 135 distributions installed, 37 extra transitive),
outputs regenerated, clean venv closure — no `dist-packages` and no host
`site-packages` on `sys.path`. The strongest single piece of evidence that the recorded
environment is what ran: bare `python` does not exist on the rebuild AMI (its `python3`
is 3.10.12), yet the recorded `python …` steps ran, and the venv's interpreter is
3.12.10 — so the recorded venv demonstrably supplied it, with nothing symlinked to fake
it. `row.json` carries `"verified": true`; full evidence in `CERT-TIER2-rc5.md`.

**What the rebuild does not prove.** A rebuild host holds no upload token, so the
tracker falls back to local logging and uploads nothing. That is by design — it is the
credential-free path a third party gets — and it means the rebuild proves the logging
code path *executes* on the recorded pins, not that a second dashboard was produced.
The capture produced the published one.

Two caveats survive certification and are worth stating plainly. `torchcodec` reaches
FFmpeg through `libavutil.so.*`, an **OS-package** edge that a pip freeze cannot see
(P1-11) — on the rebuild host all four of `libavutil.so.56/57/58/59` are absent, the
library fails to load, and LeRobot falls back to `pyav`, itself a recorded pin. The pip
closure is complete; the closure below pip is not, and no gate we run would catch that.
And `metrics.json` is 520 B here against 519 B at capture — one byte of float
formatting. Both files' sha256 are recorded on both sides, so that is a settled fact
rather than the kind of size-only discrepancy that can never afterwards be resolved.

_A note on comparing pin counts across rows: this row's numbers come from three
different capture toolchains (57 pins, then 80, now 98). A smaller freeze on a newer row
is usually a fix — later builds strip the tracker's own dependency footprint and record
only what the workload loaded — not a regression. Read each write-up's pin numbers
against the version that produced them, and treat the imports-vs-freeze audit, not the
count, as the measure of completeness._
