# Patch inventory

Base: upstream `jiangranlv/LDA-1B` at `06e6a274a9086cc26635a9fe663866335eb30fc5`.

Executed candidate: `reproducible-ai/LDA-1B` at `b55c26dad419064089f588837c5048843537577a`.

[runtime-and-dependencies.patch](runtime-and-dependencies.patch) is the exact Git diff for `lda/`, `requirements.txt` and `pyproject.toml` between those commits. It contains 162 additions and 36 deletions in 12 files: 170 changed lines in runtime code and 28 in dependency/build metadata. It preserves upstream context and is intended for review of the executed changes, not as a proposed upstream PR.

```sh
git diff --full-index --binary \
  06e6a274a9086cc26635a9fe663866335eb30fc5 \
  b55c26dad419064089f588837c5048843537577a \
  -- lda/ requirements.txt pyproject.toml
```

The full candidate has 3,626 additions and 36 deletions across 47 files. The remaining 35 files add 3,464 lines of workflow/scripts, configuration, license notices, regression tests, operational notes and ignore rules. Review those separately in the [complete pinned comparison](https://github.com/reproducible-ai/LDA-1B/compare/06e6a274a9086cc26635a9fe663866335eb30fc5...b55c26dad419064089f588837c5048843537577a).

This patch alone is not the complete runnable recipe: the workflow and adapter scripts are also needed. The [command record](../commands.md) links their immutable source. No generated `roar reproduce` script is included because this draft does not release a public lineage record or claim a cold rebuild.

Patch and source digests are recorded in [the evidence summary](../evidence/capture-summary.json). The source/demo's recorded CC-BY-NC-4.0 terms apply to the upstream source reproduced in this diff; the notes repository's prose license does not relicense third-party code.

The patch is retained byte for byte, including whitespace in upstream context lines. The local Git attribute excludes this evidence file from whitespace cleanup; report files retain the normal whitespace checks.
