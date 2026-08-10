# 010 — torchvision classification · costs

Compute target — **g4dn.xlarge** (1× Tesla T4, 16 GB), us-east-2c, AMI
`ami-0f07f1a0b382b48f7`, on-demand $0.526/h list price. Budget for this row was NTE $10.

## Cloud

| # | attempt | outcome | billed instance time | cost |
|---|---|---|---|---|
| 1–2 | recipe iteration before the first capture | — | — | ~$0.60 |
| 3 | first capture, on an L40S | trained correctly; record incomplete | 17 m 29 s | $0.54 |
| 4 | second capture, on a T4 | trained correctly; record incomplete | 25 m 09 s | $0.22 |
| 5 | this capture, on a T4 | **COMPLETED** — 4 steps, the record of record | 20 m 05 s | $0.18 |
| | | | | **~$1.54** |

One instance, `i-00abbc8faea2e6c02`, served attempt 5. It launched 21:13:36 UTC and was
terminated 21:33:41 UTC — 20 m 05 s of billed instance time at $0.526/h. Termination was
confirmed with `describe-instances` (state `terminated`), not assumed.

The $0.526/h figure is AWS's published on-demand list price; neither Cost Explorer nor
the Pricing API is reachable from this account, so it is not read back from a bill. It is
corroborated independently: the platform's own job record estimated 13 ¢ for the
14 m 48 s job window, which implies $0.527/h.

## Where the money went, and where it didn't

The GPU is **not** the constraint and never was. Throughput is ~385 img/s with
`--workers 0`, which is JPEG decode on a 4-vCPU host. An earlier capture ran on an L40S
and produced the same shape of result for **3× the cost**; the accelerator bought
nothing, because the bottleneck never moved to it. Anyone reproducing this should pick
the cheapest available GPU host, not the largest.

## Fixed vs variable — what a longer run would actually cost

This matters more than the headline, because two thirds of this row's wall clock is fixed
cost that does not scale with training length.

| | duration | cost |
|---|---|---|
| host provisioning | 2 m 30 s | |
| environment setup | 47 s | |
| **dataset fetch** (13,394 JPEGs: download, extract, hash) | **2 m 32 s** | |
| evaluation | 23.7 s | |
| checkpoint upload + lineage publication | ~3 m 10 s | |
| stage transitions, and idle between the last step and termination | 5 m 01 s | |
| **fixed subtotal** | **14 m 24 s** | **$0.13** |
| **training** (4 epochs, incl. per-epoch validation) | **5 m 41 s** | **$0.05** |
| | | |
| per epoch | 85.25 s | **$0.0125** |

Upstream's documented ResNet recipe is **90 epochs** (`references/classification/README.md`,
the parameter table at the top). Ninety epochs on this same 10-class subset on one T4:

```
0.13 + 90 × 0.0125 = $1.25       (≈ 2 h 22 m of instance time)
```

**That is not the cost of upstream's recipe.** Upstream trains on ImageNet-1k — 1.28 M
images against Imagenette's 9,469 — across 8× V100. The estimate above holds the dataset
and the hardware fixed and scales only the epoch count, which is the one axis this row
actually measured. No inference about the real ImageNet recipe should be drawn from it;
they differ by orders of magnitude.

Note how badly a naive scale-up would mislead: multiplying the 17 m 18 s headline by
22.5 gives ~6 h 30 m, roughly three times the honest answer, purely from treating the
dataset fetch and the upload as if they happened once per epoch.

## Local (free)

The substantive work was local and cost nothing:

- bare-clone check — the full pipeline in a scratch CPU venv on a tiny subset, minutes
- a full 4-epoch CPU training run to establish the checkpoint-duplication behaviour and
  validate `evaluate_checkpoint.py` end to end
- reproducing the `--resume` `UnpicklingError` and verifying the proposed fix against a
  real checkpoint — seconds each
- measuring, in-process, which distributions `import torch` and the dataset download
  actually pull in, so the recorded pin set could be checked against observed imports
  rather than against a plausible-looking count

The bare-clone check was again the highest-value spend in the row: it found the broken
`--resume` round-trip and the `T_max = 0` crash before an instance existed. Both would
otherwise have been discovered as a failed GPU job.
