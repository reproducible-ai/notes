# Public LDA-1B RoboCasa canary

A fresh one-step public run used the same pinned recipe, four demo episodes, batch four and frozen Qwen/DINO components as the successful private capture.

- [Immutable Hugging Face checkpoint](https://huggingface.co/reproducible-ai/lda-1b-robocasa/tree/9dfddadf3513472415a304285b58f843971f7658/artifacts/lda-robocasa-canary/release/checkpoints)
- [Public GLaaS lineage](https://glaas.ai/dag/d5c8d707ae657d6eeb9382079c12aacbd7f75b15142f73adb9f6eef2c0825d80)
- [Executed source and automation](https://github.com/reproducible-ai/LDA-1B/tree/fd78edbc1942903fe8dd073a208996bed014849e/.treqs)
- TReqs job: `dcc67bd2-b385-43d5-b0cf-b64b00fd59e0`
- Full allocation cost: **$1.68**; compute stopped.

The worker strict-loaded the checkpoint, checked all 1,441 tensors for finite floating values, and proved an action tensor changed after one optimizer update. The host independently streamed every published byte anonymously, verified the manifest sizes and SHA-256 digests, matched the logged result, and confirmed the actual training output feeds PUT in the public graph. The host does not claim a second full model load or an independent lineage-auditor verdict.

The supervisor published this report automatically. The prior private capture and its audit remain historical evidence. This is a non-commercial demo training-path canary; cold replay, policy quality and semantic equivalence to RoboCasa remain untested. Roar's untracked-directory warning remains.

CC BY-NC 4.0, Apache 2.0 and DINOv3 component terms are included with the checkpoint. Built with DINOv3. See [public verification evidence](https://github.com/reproducible-ai/notes/blob/main/028-robotics-lda-1b/evidence/public-release.json).

## Public upload retry

The first public job `31910970-c97d-4fa6-994b-cf662153fc59` passed training and evaluation, then failed during Xet upload: `timed out reading request body`. Its finalized cost was **$2.41**. This fresh retry uses HTTP upload with the same model and training pins. Total public-run compute cost: **$4.09** within the original $5 budget.
