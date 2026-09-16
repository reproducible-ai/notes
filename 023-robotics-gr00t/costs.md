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
