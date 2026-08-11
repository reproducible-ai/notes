# Issues — Depth Anything V2 (metric depth)

Upstream commit reproduced: `a561b849ebae10a6f5ef49e26c83cbbcd36c71bf`
(`DepthAnything/Depth-Anything-V2`, Apache-2.0, default branch `main`).

Everything below is a finding about the upstream repository or the surrounding
ecosystem. Nothing upstream is criticised for competence: this is a research
codebase that was clearly run on the authors' own cluster, and every gap below is
the ordinary distance between "it runs here" and "a stranger can run it".

---

## 1 · `np.RankWarning` was removed in NumPy 2.0 — hard failure at line 46

**Symptom**

```
File "metric_depth/train.py", line 46, in main
    warnings.simplefilter('ignore', np.RankWarning)
AttributeError: module 'numpy' has no attribute 'RankWarning'
```

**Root cause** `np.RankWarning` was deprecated in NumPy 1.25 and removed in 2.0. The
call is the fourth statement of `main()`, so the trainer cannot reach argument
validation, let alone a batch, on any environment that resolves a current NumPy.

**Fix used** constrain the environment to `numpy<2` (resolved to `1.26.4`) instead of
editing upstream. The recorded package set pins that, so a rebuild gets it.

**Upstream-worthy?** Yes, one line: delete it, or use `np.exceptions.RankWarning`
(available from NumPy 1.25). Not filed — this campaign does not contact upstream.

## 2 · The shipped Hypersim split manifests contain absolute paths on the authors' filesystem

**Symptom** `dataset/splits/hypersim/train.txt` (59,543 lines) and `val.txt` (7,386
lines) consist of pairs like

```
/mnt/bn/liheyang/DepthDatasets/HyperSim/all/ai_001_001/images/scene_cam_00_final_preview/frame.0000.tonemap.jpg \
/mnt/bn/liheyang/DepthDatasets/HyperSim/all/ai_001_001/images/scene_cam_00_geometry_hdf5/frame.0000.depth_meters.hdf5
```

`Hypersim.__getitem__` uses those strings verbatim, and the path to the list itself is
hard-coded in `train.py` (`'dataset/splits/hypersim/train.txt'`) — there is no
`--data-root` and no `--filelist` argument.

**Consequence** the manifests define the split, which is genuinely useful, but they
cannot be *executed* by anyone outside the lab. Any reproduction has to rewrite them,
which means every reproduction rewrites them differently.

**Fix used** keep upstream's two files verbatim under new names
(`upstream_train.txt`, `upstream_val.txt`) and generate `train.txt` / `val.txt` from
them, preserving order and split membership. The same applies to `vkitti2/train.txt`
and `kitti/val.txt`, which were not used here.

**Upstream-worthy?** Yes, and cheaply: accept a root prefix argument, or ship the
lists as repository-relative paths.

## 3 · `metric_depth/requirements.txt` omits two hard dependencies and lists one that is not needed

| package | listed? | who imports it |
|---|---|---|
| `h5py` | **no** | `dataset/hypersim.py` — reads every depth target |
| `tensorboard` | **no** | `train.py` — `torch.utils.tensorboard.SummaryWriter` |
| `open3d` | yes | only `depth_to_pointcloud.py`, never the trainer |
| `matplotlib` | yes | only `run.py` / `depth_to_pointcloud.py` |

Following `metric_depth/README.md` exactly (`pip install -r requirements.txt`) yields
`ModuleNotFoundError: h5py` on the first batch and, once that is fixed,
`ModuleNotFoundError: tensorboard` at `SummaryWriter`.

**Upstream-worthy?** Yes. `open3d` in particular is a heavy dependency for people who
only want to train.

## 4 · The training entry point is distributed-only, with no single-GPU path

`train.py` calls `setup_distributed()` (from `util/dist_helper.py`) unconditionally.
Outside SLURM that function reads `os.environ["RANK"]` and `os.environ["WORLD_SIZE"]`
directly — `KeyError` if absent — and `train.py` then reads `os.environ["LOCAL_RANK"]`
itself. `MASTER_ADDR` / `MASTER_PORT` must already be set: `--port` only takes effect on
the SLURM branch. The only documented launcher is `dist_train.sh`, which hard-codes
`gpus=8`.

A single-GPU run works fine — it just has to be spelled out:

```
RANK=0 WORLD_SIZE=1 LOCAL_RANK=0 MASTER_ADDR=127.0.0.1 MASTER_PORT=29500 python train.py ...
```

**Upstream-worthy?** Mild: default the world size to 1 when the variables are absent, or
document the single-GPU invocation. Not a bug, but it is an undocumented precondition and
the failure mode (`KeyError: 'RANK'`) does not point at it.

## 5 · `num_workers=4` is hard-coded in both DataLoaders

`train.py` builds both loaders with `num_workers=4` and there is no flag. On a 4-vCPU
host that is one worker per core for a 64-image epoch. It did not cost anything here and
the recorded dependency set came out complete regardless (41 distributions on the
training step, including `torch`, `torchvision`, `numpy`, `h5py`,
`opencv-python-headless` and `tensorboard`), but it is a value that anyone truncating
this recipe will want to lower and cannot.

## 6 · Cold-start cost is invisible in the recipe

The identical training step took **204 s on a freshly booted instance** and **13 s on the
same instance once warm** — roughly 110 s of first-CUDA-context and kernel warm-up before
the first batch. Nothing upstream causes this and nothing upstream can fix it, but it
dominates a short run, and a truncated benchmark that quotes the warm number is quoting
the wrong one.

## 7 · Non-issues, checked and cleared

- **Licence**: `Apache-2.0`, confirmed via the GitHub API `spdx_id` rather than the
  README badge.
- **Pretrained weights**: `depth-anything/Depth-Anything-V2-Small` on the Hub is public,
  ungated, Apache-2.0, 99,218,434 bytes. `train.py` keeps only the `pretrained.*` tensors
  from it (175 of them) and trains the DPT head from scratch — as documented.
- **Local-version pins**: none. The recorded environment has no `+cu`-style pins, so
  every recorded distribution resolves from PyPI.
- **`torch.load` without `weights_only`**: `train.py` loads the released checkpoint with
  `torch.load(..., map_location='cpu')`. Under torch 2.7's `weights_only=True` default
  this still works, because the file is a plain tensor `state_dict`. Worth knowing, not a
  defect.
- **xFormers**: `dinov2` prints `xFormers not available` twice and falls back to the
  stock attention path. Harmless.
