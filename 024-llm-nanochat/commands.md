# Commands

The immutable workflow is recorded at fork commit [`7ab29ea9a408be642f8cc5e2538e862e936c5415`](https://github.com/reproducible-ai/nanochat/commit/7ab29ea9a408be642f8cc5e2538e862e936c5415).

The principal upstream workload commands were:

```sh
python -m nanochat.dataset -n 170
python -m scripts.tok_train
python -m scripts.tok_eval
python -m scripts.base_train --depth=14 --target-param-data-ratio=8 --device-batch-size=32 --fp8 --model-tag=depth14 --run=nanochat-depth14
python -m scripts.base_eval --model-tag=depth14 --device-batch-size=32
python -m scripts.chat_sft --model-tag=depth14 --run=nanochat-depth14
python -m scripts.chat_eval -i sft --model-tag=depth14
```

For the complete captured ordering, environment reconstruction, packaging, and optional publication command, inspect `reproduce-no-puts.sh` and `reproduce.sh`. They are emitted verbatim from the lineage.
