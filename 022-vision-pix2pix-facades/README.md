# 022 — pix2pix on CMP Facades

Upstream: [`junyanz/pytorch-CycleGAN-and-pix2pix`](https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix) @ `2a7afba`
Fork: [`reproducible-ai/pytorch-CycleGAN-and-pix2pix`](https://github.com/reproducible-ai/pytorch-CycleGAN-and-pix2pix) @ `750f61d`
DAG: [`14df351c…c622b`](https://glaas.ai/dag/14df351c56d65be8181299f225e5c266f35e6aded43dc8068b5f0e2e76ac622b) · Artifacts: [`reproducible-ai/pix2pix-facades`](https://huggingface.co/reproducible-ai/pix2pix-facades)

## What ran

Upstream's published pix2pix command, unmodified:

```
python train.py --dataroot ./datasets/facades --name facades_pix2pix --model pix2pix \
  --direction BtoA --n_epochs 1 --n_epochs_decay 1 --save_epoch_freq 1 --num_threads 0
```

The dataset came from upstream's own `datasets/download_pix2pix_dataset.sh facades`, and all 400
images of the training split were used — the data is not subsampled. What is truncated is the
schedule: 2 epochs of upstream's 200. Those two were chosen as one constant-learning-rate epoch and
one decay epoch, so `linear` LR policy actually executes rather than being skipped, which a
`--n_epochs_decay 0` truncation would have done.

800 iterations, batch size 1, 256×256 crops, one Tesla T4. 67.5 s of traced training. The
generator is 54.414 M parameters and the discriminator 2.769 M, both published.

**Zero lines of upstream Python changed.** The fork adds a workflow file, `.gitignore` rules and
seven directory placeholders — nothing else. `git diff --name-only upstream..fork -- '*.py'` is
empty.

## This is a genuinely clean repo

Most rows in this campaign spend their write-up on what was broken. This one does not have much to
report, and that is the finding. There were no missing dependencies, no imports broken by a newer
NumPy, no absolute paths baked into shipped manifests, no distributed-only entry point demanding
`RANK`/`WORLD_SIZE` be conjured by hand. The published command ran against the published dataset and
produced the published kind of artifact. Difficulty 3/10, and the 3 is mostly the two traps below.

The pre-spend bare-clone check passed first time: a fresh clone, a scratch venv containing only the
seven pins the recipe declares, `PYTHONPATH` unset, both recorded commands executed — no
`ModuleNotFoundError`. That is rarer than it should be.

## The trap worth knowing about

**At upstream's default `--save_epoch_freq 5`, a short run silently produces nothing.**

`train.py` writes a checkpoint only when `epoch % save_epoch_freq == 0`, and the other save path,
`save_latest_freq`, is 5000 iterations — which a short run never reaches. So a one- to four-epoch
trial, the obvious first thing anyone does with an unfamiliar trainer, runs to completion, prints
`End of epoch`, exits 0, and leaves the checkpoint directory empty. Nothing warns. This row had to
set `--save_epoch_freq 1` or there would have been no artifact to publish.

A related sizing point that only shows up when you truncate: `--print_freq` is 100, so the loss log
only gets a line every 100 iterations. An earlier, more aggressive plan for this row — 8 images,
1 epoch — would have run 8 iterations and written a loss log containing nothing but its header. It
would have trained a model, passed every gate, and computed no visible metric at all. Running the
full 400-image split for 2 epochs produces 8 logged points (`G_GAN`, `G_L1`, `D_real`, `D_fake`) and
costs about four cents more. Truncate the schedule, not the data.

## Why there is no experiment link

Upstream *does* ship logging — `--use_wandb` at `options/base_options.py:57` — so this is not a
"no integration exists" row, and the flag was not simply overlooked.

It cannot be used against anything but the real wandb package. `util/visualizer.py:70` calls
`self.wandb_run._label(repo='CycleGAN-and-pix2pix')` on the object `wandb.init()` returns. `_label`
is private, undocumented wandb internals. No wandb-compatible substitute implements it, so enabling
the flag raises `AttributeError: '_Run' object has no attribute '_label'` and kills the run. This
was verified by replaying upstream's exact call shape on CPU, for $0, before any GPU time was
booked.

There is a second reason not to force it. `util/visualizer.py:7` imports `wandb` unconditionally at
module import, so aliasing `wandb` to a substitute would make the recorded dependency set name the
substitute in place of the wandb this repo genuinely requires — trading a link for a false
dependency record. The run therefore used upstream's own default (`--use_wandb` off) with a real
`wandb==0.21.1` installed, which is exactly what the freeze records.

## Memory, and why the method is printed next to the number

**Peak GPU memory: 9,157 MiB, nvidia-smi at 1 Hz, 69 samples**, taken from the stage shell alongside
the recorded command.

The method matters more than the number. `nvidia-smi` reports whole-device usage including the CUDA
context and the allocator's reserved blocks; `torch.cuda.max_memory_allocated()` counts live tensors
only and typically reads about half as much. An unlabelled figure is not usable for sizing — an
earlier row in this campaign was put on an L40S at $1.861/hr when a T4 at $0.526/hr would have done,
a 3.5× overpay, because the number was recorded without its method.

On the 16 GB T4 this leaves roughly 40% headroom, so the T4 is the right instance for pix2pix at
this resolution. Note that only the nvidia-smi figure exists for this row:
`max_memory_allocated()` would have meant editing `train.py`, which forfeits zero-upstream-lines.

## Cost

The recorded run cost about **$0.07** — 207.6 s of job time on a g4dn.xlarge at $0.526/hr, plus a
stated 300 s boot allowance that was *not* measured here because the host was already warm. Only
50 s of that is epoch compute; the rest is environment build, a 30 MB dataset fetch and a 229 MB
upload, none of which grows with epoch count.

A full 200-epoch run is estimated at **$0.71** — 28 s for the first epoch, 22 s for each steady-state
epoch thereafter, so 4,406 s of training plus the same fixed overhead. That estimate rests on a
single steady-state epoch, which is why it is marked moderate confidence rather than high.

## Status

Tier 1 only. All four gates pass — clean-DAG 14/14, AI-BOM 100/100 (Advanced), all URLs public,
freeze PORTABLE — and the run exited 0, but none of that executes the record on a fresh host. No
cold rebuild has been attempted, so `certification.result` is `null`.

One thing a certifier should know before starting: **the recorded dependency set is thin.** The train
step recorded 25 pins where 51 distributions were installed, and two of the omissions are packages
the workload loads — `typing-extensions`, which torch 2.4.0 declares as a hard requirement
(`typing-extensions>=4.8.0`) and imports during `import torch`, and `tqdm`. Both are transitive
dependencies of packages that *are* recorded, so the set stays jointly solvable and a rebuild will
probably succeed. That is the point worth being careful about: a green rebuild here would demonstrate
that the recorded set *resolves*, not that it is *complete*. The absence of `scikit-image`, by
contrast, is correct — the colorization model that imports it is never loaded by this recipe.
