# OLMo 3 3B scaling-ladder rung

The published OLMo-core 3B ladder architecture trained from scratch for one bounded optimizer step on 8,192 tokens from a pinned public Dolma 3 shard. The run produced a complete 42,044,866,560-byte checkpoint archive and metrics record, with a public attributed lineage that passes the mechanical Tier-1 record checks; this is a Reproducible record, not a Certified reproduction, and no convergence or model-quality claim is made.

## Why the 3B rung

OLMo-core publishes named ladder sizes from 60M through 13B. The selection question was not which small architecture was convenient, but which published rung fit one NVIDIA RTX PRO 6000 Blackwell Server Edition without changing width, depth, context length, vocabulary, optimizer, or precision.

The 7B rung was rejected before spending: parameters plus gradients and Adam states alone have a conservative 102.63 GiB floor, already above device capacity before activations. The 3B rung has 3,169,537,280 non-embedding parameters and 3,503,508,736 total parameters, with a corresponding 47.23 GiB state floor. During the recorded step it peaked at 88.10 GiB active and 91.65 GiB reserved on an NVIDIA RTX PRO 6000 Blackwell Server Edition with 94.97 GiB measured capacity. That makes 3B the largest upstream rung supported by both the accounting bound and an observed run.

## What changed

The highest edit tier was **E2**. E0 changes placed the existing rung on one device: world size one and one 8,192-token sequence per rank. E2 reduced the global batch to 8,192 tokens, the duration to one optimizer step, and disabled validation for the bounded capture. The architecture remained the upstream `TransformerConfig.olmo3_3B`, and the upstream 8,192-token context, bfloat16 training path, optimizer construction, and learning-rate calculation were retained. OLMo-core's configurator accepts only an H100- or B200-containing compatibility label to select its kernel branch. The current adapter therefore names the measured RTX PRO 6000 hardware and includes `B200 compatibility` solely as the API selector; the captured execution used the shorter selector `NVIDIA B200`, which was not a measurement of the machine.

The public ladder entry point defaults to a tokenized data mix below `gs://ai2-llm/`, which is not a public reproduction input. The adapter therefore tokenized a deterministic prefix of `allenai/dolma3_mix-6T`, specifically `data/dolma1_7-wiki-en/00000.jsonl.zst` at revision `689a3ea2d8217e64d73a5058913fa43ad15e81aa`, with `allenai/dolma2-tokenizer` at revision `5292e5d6c0f40b67cc765fe41bec991cf4345b5c`. It prepared 32,768 tokens so the one-step loader had a finite, inspectable source. This is an explicit data-preparation adaptation, not a claim to have run the private storage-backed mix.

## What the result establishes

The optimizer step completed with cross-entropy loss 12.18, z-loss 0.0015, gradient norm 20.19, and zero skipped steps. Those values are execution evidence only: one batch cannot establish learning, convergence, or parity with a full ladder training curve.

Checkpoint packaging was deliberately mechanical. Every entry below `outputs/3B/step1` was traversed in sorted order and written to an uncompressed PAX tar with normalized timestamps, ownership, and names. The archive member list was then compared exactly with the source traversal, including hidden metadata; files were not silently selected or omitted. The public archive is 42,044,866,560 bytes, and Hugging Face reports its LFS SHA-256 as `c9b8ff7e9ed2532281af3acea5d40a6c0674afb7a681de6365f44c31becb88b7`.

The attributed record passes Clean-DAG 14/14, AI-BOM 100/100 (Advanced), anonymous public-URL checks, and the portable dependency-freeze check. Independent cold certification has not been run, so this row is not certified.

## What a full run would require

The upstream 4×-Chinchilla duration is 253,562,982,400 tokens for this rung, rather than the 8,192 tokens recorded here. A defensible full-run dollar estimate is intentionally left blank. The single observed step includes first-step compilation, checkpoint writing, environment setup, and publication, while the upstream recipe is designed for a different global batch and a multi-device topology. Scaling the total wall clock or the first-step timing would publish false precision.

To restore the full run, use the upstream target batch calculation (3,117,679 tokens before topology-compatible rounding), restore the 4×-Chinchilla token duration and checkpoint schedule, enable the published evaluation callbacks, and provide a complete public tokenized form of the intended training mix. A one-device full run is not implied by this capture.

## Attempt history

Two early attempts ended before an optimizer step while the isolated runtime integration was corrected. A third trained and saved the full checkpoint directory but did not produce the finite published artifact used by this row. The fourth attempt added deterministic directory packaging and completed all six recorded stages. All four cloud attempts are retained in `row.json`; their combined metered spend was $3.60, while the successful Tier-1 capture cost $1.85.

Optional hosted experiment logging was disabled for this bounded run, and no verified public experiment run was produced.
