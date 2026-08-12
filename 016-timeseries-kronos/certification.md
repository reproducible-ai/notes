# Row 016 — Kronos — tier 2 certification (cold rebuild)

**Result: REPRODUCED.** Exit code **0**, `Steps run: 3/3`, pin diff **46/46 EXACT**.

This is an independent cold rebuild performed by a different agent than the one that
captured the row, on a host that had never seen it, from the published record and the
published notes only.

| | |
|---|---|
| DAG | `847b359a9f1a0ae3a31a621f9901f57e5387f37610adabc9e7bd24f4ecdae97d` |
| roar | `roar, version 0.4.4rc6` (TestPyPI, installed by name+version) |
| wheel sha256 | `c7115b748886259b6a089e547404376acf84c3b81b4cbc8dc5610490ebea7199` — verified on disk before install |
| wheel | `roar_cli-0.4.4rc6-cp310-abi3-manylinux_2_34_x86_64.whl` |
| interpreter | Python **3.12.10** (the recorded interpreter; provisioned by uv) |
| instance | `g4dn.xlarge`, 1× Tesla T4, `ami-0f07f1a0b382b48f7`, us-east-2 |
| driver / CUDA | 580.126.09 / 13.0 |
| exit code | **0** (read from file, not inferred from log text) |
| steps | **3/3** |
| wall-clock | run 66m40s (01:49:56 → 02:56:36 UTC); instance lifetime ~82 min |
| spend | ~$0.72 at g4dn.xlarge on-demand list ($0.526/h) |

## Command

```
roar reproduce 847b359a9f1a0ae3a31a621f9901f57e5387f37610adabc9e7bd24f4ecdae97d \
  --lineage --run --no-puts -y --step-timeout 21600
```

Run detached; exit status written to a file and read back. No `--pip-any-version`, and
`--export-requirements` was not combined with `--run`.

## Step results

| step | command | recorded | rebuild |
|---|---|---|---|
| 1 | `python repro/fetch_pretrained.py` | 4.5 s | **4.5 s**, exit 0 |
| 2 | `env -C finetune_csv python train_sequential.py --config configs/config_repro_kronos-small_1epoch.yaml --skip-basemodel` | 984.2 s | **978.9 s**, exit 0 |
| 3 | `env -C finetune_csv python train_sequential.py --config configs/config_repro_kronos-small_1epoch.yaml --skip-tokenizer` | 2918.0 s | **2892.3 s**, exit 0 |

All three within ~1% of the recorded durations. The data geometry reproduced exactly:
`Training set size: 83960, Validation set size: 8832`, 2,623 optimizer steps per stage
at batch 32, lookback 512 / predict 48.

## Package manifest diff — 46/46, EXACT

The record carries **19** pins on step 1 and **45** on each training step; their union is
**46**, which is the number the reproduce venv must satisfy. roar builds one venv for the
session, and it satisfied the union.

```
RECORDED union across the 3 producing steps : 46 pins
INSTALLED in reproduce venv                 : 67 dists
MISSING   (recorded but not installed): 0
MISMATCH  (installed at wrong version): 0
>>> PIN DIFF: 46/46   EXACT=YES
```

Enumerated by two independent methods, which agreed: `uv pip freeze --python <venv>/bin/python`
reported **67**, and `importlib.metadata` counted **67**. The 21 extras are the transitive
closure and nothing else — the `cu121` NVIDIA stack that `torch==2.3.0` depends on
(`nvidia-cublas-cu12`, `nvidia-cudnn-cu12==8.9.2.26`, `nvidia-nccl-cu12`, and 13 more),
plus `cffi`, `flatbuffers`, `fsspec`, `networkx`, `pyasn1`, `pyasn1-modules`, `pycparser`,
`tzdata` and `pip`.

`fsspec`, flagged in the record as the sole Tier-B hint, installed transitively as predicted
and was never needed as a direct pin.

## The recorded torch/numpy question — settled

The record pins `torch==2.3.0` and `numpy==1.26.4`, and the notes state plainly that these
were a previous occupant's downgrade left on a warm shared instance, not this image's
versions. The rebuild tested whether that matters.

**It did not.** Both installed from the record, not from the host:

```
host  /opt/pytorch  torch == 2.7.0     numpy == 2.4.4     (importlib.metadata)
venv  reproduce     torch == 2.3.0     numpy == 1.26.4    (importlib.metadata)
```

and the log shows them resolved and installed by name from PyPI:
`Collecting torch==2.3.0` / `Collecting numpy==1.26.4` →
`Successfully installed … numpy-1.26.4 … torch-2.3.0 …`.

Every package the workload imports resolved from **inside** the reproduce venv:

```
torch            -> /root/reproduce/Kronos/.venv/lib/python3.12/site-packages/torch/__init__.py
numpy            -> .../.venv/lib/python3.12/site-packages/numpy/__init__.py
pandas           -> .../.venv/lib/python3.12/site-packages/pandas/__init__.py
yaml             -> .../.venv/lib/python3.12/site-packages/yaml/__init__.py
einops           -> .../.venv/lib/python3.12/site-packages/einops/__init__.py
huggingface_hub  -> .../.venv/lib/python3.12/site-packages/huggingface_hub/__init__.py
safetensors      -> .../.venv/lib/python3.12/site-packages/safetensors/__init__.py
```

No package resolved from outside the venv. The host provides no `python` at all on `PATH`
(only `python3`), so the recorded `python train_sequential.py` could only have run against
the venv's own `python` — which is independent confirmation that the venv was actually used
rather than merely built.

**torch 2.3.0 worked on a T4.** In the reproduce venv: `torch.cuda.is_available() == True`,
`torch.cuda.get_device_name(0) == 'Tesla T4'`, `torch.version.cuda == '12.1'`, and both
training stages logged `Device: cuda:0` and ran at 100% GPU utilisation with 6.8 GB resident.

The record's warning about version-checking method is confirmed exactly: in the rebuilt venv
`torch.__version__` reads **`2.3.0+cu121`** (the build tag) while the distribution version is
a plain **`2.3.0`**. `importlib.metadata` is the source that agrees with the record.

The eight base-image packages behaved as the record described — `onnxruntime` announced itself
in the training log with the documented GPU device-discovery warning
(`Failed to open file: "/sys/class/drm/card0/device/vendor"`), confirming they are loaded at
interpreter start rather than imported by Kronos.

## Artefacts produced — size and sha256

Checked on the host before termination.

| bytes | sha256 | path |
|---|---|---|
| 301 | `2366e7ccfec76cbc19cf3c4c1b9c5d901be336ca1e83f2d2292c9bff381b77a2` | `pretrained/Kronos-Tokenizer-base/config.json` |
| 15,842,368 | `59d85f6af76a2c3b8240ea06cb21db4213b4eeca053f246b23e29cf832fc6bee` | `pretrained/Kronos-Tokenizer-base/model.safetensors` |
| 228 | `5e0f6a605d5f81b5c9b559fe5cf716a1acb041c744e6f41bd05b097b7a685396` | `pretrained/Kronos-small/config.json` |
| 98,980,656 | `b082dfcbd8e8c142a725c8bbb99781802f38fec81210e13479effb32b3c3e020` | `pretrained/Kronos-small/model.safetensors` |
| 15,842,368 | `0e1d6a2445165d8d9358662341f17f58fb2879e28acfe471beeb6a3ba1a7419c` | `finetuned/…/tokenizer/best_model/model.safetensors` |
| 301 | `2366e7ccfec76cbc19cf3c4c1b9c5d901be336ca1e83f2d2292c9bff381b77a2` | `finetuned/…/tokenizer/best_model/config.json` |
| 352 | `ec40d6b5978fe1ed22e92abe5f9033b5147fc474209dc245df3b4fb8d4dfbf4c` | `finetuned/…/tokenizer/best_model/README.md` |
| 98,980,656 | `d252b114fa883755de1a3293248f5db1d072cd6be38341ce4b94cc56af3de830` | `finetuned/…/basemodel/best_model/model.safetensors` |
| 228 | `5e0f6a605d5f81b5c9b559fe5cf716a1acb041c744e6f41bd05b097b7a685396` | `finetuned/…/basemodel/best_model/config.json` |
| 352 | `ec40d6b5978fe1ed22e92abe5f9033b5147fc474209dc245df3b4fb8d4dfbf4c` | `finetuned/…/basemodel/best_model/README.md` |
| 14,809 | `26acd267ad9f0675eb12c3319303437fb21ae329b5827217c7c39c809ed86c23` | `finetuned/…/logs/tokenizer_training_rank_0.log` |
| 8,113 | `dcdb3308f6909119fd3e1b0bfdedae0a90a5cdb4b6017d5df8fec0f82966509b` | `finetuned/…/logs/basemodel_training_rank_0.log` |

**Every output file matches the recorded byte size exactly**, including both training logs.

### Checkpoint hashes — the difference is isolated to the two trained files

The DAG's `artifactHash` is **blake3**, not sha256; recomputing blake3 in the rebuilt tree
resolves what would otherwise be an unreconcilable discrepancy:

| recorded artifactHash | rebuilt blake3 | file |
|---|---|---|
| `edb2156ad72eec7a…` | `edb2156ad72eec7a…` **MATCH** | `pretrained/Kronos-Tokenizer-base/config.json` |
| `1c108eeef5847c68…` | `1c108eeef5847c68…` **MATCH** | `pretrained/Kronos-Tokenizer-base/model.safetensors` |
| `205cdf4f42b2ef77…` | `205cdf4f42b2ef77…` **MATCH** | `pretrained/Kronos-small/config.json` |
| `b5ccd595f89a9fc0…` | `b5ccd595f89a9fc0…` **MATCH** | `pretrained/Kronos-small/model.safetensors` |
| `63bbae228077c99f…` | `63bbae228077c99f…` **MATCH** | `finetune_csv/data/HK_ali_09988_kline_5min_all.csv` |
| `5ab2b14b2eea91d9…` | `d19de5b1e5e5f6ac…` differs | `finetuned/…/tokenizer/best_model/model.safetensors` |
| `1b8e14054d6d1990…` | `d3c46603b1c12a5f…` differs | `finetuned/…/basemodel/best_model/model.safetensors` |

Every **input** — both pre-trained checkpoints, both configs, and the shipped CSV — is
byte-identical to what the capture saw. The revision pinning in `repro/fetch_pretrained.py`
and the in-repo dataset both did their job exactly. Only the two **trained** checkpoints
differ, which is expected: GPU training here is not bit-deterministic, and the campaign
claims *reproduce*, not *replicate*.

## Metrics (recorded for completeness; not a pass criterion)

| metric | recorded | rebuild |
|---|---|---|
| predictor validation loss | 1.8362 | **1.8430** |

Computed by upstream's own code at the end of the epoch, as claimed. The point is that a
metric is produced, not that it matches.

## Notes for the record

- No missing dependency of any kind. Nothing was added to the venv to make the run proceed,
  and no interpreter was symlinked or aliased.
- No Python version mismatch was raised: uv provisioned the recorded 3.12.10 exactly.
- The published record was sufficient. Every fact needed to run this rebuild — DAG hash,
  roar version, wheel digest, hardware, and the honest caveat about the recorded torch —
  was already in `row.json` and `README.md`. Nothing had to be sourced from the capture
  agent's working directory.

## Certified by

Independent certification agent, 2026-08-12. Instance `i-0c756785c238a1f21`, terminated and
verified terminated after evidence collection.
