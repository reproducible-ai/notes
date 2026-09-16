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
| certification attempt 1 | exit 143; operator-stopped after base training; incomplete | $13.25 |
| certification attempt 2 | exit 143; budget stop during SFT; incomplete | $23.39 |
| certification attempt 3 | exit 1; Steps 4/5 after the base command completed twice; final package regenerated, outer reproduction failed | $25.73 |
| certification attempt 4 | exit 0; all 5 reproduction steps completed | $17.94 |
| **Total certification effort** |  | **$80.31** |
| **Cumulative capture, rebuild, and certification** |  | **$177.28** |

The final instance stopped after 351 billed minutes. The stopped-instance meter, used above, was $19.66.

Certification attempts 1–4 totaled $80.31. Certification spend is reported
separately from the $96.97 capture and rebuild effort; together they reconcile to
$177.28.

The successful certification host ran for 5h19m52s, including setup and evidence
collection, for an estimated $17.94. Its host was confirmed terminated after
evidence collection.
