# Costs

| Attempt | Outcome | Cost |
|---|---|---:|
| depth-16 hardware setup | aborted before training | $1.07 |
| depth-16 hardware control | aborted before training | $1.01 |
| depth-16 calibration | projected 5.40 h; stopped at ceiling | $1.01 |
| depth-14 initial full horizon | stopped during SFT at spend cap | $13.72 |
| depth-14 complete workload | artifact uploaded; no lineage produced | $19.83 |
| depth-14 recorded | all tasks and lineage completed | $19.72 |
| roar 0.4.6 capacity attempt | no instance launched | $0.00 |
| roar 0.4.6 setup assertion | stopped during setup | $1.18 |
| roar 0.4.6 recorded | all 13 tasks and lineage completed | $19.77 |
| roar 0.4.7 recorded | all 13 tasks and lineage completed | $19.66 |
| **Total rebuild effort** |  | **$96.97** |
| independent Tier-2 certification | stopped after base training when projected completion exceeded certification NTE | $13.25 |

The final instance stopped after 351 billed minutes. The stopped-instance meter, used above, was $19.66.

The independent certification host ran for 3h56m21s at $3.363/hour, for an estimated $13.25. Certification spend is reported separately from capture and rebuild effort.
