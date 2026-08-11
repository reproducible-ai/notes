# Costs — 011 fast_neural_style

Instance: **g4dn.xlarge** (1× Tesla T4, 4 vCPU Xeon 8259CL), us-east-2, on-demand
**$0.526/hr** = $0.00014611/s. All timings are measured from the run logs and all
instance lifetimes from `ec2 describe-instances` (`LaunchTime` →
`StateTransitionReason`), not estimated.

## Attempts

| # | instance | lifetime | billed | outcome |
|---|---|---|---|---|
| 1 | `i-05a2273c3e01f94ab` | 03:11:47 → 03:40:01 = **28m14s** | $0.247 | Pipeline succeeded end to end. Record unusable — see below. |
| 2 | `i-0543ebf3d75b7fcfe` | 03:45:36 → 04:13:48 = **28m12s** | $0.247 | Host terminated **1 second before** the stylize step began, mid-run. Training lost. |
| 3 | `i-0a5f21cfd27f4df56` | 04:36:20 → 04:55:36 = **19m16s** | $0.169 | Pipeline succeeded end to end; host terminated **34 s into the lineage export**, which takes 51 s. |
| | | **75m42s** | **$0.664** | |

Attempt 2 also spent ~16 minutes queued behind a phantom slot before it started, on a
host that was already scheduled for termination.

**The training itself never failed.** It ran correctly three times, in 9m29s, (lost),
and 9m40s. Every dollar beyond the first $0.25 was spent on the recording apparatus,
not on the model.

## Per-step timings — attempt 3, the complete one

| phase | wall-clock | fixed or variable? |
|---|---|---|
| instance boot → agent acquired | 2m54s (174 s) | fixed |
| `setup` (roar install + wheel verify + env gates + VGG probe) | 3m36s (216 s) | fixed |
| `fetch_dataset` (342 MB download 6.3 s, extract 5.8 s, + tracing) | 51 s | fixed |
| `train` — 9,469 images / 2,368 batches, 1 epoch | 9m40s (580 s) | **variable** + ~77 s fixed startup |
| `stylize` | 9 s | fixed |
| `label` → `publish` → lineage export (killed) | ~1m35s | fixed |

Attempt 1, which is the only one that ran its **complete** lifecycle through job
completion and instance teardown, adds the two phases attempt 3 never reached:
label + publish + lineage published = 5m10s (310 s), and teardown → termination =
4m40s (280 s).

### The two measurements that make the split defensible

Both were taken deliberately, in the untraced setup stage, rather than reasoned about
afterwards:

- **VGG-16 ImageNet weights: 4.37 s / 553,433,881 bytes** (3.68–4.37 s across three
  runs). `Vgg16.__init__` downloads this on every cold host. It is **fixed** — paid
  once whether you run one epoch or twenty — and it sits *inside* the train step's
  wall-clock, which is exactly the kind of thing that produces an order-of-magnitude
  error if you scale a step total. Timed into a throwaway `TORCH_HOME` so the real
  cache stayed cold and the train step still paid what a fresh machine pays.
- **Dataset fetch: 342 MB in 6.3 s, extract 5.8 s.** Also fixed. Small enough here to
  be a rounding error, but measured rather than assumed — a previous row in this
  campaign had 94% of its wall-clock in a fixed dataset download and scaling the total
  was wrong by 10×.

### The split

Training throughput was measured between the first log line (800 images) and the
model save: **8,669 images in 461 s = 18.8 images/s**, so one full epoch of 9,469
images ≈ **503 s**.

- **Variable: ~503 s per epoch → $0.0735/epoch**
- **Fixed: 1,200 s → $0.175** — taken from attempt 1's complete 1,694 s billed
  lifetime minus its 494 s training loop, because that is the only run that paid every
  phase including publish and teardown.

Cross-check: 1,200 + 494 = 1,694 s = attempt 1's measured lifetime. ✓

## What a rebuild costs

**As recorded (1 epoch): ~28 minutes, ~$0.25** on one T4.

**Untruncated (upstream's default 2 epochs): ~37 minutes, ~$0.32.** The reader's path
is `roar reproduce --script`, then change `--epochs 1` → `--epochs 2` and
`--checkpoint-interval 2368` → `4736` so the single checkpoint still lands on the
final batch. Arithmetic, so it can be audited:

```
fixed 1,200 s + (2 epochs × 503 s) = 2,206 s = 36m46s
2,206 s × $0.526/3600 = $0.322
```

**What this does NOT cost out:** upstream's README trains on COCO 2014 train (82,783
images), not Imagenette (9,469). At the same measured 18.8 images/s that is 4,404 s
per epoch — **~2.9 hours for upstream's default 2 epochs, ~$1.29**, plus a 13 GB
download this row never performed and therefore never timed. That number is offered
as an order-of-magnitude sketch with its unmeasured component named, not as an
estimate this row earned.

## Honest note on `costUsd`

`rebuild.costUsd = 0.25` is attempt 1's measured billed lifetime, because it is the
only attempt that executed every phase a rebuilder would pay for. Attempt 3 cost
$0.169 only because the platform killed its host before teardown — that is a cheaper
number for a worse reason, and publishing it would understate what a rebuild costs.

The **$0.664 total** burned on this row is in the table above and is not folded into
`costUsd`: two thirds of it bought nothing, and a reader asking "what am I in for"
should not be quoted our retry bill.
