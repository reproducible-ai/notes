# 007 LeRobot ACT — cost

Budget for this row: **NTE $10**. Actual GPU spend: **≈ $1.20**.

## Attempts

| # | What ran | Outcome | Wall clock | Notes |
|---|---|---|---|---|
| — | Bare-clone check (local CPU box, no GPU) | **passed** | ~25 min | Free. Fresh clone + scratch venv + the exact recorded commands, `PYTHONPATH` unset. Caught nothing, which is the point — it is what made attempts 1–3 cheap to reason about. |
| 1 | Full workflow | **failed in setup**, ~7 s of compute | 7 s | Provisioning tool missing from the image's `PATH`; the stage exited before any paid work. |
| 2 | Full workflow | **failed at publish** | 6 min 30 s | All three traced steps succeeded (fetch 6.6 s, train 279 s, evaluate 85 s) and the artifact labels were written; only the upload stage failed. Wasted, but it is the run that proved the pipeline and the trap-① fix. |
| 3 | Full workflow | **completed** | 6 min 47 s | Captured, labelled, published, gated. |

The runner (`g6e.xlarge`, one NVIDIA L40S) was launched once at 16:40:38 UTC and
served all three attempts, so the bill is instance-hours, not attempts. It was still
up 40 min later when the row was finished and handed off; it idle-terminates on its
own, and terminating a managed instance out of band is known to strand the job agent,
so it was left alone. At $1.861/hr that is **≈ $1.24 and settling** — call it $1.20–1.60
depending on when the idle reaper fires. Storage and the 207 MB Hub upload are
negligible against that.

## Where the time actually went

Almost none of it was GPU work. Attempt 3, stage by stage:

| Stage | Duration |
|---|---|
| setup (deps already resident from attempt 2) | 15 s |
| `fetch_dataset` | 4 s (3.4 s traced) |
| `train` — 300 steps + 2 held-out evaluations | 4 min 18 s |
| `evaluate` | 1 min 24 s |
| `label` | < 1 s |
| `publish` (207 MB upload) | ~10 s |

Training itself ran at **3.75 steps/s**, so the 300 optimizer steps took ~80 s; the
remaining ~3½ minutes of the train stage were the two full passes over the held-out
split that `--eval_steps=150` triggers (see `issues.md` §4). On attempt 2 the setup
stage additionally installed the whole `lerobot[training]` dependency set, which is
where most of that run's extra minute went.

## What a full-length run would cost

This row is truncated to **300 of the 100 000 default steps** — 0.3 %. At the observed
3.75 steps/s and holding everything else equal, 100 000 steps is ≈ 7 h 25 m of pure
optimizer time on one L40S, plus held-out evaluations at whatever `eval_steps`
cadence is chosen; call it **≈ $14–16** at on-demand pricing. That is the honest
figure for a converged ACT policy on `pusht_image`, and it is why this row publishes
a pipeline-viability truncation instead.

## Human/agent effort

The expensive part of this row was not compute, it was **reading upstream source to
avoid paying for a wrong guess**: the checkpoint-path derivation
(`get_step_identifier` / `should_save_checkpoint` / `PRETRAINED_MODEL_DIR`), the
`push_to_hub` default, the wandb logger's constructor, and the editable-install /
egg-info interaction. Every one of those would have failed *after* a paid training
run had it been guessed wrong. The bare-clone check plus source reading cost roughly
half the row's elapsed time and approximately none of its money.
