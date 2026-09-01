# RWKV-7 on MiniPile

RWKV-7's published MiniPile training path produced a clean, portable record on one NVIDIA RTX PRO 6000 Blackwell. The bounded capture ran the unmodified upstream model and custom CUDA sources for two optimizer steps, published a 382 MB checkpoint and training log, and passed the strict record gate: CLEAN 14/14, AI-BOM 100, every DAG URL public, and a portable freeze.

This is a Tier-1 Reproducible record, not yet a Certified reproduction. A separate cold agent still has to execute the record and regenerate its outputs before the row can be called reproduced.

## Recipe and bounded run

The capture used upstream commit `658042ca30222715c1d3ab662a3c556824dc6618` and the entry point under `RWKV-v7/train_temp`. It retained the published L12-D768 model, 512-token context, bf16 precision, MiniPile binidx data, one GPU, DeepSpeed stage 2, and the two-stage flow that generates `rwkv-init.pth` before training.

MiniPile opened successfully with 1,498,226,207 tokens. All custom extensions compiled from upstream source for `sm_120`. The run then completed exactly two optimizer steps and stopped through the trainer's `--max_steps=2` control. The console reported losses of 11.20 and 10.90 and confirmed that the two-step limit was reached.

The training command used the upstream WandB path. The hosted project database contains the exact run and a stored step-2 metric row with loss, learning rate, weight decay, processed tokens, and throughput. This was checked from the remote data itself rather than inferred from the dashboard's HTTP status.

## Outputs and lineage

The capture published:

- `rwkv-0.pth`: 382,223,128 bytes; SHA-256 `a6235b3a8371d77e352bb4eccb5767d770d0f1502882117f092e96456cfb35c2`
- `train_log.txt`: 2,883 bytes; SHA-256 `5ff95a2d15c7954efbfb9a2f2319418ff39bb7c087f6d9b49dd9d3cbdc8ed8ef`

The full record hash is `357518abae1151de0ba348a507715a48c44688e705a3039aa49e293c989c095d`. The graph contains four recorded jobs and all fourteen expected dependency edges. The checkpoint and training log are outputs of the recorded training job before their publication step.

## Truncation and estimate

The published recipe runs 72 epochs at 2,520 optimizer steps per epoch, or 181,440 steps. The capture changed only the duration control to two steps and reduced the checkpoint interval from ten epochs to one so that the bounded run emitted its checkpoint.

The second measured step ran at about 10.60 steps per second. Extending that one short measurement to 181,440 steps and adding the measured fixed work gives a rough full-run estimate of 4h52m and $16.38 on the same GPU. Confidence is low: a two-step capture is enough to prove the path and record its dependencies, but not enough to benchmark a multi-hour training job.

## Architecture finding

An earlier attempt on an NVIDIA L40S reached the same upstream CUDA source but failed while compiling `rwkv7_cmix_bf16_v5` for `sm_89`. Its `float2` `atomicAdd` is unavailable for that target. The Blackwell run is a useful boundary: the identical upstream kernel source compiles and trains for `sm_120`, while the L40S path remains unsupported without an architecture-compatible accumulation implementation.

## Cost and status

The successful capture took 8m18s and cost $0.45. Two preceding Blackwell recipe attempts cost $0.39 and $0.50; both are retained in `runs[]`, bringing the three-attempt Blackwell capture total to $1.34. The row is ready for independent Tier-2 certification and makes no Tier-2 claim yet.
