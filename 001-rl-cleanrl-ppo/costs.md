# Costs — 001 CleanRL PPO

**Total burn: $0.10** (capture) **+ $0.13** (independent tier-2 certification) **=
$0.23.** Budget was NTE $10; this row used ~2% of it.

| # | Attempt | Target | Wall clock | Cost | Outcome |
|---|---|---|---|---|---|
| 0 | Local probe + bare-clone check | control host (CPU) | ~5 min | $0.00 | Passed. Confirmed the recipe, the dependency set, and that the run completes with no credentials. |
| 1 | `c50907a4` — first capture | `g4dn.xlarge` (Tesla T4) | 5 min 38 s | $0.05 | **Trained correctly** (500k steps, converged, model published) but the job was marked FAILED afterwards by a harness-configuration mistake of mine — not anything in the upstream repo. Lineage left unpublished. |
| 2 | `d2761ff6` — second capture | `g4dn.xlarge` (Tesla T4) | 5 min 15 s | $0.05 | **Clean.** Lineage published, tier-1 gates 4/4. |
| 3 | Independent tier-2 certification, `58df327f…` | `g4dn.xlarge` (Tesla T4), fresh host | ~15 min instance lifetime | $0.13 | **Certified.** Cold `roar reproduce --lineage --run --no-puts -y` exited 0, 1/1 steps, same output sizes and final metric, 69/69 recorded pins present, P0-14 workaround confirmed by direct `/proc` evidence. |

Final rebuild cost — what it costs to reproduce this row once, from scratch:
**$0.05** and about five minutes on a single T4. The training step itself is
**289 seconds**.

## Why it is this cheap

CartPole-v1 is a 4-dimensional observation space and a 2-action discrete space; the
policy and value networks are each two 64-unit `tanh` layers. The 500,000-timestep
default run is small enough that it is essentially free, and it does not need a GPU at
all — GPU peak memory during the run was **166 MB** of the T4's 15,360 MB, and the
recorded throughput (1,782 SPS) is dominated by the CPU-side gymnasium environment
stepping, not by the network.

A CPU-only instance would have been the better choice and would have cost less. The
GPU target was used because it is the campaign's standard image; noted for future
classic-control rows.

There is also **no dataset**: PPO generates its own experience from the simulator, so
there is no download, no storage, and no egress in the cost at all.

## Time, honestly

Wall-clock compute was ~11 minutes across both attempts. Nearly all of the human/agent
time on this row went to reading the upstream materials, running the free bare-clone
check, and diagnosing attempt 1 — not to fighting the model. The training itself never
needed a second look: it converged on the first attempt at stock hyperparameters.
