# Cost and timing — row 016, Kronos

Instance: **g4dn.xlarge** (1x Tesla T4 16 GB, 4 vCPU), us-east-2, on-demand list
price **$0.526/h** = $0.0001461/s. `pricing:GetProducts` and
`ce:GetCostAndUsage` are both denied to this role, so the hourly rate is AWS
list price, not a metered figure.

## Attempts

| # | outcome | host lifetime | cost |
|---|---|---|---|
| 1 | setup failed — `uv: command not found` | ~4m | ~$0.04 |
| 2 | setup ok, `finetune_tokenizer` failed — `NameError: name 'safetensors' is not defined` | ~8m | ~$0.07 |
| 3 | ran through setup + fetch + 400 tokenizer steps, then the host disappeared mid-stage | ~20m | ~$0.18 |
| 4 | cancelled by me mid-tokenizer on a suspected non-portable torch pin (a false positive: `torch.__version__` said `2.3.0+cu121`, the distribution metadata said a plain `2.3.0`) | ~31m of a shared host | ~$0.27 |
| 5 | **COMPLETED** — DAG `847b359a…` | 65m32s | **$0.57** |

Attempt 3 is the one worth reading about: the `treqs run --follow` process on the
control host was killed by the harness, and the compute host terminated a few
minutes later with the job left `IN_PROGRESS` and no further log lines. Later
attempts were launched **detached, without `--follow`**, and polled instead.

Every attempt after the first landed on a WARM instance the target had already
used for another job, so "host lifetime" above is the share of
`i-0582575b7e7cab71f` and its predecessors attributable to each attempt, not a
clean per-attempt boot. Row total is about **$1.26**, of which **$0.57** is the
run that produced the record.

## Per-step timings (roar-measured, during the run)

| step | duration |
|---|---|
| `fetch_pretrained` | 4.5 s (trace 3.7 s + post 0.8 s) |
| `finetune_tokenizer` | 984.2 s (trace 983.6 s + post 0.6 s) |
| `finetune_predictor` | 2918.0 s (trace 2917.4 s + post 0.6 s) |
| traced total | 3906.7 s |
| job wall-clock | 3932 s (65m32s) |

Inside the stages, from upstream's own log lines: tokenizer epoch 16m17s,
predictor epoch 2910.78 s. Per optimizer step across 2,623 steps at batch 32:
**0.358 s** (tokenizer) and **1.077 s** (predictor).

The fixed/variable split is unusually lopsided here and the fixed half is the
weak measurement: the successful run's non-training overhead was only ~26 s
because the host was warm — roar and upstream's requirements were already
installed from the attempt before it. The weight download, which would be the
obvious fixed cost, is 4.5 s for 114 MB. A cold host must additionally boot
(174 s from provider-accept to agent-acquired, observed on attempt 1), clone,
`pip install -r requirements.txt` and install roar; ~6 minutes is a fair guess
and is 0.4% of a full 24.5-hour run, so it does not move the estimate.

## Full-run estimate

(see `row.json` -> `rebuild.fullRunEstimateBasis`)
