# Upstream findings — shiyu-coder/Kronos @ 67b630e

Everything here is about the **upstream repository**. Nothing was reported to
upstream: campaign policy forbids external contact.

---

## 1. 🔴 `finetune_csv/`'s "Method 2" entry points both crash before the first batch

`finetune_csv/README.md` §3 documents two ways to train:

```
# Method 2: Individual Component Training
python finetune_tokenizer.py --config configs/config_ali09988_candle-5min.yaml
python finetune_base_model.py --config configs/config_ali09988_candle-5min.yaml
```

Both raise `UnboundLocalError` before any data is loaded:

```
File "finetune_csv/finetune_tokenizer.py", line 296, in main
  os.makedirs(config.tokenizer_save_path, exist_ok=True)
UnboundLocalError: local variable 'os' referenced before assignment
```

`os` is imported at module level (line 1), but `main()` also does
`import json, os` inside an `else:` branch — `finetune_tokenizer.py:310`,
`finetune_base_model.py:394` and `:421`. A function-local binding anywhere in a
function makes the name local **for the whole function**, so the earlier
`os.makedirs()` at `finetune_tokenizer.py:296` / `finetune_base_model.py:380`
resolves against an unassigned local.

The branch that would actually execute `import json, os` is the
`pre_trained_tokenizer: false` / `pre_trained_predictor: false` path, so the
crash fires on the *documented, default* path and cannot be avoided by config.

Fix is one word per site (`import json, os` -> `import json`); the patch is in
`patches/0001-fix-unboundlocalerror-os-in-finetune_csv-entrypoints.patch`. It is
**not applied to our fork** — this row uses upstream's "Method 1 (Recommended)"
`train_sequential.py`, which has no such shadowing (its in-branch imports are
`import json` only), and whose `--skip-basemodel` / `--skip-tokenizer` flags give
the same two-stage split. Zero upstream lines are changed by this reproduction.

## 2. 🟠 `requirements.txt` does not declare PyYAML

`finetune_csv/config_loader.py:2` does `import yaml`, and every `finetune_csv`
entry point goes through it. `requirements.txt` lists numpy, pandas, torch,
einops, huggingface_hub, matplotlib, tqdm and safetensors — no PyYAML. A fresh
environment built strictly from `requirements.txt` dies on the first config load.
(In practice PyYAML arrives transitively via other packages on most images, which
is why this survives.)

## 3. 🟠 The template config cannot run anywhere as shipped

`finetune_csv/configs/config_ali09988_candle-5min.yaml` ships absolute
placeholder paths — `/xxxx/Kronos/finetune_csv/data/...`,
`/xxx/Kronos/pretrained/Kronos-Tokenizer-base`. This is honest as a template, but
it means the documented command in the README is not runnable as written, and the
`pretrained/` directory it points at does not exist in the repository and is
never created by any script. Our config (`config_repro_kronos-small_1epoch.yaml`)
uses paths relative to `finetune_csv/` instead.

## 4. 🟠 The README quickstart reads a CSV that is not in the repository

`examples/prediction_example.py:49` (and its siblings) do
`pd.read_csv("./data/XSHG_5min_600977.csv")`. There is no `data/` directory at
the repository root; the only shipped CSVs are
`finetune_csv/data/HK_ali_09988_kline_5min_all.csv` and the two under `tests/`.
The README's "get from raw data to forecasts in just a few lines" example
therefore fails on a fresh clone.

## 5. 🟡 The working directory is load-bearing and undocumented

`train_sequential.py:10`, `finetune_tokenizer.py:18` and
`finetune_base_model.py:20` all do `sys.path.append('../')` to reach the `model`
package. That is relative to the **process working directory**, not the file, so
the scripts import only when run from inside `finetune_csv/`. Running
`python finetune_csv/train_sequential.py` from the repository root fails with
`ModuleNotFoundError: No module named 'model'`. The README never states this; it
is implied by showing bare `python train_sequential.py`.

This row makes the requirement explicit and recorded by invoking
`env -C finetune_csv python train_sequential.py ...`, so the working directory
travels inside the recorded command rather than in an unrecorded `cd`.

## 6. 🟡 `use_comet` is dead config in `finetune_csv/`

`config_loader.py:165` reads `experiment.use_comet` and forwards it through
`get_tokenizer_config()` / `get_basemodel_config()`, but no file under
`finetune_csv/` imports `comet_ml` or constructs a logger. Setting it `true`
changes nothing. Comet is wired only into the **other** pipeline,
`finetune/train_predictor.py:12,200` and `finetune/train_tokenizer.py:15,238`,
which trains from Qlib data rather than CSV. A user following
`finetune_csv/README.md` and setting `use_comet: true` gets silence.

## 7. 🟢 Not a defect — the two pipelines are genuinely different products

`finetune/` (Qlib) and `finetune_csv/` (bring-your-own CSV) share the `model/`
package and nothing else: different config mechanism (`finetune/config.py` is a
Python class; `finetune_csv` is YAML), different data path, different logging
story. Only `finetune_csv/` is reproducible by an outsider, because `finetune/`
requires a Qlib data directory that is not published.
