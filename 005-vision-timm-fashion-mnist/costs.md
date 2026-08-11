# 005 — timm ResNet-18 / Fashion-MNIST · costs

Compute target `reproai-g4dn-plaintorch-a` — g4dn.xlarge, 1× Tesla T4,
us-east-2c, AMI `ami-0f07f1a0b382b48f7`, on-demand ($0.526/hr). Budget for this
row was NTE $10.

## Cloud attempts

The row was captured by two operators in sequence; the first stalled and the
second resumed from its working directory. Both sets of attempts are counted.

| # | job | outcome | wall clock | cost |
|---|---|---|---|---|
| 1 | `2ced85f2` | FAILED — CIFAR-10 recipe, pipeline still being shaped | — | — |
| 2 | `d7a9ef6c` | CANCELLED — superseded before it finished | — | — |
| 3 | `094063c8` | FAILED — first Fashion-MNIST recipe | — | — |
| 4 | `1900ef21` | FAILED — checkpoint retention changed | — | — |
| 5 | `9b7f8a12` | FAILED — trained and published, record not finalised | — | — |
| | | attempts 1–5, two hosts | ~58 min | ~$0.51 |
| 6 | `0db6ecb8` | COMPLETED — the superseded record `42b381d9…` | 9 m 34 s | $0.10 |
| 7 | `f8037549` | **COMPLETED — the current record `af56b02d…`** | 9 m 25 s | **$0.13** |
| | | | **~78 min** | **~$0.74** |

Attempts 1–5 ran on two hosts whose individual lifetimes (~19 min and ~39 min)
are known from the campaign ledger rather than from a per-job meter, so their
cost is an aggregate estimate, not five separate measurements. None of them
failed inside timm: every one of them trained successfully and several published
the checkpoint. They failed in the recording layer afterwards.

Attempt 7 is the one that counts. It cost **$0.13** for a 15 m 19 s billed
instance lifetime (9 m 25 s of job wall clock plus the agent's boot and idle
teardown either side) — of which only **3 m 42 s** was traced work (fetch 17.3 s,
train 170.6 s, evaluate 33.9 s). The rest is on-demand instance provisioning, the
dependency install, and the 89.5 MB checkpoint upload. **On a five-epoch job the
overhead costs three times what the training does**, which is the single most
important number on this page for anyone estimating a real run — see the
truncation arithmetic in `row.json`.

Attempt 7 exists only because attempt 6 shipped without an experiment dashboard:
`--log-wandb` was never passed, so timm never called the tracker. Re-running cost
$0.13 and produced an otherwise-equivalent record. Cheap — but it was avoidable,
and the check that would have caught it (does the recorded command contain the
framework's logging flag?) costs nothing.

## Tier-2 certification

| | |
|---|---|
| host | `i-0e16cfff386a839e6`, g4dn.xlarge |
| wall clock | 12 m 59 s |
| cost | **$0.11** |

**Row total: ~$0.85** (~$0.74 capture across seven attempts, $0.11
certification).

Both instances were terminated and both terminations were **verified** with
`describe-instances` rather than assumed, followed by a campaign-wide sweep for
orphans.

## Local (free)

The expensive thinking was done on the local CPU box at zero cloud cost:

- **bare-clone check** — fresh clone, venv with only timm's six declared runtime
  dependencies plus the tracking backend, `PYTHONPATH` unset, all three steps on
  CPU: ~8 min. This is what established that timm's declared dependency set is
  complete, and it produced a real 1-epoch checkpoint (top-1 78.60) before a
  single cent was spent.
- **call-shape replay** — replaying timm's exact `wandb.init(...)` arguments
  against the tracking backend on the CPU box, before booking a GPU. It failed
  with `TypeError: 'NoneType' object is not iterable`, which is how the
  `--wandb-project` requirement was found. That failure raises *inside* `init()`,
  before epoch 0 — so on the GPU it would have burned a whole run to learn the
  same thing. Cost: about two minutes and $0.
- **output census** — reading the local run's recorded output set to confirm
  that `--save-last-only` leaves one checkpoint file and that no two recorded
  outputs share content: seconds.
- reading the five previous attempts' logs to find out what actually went wrong
  before re-running anything: free, and it is the reason attempt 6 was the only
  new job launched.

## Scale caveat

Five epochs of ResNet-18 on 60,000 28×28 grayscale images is not a timm
workload. timm's published ResNet recipes are hundreds of epochs on ImageNet-1k
— roughly four orders of magnitude more compute — so **no inference about the
cost of a real timm training run should be drawn from the $0.10 figure.**
