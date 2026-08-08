# Tier 2 — Certified reproduction · row 009 litgpt

**Reconstructed from the MMA ledger.** This row was certified *before* the rule requiring
cert evidence on a `certs/` branch existed, so the evidence lived only in the campaign
ledger. Recorded here for durability. The certification itself is unchanged.

| | |
|---|---|
| DAG (attributed) | `314f1eb9acbf26076c12b6893c1efc8e83f1b36f70034a7d8a0ceeb496b51403` |
| roar build | `0.4.4.dev0` @ `c5c553b` (P0-14 workaround applied) |
| Result | **EXIT=0 · 4/4 steps** |
| Environment | **62/62 pins exact** against the recorded freeze |
| Artefact | `lit_model.pth` — 168,905,247 B, stat'd |
| Metric | `val loss 9.738` — identical across every environment tried |
| Cost | ~$0.44 |

## Caveats recorded honestly

- **Captured pre-#274.** roar's freeze pass matched only `site-packages`, so anything under
  the AMI's system `dist-packages` was dropped from the record (P0-18). The
  imports-vs-freeze audit found **no detected miss** on this row — but "no detected miss"
  is not "verified complete"; the audit only finds gaps it knows to look for.
- 62/62 exact means the *recorded* pins all resolved and installed. It says nothing about
  packages that never reached the record in the first place.
