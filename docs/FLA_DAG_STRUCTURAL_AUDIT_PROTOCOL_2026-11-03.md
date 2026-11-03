# Read-only DAG structural audit protocol — 2026-11-03

Purpose: use **actual parsed Pegasus DAX nodes and edges** rather than filename tokens. On the frozen v17 confirmation archive, `Epigenomics_46.xml` is in fact **47** jobs; `Sipht_100.xml` is **97**, and `Sipht_60.xml` is **58**. Counts are crossed against `jobCount` and actual `<job>` elements. This resolves sample-size descriptions, not any changed simulator outcome.

The analyzer is separate from the optimizer. It reads DAX XML but does NOT invoke WorkflowSim, target fitness evaluation, VM optimizers, random numbers, or Github network. It rejects missing/duplicate jobs, missing dependency refs, duplicate edges, cycles, and malformed graph references. It explicitly FLAGS discrepant jobCount/childCount header attributes rather than silently using incorrect metadata. For negative or otherwise invalid runtime values, the topology survives, but all runtime-derived features for that DAX are **blank** and the invalid count is recorded. Negative/invalid file sizes are excluded from any logical-byte aggregation and counted explicitly; no absolute-value or zero-byte imputation is made.

The deterministic descriptors are root/sink counts, real parsed task and edge counts, join/fork tasks, longest dependency path in levels, longest path by **DAX-provided unscaled runtimes** (only if all runtimes valid), critical-runtime share, work/span ratio, maximum topological layer width, and edge overlap of referenced output/input file names.

**Do not interpret** DAX file sizes as observed inter-VM network communication; a repeated file can be cached and on the same VM. `declared_intertask_file_bytes` sums VALID producer output sizes on each dependency edge with a common input filename, is a *logical edge-file-volume proxy*, and can count one file on multiple fanout edges. DAX runtime-weighted critical path is NOT a calibrated WorkflowSim time bound because VM speeds and transfer/storage costs differ.

## Verified current data anomalies and evidence

The [successful Actions structural audit 41630971648](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41630971648) inspected all **22** DAX XML files and ran **eight** parser regression tests. Source-level deterministic output retained in `fla-dax-structure-41630971648` artifacts.

- `HEFT_paper.xml`: header declares 25 jobs and 20 child blocks, actual XML contains 10 jobs and 9 child blocks; both discrepancies remain visible in the feature CSV.
- `Epigenomics_997.xml`: 997 valid graph tasks, but **57 invalid runtime values** and **209 invalid file-size references**. Its DAG topology can be audited, but source-runtime critical path and work/span statistics are unavailable.
- `Sipht_1000.xml`: 968 actual tasks, not 1000; `Sipht_100.xml`: 97 actual tasks; `Sipht_60.xml`: 58; `Sipht_30.xml`: 29; `Epigenomics_46.xml`: 47.

The first two attempted full audits had failures from test precision and exceptional DAX metadata and were corrected transparently. Earlier failure runs are part of the engineering audit trail: 41630238570, 41630355878, 41630621761, 41630801770. These failures were in the new analysis tool, not proof the FLA fitness engine failed.

## Research interpretation and leakage guard

The confirmed read-only [v17–structure join run 41631164374](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41631164374) successfully merged the structural CSV with frozen true-simulator K16 outcomes in confirmation Actions 41626382711. No new simulator calls or optimizer target evaluations were made. The merged data is descriptive, not a new confirmation cohort.

For the four confirmation DAX files, the fraction of tasks with no incoming dependencies is about `0.043` in Epigenomics_46, `0.240` in Inspiral_50, `0.080` in CyberShake_100 and `0.753` in Sipht_100. The relatively favorable v17 result in heterogeneous Sipht is a retrospective association only. DAG family, topology, scale, execution times and VM speed regime confound one another. Do **not** pick root fraction, a join count or another after-the-fact threshold on this observed result set and present it as independently validated.

The next credible validation requires selecting and freezing **new, truly independently generated DAG topology families and seeds** BEFORE running FLA and NSGA-II candidate simulations. For synthetic workflows, be explicit that they are synthetic and not an unseen scientific application family. Report total runtime, planned/actual simulator discrepancy and the same fixed K16 real HV; preserve all negative cases. The parser alone cannot establish a publishable v17 advantage.
