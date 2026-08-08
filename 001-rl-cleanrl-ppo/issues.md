# Issues — 001 CleanRL PPO

Obstacles hit while rebuilding `cleanrl/ppo.py` on CartPole-v1, in the order they
mattered. All findings below are about the **upstream repository**.

Short version: four items, none of them a blocker, one of them worth a PR.

---

## 1. `ppo.py` saves no model at all — upstream-worthy

**Symptom.** After a successful 500k-timestep run there is no model file anywhere.
`runs/<run_name>/` contains only `events.out.tfevents.*`.

**Root cause.** Not a bug — `ppo.py` genuinely has no persistence code. There is no
`torch.save` in the file, and no `--save-model` flag in its `Args` dataclass. The
script trains an agent, logs scalars, and calls `envs.close()`.

**Why it matters here.** A reproduction pipeline needs an artifact to hash, label and
publish. More generally: a user who runs the documented command gets metrics but
cannot keep, evaluate, or share the policy they just trained.

**Why it is upstream-worthy rather than a local quirk.** This is *inconsistent within
the repo*. `save_model` already exists in 17 of CleanRL's other single-file scripts,
including PPO's own siblings — `cleanrl/ppo_continuous_action.py` and
`cleanrl/ppo_atari_envpool_xla_jax_scan.py` — and in `dqn.py`, `c51.py`,
`td3_continuous_action.py`, `ddpg_continuous_action.py`. `ppo.py` is the file the docs
send newcomers to first ("For classic control tasks like `CartPole-v1`"), and it is
the one that lacks the flag.

**Fix applied** (`patches/ppo-save-model.diff`, 10 lines):

```python
save_model: bool = False
"""whether to save model into the `runs/{run_name}` folder"""
model_path: str = ""
"""explicit path to save the model to (default: `runs/{run_name}/{exp_name}.cleanrl_model`)"""
```
```python
if args.save_model:
    model_path = args.model_path or f"runs/{run_name}/{args.exp_name}.cleanrl_model"
    os.makedirs(os.path.dirname(model_path) or ".", exist_ok=True)
    torch.save(agent.state_dict(), model_path)
    print(f"model saved to {model_path}")
```

Deliberately **not** ported from `ppo_continuous_action.py`: its follow-on block

```python
from cleanrl_utils.evals.ppo_eval import evaluate
```

That import needs the **repository root** on `sys.path`. Running `python
cleanrl/ppo.py` puts `cleanrl/` on `sys.path`, not the root — so the evaluation block
only works if the repo has been installed as a package (`uv pip install .`), which
re-introduces exactly the package coupling that CleanRL's single-file design exists to
avoid, and which the README explicitly disclaims ("not meant to be imported"). Keeping
the port to `torch.save` alone leaves `ppo.py` standalone.

`--model-path` is a small addition on top of upstream's idiom because upstream's path,
`runs/{run_name}/...`, embeds `int(time.time())` (see §2) and is therefore not a
stable target. It defaults to upstream's exact path when unset, so behaviour is
unchanged for existing users.

**Status:** patch prepared, **not** submitted (campaign rule: no external contact).

---

## 2. The output directory name embeds a wall-clock timestamp

**Symptom.** Outputs land in
`runs/CartPole-v1__ppo__1__1786116756/events.out.tfevents.1786116757...` — a different
path on every single run.

**Root cause.** `run_name = f"{args.env_id}__{args.exp_name}__{args.seed}__{int(time.time())}"`.

**Consequence.** Two runs with identical seed and identical hyperparameters produce
outputs at different paths. That is fine for a human comparing TensorBoard runs — it
is what the scheme is for — but it means no automated consumer can name the output of
a given configuration in advance, and it defeats "same inputs → same output path".
It is also why `--model-path` was added in §1 rather than reusing the default.

**Worth noting alongside the repo's own claim** of "🪛 Local Reproducibility via
Seeding": the *weights* are seeded and reproducible; the *paths* are not.

**Workaround:** `--model-path out/ppo_cartpole.cleanrl_model`. No upstream change
proposed — the timestamped run dir is intentional.

---

## 3. `.gitignore` dir-ignores `runs`, so the output dir cannot survive a clean checkout

**Symptom.** A placeholder committed at `runs/.gitkeep` is silently not tracked.
`git add runs/.gitkeep` appears to do nothing.

**Root cause.** Upstream `.gitignore` line 3 is a bare `runs` — a **directory**
ignore. Git does not descend into an excluded directory, so no later negation
(`!runs/.gitkeep`) can re-include anything beneath it. This is documented git
behaviour, and it is easy to lose an hour to because the negation *looks* correct.

**Consequence.** `runs/` — where `ppo.py` writes its only published-by-default output
— does not exist in a fresh clone. Nothing breaks (the `SummaryWriter` constructor
creates it), but the directory that holds the artifacts is not part of the tree, so a
provenance tool cannot guarantee the path exists before the run.

**Fix applied** (`patches/gitignore-runs-dir.diff`, 1 effective line): narrow `runs`
to `runs/*`. The set of ignored *files* is identical; the directory itself becomes
expressible again.

**Upstream-worthy?** Marginal. It is correct-as-intended for upstream's own workflow.
Recorded because it is a real trap for anyone automating around the repo.

---

## 4. GitHub reports the licence as "Other"; the project is MIT

**Symptom.** `gh repo view vwxyzjn/cleanrl --json licenseInfo` →
`{"key": "other", "name": "Other"}`. Any tool that classifies by that API will record
this MIT project as unknown-licence, which for a corpus build is the difference
between "usable" and "quarantined".

**Root cause.** `LICENSE` is 316 lines: the MIT text and copyright are lines 1–22, and
below a `---` separator sit ~290 lines of third-party attribution for
`cleanrl/ppo_procgen.py` and `cleanrl/ppg_procgen.py`, adapted from AIcrowd's
NeurIPS-2020 procgen starter kit. The upstream file even explains why the block is
verbatim ("the original repo did not fill out the copyright section in their license
so the following copyright notice is copied as is per the license requirement").
GitHub's licence detector does not match a file with that much appended text.

**Resolution.** Read the file, not the API. The project is **MIT** (and the README
carries an MIT badge). Recorded as MIT.

**Note:** the appended attribution covers only the two procgen files, neither of which
is involved in this row.

---

## Non-issues (checked, and clean)

Recorded because each is a standing failure mode for this kind of rebuild, and CleanRL
avoids all of them:

* **No editable self-install.** `requirements/requirements.txt` does begin with `-e .`,
  which would normally be a problem. It is irrelevant here: `ppo.py` imports nothing
  from the repo, so the package never needs installing. Running from the repo root
  with the five real dependencies is sufficient and was verified from a fresh clone.
* **No unresolvable pins.** Every recorded distribution resolves from PyPI. No
  local-version (`+cu…`) tags, no duplicate PEP-503 spellings, and the pin set solves
  as a set.
* **No hidden data dependency.** PPO generates its own experience from the simulator,
  so the run reads no dataset and needs no download, licence, or credential. This is
  the rare row with nothing to go stale.
* **Experiment tracking already exists upstream** (`--track`, Weights & Biases) and was
  enabled rather than bolted on. Note that `ppo.py` emits its metrics through
  `SummaryWriter` and relies on `wandb.init(sync_tensorboard=True)` to mirror them, so
  what reaches a tracker depends on that bridge rather than on direct `wandb.log`
  calls.
