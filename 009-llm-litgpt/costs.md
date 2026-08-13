# 009 — litgpt pretrain · costs

Compute target `reproai-g4dn-plaintorch-a` — g4dn.xlarge, 1× Tesla T4,
us-east-2, AMI `ami-0f07f1a0b382b48f7`. Budget for this row was NTE $10.

## Cloud attempts

| # | job | outcome | wall clock | cost |
|---|---|---|---|---|
| 1 | `db05cb58` | COMPLETED — 3 steps, tokenization inline | 10 m 05 s | $0.02 |
| 2 | `f7b318cf` | FAILED — new prepare step could not `import litgpt` | 6 m 11 s | $0.03 |
| 3 | `1c0bacd5` | COMPLETED — 4 steps, tokenization split out | 3 m 20 s | $0.03 |
| 4 | `d5ac7e31` | COMPLETED — recipe reduced to litgpt's own csv logger | 2 m 01 s | $0.02 |
| 5 | `302d133b` | COMPLETED — re-capture on updated provenance tooling | 7 m 14 s | $0.06 |
| 6 | `1ae272fc` | COMPLETED — re-capture on updated provenance tooling | 9 m 04 s | $0.06 |
| 7 | `a1fd4795` | COMPLETED — capture superseded by #8 | 8 m 51 s | $0.06 |
| 8 | `a6284f05` | COMPLETED — final capture; the certified one | 9 m 44 s | $0.16 |
| | | | **56 m 30 s** | **$0.44** |

Attempts 5, 6, 7 and 8 re-ran the identical pipeline to re-record it with successive
builds of the campaign's provenance tooling. None changed anything about litgpt, the
recipe or the result — same commit, same command, same `val loss 9.738`.

Attempt 8 is the record of reference. It exists for one substantive reason: attempts
1-7 were all captured on an **unpublished** build, identified only by a sha256, which a
third party cannot install. Attempt 8 is captured on a **published** build, so the
`roar reproduce` command on this row's page is one a reader can actually run. The
recipe is byte-identical to attempt 7 apart from where roar comes from. Its $0.16 is
the honest **billed instance lifetime** (17 m 56 s, launch to termination, at
$0.526/h), not the 9 m 44 s of traced work — earlier rows in this table quoted the
traced time only, which understates them.

## Certification

Three independent cold rebuilds, each on a freshly launched `g4dn.xlarge` that had
never seen this row. The final one (of attempt 8, `3b9c6606`) ran **22 m 03 s** of
billed instance lifetime — bootstrap, purge, roar install, rebuild and evidence
collection — of which the rebuild itself was **2 m 30 s**. **$0.19** at $0.526/h.

**Row total: $0.85.**

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

## Final rebuild — and where the 9 m 44 s went

Attempt 8, the recipe of record, measured per stage from timing markers written into
the workflow (these are not reconstructible afterwards, which is why they are taken
during the run):

| stage | duration |
|---|---|
| host provisioning | 156.4 s |
| environment setup (roar + litgpt deps) | 121.8 s |
| `litgpt download` (tokenizer) | 112.0 s |
| WikiText-2 fetch | 2.4 s |
| litdata tokenization | 62.1 s |
| `litgpt pretrain` | 107.5 s |
| label | 0.7 s |
| publish (169 MB to HF) | 17.7 s |
| **total** | **580.6 s** |

Of the 107.5 s pretrain stage, **0.43 s is actual token throughput** — 16 iterations at
26.900 ms. Everything else is model construction, `torch.compile` and the final
validation pass. That is the whole reason a full-run estimate cannot be produced by
multiplying the headline: 99.93 % of this run is fixed cost.

At litgpt's default `max_tokens` of 3e12 (`litgpt/pretrain.py:61`), a direct linear
extrapolation produces 23.4 billion iterations and roughly $92,120 on one T4. That
arithmetic is reproducible but is not a defensible forecast: the calibration is
compile-dominated and too short to establish sustained throughput or a full-scale
hardware plan. See `row.json` → `fullRun.estimateBasis` for why the estimate is now
intentionally empty.
