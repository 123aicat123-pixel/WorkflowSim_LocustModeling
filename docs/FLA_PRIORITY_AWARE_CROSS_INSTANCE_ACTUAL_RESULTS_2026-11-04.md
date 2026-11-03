# Priority-aware ready-task scheduling: independent new-instance true WorkflowSim results (2026-11-04)

**Status: important fixed-mapping model fidelity advance; a publishable FLA multi-objective optimizer is not yet proven. All opt-in changes confined to `fla-baseline`; `master` and original FIFO scheduling default remain untouched.**

## Evidence chain, with immutable actual simulator provenance
1. Runtime queue intervention: preregistration `docs/FLA_RUNTIME_PRIORITY_FROZEN_PILOT_2026-11-04.md`; original actual 36 simulations [41679712071](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41679712071) 3/3 PASS; independent all-case [41680104295](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41680104295) PASS. Changed only the order of already-ready compute jobs at idle VMs; exact original assignment and old evaluator objectives preserved. Historical FIFO full-parity with [41669662253](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41669662253) verified on Montage and Sipht.
2. Explanatory idle-VM competition: frozen post-outcome-selected diagnosis `docs/FLA_PRIORITY_DISPATCH_OPPORTUNITY_PROTOCOL_2026-11-04.md`. First [41680518522](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41680518522) FAILED at clean Java build due to one missing import. The missing `CondorVM` import was corrected and Java CI independently returned SUCCESS, without changing prior outcomes; corrected [41680630820](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41680630820) 4/4 PASS, 12 real replays, all reproduced nontraced original Makespan and Cost within relative 1e-6. Observed multiple idle-VM ready-task choices and genuine changed dispatch priority: Sipht stride7 upward changed 19 of 26 multi-job first selections and made Makespan **+10.650698% worse**; Sipht round_robin upward also changed 19 of 26 and made Makespan **−1.364562% better**. Montage stride7 upward changed 18 of 28 but almost no total effect. This is mechanistic evidence, not independent generalization.
3. First frozen priority-aware estimator: `ReadyQueueScheduleEvaluator.QueuePolicy=TASK_ID|SHORTEST|UPWARD`; original constructor remains TASK_ID. Postcommit diagnostic from `LIWSAPlanningAlgorithm.LastRunMetrics` and exact actual task traces has NO access to future real simulation labels. Four-task unit hand oracle passes; all clean Java CI passed after correction.
4. Known-DAG model gate `docs/FLA_PRIORITY_AWARE_DECODER_FROZEN_GATE_2026-11-04.md`; original actual [41681448520](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41681448520) 3/3 PASS (36 new real simulator replays), full independent all-case [41681867124](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41681867124) PASS. All outcomes reproduced the earlier uninstrumented actual results. Aggregate absolute Makespan forecast error over 36 correlated cases: old Task-ID ready **0.356945%**, new policy-aware ready **0.046785%**; **3 better / 30 tied / 3 worse**. The new predictor correctly captured the sign and magnitude of both large Sipht impacts but MIS-PREDICTED the direction of CyberShake round_robin SJF (+0.236779% real versus −0.019895% predicted).
5. Separate **new-instance** frozen gate `docs/FLA_PRIORITY_NEW_INSTANCE_FROZEN_GATE_2026-11-04.md`; original [41682109356](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41682109356) **8/8 PASS**, 24 new full actual WorkflowSim replays on previously unused *instances* `Inspiral_30` and `Epigenomics_100` (families historically known), both VM speed profiles and fixed round-robin/stride7 mappings. [Independent all-case actual audit 41682284043](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41682284043) PASS. Original Task ID–VM mapping and actual job data checked in every new case, no model adjustments or simulator outcome-dependent case selection.

## New-instance actual vs planned Makespan results

| DAX instance | VM speed | Cases | Old Task-ID ready mean absolute forecast error | Priority-aware mean absolute forecast error |
|---|---|---:|---:|---:|
| Inspiral_30 | default | 6 | 0.01584% | 0.01584% |
| Inspiral_30 | staggered | 6 | 0.01933% | 0.01933% |
| Epigenomics_100 | default | 6 | 2.39923% | **0.00033%** |
| Epigenomics_100 | staggered | 6 | 2.45975% | **0.00031%** |

Aggregate over **24 correlated fixed-mapping predictions**: old mean abs Makespan error **1.223536%**, new **0.008953%**; **4 better, 20 tied, 0 worse** by the prespecified numerical tolerance. This is not 24 independent workflow-family trials.

There were four actual >0.1% runtime-priority effects across the 16 non-FIFO comparisons. All four occurred for **UPWARD priority on Epigenomics_100** and were predicted in the correct direction:

| Epigenomics_100 | Fixed mapping | Real upward-vs-FIFO change | Forecast change | Error, percentage points |
|---|---|---:|---:|---:|
| default | stride7 | **+8.665192%** | +8.665222% | +0.000030 |
| staggered | stride7 | **+8.661968%** | +8.661992% | +0.000025 |
| staggered | round_robin | **+7.279015%** | +7.279040% | +0.000026 |
| default | round_robin | **+6.859519%** | +6.859543% | +0.000024 |

On Inspiral_30, all priority interventions were small (this cohort cannot test prediction of large effects). The strong Epigenomics effect is **harmful**: correct prediction does not imply improved optimization quality. The previous CyberShake SJF sign mistake remains a negative counterexample; do not delete it or claim universal correctness.

## What is actually new in the engineering
- Same Task→VM genotype can produce materially different true Makespan when an idle VM selects a different task from its ready queue. Earlier decoder disagreement was thus not just a numerical artifact.
- Exact event capture confirms actual multiple-ready-task opportunities with changed chosen first tasks, including cases where total Makespan remains nearly unchanged, and signed effects of the same upward policy are opposite on different frozen assignments.
- The new policy-aware estimator can reproduce sizable priority-sensitive actual Makespan changes in a new DAX *instance* without peeking at simulator outcomes, giving a defensible foundation for considering a joint priority+placement optimizer; model still fails in some CyberShake cases.

## Research / publication decision
1. This is not an FLA v19 algorithm, and not evidence of superior Pareto HV. The existing v12 FLA and seeded NSGA-II still solve only Task→VM placement; no priority search, fair two-component genotype, K16 true multiobjective HV or wall-time budget matching has been implemented yet.
2. A known 2024 paper already jointly coevolves task priority and VM choice rules (*A cooperative coevolutionary genetic programming hyper-heuristic for multi-objective makespan and cost optimization in cloud workflow scheduling*, Computers & Operations Research 172:106805, DOI 10.1016/j.cor.2024.106805). Therefore merely adding priority as a gene is not a literature novelty by itself.
3. A defensible next algorithm candidate would use explicit DAG-critical-path risk vs VM-ready competition, a strict *shared* priority-aware decoder for FLA and seeded NSGA-II, a fixed total search computation budget, and real Pareto HV and IGD+ under multiple independently predeclared new DAG families and seeds. The significant negative SJF CyberShake case must remain as a robustness test and cannot be tuned away using its observed truth.
4. An easy first **engineering-only** portfolio proof-of-concept could split exactly 3030 genotype evaluations across three registered priority-policy islands, and allocate exactly K16 real replays per solver across policies; report the same union reference and compute-time budget, including a full-budget fixed-FIFO control. This is a baseline portfolio study, **not claimed novel**.
5. If portfolio fails to improve true HV or computational cost, do not promote it or the priority-aware decoder as a search-optimization gain. The current evidence mainly supports a reproducible scheduler fidelity study and model-design hypothesis.

**Decision: freeze the validated priority-aware decoder, retain FIFO v12 baseline and continue only with a predeclared equal-budget algorithm-level test.**
