# 009 — litgpt pretrain · costs

Compute target `reproai-g4dn-plaintorch-a` — g4dn.xlarge, 1× Tesla T4,
us-east-2, AMI `ami-0f07f1a0b382b48f7`. Budget for this row was NTE $10.

## Cloud attempts

| # | job | outcome | wall clock | cost |
|---|---|---|---|---|
| 1 | `db05cb58` | COMPLETED — 3 steps, tokenization inline | 10 m 05 s | $0.02 |
| 2 | `f7b318cf` | FAILED — new prepare step could not `import litgpt` | 6 m 11 s | $0.03 |
| 3 | `1c0bacd5` | COMPLETED — 4 steps, tokenization split out | 3 m 20 s | $0.03 |
| 4 | `d5ac7e31` | COMPLETED — final; shim removed | 2 m 01 s | $0.02 |
| 5 | `302d133b` | COMPLETED — re-capture on updated provenance tooling | 7 m 14 s | $0.06 |
| 6 | `1ae272fc` | COMPLETED — final capture; the certified one | 9 m 04 s | $0.06 |
| | | | **37 m 55 s** | **$0.22** |

Attempts 5 and 6 re-ran the identical pipeline to re-record it with newer builds
of the campaign's provenance tooling. Neither changed anything about litgpt, the
recipe or the result — same commit, same command, same `val loss 9.738`.

## Certification

An independent cold rebuild on a freshly launched `g4dn.xlarge` — a host that had
never seen this row — took **~24 minutes** end to end including bootstrap, of
which the rebuild itself was about 5 minutes. Estimated **$0.22**.

**Row total: $0.44.**

Attempt 2 was my error, not the repo's: the prepare step was invoked as
`python reproduction/prepare_data.py`, which puts the *script's* directory on
`sys.path` rather than the repository root, so `import litgpt` failed (litgpt is
deliberately not installed). `python -m reproduction.prepare_data` fixes it —
the same path-independent form the litgpt steps already used. Cost of the
mistake: $0.03 and six minutes.

Attempts 1 → 3 → 4 were not retries of a failure but three deliberately
different recordings; each was kept and compared, and the comparison is where
most of this row's findings came from.

## Local (free)

Nearly all the real work ran on the local CPU box at zero cloud cost:

- bare-clone check — full pipeline in a scratch venv, ~4 min
- five instrumented local pipeline runs to isolate issue #7, ~2 min each
- one cold `roar reproduce --lineage --run --no-puts`, ~9 min
- dependency-resolution experiments, seconds each

The single most valuable minute in the row was the bare-clone check, which
caught issue #1 (`litgpt download` broken on huggingface_hub >= 1.0) before any
instance was ever provisioned. Finding that on the GPU instead would have cost a
provisioning cycle per iteration rather than five seconds.

## Final rebuild

Attempt 6: **9 m 04 s, $0.06** (the recipe of record), comprising a dependency install, ~11 s
tokenizer download, <1 s data fetch, ~59 s tokenization and ~30 s of
pretraining, then label and publish.

The truncated run trains 8 optimizer steps on 2,048 tokens. A meaningful litgpt
pretraining run is 3e12 tokens by default — nine orders of magnitude more — so
no inference about full-scale cost should be drawn from this figure.
