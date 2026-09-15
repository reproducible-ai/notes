# Public GR00T canary

A fresh public run completed 100 optimizer steps on the same pinned inputs as the private capture. This addendum preserves the original capture and its audit.

- [Hugging Face checkpoint, pinned revision](https://huggingface.co/reproducible-ai/gr00t-n1-7/tree/ef04eee6429a8ae492cae74d6af2a0dd5dc41a7c/artifacts/droid-canary/checkpoint-100)
- [Public GLaaS training lineage](https://glaas.ai/dag/01c4225ca5c1df31c72153671041cd530fa338dac02259384855b56e0c540c15)
- [Source and supervisor](https://github.com/reproducible-ai/Isaac-GR00T/tree/c084d6eab090a2b5822db474d790a00dfe7fae5d/.treqs)
- TReqs job: `f282527c-4573-4a28-afae-29033e75c4c6`
- Full allocation cost: **$1.57**; compute stopped.
- Final training loss: `0.0912`.

Anonymous downloads matched every manifest size and SHA-256. All 1,030 tensors matched the three-shard index. Anonymous GLaaS reads confirmed each trained weight shard is consumed by PUT. The supervisor performed these checks and published this addendum automatically. This is a training-path canary, with no new model-quality or independent-auditor claim.

Use is limited to non-commercial research/evaluation under the packaged NVIDIA license. See [verification evidence](evidence/public-release.json).
