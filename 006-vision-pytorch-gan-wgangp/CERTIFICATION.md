# Tier 2 — Certified reproduction · row 006 WGAN-GP / MNIST

> **Reconstructed from the campaign ledger.** The certifying operator's working
> directory was cleaned up before the rule requiring cert evidence on a `certs/`
> branch existed, so this evidence survived only as the ledger's copy of the
> certifier's report. It is recorded here for durability. **The certification
> itself is unchanged** — nothing has been re-run, and nothing below is inferred
> from the ledger entry beyond what it states. Where the ledger and the published
> DAG disagree, both figures are given.

| | |
|---|---|
| DAG (attributed) | `e812e9815b0934fa19a21be4f57c33349a462b5dee108b0fc9692f57b8f04f3a` |
| HF artefact | `hf://reproducible-ai/pytorch-gan-wgangp` (**not** `wgan-gp`) |
| roar build | `0.4.4.dev0` @ `c5c553b` |
| **Result** | **`EXIT=0` · 3/3 steps** |
| Environment | **45/45 recorded pins present at exact recorded versions** |
| Cost | ~$0.10 |

## Command

```bash
roar reproduce e812e9815b0934fa19a21be4f57c33349a462b5dee108b0fc9692f57b8f04f3a \
     --lineage --run --no-puts
```

The DAG has four jobs; the fourth is the `roar put`, which `--no-puts` excludes by
design. **3/3 is therefore the whole reproducible pipeline**, not a partial run.

## Artefacts regenerated (stat'd on the certification host)

| bytes at rebuild | bytes at capture | path | |
|---|---|---|---|
| 8,197,921 | 8,197,921 | `out/wgangp.pt` | ← the published artefact — **exact match** |
| 632 | **633** | `metrics/metrics.json` | **differs by one byte — see below** |
| — | 8 PNGs, 20,287–48,008 B | `samples/*.png` | recorded outputs, **not stat'd at rebuild** |

Byte-identical output is **not** claimed for this row. The checkpoint matching at
8,197,921 B is consistent with an identically-shaped model; it is not proof of
identical weights, and GPU training is not bit-deterministic even at a fixed seed.
We claim *reproduce*, not *replicate*.

### The one-byte difference, stated plainly

`metrics.json` is recorded as **633 B** in the capture and reported as **632 B** in
the certification evidence. This is **not reconciled**, and it is worth being
precise about why:

- The certification host is long gone and the rebuilt file's *content* was not
  preserved — only its size was stat'd. There is nothing left to diff.
- The file holds floating-point metrics computed on a non-deterministically-trained
  checkpoint. A one-character difference in the decimal representation of any single
  value would produce exactly this. That is a **plausible explanation, not a
  verification**, and it is offered as the former.
- It could equally be a transcription slip in the ledger entry. Neither possibility
  can be distinguished from the surviving evidence.

Nothing about the certification turns on it: the step exited 0 and the published
artefact matched exactly. But it is a one-byte discrepancy between two records that
should agree, and it is recorded rather than smoothed over.

### `truncated_run: true` is expected

`metrics.json` self-tags `truncated_run: true`. That is the evaluation script
correctly labelling a 3-epoch checkpoint against an upstream default of 200. It is
**not a defect and not a failure signal**, and a reader should not treat it as one.

## Environment verification

All **45** recorded pip pins were present in the rebuilt environment at their exact
recorded versions — 0 missing, 0 mismatched. All three traced steps then ran to exit
0 with no `ModuleNotFoundError`, which is the part that matters: it shows the
recorded pin set is *sufficient* for this row's actual import graph, not merely that
it *resolves*.

45/45 exact means every **recorded** pin resolved and installed. It says nothing
about packages that never reached the record in the first place — see the caveats.

### Interpreter and package resolution

The recorded interpreter is **3.12.10 CPython**, and the reproduce environment
matched it **exactly** — no `PYTHON VERSION MISMATCH` warning was emitted.

The campaign's standing concern on this substrate (tracked internally as P0-14) is
that a reproduce venv might resolve packages from a host package directory rather
than from itself, which would mean the certification measured the machine image
instead of the record. **It did not manifest on this row.** The reproduce venv's
`sys.path` carried **no host `dist-packages`**, and `torch` loaded from inside the
venv. The certification therefore exercised the recorded environment.

## Caveats recorded honestly

- **The capture predates roar #274.** The record's own metadata gives the capturing
  build as **roar `0.4.3`** (`roar_version: 0.4.3` on every traced step, and
  `roar-cli==0.4.3` in the freeze itself). The *certification* ran a later build,
  `0.4.4.dev0` @ `c5c553b`. Both predate #274, a fix to how roar enumerates
  installed packages when it writes the freeze, so this record may be missing
  packages that a post-#274 capture would have caught. The mechanism behind that fix
  is still under investigation upstream and is deliberately not asserted here as
  settled.
- **The imports-vs-freeze audit rates this row weak, not clean.** No *decisive*
  miss: everything `import torch`/`import torchvision` demonstrably loads is in the
  45. Three packages are absent that often accompany a torch install — `requests`,
  `urllib3`, `charset-normalizer`. This workload plausibly never imports any of
  them: no networking in the training loop, and torchvision's MNIST download goes
  through the standard library's `urllib`, not `requests`. That makes the signal
  **weak evidence, not a proven defect**. Equally, **"no detected miss" is never
  "verified complete"** — the audit finds only the gaps it knows to look for.
- **The successful cold rebuild is the stronger evidence here**, and it cuts the
  other way: the recorded set installed and ran all three steps to exit 0 on a host
  that had never seen the row. That is a positive demonstration of sufficiency that
  no static audit can provide.
- **Eight recorded outputs were not stat'd.** The `samples/*.png` grids are output
  edges of step 2 in the capture and do not appear in the certifier's stat list.
  They are not the published artefact; their absence is a gap in the evidence, not a
  known discrepancy.
- **Cost is the ledger's figure (~$0.10)**, not a metered invoice line.
