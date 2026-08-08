# 003 · minGPT `projects/adder` — obstacles

Upstream-repo findings only. Four issues; none blocked the rebuild.

---

## I-1 · `setup.py` under-declares dependencies — `import mingpt` fails on a clean install

**Severity:** real, upstream-worthy. **Blocked the rebuild?** No (only because our
recorded environment happened to contain numpy already).

**Symptom.** Follow the README's Library Installation section literally into a clean
environment and the package will not import:

```
$ .venv/bin/python -m pip install torch==2.7.0     # exactly what setup.py asks for
$ env -u PYTHONPATH .venv/bin/python -m projects.adder.adder --trainer.max_iters=1
torch/_subclasses/functional_tensor.py:276: UserWarning: Failed to initialize NumPy:
    No module named 'numpy'
Traceback (most recent call last):
  File "projects/adder/adder.py", line 13, in <module>
    from mingpt.model import GPT
  File "mingpt/model.py", line 17, in <module>
    from mingpt.utils import CfgNode as CN
  File "mingpt/utils.py", line 8, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
```

**Root cause.** `setup.py` declares `install_requires=['torch']`. `mingpt/utils.py`
imports `numpy` at module scope (used by `set_seed`). There is no `requirements.txt`.
Historically this was masked because `numpy` was a hard dependency of `torch`; modern
torch wheels do not pull it in, so the gap is now visible.

Upstream is aware in principle — `README.md` todos: *"i probably should have a
requirements.txt file..."*.

**Fix / workaround.** Install `numpy` alongside `torch`. A one-line `setup.py` change
fixes it properly; the prepared diff is in `patches/0001-declare-numpy.patch`
(**not submitted upstream** — this campaign does not open external PRs).

**Why it matters for reproducibility.** This is the class of defect that kills rebuilds
silently: the published dependency list is not the real dependency list, so anyone
resolving from the published metadata gets a broken environment. It was caught by the
bare-clone check (fresh clone + only-the-expected-pins venv + `PYTHONPATH` unset), which
took under a minute.

---

## I-2 · The demo has no stopping criterion and no published target metric

**Severity:** real, upstream-worthy. **Blocked the rebuild?** No, but it makes the row
un-*replicable* by construction.

**Symptom.** `python projects/adder/adder.py` trains indefinitely. It never exits.

**Root cause.** `Trainer.get_default_config()` sets `C.max_iters = None`, and the only
termination branch in `Trainer.run()` is:

```python
if config.max_iters is not None and self.iter_num >= config.max_iters:
    break
```

so with the shipped default the `while True:` loop has no exit. `projects/adder/readme.md`
is two lines (`### adder` / `Train a GPT model to add n-digit numbers`) and states no
iteration budget, no expected accuracy, and no expected runtime.

**Consequence.** Every reproducer must invent a stopping point, and two honest
reproducers will publish different checkpoints from identical code. There is no
published number to check a rebuild against.

**Fix / workaround.** We passed `--trainer.max_iters=3000`, chosen by measuring: the
model is ~7 % test-correct at iter 500, ~75 % at 1000, ~98 % at 2000 and ~99 % at 3000,
so 3000 is the knee. Recorded explicitly in the DAG command and stated in the published
artifact message so the choice is permanent public record rather than folklore.

**Upstream-worthy?** Yes — a default `max_iters` (or a documented one in the readme,
with the accuracy it reaches) would cost upstream one line and make the demo
checkable. Not submitted.

---

## I-3 · `mingpt` is not importable without an editable self-install

**Severity:** minor upstream ergonomics; significant for provenance capture.
**Blocked the rebuild?** No.

**Symptom.** `python projects/adder/adder.py` from the repo root:
`ModuleNotFoundError: No module named 'mingpt'`.

**Root cause.** Python puts the *script's directory* (`projects/adder/`) on `sys.path`,
not the current working directory. The repo root — where the `mingpt` package lives —
is never on the path. The README's only answer is `pip install -e .`.

**Fix (used here, no source edit):** run it as a module from the repo root instead:

```
python -m projects.adder.adder
```

`-m` puts the **repo root** on `sys.path`, so `mingpt` imports as a local package and
`projects.adder.adder` resolves as a PEP-420 namespace package. `__name__` is still
`"__main__"`, so the script's main block runs unchanged.

**Why we cared.** An editable install is not a resolvable distribution: it cannot appear
in a package freeze, so a recorded environment that depends on it can never be rebuilt
from that record. Sidestepping the install entirely — rather than installing and then
uninstalling — keeps the recorded environment honest by construction. Verified after
capture: the 43 recorded pins contain no `mingpt` distribution.

---

## I-4 · `config.json` is written before the model exists, so it records nulls

**Severity:** cosmetic but misleading. **Blocked the rebuild?** No.

**Symptom.** The run's own config log, `out/adder/config.json`, contains:

```json
"model": { "model_type": "gpt-nano", "n_layer": null, "n_head": null,
           "n_embd": null, "vocab_size": null, "block_size": null }
```

**Root cause.** In `adder.py`'s main block, `setup_logging(config)` is called at line 3
of the block — before `config.model.vocab_size` / `block_size` are assigned and before
`GPT(config.model)` expands `model_type='gpt-nano'` into `n_layer/n_head/n_embd`. The
serialised config is a snapshot of the config *before* resolution.

**Consequence.** The artifact that looks like the authoritative record of "what was
trained" does not contain the model's dimensions. Anyone reconstructing the architecture
from `config.json` alone gets nulls and must go read `model.py`'s lookup table instead.

**Fix.** Move the `setup_logging(config)` call after model construction (or re-dump).
Not submitted.

---

## Non-issues, recorded so they are not re-investigated

- **`args.txt` records an absolute path.** `setup_logging` writes `' '.join(sys.argv)`,
  and `sys.argv[0]` is the absolute path of `adder.py`. Machine-specific, but it is a
  log, not an input to anything.
- **`pin_memory=True` is hardcoded** in `Trainer.run()`, which emits a `UserWarning` on
  a CPU-only host. Harmless.
- **Checkpoint selection uses the test split.** `batch_end_callback` saves when
  `train_score + test_score` improves. Standard for a teaching demo; means the reported
  test number is mildly optimistic. Not a bug, but do not quote it as a clean held-out
  result.
- **Determinism is partial.** `set_seed(3407)` seeds python/numpy/torch, but the
  training sampler is `RandomSampler(..., replacement=True, num_samples=int(1e10))` and
  the run is not deterministic across devices. We claim *reproduce*, not *replicate*, so
  this is out of scope — but do not expect bit-identical weights.
