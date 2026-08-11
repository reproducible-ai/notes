# Costs — nanoGPT `shakespeare_char`

All figures are GPU/compute only. Both the capture and the certification ran on
`g6e.xlarge` (1× NVIDIA L40S, 46 GB), `us-east-2`, AMI `ami-0f07f1a0b382b48f7`.
On-demand list price ≈ **$1.86/hr**. Costs below are **billed instance lifetime**,
not metered job time, because that is what the bill says.

## This record — capture + certification

| | Instance lifetime | ≈ cost |
|---|---|---:|
| Capture (`19171777…`) | 12 m 38 s | **$0.39** |
| Cold-rebuild certification | 14 m 00 s | **$0.43** |
| CPU pre-flight on the control box (shim replay, bare clone, torch import audit) | — | $0.00 |
| **Total** | 26 m 38 s of GPU | **$0.82** |

First attempt on both halves; no retries, no failed launches. Every host was
terminated explicitly and confirmed `terminated` by `describe-instances` rather
than left to an idle timer — an identical g6e on this campaign once ran 45 idle
minutes (~$1.40) because someone trusted the timer.

## Where the capture's wall-clock went

Recorded per stage during the run, because it cannot be reconstructed afterwards:

| Stage | Wall-clock |
|---|---|
| provisioning + agent acquire | 2 m 55 s |
| setup (fetch + verify tracker wheel, purge, isolated install, assertions) | 1 m 18 s |
| **prepare** (download + tokenize) | **11.7 s** |
| **train** (5000 iters, 21 evals) | **5 m 33 s** |
| label | 1 s |
| publish (129 MB → Hugging Face) | 4 s |
| lineage export + publish | 2 s |

Sustained ~16.9 ms/iter at ~22 % MFU. The traced compute — the part that is
actually the model — is **5 m 45 s**; everything else is boot, tooling and upload.

## What a clean rebuild costs

This is the number that matters to a reader: what does it cost to rebuild this
model *once*, knowing what we now know? The certification measured it directly.

| Host | Rebuild wall-clock | ≈ cost |
|---|---|---:|
| 1× L40S (`g6e.xlarge`) — **measured** | 3 m 21 s of `roar reproduce` inside a 14 min host | **$0.43** all-in |
| 1× T4 (`g4dn.xlarge`) | ~68 min train (quoted) | ~$0.60 |
| 1× A100 | ~3 min (upstream README) | ~$0.15 |
| CPU only | ~16.8 s/iter measured → ~23 h at full scale — not recommended | — |

The `roar reproduce` figure covers clone, provisioning an 87-package virtualenv,
`prepare`, and the **full 5000-iteration** train. It is *faster* than the
capture's own 5 m 45 s for a mundane reason: the capture had a working Hugging
Face token and streamed metrics to the dashboard during training, while the
certification host has no credentials and fails over to local buffering
immediately. Same card, same speed, less waiting on the network.

**This row is not truncated.** The 5000-iteration recipe is genuinely small — a
1.1 MB corpus and a 10.65 M-parameter model — so the headline cost *is* the
full-run cost. There is no fixed/variable split to compute and no extrapolation
to defend. **This is one of the cheapest complete train-from-scratch recipes in
the campaign**: the whole thing costs less than a bus fare, which is exactly what
makes it a good teaching artifact and a good canary.

## Historical: what the superseded record cost

The record this one replaces (`72ad9675…`) took seven job launches to land, at
**$0.46** metered and ≈ $2.75 of instance time. None of those failures were
caused by nanoGPT — three died in the harness that installs capture tooling, two
were bookkeeping, and one was a green run that was deliberately discarded. Its
own `costs.md` is preserved in this file's git history.

Two of those seven are worth carrying forward, because this re-capture was shaped
by them:

* **Assert early, fail free.** One attempt paid for the entire training run and
  then fell over on the upload step, because a prerequisite of that step was only
  discovered at the end. This capture's setup stage asserts every prerequisite —
  tracker version, tracer binaries, `huggingface_hub`, and `trackio`'s presence in
  the *workload* interpreter — before a single GPU cycle is spent. Setup cost
  78 seconds and can only fail for free.
* **A cheap check is only worth what its environment is worth.** That row's
  logging pre-flight ran the right check in an unrepresentative environment and
  returned a confident wrong answer, which cost a capture and a reversal. This
  time the pre-flight replayed nanoGPT's *exact* `wandb.init` / `wandb.log` call
  shape through the real tracker shim, on CPU, and then verified the result by
  downloading the metrics back out of the remote store. Still $0.00. Still done
  before booking a GPU. Just actually representative.

## Cost per unit of evidence

The three $0 CPU checks on the control box are, again, the best value in the row:

| Check | Cost | What it bought |
|---|---:|---|
| Replay nanoGPT's `wandb.init`/`log` shape through the shim, with and without a token | $0.00 | proved the logging path works, and that a credential-free host degrades to local buffering instead of crashing — the exact condition every cold rebuild runs under |
| Bare clone: `prepare.py` on three packages, then the full recorded train command on CPU | $0.00 | proved the recorded command runs from a fresh clone with `PYTHONPATH` unset |
| `import torch; 'tqdm' in sys.modules` | $0.00 | one line; established that the superseded record's two missing packages are genuinely loaded, which is the entire reason this row was re-captured |

The last one is the cheapest useful measurement in this row's history. It costs a
single command and it is the difference between "the freeze looks plausible" and
"the freeze is wrong".
