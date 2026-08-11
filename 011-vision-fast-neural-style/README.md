# 011 — fast_neural_style (`pytorch/examples`)

**Status: BLOCKED at capture. The pipeline runs; the record does not carry it.**
Nine job launches across two operators trained this model correctly six times and
published its outputs, and none of them produced a lineage record that both carries the
run's steps and satisfies this project's publish-precondition check. The causes are in
the recording layer rather than in `pytorch/examples`, and under this project's boundary
rules the diagnosis lives in the operator's private notes. `issues.md` and `commands.md`
are complete and are the substance of the row — the upstream findings stand on their own
and do not depend on the capture landing. What follows describes the model and the
recipe as they actually ran.

Fast neural style transfer — Johnson et al., *Perceptual Losses for Real-Time Style
Transfer and Super-Resolution*, with instance normalisation. A small convolutional
`TransformerNet` is trained to apply one fixed artistic style to any image in a single
forward pass, supervised by a frozen VGG-16 that supplies both a content loss (feature
distance on `relu2_2`) and a style loss (Gram-matrix distance across four layers).

| | |
|---|---|
| Upstream | [`pytorch/examples`](https://github.com/pytorch/examples) · subdirectory `fast_neural_style` |
| Fork | [`reproducible-ai/examples`](https://github.com/reproducible-ai/examples) |
| License | BSD-3-Clause (verified via the GitHub API) |
| Recipe | `TransformerNet` in the *mosaic* style, Imagenette-320 (9,469 images), 1 of upstream's default 2 epochs, batch 4, 256 px |
| Hardware | 1× Tesla T4 (g4dn.xlarge), us-east-2 |
| Upstream lines changed | **0** |
| Record | none publishable — see *Why this row is held* |
| Experiment link | none — upstream ships no logging integration (see below) |

## What the pipeline does

Three traced steps. The figures below are from the run at fork commit
`3a7a01cc2d1b0d91f2c9795152fdbcbf5c944b83`, whose record
([`63edfd1d…e377`](https://glaas.ai/dag/63edfd1d69128bf4032d089ace64aa301c1a44e0b60d48abfe83b619d4e6e377))
carries all three steps and scores 97.5/100 on the AI-BOM:

| step | command | recorded duration | inputs → outputs |
|---|---|---|---|
| 1 `fetch_dataset` | `repro/fetch_dataset.py` (stdlib only) | 20.8 s | 1 → 13,396 |
| 2 `train` | upstream `neural_style.py train` | 523.3 s | 9,470 → 2 |
| 3 `stylize` | upstream `neural_style.py eval` | 6.1 s | 2 → 1 |

Every command is upstream's own entry point with upstream's own flags. Nothing under
`neural_style/` was edited; the only files this row adds live in `fast_neural_style/repro/`
and none of them is imported by the model code.

Environment as recorded: Python 3.12.10, `torch 2.7.0` (`2.7.0+cu126` at runtime,
plain-PyPI distribution version `2.7.0`), `torchvision 0.22.0`, `numpy 2.4.4`,
`pillow 12.2.0`. The `train` and `stylize` steps each record 24 pins; `fetch_dataset`
records 9, which is correct — it imports nothing outside the standard library
(`argparse`, `hashlib`, `os`, `sys`, `tarfile`, `time`, `urllib.request`), so the nine
are the tracer's own closure and nothing of the workload's is missing.

## Why this row was chosen, and what it actually measured

It was picked as the cleanest candidate available: `requirements.txt` is three lines,
persistence is two `torch.save` calls, there is no OS-package dependency, and there is
no copy or link anywhere in the subdirectory. The brief that selected it said it should
be the smoothest row of its batch — and that if it was not, that would itself be the
finding.

**The model side was as easy as advertised.** Everything in `issues.md` that is
*upstream's* is real but mild: a timestamped output filename, an undeclared Pillow
dependency, two documented flags broken since Pillow 10, no shuffle, no logging, no
evaluation metric, and a 13 GB manual dataset download. None of it blocked the row.
Most of it is invisible if you run the example by hand once, and unavoidable the moment
you try to script it.

**Turning it into a record took nine launches across two operators, and never
succeeded.** Six of them trained the model correctly. The causes were not in `pytorch/examples`, and under this
project's boundary rules they are recorded in the operator's private notes rather than
here. Read the row as evidence about a specific claim: *"the code is simple"* and
*"the result is reproducible"* are close to independent properties. This is about as
simple as a real training example gets — 260 lines, three dependencies — and the
recording still dominated the effort by an order of magnitude.

## The recipe, and the two ways it is truncated

Upstream's README trains on COCO 2014 train (82,783 images, 13 GB) for a default of 2
epochs. This row runs **1 epoch over Imagenette-320 (9,469 images)** and says so
everywhere it is recorded, including in the published artifact's own labels.

Substituting the dataset is a scale decision, not a semantic one: the objective is a
perceptual loss against frozen VGG-16 features plus a Gram-matrix style term, and
nothing in it depends on COCO's annotations, its object categories, or its particular
photographs — only on a large, varied corpus of natural images. Imagenette is natural
photography of the same character, is a single public tarball needing no credentials,
and downloads in six seconds instead of tens of minutes. The tarball's sha256
(`569b4497c98db6dd29f335d1f109cf315fe127053cedf69010d047f0188e158c`) was identical when
fetched independently on a different machine, so the dataset has a stable identity.

The model is **not converged and is not offered as a quality result.** What the row
demonstrates is that the pipeline runs end to end from a recorded description, and that
the loss it computes behaves: over the recorded epoch the running-mean total loss fell
from 10,715,696 at the first log line (800 images) to 3,024,145 at the last (8,800
images), driven almost entirely by the style term (9,574,525 → 1,606,947) while the
content term rose slightly (1,141,171 → 1,417,198). That is the expected shape for this
objective early in training: the transformer buys style at the cost of fidelity.

Note that upstream prints only every `--log-interval` batches, and 2,368 batches is not
a multiple of 200, so **there is no end-of-epoch loss line** — the last printed value is
at 8,800 of 9,469 images.

## Why this row is held

Two halves of a publishable record exist, in two different sessions, and no run produced
both at once.

| session | steps | publish edges (artifact → job, download URL, HF destination) | attribution | AI-BOM | verdict |
|---|---|---|---|---|---|
| [`63edfd1d…e377`](https://glaas.ai/dag/63edfd1d69128bf4032d089ace64aa301c1a44e0b60d48abfe83b619d4e6e377) | **3, all present** | absent — that run's upload stage never executed | **attributed, with backlink** | **97.5/100** | blocked: no artifact destination recorded |
| [`b07bda68…3922`](https://glaas.ai/dag/b07bda688e5035021848c5c8be92b282826af75e83923b73b3654dfdd3553922) | **4, all present** | **all three present** | anonymous, no backlink | 82.8/100 | blocked: publishing it would make an unattributed claim |

Of the nine launches, four produced nothing at all — three had their host terminated
mid-job by the platform and one was cancelled after sitting in a phantom queue slot. The
five that completed produced **four sessions that were correctly attributed, carried the
right repository and commit, and contained zero steps**, plus the two rows above (the
second of which is the anonymous twin of the last of those four).

The published artifacts are real and current. The Hugging Face repo carries the outputs
of the last run (fork commit `32ab2fe40f06201748c77789583b14e754155011`):

| file | bytes | sha256 |
|---|---|---|
| `ckpt_epoch_0_batch_id_2368.pth` | 6,739,701 | `eeda5cc246e88cfbbbbe38cd332e881c23abccdc2e6a24f4aa803b6616a8ebce` |
| `amber-mosaic.jpg` | 372,946 | `c00d9376649a1668e8ed42536275362f0180bebb1d53959ee47d336f0429956d` |

They are the outputs of the `b07bda68…` session above, and its DAG records both hashes.
They are **not** the outputs of the run behind `63edfd1d…`, whose checkpoint was
`396ffd21703471596e0efacad5bf2b0f5723138a1d8a1abbfaedc144b162195d` and whose stylised
image was `0c4a9d1bf040111e5bdd9fb1d1734eda7af7c4f9fbdd7861a2b3636252cfa05e`. Those bytes
were never uploaded anywhere, and the two sets differ for the reason in the next
section.

## Results are not bit-identical between runs, and that is expected

Six executions of this recipe produced six different checkpoint hashes despite
`--seed 42`. Upstream seeds `numpy` and `torch` (`neural_style.py:39-40`) but does not
set deterministic cuDNN algorithms, so GPU reduction order varies. The first-log-line
total loss differed by ~0.04% across runs (10,715,696 / 10,718,970 / 10,700,287).

A related detail worth recording because it looks like a defect and is not: the
checkpoint and the timestamped final model hold the **same weights** and have
**different bytes** (6,739,701 vs 6,741,397). `torch.save` embeds the output file's
stem in its zip container, so two saves of one `state_dict` to two paths are never
byte-identical. Verified directly on a CPU-only 8-image run before any GPU time was
spent.

## No experiment link, and why that is a finding rather than an omission

`experimentUrl` is `null`. `fast_neural_style/` was grepped for `wandb`, `mlflow`,
`trackio`, `tensorboard`, `SummaryWriter`, `comet`, `neptune` and `report_to`: **zero
hits.** Upstream ships no experiment-logging integration of any kind, so there is no
flag to switch on.

The metrics bridge this campaign uses only intercepts a `wandb` import that the workload
actually performs; against a workload that never imports `wandb` it is a guaranteed
no-op. It was therefore **removed** from the generated workflow rather than left in
place — leaving it would have put a mechanism in the record that the record never uses,
implying a logging path that does not exist.

Adding `wandb.init()` to `neural_style.py` would have produced a link. It would also
have made this row a demonstration of our patch rather than a reproduction of upstream's
work, and forfeited the zero-upstream-lines property that is the only reason the row is
evidence of anything. A null with a stated reason is the honest answer.

There is also nothing to log: this example computes **no held-out metric**. Its only
evaluation is `neural_style.py eval`, which renders an image. That image is published
alongside the model precisely because it is the row's entire qualitative result.

## Bare-clone check

From a fresh clone, in a scratch venv containing only `numpy`, `torch` and
`torchvision` — Pillow arriving transitively, per `issues.md` §2 — with `PYTHONPATH`
unset, all three recorded commands ran to completion with no `ModuleNotFoundError`.
This is the check that costs cents and saves a GPU rebuild; it is also where the
`Image.ANTIALIAS` breakage, the `python -m` failure and the timestamped-filename
problem were all found, before a single cent of GPU time was spent.

## Files

- `issues.md` — every obstacle, with root cause and what was done. The substance.
- `commands.md` — the exact recipe, and the bare-clone check that preceded it.
- `costs.md` — per-step timings, the fixed/variable split, and the full-run estimate.
- `row.json` — the object published to the `/models` table.
- `capture-*.log` — the raw run logs, including the ones that failed.

## Certification

**Not certified.** No cold rebuild has been attempted on this row by anyone. This
operator performed the capture only; certification is deliberately done by a different
agent, so that what is measured is whether a *stranger* can rebuild from the published
materials rather than whether the author can. `row.json` therefore carries
`{"tier": 1, "result": null}`, and will keep carrying it until a cold rebuild produces
an actual finding.
