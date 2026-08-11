# 011 — fast_neural_style (`pytorch/examples`)

**Status: BLOCKED at capture. No attributed lineage was ever published, so this row
has no DAG hash and cannot be certified as it stands.**

The training pipeline is not the problem — it ran correctly on every attempt that was
allowed to finish, and the trained model is
[published and public](https://huggingface.co/reproducible-ai/fast-neural-style).
Three capture attempts on one compute target failed to produce a usable record:

| attempt | outcome |
|---|---|
| 1 | Pipeline succeeded end to end. The attributed lineage published with **zero jobs** while its anonymous twin carried them. Also recorded the repository as the literal string `origin` rather than a URL — not clonable, so not rebuildable. |
| 2 | Host terminated **one second before** the third step began, mid-run. Training lost. |
| 3 | Pipeline succeeded end to end with the repository URL now recorded correctly. Host terminated **34 seconds into a lineage export that takes 51**, leaving the publication permanently `pending` and the package never uploaded. |

Attempt 1's defect and attempt 3's are independent, and neither is in
`pytorch/examples`. Per this project's boundary rules the detail lives in the
operator's private friction record rather than here; what belongs in the public notes
is the outcome, which is that **the row is held with no hash.**

`issues.md` and `commands.md` are complete and are the substance of this row — the
upstream findings stand on their own and do not depend on the capture landing.

Fast neural style transfer — Johnson et al., *Perceptual Losses for Real-Time Style
Transfer and Super-Resolution*, with instance normalisation. A small
convolutional `TransformerNet` is trained to apply one fixed artistic style to any
image in a single forward pass, supervised by a frozen VGG-16 that supplies both a
content loss (feature distance on `relu2_2`) and a style loss (Gram-matrix distance
across four layers).

| | |
|---|---|
| Upstream | [`pytorch/examples`](https://github.com/pytorch/examples) · subdirectory `fast_neural_style` |
| Fork | [`reproducible-ai/examples`](https://github.com/reproducible-ai/examples) |
| License | BSD-3-Clause (verified via the GitHub API) |
| Recipe | `TransformerNet` in the *mosaic* style, Imagenette-320 (9,469 images), 1 of upstream's default 2 epochs, batch 4, 256px |
| Hardware | 1× Tesla T4 (g4dn.xlarge) |
| Upstream lines changed | **0** |
| Experiment link | none — upstream ships no logging integration (see below) |

## Why this row was chosen, and what it actually measured

It was picked as the cleanest candidate available: `requirements.txt` is three lines,
persistence is two `torch.save` calls, there is no OS-package dependency, and there
is no copy or link anywhere in the subdirectory. The brief that selected it said, in
as many words, that it should be the smoothest row of its batch — and that if it was
not, that would itself be the finding.

**The model side was as easy as advertised. Turning it into a *record* was not.**
That gap is the interesting result here, and it is worth separating carefully,
because the two halves have different causes:

- Everything in `issues.md` that is *upstream's* is real but mild: a timestamped
  output filename, an undeclared Pillow dependency, two documented flags that have
  been broken since Pillow 10, no shuffle, no logging, no evaluation metric, and a
  13 GB manual dataset download. None of it blocked the row. Most of it is invisible
  if you run the example by hand once, and unavoidable the moment you try to script it.
- Everything that *did* block the row came from the reproduction toolchain rather
  than from `pytorch/examples`, and by the rules of this project it is recorded
  privately rather than here.

So read this row as evidence about a specific claim: **"the code is simple" and "the
result is reproducible" are close to independent properties.** This is about as
simple as a real training example gets — 260 lines, three dependencies — and it still
took three capture attempts.

## The recipe, and the two ways it is truncated

Upstream's README trains on COCO 2014 train (82,783 images, 13 GB) for a default of 2
epochs. This row runs **1 epoch over Imagenette-320 (9,469 images)** and says so
everywhere it is recorded, including in the published artifact's own description.

Substituting the dataset is a scale decision, not a semantic one: the objective is a
perceptual loss against frozen VGG-16 features plus a Gram-matrix style term, and
nothing in it depends on COCO's annotations, its object categories, or its particular
photographs — only on a large, varied corpus of natural images. Imagenette is natural
photography of the same character, is a single public tarball needing no credentials,
and downloads in six seconds instead of tens of minutes.

The model is **not converged and is not offered as a quality result.** What the row
demonstrates is that the pipeline runs end to end from a recorded description, and
that the loss it computes behaves: the running-mean total loss fell from 10,700,287
at the first log line to 3,016,956 at the last, driven almost entirely by the style
term (9,552,585 → 1,605,531) while the content term rose slightly, which is the
expected shape for this objective early in training.

## No experiment link, and why that is a finding rather than an omission

`experimentUrl` is `null`. `fast_neural_style/` was grepped for `wandb`, `mlflow`,
`trackio`, `tensorboard`, `SummaryWriter`, `comet`, `neptune` and `report_to`: **zero
hits.** Upstream ships no experiment-logging integration of any kind, so there is no
flag to switch on.

The metrics bridge this campaign uses only intercepts a `wandb` import that the
workload actually performs; against a workload that never imports `wandb` it is a
guaranteed no-op. It was therefore **removed** from the generated workflow rather than
left in place — leaving it would have put a mechanism in the record that the record
never uses, implying a logging path that does not exist.

Adding `wandb.init()` to `neural_style.py` would have produced a link. It would also
have made this row a demonstration of our patch rather than a reproduction of
upstream's work, and forfeited the zero-upstream-lines property that is the only
reason the row is evidence of anything. A null with a stated reason is the honest
answer.

## Results are not bit-identical between runs, and that is expected

Two full captures of this recipe produced checkpoints with different sha256 values
despite `--seed 42`. Upstream seeds `numpy` and `torch` (`neural_style.py:39-40`) but
does not set deterministic cuDNN algorithms, so GPU reduction order varies. The
first-log-line total loss differed by ~0.1% between runs (10,713,272 vs 10,700,287).

This project claims **reproduce, not replicate** — that the recorded description
rebuilds and computes the same quantities, not that it returns the same floats. The
drift is recorded here so nobody reads a hash mismatch as a defect.

## Files

- `issues.md` — every obstacle, with root cause and what was done. The substance.
- `commands.md` — the exact recipe, and the bare-clone check that preceded it.
- `costs.md` — per-step timings, the fixed/variable split, and the full-run estimate.
- `row.json` — the object published to the `/models` table.

## Certification

**Not certified.** No cold rebuild has been attempted on this row by anyone. This
operator performed the capture only; certification is deliberately done by a
different agent, so that what is measured is whether a *stranger* can rebuild from
the published materials rather than whether the author can. `row.json` therefore
carries `{"tier": 1, "result": null}`, and will keep carrying it until a cold rebuild
produces an actual finding.
