# Reproducible AI Campaign — notes

Per-model reproduction notes for the [Reproducible AI Campaign](https://treqs.ai/models):
every obstacle, patch, command, and cost from each rebuild attempt. Written as the
work happens, in a factual tone — blockers describe ecosystem gaps, never author
competence.

Playbook and protocol: [`reproducible-ai/playbook`](https://github.com/reproducible-ai)
(public edition). This repo is the evidence behind each published row.

## Layout

```
NNN-<vertical>-<model-slug>/     one directory per model (NNN = zero-padded sequence)
  README.md      verdict + one-paragraph summary (kept current), then the narrative
  issues.md      every obstacle: symptom, root cause, fix/workaround, upstream-worthy?
  commands.md    the command sequence that constitutes the recipe
  costs.md       attempts, per-attempt wall-clock + cost, total burn, final-rebuild cost
  patches/       diffs vs upstream
  row.json       the exact object published to the /models table
_survey/         survey.json — the dated snapshot categorization of the whole source list
_slate/          candidates.md — human-readable slate/candidate tables
```

Example directory name: `003-robotics-diffusion-policy`.

## Status

Private during in-progress work; individual rows and their notes flip public at
publication (pilot notes stay private until the playbook reaches v1.0). Licensed
**CC-BY-4.0** (see `LICENSE`).
