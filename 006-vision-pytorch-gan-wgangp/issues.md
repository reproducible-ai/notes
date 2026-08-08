# 006 — WGAN-GP / MNIST · upstream findings

> **Provenance of this file.** Unlike the rest of this row's notes, these findings
> are **not** a reconstruction. They are the operator's own contemporaneous
> observations, committed into the fork at the recorded commit `b4c63045` as
> [`implementations/wgan_gp/REPRODUCTION.md`](https://github.com/reproducible-ai/PyTorch-GAN/blob/b4c63045aead8024952f36cf7b664d8dcf1ee0c5/implementations/wgan_gp/REPRODUCTION.md),
> and therefore surviving the loss of the working directory. They are reproduced
> here faithfully, condensed but not reinterpreted. Anything added during
> reconstruction is marked.
>
> **None of these were "fixed."** This is a reproduction, not an improvement. Where
> the fork changed behaviour it is listed under "Modifications", not here.

All findings concern `eriklindernoren/PyTorch-GAN` @ `36d3c77e` (MIT, last upstream
commit January 2021), specifically `implementations/wgan_gp/`.

---

### 1. No checkpoint is ever written — **blocks reproduction outright**

After up to 200 epochs the trained generator and critic are discarded when the
process exits. `implementations/wgan_gp/` produces only PNG grids.

**Why it matters here:** there is no artifact whose lineage could be recorded, no
model to publish, and nothing to evaluate. A pipeline that emits no durable output
cannot be a reproducibility subject at all. This is the single finding that
required the largest change in the fork, and it is the one most worth carrying
upstream.

**Severity:** blocking. **Upstream-worthy:** yes.

---

### 2. `nn.BatchNorm1d(out_feat, 0.8)` passes `0.8` as `eps`, not `momentum`

`BatchNorm1d`'s signature is `(num_features, eps=1e-5, momentum=0.1, ...)`, so the
second positional argument is the **epsilon**. `0.8` is roughly five orders of
magnitude above the default epsilon and heavily damps the normalisation.
`momentum=0.8` is the far more plausible intent.

The same call appears across many implementations in the repository, so if it is a
mistake it is a repository-wide one.

**Severity:** correctness — silently changes the network's behaviour.
**Upstream-worthy:** yes.

---

### 3. `--n_cpu` is dead

Parsed and documented as "number of cpu threads to use during batch generation",
but the `DataLoader` is constructed without `num_workers`, so the value is never
used.

**Severity:** low — a misleading knob. **Upstream-worthy:** yes (trivial).

---

### 4. `--clip_value` is dead in this implementation

Weight clipping is the *WGAN* mechanism that WGAN-GP's gradient penalty replaces.
The flag is inherited from `implementations/wgan/` and has no effect here.

**Severity:** low, but conceptually confusing — it advertises the very mechanism
this variant exists to avoid. **Upstream-worthy:** yes.

---

### 5. `requirements.txt` is unpinned and effectively stale

`torch>=0.4.0`, plus bare `torchvision`, `numpy`, `scipy`, `pillow`, `urllib3`,
`scikit-image`. It admits every PyTorch release from 2018 to today, so it does not
describe an environment that can be rebuilt. It also lists dependencies this
implementation does not use.

**Severity:** medium — this is the reproducibility gap in its purest form. A
dependency file that resolves to anything pins nothing.
**Upstream-worthy:** yes.

*(Added during reconstruction, for contrast rather than as a finding: the record
this row published carries 45 fully-pinned distributions, all resolvable on PyPI.
See `commands.md`.)*

---

### 6. `torch.autograd.Variable` is used throughout

Deprecated since PyTorch 0.4. It still works as an alias for `Tensor` but is dead
weight.

**Severity:** cosmetic. **Upstream-worthy:** low priority.

---

### 7. The repository-level `.gitignore` contains `*.json`

Which silently ignores any metrics or config file written at the default paths.

**Severity:** medium and genuinely insidious — a metrics file appears to be written,
the run looks successful, and the file simply never reaches the repository. The fork
had to add an explicit rule for `metrics/` to work around it.
**Upstream-worthy:** yes.

---

### 8. The generator is updated using the critic's noise batch

In the `i % n_critic == 0` branch, `z` is reused from the discriminator step rather
than resampled.

**This is a defensible choice, not a bug** — but it is undocumented and differs from
the reference WGAN-GP algorithm. Recorded because a reader comparing this code to
the paper will notice the difference and should know it is deliberate-looking rather
than an artifact of the reproduction.

**Severity:** informational. **Upstream-worthy:** as a comment, yes.

---

## Modifications the fork made, and why

Listed for completeness — these are changes, not findings. Every one preserves
upstream behaviour when the new flag is omitted: running `python wgan_gp.py` with no
arguments does exactly what it did before. Full diff in
`patches/fork-vs-upstream.diff` (+489 / −4 across 11 files; the only modified
upstream file is `wgan_gp.py`, +46 / −4).

| # | change | driven by |
|---|---|---|
| 1 | `--checkpoint PATH` — saves both `state_dict`s plus the argparse config, `img_shape`, `lambda_gp` and the batch count. Default `""` = save nothing = upstream. | finding 1 |
| 2 | `--data_root` and `--sample_dir`, both defaulting to upstream's hard-coded literals. Upstream's paths were relative to the *process* working directory, so the script could only be launched from `implementations/wgan_gp/`. | packaging the pipeline |
| 3 | `os.makedirs("images")` moved below `parse_args()`. Upstream ran it at **import time** — before the options existed — which is precisely why the sample directory could not be configured. | enables 2 |
| 4 | `--seed`, default `-1` = unseeded = upstream. Upstream seeds nothing, so two runs of the same commit differ. The campaign run passes `--seed 42`. | determinism of the recipe |
| 5 | `prepare_data.py` added — downloads MNIST as its own step. | lineage correctness (see `commands.md`) |
| 6 | `eval_wgan_gp.py` added — loads the checkpoint and computes the metrics. `Generator`/`Discriminator` are **copied**, not imported, because upstream defines them at module scope beside the training loop and importing would run training. `strict=True` on `load_state_dict` so future drift fails loudly. | finding 1 |

**Zero lines of upstream's model definition or training loop were changed.** The
four `wgan_gp.py` deletions are the hard-coded `os.makedirs("images")`, the two
hard-coded `../../data/mnist` literals, and the hard-coded `"images/%d.png"` output
path — each replaced by the configurable equivalent.
