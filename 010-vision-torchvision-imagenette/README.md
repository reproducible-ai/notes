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
Fork: [`reproducible-ai/vision`](https://github.com/reproducible-ai/vision) at `f3b4159`
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
| Hardware | 1× g4dn.xlarge (Tesla T4), us-east-2c |
| Wall clock | fetch 2m50s · train 5m47s · evaluate 23.9s · whole pipeline 15m09s |
| Artefact | `checkpoint.pth`, 89,553,609 B, sha256 `05e40efa79fa…` → [huggingface.co/reproducible-ai/vision-classifier](https://huggingface.co/reproducible-ai/vision-classifier) |
| Metric | **top-1 60.13 %**, top-5 93.78 % on the held-out Imagenette val split |

Accuracy climbed 32.8 → 41.6 → 51.1 → 60.1 across the four epochs, so the run is
visibly learning and well clear of the 10 % chance level. It is **not** converged and
**not** an ImageNet number; the run is deliberately truncated and
`references/classification/REPRODUCIBLE_AI.md` in the fork says so at the top, because a
`60.1` sitting next to the word "resnet18" invites exactly the wrong reading.

We claim **reproduce, not replicate**. An earlier run of this identical recipe on a
different GPU reached top-1 55.31 %. Nothing was changed between them: `train.py`
exposes no determinism flag and cuDNN algorithm selection is unpinned, so the metric
moves a few points run to run. What reproduces is the *procedure and its artefacts*, not
the digits.

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

**One honest caveat.** The recorded environment is 21 pins and it is portable: every pin
resolves, the set installs as a set, and none carries a `+cu` local version that exists on
no index. But it is *not* a complete list of what the recipe loads. `typing-extensions` is
imported in-process by `import torch`, and `tqdm` is used by torchvision's own download
path (`torch.utils.model_zoo.tqdm`) during the dataset fetch; neither appears in the
recorded pins. Both are transitive dependencies of `torch==2.7.0`, so installing the
recorded set brings them back and the rebuild works — but it works because the resolver
happens to supply them today, not because they were recorded. That is worth stating
plainly rather than letting "portable" stand in for "complete".

## Reading order

- `issues.md` — upstream findings, two of them real bugs, with a prepared patch
- `commands.md` — the exact commands, reproducible as written
- `costs.md` — spend
