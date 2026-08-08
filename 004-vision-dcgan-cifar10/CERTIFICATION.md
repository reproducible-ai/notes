# Tier 2 — Certified reproduction · row 004 DCGAN / CIFAR-10

> **Reconstructed from the campaign ledger.** The certifying operator's working
> directory was cleaned up before the rule requiring cert evidence on a `certs/`
> branch existed, so this evidence survived only as the ledger's copy of the
> certifier's report. It is recorded here for durability. **The certification
> itself is unchanged** — nothing has been re-run, and nothing below is inferred
> from the ledger entry beyond what it states. Where the ledger and the published
> DAG disagree, both figures are given.

| | |
|---|---|
| DAG (attributed) | `3a8ff4c4c89b4cf796fa568b773e4d482fe1fde848b8baf1805ce6a47b800ba0` |
| HF artefact | `hf://reproducible-ai/dcgan` |
| roar build | `0.4.4.dev0` @ `c5c553b` |
| **Result** | **exit 0 · 2/2 steps** |
| Exit-code source | roar's own job DB (not a parsed banner) |
| Environment | **45/45 recorded pins present at exact recorded versions** |
| Cost | ~$0.41 |

## Command

```bash
roar reproduce 3a8ff4c4c89b4cf796fa568b773e4d482fe1fde848b8baf1805ce6a47b800ba0 \
     --lineage --run --no-puts
```

The DAG has three jobs; the third is the `roar put`, which `--no-puts` excludes by
design. **2/2 is therefore the whole reproducible pipeline**, not a partial run.

## Artefacts regenerated (stat'd on the certification host)

| bytes at rebuild | bytes at capture | path | |
|---|---|---|---|
| 14,323,315 | 14,323,315 | `out/netG_epoch_0.pth` | ← the published artefact — **exact match** |
| 379,915 | 379,915 | `out/real_samples.png` | **exact match** |
| 573,413 | **546,896** | `out/fake_samples_epoch_000.png` | **differs — see below** |
| — | 11,076,841 | `out/netD_epoch_0.pth` | recorded output, **not stat'd at rebuild** |

### The one file that differs, stated plainly

`fake_samples_epoch_000.png` is 573,413 B on the rebuild against 546,896 B in the
capture record — a 4.8% difference. This is **not** evidence of a broken
reproduction, and it is **not** being explained away:

- It is a PNG of *generated* images. Its byte size is the size of the compressed
  pixel data, so it varies with whatever the generator actually produced.
- GPU training is not bit-deterministic even at a fixed seed, so the generator's
  weights after 782 iterations are not expected to be identical run-to-run.
- Consistently, the two files whose sizes *are* content-independent match exactly:
  `netG_epoch_0.pth` is a fixed-shape state dict, and `real_samples.png` is a grid
  of *dataset* images selected deterministically by the fixed seed.

**Byte-identical output is not claimed and was not observed.** This row claims
*reproduce*, not *replicate*. The size agreement on the published artefact is
consistent with an identically-shaped model, not proof of identical weights.

## Environment verification

All **45** recorded pip pins were present in the rebuilt environment at their
exact recorded versions — 0 missing, 0 mismatched. Both traced steps then ran to
exit 0 with no `ModuleNotFoundError`, which is the part that matters: it shows the
recorded pin set is *sufficient* for this row's actual import graph, not merely
that it *resolves*.

45/45 exact means every **recorded** pin resolved and installed. It says nothing
about packages that never reached the record in the first place — see the caveats.

## What this row settled: the bare-`python` question

Every step in this campaign's DAGs is recorded as `python …`, and for a while it
was an open question whether `roar reproduce` actually activates the virtual
environment it provisions, or whether steps were quietly running against whatever
interpreter the host image happened to carry. If the latter, every certification
would be measuring the AMI rather than the record.

**This row is the direct evidence that it does activate.** The certification host
had **no bare `python` on its system PATH at all**. Step 2's recorded command is
literally `python dcgan/main.py …`. It ran, and it exited 0. A command that cannot
resolve without the venv on PATH did resolve — so the uv-provisioned venv was
demonstrably active for the workload. Nothing was symlinked to fake it.

## Attempt history

This was the **first successful certification of this row after three inconclusive
attempts**. Per the ledger, **all three were substrate failures, not row defects**
— failures of the certification host and toolchain rather than of the record under
test. The certification run reported here applied the campaign's standing
workaround for the then-current substrate defect (tracked internally as P0-14).

The specific failure modes of those three attempts belong to the campaign's
internal tooling and are not upstream-repo findings, so they are not detailed in
these public notes.

## Caveats recorded honestly

- **The capture predates roar #274.** The record's own metadata gives the capturing
  build as **roar `0.4.3`** (`roar_version: 0.4.3` on every traced step, and
  `roar-cli==0.4.3` in the freeze itself). The *certification* ran a later build,
  `0.4.4.dev0` @ `c5c553b`. Both predate #274, a fix to how roar enumerates
  installed packages when it writes the freeze, so this record may be missing
  packages that a post-#274 capture would have caught. The mechanism behind that
  fix is still under investigation upstream and is deliberately not asserted here
  as settled.
- **The imports-vs-freeze audit rates this row weak, not clean.** No *decisive*
  miss: everything `import torch`/`import torchvision` demonstrably loads is in the
  45. Three packages are absent that often accompany a torch install —
  `requests`, `urllib3`, `charset-normalizer`. This workload plausibly never
  imports any of them: no networking in the training loop, and torchvision's
  CIFAR-10 download goes through the standard library's `urllib`, not `requests`.
  That makes the signal **weak evidence, not a proven defect**. Equally, **"no
  detected miss" is never "verified complete"** — the audit finds only the gaps it
  knows to look for.
- **The successful cold rebuild is the stronger evidence here**, and it cuts the
  other way: the recorded set installed and ran the pipeline to exit 0 on a host
  that had never seen the row. That is a positive demonstration of sufficiency
  that no static audit can provide.
- **One recorded output was not stat'd.** `netD_epoch_0.pth` is an output edge of
  step 2 in the capture and does not appear in the certifier's stat list. It is
  not the published artefact and its absence from the list is a gap in the
  evidence, not a known discrepancy.
- **Cost is the ledger's figure (~$0.41)**, not a metered invoice line.
