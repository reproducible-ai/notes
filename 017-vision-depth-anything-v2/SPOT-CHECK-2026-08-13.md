# Independent spot check · 2026-08-13

This is supplemental evidence. It does not replace the row's original capture or certification history.

| field | evidence |
|---|---|
| attributed DAG | `74bdd85f01ee05c67b08656a55f7bd595d427abadd736f199da783564ddfee5a` |
| source commit | `1169b2de2d84e363fe3c740aeec20a59facb7709` |
| Tier 1 | PASS — 14/14 checks; AI-BOM 100/100 |
| Tier 2 | PASS — cold reproduction exited 0; 3/3 steps; all recorded outputs regenerated |
| roar build | 0.4.4rc7; wheel sha256 `7f5321965766eb27462b2931b7961eaf48742109a74f5aa5194a4ba9492f988a` |
| reconstruction host | g4dn.xlarge; NVIDIA T4; AMI `ami-0f07f1a0b382b48f7` |
| package check | 44/44 recorded packages present at exact versions |
| certification cost | approximately $0.19 |
| teardown | instance termination confirmed |

Capture-agent, Tier-1-QA, and certifier identities were not all retained at exact version granularity and are not inferred.
