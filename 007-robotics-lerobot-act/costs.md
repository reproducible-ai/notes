# 007 LeRobot ACT — cost

Budget for this row: **NTE $10**. Actual GPU spend: **≈ $1.20** for the first capture
(2026-08-07) plus **≈ $0.50–0.80** for the 2026-08-08 re-capture — **≈ $1.70–2.00 in total**.

## Attempts

| # | What ran | Outcome | Wall clock | Notes |
|---|---|---|---|---|
| — | Bare-clone check (local CPU box, no GPU) | **passed** | ~25 min | Free. Fresh clone + scratch venv + the exact recorded commands, `PYTHONPATH` unset. Caught nothing, which is the point — it is what made attempts 1–3 cheap to reason about. |
| 1 | Full workflow | **failed in setup**, ~7 s of compute | 7 s | Provisioning tool missing from the image's `PATH`; the stage exited before any paid work. |
| 2 | Full workflow | **failed at publish** | 6 min 30 s | All three traced steps succeeded (fetch 6.6 s, train 279 s, evaluate 85 s) and the artifact labels were written; only the upload stage failed. Wasted, but it is the run that proved the pipeline and the trap-① fix. |
| 3 | Full workflow | **completed** | 6 min 47 s | Captured, labelled, published, gated. |
| 4 | Full workflow, re-captured 2026-08-08 on a newer capture toolchain | **completed, first attempt** | 6 min 1 s traced (12 min 18 s wall including provisioning) | Same recipe, same host class, same upstream base. Recorded environment grew 57 → 80 pins; see `README.md`. |

The runner (`g6e.xlarge`, one NVIDIA L40S) was launched once at 16:40:38 UTC and
served all three of the first day's attempts, so the bill is instance-hours, not
attempts. It was still
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

This row is truncated to **300 of the 100 000 default steps** — 0.3 %. Scaling the
headline 6m01s by 333 would be wrong by a wide margin, because **only 22 % of the
traced run is variable**. The step durations below are read from the lineage itself
(`cc490321`), not from a stopwatch:

| component | duration | scales with `--steps`? |
|---|---|---|
| `fetch_dataset` | 6.3 s | no |
| `train` — dataset + policy construction and the two `--eval_steps=150` held-out passes | 191.3 s | no |
| `train` — 300 optimizer steps @ 3.72 steps/s | 80.6 s | **yes** |
| `evaluate` | 83.2 s | no |
| provisioning + setup | ~150 s | no |
| **fixed total** | **430.8 s = 0.120 h = $0.22** | |
| **variable** | **0.2688 s/step = $0.000139/step** | |

At $1.861/h (`g6e.xlarge` on-demand, us-east-2): 100 000 steps ≈ 26 882 s ≈ 7 h 28 m of
optimizer time ≈ $13.90, plus $0.22 fixed → **≈ 7 h 36 m and ≈ $14.12**. That is the
honest figure for a converged ACT policy on `pusht_image`, and it is why this row
publishes a pipeline-viability truncation instead.

Two caveats. The estimate holds the *number* of held-out evaluations at two — i.e. it
assumes `--eval_steps` is scaled with the run length. Leaving `--eval_steps=150` fixed
would trigger 666 held-out passes at ~95 s each and roughly double the total. And it
excludes the ResNet-18 ImageNet weight download, which is fixed, unmetered here, and
outside the captured lineage.

## Human/agent effort

The expensive part of this row was not compute, it was **reading upstream source to
avoid paying for a wrong guess**: the checkpoint-path derivation
(`get_step_identifier` / `should_save_checkpoint` / `PRETRAINED_MODEL_DIR`), the
`push_to_hub` default, the wandb logger's constructor, and the editable-install /
egg-info interaction. Every one of those would have failed *after* a paid training
run had it been guessed wrong. The bare-clone check plus source reading cost roughly
half the row's elapsed time and approximately none of its money.

## The re-capture (2026-08-08)

One attempt, no retries. A fresh `g6e.xlarge` registered at 16:25:11 UTC, the job ran
16:22:39 → 16:34:57 UTC, and the runner's agent had deregistered by 16:40 UTC. That is
**≈ 15 minutes of instance time at $1.861/hr ≈ $0.47**, rising to ≈ $0.78 if the idle
reaper had held the host for its full 15-minute timeout after the job ended.

| Stage | Duration |
|---|---|
| provisioning + setup (cold image: dependency install, tooling install, environment gates) | ~2 min 30 s |
| `fetch_dataset` | 6.3 s |
| `train` — 300 steps + 2 held-out evaluations | 4 min 32 s |
| `evaluate` | 1 min 23 s |
| `label` + `publish` (207 MB upload) | ~10 s |

Training again ran at **3.72 steps/s**, so the 300 optimizer steps took ~80 s and the
rest of the train stage was the two held-out passes. The pre-flight work — a fresh
clone, a scratch venv built from the recorded pins, and running the recorded download
step against it — was done on a CPU box and cost nothing.
