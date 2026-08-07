# 003 · minGPT `projects/adder` — cost

Budget: NTE $10. **Actual: $0.03 reported job cost** (~$0.25 upper bound on the
underlying instance time). This is the cheapest kind of row in the campaign.

## Attempts

| # | What | Target | Wall clock | Reported cost | Outcome |
|---|------|--------|-----------:|--------------:|---------|
| 0 | Local bare-clone check + iteration sweep (3000 iters, CPU) | control host, 4 vCPU | ~5 min | $0.00 | Found the undeclared `numpy` dependency; fixed the iteration budget at 3000 |
| 1 | First capture | `reproai-g4dn-plaintorch-a` (g4dn.xlarge, Tesla T4) | 3 min 40 s | $0.00 | **FAILED** in `setup`, before any training — operator error, see below |
| 2 | Capture | same (agent still warm) | 3 min 58 s | $0.03 | **COMPLETED** — 99.2 % test, artifact published, all four gates green |

**Total reported job cost: $0.03.**

## Attempt 1 — what failed

Not a model problem and not a substrate problem: the setup stage downloaded a wheel to
a filename that discarded its PEP-427 metadata, and pip refused it before the training
ever started.

```
ERROR: Invalid wheel filename (wrong number of parts): 'roar_cli'
```

pip parses the *filename* for name/version/abi/platform, so `-o /tmp/roar_cli.whl`
is rejected outright. Downloading to the canonical
`roar_cli-<version>-<pytag>-<abi>-<platform>.whl` fixed it. One-line change, one
re-run, zero training compute wasted — the stage failed fast and cost nothing.

## Instance time

Reported job cost counts task execution. The underlying on-demand instance also carries
boot and a 15-minute idle timeout. Both attempts ran on one warm instance across roughly
15:14–15:24 UTC, so the true EC2 cost is bounded above by ~25 min of g4dn.xlarge
(~$0.526/hr) ≈ **$0.22**. Either way, an order of magnitude inside budget.

## Sizing note

The row does **not** need a GPU. Measured locally: 3000 iterations in **2 min 22 s** on
4 CPU cores, reaching 99.4 % test accuracy — slightly *better* than the T4 run's 99.2 %,
which is run-to-run variance, not a hardware effect. A g4dn.xlarge was used only because
it is the smallest target available under this org; a CPU instance would be cheaper
still and would change nothing about the record.

The dominant cost of this row is instance boot and idle timeout, not compute. There is
no dataset download, no checkpoint fetch, and the model is 0.09 M parameters.
