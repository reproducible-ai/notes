# 004 — DCGAN / CIFAR-10 · costs

> **Reconstructed.** The operator's per-attempt cost table for this row was lost
> with the working directory. Only two cost figures survive in evidence, and only
> those two are stated. **The attempt-by-attempt burn for the capture phase is
> unknown and is not estimated here** — a made-up table would be worse than an
> admitted gap.

## What survives

| phase | figure | source |
|---|---|---|
| Tier-2 certification (the successful one) | **~$0.41** | campaign ledger's copy of the certifier's report |
| Capture (the recorded run) | **unknown** | no surviving record |

## What the record *does* say about the capture

The DAG timestamps bound the traced portion of the capture precisely, even though
the instance's total billed lifetime is not recorded:

| step | job | wall clock | window (UTC) |
|---|---|---|---|
| 1 `prepare` | `f4ce119f` | 24 m 57 s | 17:05:24 → 17:30:21 |
| 2 `train` | `a37eae73` | 1 m 42 s | 17:30:23 → 17:32:05 |
| 3 `publish` | `325b53a3` | <1 s | 17:32:15 |
| | | **≈ 26 m 41 s traced** | |

Add an untraced setup stage and instance provisioning, neither of which is in the
record, so the billed lifetime was longer than 26 minutes. On the recorded
hardware — a single Tesla T4 with 4 vCPU — a run of that length is a small number
of cents to low tens of cents. **That is arithmetic on a public on-demand rate, not
a recorded figure, so it is offered as a bound and not as this row's cost.**

## The shape of the burn is worth noting

**94% of the traced wall clock is the CIFAR-10 download, not training.** 24 m 57 s
fetching 170 MB from `cs.toronto.edu` at a throttled ~114 kB/s, versus 1 m 42 s of
actual GPU work at a 1,480 MB peak. The GPU sat idle for the entire first step
(`gpu_used: false` on the record).

The practical consequence for anyone rebuilding this row: **you are paying for a
GPU to wait on a slow HTTP server.** Mirroring CIFAR-10 to storage near the compute
would cut this row's cost by roughly an order of magnitude without changing a line
of the recipe or a byte of the result.

## Attempt history

The certification succeeded on its fourth attempt; the ledger records the three
preceding attempts as **substrate failures rather than row defects**, and does not
preserve a per-attempt cost. Their combined cost is therefore unknown. They were
short failures — the campaign's certification hosts are terminated on failure —
but no figure is asserted.

An earlier capture of this row was superseded before certification because its
recorded freeze pinned a local-version wheel (`+cuNNN`) that does not exist on
PyPI, making the record unrebuildable on any host. That is what the re-capture on
a plain-PyPI torch image fixed. Its cost is likewise not on file.

## Known total

**~$0.41 certified, capture cost unrecorded.** The row's true total is higher than
$0.41 by an unknown amount.
