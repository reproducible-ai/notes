# nanochat depth 14

The full depth-14 pipeline completed on one 96 GB Blackwell GPU and produced a public 983 MB model artifact plus a public lineage record. The record passes **Tier 1**: the clean-DAG check is 14/14, the AI-BOM is 100/100, every public URL resolves, and the recorded dependency freeze is portable. A later independent cold rebuild returned exit code 0, completed all five reproduction steps, and regenerated the final package, so the row now passes **Tier 2** as a certified reproduction.

## What was run

This row uses nanochat's own `--depth` complexity dial rather than shortening training. Depth 14 derives a 399,114,882-parameter model and a 1,313,865,728-token compute-optimal horizon. The run completed all 2,506 pretraining iterations, base evaluation, supervised fine-tuning, chat evaluation, packaging, and artifact publication.

The upstream speedrun assumes eight GPUs. On one GPU, gradient accumulation increased to eight while each microbatch remained 32 sequences of 2,048 tokens. The resulting global batch stayed exactly 524,288 tokens, so the topology changed without changing the batch seen by each optimizer step.

The accelerator identified itself as an NVIDIA RTX PRO 6000 Blackwell Server Edition with compute capability sm_120, with GPU accounting reported as Enabled. A real matrix multiplication and the selected PyTorch SDPA attention path were asserted before data download. The workload ran in an isolated virtual environment, and a fail-loud check confirmed that its source declaration, lock, and installed distribution agreed on the tokenizer dependency before training.

## Calibration chose depth 14

Depth 16 was tested first. Its five-step steady-state median was 5.429 seconds, projecting 5.40 hours for its complete 3,584-iteration horizon—well beyond the 3.5-hour pretraining ceiling. That calibration stopped cleanly before full training.

Depth 14 calibrated at a 4.197-second steady-state median and projected 10,518 seconds of pretraining, inside the 12,600-second ceiling. The observed pretraining task ultimately took 12,018 seconds. The calibration was close enough to select a viable configuration while its explicit ceiling still failed loudly for the larger one.

## Results

| Stage | Result |
|---|---:|
| Pretraining final validation BPB | 0.830315 |
| Standalone base CORE | 0.1633 |
| SFT final validation BPB | 0.3393 |
| SFT final ChatCORE | 0.0981 |
| Standalone chat ChatCORE | 0.0998 |
| Standalone HumanEval | 8.54% |

These values identify the produced result; they are not replication targets. The reproduction claim is about rebuilding the recorded outputs from the record, not matching a metric value.

## Why ten attempts are recorded

The attempt ledger is part of the result. Three short depth-16 runs established the hardware path, corrected its fail-loud control, and measured the configuration out of bounds for the run window. The first depth-14 full-horizon attempt finished pretraining and base evaluation but stopped during supervised fine-tuning before its spend cap. A second completed every workload and uploaded the artifact but produced no lineage record. A third published the first lineage record. Two short follow-ups established a fresh recorder target and corrected a fail-loud setup assertion. The ninth and tenth attempts each completed all thirteen tasks; the tenth published the current authoritative lineage.

The final attempt cost $19.66. Total metered compute across the ten attempts was $96.97. Keeping both figures avoids presenting the cost of the successful job as the cost of reaching the result.

## The record passes Tier 1

The public lineage contains the full code commit, ordered workload, produced artifacts, runtime metadata, and a 100/100 AI-BOM. All referenced public URLs resolve. The recorded dependency set is portable, and the two reproduction scripts beside this file are generated verbatim from the lineage.

The complete Tier-1 gate passed against the existing published lineage: strict clean-DAG 14/14, AI-BOM 100/100 Advanced, all public URLs readable, portable freeze, and row schema valid. A later independent Tier-2 attempt returned literal exit code 0 with `Steps run: 5/5`, regenerated the final model package, matched all 29 recorded dependency pins, and used the rebuilt CPython 3.12.10 environment.

## Upstream portability edit

The published attention loader selects a Flash Attention 3 kernel on CUDA architectures beyond those for which it names explicit support. Blackwell sm_120 needs the existing SDPA fallback. The fork makes that selection explicit: Hopper and Ampere use their supported FA3 repositories; other compute majors use SDPA.

Both sides were exercised. A negative control using the original broad predicate selected FA3 for simulated sm_120 and failed, while the patched policy returned no FA3 repository for sm_120 and the actual GPU completed a real SDPA operation. The change affects kernel choice, not model dimensions, token horizon, or global batch.

## Reproduction status

Authoritative lineage: [`3571175f…fadfd`](https://glaas.ai/dag/3571175fc75d017ea5ec71a9dc316b2a88c48e6460f6a2553d42c36a006fadfd).

The reader-facing command is:

```sh
roar reproduce 3571175fc75d017ea5ec71a9dc316b2a88c48e6460f6a2553d42c36a006fadfd --lineage --run --no-puts
```

Tier 1 and Tier 2 both pass. See [`CERT-TIER2.md`](CERT-TIER2.md) for the successful cold-rebuild evidence and the retained history of the earlier stopped attempt.
