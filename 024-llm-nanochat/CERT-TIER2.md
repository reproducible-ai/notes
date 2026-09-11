# Tier-2 cold certification attempt

Date: 2026-09-11  
DAG: `3571175fc75d017ea5ec71a9dc316b2a88c48e6460f6a2553d42c36a006fadfd`  
Result: **FAIL / BLOCKED** (certification spend ceiling)

The independent cold rebuild ran exactly:

```text
roar reproduce 3571175fc75d017ea5ec71a9dc316b2a88c48e6460f6a2553d42c36a006fadfd --lineage --run --no-puts -y --step-timeout 21600
```

The sole allowed attempt returned literal exit code `143` after an evidence-preserving stop. The output contained no `Steps run: N/M` summary.

Base training completed its full 2,506-step horizon. The rebuilt checkpoint reported validation BPB 0.830313, CORE 0.1719, 174.48 minutes of training, and 41,300.86 MiB peak device memory. Supervised fine-tuning then began from that checkpoint. At that point, projected completion exceeded the $25 certification not-to-exceed limit, so the independent certifier stopped the run. No retry was made.

The following partial outputs were regenerated before the stop:

| Path | Bytes | SHA-256 |
|---|---:|---|
| `outputs/nanochat/base_checkpoints/depth14/meta_002506.json` | 1,365 | `4ec0e71a7b82a2d20b33bcd7cab36019a46f23bc198bced7629f2cf854a0fad2` |
| `outputs/nanochat/base_checkpoints/depth14/model_002506.pt` | 1,126,739,160 | `111c5690d22ea8d2e2521e731632bb921a0fc6066c21cdb5540b9fc6bfb2cfdc` |
| `outputs/nanochat/base_checkpoints/depth14/optim_002506_rank0.pt` | 1,714,515,717 | `a657758674999c946f67368844642e7e7f19076dc1595dd7c5dcd265e7589f5e` |

The remaining SFT, evaluation, packaging, and final artifact outputs were not completed. This attempt therefore does not certify the row.

## Environment evidence

- Hardware: one RTX PRO 6000 Blackwell (`g7e.2xlarge`) in `us-east-2`
- Host lifetime: 3h56m21s
- Reproduction wall clock: 3h44m12s
- Estimated host spend: $13.25 at $3.363/hour
- Recorded dependency union: 29/29 exact, with no missing or mismatched pins
- Installed closure: 47 distributions; `uv pip freeze` and `importlib.metadata` independently agreed
- Executed interpreter: rebuilt virtual-environment Python 3.12.10
- The cold host was confirmed terminated after evidence collection

The certifier was independent of the capture operator and did not fix, recapture, or publish the workload.
