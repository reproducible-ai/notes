# Independent Tier-2 certification

An independent cold agent rebuilt DAG `357518abae1151de0ba348a507715a48c44688e705a3039aa49e293c989c095d` on a fresh NVIDIA RTX PRO 6000 Blackwell host. The certifier did not perform the capture and used only the published DAG, public fork, and public notes.

## Result

The exact certification command was:

```text
roar reproduce 357518abae1151de0ba348a507715a48c44688e705a3039aa49e293c989c095d --lineage --run --no-puts -y --step-timeout 21600
```

- Literal exit code: `0`
- Literal step count: `Steps run: 3/3`
- Run wall-clock: 8m29s (`2026-09-01T13:42:27Z` to `13:50:56Z`)
- Publish step: skipped by `--no-puts`, as required

Before GPU spend, the independent record gate passed: CLEAN 14/14, AI-BOM 100, all recorded URLs public, portable freeze, and valid row schema.

## Rebuilt outputs

| Output | Bytes | SHA-256 |
|---|---:|---|
| `rwkv-0.pth` | 382,223,128 | `ba42c5010b0c4f78a8282d96d808a2fe1cfc896c12e862f8c30cf1dfc8091be2` |
| `train_log.txt` | 2,883 | `e860af2b7921308f296b1e7b770e2e9eecdbbd4df12f8bf083ae0bf115e3c739` |
| `rwkv-init.pth` (intermediate) | 382,290,251 | `c267266dbf4526efcb2dba73885724542023cd9fded565c1416bad01b76440bb` |

Both published outputs were regenerated at exactly their recorded byte sizes. Their hashes are recorded above; checkpoint bytes and training-log text are not required to be identical across independent training runs.

## Environment and identity

- Hardware: 1× NVIDIA RTX PRO 6000 Blackwell Server Edition (`g7e.2xlarge`, compute capability 12.0)
- Image: `ami-0bd8f1bf63eb27e06`, us-east-2
- Rebuilt interpreter: row-local `.venv/bin/python`, Python 3.12.10
- PyTorch: 2.13.0+cu130; CUDA 13.0 available; architecture list includes `sm_120`
- Recorded manifest: 49/49 union pins exact, 0 missing, 0 mismatched
- Installed closure: 88 distributions, independently enumerated by `uv pip freeze` and `importlib.metadata`
- roar: 0.4.5, PyPI wheel SHA-256 `8dcc24d1ee03cb33922af815844ab3e750b3d5429267ed03e59ea1996f90c63a`
- All six installed tracer binaries matched the verified wheel byte for byte; the valid run used the eBPF tracer
- Host substrate had no `python` command before reproduction, and its workload interpreter could not import roar. The recorded `python` commands therefore resolved from the rebuilt row-local environment.

The valid cold host was `i-0de5a07e35c0423b6`. A preliminary cold substrate invocation was discarded before the valid run; it made no row-level finding. Approximate combined certification spend was $1.52, including both hosts and evidence collection.

Certifier identity: `/root/certify_row_018_blackwell`; model identity was not supplied at launch; Codex CLI 0.147.0.
