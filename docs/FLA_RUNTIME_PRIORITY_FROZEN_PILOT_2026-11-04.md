# Runtime-ready-task priority actionability pilot — pre-registered 2026-11-04

## Motivation
A major prerequisite for jointly optimizing *task order* and *VM placement* is to prove that task order is actionable in the ACTUAL WorkflowSim scheduler on a frozen VM assignment. Earlier 9,120 same-VM planned-vs-simulated pair order differences arose among DAX-incomparable tasks. Search variants v18 and dual-model objectives did not deliver stable true-HV benefit on new workflows; further blind mutation/decoder tuning is suspended.

This is NOT yet a new FLA algorithm. SJF and upward path ranks are known rules; this study only isolates whether controlling their runtime ready-job priority can influence true Makespan/Cost and can preserve task/VM/precedence invariants.

## Intervention and negative controls
- Opt-in `-Ddagfla.fixedVmReadyPriority=fifo|shortest|upward`. Default is `fifo` (the exact original pending-order semantics). Changes only ordering of compute jobs ALREADY in WorkflowScheduler's pending list, before StaticSchedulingAlgorithm selects at most one job for an IDLE VM. Non-compute/stage-in slots remain at their original position; actual Task->VM assignment is frozen and never changed. No child is released before all parents complete by WorkflowEngine.
- Shortest prioritizes smaller original Task MI, ties smaller original Task ID.
- Upward prioritizes longer remaining DAG downstream task MI-path, ties smaller original Task ID. This is a simple HEFT-like known heuristic, not an original method.
- Timing and stage-in costs continue to be computed by the same WorkflowSim runtime. Search optimizer never changes its fitness or genetic decisions.
- All fixed mapping policies are preselected, algorithm-independent: `all_vm0`, `all_vm12`, `round_robin`, `stride7`; original Task ID order and VM ID mapping exactly as in `FLAReadyQueueCrossDagAudit`.

## FROZEN development pilot cases (do not replace after outcomes)
- DAX `CyberShake_100`, `Montage_100`, `Sipht_60`, all historically known benchmark families.
- VM speed `default`, original resource prices, seed 509, original unclustered STATIC scheduling and same independent fixed-genotype replay harness.
- **3 DAX × 4 exact frozen mappings × 3 queue policies = 36 real WorkflowSim simulator calls**; count DAX instances as 3 independent families, not 36 independent families.
- Use already-validated `FLAReadyQueueCrossDagAudit` with `-Ddagfla.fixedTaskTrace=true` and `-Ddagfla.readyQueueDiagnostic=true`, which asserts original mapping identity, task-level ID/VM coverage and finite objectives. Old/ready planning values should be invariant to runtime-only policy; fail the pilot if they change.
- Pure unit test checks FIFO unchanged, independent compute-only reorder, stage-in position unchanged, rejected unknown priority. Rebuild all Java sources and rerun original ready-queue four-task oracle + previous stage-in regression.
- For Montage_100 and Sipht_60, archive original default FIFO baseline run `41669662253` is a separate historical parity reference; require old FIFO actual Makespan/Cost to reproduce that archived output within 1e-6 relative tolerance. CyberShake_100 has no such old cross-DAG historical record under these exact four mappings and is independently paired to its new FIFO runs only.

## Outcomes / interpretation
Primary engineering gate: for same (DAX, mapping) can an alternative ready-job policy cause a nontrivial change in actual WorkflowSim Makespan, without VM assignment/precedence changes? Declare effect if |delta Makespan| > 1e-6 relative. Report both negative and positive cases and actual Cost change, separately by family and policy, and the count of changed schedules. Do not select the best policy after seeing its simulator outcome and call that implementable *online* optimization.
Secondary: actual per-task timelines and record of order changes, runtime cost. Preserve all raw actual CSV/logs, exact source SHA and job IDs.
Scientifically, a positive feasibility gate justifies implementing a **two-component genotype** (VM allocation + runtime priority), with an operator that can search priorities and a fair paired NSGA-II baseline using the SAME encoding. It does NOT establish novelty or a better FLA solver. Before publication, evaluate real priority-aware optimizer against standard HEFT/SJF/random task rules, with untouched holdout DAG families and multiple seeds, search-cost parity, true HV/IGD+/runtime, ablations and multiple-test correction.

## No-change safety
`master` must remain unchanged. Default `fifo` queue, original FLA v12/NSGA-II and StageInAware decoding must remain untouched. This is a research pilot only, not a deployment.
