# Costs — 011 fast_neural_style

Instance: **g4dn.xlarge** (1× Tesla T4, 4 vCPU Xeon 8259CL), us-east-2, on-demand
**$0.526/hr** = $0.00014611/s. Every timing below is read off a run log or from
`ec2 describe-instances` (`LaunchTime` → `StateTransitionReason`). Nothing here is
estimated except where it says so, and where it says so it shows the arithmetic.

## The run that produced the record

Fork commit `3a7a01cc2d1b`, instance `i-03d77c830864afd02`, DAG `63edfd1d…e377`.

| phase | wall-clock | fixed or variable? |
|---|---|---|
| instance launch → agent acquired | 2m24s (144 s) | fixed |
| `setup` — CLI install, wheel sha256 verification, environment gates, VGG-16 probe | 3m22s (202 s) | fixed |
| `fetch_dataset` — 342 MB download + extract + tracing of 13,396 files | 50 s | fixed |
| `train` — 9,469 images / 2,368 batches, 1 epoch | 9m12s (552 s) | **492 s variable + 60 s fixed** |
| `stylize` | 11 s | fixed |
| `label` | 1 s | fixed |
| lineage export (49 s) + publish (48 s) | 1m37s (97 s) | fixed |
| job completion → instance termination | 1m34s (94 s) | fixed |
| **total billed** | **19m12s (1,152 s)** | **= $0.168** |

The teardown figure is measured on the next cold instance (`i-08d4edefb6a9b0a8e`:
completed 18:28:27, terminated 18:30:01) because the instance that produced this record
was reused for a further job instead of being torn down immediately. Every other number
is from this run's own log.

### The three measurements that make the split defensible

All three were taken deliberately — in the untraced setup stage, or from timestamps in
the log — rather than reasoned about afterwards.

- **VGG-16 ImageNet weights: 4.10 s / 553,433,881 bytes.** `Vgg16.__init__`
  (`neural_style/vgg.py:10`) constructs
  `models.vgg16(weights=VGG16_Weights.IMAGENET1K_V1)`, so the first thing training does
  on a cold host is pull a ~528 MB checkpoint from `download.pytorch.org`. It is
  **fixed** — paid once whether you run one epoch or twenty — and it sits *inside* the
  train step's wall-clock, which is exactly the kind of thing that makes a full-run
  estimate wrong by an order of magnitude. Timed into a throwaway `TORCH_HOME` so the
  real cache stayed cold and the train step still paid what a fresh machine pays. Three
  independent measurements this session: 4.10 s, 3.75 s, 3.85 s, all 553,433,881 bytes.
- **Dataset fetch: 342 MB in 6.3 s, extract 5.8 s.** Also fixed. Small enough here to be
  a rounding error, but measured rather than assumed — an earlier row in this campaign
  had 94% of its wall-clock in a fixed download, and scaling its total was wrong by 10×.
- **Training throughput: 8,669 images in 450 s = 19.26 images/s**, taken between the
  first log line (800 images, 17:04:09) and the model save (17:11:39). One full epoch of
  9,469 images is therefore **492 s**, and the remaining 60 s of the 552 s train step is
  fixed: ~30 s to import torch, build the network and download the VGG-16 weights before
  the first batch, and ~31 s after the last batch for the two `torch.save` calls and the
  tracer's flush.

### The split

- **Variable: 492 s per epoch → $0.0719/epoch**
- **Fixed: 660 s → $0.0964** (1,152 s billed − 492 s of epoch)

## What a rebuild costs

**As recorded (1 epoch): 19m12s, $0.17** on one T4.

**Untruncated (upstream's default 2 epochs): 27m24s, $0.24.** The reader's path is
`roar reproduce --script`, then change `--epochs 1` → `--epochs 2` and
`--checkpoint-interval 2368` → `4736`, so the single checkpoint still lands on the final
batch of the final epoch. Both edits are in the same command; nothing else changes.
Arithmetic, so it can be audited:

```
fixed 660 s + (2 epochs × 492 s) = 1,644 s = 27m24s
1,644 s × $0.526/3600 = $0.240
```

### The one number that varies, and by how much

The lineage publish inside the fixed portion is the least stable component measured this
session: 48 s on the run that produced this record, and 166 s and 295 s on two other
executions of the same recipe. Substituting the worst case for the observed one moves
the fixed portion from 660 s to 907 s and the untruncated estimate from $0.24 to $0.28 —
so the estimate is stable to about ±15% against the largest source of variance in it.
The figures above use the run being published, not the best or the worst.

## What this does NOT cost out

Upstream's README trains on COCO 2014 train (82,783 images), not Imagenette (9,469). At
the same measured 19.26 images/s that is **4,298 s per epoch — about 2.4 hours for
upstream's default 2 epochs, ~$1.35** including this row's fixed portion, plus a 13 GB
manual download this row never performed and therefore never timed. That is offered as
an order-of-magnitude sketch with its unmeasured component named, not as an estimate
this row earned.

## Total spend on the row

Six job launches across two operators produced one publishable record. The billed GPU
time behind this row, across every attempt by both operators, is **$1.40**; the run that
produced the published record accounts for **$0.17** of it. `costUsd` reports the
latter, because a reader asking *"what am I in for if I rebuild this?"* should be quoted
the cost of the run, not our retry bill.
