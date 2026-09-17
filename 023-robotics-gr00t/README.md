# GR00T N1.7

GR00T N1.7 completed a public **100-step DROID 1.0.1 training capture** on 2026-09-15. The supervisor verified anonymous checkpoint downloads and public lineage automatically. This is a **partial training result**: cold replay, held-out policy quality and full reproduction remain untested.

## Public artifacts and lineage

- [Download the checkpoint at its immutable Hugging Face revision](https://huggingface.co/reproducible-ai/gr00t-n1-7/tree/ef04eee6429a8ae492cae74d6af2a0dd5dc41a7c/artifacts/droid-canary/checkpoint-100).
- [Inspect the public GLaaS training lineage](https://glaas.ai/dag/01c4225ca5c1df31c72153671041cd530fa338dac02259384855b56e0c540c15).
- [View the GLaaS AI-BOM audit](https://glaas.ai/dag/01c4225ca5c1df31c72153671041cd530fa338dac02259384855b56e0c540c15/audit).
- [Read the verification receipt](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/evidence/public-release.json) and [release record](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/PUBLIC-RELEASE.md).

## Selected public run

| Field | Recorded value |
| --- | --- |
| Job | `f282527c-4573-4a28-afae-29033e75c4c6` |
| Executed source and supervisor | [`c084d6eab090a2b5822db474d790a00dfe7fae5d`](https://github.com/reproducible-ai/Isaac-GR00T/tree/c084d6eab090a2b5822db474d790a00dfe7fae5d) |
| Dataset and scope | DROID 1.0.1; three episodes; 100 optimizer steps |
| Training settings | Batch 1, BF16, one GPU requested |
| Accelerator | Model not retained in the public verification receipt |
| Job duration | 576.804 seconds (9m36.804s); scheduler clock |
| Finalized allocation cost | **$1.57**, including idle shutdown; allocation stopped |
| Final training loss | **0.0912**; not a held-out quality score |

## Verification performed

Anonymous downloads matched all **31 manifest entries** by size and SHA-256. The **1,030 tensors** matched the three-shard safetensors index. The weight shards total **12,576,200,896 bytes** (about 12.58 GB).

The result receipt's **104,913-byte** artifact and SHA-256 refer to `model.safetensors.index.json`, not the complete weights. Individual shard hashes are recorded in the public verification receipt.

Anonymous GLaaS readback found **5 jobs, 98 artifacts and 231 links** and confirmed that each trained weight shard feeds the publication PUT. The supervisor performed verification and publication automatically. This public run has no independent lineage-auditor or cold-replay certification claim.

## Recipe and deviations

The [executed workflow](https://github.com/reproducible-ai/Isaac-GR00T/blob/c084d6eab090a2b5822db474d790a00dfe7fae5d/.treqs/workflows/droid-canary.yaml) and [training wrapper](https://github.com/reproducible-ai/Isaac-GR00T/blob/c084d6eab090a2b5822db474d790a00dfe7fae5d/.treqs/scripts/run_droid_canary.py) pin the recipe. The wrapper uses 100 steps and save interval 100, batch 1, reduced data-loading settings, model-only saving, and disabled Flash Attention and external logging. The corresponding example defaults are 10,000 steps, save interval 1,000 and batch 32; an example default is not evidence of the full original model-training schedule.

See [commands and replay limitations](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/commands.md). The website's displayed replay command has not been validated on a fresh host. Its generic Roar installation hint does not reproduce the pinned environment by itself.

## Attempts and cost

| Recorded run | Result | Final compute cost |
| --- | --- | ---: |
| Earlier private capture | 100 steps; final loss 0.0893; finalization needed authorized recovery | $1.52 |
| Selected public run | 100 steps; final loss 0.0912; automated public verification | $1.57 |
| Known subtotal | Both recorded jobs | **$3.09** |

The selected-run cost is not the cost of a cold replay or full training. The [cost ledger](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/costs.md) separates job duration from billed allocation lifetime and lists excluded costs.

## Limitations and licensing

- No held-out policy evaluation, independent cold replay, author verification or full reproduction is established. `verified` remains false and certification is unset.
- Roar's untracked-directory warning remains; checks cover the published inventory and graph described above.
- Separate calibration does not support a full-run cost estimate: inconsistent-slopes.
- The AI-BOM audit is linked above. A completeness score is not recorded in this notes snapshot; the audit link does not assert cold-replay certification.
- The checkpoint includes the NVIDIA license and notices. Its recorded use scope is non-commercial research/evaluation; consult the packaged terms.

## Earlier private capture and evidence

The [historical private report](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/PRIVATE-CAPTURE.md), [capture summary](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/evidence/capture-summary.json), [findings](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/issues.md), and [command history](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/commands.md) preserve the prior attempt. Its artifacts remain private. Its source revision, loss, cost and operator identity must not be attributed to the later public run.

The public supervisor is pinned with the selected source above. The earlier report's training-operator identity belongs to the private capture; no new operator model identity is inferred for this public automation.


## Calibration estimate

Separate calibration does not support a full-run cost estimate: inconsistent-slopes.

Projects the explicitly pinned 10000-update DROID fine-tuning scenario (first 32 episodes, batch 32, BF16, one 96 GB Blackwell GPU). It does not estimate original pretraining or the full DROID distribution.

The public artifact, lineage, AI-BOM and selected-run costs above are preserved. The new calibration checkpoint and lineage remain private. Its independent audit checks calibration evidence; it does not retroactively audit the public capture.

### Recipe and interpretation

- Calibration uses batch 32 and 32 pinned DROID episodes; the preserved public capture used batch 1 and three episodes.
- Independent early stops preserve the full cosine schedule and 500 warmup updates; no point resumes another point.
- Frozen language/vision backbone, trainable projector and diffusion model; SDPA, full model/optimizer checkpoints every 1000 projected updates, no periodic policy evaluation.
- The projection includes observed cold setup and finalization, measured checkpoint overhead, an allocation rate allowance and forecast transfer allowance. Actual allocation charges are recorded separately.

### Measured points

| Point | Completed updates | Training seconds | Steady updates | Steady seconds |
| --- | ---: | ---: | ---: | ---: |
| p1 | 100 | 164.84551071700002 | 80 | 80.56914754700006 |
| p2 | 200 | 292.28611577000004 | 180 | 183.85065417199996 |
| p3 | 400 | 473.30364272299994 | 380 | 391.14686883700006 |

Point timings are independent measurements within one allocation, not additional charges.

The estimate concerns the separately calibrated recipe. Public capture links, step counts and costs remain those of the earlier run. No cold replay, convergence, held-out policy quality or certification is established.

[Calibration evidence and calculation](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/evidence/calibration.json).
