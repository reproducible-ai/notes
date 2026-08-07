# Costs — nanoGPT `shakespeare_char`

All figures are GPU/compute only. Compute target: `g6e.xlarge`
(1× NVIDIA L40S, 46 GB), `us-east-2`, AMI `ami-0f07f1a0b382b48f7`.
On-demand list price ≈ **$1.86/hr**.

## Attempts

| # | What it did | Outcome | Metered | Notes |
|---|---|---|---:|---|
| 0 | Bare-clone check (CPU, this box) | ✅ passed | $0.00 | prepare + a 2-iter CPU train in an empty venv |
| 0b | Logging-path preflight (CPU, this box) | ⚠ misleading | $0.00 | ran in an unrepresentative env; right answer, wrong reasoning (issue 6) |
| 1 | Full pipeline | ❌ setup | $0.00 | tooling install step could not run on this image |
| 2 | Full pipeline | ❌ publish | $0.09 | prepare + train + label all succeeded; upload step aborted |
| 3 | Full pipeline | ✅ completed | $0.06 | 2 m 53 s execution end-to-end |
| 3b | Logging re-verification (CPU) | ✅ informative | $0.00 | showed 0b's reasoning was wrong (issue 6) |
| 4 | Full pipeline, logging on | ⚠ green but **rejected** | $0.06 | 2 m 54 s; metrics identical to attempt 3 |
| 4b | Rebuild check of attempt 4 (CPU) | ✅ decisive | $0.00 | its recorded command needs a package its record lacks |
| 5 | Full pipeline (bookkeeping re-run) | ❌ setup | $0.00 | integrity guard on a tooling download fired; not upstream |
| 6 | Full pipeline (bookkeeping re-run) | ✅ completed | $0.19 | included instance boot |
| 7 | Full pipeline | ✅ **published row** | $0.06 | 2 m 51 s; the record's final, coherent state |
| | **Total metered** | | **$0.46** | |

No failure was caused by the upstream repository. Attempts 1, 2 and 5 died in
the harness that installs capture tooling onto the machine image. Attempt 2 is
the expensive kind: it paid for the whole training run and then fell over on the
last step, which is why attempt 3 asserts that step's prerequisite up front in
setup instead of discovering it at the end. Attempt 5 is the cheap kind: an
integrity check on a tooling download failed and the job stopped before the GPU
did any work, for $0.00. That asymmetry — assert early, fail free — is the single
most useful habit this row reinforced.

Attempts 6 and 7 were pure bookkeeping: making the published artifact, the
recorded commit and the repository HEAD all refer to the same run, after
attempt 4 had been backed out. No training question was open by then.

Attempt 4 is the interesting one, and it is a **discarded** result. It enabled
the repo's own metric logging, completed, and passed every completeness check we
have. A from-scratch rebuild check (4b) then showed its recorded command imports
a package its recorded environment does not contain, so the row stayed on
attempt 3. See issue 6.

That $0.06 was not wasted. Attempt 4 is a full independent repetition of attempt
3, and it returned **bit-identical** train and validation losses at all 21 eval
points — which is what lets this row claim replication rather than mere
reproduction. A rejected attempt that produces a second independent measurement
is a decent outcome for six cents.

## All-in instance cost

Metered job time understates the real burn, because an on-demand target stays
warm between jobs and has a 15-minute idle timeout. The instance was up from
16:40 to roughly 18:08 UTC — about **88 minutes**, ≈ **$2.75** of instance
time — spanning all seven attempts plus idle. Call the honest all-in figure for
this row **under $3**, against a $10 not-to-exceed budget. Roughly two thirds of
that was spent on tooling and bookkeeping rather than on training; the training
itself accounts for about eight minutes of GPU time across four full runs.

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

Worth stating plainly, in both directions.

The bare-clone check (attempt 0) is the cheapest insurance available: it
established the real dependency closure and proved the recipe ran end-to-end,
for free, before a cent of GPU time. Nothing it would have caught went on to
bite us, which is the point — that is what a passing check looks like.

The logging preflight is the honest counter-example. Attempt 0b ran the right
check in the wrong environment and returned a confident false negative, which
directly caused a captured run to be made with logging off and then re-run
(attempt 4) once 3b corrected it. A free check is only worth what its
environment is worth. Cheap checks first, yes — but a cheap check that does not
resemble the real thing can cost more than no check at all, because you act on
it.
