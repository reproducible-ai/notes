# Upstream findings — `pytorch/vision` `references/classification`

Findings against [`pytorch/vision`](https://github.com/pytorch/vision) at
`34572106ad1f0ea95793e379751f8bb0cfeeac1c`. Nothing here was reported upstream; a
prepared patch for #1 is in `patches/`.

Two of the five are genuine bugs that make documented flags fail. The rest are
foot-guns that cost time before a single image is classified.

---

## 1. `--resume` cannot read a checkpoint `train.py` itself wrote (PyTorch ≥ 2.6)

**Severity: bug. The documented resume and `--test-only` paths are both broken.**

`train.py` writes its own argparse namespace into every checkpoint:

```python
# references/classification/train.py:374
checkpoint = {
    "model": model_without_ddp.state_dict(),
    "optimizer": optimizer.state_dict(),
    "lr_scheduler": lr_scheduler.state_dict(),
    "epoch": epoch,
    "args": args,          # <-- an argparse.Namespace
}
```

and reads it back with `weights_only=True`:

```python
# references/classification/train.py:341
if args.resume:
    checkpoint = torch.load(args.resume, map_location="cpu", weights_only=True)
```

PyTorch 2.6 flipped the default of `weights_only` to `True` and the code was updated to
pass it explicitly — but the *writer* was not changed to stop pickling a `Namespace`.
`argparse.Namespace` is not an allowed global, so the load raises:

```
_pickle.UnpicklingError: Weights only load failed.
  WeightsUnpickler error: Unsupported global: GLOBAL argparse.Namespace was not an
  allowed global by default.
```

Reproduced on torch 2.7.0 against a checkpoint produced by `train.py` itself, minutes
earlier, on the same machine. Every `--resume` and every `--test-only --resume`
invocation in `references/classification/README.md` hits this. It is a self-inflicted
round-trip failure: the only producer of these files is the only consumer of them.

Two clean fixes, either sufficient:

- **stop writing `args`** — it is never read back (line 341–351 loads `model`,
  `optimizer`, `lr_scheduler`, `epoch`, `model_ema`, `scaler`, never `args`); or
- **allow-list it at the load site** with
  `torch.serialization.safe_globals([argparse.Namespace])`.

The first is better — `args` is dead weight in the file — but it breaks anyone reading
`args` out of an existing checkpoint. The prepared patch takes the second, conservative
route. See `patches/0001-resume-weights-only.patch`.

Note the file already carries `# TODO: this could probably be weights_only=True` on the
*dataset cache* loads at lines 130 and 163, so the tension was noticed in one place and
missed in the other.

## 2. `--epochs 1` with the default warmup is unrunnable

**Severity: bug (crash on a plausible flag combination).**

```python
# references/classification/train.py:293
main_lr_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
    optimizer, T_max=args.epochs - args.lr_warmup_epochs, eta_min=args.lr_min
)
```

`T_max` is `epochs - lr_warmup_epochs`, unguarded. Every ImageNet recipe in the README
uses `--lr-warmup-epochs 1` (or 5), so `--epochs 1 --lr-warmup-epochs 1` gives
`T_max=0` and the schedule cannot be constructed. `--epochs 1` is the first thing anyone
types to check the pipeline works, and warmup is on in the copy-pasteable command right
above it. A one-line `max(1, ...)` — or an explicit argparse error saying
`--epochs must exceed --lr-warmup-epochs` — turns a confusing traceback into an
instruction.

## 3. Every epoch writes two 89 MB checkpoints, and there is no way off

```python
# references/classification/train.py:385
utils.save_on_master(checkpoint, os.path.join(args.output_dir, f"model_{epoch}.pth"))
utils.save_on_master(checkpoint, os.path.join(args.output_dir, "checkpoint.pth"))
```

The same dict is written twice per epoch, unconditionally, whenever `--output-dir` is
set — and `--output-dir` is also the only way to get *any* checkpoint. A 4-epoch resnet18
run leaves 5 files and 448 MB; the 600-epoch recipes in the README leave 601 files. There
is no `--save-every`, no `--keep-last`, and no way to ask for only the rolling
`checkpoint.pth`. For a reference script whose README recommends multi-hundred-epoch runs
on 8 GPUs this is a real disk cost, and it is invisible until it fills a volume.

Worth recording precisely, because "the same dict written to two names" sounds like it
should produce two identical files and does not: `torch.save` embeds the *output file
stem* as the top-level directory inside the zip archive, so the 190 entries in
`checkpoint.pth` are named `checkpoint/…` and those in `model_3.pth` are named
`model_3/…`. The files are 89,551,113 B and 89,550,031 B respectively and have different
SHA-256s despite identical tensor content. Content-addressed tooling will therefore store
both copies in full.

## 4. The repository root shadows the installed `torchvision`

Running `python -m references.classification.train` from the repository root imports the
**source tree** `vision/torchvision/`, not the installed distribution — so the C
extensions are missing and the import fails. Scripts here must be invoked by **path**
(`python references/classification/train.py`), which also happens to put
`references/classification/` on `sys.path` so the sibling imports (`presets`, `utils`,
`transforms`, `sampler`) resolve. That is the only invocation that works, and neither
`references/classification/README.md` nor the root `README.md` says so; the READMEs show
`torchrun --nproc_per_node=8 train.py`, which implies a working directory nobody states.

## 5. A stale `*.egg-info` reports a version that was never published

If a build has ever run in the worktree, `torchvision.egg-info/` persists and
`importlib.metadata.version("torchvision")` reports `0.29.0a0` (from `version.txt`) —
a version that does not exist on PyPI. Any tooling that records the environment then
captures an uninstallable pin. `rm -rf *.egg-info` before capture is the workaround, but
the underlying issue is that an in-tree `.egg-info` silently outranks the real installed
distribution's metadata.

## 6. Deprecated `torch.cuda.amp.autocast` (cosmetic)

```python
# references/classification/train.py:29
with torch.cuda.amp.autocast(enabled=scaler is not None):
```

Emits `FutureWarning: torch.cuda.amp.autocast(args...) is deprecated. Please use
torch.amp.autocast('cuda', args...)` on every run under torch 2.7. Harmless, but it is
the first thing printed by the flagship reference trainer.
