# GloVe on text8

This row runs Stanford NLP's published GloVe `demo.sh` recipe end to end on the complete text8 corpus: vocabulary construction, co-occurrence generation, shuffle, 15 training iterations, and the supplied word-analogy evaluation. No upstream workload source was changed.

The final recorded job ran for 3h07m53s on one Tesla T4 and reported 22.99% total analogy accuracy. Its model bundle and evaluation are public at Hugging Face. The lineage record passes strict Clean-DAG verification 14/14, has an AI-BOM score of 100/100, has a portable dependency freeze, and every public URL resolves.

The evaluation job itself records `evaluation.txt` as an output; this positive control distinguishes the final record from the preceding one, where the file existed but lacked that producing edge. Tier 1 inspects the record and executes nothing. Independent Tier-2 certification is pending and is required before this row can be called reproduced.

The upstream demo also does not set the seed options implemented by its shuffle and training binaries. Complete executions consequently report different analogy scores; this row makes no metric-equivalence claim.

## Attempt accounting

- Clean-environment run: exit 0, full text8 demo, 22.68% accuracy, no compute charge.
- First recorded retry: stopped during co-occurrence generation at the then-current time limit; approximately $0.15.
- Second recorded retry: full training and evaluation completed, but publication did not retain its evaluation input; approximately $1.67.
- Final recorded retry: all eleven tasks exited 0 and lineage was published; approximately $1.67.
- Direct-writer retry: all eleven tasks exited 0, lineage was published, and all Tier-1 gates passed; $1.70 on the target meter.

The final job estimate was $1.65; its compute-target meter was $1.70 for 192 instance-minutes including provisioning and finalization. Both measurements are retained rather than silently reconciled. Earlier complete attempts were estimated at $1.65 and metered at approximately $1.67 each.
