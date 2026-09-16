# GR00T N1.7

Recorded partial training capture on DROID 1.0.1. Harness outcome: PASS; scheduler: COMPLETED. Recorded optimizer steps: 100. Cold reproduction and model quality are not established by this capture.

## What was run

| Field | Recorded value |
|---|---|
| Dataset | DROID 1.0.1 |
| Selected attempt | c1d5947f-ef2a-4e27-b071-94f6cc95e7c9 |
| Source revision | 9124d64bc9b19f118285939e8ffd29ce5f094733 |
| Executed revision | 143ffa3da28a11f037c2a0628fb796ef1f93e5ce |
| Hardware | unknown |
| Duration | 755.963s |

## Results

- optimizerSteps: 100
- finalLoss: 0.0893
- loadVerified: True
- Artifact sha256: 12117379d91d029c5979a585d07ba794001730c9516d6de5512e3dedfee30730
- Artifact sizeBytes: 104913
- Artifact format: gr00t-n1.7-safetensors-checkpoint
- Artifact loadVerified: True

## Attempts and cost

Known compute subtotal: $1.5200 across 1 of 1 recorded jobs. Selected-run cost: 1.52 USD.
See [costs](costs.md) for individual jobs, unknown charges and timing sources.

## Attempt history

| Issue / attempt | State | Recorded outcome | Scheduler | Blocker |
|---|---|---|---|---|
| #39 / c1d5947f-ef2a-4e27-b071-94f6cc95e7c9 | completed | PASS | COMPLETED | unknown |

## Findings and decisions

### Packaging previously trusted a passed status without binding verification to checkpoint bytes.

issue: Verification now loads each tensor on CPU and records load verification plus trainer-state hash. Packaging checks verified shard, index, and trainer-state hashes before emitting receipts and includes taskMetric.

Evidence: Supporting evidence retained privately

Verified cause: Packaging accepted status, step count, and finite loss while assigning loadVerified unconditionally.
Resolution: Added verification evidence requirements and stale-file rejection.

### Existing tests hard-coded the placeholder publication repository.

issue: Assertions now derive the repository from the workflow. Offline checks exercise a replacement repository and preserve complete checkpoint directory publication.

Evidence: Supporting evidence retained privately

Verified cause: Literal placeholder assertions would fail after supervisor repository replacement.
Resolution: Made assertions binding-aware and added offline publication checks.

### Corrected the documented ceiling from $15 to $5.

decision: The supervisor must enforce total cost across all stages. Existing stage timeouts do not enforce a dollar ceiling. Also corrected the source revision and removed an unsupported success assertion.

Evidence: Supporting evidence retained privately

Verified cause: Inherited documentation specified a different budget and source revision.
Resolution: Aligned documentation with the task packet.

### Tensor-dependent tests could not run locally.

observation: The local Python environment lacks PyTorch. Standard-library contract tests, compilation, and lint passed. The existing dependency-enabled suite remains in supervisor setup before training. Synthetic receipt fixtures do not establish checkpoint readability or model quality.

Evidence: Supporting evidence retained privately

Verified cause: PyTorch is not installed in the local Python environment.
Resolution: unknown


## Evidence and limitations

[Capture summary](evidence/capture-summary.json) records source revisions, receipt hashes and supporting-file availability.
See [commands](commands.md) and [issues](issues.md).

- Evidence and artifacts remain private; this report does not publish them.
- Training capture does not establish cold certification or full reproduction.
- Missing measurements remain unknown; no full-run cost extrapolation is asserted.
- Private artifact destinations are redacted from narrative observations.
- Text and commands containing private references are omitted; originals remain in private evidence.
- Finalization required authorized recovery under harness revision d43724ce6db07481dd48f3b78488f948e97cc186; the original run did not complete unattended.

## Public artifacts and lineage

See the [fresh public canary](PUBLIC-RELEASE.md) for verified downloads and public GLaaS lineage.
