# 010 — torchvision classification · costs

Compute target — **g4dn.xlarge** (1× Tesla T4, 16 GB), us-east-2c, AMI
`ami-0f07f1a0b382b48f7`, on-demand $0.526/h. Budget for this row was NTE $10.

## Cloud

| # | attempt | outcome | wall clock | cost |
|---|---|---|---|---|
| 1–2 | earlier attempts | recipe iteration before the first capture | — | ~$0.60 |
| 3 | first capture, on an L40S | trained correctly; record incomplete | 17 m 29 s | $0.54 |
| 4 | this capture, on a T4 | **COMPLETED** — 4 steps, the record of record | 15 m 09 s | $0.22 |
| | | | | **~$1.36** |

One instance, `i-0a9e54981f4f763f7`, served attempt 4. It launched 16:19:52 UTC and was
terminated 16:45:01 UTC — 25 m 09 s of billed instance time covering a short failed start
and the successful pipeline, at $0.526/h. Termination was confirmed with
`describe-instances` (state `terminated`), not assumed.

## Where the money went, and where it didn't

The GPU is **not** the constraint and never was. Throughput is ~400 img/s with
`--workers 0`, which is JPEG decode on a 4-vCPU host. The first capture ran on an L40S
and produced the same shape of result for **2.5× the cost**; the accelerator bought
nothing, because the bottleneck never moved to it. Anyone reproducing this should pick
the cheapest available GPU host, not the largest.

Breakdown of the 15 m 09 s: dataset fetch 2 m 50 s (13,394 JPEGs — download, extract and
hash), training 5 m 47 s, evaluation 24 s, checkpoint upload ~30 s, and the balance in
host bootstrap and environment setup. Cost per epoch was roughly **$0.02**, and the
dataset fetch cost about half what the training did.

## Local (free)

The substantive work was local and cost nothing:

- bare-clone check — the full four-step pipeline in a scratch CPU venv on a tiny subset,
  minutes
- a full 4-epoch CPU training run to establish the checkpoint-duplication behaviour and
  validate `evaluate_checkpoint.py` end to end
- reproducing the `--resume` `UnpicklingError` and verifying the proposed fix against a
  real checkpoint — seconds each
- resolving the recorded pin set with a real resolver, offline, to see what a rebuild
  would actually install

The bare-clone check was again the highest-value spend in the row: it found the broken
`--resume` round-trip and the `T_max = 0` crash before an instance existed. Both would
otherwise have been discovered as a failed GPU job.

## Scale caveat

This is a truncated run: 4 epochs on a 10-class, 9,469-image subset. The upstream recipe
this script is written for is 600 epochs on ImageNet-1k across 8 GPUs. **No inference
about the cost of the real recipe should be drawn from the figures above** — they differ
by several orders of magnitude.
