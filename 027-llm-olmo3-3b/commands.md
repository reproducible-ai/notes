# Recorded recipe

The exact editable commands are generated from the published lineage in `reproduce-no-puts.sh` and `reproduce.sh`. The safe reader-facing command is:

```sh
roar reproduce d88d877377a9d97f3213bd3604c0d1a2e6685374d98d374d81bd1325d0bf9a9b --lineage --run --no-puts
```

The recorded workflow had exactly six stages: isolated environment setup, public-data preparation, training, deterministic checkpoint packaging, artifact labeling, and publication.

Source was pinned at fork commit `790e8d09bfe0ba2b64618a1321fc2a3320d3dfc2`, based on upstream commit `92870a33c3fee060d57c3faec52b0b369ece85a6`.
