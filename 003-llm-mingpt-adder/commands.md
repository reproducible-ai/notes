# 003 · minGPT `projects/adder` — the recipe

Everything below was actually run. Paths are the operator's working path.

---

## 0. Facts to establish before spending anything

```bash
gh repo view reproducible-ai/minGPT --json defaultBranchRef
# => {"defaultBranchRef":{"name":"master"}}     <-- master, NOT main
```

minGPT's default branch is **`master`**. Anything that silently assumes `main` will
point at a branch that does not exist.

---

## 1. Bare-clone check (do this first — it costs under a minute)

Fresh clone, scratch venv containing **only** the pins the record is expected to carry,
`PYTHONPATH` unset. This is what catches a dependency the published metadata does not
declare.

```bash
git clone https://github.com/reproducible-ai/minGPT.git bareclone && cd bareclone
uv venv --python 3.12 .bcvenv
uv pip install --python .bcvenv/bin/python torch==2.7.0

# what setup.py alone gives you:
env -u PYTHONPATH .bcvenv/bin/python -m projects.adder.adder \
    --trainer.max_iters=1 --trainer.num_workers=0
#   ModuleNotFoundError: No module named 'numpy'      <-- issues.md I-1

uv pip install --python .bcvenv/bin/python numpy

# and again:
env -u PYTHONPATH .bcvenv/bin/python -m projects.adder.adder \
    --trainer.max_iters=1 --trainer.num_workers=0
#   running on device cpu
#   train final score: 17/9500 = 0.18% correct
#   test  final score: 0/500 = 0.00% correct
#   saving model with new top score of 17.0
```

Also assert there are no unbuildable local-version pins:

```bash
.bcvenv/bin/python -m pip list --format=freeze | grep '+'      # must print nothing
```

**Result: `torch` + `numpy` is the complete dependency set.** No self-install of
`mingpt` is required at any point.

---

## 2. Choosing the iteration budget

Upstream ships none (issues.md I-2), so measure. On a 4-core CPU box:

```bash
time env -u PYTHONPATH .bcvenv/bin/python -m projects.adder.adder \
     --trainer.max_iters=3000 --trainer.num_workers=0
```

| iter | train | test |
|-----:|------:|-----:|
| 0    | 0.18 % | 0.00 % |
| 500  | 7.93 % | 6.60 % |
| 1000 | 76.60 % | 74.60 % |
| 2000 | 99.25 % | 98.40 % |
| 3000 | 99.69 % | **99.40 %** |

`real 2m21.9s` — **the entire row runs on a CPU in under 2½ minutes.** No GPU is needed.
3000 is the knee; that is the number we recorded.

---

## 3. Scaffold the workflow

Generated, not hand-authored:

```bash
python3 tools/scaffold_row.py \
  --name mingpt-adder \
  --repo reproducible-ai/minGPT \
  --project reproducible-ai/mingpt \
  --hf reproducible-ai/mingpt \
  --model-version 3 \
  --tracer preload \
  --license-id MIT --license-name "MIT License" \
  --description "minGPT (karpathy) projects/adder demo: a gpt-nano Transformer trained from scratch to add two 2-digit numbers." \
  --doc-url "https://github.com/reproducible-ai/minGPT/blob/master/projects/adder/readme.md" \
  --train "python -m projects.adder.adder --trainer.max_iters=3000 --trainer.num_workers=0" \
  --output out/adder/model.pt \
  --out-dir out/adder \
  --dir /home/ubuntu/cra-003-mingpt/minGPT
```

Two deliberate choices in that command:

- **`python -m projects.adder.adder`, not `python projects/adder/adder.py`.** Makes the
  recorded command path-independent and removes the need for `pip install -e .`
  entirely (issues.md I-3). Everything the run needs is *inside* the recorded command —
  no `cd`, no `export PYTHONPATH` on the line above, because environment set *around* a
  recorded command is not part of the record.
- **`--trainer.num_workers=0`** (upstream default is 4). The dataset is synthetic and
  microscopic, so worker processes buy nothing; keeping them out keeps the capture
  simple and the recorded package set complete.

minGPT ships **no experiment logging** — no wandb, mlflow, trackio or tensorboard
anywhere in the repo — so none was added.

```bash
git add .gitignore .treqs/workflows/mingpt-adder.yaml out/adder/.gitkeep
git commit && git push origin master        # master, not main
```

---

## 4. Capture

```bash
treqs project use reproducible-ai/mingpt     # org scope; verify with `treqs project status`
treqs run --title "mingpt-adder re-capture (row 003)" \
          --workflow .treqs/workflows/mingpt-adder.yaml \
          --target reproai-g4dn-plaintorch-a \
          --lineage public --source-commit HEAD --follow --yes
```

Four stages, 3 min 58 s end to end:

```
setup → train → label → publish
```

Train step on a Tesla T4: **194.97 s**, 3000 iters at ~10.6 ms/iter.

```
train final score: 9365/9500 = 98.58% correct
test  final score:  496/500  = 99.20% correct
saving model with new top score of 9861.0
```

Take the **attributed** hash from the job record, not the more prominent hash in the log:

```bash
treqs jobs show bc6a4cd6-da3f-4402-bb45-f16830f99089
# Session: c2ffb3ef71e1f4dafd87e0fc95ef172addb0e4f9b7ebc490360dbf572d60d0cc
```

---

## 5. Gate

```bash
python3 tools/gate_row.py \
  c2ffb3ef71e1f4dafd87e0fc95ef172addb0e4f9b7ebc490360dbf572d60d0cc \
  --hf reproducible-ai/mingpt
```

```
Tier-1 bar — c2ffb3ef71e1f4da · reproducible-ai/mingpt
  [OK] clean-dag    Clean-DAG check — 13/13 passed  ·  2 jobs (published DAG)
  [OK] ai-bom       AI-BOM score: 100/100  ·  profile: Advanced
  [OK] public-urls  RESULT: ALL PUBLIC
  [OK] freeze       RESULT: PORTABLE

RESULT: REPRODUCIBLE RECORD — tier 1 complete
```

43 recorded pins, all resolvable on PyPI and jointly solvable; `torch==2.7.0` with no
local version; **no `mingpt` distribution in the freeze**.

---

## 6. Independent re-run (what a visitor runs)

```bash
roar reproduce c2ffb3ef71e1f4dafd87e0fc95ef172addb0e4f9b7ebc490360dbf572d60d0cc \
      --lineage --run --no-puts
```

---

## Appendix · proving `inputs: []` on the train step is correct

The captured train step records zero inputs. Rather than assume, a control was run in
the same repo under the same roar build:

```bash
roar run -n ctl -- python -c "print(len(open('README.md').read()))"
roar show @2
#   Inputs (1):
#     blake3:3c717d1f9923…   9.6KB  .../bareclone/README.md
```

The tracer sees the repository. It excludes `.py` source, which is already pinned by the
recorded git commit. The adder demo reads **no data files at all** — `AdditionDataset`
synthesises every problem in-process from `torch.Generator().manual_seed(1337)` — so an
empty input set is complete and correct **for this workload specifically**. For a
workload that does read data files, `inputs: []` would mean the capture is broken.
