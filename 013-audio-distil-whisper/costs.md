# Costs

| Attempt | Outcome | Wall clock | Cost |
|---|---|---:|---:|
| Capture 1 | Cancelled during environment validation | 2m24s | $0.05 |
| Capture 2 | Completed and published attributed lineage | 4m18s | $0.06 |
| **Total campaign spend** |  |  | **$0.11** |

The row's `rebuild.costUsd` is $0.06, the cost of the completed rebuild. Its approximate fixed/scaling split is $0.05/$0.01: environment construction, downloads, student initialization, evaluation, and publication dominate this one-step run; only the short training segment scales with optimizer steps.

No defensible full-run estimate is given. The one-step fixture changes model size, dataset size, batching, and training length simultaneously, while upstream recommends at least 50,000 steps for convergence.
