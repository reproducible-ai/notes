# Cost record

| Attempt | Outcome | Wall clock | Cost |
|---|---:|---:|---:|
| 1 | stopped before training | 2m09s | $0.23 |
| 2 | stopped before training | 1m44s | $0.23 |
| 3 | trained and checkpointed; artifact path superseded | 19m31s | $1.29 |
| 4 | recorded rebuild, six stages complete | 29m12s | $1.85 |
| **Total capture spend** |  |  | **$3.60** |

The row's `rebuild.costUsd` is the successful recorded rebuild, not the total effort. Its fixed/scaling split is necessarily approximate: $1.83 is assigned to boot, environment, data preparation, first-step compilation, checkpointing, packaging, publication, and teardown; $0.02 is the measured-order cost of the forward/backward and optimizer work that scales with additional steady-state steps. This split is not used to claim a full-run estimate.
