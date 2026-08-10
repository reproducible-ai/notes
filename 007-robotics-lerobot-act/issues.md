# 007 LeRobot ACT — obstacles

Every obstacle hit while reproducing `huggingface/lerobot`'s ACT policy from its
published materials, in the order it bit. "Upstream-worthy?" means: is this a defect
or gap in the upstream repository that a patch could fix?

---

## 1. `pip uninstall` leaves `src/<pkg>.egg-info` behind, and a `src/`-layout project makes it live again

**Symptom.** After `pip install -e ".[training]"` followed by `pip uninstall -y
lerobot`, `lerobot` still reports as an *installed distribution* — but only from
inside a process that has put `src/` on `sys.path`.

```
$ pip uninstall -y lerobot
Successfully uninstalled lerobot-0.6.2
$ ls src/lerobot.egg-info/
PKG-INFO  SOURCES.txt  dependency_links.txt  entry_points.txt  requires.txt  top_level.txt

$ python -c "import importlib.metadata as m; print(m.version('lerobot'))"
importlib.metadata.PackageNotFoundError: No package metadata was found for lerobot

$ python -c "import sys; sys.path.insert(0,'src'); import importlib.metadata as m; print(m.version('lerobot'))"
0.6.2
```

**Root cause.** LeRobot builds with setuptools (`build-backend =
"setuptools.build_meta"`) in a `src/` layout. The PEP 660 editable build writes
`src/lerobot.egg-info/` into the working tree, and pip's uninstall removes the
`.dist-info` and the `.pth` hook but **not** the in-tree egg-info. `importlib.metadata`
scans `sys.path`, so the stale metadata is invisible until something adds `src/` —
which is precisely what a reproduction does to import the framework from the checkout
rather than from an install.

**Why it matters here.** Any environment record built from `importlib.metadata`
therefore contains `lerobot==0.6.2` inside the traced steps. That version is **not on
PyPI** (latest release: 0.6.1), so `pip install` of the recorded environment fails and
the run cannot be rebuilt anywhere — while the recorded pipeline still *looks*
perfectly well-formed. It is a silent, structure-invisible defect.

**Fix.** Sweep the egg-info *after* the uninstall, and then assert it is gone with
`src/` on the path — not just with the default path, which would pass either way:

```
pip install --constraint repro/constraints.txt -e ".[training]"
pip uninstall -y lerobot
rm -rf ./*.egg-info src/*.egg-info
python -c "import os,sys; sys.path.insert(0, os.path.abspath('src')); \
  import importlib.metadata as m; \
  d=[x.metadata['Name'] for x in m.distributions() if (x.metadata['Name'] or '').lower()=='lerobot']; \
  print('lerobot distributions visible:', d); sys.exit(1 if d else 0)"
```

`.gitignore` already lists `*.egg-info/`, so the leftover never shows up in
`git status` — which is part of why it is easy to miss.

**Upstream-worthy?** Partly. The leftover egg-info is pip/setuptools behaviour, not a
LeRobot bug. But LeRobot ships `version = "0.6.2"` in `pyproject.toml` while the
newest PyPI release is 0.6.1, so the in-tree version string never resolves for
anyone; a repo that expects to be installed from source could note that in its
contributor docs. Not filed — the campaign does not open upstream issues.

---

## 2. `WandBLogger` is coupled to wandb's exact API, so no wandb-compatible tracker can substitute

**Symptom.** Enabling upstream's own experiment logging (`--wandb.enable=true`) under
any drop-in `wandb` replacement aborts — twice over, at two different points, both on
the happy path.

**Root cause.** Three distinct couplings in `src/lerobot/common/wandb_utils.py`, found
by replaying the exact call shapes against `trackio` 0.34.0:

```python
 99:        wandb.init(id=…, project=…, entity=…, name=…, notes=…, tags=…, dir=…,
110:                   config=…, save_code=False, job_type="train_eval",
110:                   resume="must" if cfg.resume else None,   # ← (a)
111:                   mode=…)
115:        run_id = wandb.run.id
122:        logging.info(f"Track this run --> {colored(wandb.run.get_url(), …)}")   # ← (c)
...
202:                self._wandb.log(data=batch_data, step=step)                     # ← (b)
```

**(a) `resume=None` — fatal, at construction.** `TrainPipelineConfig.resume` defaults
to `False`, so every non-resumed run passes `resume=None`. wandb reads `None` as "do
not resume"; substitutes accept only `"must"` / `"allow"` / `"never"` and raise
`ValueError: resume must be one of: 'must', 'allow', or 'never'`. This fires before
step 1. Trivially fixed upstream by passing `"never"` instead of `None` — which is
also what the value *means*.

**(b) `log(data=…)` — fatal, at the first `log_freq` boundary.** wandb's first
parameter is literally named `data`; substitutes name it `metrics`, so the keyword
form is `TypeError: log() got an unexpected keyword argument 'data'`. Note line 200
already calls `self._wandb.log(batch_data)` **positionally** on the custom-step-key
branch — so the two branches of the same method have different portability. Passing
`batch_data` positionally on line 202 as well would fix it and change nothing for
wandb users.

**(c) `wandb.run.get_url()` — cosmetic, but unguarded.** `wandb.run.id` is broadly
implemented by wandb-compatible trackers; `Run.get_url()` is wandb-specific and does
not appear anywhere in `trackio` 0.34.0, on `Run` or elsewhere. It is used only to
print a link, so a purely cosmetic line takes down the run.

**(d) Not fatal, but worth knowing:** with `--wandb.enable=true` and
`training.save_checkpoint` on, `log_policy()` uploads the whole checkpoint as a run
artifact at every save — 207 MB on this row. `--wandb.disable_artifact=true` turns that
off and is a config flag, not a patch.

**Workaround.** Run with logging off (the default) and compute the held-out metric as
a separate pipeline step (`repro/evaluate_act.py` → `metrics/metrics.json`). Nothing
of substance is lost: the number training would have logged is recomputed from the
saved checkpoint, and it becomes a real artifact rather than a log line.

**Upstream-worthy? Yes, and it is small.** Three edits — one of them a single word —
make `WandBLogger` tracker-agnostic without altering behaviour for wandb users:
`resume=None` → `resume="never"`, `log(data=x, …)` → `log(x, …)`, and a `getattr`
guard around `get_url()`. See `patches/wandb-tracker-agnostic.diff` (all three;
`patches/wandb-get-url-guard.diff` is the earlier, partial version and is kept only
for provenance). **Not submitted** — the campaign prepares upstream patches but does
not post them.

**How this was established.** Not by inference: each call shape above was replayed
directly against `trackio` 0.34.0 with LeRobot's exact keyword set, and the failures
are the verbatim exception messages quoted. The check costs seconds and needs no GPU,
which is the general lesson — a logging integration can be validated against a
substitute tracker before any training host is provisioned.

---

## 3. `torchcodec` is a hard dependency of `lerobot[dataset]` but cannot load without system FFmpeg

**Symptom.** Every step that touches a `LeRobotDataset` prints a ~15-line warning
block:

```
WARNING:lerobot.utils.import_utils:Could not load libtorchcodec. Likely causes:
  1. FFmpeg is not properly installed in your environment...
[start of libtorchcodec loading traceback]
FFmpeg version 7: libavutil.so.59: cannot open shared object file: No such file or directory
FFmpeg version 6: libavutil.so.58: cannot open shared object file: No such file or directory
...
'torchcodec' is installed but cannot be loaded. Falling back to 'pyav' as a default decoder.
```

**Root cause.** `torchcodec` is pulled in unconditionally by the `dataset` extra, and
its native extension links against system FFmpeg shared objects that the wheel does
not bundle. The message also blames the PyTorch version (`2.7.0+cu126`), which is a
red herring — the pairing is correct; the FFmpeg libraries are simply absent.

**Impact: none, for this row.** `pusht_image` stores frames in parquet, so no video is
decoded and the PyAV fallback is never exercised either. Reproduced identically on a
CPU-only box and on the GPU runner, so it is an environment property rather than a
runner quirk.

**Upstream-worthy?** Marginal, and worth saying only because the warning reads like a
failure. The decoder is genuinely optional for image datasets; the diagnostic could
be demoted to a debug-level message when the dataset carries no video features. Not
filed.

---

## 4. `--eval_steps` runs a *full* pass over the held-out split, which dominates wall clock on a truncated run

**Symptom.** A 4-step smoke run configured with `--eval_steps=2` took 3 m 42 s on
CPU, of which ~3 m 40 s was the two held-out evaluations; the training steps
themselves took ~1 s each.

**Root cause.** Not a bug — `eval_steps` triggers a complete pass over the held-out
episodes (here 21 episodes / 2 742 frames), and `should_save_checkpoint` also forces
an evaluation on the final step. On a full-length run that cost is negligible against
100 000 training steps; on a deliberately truncated one it is most of the run.

**Consequence for anyone truncating LeRobot training:** set `--eval_steps` to a
divisor of `--steps` that you actually want, and expect the last step to evaluate
regardless. In this row `--eval_steps=150` over `--steps=300` gives two evaluations
(step 150 and step 300) and adds ~15 s on an L40S.

**Upstream-worthy?** No — documented behaviour, recorded here so the next person
sizing a truncated LeRobot run is not surprised by the bill.

---

## 5. Checkpoint layout is derived, not configurable — the publish path has to be predicted before the run

**Symptom.** The workflow must name the artifact path
(`outputs/act_pusht/checkpoints/000300/pretrained_model/model.safetensors`) up front,
in the label and publish stages, before any training has happened.

**Root cause.** The step directory name comes from
`get_step_identifier(step, total_steps)` in `src/lerobot/common/train_utils.py`, which
zero-pads to `max(6, len(str(total_steps)))` digits — so `--steps=300` yields
`000300`, but `--steps=1000000` would yield `1000000`. The `pretrained_model`
sub-directory is the constant `PRETRAINED_MODEL_DIR`. With `--save_freq=-1`,
`should_save_checkpoint` writes only the final checkpoint.

**Impact.** Read those three functions before writing the workflow; a wrong guess
fails at the *label* stage after the whole training run has been paid for. Verified by
reading the source rather than by guessing, and it matched.

**Upstream-worthy?** No — deterministic and documented in docstrings.

---

## 6. Bare-clone check: passed

The highest-value pre-flight, run before spending anything on GPU: a **fresh clone**,
a scratch venv containing only the dependency set the row expects to record,
`PYTHONPATH` unset, no editable install in effect, and the exact recorded commands.

```
$ env -u PYTHONPATH .venv-bare/bin/python -c \
    "import os,sys; sys.path.insert(0, os.path.abspath('src')); \
     import importlib.metadata as m; \
     print('lerobot dists on sys.path:', [(d.metadata['Name'],d.version) \
       for d in m.distributions() if (d.metadata['Name'] or '').lower()=='lerobot']); \
     import lerobot; print('lerobot.__version__ =', lerobot.__version__, '| file:', lerobot.__file__)"
lerobot dists on sys.path: []
lerobot.__version__ = unknown | file: .../bareclone/src/lerobot/__init__.py

$ env -u PYTHONPATH .venv-bare/bin/python repro/fetch_dataset.py \
    --repo-id lerobot/pusht_image --out-dir data/pusht_image
dataset: codebase_version=v3.0 episodes=206 frames=25650 tasks=1 fps=10
total bytes: 31621889

$ env -u PYTHONPATH .venv-bare/bin/python repro/train_act.py ... --policy.device=cpu --steps=4 ...
step:4 smpl:8 ... loss:62.748 l1_loss:0.880 kld_loss:6.187      # checkpoint written

$ env -u PYTHONPATH .venv-bare/bin/python repro/evaluate_act.py --checkpoint .../000004/pretrained_model ...
{"eval_loss": 0.6236292123794556, "action_l1": 65.1900405883789, ...}
```

No `ModuleNotFoundError` anywhere; all three recorded commands ran to completion and
the metric was computed. `lerobot.__version__` degrading to `"unknown"` is the
positive signal that the framework is being imported from the checkout with no
distribution metadata backing it — which is exactly the state a rebuild host is in.

Two deliberate deviations from the campaign runner, neither affecting what the check
proves: the check box has no GPU, so training ran on CPU with `--steps=4`; and the
torch family came from the CPU wheel index (`torch==2.7.0+cpu`) to fit the box's
disk. The campaign runner uses a plain-installed `torch==2.7.0`.
