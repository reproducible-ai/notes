# Commands

The public workflow is pinned to fork commit `5164ee1bcca097f05837faec983615de6e4c281a`:

```bash
git clone https://github.com/reproducible-ai/distil-whisper.git
cd distil-whisper
git checkout 5164ee1bcca097f05837faec983615de6e4c281a
```

The exact environment construction, student initialization, distillation, evaluation, labeling, and artifact publication commands are in `.treqs/workflows/distil-whisper.yaml`. It creates an isolated Python 3.12 environment and installs exact dependency versions before running the two upstream entry points.

Reproduce the attributed record without republishing artifacts:

```bash
roar reproduce acc9448d8d05c85402418424a7f9aa3da9bd539755554ba8442d95092d1bdad7 --lineage --run --no-puts
```

This command has not undergone independent Tier-2 cold certification.
