# Fixed-mapping WorkflowSim original-Task-ID event-chain root-cause audit — 2026-11-03

**Status: completed evidence-backed development mechanism study.** No claim of a novel optimized FLA operator, changed default scheduler, superior HV, or journal-level validation.

## Provenance and experiment
- Frozen before new outcomes: `docs/FLA_FIXED_EVENT_CHAIN_PROTOCOL_2026-11-03.md`, original v17 K16 default-profile mappings from [GitHub Actions 41626382711](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41626382711). Original candidate indices 1 and 2 from FLA v12 and equal-cost-seeded NSGA-II on `Epigenomics_46` and `CyberShake_100`, seed 211, `default` and `staggered` VM-speed profiles.
- [Actual source simulator Actions 41664213940](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41664213940): **16 new completed exact-genotype WorkflowSim simulations**, all 2 workflow jobs PASS. Frozen default objective parity is checked in Java against original archived Makespan and Cost within relative 1e-6.
- New passive logging: `sources/org/workflowsim/FLATaskEventTrace.java`, opt-in `-Ddagfla.fixedEventTrace=true` and independently existing `-Ddagfla.fixedTaskTrace=true`. WorkflowEngine captures actual parent-finished ENGINE_READY and ENGINE_COMPLETE events; WorkflowScheduler captures SCHEDULER_ARRIVE and SCHEDULER_DISPATCH events; WorkflowDatacenter captures DATACENTER_SUBMIT with the actual file-transfer delay that it passes to the CloudSim scheduler. Tasks matched by `Job.getTaskList().get(0).getCloudletId()`, not internal Job ID. All logging disabled in normal operation.
- [Independent read-only Actions 41664494795](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41664494795): PASS. The script `scripts/fla_fixed_event_chain_audit.py` verified 16 complete exact-mapping traces, per-original-Task-ID event identity, chronology, actual start/finish, max true Makespan, real stage-in nonnegative, and DAX ancestor independence. **14 distinct physical mapping × speed observations**, with **0 cross-arm duplicated-profile inconsistencies**. Original full event logs and read-only per-pair CSV archived as Actions artifacts.
- The results were obtained without any changed objective function, random choice, search algorithm, VM scheduling policy, task mapping, event delay or CloudSim simulator behavior. New tests are opt-in only.

## Previously verified baseline
[Earlier immutable per-Task-ID order validation Actions 41660490329](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41660490329) found **9,120 planned-vs-actual same-VM pair-order reversals** in the 16 replay-arm/profile rows; all belonged to pairs of tasks with **no DAX ancestor/descendant path**, according to the independent [dependency audit 41660802623](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41660802623). These pair observations are correlated and some physical assignments are duplicates across source algorithms.

## New event-stage results — exact original Task IDs

Counts are inversions among *DAG-independent tasks mapped to the same VM*, comparing event timestamp ordering with actual first-start ordering; timestamp ties are excluded from each stage's comparable denominator. Each displayed row combines original candidates 1 and 2.

| Workflow | Mapping source | Speed | Planned vs actual | ENGINE_READY vs actual | SCHEDULER_DISPATCH vs actual | DATACENTER_SUBMIT vs actual |
|---|---|---|---:|---:|---:|---:|
| Epigenomics_46 | FLA v12 | default | 103/888 | **0/864** | **0/888** | **0/888** |
| Epigenomics_46 | FLA v12 | staggered | 102/888 | **0/864** | **0/888** | **0/888** |
| Epigenomics_46 | seeded NSGA-II | default | 119/1187 | **0/1153** | **0/1187** | **0/1187** |
| Epigenomics_46 | seeded NSGA-II | staggered | 171/1187 | **0/1153** | **0/1187** | **0/1187** |
| CyberShake_100 | FLA v12 | default | 2421/5871 | **0/5684** | **0/5871** | **0/5871** |
| CyberShake_100 | FLA v12 | staggered | 2259/5871 | **0/5684** | **0/5871** | **0/5871** |
| CyberShake_100 | seeded NSGA-II | default | 2173/4720 | **0/4584** | **0/4720** | **0/4720** |
| CyberShake_100 | seeded NSGA-II | staggered | 1772/4720 | **0/4584** | **0/4720** | **0/4720** |

For pairs that started in a wrong planned order relative to actual VM start:
- **8,721 of 9,120 pair-events (95.625%)** already showed a distinct actual ENGINE_READY timestamp ordering in the opposite direction to the *planned start* ordering.
- **399 of 9,120 pair-events (4.375%)** had tied/indistinguishable earlier ENGINE_READY time ordering; the first distinct opposite ordering could be identified at SCHEDULER_DISPATCH.
- **0 newly first detected** at SCHEDULER_ARRIVE or DATACENTER_SUBMIT; **0 unresolved tied cases** under this audit.
- The 8,721 and 399 counts INCLUDE duplicated physical mappings across optimizer sources. They are not independent Bernoulli samples, and neither frequency nor percentage is a cross-DAG population estimate.

## Mechanistic conclusion and what is NOT established

The test narrows the observed schedule-order mismatch: the primary difference is **between the decoder's predicted planned task-start ranking and the runtime readiness/dispatch ranking of DAX-unrelated jobs sharing a VM**. The actual WorkflowSim ENGINE_READY, SCHEDULER_DISPATCH and DATACENTER_SUBMIT sequences are consistent with actual job start ordering for comparable pairs. This suggests investigating a **dependency-release-aware and VM-ready-queue-aligned planning decoder**, rather than blindly rescaling individual task compute times or assuming that the Datacenter reorders already dispatched jobs.

However:
1. ENGINE_READY and SCHEDULER_DISPATCH are observational timestamps. Tied timestamps do not establish a total order; observed first-divergence stage is not a causal intervention.
2. The issue is **not** proven to originate from a bug in WorkflowEngine/CloudSim or a violation of precedence constraints. The planning decoder's topological insertion and actual event-driven ready-job dispatch use different scheduling abstractions.
3. The true per-job file stage-in time measured by DATACENTER_SUBMIT is a distinct quantity from the signed `actualCPUTime - nominal taskLength/MIPS` accounting delta. They must never be conflated.
4. Dataset has two already observed DAX instances, optimizer seed 211, first two original source K16 candidates, two VM profiles, and duplicated physical mapping observations. It is a development mechanism pilot, not an independent test set; no claim of statistical significance or FLA superiority follows.
5. This does NOT establish any cost, makespan or HV benefit from a new decoder; a simulator-aligned estimator must first be implemented and independently validated as a *prediction* change, not immediately installed as an optimization advantage.

## Next falsifiable experiment

Separate the decoder's **predicted parent-release time** from its predicted VM insertion/slot time, and compare these against independently recorded ENGINE_READY and job actual start times for the SAME frozen mappings. A candidate read-only event-driven decoder should be fit/frozen on known development DAGs and evaluated on unseen DAG families/VM configurations before it influences FLA or NSGA-II optimization. Preserve exact mapping and same budget; report planner ranking fidelity, true simulator HV and runtime, including negative outcomes.

**Decision: keep v12/NSGA-II defaults unchanged, retain the verified event trace and continue model-fidelity studies.**
