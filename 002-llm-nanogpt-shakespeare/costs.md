# Costs — nanoGPT `shakespeare_char`

All figures are GPU/compute only. Compute target: `g6e.xlarge`
(1× NVIDIA L40S, 46 GB), `us-east-2`, AMI `ami-0f07f1a0b382b48f7`.
On-demand list price ≈ **$1.86/hr**.

## Attempts

| # | What it did | Outcome | Metered | Notes |
|---|---|---|---:|---|
| 0 | Bare-clone check (CPU, this box) | ✅ passed | $0.00 | prepare + a 2-iter CPU train in an empty venv |
| 0b | Logging-path preflight (CPU, this box) | ✅ informative | $0.00 | settled the experiment-logging question before any GPU spend (issue 6) |
| 1 | Full pipeline | ❌ setup | $0.00 | tooling install step could not run on this image |
| 2 | Full pipeline | ❌ publish | $0.09 | prepare + train + label all succeeded; upload step aborted |
| 3 | Full pipeline | ✅ **completed** | $0.06 | 2 m 53 s execution end-to-end |
| | **Total metered** | | **$0.15** | |

Neither failure was caused by the upstream repository — both were in the
harness that installs the capture tooling onto the machine image. Attempt 2
is the expensive kind of failure: it paid for the whole training run and then
fell over on the last step, which is why attempt 3 asserts that step's
prerequisite up front in setup instead of discovering it at the end.

## All-in instance cost

Metered job time understates the real burn, because an on-demand target stays
warm between jobs and has a 15-minute idle timeout. The instance was up from
16:40 to roughly 17:25 UTC — about **45 minutes**, ≈ **$1.40** of instance
time — spanning all three attempts plus idle. Call the honest all-in figure for
this row **under $1.50**, against a $10 not-to-exceed budget.

## What a clean rebuild costs

This is the number that matters to anyone reading the published row: what does it
cost to rebuild this model *once*, knowing what we now know?

| Host | Train wall-clock | ≈ cost |
|---|---|---|
| 1× L40S (`g6e.xlarge`) | 2 m 30 s | **$0.15** |
| 1× T4 (`g4dn.xlarge`) | ~68 min (quoted) | ~$0.60 |
| 1× A100 | ~3 min (upstream README) | ~$0.15 |
| CPU only | hours — not recommended at full scale | — |

Stage breakdown on the L40S:

| Stage | Wall-clock |
|---|---|
| prepare (download + tokenize) | 3 s |
| train (5000 iters) | 2 m 30 s |
| label + publish | 4 s |

Sustained ~17 ms/iter at ~22% MFU. The 5000-iteration recipe is genuinely
small: the corpus is 1.1 MB and the model is 10.65 M parameters. **This is one
of the cheapest complete train-from-scratch recipes in the campaign** — the
whole thing costs less than a bus fare, which is exactly what makes it a good
teaching artifact and a good canary.

## Cost per unit of evidence

Worth stating plainly: the two free CPU checks (attempt 0 and 0b) each caught a
failure that would otherwise have surfaced only after a paid GPU run. The
logging preflight in particular would have produced a *green-looking* training
run with no metrics recorded anywhere — the worst kind of failure, because
nothing errors. Free checks first is not a slogan here; it is the
difference between $0.15 and several times that.
