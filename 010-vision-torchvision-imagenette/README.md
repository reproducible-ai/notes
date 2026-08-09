# 010 — torchvision `references/classification` (resnet18 / Imagenette)

**Verdict: partial.** The model rebuilds. The *record* of the rebuild is incomplete.

The reference training recipe in [`pytorch/vision`](https://github.com/pytorch/vision)
`references/classification/train.py` runs end to end from published materials with **no
modification to any upstream file**, trains a resnet18 from scratch, and produces a real
checkpoint and a real held-out metric. The lineage captured for that run, however, is
missing a step and is not attributed, so the row is held below the tier-1 bar pending a
re-capture. The shortfall is in the capture, not in torchvision.

Upstream: [`pytorch/vision`](https://github.com/pytorch/vision) at
[`34572106`](https://github.com/pytorch/vision/commit/34572106ad1f0ea95793e379751f8bb0cfeeac1c),
BSD-3-Clause.
Fork: [`reproducible-ai/vision`](https://github.com/reproducible-ai/vision) at `5fb94ce`
(+361 lines, **0 deleted — no upstream file touched**).

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
| Hardware | 1× g6e.xlarge (L40S), us-east-2 |
| Wall clock | train 3m43s; whole pipeline ~17m including dataset fetch |
| Artefact | `checkpoint.pth`, 89,551,113 B → [huggingface.co/reproducible-ai/vision-classifier](https://huggingface.co/reproducible-ai/vision-classifier) |
| Metric | **top-1 55.31 %**, top-5 92.23 % on the held-out Imagenette val split |

Accuracy climbed 29.4 → 32.5 → 38.4 → 55.3 across the four epochs, so the run is
visibly learning and well clear of the 10 % chance level. It is **not** converged and
**not** an ImageNet number; the run is deliberately truncated and
`references/classification/REPRODUCIBLE_AI.md` in the fork says so at the top, because a
`55.3` sitting next to the word "resnet18" invites exactly the wrong reading.

Two additive scripts sit beside `train.py` (neither modifies it):
`fetch_imagenette.py` (download + extract) and `evaluate_checkpoint.py` (re-uses
`train.evaluate` unchanged and writes the accuracy to JSON). The second exists only
because of issue #1 below — upstream's own `--test-only --resume` path cannot read the
checkpoint upstream just wrote.

## What blocks the row

The published lineage for this run has two gaps, both in the capture rather than in
torchvision:

- the **evaluate step is absent** from the published graph. It ran (exit 0, wrote
  `metrics.json`, top-1 55.3121) but only 3 of the 4 recorded steps reached the
  published DAG, so the metric artefact is not in lineage;
- the graph carrying the run is **not attributed** to the organisation.

Tier-1 therefore reports `NOT PUBLISHABLE` (clean-dag 10/13, AI-BOM 82.8/100). Freeze
audit is **PORTABLE** and public-URL check is **ALL PUBLIC**; an imports-vs-freeze audit
found **zero Tier-A misses** against the 44 recorded pins, with three Tier-B maybes
(`requests`, `urllib3`, `charset-normalizer`) — none of which is imported by any script in
the recipe, so the recorded pins cover what the workload actually loads. Imagenette is
fetched through `torchvision.datasets`, which uses stdlib `urllib`, not `requests`.

The training and evaluation themselves are sound — see `issues.md` for the upstream
findings, which stand on their own regardless of the record's status.

## Reading order

- `issues.md` — five upstream findings, two of them real bugs, with a prepared patch
- `commands.md` — the exact commands, reproducible as written
- `costs.md` — spend
