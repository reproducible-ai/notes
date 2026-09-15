# Obstacles

Causes remain unverified until supported by evidence. Service and harness findings must be attributed separately from model defects.

## P1 — Packaging previously trusted a passed status without binding verification to checkpoint bytes.

Verification now loads each tensor on CPU and records load verification plus trainer-state hash. Packaging checks verified shard, index, and trainer-state hashes before emitting receipts and includes taskMetric.

- Note: `c1d5947f-ef2a-4e27-b071-94f6cc95e7c9/operator/iterations/0001/receipt-verification-binding`
- Evidence: Supporting evidence retained privately
- Verified cause: Packaging accepted status, step count, and finite loss while assigning loadVerified unconditionally.
- Fix/workaround: Added verification evidence requirements and stale-file rejection.
- Upstream action: not assessed

## P1 — Existing tests hard-coded the placeholder publication repository.

Assertions now derive the repository from the workflow. Offline checks exercise a replacement repository and preserve complete checkpoint directory publication.

- Note: `c1d5947f-ef2a-4e27-b071-94f6cc95e7c9/operator/iterations/0001/publication-binding-tests`
- Evidence: Supporting evidence retained privately
- Verified cause: Literal placeholder assertions would fail after supervisor repository replacement.
- Fix/workaround: Made assertions binding-aware and added offline publication checks.
- Upstream action: not assessed
