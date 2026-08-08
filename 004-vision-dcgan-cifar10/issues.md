# 004 — DCGAN / CIFAR-10 · upstream findings

> ## ⚠️ The operator's issues list for this row does not exist.
>
> It was lost with the working directory, before the campaign adopted the
> push-to-branch rule. **This file is therefore not the operator's findings** — it
> is the much smaller set of observations that can be derived from evidence that
> survives: the published DAG, and the fork's diff against upstream.
>
> Row 006 is the useful contrast: that operator committed their findings *into the
> fork*, so eight upstream observations survived intact. Nothing equivalent exists
> here. **Whatever this row's operator noticed and did not commit is simply gone**,
> and no attempt has been made to guess at it. Read the absence of a finding below
> as "not recoverable", not as "nothing was there."
>
> Each item below cites the specific artifact it is derived from.

---

### 1. The repository directory-ignores its output paths — a cold rebuild has nowhere to write

**Derived from:** the fork's `.gitignore` diff (+12 lines, `patches/fork-vs-upstream.diff`).

Upstream's `.gitignore` ignores output locations as **directories**. A
directory-ignore does not survive `git clone`: the directory is absent from a fresh
checkout entirely. The consequences for reproduction are concrete —

- the run either fails to write, or writes somewhere untracked;
- outputs that land outside a tracked path never become lineage edges, so the
  provenance record silently loses the artifacts it exists to record.

The fix is to ignore *contents* while committing a placeholder, so the directory
exists in a fresh clone:

```gitignore
cifar10-data/*
!cifar10-data/.gitkeep
out/*
!out/.gitkeep
```

**Severity:** medium, and insidious — the failure is silent and looks like a tracer
problem rather than a repository-layout problem. **Upstream-worthy:** yes; this is a
general pattern across example repositories, not specific to `dcgan/`.

---

### 2. The CIFAR-10 source is throttled to ~114 kB/s, and it dominates the run

**Derived from:** the DAG's own step timings and artifact sizes.

Step 1 downloads 170,498,071 B from `cs.toronto.edu` in 1,497.17 s — an average of
**~114 kB/s sustained**. The campaign ledger records the observed instantaneous rate
as a steady ~110–128 kB/s throughout, i.e. **throttling, not a stall**.

That single download is **94% of this row's traced wall clock** (24 m 57 s against
1 m 42 s of actual training), and the GPU is idle for all of it (`gpu_used: false`
on the step record).

Two practical consequences:

- Anyone rebuilding this row should expect to wait ~25 minutes on step 1 and should
  **not** kill it as hung.
- The row pays for a GPU to wait on a slow HTTP server. Mirroring CIFAR-10 near the
  compute would cut the cost by roughly an order of magnitude without changing the
  recipe or the result.

**Severity:** cost and operator-experience, not correctness.
**Upstream-worthy:** not really — this is the dataset host's behaviour, not
`pytorch/examples`'.

---

### 3. External data is tracked but the remote is not pinned

**Derived from:** the DAG's input/output edges on step 1.

CIFAR-10 is fetched inside a traced step, so the downloaded bytes *are* recorded as
artifacts with their hashes. But the **remote** is not pinned: nothing in the record
constrains what `cs.toronto.edu` serves. If those bytes ever change, a rebuild
trains on different data.

The recorded hashes are what would *detect* that after the fact. Nothing *prevents*
it. This is a general property of any recipe that downloads its dataset at run time,
and it is worth stating plainly rather than letting a green record imply more than
it does.

**Severity:** informational, but it bounds what "reproducible" means for this row.

---

### 4. Upstream seeds from `random.randint` when `--manualSeed` is unset

**Derived from:** `dcgan/main.py` at the recorded commit (unmodified upstream code).

```python
if opt.manualSeed is None:
    opt.manualSeed = random.randint(1, 10000)
```

Two runs of the same commit with the same flags therefore differ. The recorded
recipe passes `--manualSeed 42` so that it is a recipe rather than a sample. This is
a reasonable default for an *example*, but it means the published invocation in the
README is not by itself reproducible.

**Severity:** low. **Upstream-worthy:** arguably not — it is defensible for a demo.

---

## What is NOT claimed here

- **No difficulty rating.** The published scale is an operator judgement and no
  operator judgement survives for this row.
- **No account of obstacles hit during capture.** Three certification attempts
  preceded the successful one and the ledger records all three as substrate
  failures rather than row defects — but the substrate in question is the
  campaign's own tooling, not `pytorch/examples`, so it is not an upstream finding
  and is not detailed in these public notes.
- **No claim that `dcgan/main.py` is free of other issues.** It was not audited; it
  was run, unmodified, and it worked. The fork changed **zero Python lines** (see
  `patches/fork-vs-upstream.diff`), which is a statement about what this
  reproduction needed, not a statement about the code's quality.
