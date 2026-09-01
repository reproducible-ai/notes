# Independent Tier-2 certification

An independent cold agent certified DAG `0bc12b45d58b9d1657f3d39f770ae43659612cfdabc55be6e138af3358924d01` on 2026-09-01. The record passed Clean-DAG 14/14, AI-BOM 100/100, public-URL, portable-freeze, and canonical schema-v2 gates before compute was launched.

## Result

- Command: `roar reproduce 0bc12b45d58b9d1657f3d39f770ae43659612cfdabc55be6e138af3358924d01 --lineage --run --no-puts -y --step-timeout 21600`
- Literal exit code: `0`
- Literal step count: `Steps run: 3/3`
- No `ModuleNotFoundError` or Python-version mismatch appeared.
- The valid reproduce took approximately 11 minutes; host lifetime was approximately 32 minutes including bootstrap, an invalidated apparatus attempt, the corrected run, and evidence collection.
- Estimated g4dn.xlarge compute cost: $0.28.

The first apparatus attempt used a build inferred from a mislabeled historical log rather than the version in the public DAG metadata. It is explicitly invalidated and carries no certification conclusion. The agent then installed the recorded 0.4.5 release and reran the full reproduction from a new clean working directory; only that corrected run supports this result.

## Harness identity

- `roar, version 0.4.5`
- Linux x86_64 wheel SHA-256: `8dcc24d1ee03cb33922af815844ab3e750b3d5429267ed03e59ea1996f90c63a`
- All six tracer binaries extracted from that verified wheel matched their installed copies byte-for-byte.
- Host: `i-09f24827a2d3a1d20` (`cert-row011-fast-neural-style`), one Tesla T4 on g4dn.xlarge, AMI `ami-0f07f1a0b382b48f7` in us-east-2.
- Self-shutdown ceiling: 33m44s from launch, keeping maximum estimated spend below the $0.30 NTE.

Before the run the host had no `python` executable on PATH; its `python3` was `/usr/bin/python3` at Python 3.10.12. The recorded steps used `/tmp/cert-011-v045/reproduce/examples/.venv/bin/python` at Python 3.12.10. Inside that environment PyTorch 2.7.0 (`2.7.0+cu126` runtime) reported CUDA available.

## Dependency manifest

The recorded union contains 10 pinned packages. All 10 were installed at their exact recorded versions; none was missing or mismatched. The rebuilt environment contained 28 distributions after transitive dependencies. `uv pip freeze` enumerated all 28 and `importlib.metadata` independently confirmed 28 distributions.

## Regenerated outputs

| Path | Bytes | SHA-256 |
|---|---:|---|
| `fast_neural_style/out-ckpt/ckpt_epoch_0_batch_id_2368.pth` | 6,739,701 | `a41b6b1b5f86c87d83e7088da1c3b19d1523ac038339becbf464d3de71789108` |
| `fast_neural_style/out-model/epoch_1_2026-09-01_17-46-02_100000.0_10000000000.0.model` | 6,741,397 | `3e159add916234937777e4ae3e1841ce95e11b0e9c4254b41475aac7e77e54af` |
| `fast_neural_style/out-stylized/amber-mosaic.jpg` | 373,663 | `8ca5d31b64a450549d53adb08a86e12cca1da75c485a10167c17fba2cfae3e62` |

The complete valid-run log was copied off-host before termination. Its uncompressed SHA-256 is `4490b650ecfd5ace5b69a90c1f833c19faabd97396246c3e600908fe52cc41ae`.

## Certifier identity

- Agent: `/root/certify_row_011`
- Model: unavailable; the exact configured model was not supplied at launch.
- Harness: Codex 0.147.0.
- This agent did not capture the row and used only the supplied row name, full DAG hash, and public evidence.
