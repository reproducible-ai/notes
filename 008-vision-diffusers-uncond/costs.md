# 008 — costs

Budget for this row: NTE $10. **Actual paid spend: $0.06.**

## Attempts

| # | What | Where | Wall-clock | Cost | Outcome |
|---|---|---|---|---|---|
| 0 | Bare-clone dependency check (fresh clone, scratch venv, `PYTHONPATH` cleared) | local CPU | ~3 min | $0.00 | Caught findings §1 and §2 before any spend |
| 1 | CPU rehearsal, `--resolution=32`, full epoch, end-to-end incl. artifact write and metrics sync | local CPU | 29 min | $0.00 | Exit 0. Confirmed the recipe before buying GPU time |
| 2 | **Paid GPU run**, `--resolution=64`, full recorded workflow | `g4dn.xlarge` (Tesla T4), us-east-2 | 10 min 05 s | **$0.06** | Exit 0, first attempt |

Total: **$0.06**, one paid attempt, no failed paid attempts.

## Attempt 2 breakdown

Job `39fd547c-019c-4e4c-a7be-f78c76ce93e9`, queued 19:32:20Z, completed 19:42:25Z.

| Phase | Duration |
|---|---|
| Provision + agent acquisition | 2 min 15 s |
| Repo prepare + environment | 6 s |
| Setup (dependency install, pre-flight) | ~3 min 40 s |
| **Training** — 460 steps @ ~2.4 it/s | 3 min 12 s |
| End-of-epoch sampling (10 denoising steps, batch 4) + save | ~15 s |
| Publish (455 MB upload @ 34 MB/s) | ~15 s |
| Lineage export/publish | ~1 s |

Training is a *third* of the bill. Provisioning and dependency installation
together cost more than the model did — which is the usual shape for a truncated
row, and the reason the CPU rehearsal was worth doing: an attempt that dies in
setup costs almost as much as one that succeeds.

## Notes on cost control

- The 29-minute CPU rehearsal was free and de-risked the entire paid run. Two of
  the three real obstacles (§1, §2 in `issues.md`) were found at zero cost.
- `--ddpm_num_inference_steps=10` instead of the default 1000 removes ~1000
  UNet forward passes at epoch end for a few seconds of saving each. Cheap win.
- The dominant *avoidable* cost on this row is dependency installation, which
  runs on every attempt. A warmed image with `accelerate`/`datasets`/`wandb`
  present would cut attempt cost by roughly a third.
