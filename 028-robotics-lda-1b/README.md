# LDA-1B

## Latest public run

See the [fresh public canary](PUBLIC-RELEASE.md) for public artifacts, lineage and verification. The original private capture is documented below.

An unattended one-step LDA RoboCasa training capture completed all seven workflow tasks, private checkpoint upload, independent artifact checks and a lineage audit. This is a bounded demo training-path result; model quality and cold reproduction have not been established.

## What was run

On 2026-09-14, campaign [#38](https://github.com/reproducible-ai/campaign-queue/issues/38) fine-tuned the pinned `Wayer2/LDA-robocasa` checkpoint for one optimizer step using the four committed `sim_pick_place` demonstration episodes. The task selected a 96 GB RTX PRO 6000 Blackwell target in us-east-2. The executed runtime guard checked that exactly one RTX PRO 6000 GPU was visible, with compute capability 12.0 and at least 90 GiB of memory. Final receipts identify the region and instance lifetime but do not record an instance-type or host-memory measurement. Per-device and effective batch size were four, accumulation was one, precision was BF16, and both Qwen and DINO were frozen. Only the policy objective was exercised.

The pinned RoboCasa config specifies 300,000 training steps and a different training dataset. The demo adapter supplies two history observations, pads 12-wide states to 58, preserves loader-padded/masked 138-wide actions, and maps the demo's out-of-range embodiment slot 32 to the existing Franka slot 4. Checkpoint keys and shapes were preserved. This shape adaptation does not establish the semantic equivalence of the demo and RoboCasa action spaces.

## Source and inputs

| Component | Recorded revision |
| --- | --- |
| [Upstream source](https://github.com/jiangranlv/LDA-1B) and committed demo | `06e6a274a9086cc26635a9fe663866335eb30fc5` |
| [Executed fork candidate](https://github.com/reproducible-ai/LDA-1B/blob/b55c26dad419064089f588837c5048843537577a/.treqs/README.md) | `b55c26dad419064089f588837c5048843537577a` |
| Recipe before the final operator candidate | `3308fc909418fdf7645b0ad097c654a7d9375d63` |
| LDA weights and RoboCasa config | `Wayer2/LDA-robocasa@811d14d8c22d3e98021c035948118143f53dd312` |
| Qwen input | `Qwen/Qwen3-VL-4B-Instruct@ebb281ec70b05090aa6165b016eac8ec08e71b17` |
| DINO architecture/license reference | `facebook/dinov3-vits16-pretrain-lvd1689m@114c1379950215c8b35dfcd4e90a5c251dde0d32` |
| Roar source build | `treqs/roar@61e5e98ca823a25c19522870cb81d3ce730c391d`; package 0.4.7 |
| Harness | `reproducible-ai-harness@7be12d448e75ca8a5b9b778b060bc1d3c742521b`; version 0.1.0 |

DINO weights came from the strict-loaded LDA checkpoint. The pinned RoboCasa config SHA-256 is `82ce61c4f70c71ecf7ff9dd0139c9de127f091f43803c785a7c786e35af5933d`. Setup used Python 3.11, PyTorch 2.9.0+cu128, torchvision 0.24.0+cu128, torchcodec 0.8.1, Accelerate 1.5.2 and DeepSpeed 0.17.6. Roar ran in a separate environment with huggingface-hub 0.36.0 and the preload tracer; its source import and eight native binary hashes were checked. The source pin distinguishes this build from an identically versioned PyPI package.

The operator receipt records Codex CLI 0.154.0 and the clean harness commit above. Its configured model is unknown because the runtime default was not recorded. The structured `operator` field is therefore omitted rather than populated with a placeholder identity; known launch facts are preserved in [the evidence summary](evidence/capture-summary.json).

## What the record contains

All seven workflow tasks completed: setup, fetch, train, evaluate, package, label and private publish. Training recorded one completed optimizer step. Checkpoint checks verified the input inventory, unchanged state-dict key set, finite floating tensors and an actual change to `action_model.action_decoder.layer1.W` among the trainable parameters. The checkpoint contains 1,441 tensors and is 14,422,502,892 bytes. Its SHA-256 is `561e66836412784e9011d0a9d19b731a22c77b8e7632d4badc18696ca209be7e`.

The harness independently read back and checked the 19-file private release, including exact agreement between the logged result and uploaded result sidecar. Published lineage contained 5 jobs, 71 artifacts and 212 links, matching the captured topology. The independent auditor passed the directed training-to-model-to-upload chain, including evaluation. Role labels remain imprecise, so the audit followed command content and directed edges.

The retained timeline shows no maintainer intervention between worker start and terminal PASS at 16:55:48 UTC. Earlier attempts required intervention and remain documented in [issues.md](issues.md) and [costs.md](costs.md). This observed unattended execution is distinct from the auditor's narrower lineage verdict.

Artifact locations, lineage addresses and raw evidence remain private. No public reproduction command, hosted experiment result or AI-BOM score is asserted. The workflow's evaluation stage checks checkpoint integrity and a real update; it does not measure held-out policy success.

## Changes from upstream

The [pinned upstream-to-candidate diff](https://github.com/reproducible-ai/LDA-1B/compare/06e6a274a9086cc26635a9fe663866335eb30fc5...b55c26dad419064089f588837c5048843537577a) contains 3,626 added and 36 deleted lines across 47 files (3,662 changed lines). Of those, the ten `lda/` runtime files account for 155 additions and 15 deletions; dependency files add 7 and delete 21 lines. The remainder is workflow/scripts, records, regression tests and ignore rules. This distinction avoids presenting the whole integration bundle as model-code changes.

Runtime changes cover strict checkpoint loading, checkpoint-compatible initialization, explicit demo adaptation, compatible attention/loading paths, and training evidence/error handling. The recipe also supplies the Blackwell dependency set, GPU optimizer placement, pinned Roar source install and portable receipt paths. [commands.md](commands.md) gives the recorded recipe and exact diff commands. The [patch inventory](patches/README.md) includes the exact runtime/dependency diff and identifies the broader integration changes in the pinned comparison.

## Attempts and cost

Seven linked harness attempts (#32–#38) include one preflight rejection, one unallocated job and eight paid jobs. Finalized compute spend is **$6.24**, including **$5.00** before the final run and **$1.24** for the successful capture. The final job lasted **17m50.508s**; its instance lifetime was **22m25.707s**, including provisioning and shutdown. [costs.md](costs.md) lists each job, duration and failure. The structured `rebuild` fields describe this final capture, not a separately measured cold replay.

## Limits of the result

This record remains `progress` with `verified: false`. No cold rebuild, policy-quality benchmark, full dataset training, public artifact/lineage publication or defensible full-run cost estimate has been completed. The retained untracked-directory warning and role-label limitation are disclosed. Known parameter changes and what must be revisited for a full run are listed in `row.json`.

Component terms are recorded separately: source/demo CC-BY-NC-4.0, LDA/Qwen weight metadata Apache-2.0, and the DINOv3 License. The private run preserved those notices; it does not establish permission for a broader distribution or training scope. The original certification campaign's licensing gate was not reopened by this canary.
