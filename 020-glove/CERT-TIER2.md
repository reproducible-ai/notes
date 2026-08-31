# Independent Tier-2 certification

An independent cold agent rebuilt DAG `5d5c04ca31854eb2678552dcf24f96e39d77449513643e7e0a2e3ee4f6399673` from the public record and fork.

The exact command was:

```text
roar reproduce 5d5c04ca31854eb2678552dcf24f96e39d77449513643e7e0a2e3ee4f6399673 --lineage --run --no-puts -y --step-timeout 21600
```

It exited `0` and reported `Steps run: 8/8`. All eight run steps independently reported success. The publish step was intentionally suppressed by `--no-puts`.

The reconstructed environment used Python 3.12.10. Its complete recorded pip union is `numpy==1.26.4`; both `uv pip freeze` and `importlib.metadata` independently enumerated exactly that one distribution, with nothing missing or mismatched. The row-local virtual environment supplied both `python` and `python3`, and NumPy loaded from that environment.

The certifier verified roar-cli 0.4.5 from its sha256-identified PyPI wheel (`8dcc24d1ee03cb33922af815844ab3e750b3d5429267ed03e59ea1996f90c63a`). Each of the six installed tracer binaries matched the verified wheel byte for byte.

## Regenerated outputs

| output | bytes | sha256 |
|---|---:|---|
| `outputs/evaluation.txt` | 923 | `7056d3779f0287777148198489eb94ec876f9ec8b7a1b743dc99b7c88be10371` |
| `outputs/glove-text8.tar.gz` | 70,171,487 | `063e238a37c9a3455fe53551c27dd9487b0f38b379ef3de4623bcf75a8431e0f` |
| `outputs/vectors.bin` | 58,172,640 | `88a57a548426eabee8361053f5e41b1725e926f06dbbf4ac7726e269f8845934` |
| `outputs/vectors.txt` | 34,421,413 | `74dc56430fb7466107dd8b995c9a3ba5b7485efbfc29118f639946c82f5c67f4` |

As positive controls, the archive passed an integrity read and contains the two vector files, evaluation, and vocabulary. The rebuilt evaluation computed 22.58% total analogy accuracy. Metric equality is not part of the reproduction claim.

Certification ran on one NVIDIA Tesla T4 (`g4dn.xlarge`) in `us-east-2`. The valid reproduction took approximately ten minutes. Combined certification compute, including a discarded preliminary invocation and evidence collection, is estimated at $0.75. The preliminary invocation was not used for any certification conclusion.

Certifier identity: `/root/certify_row_020`; exact configured model and harness version were not supplied and are recorded as unavailable rather than inferred. Harness: Codex.
