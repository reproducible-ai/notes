# Pre-flight: everything that was decided on CPU, for $0, before a GPU was booked

This row spent no GPU time discovering anything. The whole dependency window, the
TensorFlow substitution, the dataset layout and the extraction strategy were
settled on a 4-core control host, and two real defects were found there — one of
which would have killed a paid run minutes after training had already succeeded.

## 1. Upstream, as published, does not import

`hparams.py:1` is `import tensorflow as tf` and `hparams.py:8` is
`tf.contrib.training.HParams(...)`. `tf.contrib` was deleted in TensorFlow 2.0.
`requirements.txt` pins `tensorflow==1.15.2`, which publishes wheels for CPython
3.5–3.7. The campaign image runs CPython 3.12.10.

Resolution: `repro/tf_hparams_shim.py` provides `tf.contrib.training.HParams` and
`tf.logging`, registered as `tensorflow` only while upstream's `hparams.py` is
imported. Verified to read upstream's real values:

```
PASS  upstream hparams.py (via the TF shim): epochs=500 batch_size=64
      iters_per_checkpoint=1000 n_symbols=148
PASS  --hparams= override grammar: epochs=1 batch_size=16 types preserved
```

`epochs=500` is where this row's `truncation.full` comes from. It is read, not
typed.

## 2. Four library ceilings, each found by executing the upstream call

```
FAIL  plotting_utils (matplotlib tostring_rgb + np.fromstring):
      ValueError: The binary mode of fromstring is removed, use frombuffer instead
```

with numpy 2.4.4, the image's own version. `plotting_utils.py:9` is reached from
`logger.log_validation`, which runs at every checkpoint — so on the stock image
this row trains correctly and dies at the first validation, on a GPU. Pinned
`numpy==1.26.4` (and `scipy==1.17.1`, forced by it: scipy 1.18 requires numpy≥2).

```
ModuleNotFoundError: No module named 'pkg_resources'
```

with setuptools 84.0.0: `librosa==0.9.2` does `from pkg_resources import
resource_filename` at `librosa/util/files.py:10`, and setuptools 84 removed
`pkg_resources`. Nothing in that traceback names setuptools as the cause. Pinned
`setuptools==79.0.1`.

librosa ≥0.10 makes `filters.mel` and `util.pad_center` keyword-only, which
breaks `layers.py:50`, `audio_processing.py:50` and `stft.py:67`. Pinned
`librosa==0.9.2`, which accepts the positional form with a `FutureWarning`:

```
layers.py:50: FutureWarning: Pass sr=22050, n_fft=1024, n_mels=80, fmin=0.0,
fmax=8000.0 as keyword args. From version 0.10 passing these as positional
arguments will result in an error
```

matplotlib 3.10 removed `FigureCanvas.tostring_rgb()`, also `plotting_utils.py:9`.
Pinned `matplotlib==3.9.4`.

All ten checks pass under the final pin set:

```
PASS  upstream hparams.py (via the TF shim)
PASS  --hparams= override grammar
PASS  librosa positional mel filterbank (layers.TacotronSTFT): mel_basis (80, 513)
PASS  mel spectrogram of a waveform: mel (1, 80, 173) range [-11.51, 1.44]
PASS  STFT.inverse -> librosa.util.pad_center: round trip (1, 1, 22016)
PASS  text_to_sequence with english_cleaners (inflect + unidecode): 88 symbol ids
PASS  scipy.io.wavfile.read (utils.load_wav_to_torch): (22050,) @ 22050 Hz
PASS  plotting_utils (tostring_rgb + np.fromstring): alignment (400, 600, 3) ...
PASS  import train.py itself, with the shim already withdrawn
PASS  logger.Tacotron2Logger (torch.utils.tensorboard): 1 event file(s) written
preflight_cpu: PASS
```

## 3. The bare-clone check, and the bug only it could find

Fresh clone of the pushed fork, a scratch venv holding only the pins expected to
be recorded (plus a CPU-only torch), `env -u PYTHONPATH`, and the exact recorded
`train` argv.

The narrow probe above passed. The whole command did not:

```
File ".../train.py", line 16, in <module>
    from logger import Tacotron2Logger
File ".../logger.py", line 3, in <module>
    from torch.utils.tensorboard import SummaryWriter
File ".../torch/utils/tensorboard/_embedding.py", line 10, in <module>
    _HAS_GFILE_JOIN = hasattr(tf.io.gfile, "join")
AttributeError: module 'tensorflow' has no attribute 'io'
```

TensorBoard probes for TensorFlow at import time and routes its file IO through
`tf.io.gfile` if `import tensorflow` succeeds. The shim made it succeed. The
probe had passed only because it happened to withdraw the shim before importing
`logger`, and the real entry point did not.

Fixed by ordering: install the shim, import `hparams`, withdraw the shim, import
`train`. `preflight_cpu.py` gained the check that would have caught it — it
imports `train.py` itself and asserts `tensorflow` is absent from `sys.modules`.

After the fix, the exact recorded command runs to the first line that genuinely
needs a GPU and stops there:

```
File ".../train.py", line 74, in load_model
    model = Tacotron2(hparams).cuda()
AssertionError: Torch not compiled with CUDA enabled
```

Zero `ModuleNotFoundError`. The model constructs; only `.cuda()` fails, on a
CPU-only torch. (The workload cannot be run further off a GPU:
`utils.get_mask_from_lengths` builds a `torch.cuda.LongTensor` unconditionally.)

## 4. Upstream is unmodified, proved by blob hash

```
upstream: https://github.com/NVIDIA/tacotron2 @ 185cd24e046cc1304b4f8e564734d2498c6e2e6f
upstream files: 32  |  files in HEAD: 44
added by this fork (12): .gitignore, .treqs/workflows/..., DUMMY/.gitkeep,
  outdir/.gitkeep, repro/*.py
assert_upstream_unmodified: PASS (32 upstream files byte-identical to
  185cd24e046c, 0 declared exemption(s))
```

Zero declared exemptions — including all three `filelists/*.txt`, which upstream's
README asks the reader to rewrite with `sed`.

## 5. The dataset, measured rather than assumed

LJ Speech is 2,748,572,632 bytes, sha256
`be1a30453f28eb8dd26af4101ae40cbf2c50413b1bb21936cbcdc6fae3de8aa5`, served with
`Last-Modified: Mon, 19 Feb 2018`.

The first extraction implementation ran at 800 files/min and slowing. The cause
is worth recording: `tarfile` opened seekably (`r:bz2`) reads a member header,
advances, then seeks *backwards* to the member's data when `extractfile()` is
called — and `bz2.BZ2File` implements a backward seek by rewinding and
re-decompressing from byte zero. Extracting 13,100 members that way is quadratic.
Stream mode (`r|bz2`) is forward-only: **250.3 s** on the campaign host for the
whole corpus.

Mel-spectrogram throughput was measured on real LJ Speech audio at **0.015 s per
utterance** (16 utterances in 0.24 s), which is what establishes that the GPU
decoder, not the data pipeline, sets the step time — and therefore that forcing
`num_workers=0` for provenance costs nothing.
