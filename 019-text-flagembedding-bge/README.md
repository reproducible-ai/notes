# FlagEmbedding checkpoint fine-tune

This record adapts a compact BERT checkpoint with FlagEmbedding's published encoder-only fine-tuning entry point. It is a checkpoint fine-tune, not training a model from scratch, and its single optimizer step demonstrates that the published pipeline executes rather than convergence or embedding quality.

## What was run

The recorded command invoked `FlagEmbedding.finetune.embedder.encoder_only.base`, starting from `prajjwal1/bert-tiny` and using the repository's public ten-example NLI file. It ran one optimizer step with batch size one, query length 32, passage length 64, CLS pooling and normalized embeddings on one Tesla T4. Seed 43 distinguishes this sub-row capture from the earlier seed-42 capture.

The run produced a 17,547,912-byte `model.safetensors` checkpoint with SHA-256 `f906e515a17d89038114d56af5c06d31fb68808532bac93bf69521e45924e3ad`. The artifact is publicly downloadable from the `reproducible-ai/flagembedding-bge-finetune` Hugging Face repository.

## Timing and scope

The instance lifetime through job completion was 5m20s. Environment setup took 75.6 seconds, the fine-tune took 27.3 seconds, artifact labeling took 0.6 seconds and upload took 7.0 seconds. The target meter reported $0.05 at completion.

The one optimizer step represented 0.1 epoch over the selected ten-example file. Upstream's standard encoder example instead initializes `BAAI/bge-large-en-v1.5`, combines four groups of example data, uses two processes with DeepSpeed, processes sequences up to 512 tokens and runs two epochs. Those differences are listed explicitly in `row.json`.

Because the checkpoint, dataset, parallelism, sequence lengths and training duration all changed together, multiplying the observed step time would not produce a defensible estimate for the full published recipe. The full-run estimate is therefore null with its basis stated.

## Record status

The attributed public lineage contains two jobs and twenty artifacts. Strict Clean-DAG verification passes 14/14, including the training-request backlink. The AI-BOM scores 100/100, all recorded URLs resolve anonymously, the dependency freeze is portable, and an imports-versus-freeze audit reports no decisive missing packages.

This is a Tier-1 record only. No independent cold rebuild has certified it yet.

No experiment URL is claimed. The selected upstream fine-tune recipe explicitly disables external reporting with `WANDB_MODE=disabled`, and the recorded invocation follows that path with `--report_to none`. Adding a new logging integration would change the workload.
