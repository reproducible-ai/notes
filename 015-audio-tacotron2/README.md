# Tacotron 2 (NVIDIA) — LJ Speech, 101 of 390,500 optimiser steps

The campaign had no speech synthesis. Every row through 014 consumes data and
emits a label, a token, an image, an action or a radiance field. Tacotron 2 emits
a **mel spectrogram**: a sequence-to-sequence model that reads characters and
produces, frame by frame, the 80-band time–frequency picture of a voice saying
them. It is autoregressive over frames rather than over tokens, its attention is
monotonic rather than free, and its stop condition is a learned per-frame gate
rather than an end-of-sequence symbol. Nothing else in the list has that shape.

`NVIDIA/tacotron2` is the reference PyTorch implementation of *Natural TTS
Synthesis by Conditioning WaveNet on Mel Spectrogram Predictions*, BSD-3-Clause,
5,295 stars, last pushed June 2024. It has a real `train.py` — not a library, not
a CLI wrapper around a config framework — which is why it was chosen over several
higher-starred candidates.

It is also the oldest code in the campaign. `requirements.txt` pins
`tensorflow==1.15.2`, `librosa==0.6.0`, `numpy==1.13.3`, `scipy==1.0.0`,
`matplotlib==2.1.0`, `inflect==0.2.5` and `Unidecode==1.0.22`. Not one of those
installs on a current interpreter. **The row's finding is that "unmodified
upstream source" and "modern dependency stack" are compatible here, but only
inside a narrow window that four separate library removals define — and that
nothing in the recorded package list tells you the window exists.**

## What ran

Four steps on a single T4. Zero lines of upstream source changed; the harness is
additive, under `repro/`, and a per-run check proves the claim by git blob hash.

1. **`fetch_ljspeech`** (5m05s) — the LJ Speech corpus (2,748,572,632 bytes,
   13,100 utterances, ~24 hours of a single speaker), fetched from the dataset's
   own URL as a SHA-256-pinned step and extracted into `DUMMY/`. 23.0 s to
   download at 119 MB/s, 7.5 s to hash, 242.2 s to extract. 13,102 outputs.
2. **`train`** (7m05s) — upstream's `train.py`, entered through a wrapper that
   caps the number of batches its DataLoader yields. 101 optimiser steps at
   batch 16, two full validation passes over upstream's 100-utterance validation
   filelist, two checkpoints. 1,734 recorded inputs, 71 recorded pins.
3. **`label`** / **`publish`** (1s / 1m49s) — artefact labels and the 338 MB
   upload.

The artefact is `outdir/checkpoint_100` — 338,429,486 bytes, sha256
`b91b446b9c5265b28f16985a080849b986556991b2f248f36738391f5f0b28f8` — a dict of
`iteration`, `state_dict`, `optimizer` and `learning_rate`, which is what
upstream's `save_checkpoint` writes.

The run is deterministic across hosts: `hparams.py` seeds at 1234, and an
earlier, complete attempt on a different machine produced training loss
`49.424385` at step 0 and validation loss `36.168822`/`36.168824` — the same
numbers to five decimal places.

### Why the dataset directory is called `DUMMY`

Upstream's filelists ship with the literal path `DUMMY/LJ001-0001.wav`, and
step 5 of its README tells you to fix that with

```
sed -i -- 's,DUMMY,ljs_dataset_folder/wavs,g' filelists/*.txt
```

That `sed` edits three published files — and those three files *are* the
published train/validation/test split, 12,500 / 100 / 500 utterances, the only
record of which utterance belongs where. Rewriting them to reproduce the model
would mean the row could no longer claim to have used upstream's split.

So this row satisfies the path in the other direction: it extracts the corpus
into a directory literally named `DUMMY`, and the filelists resolve with no edit.
The fetch step then asserts it, and the assertion is worth more than the trick:
it opens all three filelists and checks that **every one of the 13,100 audio
paths resolves**, with the filelists byte-identical to NVIDIA's.

## The four ceilings, and why a freeze cannot warn you about them

Upstream's pins do not install, so the row runs against modern releases. But
"modern" is not "newest": four upstream lines stop working at four specific
library versions, and every one of them is a *removal*, not a deprecation.

| pin | forced by | what happens above it |
|---|---|---|
| `librosa==0.9.2` | `layers.py:50` calls `librosa.filters.mel(sr, n_fft, n_mels, fmin, fmax)` positionally; `audio_processing.py:50` and `stft.py:67` call `pad_center(x, size)` positionally | librosa 0.10 made all of those keyword-only → `TypeError` on the first line of dataset construction |
| `setuptools==79.0.1` | librosa 0.9.2 does `from pkg_resources import resource_filename` (`librosa/util/files.py:10`) | setuptools 84 removed `pkg_resources` → `import librosa` dies with `ModuleNotFoundError: No module named 'pkg_resources'`, and nothing anywhere names setuptools as the cause |
| `numpy==1.26.4` | `plotting_utils.py:9` calls `np.fromstring(..., sep='')` | numpy 2.0 removed the binary mode → `ValueError: The binary mode of fromstring is removed` |
| `matplotlib==3.9.4` | `plotting_utils.py:9` also calls `fig.canvas.tostring_rgb()` | matplotlib 3.10 removed it → `AttributeError` |

The last two are the interesting ones, because of *when* they fire.
`plotting_utils` is reached only from `logger.log_validation`, which runs only at
a checkpoint. On the campaign's stock image — numpy 2.4.4 — this row would train
perfectly for as long as you like and then die at the first validation pass, on a
GPU, with a numpy error in a plotting helper. The failure is minutes and dollars
away from its cause.

None of this is visible in a recorded environment. A freeze lists
`librosa==0.9.2` and `numpy==1.26.4`; it does not say *ceiling*. Rebuild from the
freeze and it works; rebuild from `requirements.txt`, or from "the same libraries,
current versions", and it does not. The reproducible artefact here is the pin
set, and the pin set is a discovery, not a transcription — which is why this row
carries `repro/preflight_cpu.py`, ten assertions that execute each of those
upstream calls for real, on CPU, in a few seconds, before any GPU is billed.

## The TensorFlow that isn't there

`hparams.py` — upstream's configuration file, and the only place the model's
hyperparameters are written down — begins `import tensorflow as tf` and builds
its config with `tf.contrib.training.HParams`. `tf.contrib` was deleted in
TensorFlow 2.0 and `HParams` has no successor anywhere in the TensorFlow API;
`tensorflow==1.15.2` publishes wheels for CPython 3.5–3.7 only. So there is no
TensorFlow, old or new, that makes this file import on a current interpreter.

Rewriting `hparams.py` was not an option — it is precisely the file whose
contents this row wants to be able to claim are NVIDIA's. Hard-coding the values
in the harness was worse: the row's published "untruncated default" would then be
a number an operator typed rather than one read from upstream's config.

`repro/tf_hparams_shim.py` supplies the one missing container — an attribute bag
with TF 1.x's `parse()` grammar for `--hparams=name=value` — registers it in
`sys.modules` as `tensorflow`, lets upstream's `hparams.py` execute byte-for-byte
as published, and **withdraws it again immediately**.

The withdrawal is not tidiness. TensorBoard probes for TensorFlow at import time:
`torch/utils/tensorboard/_embedding.py:10` evaluates
`_HAS_GFILE_JOIN = hasattr(tf.io.gfile, "join")` against whatever `import
tensorflow` returns, and routes all of its file IO through `tf.io.gfile` if it
finds one. A shim that answers the import but has no `io` attribute therefore
turns `train.py`'s logger into

```
AttributeError: module 'tensorflow' has no attribute 'io'
```

before argument parsing. This row hit that twice, both times for free: once on
CPU in a narrow probe, and once — after the narrow probe had been fixed and
passed — in the bare-clone run of the *whole* recorded command, because the two
imported the same modules in a different order. The second is the lesson worth
keeping: **a check that exercises part of the recorded command can pass while the
command fails.**

## Truncation

Upstream's `hparams.py` sets `epochs=500` over a 12,500-utterance filelist.
At this row's batch size that is 500 × 781 = **390,500 optimiser steps**; at
upstream's default batch size of 64 it is 500 × 195 = 97,500. Either way it is
days of single-GPU time. This row runs **101 steps**.

Three numbers shorten it and only one of them is this row's invention:

- `epochs=1` and `iters_per_checkpoint=100` go through upstream's own `--hparams`
  flag. The checkpoint interval matters more than it looks: upstream writes
  checkpoints only inside the `iteration % iters_per_checkpoint == 0` branch, and
  its default of 1000 is larger than this whole run — leave it alone and the run
  finishes having written nothing to publish.
- `batch_size=16`, also upstream's own flag, is a hardware fact rather than a
  preference. Tacotron 2 unrolls a 1024-wide decoder LSTM over every mel frame of
  the longest clip in the batch (760 frames in the first batch here), and 64 of
  those does not fit in a T4's 16 GB. NVIDIA trained this on V100s.
- `--train-iters 101` is the harness's, and it is in the recorded argv, so the
  lineage states the truncation on its face.

`train.py` exposes no way to stop early: its loop is
`for epoch in range(...): for i, batch in enumerate(train_loader):`, so the only
lever that does not touch the file is the length of `train_loader`. The harness
wraps it in an object that yields 101 batches and proxies everything else. The
model, the loss, the optimiser, the gradient clipping, the validation pass, the
TensorBoard logging and the checkpoint writer are all upstream's, untouched.

101 steps is not convergence and is not claimed to be. It is enough to show the
pipeline works end to end: training loss falls 49.42 → 3.00 and validation loss
36.17 → 5.19 over the run, and the attention alignment is still noise —
Tacotron 2's attention typically takes tens of thousands of steps to become
monotonic, which is the point at which the model starts producing intelligible
speech. The first optimiser step takes 46.45 s (CUDA context and cuDNN
autotuning); the remaining hundred average **2.891 s** (min 2.54, max 3.15), and
each validation pass over the 100-utterance filelist costs 34.1 s.

## One deliberate change to how upstream loads data

`train.py:55` hardcodes `num_workers=1`, so mel-spectrogram computation happens in
a forked child. The harness forces `num_workers=0` and says so in the recorded
argv (`--dataloader-workers 0`).

The reason is provenance, not performance. Imports made in a forked worker are
attributed to that process, and a workload whose libraries are imported in a
worker can record a package list missing most of what it used — a record that
looks complete and rebuilds only by luck. It costs nothing here: the mel pipeline
was measured at **0.015 s per utterance**, so the GPU decoder dominates the step
either way, and the same batches are produced in the same order by the same code.

## Native libraries: the pip-closure boundary this row was chosen to map

The audio stack is where a pip freeze is supposed to stop being sufficient:
`librosa` → `soundfile` → **libsndfile**, plus `audioread`, plus `numba` →
`llvmlite` → LLVM. `repro/native_deps_probe.py` imports what the workload
imports, reads `/proc/self/maps`, and sorts every mapped `.so` into three
buckets: inside a wheel, outside a wheel but owned by a dpkg package, and owned
by nothing at all.

On the campaign image, of **335 native libraries mapped into the process**:

- **276 are inside wheels.** That includes
  `_soundfile_data/libsndfile_x86_64.so` — libsndfile 1.2.2, shipped *inside* the
  `soundfile` wheel. The feared libsndfile OS dependency does not exist on a
  modern `soundfile`; the freeze covers it. `audioread` never loads a native
  library at all on this path, because `utils.load_wav_to_torch` reads wavs with
  `scipy.io.wavfile`, not with librosa.
- **5 are dpkg-owned**: `libssl3` (libcrypto, libssl), `libffi8`, `libstdc++6`,
  `libuuid1`. These are the ones an OS-package inventory can express.
- **53 are owned by no dpkg package whatsoever.** Not edge cases: `libc.so.6`,
  `ld-linux-x86-64.so.2`, `libm`, `libpthread`, `libdl`, `libgcc_s`, `libz`,
  `libbz2`, `liblzma`, **all 41 CPython standard-library extension modules** under
  `/usr/local/lib/python3.12/lib-dynload/`, and `libcuda.so.580.126.09`, the
  NVIDIA driver.

That last bucket is the finding. Row 012 reported that `libGL`/`libGLX`/
`libGLdispatch` were libglvnd files installed outside apt by the NVIDIA driver
bundle and so could never enter a dpkg-derived record. This row shows that was
not a special case: on this image the *majority* of non-wheel libraries — the C
runtime and the Python interpreter's own extension modules included — are outside
the package manager. Any inventory built from `dpkg` can describe 5 of the 58
non-wheel libraries this workload loads. **The gap is structural, and it is
larger than one driver.**

For this row it happens not to bite, because the one dependency that would
normally cross the boundary — libsndfile — travels inside its wheel. That is
worth stating precisely: *this* row is pip-closed, and it is pip-closed by an
upstream packaging decision made by the `soundfile` maintainers, not by anything
the record could guarantee.

## What is in the record, and what a rebuilder still has to know

Everything above lives in the fork: the pins are in the workflow with the line
numbers that force them, `repro/preflight_cpu.py` fails loudly if any ceiling is
wrong, `repro/assert_upstream_unmodified.py` fails if an upstream file moves, and
`repro/native_deps_probe.py` prints the library boundary into the run's own log.

The training step's recorded package list has **71 pins** and an
imports-versus-freeze audit finds **zero Tier-A misses**: `torch`, `numpy`,
`scipy`, `librosa`, `matplotlib`, `numba`, `llvmlite`, `soundfile`, `audioread`,
`resampy`, `scikit-learn`, `pooch`, `inflect`, `Unidecode`, `tensorboard` and
`setuptools` are all present, which is the set that actually matters here. Four
lazily-imported hints are absent — `requests`, `idna`, `charset-normalizer`,
`huggingface-hub` — consistent with a recorder that captures what was *loaded*:
`pooch` imports `requests` only when it downloads something, and this workload
never makes it.

It is also, in the other direction, **thicker than the workload**: 22 of the 71
pins are packages Tacotron 2 never imports — `boto3`, `botocore`, `s3transfer`,
`jmespath`, `paramiko`, `PyNaCl`, `bcrypt`, `invoke`, `google-auth`, `psutil`,
`pandas`, `pyarrow`, `pytz`, `cloudpickle`, `dill`, `tabulate`, `wcwidth`,
`defusedxml`, `brotli`, `zstandard`, `backports.tarfile`, `platformdirs`. That
set is an AWS-plus-SSH-plus-dataframe stack, i.e. the machinery of the machine
rather than of the model, and none of it belongs to any other model this campaign
has built. A thick freeze installs fine and does not block a rebuild, but it is
worth saying out loud that a recorded package list is evidence of what a *host*
had loaded, not a statement about what a workload needs.

The dataset step records nine packages, which is the recording tool's own
closure and is **correct** for that step rather than a gap: an AST parse of the
exact file it ran shows `repro/fetch_ljspeech.py` imports `__future__`,
`argparse`, `hashlib`, `os`, `shutil`, `sys`, `tarfile`, `time` and `urllib` —
nothing outside the standard library — with no `__import__`, `importlib`, `exec`
or `subprocess` anywhere to hide one. A step with no third-party imports has no
third-party pins to record.

What the environment cannot carry is the *reason* for the pins, and that is the
honest answer to "can a stranger rebuild this?". A freeze can tell you
`librosa==0.9.2` and `numpy==1.26.4` were installed. It cannot tell you that both
are ceilings rather than coincidences, that setuptools is load-bearing, or that
53 of the libraries the process mapped are outside every package manager on the
box. That is why the ceilings are written into the workflow next to the upstream
line numbers that force them, rather than left to the freeze to imply.

## Experiment logging

`experimentUrl` is **null**, and the reason is stated rather than defaulted to.

Upstream ships TensorBoard and only TensorBoard. `grep -ri 'wandb\|mlflow\|comet\|neptune'`
over the whole tree returns nothing. What it does have is real and wired up:
`logger.py` subclasses `torch.utils.tensorboard.SummaryWriter`, `train.py` calls
`log_training` every iteration (`train.py:242`) and `log_validation` at every
checkpoint (`train.py:147`), and this run wrote scalars, per-parameter histograms
and three matplotlib figures — alignment, target mel and predicted mel — into
`outdir/logdir`. TensorBoard is not bridged to trackio, so no experiment URL can
come from it, and adding a `wandb.init()` to `train.py` to manufacture one would
modify the workload and forfeit the only property that makes this row worth
reading. So there is no link, and there is no logging flag left unpressed.
