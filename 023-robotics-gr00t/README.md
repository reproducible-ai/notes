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
- No full-run cost is published. The calibration below measures a 32-episode slice, which is not upstream's data configuration; see "What this cost measurement covers".
- The AI-BOM audit is linked above. A completeness score is not recorded in this notes snapshot; the audit link does not assert cold-replay certification.
- The checkpoint includes the NVIDIA license and notices. Its recorded use scope is non-commercial research/evaluation; consult the packaged terms.

## Earlier private capture and evidence

The [historical private report](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/PRIVATE-CAPTURE.md), [capture summary](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/evidence/capture-summary.json), [findings](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/issues.md), and [command history](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/commands.md) preserve the prior attempt. Its artifacts remain private. Its source revision, loss, cost and operator identity must not be attributed to the later public run.

The public supervisor is pinned with the selected source above. The earlier report's training-operator identity belongs to the private capture; no new operator model identity is inferred for this public automation.

## What this cost measurement covers

**This is not a full-run cost, and the configuration it prices is not one to run as given.**

The calibration measured **$19 and 3.76 hours for 10,000 fine-tuning updates against the first 32 DROID episodes**, batch 32, BF16, on one 96 GB NVIDIA RTX PRO 6000 Blackwell Server Edition (`g7e.2xlarge`). The step count is upstream's `finetune.sh` default. The data is not: upstream's README calls the small sample *"for quick validation"* and says production training replaces `--dataset-path` with the full DROID dataset — ~358 GB and 95,658 episodes, against the 32 episodes (~0.12 GB) used here.

**Why the number does not extrapolate.** 32 episodes fit entirely in the host's 64 GB page cache, so every sample is served from memory and the video-decode cost amortises to nothing. At `episode_sampling_rate=0.1` those 32 episodes yield 320 distinct splits, and a 10,000-step run at batch 32 draws 320,000 samples from them — roughly a thousand repetitions each. At full data scale the arithmetic inverts: 320,000 draws against 27.6 M frames means each sample is seen fewer than once, nothing amortises, and every step pays AV1 seek-and-decode against a working set 5.5x larger than RAM. That decode term is absent from this measurement by construction, so $19 is a compute-bound floor for the untruncated run, not an estimate of it.

**Following this recipe produces an overfit model, not a reproduction.** A thousand passes over 320 splits is not what upstream's 10,000 steps are for.

**The hardware was inherited, not chosen.** The calibration ran on a Blackwell target that happened to be dormant, provisioned for unrelated work. roar recorded a peak of **39,042 MB against the card's 97,887 MB — about 40% used**. A 48 GB card fits that peak with headroom; whether it would be cheaper overall depends on throughput that was not measured. Read `g7e.2xlarge` below as what was used, not as what this workload needs.

The completed calibration ran independent 100-, 200- and 400-update points. After excluding the first 20 updates of each process, their measured rates were 1.0071, 1.0214 and 1.0293 seconds/update. Weighted across all 640 steady updates, training takes 1.024323 seconds/update. The full cosine schedule and 500 warmup updates were retained; early stopping did not shorten that schedule.

| Projected component | Seconds |
| --- | ---: |
| 10 full model/optimizer checkpoint saves | 1519.56 |
| Periodic policy evaluation (none in this recipe) | 0.00 |
| One-time finalization and allocation shutdown | 1195.05 |
| One-time boot, setup and input preparation | 509.72 |
| One-time training startup residual | 71.24 |
| 10,000 training updates | 10243.23 |

The sum is **3.76 allocation-hours**. At the recorded conservative **$4/allocation-hour** allowance, including bounded gp3 storage and IPv4, plus **$3.57 forecast transfer**, the calculation is **$18.61**, rounded up to **$19**. Finalization excludes the last measured checkpoint, which is already counted among the ten projected saves. These are forecast allowances, not actual invoice charges.

The original `ols/v1` calculation fitted total process time and rejected the estimate because adjacent slopes differed by about 40.8%. That result remains in the [original calibration record](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/evidence/calibration.json). This estimate uses an explicitly different method, `steady-throughput-plus-fixed/v1`, whose measured steady rates differ by 2.2%. It does not relabel the earlier audit as approving this new calculation.

The longest measured point is only 400 updates, so the projection extends it 25 times. The small observed rate spread is not a statistical confidence interval. Long-run performance, checkpoint behavior and prices may change. Frozen language/vision backbones, a trainable projector and diffusion model, SDPA, checkpoint cadence and data selection remain part of the estimated recipe.

The public capture's artifact, GLaaS lineage, AI-BOM and actual costs above remain unchanged. That capture used batch 1 and three episodes; the estimate comes from separate batch-32, 32-episode measurements. No additional training run was needed for this calculation, and no full run, convergence, policy quality or cold-replay certification is claimed.

[Calculation inputs and limitations](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/evidence/full-run-cost/input.json) · [calculated result](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/evidence/full-run-cost/estimate.json) · [raw timing evidence](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/evidence/full-run-cost/timings.json).

Recalculate with the [versioned calculator](https://github.com/reproducible-ai/reproducible-ai-harness/blob/9053553/scripts/estimate_cost.py):

```bash
python3 estimate_cost.py evidence/full-run-cost/input.json
```
