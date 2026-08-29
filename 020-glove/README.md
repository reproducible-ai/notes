# GloVe on text8

This row runs Stanford NLP's published GloVe `demo.sh` recipe end to end on the complete text8 corpus: vocabulary construction, co-occurrence generation, shuffle, 15 training iterations, and the supplied word-analogy evaluation. No upstream workload source was changed.

The successful recorded job ran for 3h07m08s on one Tesla T4 and reported 22.82% total analogy accuracy. Its model bundle and evaluation are public at Hugging Face. The lineage record has an AI-BOM score of 100/100 and every public URL resolves.

The row is nevertheless blocked at Tier 1. Strict Clean-DAG verification passed 13 of 14 checks: the separately published `evaluation.txt` does not trace to a producing job output. Under campaign policy, a successful workload and a green AI-BOM are not substitutes for a complete record, so no Tier-2 rebuild was requested.

The upstream demo also does not set the seed options implemented by its shuffle and training binaries. Complete executions consequently report different analogy scores; this row makes no metric-equivalence claim.

## Attempt accounting

- Clean-environment run: exit 0, full text8 demo, 22.68% accuracy, no compute charge.
- First recorded retry: stopped during co-occurrence generation at the then-current time limit; approximately $0.15.
- Second recorded retry: full training and evaluation completed, but publication did not retain its evaluation input; approximately $1.67.
- Final recorded retry: all eleven tasks exited 0 and lineage was published; approximately $1.67.

The job estimate for each complete recorded run was $1.65; the compute-target meter increment was approximately $1.67. Both measurements are retained rather than silently reconciled.
