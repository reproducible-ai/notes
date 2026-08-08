# 003 · minGPT — `projects/adder`

**Verdict: REPRODUCED.** Difficulty: **easy (2/10)** — the easiest kind of row there is.

`karpathy/minGPT`'s `projects/adder` demo rebuilds from its published materials with
**zero changes to upstream source code**. A gpt-nano Transformer (0.09 M parameters)
trained from scratch to add two 2-digit numbers reached **99.2 % on the held-out test
split** in **195 seconds** on a single Tesla T4 (and 2 min 22 s on a 4-core CPU — this
row genuinely needs no GPU). Total compute spend: **$0.03** of reported job cost.

The whole model is three files (`mingpt/model.py`, `mingpt/trainer.py`, `mingpt/utils.py`)
plus a 190-line demo script. There is no dataset to download, no tokenizer to build, no
checkpoint to fetch, and no license or access gate: `AdditionDataset` synthesises all
10 000 possible 2-digit addition problems in-process from a hardcoded
`torch.Generator().manual_seed(1337)`. Data availability — the single most common
reason a rebuild dies — simply does not apply here.

Two real upstream defects were found, neither of them fatal:

1. **`setup.py` under-declares its dependencies.** It lists only `torch`, but
   `mingpt/utils.py` does `import numpy as np` at module scope. Follow the README
   literally (`pip install -e .` into a clean environment) and `import mingpt` raises
   `ModuleNotFoundError: No module named 'numpy'`. Upstream's own todo list admits it:
   *"i probably should have a requirements.txt file..."*.
2. **The demo has no stopping criterion.** `Trainer.get_default_config()` sets
   `max_iters = None` and `Trainer.run()`'s only termination branch is
   `if config.max_iters is not None`. As shipped, `python projects/adder/adder.py`
   **trains forever**. `projects/adder/readme.md` is two lines long and publishes no
   iteration count, no target accuracy, and no expected runtime, so there is nothing
   to reproduce *against* — the operator has to invent the stopping point. We chose
   `--trainer.max_iters=3000`, which empirically converges.

A third, smaller one: `setup_logging()` writes `out/adder/config.json` **before** the
model is constructed, so the "config log" records `n_layer: null, n_head: null,
n_embd: null, vocab_size: null, block_size: null`. The file that looks like the
run's configuration record does not contain the model's actual dimensions.

## What was rebuilt

| | |
|---|---|
| Upstream | [`karpathy/minGPT`](https://github.com/karpathy/minGPT) @ `37baab7` (default branch **`master`**, not `main`) |
| Fork | [`reproducible-ai/minGPT`](https://github.com/reproducible-ai/minGPT) @ `e2108219` |
| Demo | `projects/adder` — gpt-nano (3 layers, 3 heads, n_embd 48), vocab 10, block 6 |
| Command | `python -m projects.adder.adder --trainer.max_iters=3000 --trainer.num_workers=0` |
| Result | test 99.2 % (496/500), train 98.6 % (9365/9500); `model.pt` 358 971 B |
| Published | [`hf://reproducible-ai/mingpt`](https://huggingface.co/reproducible-ai/mingpt) |
| Lineage | [`c2ffb3ef…`](https://glaas.ai/dag/c2ffb3ef71e1f4dafd87e0fc95ef172addb0e4f9b7ebc490360dbf572d60d0cc) |

## Narrative

**Reading the materials.** minGPT is semi-archived (upstream's own note, Jan 2023) and
deliberately tiny. The adder project ships one script and a two-line readme. Within a
few minutes of reading `adder.py` and `trainer.py` it was clear that (a) the dataset is
synthetic and seeded, so there is no data-acquisition risk at all, and (b) the demo
never terminates on its own.

**The one structural obstacle: `mingpt` is not importable.** `adder.py` does
`from mingpt.model import GPT`, but running `python projects/adder/adder.py` puts
*`projects/adder/`* on `sys.path` — not the repo root — so the import fails. The README's
answer is `pip install -e .`. That works, but an editable self-install is a trap for
provenance capture: it is not a resolvable distribution, so it never appears in a
package freeze, and the recorded environment then claims a dependency the rebuild has
no way to install.

The fix needs no install at all. `python -m projects.adder.adder`, run from the repo
root, puts the **repo root** on `sys.path` (that is what `-m` does), so `mingpt`
resolves as a plain local package and `projects.adder.adder` resolves as a namespace
package. `__name__ == "__main__"` still holds, so the script's main block runs
unchanged. **One command-shape change, zero source edits, and the self-install
disappears entirely.**

**Bare-clone check.** From a fresh clone, in a venv containing only `torch==2.7.0`,
with `PYTHONPATH` unset, the command failed on `import numpy` — that is defect (1)
above, caught for real rather than theorised. Adding `numpy` alone made it run to
completion. No third package was needed. See `commands.md`.

**Capture.** One `treqs run`, four stages, 3 min 58 s wall clock end to end. The train
step recorded **43 pip pins**, all portable (`torch==2.7.0` with no `+cu128` local
version), jointly solvable by pip, and containing **no `mingpt` distribution** — the
self-install stayed out of the record, which was the whole point.

**On the train step recording zero inputs.** The captured DAG shows the train step with
`inputs: []`. That is *correct here*, not a tracer failure, and it was worth proving
rather than assuming. A control run under the identical roar build in the same repo
(`python -c "open('README.md').read()"`) recorded `README.md` as an input, so the tracer
plainly sees the repository; it excludes `.py` source because that is already pinned by
the recorded git commit. The adder demo reads **no data files at all** — its dataset is
generated in-process from a seeded RNG — so an empty input set is the complete and
honest answer. Any row whose workload does have file inputs should treat `inputs: []`
as a red flag; this one should not.

## Honest limits

- We claim **reproduce, not replicate**. The 99.2 % figure is what this run produced on
  a T4; the CPU run reached 99.4 %. Neither is compared against an upstream number
  because upstream publishes none.
- `max_iters=3000` is **our** choice, not upstream's. A different operator reading the
  same materials would have to invent their own, and would get a different checkpoint.
  This is the row's real reproducibility weakness and it is upstream's, not the tooling's.
- `--trainer.num_workers=0` (upstream default is 4) was set deliberately. It changes
  nothing about the maths; it keeps DataLoader worker processes out of the capture.
- The published `model.pt` is the best-scoring checkpoint seen during the run, not the
  final-iteration weights — that is upstream's `batch_end_callback` behaviour, and the
  score it is selected on is `train_score + test_score`, i.e. **selection touches the
  test split**. Fine for a demo; worth knowing before quoting the number.
