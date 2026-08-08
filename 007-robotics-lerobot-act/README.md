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
| Fork | `reproducible-ai/lerobot` @ `78c775d1fe64be80e61e007593cecc5f080ac51b` |
| Dataset | `lerobot/pusht_image` (public, anonymous fetch, 31 621 889 bytes over 7 files) |
| Artifact | `hf://reproducible-ai/lerobot-act` → `model.safetensors` (207 MB, public) |
| Lineage | [`023d15ff…50ed8`](https://glaas.ai/dag/023d15ffb248254a2955d46a513c57a485a78587701d43a1053819f96ad50ed8) — 4 jobs |
| Metric | held-out `eval_loss` **0.5362**, unnormalised action L1 **53.30**, over 2 742 frames / 21 held-out episodes |
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

**3. Upstream's experiment logging cannot be bridged.** LeRobot ships wandb support
behind `--wandb.enable=true`, so the honest thing would be to enable it and let it
mirror to a hosted Space. It cannot: `WandBLogger.__init__` calls
`wandb.run.get_url()` unguarded at `src/lerobot/common/wandb_utils.py:122`, and
`get_url` does not exist on any wandb-API-compatible tracker we can substitute
(checked against `trackio` 0.34.0 — the symbol appears nowhere in the package).
Enabling logging therefore aborts training at startup. Rather than patch upstream to
suit the tracker, this row runs with logging **off** and computes the held-out metric
as its own pipeline step instead. See `issues.md`.

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
roar reproduce 023d15ffb248254a2955d46a513c57a485a78587701d43a1053819f96ad50ed8 \
    --lineage --run --no-puts
```

Held constants: roar 0.4.4.dev0 · `preload` tracer · Python 3.12.10 · torch 2.7.0 ·
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
