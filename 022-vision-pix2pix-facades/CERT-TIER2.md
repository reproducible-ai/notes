# Tier-2 cold certification attempt

Date: 2026-08-28  
DAG: `14df351c56d65be8181299f225e5c266f35e6aded43dc8068b5f0e2e76ac622b`  
Result: **FAIL** (published input unavailable)

The independent cold rebuild ran:

```text
roar reproduce 14df351c56d65be8181299f225e5c266f35e6aded43dc8068b5f0e2e76ac622b --lineage --run --no-puts -y --step-timeout 21600
```

It returned literal exit code `1` with `Steps run: 1/2`.

The first recorded command tried the published CMP Facades archive endpoint 20 times. Every connection timed out and the archive remained at zero bytes. The download script nevertheless returned success, so the rebuild continued to training without a dataset. Training failed before reading its first sample:

```text
ValueError: num_samples should be a positive integer value, but got num_samples=0
```

Neither recorded model output was regenerated:

- `checkpoints/facades_pix2pix/latest_net_G.pth` — absent
- `checkpoints/facades_pix2pix/latest_net_D.pth` — absent

This attempt does not establish that the model recipe or recorded dependency set fails. It establishes that the published input could not be retrieved during the cold attempt. The row remains a Tier-1 Reproducible record and is not a Certified reproduction.

## Environment evidence

- Hardware: one NVIDIA T4 (`g4dn.xlarge`) in `us-east-2`
- Cold-run wall clock: 48m39s
- Estimated run spend: $0.43 at $0.526/hour
- Recorded pin union: 25/25 exact; no missing or mismatched pins
- Installed closure: 48 distributions; `uv pip freeze` and `importlib.metadata` agreed
- Executed interpreter: rebuilt venv Python 3.12.10
- Host packages were absent from the venv's `sys.path`
- The cold host was terminated after evidence collection

The certifier was independent of the capture operator and did not modify or recapture the row.
