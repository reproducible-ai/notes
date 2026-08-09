# 010 — torchvision classification · costs

Compute target `e4d609eb` — **g6e.xlarge** (1× NVIDIA L40S, 48 GB), us-east-2,
AMI `ami-0f07f1a0b382b48f7`, on-demand $1.861/h. Budget for this row was NTE $10.

## Cloud

| # | job | outcome | wall clock | cost |
|---|---|---|---|---|
| 1–2 | earlier attempts | recipe iteration before the final capture | — | ~$0.60 |
| 3 | `1eacc91f` | **COMPLETED** — 4 steps, the capture of record | 17 m 29 s | $0.54 |
| | | | | **~$1.14** |

Instance `i-02f57d52fc254a29a` launched 02:18:50 UTC and was terminated
02:36:19 UTC, immediately on job completion.

Breakdown of the 17 m 29 s: dataset fetch 3 m 03 s (13,394 JPEGs, download +
extract + hash), training 3 m 43 s, evaluation 26 s, checkpoint upload ~30 s,
and the balance in host bootstrap and environment setup.

## Where the money went, and where it didn't

The GPU was **not** the constraint. Measured throughput was ~219 img/s with
`--workers 0`, which is JPEG decode on a 4-vCPU host, not the L40S. An L40S is
badly over-specified for a 4-epoch resnet18 on 9,469 images; a T4 would have
produced the same result for a third of the price, because the bottleneck never
moved to the accelerator. The instance type was inherited from the compute
target, not chosen for this workload — worth fixing before any similar row.

Cost per epoch was therefore roughly **$0.03**, and the dataset fetch cost about
as much as the training did.

## Local (free)

The substantive work was local and cost nothing:

- bare-clone check — full four-step pipeline in a scratch CPU venv on a tiny
  subset, minutes
- a full 4-epoch CPU training run to establish the checkpoint-duplication
  behaviour and validate `evaluate_checkpoint.py` end to end
- reproducing the `--resume` `UnpicklingError` and verifying the proposed fix
  against a real checkpoint — seconds each

The bare-clone check was again the highest-value spend in the row: it found the
broken `--resume` round-trip and the `T_max = 0` crash before an instance
existed. Both would otherwise have been discovered as a failed GPU job.

## Scale caveat

This is a truncated run: 4 epochs on a 10-class, 9,469-image subset. The
upstream recipe this script is written for is 600 epochs on ImageNet-1k across 8
GPUs. **No inference about the cost of the real recipe should be drawn from the
figures above** — they differ by several orders of magnitude.
