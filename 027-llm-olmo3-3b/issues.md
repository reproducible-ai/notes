# Upstream reproducibility findings

## P0 — The ladder defaults to a non-public tokenized data root

`src/olmo_core/internal/ladder.py` constructs the default ladder input from `DataMix.OLMo_mix_0925` beneath `gs://ai2-llm/`. The repository exposes local `run` and `benchmark` commands, but the default training data they resolve is not anonymously readable, and the ladder entry point contains no public preparation path for the corresponding tokenized mix.

A competent external reproducer therefore cannot follow the published ladder entry point from source and public inputs alone. This capture adapted the recipe to a pinned subset of the official public `allenai/dolma3_mix-6T` dataset and pinned official Dolma 2 tokenizer. That makes the bounded data used here reproducible, but it does not make it identical to the storage-backed default mix.

An upstream fix would expose a public manifest and preparation command for the ladder's intended mix, including immutable dataset and tokenizer revisions.
