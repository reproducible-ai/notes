# Commands — 001 CleanRL PPO

The recipe, in the order it was run. Everything here is reproducible by a third party
except the compute-target and credential lines, which are campaign-specific.

## 0. Upstream facts worth checking first

```bash
# The default branch is `master`, NOT `main` — a wrong assumption here is fatal
# because a reproduction clones the recorded remote at the recorded commit.
gh repo view vwxyzjn/cleanrl --json defaultBranchRef        # -> "master"

# The licence API is wrong; read the file (see issues.md #4)
gh repo view vwxyzjn/cleanrl --json licenseInfo             # -> "other"  (actually MIT)
head -22 LICENSE                                            # -> MIT License, (c) 2019 CleanRL developers
```

## 1. Clone

```bash
git clone https://github.com/reproducible-ai/cleanrl.git    # fork of vwxyzjn/cleanrl
cd cleanrl
```

Upstream base for this row: `fe8d8a0`.

## 2. Dependencies

`ppo.py` is standalone — it imports `gymnasium`, `numpy`, `torch`, `tyro` and
`tensorboard`, and nothing from the repo. **Do not** `pip install -e .`; it is not
needed, and an editable install of a package the script never imports only adds risk.

```bash
pip install "gymnasium==0.29.1" tyro tensorboard torch
```

`gymnasium` is pinned to upstream's own `pyproject.toml` pin. It is not cosmetic:
`ppo.py` reads `infos["final_info"]`, the pre-1.0 vector-env contract, and gymnasium
1.x changed it.

Verified working substrate for this row: Python **3.12.10**, `torch==2.7.0`,
`numpy==2.5.1`. Upstream's `pyproject.toml` pins `torch==2.4.1` and caps
`requires-python` at `<3.11`; both constrain the *`cleanrl` package*, which is never
installed here, and neither was binding on the script.

## 3. Train (the recipe)

Upstream defaults, full run, no truncation:

```bash
python cleanrl/ppo.py \
    --env-id CartPole-v1 \
    --seed 1 \
    --total-timesteps 500000 \
    --track --wandb-project-name cleanrl-ppo-cartpole \
    --save-model --model-path out/ppo_cartpole.cleanrl_model
```

* `--save-model` / `--model-path` are the 10-line patch in
  `patches/ppo-save-model.diff` — stock `ppo.py` saves nothing (issues.md #1).
* `--track` is upstream's own Weights & Biases flag. Drop it and the run is identical
  minus tracking; nothing else depends on it.
* Everything else is a default. `learning_rate 2.5e-4`, `num_envs 4`, `num_steps 128`,
  `gamma 0.99`, `gae_lambda 0.95`, `clip_coef 0.2`, `ent_coef 0.01`, `vf_coef 0.5`, …
  are literals in the `Args` dataclass at the top of the file.

Expected output: `SPS:` lines and `episodic_return` climbing to **500.0**
(CartPole-v1's ceiling) and staying there. Run took **289 s** on one Tesla T4.

## 4. Bare-clone check (do this before spending anything)

The single highest-value step. Fresh clone, scratch venv with only the expected pins,
`PYTHONPATH` unset, **no credentials at all** — i.e. exactly what a stranger has:

```bash
git clone https://github.com/reproducible-ai/cleanrl.git && cd cleanrl
uv venv --python 3.12 /tmp/venv-bare
uv pip install --python /tmp/venv-bare/bin/python \
    torch==2.7.0 gymnasium==0.29.1 tyro tensorboard

env -u PYTHONPATH -u HF_TOKEN -u TRACKIO_SPACE_ID \
  /tmp/venv-bare/bin/python cleanrl/ppo.py \
      --env-id CartPole-v1 --seed 1 --total-timesteps 2048 \
      --track --wandb-project-name cleanrl-ppo-cartpole \
      --save-model --model-path out/ppo_cartpole.cleanrl_model
```

Result: **exit 0**, `model saved to out/ppo_cartpole.cleanrl_model`, no
`ModuleNotFoundError`. Note this passes with `--track` set and **no `wandb`
installed** — see the note in `issues.md` about how `ppo.py` routes metrics.

Sanity checks on the venv before trusting it:

```bash
uv pip list --python /tmp/venv-bare/bin/python --format=freeze | grep '+'    # local-version pins: empty
uv pip list --python /tmp/venv-bare/bin/python --format=freeze \
  | cut -d= -f1 | tr 'A-Z_' 'a-z-' | sort | uniq -d                          # PEP-503 dupes: empty
```

## 5. Capture + publish (campaign-specific)

```bash
treqs project use reproducible-ai/cleanrl-ppo
treqs run --title "CleanRL PPO CartPole-v1 (row 001)" \
  --workflow .treqs/workflows/cleanrl-ppo-cartpole.yaml \
  --target <compute-target> --lineage public --source-commit HEAD --yes
```

Workflow: `setup → train → label → publish`, one commit, four stages.

## 6. Reproduce this exact row

```bash
roar reproduce 58df327f1e02faf0d64efb8f07daac7c9eca70d3713d008bc8587fea780617be \
    --lineage --run --no-puts
```

## 7. Independent cold rebuild (tier 2 certification)

```bash
roar reproduce 58df327f1e02faf0d64efb8f07daac7c9eca70d3713d008bc8587fea780617be \
    --lineage --run --no-puts -y --step-timeout 21600
```

Run on a freshly launched `g4dn.xlarge` (1x Tesla T4, us-east-2, AMI
`ami-0f07f1a0b382b48f7`) that had never seen this row, under `roar-cli 0.4.4.dev0`
installed from the presigned wheel (sha256
`a5bcde02f6a1f7bfa29ee52044f69fb72a87a1f3b6867db6911e8e82749415f0`) with
`uv tool install --python 3.12.10 --force` — the recorded-interpreter workaround for
P0-14 — and the uv-installed binary symlinked onto `PATH` so the nested `roar run`
inside the recorded step resolves. Detached with `nohup … &`, polled over SSM.

```
Steps run: 1/1          exit code: 0   (from roar's own job DB — job_uid 72be16dc)
```

It rebuilt `out/ppo_cartpole.cleanrl_model` (41,625 B) and
`events.out.tfevents...` (678,636 B), with `episodic_return=[500.]` at the final
`global_step=499612` — CartPole-v1's ceiling, identical to the capture. All 69
recorded pip pins were present in the reproduce venv at the recorded versions (0
missing, 0 mismatched), diffed via `roar reproduce --lineage --export-requirements`
against `uv pip freeze --python .venv/bin/python`.

**P0-14 check, direct evidence, not inference:** the training process's
`/proc/<pid>/environ` carried `VIRTUAL_ENV=…/reproduce/cleanrl/.venv` with
`.venv/bin` prepended to `PATH`; every loaded `torch` `.so` (`_C`, `libc10`,
`libtorch`, `libtorch_cuda`, …) resolved under `.venv/lib/python3.12/site-packages/`
per `/proc/<pid>/maps`; and a `dist-packages` grep against those same maps returned
zero hits — no host package directory was mapped into the process at all.

Instance terminated and confirmed terminated. ~15 min instance lifetime, ~$0.13.
