# Distil-Whisper

The truncated teacher-student pipeline completed training, evaluation, artifact upload, and attributed lineage publication. The record is not Tier-1 complete: its mechanical gate reached 13/14 because no verified hosted experiment URL was produced, and no cold certification was attempted.

## What was run

The upstream two-stage path was preserved: `create_student_model.py` first derived a student from a teacher checkpoint, then `run_distillation.py` performed distillation and evaluation. The run used upstream's documented `--use_pseudo_labels False` alternative, so the public fixture's transcripts supplied the labels. Evaluation computed loss and word error rate; metric values are not treated as replication targets.

This was deliberately a pipeline proof. It used `openai/whisper-tiny.en`, a four-encoder/one-decoder-layer student, two training samples, one evaluation sample, and one optimizer step. Upstream recommends at least 50,000 steps for convergence and reports work at a vastly larger data scale. Nothing in this row claims convergence or comparable model quality.

## What the record contains

The completed run published a 122,661,856-byte `model.safetensors` artifact and the attributed DAG `acc9448d8d05c85402418424a7f9aa3da9bd539755554ba8442d95092d1bdad7`. The AI-BOM scored 100/100, all artifact and source URLs resolved anonymously, and the environment passed the portability audit.

A separate import-versus-freeze check found one caveat beyond the main gate: `wandb` is a top-level dependency on the executed path but is absent from the DAG's 62-package freeze. The record therefore should not be presented as a complete cold-reproduction proof.

## Attempts and cost

The first paid attempt was cancelled after environment validation detected an incompatible interpreter, before distillation completed. The corrected second attempt completed all five workflow tasks. The two attempts cost $0.05 and $0.06 respectively, for $0.11 total campaign spend; the structured rebuild cost is the $0.06 completed run.

The completed job took 4m18s from start to terminal state. About 1m48s was environment setup, 23s student initialization, 40s distillation plus evaluation, and 11s artifact publication; the remainder was task orchestration.

## Limits of the result

No verified hosted experiment run was produced, so `experimentUrl` is null and the clean-DAG gate remains 13/14. A full-run estimate is also intentionally null: scaling one tiny-model step on two fixture examples to the published recipe would imply precision the measurement does not have. Restoring the published teacher, student depth, datasets, sample counts, batching, and at least 50,000 optimizer steps is required for a full run.

No Tier-2 certification was run, and this row is not marked CLEAN or certified.
