# 006 — WGAN-GP on MNIST (`eriklindernoren/PyTorch-GAN`)

> ## ⚠️ These notes were RECONSTRUCTED, not written as the work happened.
>
> The operator's working directory for this row was cleaned up **before the campaign
> adopted the rule that notes must be pushed to a per-row branch**. No `row.json`,
> no README, no `commands.md` and no issues list survived in this repository. The
> capture and the tier-2 certification themselves were never lost — the
> certification evidence had been copied into the campaign ledger, and the lineage
> record is public and immutable.
>
> Everything below is derived from three surviving sources, and from nothing else:
>
> 1. **the published DAG** `e812e981…` (commands, git commit, runtime, per-step
>    inputs/outputs, recorded pins, exit codes);
> 2. **the campaign ledger's copy of the tier-2 certification result**
>    (see `CERTIFICATION.md`); and
> 3. **`implementations/wgan_gp/REPRODUCTION.md`, committed in the fork at the
>    recorded commit `b4c63045`** — operator-authored, contemporaneous, and
>    genuinely surviving. This row is luckier than 004: because the operator wrote
>    their findings *into the fork* rather than only into a working directory, the
>    upstream observations below are the operator's own words, not a reconstruction.
>
> **No operator narrative has been invented.** There is no account of what was tried
> in what order, or of what proved difficult, because that account no longer exists.
> This row therefore carries **no difficulty rating** — the published scale is an
> operator judgement, and no operator judgement survives.

**Verdict: reproduced** (truncated). Playbook v1.0. Tier 1 green, tier 2 certified.

WGAN-GP (Gulrajani et al., 2017) as implemented in `PyTorch-GAN`'s
`implementations/wgan_gp` — an MLP generator and critic on 28×28 MNIST — trained for
**3 epochs of an upstream default 200**, with the checkpoint published under a
complete, publicly resolvable lineage record (AI-BOM 100/100), and a metric actually
computed on the held-out test split. This is a *reproduce* result, not a *replicate*
one: the claim is that the pipeline rebuilds from the record on a cold host and
produces a number, not that the number is good or that the samples are.

- Upstream: <https://github.com/eriklindernoren/PyTorch-GAN> @ `36d3c77e`, MIT © 2018 Erik Linder-Norén
- Fork: <https://github.com/reproducible-ai/PyTorch-GAN> @ `b4c63045`
- Operator's reproduction record (in-fork): [`implementations/wgan_gp/REPRODUCTION.md`](https://github.com/reproducible-ai/PyTorch-GAN/blob/b4c63045aead8024952f36cf7b664d8dcf1ee0c5/implementations/wgan_gp/REPRODUCTION.md)
- DAG: <https://glaas.ai/dag/e812e9815b0934fa19a21be4f57c33349a462b5dee108b0fc9692f57b8f04f3a>
- AI-BOM: <https://glaas.ai/dag/e812e9815b0934fa19a21be4f57c33349a462b5dee108b0fc9692f57b8f04f3a/audit>
- Model: <https://huggingface.co/reproducible-ai/pytorch-gan-wgangp>
- Training request: <https://app.treqs.ai/reproducible-ai/pytorch-gan-wgangp/training/137157c3-6979-4a69-b87b-7e2744f8fe25>

> **The Hugging Face repo is `reproducible-ai/pytorch-gan-wgangp`, not
> `reproducible-ai/wgan-gp`.** The short name has caught people out; the DAG's own
> `roar put` step names the long one, and that is the one the record certifies
> against.

## The headline finding: upstream saves no model

`implementations/wgan_gp/wgan_gp.py` as published trains for up to 200 epochs and
then **throws the result away**. The generator and critic exist only in the
process's memory and are discarded at exit; the directory's sole durable output is
a set of PNG sample grids. There is nothing to publish, nothing to evaluate, and
nothing to re-use.

That single gap is what most of this row's 489-line diff exists to close, and it is
a reproducibility finding rather than a bug in the model: the code is *correct*, it
is simply not *reproducible* in the sense the campaign measures, because it emits no
artifact whose lineage could be recorded.

Seven further upstream observations — including a `BatchNorm1d` call that passes
`0.8` as `eps` rather than `momentum`, two dead command-line flags, and a
repository-level `.gitignore` rule that silently swallows any metrics file written
at a default path — are recorded in `issues.md`, quoted from the operator's own
in-fork `REPRODUCTION.md`. **None of them were "fixed."** This is a reproduction, not
an improvement.

## What was run

Three traced steps on a single `NVIDIA L40S` host, then a publish — a longer chain
than most rows in this campaign, and deliberately so: data preparation, training and
evaluation are separate steps so the lineage graph says that training *consumed* the
dataset rather than *produced* it.

1. **prepare** — download MNIST as its own step (8 recorded artifacts). 126.13 s.
2. **train** — 3 epochs, seed 42, writing `out/wgangp.pt` (8,197,921 B) and 8 sample
   grids. 66.20 s, GPU peak 582 MB.
3. **evaluate** — load the checkpoint, score MNIST's **test** split, write
   `metrics/metrics.json` (633 B). 6.60 s.
4. **publish** — `roar put out/wgangp.pt hf://reproducible-ai/pytorch-gan-wgangp`.

Exact commands, recorded runtime and the full 45-pin freeze are in `commands.md`;
the cold-rebuild evidence is in `CERTIFICATION.md`; the burn is in `costs.md`.

## Tier 1 — re-verified today

Re-run against the live record while writing these notes, to confirm nothing had
drifted since certification:

```
Tier-1 bar — e812e9815b0934fa · reproducible-ai/pytorch-gan-wgangp
  [✅] clean-dag    Clean-DAG check — 13/13 passed  ·  e812e9815b0934fa · 4 jobs (published DAG)
  [✅] ai-bom       AI-BOM score: 100/100  ·  profile: Advanced  ·  glaas.ai/dag/e812e9815b0934fa19a21be4f57c33349a462b5dee108b0fc9692f57b8f04f3a/audit
  [✅] public-urls  RESULT: ALL PUBLIC
  [✅] freeze       RESULT: PORTABLE

RESULT: REPRODUCIBLE RECORD — tier 1 complete (NOT yet a Certified reproduction; tier 2 is a cold rebuild)
```

## Caveats recorded honestly

- **`metrics.json` self-tags `truncated_run: true`.** That is the evaluation script
  correctly labelling a 3-epoch checkpoint as what it is. It is **expected, not a
  defect**, and a reader encountering it should not read it as a failed run.
- **The freeze may be incomplete, and that is a property of the capture build, not
  of the row.** The record carries 45 pins. Our imports-vs-freeze audit finds **no
  decisive miss** — everything `import torch` and `import torchvision` demonstrably
  load is present — but three packages that *often* appear on a torch install are
  absent: `requests`, `urllib3`, `charset-normalizer`. This row's workload may
  genuinely never import them: there is no networking in the training loop, and
  torchvision's MNIST download uses the standard library's `urllib`, not `requests`.
  So the evidence is **weak, and it is not a proven defect** — but it is also not a
  clean bill of health. **"No detected miss" is never "verified complete":** the
  audit only finds gaps it already knows to look for. The capture predates a fix to
  how roar enumerates installed packages, so any record taken on that build may be
  missing something; the mechanism behind that fix is still under investigation and
  is not asserted here.
- **The cold rebuild is what actually retires most of this risk**, and it passed:
  all 45 recorded pins installed at their exact recorded versions on a host that had
  never seen the row, and all three steps ran to exit 0 with no `ModuleNotFoundError`.
  That demonstrates the recorded set is *sufficient* for this row's import graph,
  which is a stronger statement than the static audit can make.
- **`metrics.json` was 633 B in the capture and is reported as 632 B in the
  certification evidence.** One byte. It is not reconciled here, because the
  certification host is long gone and the file's rebuilt content was not preserved —
  the metrics are floating-point values whose decimal representation can differ in
  length between runs, which would produce exactly this, but that is an explanation
  offered, not a verification performed. See `CERTIFICATION.md`.
- **Sample grids are recorded but were not compared.** The capture recorded eight
  PNGs under `samples/`; the certification stat'd only `wgangp.pt` and
  `metrics.json`. The eight PNGs are lineage edges in the record and were not part
  of the rebuild evidence.
- **`amiId` in `row.json` is asserted, not derived.** The published lineage record
  does not expose the machine image, so that field is taken from the campaign's own
  compute-target configuration and cannot be checked by a reader against the DAG.
  Everything else in `row.json` is derived from the record.

## Recorded hardware, in full

`row.json` carries `hw` as an atomic value (`1× NVIDIA L40S (g6e.xlarge)`) so it renders in an
index table. The complete runtime as recorded in the DAG:

- **1× NVIDIA L40S**, 4 vCPU AMD EPYC 7R13, **CUDA 13.0**
- The instance *type* is not in the record — only the accelerator and CPU are. `g6e.xlarge` is
  inferred from that pairing, and is stated here as an inference rather than a finding.

Peak GPU memory was **582 MB of 46,068 MB** — this row used **1.3%** of the card it was given.
A T4 would have run it identically for roughly a third of the price. The truncated run cost
$0.10, so the absolute waste was trivial; at the untruncated 200 epochs (estimated ~75m33s,
**~$2.34** on the L40S) the same choice would cost meaningfully more than it needs to.
