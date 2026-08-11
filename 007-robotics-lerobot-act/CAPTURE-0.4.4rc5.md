# Row 007 — re-capture on roar `0.4.4rc5`, with a working experiment link

_Supersedes the `cc490321…` capture. Same model, same dataset, same recipe, same
hardware; the only deliberate change is that **upstream's own experiment logging is
switched on**, which had never been possible on this row before._

| | |
|---|---|
| DAG (attributed) | `27064dbb01d6fa6e241329f93deff5e224eba4400482790adaabf52955be91fb` |
| Anonymous host-published twin | `f6203101b391dab61b673c3186cf3d766111a72c65f9c186580b25d621a1b293` |
| Fork / commit | `reproducible-ai/lerobot` @ `8cdbf8c226b80293d1692feb11cc767e1d4df531` |
| Upstream | `huggingface/lerobot` @ `ff7cc3de1de830f5f3276918a013d04bdf9ea4be` |
| Target / AMI | `e4d609eb` `reproai-g6e1x-plaintorch-b` · `ami-0f07f1a0b382b48f7` · g6e.xlarge, 1×L40S |
| roar | `0.4.4rc5`, wheel sha256 `ed35ed6bda3b5698ab65a887e7390c2ac073123f6d94bfa27b8282285352219c` |
| Recorded interpreter | CPython 3.12.10 |
| Pins / audit | **98 pins · imports-vs-freeze Tier-A 0 · Tier-B 0 — THICK** |
| Tier-1 gates | clean-dag 13/13 · AI-BOM 100/100 · URLs ALL PUBLIC · freeze PORTABLE |
| Upstream `src/` lines changed | **0** |
| Experiment link | https://huggingface.co/spaces/reproducible-ai/experiments?project=lerobot-act-pusht |

## 1. What changed, and why it is only configuration

LeRobot has always shipped wandb support. It is gated at
`src/lerobot/scripts/lerobot_train.py:393` on `cfg.wandb.enable and cfg.wandb.project`,
and `WandBConfig.enable` defaults to `False`
(`src/lerobot/configs/default.py:94`). Three of upstream's own flags turn it on:

```
--wandb.enable=true --wandb.project=lerobot-act-pusht --wandb.disable_artifact=true
```

`--wandb.disable_artifact=true` is **not cosmetic**. With logging on,
`WandBLogger.log_policy()` calls `wandb.log_artifact()` at every checkpoint save, and
the tracker implements `log_artifact` for real — without the flag the run would push
the 207 MB `model.safetensors` to the Space on each save. `log_policy()` returns
early when the flag is set (`wandb_utils.py:126`).

Nothing under `src/` is modified. The row keeps its zero-upstream-lines property.

## 2. The part that is easy to get wrong: WHERE the space id goes

This is the single most important line in the workflow, because the wrong version of
it **passes capture and fails every rebuild**.

`roar run` records **argv only**. Anything `export`ed on a preceding line is not in
the lineage and is not replayed. The wandb→trackio bridge picks its mode from the
traced child's environment:

| `TRACKIO_SPACE_ID` | bridge installs | `run.get_url()` |
|---|---|---|
| set | the real tracker, aliased as `wandb` | **present** |
| unset | a silent no-op stub | **absent** |

LeRobot calls `wandb.run.get_url()` **unguarded** at
`src/lerobot/common/wandb_utils.py:122`, inside `WandBLogger.__init__`, before
training step 1. The no-op stub's `_Run` class implements only
`summary`/`config`/`id`/`name`/`log`/`finish`/`watch`/`log_code`. So with the space id
merely exported around the command, the train step would have succeeded here and died
on every rebuild host with:

```
AttributeError: '_Run' object has no attribute 'get_url'
```

Both branches were verified directly against the installed bridge before any GPU was
booked. The fix is to put the assignment **inside the recorded command**:

```
roar run -n train --wandb-to-trackio -- env TRACKIO_SPACE_ID=reproducible-ai/experiments python repro/train_act.py …
```

`env` is `exec`, not a shell, so the tracer keeps its view of the Python process —
measured identically (`in:0 out:1`) for `env VAR=v python probe.py` and for bare
`python probe.py`. And `roar reproduce` does not rewrite `argv[0]`; it only prepends
the rebuilt venv's `bin` to `PATH`, so the `python` that `env` resolves is still the
recorded interpreter. The recorded command reads back verbatim in the published DAG.

A rebuild host has no upload token, so its tracker falls back to local logging and
uploads nothing — warnings, exit 0, no credential required. That is the intended
third-party path, and it is why **`trackio` has to be a recorded pin**: if
`import trackio` fails on the rebuild host the bridge silently drops to the no-op stub
and the `get_url` crash comes back.

## 3. Verifying the link — a 200 is not a test

The Space is a Gradio app and returns **200 for any query string**, and the tracker
writes `space_id` to its database even when sync fails. So a run that logged nothing
still publishes a link that 200s. Four independent checks were used instead:

1. **The bridge took the tracker branch, not the stub.** The traced child logged
   `[wandb->trackio] active (wandb -> trackio, space=reproducible-ai/experiments)`.
2. **The upload token reached the traced environment.** Asserted before any paid step
   (`HF_TOKEN present in task env: True | length: 37`); the value is never printed.
3. **No local-fallback warning anywhere in the run.** A token-less control run of the
   identical code path was executed first and is loud about failure —
   `could not flush buffered remote data … 500`, `could not upload buffered logs to
   Bucket … 401 Unauthorized`, `Some logs could not be sent to the remote server`.
   None of those strings appear in this run; it ends with
   `* Run finished. Uploading logs to the remote Trackio server (please wait...)`
   followed by `roar: done · 272.2s … exit 0`.
4. **The remote store's own timestamp.** The backing bucket
   `reproducible-ai/experiments-bucket` reports
   `updatedAt: 2026-08-11T01:51:04.290Z`. This run flushed at 01:51:01. The remote
   store was written by this run.

## 4. Pin count went UP, not down

| | rc2 record (`cc490321…`) | this record (`27064dbb…`) |
|---|---|---|
| fetch_dataset | 23 | 23 |
| train | 79 | **97** |
| evaluate | 73 | 73 |
| union | 80 | **98** |
| Tier-A missing | 0 | **0** |
| Tier-B missing | 0 | **0** |

rc5 records the *loaded* package set rather than the whole environment, so a smaller
freeze would have been correct here. It did not shrink: the 18 additional pins in the
train step are the tracker and its transitive closure, which this run genuinely loads
now that logging is on. Tier-A and Tier-B both stay at zero, so the record is at least
as complete as the certified one it supersedes on every axis.

Note that `wandb` itself is also a recorded pin. It is installed (LeRobot's
`training` extra declares it) but never imported — the bridge aliases `wandb` in
`sys.modules` before the workload's first import — so it is recorded as an installed
distribution, not as a loaded one.

## 5. Measured timings

Stage boundaries from the job log; traced durations from the lineage.

| phase | wall clock | traced |
|---|---|---|
| provisioning + agent boot | 115 s | — |
| setup (deps, CLI, pre-flight assertions) | 167 s | — |
| `fetch_dataset` | 6 s | 4.07 s |
| `train` | 273 s | 271.40 s |
| `evaluate` | 84 s | 83.44 s |
| label + publish | 7 s | — |
| **total job** | **655 s (10m55s)** | **358.91 s (5m59s)** |

Inside the train step:

| component | measured |
|---|---|
| 300 optimizer steps | 79.2 s (`step_s` 0.264 = `data_s` 0.229 + `updt_s` 0.035) |
| 2 held-out eval passes (`--eval_steps=150`) | 165 s (83 s + 82 s) |
| ResNet-18 ImageNet weights download | **0.34 s, 46,830,571 B** |
| construction, checkpoint save, tracker flush | ~28.8 s |

The ResNet-18 figure is measured, not assumed: ACT's default backbone is `resnet18`
with `pretrained_backbone_weights="ResNet18_Weights.IMAGENET1K_V1"`
(`configuration_act.py:98-99`), so first policy construction fetches
`resnet18-f37072fd.pth` from `download.pytorch.org`. The workflow times that download
into a throwaway `TORCH_HOME` so the real cache stays cold and the train step still
pays the cost a fresh machine pays; the probe only sizes the component, it does not
remove it. Previous estimates for this row had to exclude it as an unquantified
caveat. It is 0.34 s — negligible, and now stated rather than waved at.

## 6. Known and not chased

- **`torchcodec` → FFmpeg → `libavutil.so.*`** (P1-11). `torchcodec` is a recorded
  pin but needs an OS package no pip freeze captures; it fails to load and LeRobot
  falls back to `pyav`, which is also a recorded pin. Expected on this row; it did not
  affect the result.
- The anonymous host-published twin is a different, smaller graph than the attributed
  one. Certification is against the **attributed** graph.
