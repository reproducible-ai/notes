# Attempts and cost

The selected public run cost **$1.68**; the failed public upload attempt cost **$2.41**. Public attempts total **$4.09**. The earlier private campaign cost **$6.24**, making known compute across the recorded private and public history **$10.33**.

`row.json.rebuild` describes the selected public job's scheduler duration and finalized allocation cost, including idle shutdown. These are different clocks; neither measures optimizer time. No cold replay or full-training cost was measured. Totals exclude unmeasured development, tokens, storage, transfer and other services.

## Public runs

| Run | Job | Job seconds | Instance lifetime seconds | Final USD | Result |
| --- | --- | ---: | ---: | ---: | --- |
| First public attempt | `31910970-c97d-4fa6-994b-cf662153fc59` | 1847.603 | 2586.682 | $2.41 | Training passed; Xet upload failed; allocation stopped |
| Selected public HTTP retry | `dcc67bd2-b385-43d5-b0cf-b64b00fd59e0` | 1268.693 | 1806.462 | $1.68 | Completed; allocation stopped |

See [timing and finalized cost observations](https://github.com/reproducible-ai/notes/blob/main/028-robotics-lda-1b/evidence/public-run-timing.json) and [public verification evidence](https://github.com/reproducible-ai/notes/blob/main/028-robotics-lda-1b/evidence/public-release.json).

## Earlier private campaign ledger

The ledger and budget discussion below apply to the earlier private campaign only. Its original evidence is preserved.

Finalized LDA compute spend across issues #32–#38 is **$6.24**. The completed final capture cost **$1.24**; earlier paid jobs cost **$5.00**. Costs come from final on-demand instance receipts, not the scheduler estimate.

## Per-job ledger

Job duration is scheduler start to terminal state. Instance duration includes provisioning and idle/shutdown time. These are separate clocks; neither is the one-step optimizer time.

| Issue / job | Job duration (s) | Instance lifetime (s) | Final cost (USD) | Result |
| --- | ---: | ---: | ---: | --- |
| #32 preflight | — | — | unknown / no job | Missing declared upload secret; no job or billing receipt exists. |
| #33 / `046cf5fb-9f4d-4e69-babd-b976e091d143` | — | — | $0.00 | Cancelled before allocation; no workflow task ran. |
| #34 / `60d9d509-5cec-4640-9823-3304c2cf8769` | 73.064 | 603.164 | $0.56 | Dependency resolution failed before training. |
| #34 / `9f8ea77a-413c-49d3-9733-2de2f07437fe` | 303.142 | 496.665 | $0.45 | Accelerate/DeepSpeed precision configuration failed before an optimizer update. |
| #34 / `7609a41a-c4d3-425e-855a-66626a941ae9` | 315.469 | 534.506 | $0.45 | Custom-sampler batch inference failed before an optimizer update. |
| #35 / `9e20d416-65db-4ce4-bbcb-6cba05a3e561` | 541.076 | 695.528 | $0.62 | Host OOM during optimizer preparation; no update. |
| #35 / `5020d01f-3078-42e8-89f4-e18459560749` | 332.256 | 536.502 | $0.45 | Demo/checkpoint shape failure after moving optimizer state to GPU; no update. |
| #36 / `1055f170-bcbd-45c4-b15d-ceafbaf5c61e` | 1033.332 | 1299.002 | $1.18 | All seven tasks and one update completed, but independent lineage verification blocked the attempt (3/57/120 published versus 5/71/212 captured). |
| #37 / `4b0d301d-b5dd-428b-9465-62d3dd18ee73` | 1055.853 | 1432.179 | $1.29 | All seven tasks, one update and full lineage completed; independent result-sidecar equality failed. Maintainer intervention occurred; attempt BLOCKED. |
| #38 / `9740975f-4f5d-4116-aaba-4e5a43616c42` | 1070.508 | 1345.707 | $1.24 | All seven tasks completed; 19 private files independently checked; full lineage and auditor PASS. Observed unattended from worker start to terminal PASS; no cold rebuild certification. |

#34 totals $1.46 across three jobs; #35 totals $1.07 across two. Its final repair candidate was rejected before another launch. #36 totals $1.18; #37 totals $1.29; #38 totals $1.24. #33's finalized zero is retained. #32 has no cost receipt and is not assigned an invented zero; no compute launch was recorded. All eight paid jobs have finalized cost and stopped-instance receipts.

The original LDA approval was $15.00. The final attempt had a $5.00 cap, and $8.76 remains after the recorded $6.24 compute spend. Budget limits are not charges. This ledger does not include unmeasured human/agent development costs, token usage, storage, network transfer or external service charges. No larger all-in cost is inferred.

## Final capture timing

| Stage | Scheduler task duration (s) |
| --- | ---: |
| setup | 125.475 |
| fetch | 165.464 |
| train | 486.736 |
| evaluate | 111.968 |
| package | 64.980 |
| label | 0.380 |
| publish | 51.350 |

These durations come from task start/completion events. They include wrapper overhead and differ from inner Roar trace timings. The job's 1,070.508 seconds also include repository preparation, final lineage export and orchestration. Instance lifetime was 1,345.707 seconds. Independent readback and audit continued after the job completed; terminal harness PASS was recorded at 16:55:48 UTC.

## Final capture versus full rebuild

The historical private capture cost $1.24 and lasted 17m50.508s; current `row.json.rebuild` selects the public run above. There is no separately measured cold replay or cost for reproducing the full published training recipe. One optimizer step on four demo episodes with frozen encoders cannot support a defensible full-run extrapolation, so `fullRun.estimateUsd` remains null.
