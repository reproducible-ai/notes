# 001 · CleanRL — PPO (`ppo.py`, CartPole-v1)

**Verdict: reproduced.** Difficulty **2/10 — genuinely easy**, and the easiest kind
of easy: nothing was worked around, nothing was pinned down by trial and error. The
run converged on the first honest attempt at upstream's own default hyperparameters.

| | |
|---|---|
| Upstream | [`vwxyzjn/cleanrl`](https://github.com/vwxyzjn/cleanrl) @ `fe8d8a0` (default branch **`master`**, not `main`) |
| Licence | **MIT** — see [`LICENSE`](https://github.com/vwxyzjn/cleanrl/blob/master/LICENSE) |
| Entry point | `cleanrl/ppo.py`, `--env-id CartPole-v1` |
| Recipe | upstream defaults, **full 500,000 timesteps** (not truncated) |
| Result | final episodic return **500.0** — CartPole-v1's ceiling |
| Wall clock | 289 s train · ~5 min end-to-end |
| Fork | [`reproducible-ai/cleanrl`](https://github.com/reproducible-ai/cleanrl) @ `99bb287` |
| Patch vs upstream | 10 lines in `ppo.py`, 1 line in `.gitignore` |

## Summary

CleanRL is a *single-file* RL library: `cleanrl/ppo.py` is 320 lines that import
`gymnasium`, `numpy`, `torch`, `tyro` and `tensorboard` and **nothing from the
repository itself**. That one design decision is why this row was easy, and it is
worth stating plainly because it is the exact opposite of what usually goes wrong:

* There is **no package to install**, so there is no `pip install -e .` to blind a
  tracer or to vanish from a dependency freeze. `python cleanrl/ppo.py` from the repo
  root is the whole recipe, and it is path-independent.
* The dependency set is small (16 distributions when nothing optional is loaded) and
  every one of them resolves from PyPI with no local-version tag and no private index.
* The hyperparameters are literal defaults in a `@dataclass` at the top of the file.
  Reproducing "the published recipe" means passing `--env-id CartPole-v1` and nothing
  else.

The rebuild converged: episodic return reaches CartPole-v1's maximum of 500 and stays
there, consistent with the ~490 average that upstream's own
[docs](https://docs.cleanrl.dev/rl-algorithms/ppo/#ppopy) report for `ppo.py` against
`openai/baselines`.

**One real gap, and it is a provenance gap rather than a correctness one:** `ppo.py`
as published **saves no model**. It writes TensorBoard event files and exits. There is
no `torch.save` anywhere in the file, so there is no artifact to hash, label, or
publish. Ten lines were added to fix that — ported from its own sibling
`cleanrl/ppo_continuous_action.py`, which already has the flag. See
[`issues.md`](issues.md#1) for why this is worth reporting upstream and why the port
deliberately drops that sibling's evaluation block.

## Narrative

**Reading the materials.** The README and the PPO docs page agree on the command and
are accurate. The README's headline claim — "Every detail about an algorithm variant
is put into a single standalone file" — is true, and it is load-bearing: it is what
makes the repo cleanly reproducible. A caveat the README also states outright:
*"CleanRL is not a modular library and therefore it is not meant to be imported."*

**The licence needs a human.** GitHub's licence API reports `"key": "other"` for this
repository, which would categorise a permissively-licensed project as unknown. The
`LICENSE` file itself opens `MIT License / Copyright (c) 2019 CleanRL developers`. The
API is confused by ~290 lines of third-party attribution appended below the MIT text
(for `ppo_procgen.py` / `ppg_procgen.py`, adapted from an Apache-2.0 starter kit). The
project is MIT; the row records MIT.

**Dependencies.** `pyproject.toml` pins `gymnasium==0.29.1` and `torch==2.4.1` and
declares `requires-python = ">=3.8,<3.11"`. Two notes:

* The `gymnasium` pin matters. `ppo.py`'s logging branch reads
  `if "final_info" in infos:` and iterates `infos["final_info"]` — the pre-1.0
  vector-env contract. Gymnasium 1.x changed autoreset semantics and that key's shape.
  Pinning 0.29.1, as upstream already does, avoids it; a floating `gymnasium` would
  not.
* The `requires-python` ceiling applies to installing the **`cleanrl` package**. Since
  `ppo.py` is standalone and the package is never installed, it is not binding on the
  script. It ran on Python 3.12.10 with `torch==2.7.0` without modification. Metric
  *values* are not claimed to be bit-identical across that substrate — only that the
  metric is computed and the agent converges, which it does.

**Bare-clone check.** Before spending anything, the exact recorded command was run
from a fresh clone in a scratch venv containing only the expected pins, with
`PYTHONPATH` unset and **no credentials of any kind**: exit 0, model written. No
`ModuleNotFoundError`. This is the check that decides whether a row can ever be
rebuilt by a stranger, and CleanRL passes it without help.

**Cost.** $0.10 total across two attempts. The first attempt trained correctly and was
lost to harness configuration on my side, not to anything in the upstream repo; the
fix is described in `issues.md` and the second attempt was clean.

## Would a competent stranger rebuild this?

**Yes, in well under an hour**, working only from the README and the PPO docs page.
The single-file design removes nearly every failure mode this campaign exists to
measure. The only thing they would not get is a **saved model** — they would finish
with TensorBoard scalars and no weights, and would have to notice that themselves.
