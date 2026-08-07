# patches

Empty on purpose. `karpathy/nanoGPT`'s `shakespeare_char` recipe required **no
patch** — it ran as published.

The only change to the fork was the addition of a workflow file under `.treqs/`
and the matching `.gitignore` rules, which are reproduction scaffolding rather
than a change to the model, the data pipeline or the training code. Not a single
line of `prepare.py`, `train.py`, `model.py`, `configurator.py` or
`config/train_shakespeare_char.py` was modified.
