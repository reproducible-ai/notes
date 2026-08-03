# Candidates — seeded from an internal phase-1 analysis (40 models)

Source: an internal phase-1 analysis. This is a **merge of existing
analysis into the survey taxonomy**, not the full dated snapshot
(that's the A-SURVEY task). Machine-mapped from the analysis's `phase1a_status` +
`has_training_data/split/code` — review before publishing.

## Category counts (of 40)

| Category | Count | Mapping rule |
|---|---:|---|
| `no-training-pipeline` | 16 | not_reproducible + no training code (weights/inference/wrapper only) |
| `recipe-incomplete` | 13 | training code present but data/split/hyperparams missing or ambiguous (incl. all needs_more_info) |
| `queued` (eligible) | 9 | reproducible per cold read (8) + 1 additional eligible (FastWAM) |
| `not-applicable` | 2 | not a real reproduction target (API client / speculative arch) — **excluded from repro-rate stats** |

**Headline (of 38 real candidates):** ~21% eligible, ~42% ship no training code.
That is the campaign's core ecosystem finding, in miniature.

## Queued / eligible

| id | model | license | sec | note |
|---|---|---|---|---|
| m07 | Ultralytics YOLO | AGPL-3.0 (paid tier) | medium | `exec()` in dataset YAML — vet before use |
| m11 | CosyVoice | Apache-2.0 | low | 8×A100 (ci002) |
| m16 | Needle | MIT | low | full pretrain is TPU/cost-blocked; finetune-only feasible |
| m17 | GR00T-WholeBodyControl | Dual Apache/custom | medium | Isaac Sim (ci003); reduced-scope only |
| m24 | LingBot-VA | Apache-2.0 | low | overlaps other campaign work — reconcile selection before use |
| m27 | FastWAM | — | — | overlaps other campaign work — reconcile selection before use |
| m33 | MiniMind-O | Apache-2.0 | low | small LLM, full pipeline, ~2h on 1×3090 → minutes at reduced scale |
| m34 | InsightFace | MIT (code) | low | 8×A100 (ci002) |
| m37 | SAM 2 | Apache-2.0 | low | 8×A100 (ci002) |

## Smoke-test model pick

**Primary: MiniMind-O (m33).** Apache-2.0, security low, a genuine end-to-end
small-LLM pipeline (data → train → eval) that traverses on one small GPU in ~2h,
so at reduced scale (a few steps) it runs in minutes — CPU-feasible for a pure
apparatus test. Best representative-yet-cheap choice.

**Backup: YOLO (m07)** — tinier, but AGPL + a medium security flag (`exec()` in
dataset YAML) make it a messier first exercise of the apparatus.

Avoid for the smoke test: the ci002/ci003 models (8×A100 / Isaac Sim) and the two
overlapping models (m24, m27) until selection is reconciled.
