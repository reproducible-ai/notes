# Independent spot check · 2026-08-13

This is supplemental evidence. It does not replace the row's original capture or certification history.

| field | evidence |
|---|---|
| attributed DAG | `b77b47626346bffc7477b72d90a50858ea8c500f88a65775cc5c3184eb380679` |
| source commit | `660fdc2cf9f8b9ae80d41bdbcf5df557a3294fac` |
| Tier 1 | PASS — 14/14 checks; AI-BOM 100/100 |
| Tier 2 | PASS — cold reproduction exited 0; 1/1 step |
| roar build | 0.4.4rc7; wheel sha256 `7f5321965766eb27462b2931b7961eaf48742109a74f5aa5194a4ba9492f988a` |
| reconstruction host | g4dn.xlarge; NVIDIA T4; AMI `ami-0f07f1a0b382b48f7` |
| recorded pins | 7/7 present at exact versions |
| model output | `out/adder/model.pt`, 358,331 bytes, sha256 `9d870b6107d9cb93ef8d7f65adad32c05a7d9146c2c352a9e9957a5157ece607` |
| config output | `out/adder/config.json`, 672 bytes, sha256 `2cf6fca96c75504c67f4939e7d84cce3e555769d292daa264fe57d574baac427` |
| certification time and cost | approximately 8m38s and $0.08 |
| teardown | instance termination confirmed |

The certifier was a fresh Codex agent configured as `gpt-5.6-luna`. Exact capture-agent and Tier-1-QA identities were not retained and are not inferred.
