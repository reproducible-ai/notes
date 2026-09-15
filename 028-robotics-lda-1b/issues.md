# Issues encountered

This is the history of linked campaign issues #32–#38, including resolved failures. BLOCKED attempts are retained; a scheduler COMPLETED state alone does not establish harness acceptance.

## 1. Missing declared upload credential (P1)

**Symptom / cause:** #32 was rejected before compute because the workflow did not declare the credential required by its private upload.

**Fix / disposition:** Declare HF_TOKEN in workflow secrets and preflight input access.

**Upstream action:** Recipe integration fix; no upstream model defect asserted.

**Record:** [campaign #32](https://github.com/reproducible-ai/campaign-queue/issues/32); detailed logs and receipts retained privately.

## 2. No allocation on the initial compute route (P1)

**Symptom / cause:** #33 ended without acquiring an instance or running a task; finalized compute cost was $0.00.

**Fix / disposition:** Continue on an existing compatible 96 GB Blackwell target.

**Upstream action:** Compute routing issue; no upstream model change.

**Record:** [campaign #33](https://github.com/reproducible-ai/campaign-queue/issues/33); detailed logs and receipts retained privately.

## 3. Cold dependency resolution and Blackwell compatibility (P1)

**Symptom / cause:** #34 first failed dependency resolution across PyPI and the CUDA wheel index.

**Fix / disposition:** Use the aligned CUDA 12.8 dependency pins and explicit uv index strategy in the pinned setup recipe.

**Upstream action:** Potential upstream environment documentation improvement; no upstream PR recorded.

**Record:** [campaign #34](https://github.com/reproducible-ai/campaign-queue/issues/34); detailed logs and receipts retained privately.

## 4. Precision ownership and custom-sampler batch inference (P1)

**Symptom / cause:** #34 next failed duplicated Accelerate/DeepSpeed precision settings, then failed batch-size inference because the custom DataLoader exposed no batch_size.

**Fix / disposition:** Keep BF16 in the DeepSpeed JSON and explicitly set micro/global batch size 4 with accumulation 1.

**Upstream action:** Recipe integration fixes; retained regression coverage.

**Record:** [campaign #34](https://github.com/reproducible-ai/campaign-queue/issues/34); detailed logs and receipts retained privately.

## 5. Host OOM followed by demo/checkpoint mismatch (P1)

**Symptom / cause:** #35 hit confirmed host OOM during optimizer preparation. Moving optimizer state to GPU exposed the demo input mismatch. A further candidate was rejected before launch because it expected action width 29 and lacked two history observations.

**Fix / disposition:** Disable CPU optimizer offload; use the pinned 58/138/2/32 contract and an explicit shape-only demo adapter. Initialize the exception-path output variable so the original failure is preserved.

**Upstream action:** Exception handling is a potential upstream fix. Demo adaptation is canary-specific and has not established policy semantics.

**Record:** [campaign #35](https://github.com/reproducible-ai/campaign-queue/issues/35); detailed logs and receipts retained privately.

## 6. Retry ownership checkpoint and manual recovery (P1)

**Symptom / cause:** Earlier retries required a harness staging-ownership checkpoint correction and maintainer recovery. Idle failed-job instances were manually stopped. Those attempts are not unattended successes.

**Fix / disposition:** Preserve the same owned private destination during retry and retain append-only intervention records; continue under the remaining original budget.

**Upstream action:** Harness fix 12105c06493f949873f84caf3dcd53713037340b; no upstream model change.

**Record:** [campaign #34](https://github.com/reproducible-ai/campaign-queue/issues/34); detailed logs and receipts retained privately.

## 7. Published lineage omitted train and evaluate (P1)

**Symptom / cause:** #36 completed training and upload, but publication contained only 3 jobs / 57 artifacts / 120 links versus the captured 5 / 71 / 212. Traversal selected only the latest producer of byte-identical copied content.

**Fix / disposition:** Install Roar main at 61e5e98ca823a25c19522870cb81d3ce730c391d, including the merged multiple-producer traversal fix; verify a fresh run.

**Upstream action:** Roar PR #302 was merged. The incomplete historical publication was retained as blocked.

**Record:** [campaign #36](https://github.com/reproducible-ai/campaign-queue/issues/36); detailed logs and receipts retained privately.

## 8. Portable receipts and bounded verification failure (P1)

**Symptom / cause:** #37 completed the workload and full lineage publication. Readback was delayed by a network outage, then failed because two evaluation paths were redacted in logs but remained absolute in the uploaded result. An uncaught verification error caused worker restarts.

**Fix / disposition:** Use repository-relative evaluation paths (recipe 3308fc9) and retain invalid artifacts as BLOCKED (harness 7be12d4). Run #38 afresh after both fixes.

**Upstream action:** Model recipe and harness fixes; prior result preserved. Maintainer intervention prevents an unattended-success claim for #37.

**Record:** [campaign #37](https://github.com/reproducible-ai/campaign-queue/issues/37); detailed logs and receipts retained privately.

## 9. Lineage role labels remain imprecise (P2)

**Symptom / cause:** #38 labels the training wrapper as other and packaging as training; the latest producer field identifies packaging. An additional directed producer edge identifies the actual training command.

**Fix / disposition:** The independent auditor checked commands and directed edges, not the role heuristic alone. Role labeling remains a follow-up.

**Upstream action:** Platform follow-up; no role-label fix is claimed.

**Record:** [campaign #38](https://github.com/reproducible-ai/campaign-queue/issues/38); detailed logs and receipts retained privately.

## 10. Untracked-directory warning remains (P2)

**Symptom / cause:** Roar reported untracked artifact directories during the final publication path.

**Fix / disposition:** Retain the warning and bound the result to the independently checked published inventory and lineage. No warning-free capture claim.

**Upstream action:** Capture/filtering follow-up; no fix is claimed.

**Record:** [campaign #38](https://github.com/reproducible-ai/campaign-queue/issues/38); detailed logs and receipts retained privately.

## Remaining scope

There is no held-out robotics evaluation or cold-rebuild certification. Full-data licensing, embodiment semantics, quality targets and a full-run estimate remain outside the completed canary. These are disclosed limitations, not missing evidence for the one-step capture itself.
