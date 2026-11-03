# FLA WorkflowSim event-chain and DAG parent-release vs VM-wait root-cause study — 2026-11-03

**Status: completed, successful mechanism diagnosis on frozen development examples; not a validated improved optimization algorithm.**

## Artifact chain and immutable validation
- Frozen experiment protocol: `docs/FLA_FIXED_EVENT_CHAIN_PROTOCOL_2026-11-03.md`, seed 211, Epigenomics_46 and CyberShake_100, v12 FLA and seeded NSGA-II source candidate indices 1 and 2 from original default-speed v17 K16 archives Actions 41626382711, and two VM speed profiles.
- [Original full event tracing 41664213940](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41664213940): **16 new actual WorkflowSim replays**, 2/2 matrix jobs PASS. All exact Task→VM assignments remain unchanged, and default-profile makespan/cost match archived original simulator values within relative 1e-6.
- [Independent full event audit 41664494795](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41664494795): PASS, 16 replay-arm profiles; **14 unique physical profile-specific assignments**, zero duplicate-profile disagreement. Verified five real WorkflowSim event types and actual job start/finish for all original Task IDs.
- [Independent parent-release vs after-ready-wait audit 41664986651](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41664986651): PASS; per-task CSV for all **1176 Task ID observations**, decomposition identity checked row-by-row, independent original DAX parent edges and max-parent-finish timestamps used.

## First event-stage schedule-order divergence

Using only DAX-independent task pairs sharing the same VM, 9,120 planned-vs-actual task-start order inversions were recorded in 16 original replay-arm/profile rows (includes duplicated physical assignments, not independent cases).

- **8,721 / 9,120 (95.625%)**: the first measurable opposite ordering is already present in timestamp order at ENGINE_READY, relative to the decoder's planned-start order.
- **399 / 9,120 (4.375%)**: ENGINE_READY comparison has a timestamp tie; first measurable opposite ordering appears at SCHEDULER_DISPATCH.
- **0 comparable-pair inversions** between ENGINE_READY and observed actual job start, between SCHEDULER_DISPATCH and observed actual job start, and between DATACENTER_SUBMIT and observed actual job start, for this data.
- No measured task-dependency (ancestor/descendant) pair order inversion in the separate earlier DAX ancestry analysis; all 9,120 planned vs actual reversals involved independent tasks sharing a VM.
- These facts localize an *observed difference in the ordering abstraction*, not a defect in WorkflowEngine or a causal allocation of runtime error to specific mechanisms. Ties are never broken arbitrarily by log row order.

## Further decomposition: parent-release versus post-ready waiting

For a fixed original Task ID `i`:

- `predicted_release_i=max(predicted_parent_finish_j)` over original direct DAX parents, 0 for sources;
- `actual_ready_i` is directly emitted by WorkflowEngine after dependencies are received;
- `planned_wait_i=planned_start_i-predicted_release_i`;
- `actual_wait_i=actual_start_i-actual_ready_i`;
- **exact arithmetic identity**:

```
(actual_start_i - planned_start_i)
= (actual_ready_i - predicted_release_i)
+ (actual_wait_i - planned_wait_i).
```

Each term is *signed*. The absolute values of the two terms do not add to the total absolute start error; opposite signs can cancel. This is an observational decomposition, NOT a causal component intervention.

| DAX | Mapping source | Profile | Mean abs parent-release error (s) | Mean abs after-ready-wait error (s) | Mean abs total start error (s) |
|---|---|---|---:|---:|---:|
| Epigenomics_46 | FLA v12 | default | 282.598 | **808.206** | 935.016 |
| Epigenomics_46 | FLA v12 | staggered | 258.126 | **1124.035** | 1216.950 |
| Epigenomics_46 | seeded NSGA-II | default | 97.538 | **754.056** | 738.458 |
| Epigenomics_46 | seeded NSGA-II | staggered | 140.194 | **1139.963** | 1101.964 |
| CyberShake_100 | FLA v12 | default | **1145.939** | 166.579 | 1276.692 |
| CyberShake_100 | FLA v12 | staggered | **1581.035** | 227.036 | 1748.802 |
| CyberShake_100 | seeded NSGA-II | default | **657.876** | 110.958 | 715.304 |
| CyberShake_100 | seeded NSGA-II | staggered | **885.105** | 151.287 | 971.168 |

Across all 1176 original task-row observations, `|release_error|>|wait_error|` for **748 rows** (these observations are correlated and may include physically duplicated schedules). Maximum observed true `ENGINE_READY - max(actual_direct_parent_finish)` was **0.776923 s** in the development cohort, supporting that the much larger predicted-release discrepancy is predominantly about simulated execution-finish estimates, rather than the engine waiting thousands of seconds to release a task after all its parents finish.

## Scientific interpretation and next gate

- **Epigenomics** in this small cohort shows larger after-ready waiting error magnitudes; **CyberShake** shows larger parent-release prediction error magnitudes.
- These two error sources are coupled over the DAG. A late parent completion may itself have resulted from VM queue or stage-in mismatch earlier in the execution history. Do NOT equate the relative magnitude of one signed term with a causal share of ultimate makespan error.
- Candidate innovation hypothesis: **DAG-depth-/ready-queue-aware and simulator-aligned scheduling decoder**, with separate parent-finish propagation and VM wait estimates, applied fairly as a shared decoder to FLA and seeded NSGA-II. This is an UNTESTED hypothesis, not an improvement claim.
- Next falsification: lock a read-only revised decoder on development examples, then compare it with the historical decoder on *identical withheld assignments* across unseen DAG families, multiple independent seeds and VM speed regimes. First report planned-vs-actual makespan ranking agreement and task timeline error; only then re-optimize both algorithms with the same new decoder and equal search/simulation budgets. Analyze HV, IGD+, runtime, failure cases, and both reference-point policies.
- The experiment has only two known DAX instances and one optimizer seed. No Q1-readiness, superior HV, or solver-specific fairness claims follow. Duplicate physical mappings must not inflate inferential sample size.

Source implementation opt-in only: `sources/org/workflowsim/FLATaskEventTrace.java`, `scripts/fla_fixed_event_chain_audit.py`, `scripts/fla_parent_release_vs_wait_audit.py`. Neither `master` nor the default optimizer/simulation configuration was changed.
