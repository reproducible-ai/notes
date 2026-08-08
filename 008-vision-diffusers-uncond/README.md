# 008 — diffusers `examples/unconditional_image_generation` (DDPM)

**Verdict: reproduced** (truncated). Playbook v1.0.

A DDPM `UNet2DModel` was trained from scratch with the upstream example script,
unmodified, on the README's own `huggan/pokemon` dataset, and the resulting
`diffusion_pytorch_model.safetensors` was published with a complete, publicly
resolvable lineage record (AI-BOM 100/100). Training was deliberately truncated
to **1 epoch of 100** — this is a *reproduce* result, not a *replicate* one: the
claim is that the pipeline rebuilds, not that the sample quality matches the
reference model.

- Upstream: <https://github.com/huggingface/diffusers> @ `9c6a68c3`, Apache-2.0
- Fork: <https://github.com/reproducible-ai/diffusers> @ `0af4dfdf`
- DAG: <https://glaas.ai/dag/c7e6843763c25d8036ff22e48ba43a12d0dd0051d016f1f1e0090a88a3e99453>
- Model: <https://huggingface.co/reproducible-ai/diffusers-uncond>
- Metrics: <https://huggingface.co/spaces/reproducible-ai/experiments?project=train_unconditional>

## Difficulty: 3/5 — medium

Not because the model is hard, and not because anything was broken. The example
script itself needed **zero source changes** and ran correctly on the first
GPU attempt. The difficulty is concentrated in one structural fact, discovered
before spending anything:

> **The example cannot be run against any released `diffusers`.**
> `train_unconditional.py` opens with `check_min_version("0.40.0.dev0")`, and the
> newest release on PyPI is `0.39.0`. Every published version of the library is
> rejected by the example that ships beside it.

This is the reproducibility crux of the row. The README is candid about it — it
tells you to `git clone` and `pip install .` from source — but the consequence is
that a naive `pip install diffusers` reproduction is impossible *by construction*,
and a source install records a `diffusers==0.40.0.dev0` pin that resolves nowhere.
Both routes produce a record that looks fine and rebuilds nowhere.

The resolution was to not install `diffusers` at all and take the library from the
checked-out commit, putting `src/` on `sys.path` from *inside* the recorded
command. The git commit is already part of the lineage record, so the library is
pinned by the same mechanism that pins the training script — which is arguably
more honest than a version pin would have been. The recorded environment then
contains only distributions that genuinely resolve on PyPI (85/85 verified).

Everything else was ordinary: the deps that the example under-declares had to be
added, and the repo's `.gitignore` had to stop directory-ignoring an output path.

## What was run

One `roar run` step, one epoch, on a `g4dn.xlarge` (Tesla T4). 460 optimisation
steps, batch 16, resolution 64, EMA on — i.e. the README's own Pokémon command
with `--num_epochs` cut from 100 to 1 and the sampling loop cut from 1000
denoising steps to 10. Loss and EMA decay were logged every step to the campaign
trackio Space, and a batch of sample images was generated and logged at the end
of the epoch. A metric is *computed*; no claim is made about its value.

See `commands.md` for the exact recipe, `issues.md` for the five upstream
findings, and `costs.md` for the burn.
