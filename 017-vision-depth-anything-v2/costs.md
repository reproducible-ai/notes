# Costs — Depth Anything V2 (metric depth)

Instance: **g6e.xlarge** (1x NVIDIA L40S), us-east-2, on-demand **$1.861/hr**.
One host, `i-0a26107cfd9623fd9`, launched 19:59:02 UTC, terminated 20:17 UTC on
2026-08-11 — **~18.5 minutes billed ≈ $0.57 total for the row**, covering three launches.

## Attempts

| # | job | wall | outcome | cost |
|---|---|---|---|---|
| 1 | `1d5dbd71` | 20:01:53 → 20:02:56 (63 s) | aborted in environment setup, before any training | $0.04 |
| 2 | `24adfb5a` | 20:05:34 → 20:10:58 (5m24s) | training completed and the checkpoint was written; a bug in my own stage script killed the stage immediately afterwards, so the artifact was never labelled or published | $0.16 |
| 3 | `42d36374` | 20:13:03 → 20:14:31 (1m29s) | **recorded run** — all six stages, artifact published | $0.03 |

Costs in the table are the control plane's own per-job estimates and total $0.23; the
billed figure is the instance lifetime, $0.57, because a single host served all three
launches and was not idle-terminated between them. **$0.57 is the honest number for this
row.**

Attempt 2 is the interesting one for anyone reading these numbers: it is where the
*cold* training cost was measured (204 s for the training step on a freshly booted GPU),
and attempt 3 is where the same step took 13 s on the same, now-warm host.

## Per-step timings — the recorded run

Measured during the run, not reconstructed.

| step | traced | stage wall | notes |
|---|---|---|---|
| `setup` | — | 15 s | 46 s on the cold host; installs + capture tool |
| `fetch_weights` | 4.9 s | 6 s | 99.2 MB encoder download, 3.7 s of it transfer |
| `prepare_data` | 40.3 s | 42 s | 160 files / 19.6 MB by HTTP range request |
| `train` | 11.4 s | 13 s | 204 s on a cold host — see below |
| `label` | — | 1 s | |
| `publish` | — | 7 s | 297 MB checkpoint upload |

Inside the 13 s training step: 4.5 s to build the datasets, the model, the process group
and load the encoder; 2.2 s for iteration 0 (includes one-off cuDNN autotuning); 2.5 s for
the remaining 15 iterations plus the 16-frame evaluation; the balance is the checkpoint
write and process teardown.

## Fixed vs variable

- **Fixed, per run: ~6.2 min ≈ $0.19.** Instance boot + setup (~4.0 min), encoder download
  (4.9 s), dataset slice (40.3 s), first-CUDA-context and kernel warm-up (~110 s on a cold
  host), checkpoint upload (7 s).
- **Variable: $0.0013.** The epoch itself — 64 training frames (16 iterations at batch 4)
  plus 16 validation frames in 4.63 s, of which ~2.0 s is one-off autotuning, i.e.
  **~0.0325 s per frame**.

The ratio is the point: **99.3% of this record's cost is fixed**. Multiplying the headline
wall clock by the truncation factor would overstate a full run by two orders of magnitude.

## Full-run estimate — $135, and what it excludes

Upstream's `dist_train.sh` is 120 epochs over 59,543 training frames, evaluating 7,386 at
each epoch. At the measured 0.0325 s/frame:

```
66,929 frames/epoch x 0.0325 s = 2,175 s  = 36.3 min/epoch
36.3 min x 120 epochs           = 72.5 GPU-hours
72.5 h x $1.861/h               = $135
```

Two exclusions, stated rather than guessed:

1. **Dataset acquisition.** This row moved 19.6 MB out of two 2.2 GB archives. The full
   split spans 411 scene archives, on the order of 900 GB. Nothing measured here supports
   pricing that, and the range-request trick does not scale to whole scenes.
2. **Upstream's actual configuration.** `dist_train.sh` trains ViT-L across 8 GPUs. The
   $135 above is for the ViT-S single-GPU configuration that was actually measured. A
   ViT-L run is a materially larger job and this row has no measurement of it.

If you want the cheap version of this row: it fits in **5.2 GB of GPU memory**, so a
$0.526/hr T4 would have run it for roughly a third of the price. The L40S was used only
because it was the free target at the time.
