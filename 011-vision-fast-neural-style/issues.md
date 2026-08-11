# Issues — 011 fast_neural_style (`pytorch/examples`)

Every obstacle hit while turning `examples/fast_neural_style` into a recorded,
rebuildable pipeline. Symptom → root cause → what was done → is it upstream-worthy.

This row was picked as the *cleanest candidate in its batch*: three declared
dependencies, `torch.save` only, no OS-package edge, no copy/link anywhere. It
largely lived up to that — nothing here blocked the row. But "clean" turned out to
mean "clean to run by hand", and that is a different property from "clean to
record". Most of what follows is the gap between those two.

---

## 1. The final model's filename contains a wall-clock timestamp — so the pipeline cannot name its own output

**Severity: this is the one real obstacle in the row.**

`neural_style/neural_style.py:119-122`:

```python
timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
save_model_filename = f"epoch_{args.epochs}_{timestamp}_{args.content_weight}_{args.style_weight}.model"
save_model_path = os.path.join(args.save_model_dir, save_model_filename)
torch.save(transformer.state_dict(), save_model_path)
```

Observed on a probe run: `epoch_1_2026-08-11_03-07-15_100000.0_10000000000.0.model`.

**Why it matters here and not to a human.** A person runs the training, looks in the
directory, and reads the filename off the screen. A *recorded* pipeline cannot: the
step after training has to be written before the training runs, and it has to name
its input literally. `roar label set artifact <path>` and `roar put <path>` take
literal paths, and traced commands are argv, not shell — there is no glob, no
`$(ls -t | head -1)`, no shell at all. Upstream's own README has the same problem in
miniature: its stylize example says `--model </path/to/saved/model>` and its train
example never tells you what that path will be.

**What was done.** No source change. The recipe uses upstream's *other* save path,
which is deterministic — `neural_style.py:110-114` writes
`ckpt_epoch_{e}_batch_id_{batch_id+1}.pth` into `--checkpoint-model-dir` every
`--checkpoint-interval` batches. Setting `--checkpoint-interval` to exactly the
number of batches in the epoch (2368 = ceil(9469/4)) makes it fire once, on the last
batch, *after* that batch's `optimizer.step()`. So the deterministically-named file
holds the same weights as the timestamped one — it is not an early snapshot. Both
files are written and both are in the lineage; only the nameable one is labelled and
published.

**A dependency this creates, and the guard for it.** `--checkpoint-interval` is now
derived from the dataset size. If the dataset ever changed, training would run for
~8 GPU-minutes and then write a file no downstream step knows the name of. So the
fetch step asserts the count (`--expect-train-images 9469`) and exits non-zero before
any GPU time is spent.

**Upstream-worthy: yes.** A `--save-model-name` override, or simply dropping the
timestamp when one is supplied, would cost a few lines and make the example
scriptable. Not filed — this campaign does not post upstream (see the boundary note
in the README).

---

## 2. `requirements.txt` omits Pillow, which the code imports directly

`fast_neural_style/requirements.txt` is three lines:

```
numpy
torch>=2.6
torchvision
```

But `neural_style/utils.py:2` is `from PIL import Image`, and every image this
example loads or saves goes through it (`load_image`, `save_image`). Pillow is
present only because `torchvision` depends on it transitively.

**Why this is worth writing down rather than shrugging at.** It is the same shape as
the defect this campaign spends most of its effort on: a dependency that is genuinely
used but not written down, which *happens* to be installed because something else
pulled it in. It works today and it is not guaranteed to. It also means the declared
dependency list is not a description of the workload.

The recorded environment for this row does list `pillow` — the recorded package set
is derived from what the process actually loaded, not from `requirements.txt`, so the
lineage is more accurate than the repo's own manifest. That is a nice result but it
is luck from the reader's point of view, not something `requirements.txt` earned.

**Fix applied:** none to upstream. The workflow's setup stage asserts
`import PIL` explicitly so a missing Pillow fails in an untraced stage rather than
mid-training. **Upstream-worthy: yes**, one line.

---

## 3. `--style-size` and `--content-scale` have been broken since Pillow 10.0 (July 2023)

Both documented flags route into `utils.load_image`, which calls a constant Pillow
removed three years ago:

```python
# neural_style/utils.py
 8:        img = img.resize((size, size), Image.ANTIALIAS)      # --style-size
10:        img = img.resize((...), Image.ANTIALIAS)             # --content-scale
```

Reproduced directly against Pillow 12.2.0, both paths:

```
  File ".../neural_style/utils.py", line 8, in load_image
    img = img.resize((size, size), Image.ANTIALIAS)
AttributeError: module 'PIL.Image' has no attribute 'ANTIALIAS'

  File ".../neural_style/utils.py", line 10, in load_image
    img = img.resize((int(img.size[0] / scale), int(img.size[1] / scale)), Image.ANTIALIAS)
AttributeError: module 'PIL.Image' has no attribute 'ANTIALIAS'
```

`Image.ANTIALIAS` was deprecated in Pillow 9.1 and **removed in 10.0**; the modern
spelling is `Image.Resampling.LANCZOS` (or just `Image.LANCZOS`). `requirements.txt`
does not pin Pillow at all, so a fresh install always gets a version where these two
flags raise.

The README documents `--content-scale` as the remedy "if memory is an issue" — i.e.
the flag you reach for exactly when a large image will not fit, which is when it will
fail. Nothing else in the example is affected: with both flags left unset,
`load_image` skips the resize branch entirely.

**Fix applied:** the recipe deliberately passes neither flag, and the workflow says
why at the stylize stage. **Upstream-worthy: yes**, a two-token change.

---

## 4. `neural_style/` has an `__init__.py` but cannot be imported as a package

`neural_style/__init__.py` exists (empty, 0 bytes), which makes the directory look
like a package. It is not usable as one — `neural_style.py:15-17` uses flat sibling
imports:

```python
import utils
from transformer_net import TransformerNet
from vgg import Vgg16
```

Those resolve only because Python puts a *script's own directory* at `sys.path[0]`.
Run it as a module and it dies:

```
$ python -m neural_style.neural_style eval ...
  File ".../neural_style/neural_style.py", line 15, in <module>
    import utils
ModuleNotFoundError: No module named 'utils'
```

**Why this mattered for the row.** The standing advice for making a recorded command
path-independent is "use `python -m pkg.module` and run from the repo root" — the
recipe that avoids depending on the working directory. That advice is unavailable
here. The command must be `python fast_neural_style/neural_style/neural_style.py`,
spelled as a path, so that `sys.path[0]` becomes `fast_neural_style/neural_style/`
and the sibling imports resolve.

That works and is what the recipe does, and it is stable under `roar reproduce`
because reproduce replays argv verbatim from the repository root. But it is worth
naming: this example is *not* runnable from an arbitrary directory, and a generic
`import utils` sitting on `sys.path[0]` is a name a larger tree could easily shadow.

**Fix applied:** none needed. **Upstream-worthy: marginal** — deleting the empty
`__init__.py` would at least stop advertising a package that does not exist.

---

## 5. The DataLoader does not shuffle

`neural_style.py:49`:

```python
train_loader = DataLoader(train_dataset, batch_size=args.batch_size)
```

No `shuffle=True`, and no `num_workers` either. With upstream's intended COCO
directory (one flat folder of photographs) the ordering is arbitrary and nobody
notices. With any `ImageFolder` that has real classes — which is what this row uses,
and what anyone substituting a smaller dataset will use — training walks class 0 to
completion, then class 1, and so on. The style loss is global and the content loss is
per-image, so this does not invalidate the run, but the optimizer sees a strongly
non-i.i.d. stream, which is not what the paper's recipe assumes.

Recorded as a fidelity note on this row's result rather than a defect in it.
**Upstream-worthy: yes**, one keyword argument.

**The flip side is a genuine benefit, and it is worth saying so.** Because there is
no `num_workers` knob at all, data loading is single-process by construction. This
campaign has repeatedly lost the workload's package set from a recorded step when
DataLoader worker processes were in play — the step records the tracer's own
dependency closure instead of the workload's. This example cannot be got wrong that
way. It is the only row so far that gets that property for free.

---

## 6. There is no experiment logging, and no quantitative evaluation

Grepped the entire `fast_neural_style/` subdirectory for `wandb`, `mlflow`,
`trackio`, `tensorboard`, `SummaryWriter`, `comet`, `neptune`, `report_to`: **zero
hits.** Upstream ships no logging integration of any kind.

So `experimentUrl` is `null` on this row, and the reason is recorded rather than
defaulted into. The bridge this campaign uses only intercepts a `wandb` import that
the workload actually performs; against a workload that never imports `wandb` it is a
guaranteed no-op, and enabling it would put a mechanism in the record that the record
never uses. **It was therefore removed from the generated workflow rather than left
in.** Adding `wandb.init()` to `neural_style.py` to manufacture a link would forfeit
the zero-upstream-lines property that is the only reason this row is evidence of
anything.

Relatedly, the example computes no held-out metric. `eval` is a *stylize* command: it
renders one image. The quantitative output of this row is therefore the training loss
— content, style and total, printed by `neural_style.py:101-108` — and nothing else.
That is upstream's design, not a truncation artifact; a perceptual-loss style-transfer
model has no accuracy to report. Stated here so the row's "metrics" claim is not read
as more than it is.

---

## 7. The documented dataset is a 13 GB manual browser download

The README's only dataset guidance is:

> `--dataset`: path to training dataset … I used COCO 2014 Training images dataset
> [80K/13GB] [(download)](https://cocodataset.org/#download).

There is no fetch script, no checksum, and no size-reduced alternative. A pipeline
that starts from "go to a website and download 13 GB" cannot be recorded: the
training step's input would appear in the lineage from nowhere.

**Fix applied:** `fast_neural_style/repro/fetch_dataset.py` — new file, standard
library only (`urllib` + `tarfile`), nothing under `neural_style/` touched. It
downloads Imagenette-320 (9,469 train images, 342 MB), prints the archive sha256,
extracts with `filter="data"`, and asserts the image count. Standard library was a
deliberate choice: the fetch step then adds no dependency the training step does not
already need, so the recorded package set stays a description of the workload rather
than of the fetcher.

Substituting Imagenette for COCO is a **scale** decision, not a semantic one — the
objective is a VGG-16 perceptual loss plus a Gram-matrix style term, and nothing in
it depends on COCO's annotations, categories or particular photographs. It is
declared on both axes in `row.json` (`truncation.note`) and in the published artifact
description, and it is the reason the run costs cents rather than an hour.

---

## 8. Monorepo hazard: a sibling directory in the same repo *is* exposed

Not a defect in `fast_neural_style/`, but it is the reason every path in this row's
workflow is scoped, and it belongs in the record.

`pytorch/examples` is one repository containing ~25 unrelated examples. This row
reproduces one of them. `examples/imagenet/main.py:432` does:

```python
shutil.copyfile(filename, 'model_best.pth.tar')
```

which reproduces an already-written checkpoint's bytes *exactly* at a second path.
That is the duplicate-bytes shape this campaign screens every row for, and it is one
directory away from this one.

`fast_neural_style/` itself is clean, verified rather than assumed — grepped for
`os.link`, `os.symlink`, `shutil.copyfile`, `shutil.copy2` and `shutil.copy`: no
hits anywhere under it. Its only persistence is two `torch.save` calls
(`neural_style.py:114` and `:122`).

**And the two `torch.save` calls were checked empirically, not argued from.** This
recipe deliberately makes both fire with the same weights, so "same weights ⇒ same
bytes" was the thing to disprove. On an 8-image probe run:

| file | size | sha256 (first 8) |
|---|---|---|
| `ckpt_epoch_0_batch_id_2.pth` | 6,739,497 B | `e43d7632` |
| `epoch_1_…_100000.0_10000000000.0.model` | 6,741,397 B | `2e993b14` |

Different sizes, different hashes — `torch.save` embeds the output file's stem in the
zip container, so identical weights do not produce identical files. The exposure does
not fire here.

**The generalisable lesson:** repo-level screening is the wrong granularity for a
monorepo. `pytorch/examples` would screen as *exposed*; `pytorch/examples/fast_neural_style`
screens as *clean*. Both statements are true and only the second one is about this row.

---

## 9. The repo's own `.gitignore` would have silently swallowed this row's outputs

`.gitignore` in `pytorch/examples` contains, among others:

```
data
fast_neural_style/saved_models
```

Both are **directory ignores with no tracked file inside**, which is precisely the
pattern that drops a directory from a clean checkout — and a directory that does not
survive a clean checkout does not survive a rebuild, so anything written into it
falls out of the lineage without a warning. `fast_neural_style/saved_models` is the
example's own natural output directory, and the bare `data` pattern matches a path
component named `data` at *any* depth, so the obvious `fast_neural_style/data` for a
dataset is caught too.

Worse, neither can be rescued with a negation: git will not re-include a file whose
parent directory is excluded.

**Fix applied:** this row's four output directories are named around both patterns —
`fast_neural_style/out-data`, `out-models`, `out-ckpt`, `out-stylized` — and each
gets the file-pattern ignore plus a tracked `.gitkeep`, so the directory survives a
clean checkout and its contents stay out of git. Verified with `git check-ignore -v`
that each output path resolves to the intended rule and not to an upstream one.

**Upstream-worthy: no.** Upstream's `.gitignore` is entirely reasonable for a repo of
runnable examples; it is only hostile to *recording* them.
