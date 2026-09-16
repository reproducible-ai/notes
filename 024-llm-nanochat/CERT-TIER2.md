# Tier-2 cold certification

Date: 2026-09-15
DAG: `3571175fc75d017ea5ec71a9dc316b2a88c48e6460f6a2553d42c36a006fadfd`  
Result: **PASS**

An independent cold rebuild ran exactly:

```text
roar reproduce 3571175fc75d017ea5ec71a9dc316b2a88c48e6460f6a2553d42c36a006fadfd --lineage --run --no-puts -y --step-timeout 21600
```

The command returned literal exit code `0` and reported `Steps run: 5/5`. All five
pipeline steps succeeded: data preparation, tokenizer training, base training,
supervised fine-tuning, and model packaging. The final tracer fallback-signature
count was zero.

The host exposed only the preload tracer launcher as executable. Automatic tracer
selection chose preload, its preflight produced a report, and the live training
processes were parented by `roar-tracer-preload`.

## Regenerated outputs

| Path | Bytes | SHA-256 |
|---|---:|---|
| `outputs/nanochat-depth14.tar.gz` | 982,835,675 | `cee357fed40c4839825933a257217f9524bdd6221d4cb2140f16e61a47a8b5ce` |
| `outputs/nanochat/base_checkpoints/depth14/meta_002506.json` | 1,364 | `6224204699b1cb475c0c6c5d4cac76e47fcc3f07ae58e48a39d2e77639ebf015` |
| `outputs/nanochat/base_checkpoints/depth14/model_002506.pt` | 1,126,739,160 | `70ed104dff80779a39d6f67385aa581a3604bc8fb290f8188ad7ea37fc73cb8c` |
| `outputs/nanochat/base_checkpoints/depth14/optim_002506_rank0.pt` | 1,714,515,717 | `15c567c5636ab701c26282fc0d644272acac34ec451aab80da27a979f290a37e` |
| `outputs/nanochat/chatsft_checkpoints/depth14/meta_000934.json` | 859 | `891a01425ff9a1f588160c735d8607e89696ca684c79d981aad983016e7b1510` |
| `outputs/nanochat/chatsft_checkpoints/depth14/model_000934.pt` | 1,126,739,160 | `4eef437e6af43dcadcb97b33b681236d6eb74e3886b07fbaf0ad738525850166` |
| `outputs/nanochat/chatsft_checkpoints/depth14/optim_000934_rank0.pt` | 1,714,515,717 | `3e02b2b254a7b99ea0fd7beed9e09a3e050950797d3a067790b05fd6a6142ea8` |

## Environment evidence

- Recorded dependency union: 29/29 exact, with no missing or mismatched pins.
- Installed closure: 47 distributions. `uv pip freeze` and
  `importlib.metadata` independently enumerated the same 47 distributions.
- Executed interpreter: the rebuilt virtual environment's CPython 3.12.10.
- Hardware: one RTX PRO 6000 Blackwell (`g7e.2xlarge`) in `us-east-2`.
- Reproduction wall clock: 5h06m32s.
- Host lifetime: 5h19m52s.
- Estimated attempt spend: $17.94.
- Cumulative estimated spend through this attempt: $177.28.
- The host was confirmed terminated after evidence collection.

The certifier was independent of the capture operator and did not modify, recapture,
or publish the workload.

## Earlier certification attempt

The earlier independent attempt on 2026-09-11 remains part of the history. It
returned exit code `143` after an evidence-preserving stop at its spend ceiling and
did not emit a `Steps run: N/M` summary. It completed base training and began SFT,
but did not produce the final package. Its partial output hashes and environment
evidence remain available in the branch commit that recorded that attempt.
