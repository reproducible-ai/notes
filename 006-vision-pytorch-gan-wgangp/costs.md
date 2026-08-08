# 006 — WGAN-GP / MNIST · costs

> **Reconstructed.** The operator's per-attempt cost table for this row was lost
> with the working directory. Only one cost figure survives in evidence, and only
> that one is stated. **The attempt-by-attempt burn for the capture phase is unknown
> and is not estimated here** — a made-up table would be worse than an admitted gap.

## What survives

| phase | figure | source |
|---|---|---|
| Tier-2 certification | **~$0.10** | campaign ledger's copy of the certifier's report |
| Capture (the recorded run) | **unknown** | no surviving record |

~$0.10 is the cheapest certification of any row in this campaign to date.

## What the record *does* say about the capture

The DAG timestamps bound the traced portion of the capture precisely, even though
the instance's total billed lifetime is not recorded:

| step | job | wall clock | window (UTC) |
|---|---|---|---|
| 1 `prepare` | `c22a45a8` | 2 m 06 s | 15:13:36 → 15:15:43 |
| 2 `train` | `74d3e84d` | 1 m 06 s | 15:15:44 → 15:16:50 |
| 3 `evaluate` | `a94de43c` | 6.6 s | 15:16:52 → 15:16:58 |
| 4 `publish` | `bed22257` | <1 s | 15:17:10 |
| | | **≈ 3 m 22 s traced** | |

Add an untraced setup stage and instance provisioning, neither of which is in the
record, so the billed lifetime was longer than 3 minutes 22 seconds. **This is one
of the fastest end-to-end pipelines in the campaign.**

Cost cannot be derived from that, because the hourly rate depends on the instance
type and the record does not carry it — only the hardware it exposed (1× NVIDIA
L40S, 4 vCPU AMD EPYC 7R13). L40S-class instances are among the campaign's more
expensive targets, so a three-minute run on one is still cents rather than dollars,
but no figure is asserted.

## The hardware was heavily over-provisioned

Worth recording as a campaign observation rather than a row defect: **peak GPU
memory across the entire run was 582 MB, on a card with 46,068 MB.** The generator
and critic are MLPs over 28×28 MNIST images. Training ran for 66 seconds.

This row would produce a bit-for-bit equivalent record — same commands, same pins,
same claim — on a far cheaper target, and possibly on CPU. The L40S is what the
campaign's compute target happened to provide, not what the recipe requires. Anyone
rebuilding this row should not read the recorded hardware as a requirement.

The same point applies to the shape of the run: step 1, the MNIST download, is
**62% of the traced wall clock** and uses no GPU at all (`gpu_used: false` on the
record).

## Attempt history

Unknown. The ledger records this row as certified on the campaign's standard cold
rebuild with no note of prior failed attempts, and no per-attempt cost table
survives. **Absence of a recorded failure is not evidence that there were none** —
it is simply the limit of what the surviving evidence says.

## Known total

**~$0.10 certified, capture cost unrecorded.** The row's true total is higher than
$0.10 by an unknown amount.
