# Tier 2 — cold rebuild certification · row 005 timm ResNet-18 / Fashion-MNIST

**STATUS: IN PROGRESS** — this file is pushed early so the evidence survives an agent
death. It will be replaced with the final result.

| | |
|---|---|
| DAG | `42b381d91f299d028c45ff043a71e34e6c9e1122574585f32c3b3d99b31f10c2` |
| HF repo | `reproducible-ai/timm-classifier` |
| Instance | `i-0b890ed5cb2a1038c` · g4dn.xlarge · 1×Tesla T4 15360 MiB · `ami-0f07f1a0b382b48f7` · us-east-2a |
| Recorded interpreter | Python 3.12.10 |
| Host interpreter | Python 3.10.12 (`python3` only; bare `python` absent) |
| Date | 2026-08-10 |

## Tier-1 pre-flight (free, run before spending)

```
Tier-1 bar — 42b381d91f299d02 · reproducible-ai/timm-classifier
  [OK] clean-dag    Clean-DAG check — 13/13 passed  ·  4 jobs (published DAG)
  [OK] ai-bom       AI-BOM score: 100/100  ·  profile: Advanced
  [OK] public-urls  RESULT: ALL PUBLIC
  [OK] freeze       RESULT: PORTABLE
RESULT: REPRODUCIBLE RECORD — tier 1 complete
```

Recorded pins per job (from `jobs/<uid>.metadata.packages.pip`, the job record, not the
session endpoint): step 1 `fetch` 44 · step 2 `train` 45 · step 3 `validate` 57 ·
step 4 `put` 0. Union = **57**.
