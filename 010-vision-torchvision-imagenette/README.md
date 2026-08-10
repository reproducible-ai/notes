# 010 — torchvision `references/classification` (resnet18 / Imagenette)

**Verdict: reproduced.** The recipe runs from published materials, trains a real model,
and the record of that run is complete and public.

The reference training recipe in [`pytorch/vision`](https://github.com/pytorch/vision)
`references/classification/train.py` runs end to end from published materials with **no
modification to any upstream file**, trains a resnet18 from scratch, and produces a real
checkpoint and a real held-out metric. Everything the run touched — the dataset it
downloaded, the checkpoint it wrote, the metric it scored — is in the published graph,
under the four steps that actually ran.

Upstream: [`pytorch/vision`](https://github.com/pytorch/vision) at
[`34572106`](https://github.com/pytorch/vision/commit/34572106ad1f0ea95793e379751f8bb0cfeeac1c),
BSD-3-Clause.
Fork: [`reproducible-ai/vision`](https://github.com/reproducible-ai/vision) at `032ac1b7`
(+414 lines, **0 deleted — no upstream file touched**).

---

## What was run

`references/classification/train.py` targets full ImageNet, which is not a runnable
reproducibility record. The recipe was truncated onto **Imagenette** — a 10-class
ImageNet subset published by fast.ai, MD5-verified on download, and already reachable
through `torchvision.datasets.Imagenette`, which extracts to exactly the `ImageFolder`
layout `train.py` expects. That keeps the *code path* upstream and only shrinks the data.

| | |
|---|---|
| Model | `resnet18`, trained **from scratch** (`--weights` unset) |
| Data | Imagenette 320px — 9,469 train / 3,925 val, 10 classes |
| Schedule | 4 epochs, batch 64, SGD lr 0.05, cosine annealing, 1 warmup epoch |
| Steps | 592 optimizer steps |
| Hardware | 1× g4dn.xlarge (Tesla T4), us-east-2c |
| Wall clock | fetch 2m32s · train 5m41s · evaluate 23.7s · host launch to pipeline complete 17m18s |
| Artefact | `checkpoint.pth`, 89,553,609 B, sha256 `d78326dda052…` → [huggingface.co/reproducible-ai/vision-classifier](https://huggingface.co/reproducible-ai/vision-classifier) |
| Metric | **top-1 55.36 %**, top-5 93.10 % on the held-out Imagenette val split |

Accuracy climbed 31.98 → 39.85 → 46.57 → 55.36 across the four epochs, so the run is
visibly learning and well clear of the 10 % chance level. It is **not** converged and
**not** an ImageNet number; the run is deliberately truncated and
`references/classification/REPRODUCIBLE_AI.md` in the fork says so at the top, because a
`55.4` sitting next to the word "resnet18" invites exactly the wrong reading.

We claim **reproduce, not replicate**. This identical recipe has now been run three times
and scored top-1 55.31 %, 60.13 % and 55.36 %. Nothing was changed between them:
`train.py` exposes no determinism flag and cuDNN algorithm selection is unpinned, so the
metric moves several points run to run. What reproduces is the *procedure and its
artefacts*, not the digits — a reader who reruns this and lands on 58 % has reproduced it.

Two additive scripts sit beside `train.py` (neither modifies it):
`fetch_imagenette.py` (download + extract) and `evaluate_checkpoint.py` (re-uses
`train.evaluate` unchanged and writes the accuracy to JSON). The second exists only
because of issue #1 below — upstream's own `--test-only --resume` path cannot read the
checkpoint upstream just wrote.

## The record

Tier 1 is green on all four gates:

```
  [✅] clean-dag    Clean-DAG check — 13/13 passed  ·  4 jobs (published DAG)
  [✅] ai-bom       AI-BOM score: 100/100  ·  profile: Advanced
  [✅] public-urls  RESULT: ALL PUBLIC
  [✅] freeze       RESULT: PORTABLE
```

The published graph carries all four steps — `fetch_imagenette` → `train` → `evaluate`
→ publish — numbered 1 to 4 with no gaps, matching the four steps the host actually ran.
That match was checked rather than assumed: the workflow dumps the local execution graph
immediately before and immediately after the publish, and both dumps report the steps the
published graph contains. A step that runs successfully and then quietly fails to appear
in the published record is not a hypothetical — it is why the check is in the workflow.

**On the recorded environment.** The record pins 44 distributions, and it is portable:
every pin resolves, the set installs as a set, no pin carries a `+cu` local version that
exists on no index, and no package appears twice under two PEP-503 spellings. It is also
*complete for what the recipe loads*. That was measured, not assumed — `import torch`
pulls `typing_extensions` and `numpy` into the process in the workload's own interpreter,
and `torchvision`'s downloader reaches for `tqdm` via `torch.utils.model_zoo`. All three,
plus `torch`, `torchvision` and `pillow`, are in the recorded set.

The honest qualifier runs the other way: 44 pins is a **superset**, not a minimum. A
fresh clone of this fork ran the whole pipeline — fetch, train, evaluate — in a scratch
virtualenv holding **13** distributions and nothing else. So the record over-describes
the environment rather than under-describing it. That is the safe direction to be wrong
in: a rebuild installs more than it strictly needs, instead of discovering a missing
import halfway through training. It is still worth stating plainly, rather than letting
"portable" stand in for "minimal".

**No experiment link.** `references/classification` ships no experiment-logging
integration at all: grepping the whole directory for `wandb`, `mlflow`, `tensorboard`,
`trackio`, `report_to` and `SummaryWriter` returns nothing. Adding one would mean writing
logging code into someone else's training script, which forfeits the zero-upstream-lines
property that makes this row worth anything. So there is no link, and that is a finding
about the upstream recipe rather than an omission here.

**Not certified.** No cold rebuild has been run against this record. Everything above
says the record is complete and public; none of it says the record has been executed.

## Reading order

- `issues.md` — upstream findings, two of them real bugs, with a prepared patch
- `commands.md` — the exact commands, reproducible as written
- `costs.md` — spend, and the fixed/variable split behind the full-run estimate
