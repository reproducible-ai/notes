# RWKV-7 on MiniPile

This rebuild is blocked before training. The current published RWKV-7 MiniPile entry point loads a CUDA channel-mix extension whose source does not compile for the NVIDIA L40S GPU's `sm_89` architecture, so there is no checkpoint, loss, published DAG, or experiment run to claim.

## What was attempted

The capture followed the current files under `RWKV-v7/train_temp` at upstream commit `658042ca30222715c1d3ab662a3c556824dc6618`. It retained the published L12-D768 model, 512-token context, MiniPile binidx data, bf16 precision, one GPU, DeepSpeed stage 2, and the repository's two-stage flow: generate `rwkv-init.pth`, then train from it.

The only intended budget reduction was the repository's existing `--my_exit_tokens` option. It was set to 16,384 tokens, enough for two optimizer steps at micro-batch 16 and context length 512. The upstream WandB option was enabled for the training stage; no logging code was added.

The clean dependency environment used Python 3.12 with exact top-level pins for PyTorch, PyTorch Lightning 1.9.5, DeepSpeed, WandB, Trackio, Ninja, NumPy, Requests, and Setuptools. A fresh-clone check imported that set without host `dist-packages`, found no local-version distribution pins, and parsed the exact training entry point. The GPU-only CUDA compilation could not be exercised on the free control host.

## Where it failed

The paid run completed environment setup and downloaded both published MiniPile files. The dataset reader opened the index and reported 1,498,226,207 tokens, matching the recipe. Initialization then imported `src/model.py`, which JIT-compiles the repository's CUDA extensions.

The first extension, `rwkv7_clampw`, compiled successfully for `compute_89` / `sm_89`. The next extension failed in `cuda/rwkv7_cmix_bf16_v5.cu`:

```text
error: no instance of overloaded function "atomicAdd" matches the argument list
argument types are: (float2 *, float2)
```

The failing helper at lines 20–22 casts a float pointer to `float2*` and calls vector `atomicAdd`. That overload is not available for the generated sm_89 target. Ninja stopped, PyTorch raised `RuntimeError: Error building extension 'rwkv7_cmix_bf16_v5'`, and the initialization command exited 1.

This is a P0 upstream-materials finding: following the published current path on this Ampere-or-newer campaign GPU produces no initial model and cannot reach training. A likely implementation direction is to use two scalar float atomics for sm_89 and retain the vector operation only where supported, but this campaign did not patch the model code or spend another run testing an invented fix.

## Attempts and cost

Three earlier August jobs each ended before training, cost $0.00 according to their job records, and published no lineage. They are retained in the structured attempt table for accounting but do not support any claim about the current recipe.

For the current recipe, one launch never acquired a worker and was cancelled at $0.00. The executed capture ran for 4m57s from job start to terminal failure and reports an API cost of $0.13. It downloaded and validated MiniPile, then stopped at CUDA compilation. No training step, model publication, or lineage publication occurred.

## Logging and reproducibility status

The run log positively showed the WandB-to-hosted-logging bridge active with its destination, but upstream calls `wandb.init()` only at the first training batch. Compilation failed earlier, so no metric-bearing hosted run exists and `experimentUrl` is intentionally null.

There is also no DAG hash to pass to the Tier-1 row gate. Workflow preflight passed before launch, but the four Tier-1 record gates require a published DAG and are therefore not applicable. This row is neither a Reproducible record nor a Certified reproduction. Its result is the precise blocker: the published CUDA source is incompatible with sm_89 before training begins.
