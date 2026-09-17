# Attempts and cost

The selected public run cost **$1.57**. The earlier private capture cost **$1.52**. Known compute across these two recorded jobs is **$3.09**.

`row.json.rebuild` describes the selected public job's scheduler duration and finalized allocation cost, including idle shutdown. These are different clocks; neither measures optimizer time. No cold replay or full-training cost was measured. Totals exclude unmeasured development, tokens, storage, transfer and other services.

## Public runs

| Run | Job | Job seconds | Instance lifetime seconds | Final USD | Result |
| --- | --- | ---: | ---: | ---: | --- |
| Public 100-step run | `f282527c-4573-4a28-afae-29033e75c4c6` | 576.804 | 1737.346 | $1.57 | Completed; allocation stopped |

See [timing and finalized cost observations](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/evidence/public-run-timing.json) and [public verification evidence](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/evidence/public-release.json).

## Earlier private campaign ledger

The ledger and budget discussion below apply to the earlier private campaign only. Its original evidence is preserved.

Finalized per-job charges are distinct from scheduler estimates. Repeated observations of one job are counted once.

| Job | Outcome | Job seconds | Actual USD | Cost source | Estimated USD |
|---|---|---:|---:|---|---:|
| edd28f95-2805-4985-90ea-52af84f65dab | ok | 755.963 | 1.52 | reconciliation.jobActualCostUsd | 0.67 |

Known compute subtotal: $1.5200 across 1 of 1 recorded jobs.
Historical private selected-run cost: 1.52 USD. This is capture cost, not a measured cold replay.
Unknown charges are not assigned zero. These charges exclude unmeasured development, token, storage and transfer costs.

## Attempt outcomes

| Issue / attempt | Harness outcome | Recorded jobs |
|---|---|---:|
| #39 / c1d5947f-ef2a-4e27-b071-94f6cc95e7c9 | PASS | 1 |

## Task timings

Task durations and job duration are different clocks; neither is an optimizer-step duration.

| Attempt | Task | Status | Exit code | Seconds |
|---|---|---|---:|---:|
| c1d5947f-ef2a-4e27-b071-94f6cc95e7c9 | setup | COMPLETED | 0 | unknown |
| c1d5947f-ef2a-4e27-b071-94f6cc95e7c9 | fetch_droid | COMPLETED | 0 | unknown |
| c1d5947f-ef2a-4e27-b071-94f6cc95e7c9 | train | COMPLETED | 0 | unknown |
| c1d5947f-ef2a-4e27-b071-94f6cc95e7c9 | evaluate | COMPLETED | 0 | unknown |
| c1d5947f-ef2a-4e27-b071-94f6cc95e7c9 | package | COMPLETED | 0 | unknown |
| c1d5947f-ef2a-4e27-b071-94f6cc95e7c9 | label | COMPLETED | 0 | unknown |
| c1d5947f-ef2a-4e27-b071-94f6cc95e7c9 | publish | COMPLETED | 0 | unknown |


## Calibration allocations

The original process-time fit rejected the estimate for inconsistent slopes. Its result is preserved; the separate steady-throughput calculation below estimates the declared full recipe.

These charges are separate from the preserved public capture and its historical ledger.

| Job | Outcome | Duration seconds | Finalized USD | Cost source |
| --- | --- | ---: | ---: | --- |
| 5e175ec6-6369-41ee-8de2-8ef9403e037d | failed | 650.989 | 1.4 | observations/budget.jsonl:122 |
| cacd46e3-5884-4e4e-971c-dbeb4f608adb | failed | 505.888 | 1.57 | observations/budget.jsonl:136 |
| e9b250f1-d3fb-4c7f-96e6-4ded702ec0cf | failed | 2830.975 | 3.42 | observations/budget.jsonl:371 |
| a9a97def-9cd3-4f74-ac1d-3634b605557a | ok | 2522.672 | 2.92 | reconciliation.jobActualCostUsd |

Known calibration charges: $9.31 across 4 of 4 allocations. Unknown charges remain unknown; each job is counted once.

Setup, all calibration points and shutdown share the allocation charge. The full-run projection is a separate estimate and is not included in actual spend.

[Timing, assumptions and projection breakdown](https://github.com/reproducible-ai/notes/blob/main/023-robotics-gr00t/evidence/calibration.json).

## Projected full recipe

Approximately $19 for the declared 10,000-update DROID fine-tuning scenario: 32 pinned episodes, batch 32, BF16, one 96 GB RTX PRO 6000 Blackwell (g7e.2xlarge). The steady-throughput-plus-fixed/v1 method uses 655.566671 measured seconds / 640 steady updates = 1.024323 s/update. Add measured setup (509.72 s), mean process startup (71.24 s), 10 checkpoint saves (151.96 s each), and finalization/shutdown (1195.05 s), with no periodic policy evaluation. Total about 3.76 allocation-hours at the recorded $4/hour allowance plus $3.57 forecast transfer = $18.61, rounded up to $19. Low confidence; longest measured point was 400 updates. The earlier ols/v1 process-time fit remains rejected for inconsistent slopes; this separately documented method uses steady training timings.

This forecast is separate from the $9.31 actual calibration compute ledger and the $3.09 earlier capture subtotal. It is not added to actual spend. See [inputs](evidence/full-run-cost/input.json) and [calculation](evidence/full-run-cost/estimate.json).
