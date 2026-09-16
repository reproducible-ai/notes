# LDA-1B

LDA-1B completed a public **one-step RoboCasa demo training capture** on 2026-09-15. All seven workflow tasks completed, followed by anonymous checkpoint checksum verification and public training-to-PUT lineage checks. This is a **partial training result**; policy quality, semantic equivalence to RoboCasa and independent cold replay remain untested.

## Public artifacts and lineage

- [Download the checkpoint at its immutable Hugging Face revision](https://huggingface.co/reproducible-ai/lda-1b-robocasa/tree/9dfddadf3513472415a304285b58f843971f7658/artifacts/lda-robocasa-canary/release/checkpoints).
- [Inspect the public GLaaS training lineage](https://glaas.ai/dag/d5c8d707ae657d6eeb9382079c12aacbd7f75b15142f73adb9f6eef2c0825d80).
- [View the GLaaS AI-BOM audit](https://glaas.ai/dag/d5c8d707ae657d6eeb9382079c12aacbd7f75b15142f73adb9f6eef2c0825d80/audit).
- [Read the verification receipt](https://github.com/reproducible-ai/notes/blob/main/028-robotics-lda-1b/evidence/public-release.json) and [release record](https://github.com/reproducible-ai/notes/blob/main/028-robotics-lda-1b/PUBLIC-RELEASE.md).

## Selected public run

| Field | Recorded value |
| --- | --- |
| Job | `dcc67bd2-b385-43d5-b0cf-b64b00fd59e0` |
| Executed source | [`fd78edbc1942903fe8dd073a208996bed014849e`](https://github.com/reproducible-ai/LDA-1B/tree/fd78edbc1942903fe8dd073a208996bed014849e) |
| Inputs | Four committed `sim_pick_place` demo episodes; pinned LDA RoboCasa checkpoint |
| Training settings | One optimizer step, batch 4, BF16, frozen Qwen/DINO; policy objective only |
| Hardware | 1× RTX PRO 6000 Blackwell Server 96 GB |
| Job duration | 1268.693 seconds (21m08.693s); scheduler clock |
| Finalized allocation cost | **$1.68**, including idle shutdown; allocation stopped |
| Publication transport | HTTP upload with `HF_HUB_DISABLE_XET=1` |

## Verification performed

The worker strict-loaded the checkpoint, checked **1,441 tensors** for finite floating values and proved `action_model.action_decoder.layer1.W` changed after one optimizer update. The published checkpoint is **14,422,502,892 bytes** with SHA-256:

```text
ddb9a15624b5f8aae304b27ba0fc6c89adae44a9c140edba3e76942f5696f009
```

The host anonymously streamed every published byte and checked manifest sizes and SHA-256 digests. The release has **17 manifest entries plus the manifest and result sidecar**. Readback matched the logged result. The host did not perform a second full model load.

Public lineage contains **5 jobs, 71 artifacts and 212 links**. Directed edges establish that the actual training output feeds PUT despite byte-identical packaging copies. The supervisor performed these checks and published the release automatically. The earlier private run's independent auditor PASS is historical; no independent public-run auditor verdict is claimed.

## Source, inputs and recipe differences

| Component | Pinned revision |
| --- | --- |
| Upstream source and demo | `06e6a274a9086cc26635a9fe663866335eb30fc5` |
| Public fork | `fd78edbc1942903fe8dd073a208996bed014849e` |
| LDA RoboCasa checkpoint/config | `Wayer2/LDA-robocasa@811d14d8c22d3e98021c035948118143f53dd312` |
| Qwen | `Qwen/Qwen3-VL-4B-Instruct@ebb281ec70b05090aa6165b016eac8ec08e71b17` |
| DINO architecture/license reference | `facebook/dinov3-vits16-pretrain-lvd1689m@114c1379950215c8b35dfcd4e90a5c251dde0d32` |
| Roar source build | `61e5e98ca823a25c19522870cb81d3ce730c391d`; package 0.4.7 |
| Shared public supervisor | `c084d6eab090a2b5822db474d790a00dfe7fae5d` |

DINO weights come from the strict-loaded LDA checkpoint. The demo adapter supplies two history observations, pads states to 58, preserves padded/masked 138-wide actions and maps embodiment slot 32 to Franka slot 4. This preserves checkpoint shapes but does not establish action-space semantics.

The pinned RoboCasa config specifies **300,000 steps**, versus this run's one step and four demo episodes. A full run also needs the intended data, objectives, trainable modules, batch size, learning rates and schedule; increasing the step count alone is insufficient. Setup-heavy one-step billing cannot support a full-run cost estimate.

See the [executed workflow](https://github.com/reproducible-ai/LDA-1B/blob/fd78edbc1942903fe8dd073a208996bed014849e/.treqs/workflows/robocasa-demo-canary.yaml), [commands and replay limitations](https://github.com/reproducible-ai/notes/blob/main/028-robotics-lda-1b/commands.md), and [patch inventory](https://github.com/reproducible-ai/notes/blob/main/028-robotics-lda-1b/patches/README.md). The website's displayed replay command has not been validated on a fresh host; its generic installation hint does not reproduce the pinned Roar source/native build by itself.

## Attempts and cost

| Recorded effort | Result | Final compute cost |
| --- | --- | ---: |
| Earlier private campaign, issues #32–#38 | Successful private capture after retries; selected private run cost $1.24 | $6.24 |
| First public attempt | Training and evaluation passed; Xet upload timed out | $2.41 |
| Selected public HTTP retry | All tasks and public verification passed | $1.68 |
| Public attempts subtotal | Within the separate $5 public-run budget | **$4.09** |
| Known private + public subtotal | Recorded compute only | **$10.33** |

The selected public job is `dcc67bd2-b385-43d5-b0cf-b64b00fd59e0`; the failed public job is `31910970-c97d-4fa6-994b-cf662153fc59`. Both allocations stopped. The retry kept the same training/model pins and disabled Xet for upload. [Costs and timing](https://github.com/reproducible-ai/notes/blob/main/028-robotics-lda-1b/costs.md) distinguish job duration, instance lifetime and excluded costs.

## Limitations and licensing

- No independent cold replay, held-out policy benchmark, full-scale training, author verification or certification is established. `verified` remains false and certification is unset.
- The shape-only demo adapter does not validate RoboCasa policy semantics.
- Roar's untracked-directory warning remains, and role labels are not sufficient evidence of the actual producer; verification used commands and directed edges.
- The AI-BOM audit is linked above. A completeness score is not recorded in this notes snapshot; no full-run cost is extrapolated.
- The checkpoint packages CC BY-NC 4.0, Apache 2.0 and DINOv3 component terms and notices. Built with DINOv3. The recorded release scope is non-commercial research/evaluation; consult those component terms.

## Earlier private capture and evidence

The [historical private report](https://github.com/reproducible-ai/notes/blob/main/028-robotics-lda-1b/PRIVATE-CAPTURE.md), [capture summary](https://github.com/reproducible-ai/notes/blob/main/028-robotics-lda-1b/evidence/capture-summary.json), [issue history](https://github.com/reproducible-ai/notes/blob/main/028-robotics-lda-1b/issues.md), [cost ledger](https://github.com/reproducible-ai/notes/blob/main/028-robotics-lda-1b/costs.md) and [patches](https://github.com/reproducible-ai/notes/blob/main/028-robotics-lda-1b/patches/README.md) preserve the earlier campaign. Its checkpoint digest, candidate revision and auditor verdict describe that private run, not the selected public run.

The current public supervisor and adapter are pinned above. An operator model identity was not recorded for this automation; no identity is inferred from the earlier private campaign.
