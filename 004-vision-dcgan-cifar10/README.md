# 004 — DCGAN on CIFAR-10 (`pytorch/examples`)

> ## ⚠️ These notes were RECONSTRUCTED, not written as the work happened.
>
> The operator's working directory for this row was cleaned up **before the campaign
> adopted the rule that notes must be pushed to a per-row branch**. No `row.json`,
> no README, no `commands.md` and no issues list survived. The capture and the
> tier-2 certification themselves were never lost — the certification evidence had
> been copied into the campaign ledger, and the lineage record is public and
> immutable.
>
> Everything below is derived from two surviving sources, and from nothing else:
>
> 1. **the published DAG** `3a8ff4c4…` (commands, git commit, runtime, per-step
>    inputs/outputs, recorded pins, exit codes), and
> 2. **the campaign ledger's copy of the tier-2 certification result**
>    (see `CERTIFICATION.md`).
>
> Where the fork itself carries operator-authored content committed at the recorded
> commit, that is cited as such. **No operator narrative has been reconstructed.**
> There is no account here of what the operator tried, in what order, or what they
> found difficult, because that account no longer exists and inventing it would be
> worse than omitting it. This row therefore carries **no difficulty rating** — the
> published rating scale is an operator judgement, and there is no operator
> judgement on file.

**Verdict: reproduced** (truncated). Playbook v1.0. Tier 1 green, tier 2 certified.

DCGAN (Radford et al., 2015) as shipped in `pytorch/examples/dcgan`, trained on
CIFAR-10 for **one epoch of a default 25**, with the generator checkpoint published
under a complete, publicly resolvable lineage record (AI-BOM 100/100). This is a
*reproduce* result, not a *replicate* one: the claim is that the pipeline rebuilds
from the record on a cold host, not that the samples are good. They are not — one
epoch of DCGAN is not a converged model, and the `roar put` message on the record
says so in the artifact's own publish metadata.

- Upstream: <https://github.com/pytorch/examples> @ `acc295dc`, BSD-3-Clause
- Fork: <https://github.com/reproducible-ai/examples> @ `6012a427`
- DAG: <https://glaas.ai/dag/3a8ff4c4c89b4cf796fa568b773e4d482fe1fde848b8baf1805ce6a47b800ba0>
- AI-BOM: <https://glaas.ai/dag/3a8ff4c4c89b4cf796fa568b773e4d482fe1fde848b8baf1805ce6a47b800ba0/audit>
- Model: <https://huggingface.co/reproducible-ai/dcgan>
- Training request: <https://app.treqs.ai/reproducible-ai/dcgan/training/d672f01e-cabe-485c-9619-c5e1304155e5>

## Zero upstream source lines were changed

This is the strongest single statement the record supports about this row, and it
is fully checkable: the fork is **3 commits and +110/−0 lines ahead** of upstream
`acc295dc`, across six files, **none of which is Python**.

| file | status | +/− |
|---|---|---|
| `.gitignore` | modified | +12 / −0 |
| `.treqs/config.toml` | added | +11 / −0 |
| `.treqs/workflows/dcgan-cifar10.yaml` | added | +44 / −0 |
| `.treqs/workflows/plaintorch-image-audit.yaml` | added | +43 / −0 |
| `cifar10-data/.gitkeep` | added | 0 |
| `out/.gitkeep` | added | 0 |

`dcgan/main.py` is byte-for-byte upstream. The recipe is upstream's own documented
invocation with `--niter` cut from 25 to 1 and `--manualSeed` fixed at 42. The
complete diff is in `patches/fork-vs-upstream.diff`.

The two `.gitkeep` files and the `.gitignore` change exist for one reason, which
is a genuine reproducibility finding rather than a workaround: upstream's
`.gitignore` **directory-ignores** output paths. A directory-ignore means the
directory does not survive a clean checkout, so a cold rebuild has nowhere to write
and the outputs never become lineage edges. The fix is to ignore the *contents*
(`out/*`) while committing a `.gitkeep`, so the directory exists in a fresh clone
and every artifact it receives is captured. See `commands.md`.

## What was run

Two traced steps on a single `Tesla T4` host, then a publish:

1. **prepare** — download CIFAR-10 via `torchvision.datasets.CIFAR10(download=True)`
   (9 recorded artifacts, 170,498,071 B tarball).
2. **train** — `python dcgan/main.py --dataset cifar10 --niter 1 --accel
   --manualSeed 42` — 782 iterations, batch 64, 64×64 images. Recorded GPU peak
   1,480 MB, 101.98 s.
3. **publish** — `roar put out/netG_epoch_0.pth hf://reproducible-ai/dcgan`.

Exact commands, recorded runtime and the full 45-pin freeze are in `commands.md`;
the cold-rebuild evidence is in `CERTIFICATION.md`; the burn is in `costs.md`.

## Tier 1 — re-verified today

Re-run against the live record while writing these notes, to confirm nothing had
drifted since certification:

```
Tier-1 bar — 3a8ff4c4c89b4cf7 · reproducible-ai/dcgan
  [✅] clean-dag    Clean-DAG check — 13/13 passed  ·  3a8ff4c4c89b4cf7 · 3 jobs (published DAG)
  [✅] ai-bom       AI-BOM score: 100/100  ·  profile: Advanced  ·  glaas.ai/dag/3a8ff4c4c89b4cf796fa568b773e4d482fe1fde848b8baf1805ce6a47b800ba0/audit
  [✅] public-urls  RESULT: ALL PUBLIC
  [✅] freeze       RESULT: PORTABLE

RESULT: REPRODUCIBLE RECORD — tier 1 complete (NOT yet a Certified reproduction; tier 2 is a cold rebuild)
```

## Caveats recorded honestly

- **The freeze may be incomplete, and that is a property of the capture build, not
  of the row.** The record carries 45 pins. Our imports-vs-freeze audit finds **no
  decisive miss** — everything `import torch` and `import torchvision` demonstrably
  load is present — but three packages that *often* appear on a torch install are
  absent: `requests`, `urllib3`, `charset-normalizer`. This row's workload may
  genuinely never import them: there is no networking in the training loop, and
  torchvision's CIFAR-10 download uses the standard library's `urllib`, not
  `requests`. So the evidence is **weak, and it is not a proven defect** — but it is
  also not a clean bill of health. **"No detected miss" is never "verified
  complete":** the audit only finds gaps it already knows to look for. The capture
  predates a fix to how roar enumerates installed packages, so any record taken on
  that build may be missing something; the mechanism behind that fix is still under
  investigation and is not asserted here.
- **The cold rebuild is what actually retires most of this risk**, and it passed:
  all 45 recorded pins installed at their exact recorded versions on a host that
  had never seen the row, and both steps ran to exit 0 with no
  `ModuleNotFoundError`. That demonstrates the recorded set is *sufficient* for
  this row's import graph, which is a stronger statement than the static audit can
  make. It still says nothing about packages that never reached the record.
- **The record's own outputs and the certification's stat'd outputs do not agree on
  one file.** `netG_epoch_0.pth` (14,323,315 B) and `real_samples.png` (379,915 B)
  match the capture exactly; `fake_samples_epoch_000.png` was 546,896 B at capture
  and 573,413 B at rebuild. That is expected — it is a PNG of *generated* images, so
  its compressed size tracks pixel content, and GPU training is not bit-deterministic
  — but it means this row demonstrates *reproduce*, not *replicate*, and no
  byte-identity claim is made. Details in `CERTIFICATION.md`.
- **The certification stat'd three of the four recorded training outputs.**
  `netD_epoch_0.pth` (11,076,841 B at capture) is a recorded output of step 2 and
  was not stat'd on the rebuild host. It is not the published artifact.
- **External data is tracked but not content-addressed at the source.** CIFAR-10 is
  fetched from `cs.toronto.edu` inside a traced step, so the downloaded bytes are
  recorded as artifacts with their hashes — but the *remote* is not pinned. If
  upstream ever serves different bytes, a rebuild would train on different data.
  The hashes in this DAG are what would catch that; nothing prevents it.
- **`amiId` in `row.json` is asserted, not derived.** The published lineage record
  does not expose the machine image, so that field is taken from the campaign's own
  compute-target configuration and cannot be checked by a reader against the DAG.
  Everything else in `row.json` is derived from the record.

## Where the wall-clock actually went

The traced run was **26m41s**, and it is worth being precise about the shape of that
number, because it is the difference between a useful cost estimate and a misleading one.

| phase | duration | scales with epochs? |
|---|---|---|
| CIFAR-10 download | **24m57s** | no — fixed |
| training (1 epoch) | **1m42s** | yes |

**94% of this run was a fixed cost.** Anyone scaling the headline 26m41s by 25 to price the
untruncated recipe would land near 11 hours; the real figure is closer to **67 minutes** —
42m30s of training plus the same 24m57s download. That is a factor-of-ten error, and it comes
entirely from treating a fixed cost as a variable one.

This is why `row.json` carries `fixedCostUsd`, `scalingCostUsd` and `fullRunEstimateBasis`
separately rather than a single number: the fixed/variable split differs on every row, and only
someone who watched the run knows which portion scales.

_Caveat, recorded in `costs.md` and repeated here: the instance's total billed lifetime was not
captured — boot and provisioning are outside the traced window. Every figure here is a floor._
