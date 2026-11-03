# FLA fixed-assignment task-timeline and dependency-order mechanism study — 2026-11-03

**Status: 16 real fixed-genotype WorkflowSim replay calls succeeded and multiple independently replayed read-only analyses PASS.** This is a newly verified *model-fidelity mechanism* observation, NOT a novel optimization algorithm or proven HV improvement. `master` unchanged. Original v12/default solver policy unchanged.

## Evidence chain and source code

- Preregistered observational task-trace scope: `docs/FLA_FIXED_TASK_TIMELINE_PROTOCOL_2026-11-03.md`. Original v17 default K16 source assignments from [Actions 41626382711](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41626382711), exactly two original candidate assignments per solver source (`v12`, `NSGA-II`) at optimizer seed 211, two DAX instances `Epigenomics_46` and `CyberShake_100`, two VM profiles `default` and `staggered`. Total 8 frozen assignment identities and 16 real replays. Some assignment identities are shared between solver sources; there are **14 distinct physical assignment × VM-profile observations**, not 16 independent configurations.
- New passive opt-in `-Ddagfla.fixedTaskTrace=true` stores detached `StageInAwareScheduleEvaluator` predicted task starts/finishes in `LIWSAPlanningAlgorithm.LastRunMetrics`, and raw observed WorkflowSim single-task compute Job starts/finishes/CPU seconds in `LIWSABenchmarkExample.RunResult`. Original task IDs are retrieved from `job.getTaskList()` and cross-checked against the exact original genotype mapping; WorkflowSim's internal Job IDs differ from original Task IDs. Default flag OFF, no search changes.
- First attempt [Actions 41660033665](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41660033665) **FAILED**, correctly refusing an unsupported assumption that `actualCPUTime - taskLength/nominalMIPS` was always nonnegative and a physical stage-in duration. Both families exposed a negative signed residual; this is an *accounting discrepancy*, and cannot be interpreted as negative real stage-in. The explicit scientific correction retained the **signed** residual without zeroing or silently relabeling it as observed file transfer.
- Corrected actual source [Actions 41660167042](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41660167042) **SUCCESS**, 2/2 matrix jobs, 16 actual independent replays and 1176 Task-ID matched records. Each default-profile total makespan/cost reproduced the archived original simulator result within 1e-6 relative precision. Source reports and complete raw task CSV are retained inside original job artifacts.
- Independent [read-only order audit 41660490329](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41660490329) **SUCCESS**; checked exact original Task IDs, VM IDs, start/finish accounting, 16 task-count and max-finish/makespan parity invariants. All 1176 original records included, no new oracle calls, original results unchanged. **0 cross-arm physical assignment inconsistencies.** Preserved `task_order_cases.csv`, `task_order_by_vm.csv`, report and source SHA.
- Further independent [DAX ancestry order audit 41660802623](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41660802623) **SUCCESS**. Mapped DAX job elements to original WorkflowParser Task IDs beginning at 1 in job declaration order, used exact DAX child/parent edges and transitive ancestor closure to separate dependent from independent same-VM task pairs. Preserved raw per-case CSV and complete report. No new simulation/optimizer calls.

## Same-VM planning-versus-simulator ordering inversions

An inversion is an unordered pair of tasks **assigned to the same VM** whose predicted task start order is reversed in the actual observed WorkflowSim start order. Pairs tied in either trajectory are excluded, and only valid within-VM comparable pairs are counted. These are **task-pair events within 16 replay traces, NOT 9120 independent workflows or random replications**.

| DAX | Original assignment source | Speed profile | Inverted / comparable within-VM task pairs | Inversion percentage |
|---|---|---|---:|---:|
| Epigenomics_46 | FLA v12 | default | 103 / 1216 | 8.470% |
| Epigenomics_46 | FLA v12 | staggered | 102 / 1216 | 8.388% |
| Epigenomics_46 | NSGA-II | default | 119 / 1614 | 7.373% |
| Epigenomics_46 | NSGA-II | staggered | 171 / 1614 | 10.595% |
| CyberShake_100 | FLA v12 | default | 2421 / 6080 | 39.819% |
| CyberShake_100 | FLA v12 | staggered | 2259 / 6080 | 37.155% |
| CyberShake_100 | NSGA-II | default | 2173 / 4919 | 44.176% |
| CyberShake_100 | NSGA-II | staggered | 1772 / 4919 | 36.024% |

Task-level finish-error diagnostic on the same observed records (mean absolute values in seconds, averaged across all original tasks from the two source candidates for each displayed row):

| DAX | Source | Speed | Mean abs start error (s) | Mean abs finish error (s) | Mean abs task duration error (s) |
|---|---|---|---:|---:|---:|
| Epigenomics_46 | FLA v12 | default | 935.016 | 934.507 | 0.509 |
| Epigenomics_46 | FLA v12 | staggered | 1216.950 | 1216.441 | 0.509 |
| Epigenomics_46 | NSGA-II | default | 738.458 | 737.950 | 0.508 |
| Epigenomics_46 | NSGA-II | staggered | 1101.964 | 1101.456 | 0.509 |
| CyberShake_100 | FLA v12 | default | 1276.692 | 1276.549 | 0.318 |
| CyberShake_100 | FLA v12 | staggered | 1748.802 | 1748.756 | 0.318 |
| CyberShake_100 | NSGA-II | default | 715.304 | 715.234 | 0.379 |
| CyberShake_100 | NSGA-II | staggered | 971.168 | 970.983 | 0.379 |

These are absolute task-clock differences, NOT end-to-end makespan error or evidence that every task has a much larger physical compute duration. A striking example is Epigenomics_46 FLA candidate #2 staggered: one task's observed start differed from planner by +23511.632 s and finish by +23503.668 s. The original workflow actual makespan was independently revalidated from the maximum observed job finish.

## Stronger DAG-specific finding: every observed inversion is between DAG-independent tasks

The independent DAX ancestry audit specifically classified each inverted same-VM task pair as:
- **Ancestor-related (dependent)** if one task can reach the other through one or more original DAX edges, versus
- **Independent** if no path exists between the two.

Every observed inversion in all 16 original replay-arm rows was in the **independent** category. Across original arm/profile/candidate rows, **0 dependent inversions**, **9120 independent inversions** (the 9120 count includes repeated physical assignment traces across arms and MUST NOT be treated as 9120 independent cases).

| DAX | Assignment source | Profile | Dependent inverse / comparable | Independent inverse / comparable |
|---|---|---|---:|---:|
| Epigenomics_46 | v12 | default | 0/328 | 103/888 |
| Epigenomics_46 | v12 | staggered | 0/328 | 102/888 |
| Epigenomics_46 | NSGA-II | default | 0/427 | 119/1187 |
| Epigenomics_46 | NSGA-II | staggered | 0/427 | 171/1187 |
| CyberShake_100 | v12 | default | 0/209 | 2421/5871 |
| CyberShake_100 | v12 | staggered | 0/209 | 2259/5871 |
| CyberShake_100 | NSGA-II | default | 0/199 | 2173/4720 |
| CyberShake_100 | NSGA-II | staggered | 0/199 | 1772/4720 |

**Interpretation:** The studied planner and simulator both preserved the precedence order of ancestral task pairs, but frequently chose different time orders for independent tasks competing for a shared VM. The observed close magnitude of start and finish error relative to task-duration error also points toward a *schedule timing/order* mismatch rather than a uniform task-computation-speed error. This prioritizes investigating VM-ready queues, concurrent ready-job dispatch, tie-breaking and file/cache readiness. None of these specific mechanisms is yet independently isolated as the causal origin.

## Research decision and next falsification test

1. KEEP the default v12 and baseline/current selector unchanged. No scientifically established FLA advantage over equal-cost-seeded NSGA-II.
2. Next test should log actual per-VM *ready, submission, start, stage-in, finish* transitions and compare to the estimator's topological earliest-insertion decisions on identical mappings, without using search feedback; distinguish contention/queue reorder from file arrival or simulator event sequencing.
3. A novel scheduler proposition would be a **simulator-aligned, dependency-preserving ready-queue/timing decoder** used equally for FLA and NSGA-II. First validate improvement in prediction fidelity and ranking using exact matched assignments, then prospective unseen DAG/VM scenario quality under fixed budget. Until that experiment, this remains only a hypothesis and not a publication contribution.
4. The 2 observed workflow instances, two default-selected genotype prefixes per source, one seed and two VM profiles are too limited for generalization. Duplicate physical schedules are not independent observations. VM profile also changes job event order, so this audit does NOT isolate an independent causal contribution of processor speed alone.
5. Preserve negative signed CloudSim accounting residual examples and avoid asserting they are stage-in times. To causally attribute stage-in, instrument *actual* file transfer events separately and reconcile units, aggregation and cache semantics.

**Conclusion:** This round narrows an important planning-to-real simulation mismatch to scheduling order among **DAG-independent tasks on shared VMs**. The result is reproducible, but neither a demonstrated optimized FLA method nor evidence sufficient for a high-tier journal claim.
