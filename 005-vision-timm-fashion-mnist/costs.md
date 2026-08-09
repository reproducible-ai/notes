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
| 6 | `0db6ecb8` | **COMPLETED — the record** | 9 m 34 s | **$0.10** |
| | | | **~68 min** | **~$0.61** |

Attempts 1–5 ran on two hosts whose individual lifetimes (~19 min and ~39 min)
are known from the campaign ledger rather than from a per-job meter, so their
cost is an aggregate estimate, not five separate measurements. None of them
failed inside timm: every one of them trained successfully and several published
the checkpoint. They failed in the recording layer afterwards.

Attempt 6 is the one that counts and cost **$0.10** for 9 m 34 s of instance
life — of which only **3 m 47 s** was traced work (fetch 18.3 s, train 166.5 s,
evaluate 42.2 s). The remaining ~6 minutes is on-demand instance provisioning,
the dependency install, and the 89.5 MB checkpoint upload. On a five-epoch job
the overhead costs more than the training does.

The instance was terminated by hand immediately after the job completed and the
termination was verified.

## Local (free)

The expensive thinking was done on the local CPU box at zero cloud cost:

- **bare-clone check** — fresh clone, venv with only timm's six declared runtime
  dependencies, `PYTHONPATH` unset, all three steps on CPU: ~6 min. This is what
  established that timm's declared dependency set is complete, and it produced a
  real 1-epoch checkpoint (top-1 77.41) before a single cent was spent.
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
