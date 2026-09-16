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
- The full training schedule and fixed/scaling cost split are unknown, so no full-run cost estimate is defensible.
- The AI-BOM audit is linked above. A completeness score is not recorded in this notes snapshot; the audit link does not assert cold-replay certification.
- The checkpoint includes the NVIDIA license and notices. Its recorded use scope is non-commercial research/evaluation; consult the packaged terms.

## Earlier private capture and evidence

The [historical private report](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/PRIVATE-CAPTURE.md), [capture summary](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/evidence/capture-summary.json), [findings](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/issues.md), and [command history](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/commands.md) preserve the prior attempt. Its artifacts remain private. Its source revision, loss, cost and operator identity must not be attributed to the later public run.

The public supervisor is pinned with the selected source above. The earlier report's training-operator identity belongs to the private capture; no new operator model identity is inferred for this public automation.
