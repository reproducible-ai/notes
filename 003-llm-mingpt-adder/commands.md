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

## 7. Independent cold rebuild (tier 2 certification)

```bash
roar reproduce c2ffb3ef71e1f4dafd87e0fc95ef172addb0e4f9b7ebc490360dbf572d60d0cc \
    --lineage --run --no-puts -y --step-timeout 21600
```

Run on a freshly launched `t3.large` (no GPU — this row doesn't need one; 2 vCPU,
us-east-2, AMI `ami-0f07f1a0b382b48f7`) that had never seen this row, under
`roar-cli 0.4.4.dev0` installed from the presigned wheel (sha256
`a5bcde02f6a1f7bfa29ee52044f69fb72a87a1f3b6867db6911e8e82749415f0`) with
`uv tool install --python 3.12.10 --force` — the recorded-interpreter workaround for
P0-14 — and the uv-installed binary symlinked onto `PATH` so the nested `roar run`
inside the recorded step resolves. Detached with `nohup bash -c '... ; echo $? >
/tmp/cert.exitcode' …`, polled over SSM, so the literal shell exit code of the
`roar reproduce` process itself was captured directly rather than inferred from log text.

```
Steps run: 1/1          literal exit code: 0
```

Run **twice** end to end (the first pass didn't have the exit-code wrapper attached, so
it was re-run cleanly to capture that literal value — both passes reproduced
independently). Both rebuilt `out/adder/model.pt` (358,331 B) and `out/adder/config.json`
(673 B) **byte-identical across the two independent cold runs** (same sha256 both times:
`model.pt` = `569c1f2a7a753c185604fc7a10f9b6a9eb87b621baca6496dc659e71eac98f4a`,
`config.json` = `aebe5b56107c5ff4c0f5ac66316ca5c81655ff3a2b91a92d0d416b30eda50dcc`) — the
adder demo trains deterministically on CPU. `out/adder/args.txt` differed in byte count
between the two runs (95 B vs 122 B) purely because it logs `sys.argv[0]`'s absolute
path (see issues.md's "non-issues" note) and the two SSM invocations resolved
`/root/reproduce/...` vs a longer snap-confined path — not a reproducibility defect.

**Note on `model.pt` size vs. the capture:** the original GPU capture (README's own
table) reports `model.pt` at 358,971 B; this CPU cold rebuild produced 358,331 B, both
times. Expected — this claim is *reproduce*, not *replicate*, and the capture ran on a
Tesla T4 while this certification deliberately used no GPU at all. The final train/test
accuracy lines for this specific cold run were not captured in the polled log excerpt
before the log rotated past them (a gap in this certification's own polling, noted
honestly rather than papered over); the two runs' output artifacts being byte-identical
to each other is offered as the stronger determinism evidence in its place.

All **43 recorded pip pins present at recorded versions** in the reproduce venv (0
missing, 0 mismatched) — diffed by fetching `jobs/<uid>.metadata.packages.pip` from the
glaas public API against `uv pip freeze --python .venv/bin/python`, PEP-503
name-normalized before comparison. (`roar reproduce --export-requirements` returned
"Artifact not found" when invoked standalone after the run completed — not investigated
further since the API-based diff gave the same answer directly.)

**P0-14 check, direct evidence, not inference:** the reproduce venv's own `sys.path`
contains only stdlib entries plus `.venv/lib/python3.12/site-packages` — zero
`dist-packages` entries (`HOST_SHADOW_PATHS: []`). `ldd` on `libtorch_python.so` shows
every torch `.so` (`libtorch`, `libtorch_cpu`, `libtorch_cuda`, `libc10`, `libcudnn`,
`libcusparseLt`, `libcufile`, …) resolving from inside
`.venv/lib/python3.12/site-packages/torch/lib/`, with only system `libc`/`libstdc++`/
`libpthread` coming from `/lib`. The host itself has **no bare `python`** at all
(`command -v python` → not found, only `/usr/bin/python3`), so the recorded step could
only have run under the venv's own provisioned interpreter.

**P0-7 purge, this host:** both stale `roar_cli-*.dist-info` dirs present as predicted
(`0.4.0` under `/usr/local/lib/python3.10/dist-packages`, `0.4.3` under
`/opt/pytorch/lib/python3.12/site-packages`), plus their `roar/` package dirs and
`roar_inject.pth` files, and all four stale entrypoints
(`/usr/local/bin/roar[-worker]`, `/opt/pytorch/bin/roar[-worker]`). Purged unpiped;
verified empty by a follow-up `find` sweep before installing anything (`PURGE_VERIFIED_CLEAN`).

`roar --version` after the symlink: `0.4.4.dev0`. `<site-packages>/roar/bin/` held all
**6** tracer artefacts (`libroar_tracer_preload.so`, `roar-proxy`, `roar-tracer`,
`roar-tracer-ebpf`, `roar-tracer-preload`, `roard`) — this wheel was not the P0-10
tracerless build.

Instance `i-039b2f4739e893159` terminated and confirmed terminated. ~24 min instance
lifetime (16:01:35Z–16:25:41Z, two full reproduce passes), ~$0.03.

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
