# Ready-queue decoder first frozen development gate — 2026-11-03

**Status when written:** alternative Java estimator implemented but no new real simulator comparison seen. This protocol precedes the actual benchmark workflow.

## Candidate
`sources/org/workflowsim/planning/ReadyQueueScheduleEvaluator.java` is a distinct fixed-map estimator: after dependencies finish, an idle VM selects the ready original Task ID in original DAX declaration order; the VM stays busy until its predicted duration (compute + estimated stage-in). Completed outputs update estimated per-VM caches. It has no feedback from the real simulator and does not change any existing optimization search, objective function, or default decoder. The alternative is intentionally simple and may fail if true WorkflowSim release batching and cache semantics differ.

The deterministic 4-task hand oracle is `ReadyQueueScheduleEvaluatorTest`: original topological insertion predicts Makespan=21, while the event-driven original-DAX-ID ready queue predicts Makespan=22. This is a semantics counterexample, NOT experimental superiority evidence.

## Predeclared development benchmark
- Original immutable v17 default profile archived mapping source Actions 41626382711.
- DAGs: `Epigenomics_46`, `CyberShake_100`.
- Search seed 211; original FLA v12 and equal-cost-seeded NSGA-II K16 source arms; original candidate positions **1 and 2** only.
- VM profiles: `default`, `staggered`.
- Total: 16 new full WorkflowSim fixed-assignment replay calls, including some duplicate physical mappings across algorithm sources. No new optimizer search, no re-selection using outcome values.
- Record for each exact original mapping: (insertion stage-in-aware predicted M,C), (ready-queue predicted M,C), (actual WorkflowSim M,C), plus mean absolute per-task start/finish error of each estimator.
- Primary **falsification**: paired percent absolute Makespan error, ready-queue minus insertion; failure if improvement is absent or unstable. Secondary: cost error, task start/finish error, and whether the alternative can reproduce measured order patterns.
- Require original default source Makespan/Cost and original mapping identity equal archive within 1e-6 relative tolerance. Run the 4-task Java unit oracle and the existing StageInAwareEvaluatorTest on clean build.
- Preserve individual cases (including failures and negative changes), CI logs, source SHA, original archived input and all per-task diagnostic data. Deduplicate physical assignments for interpretation.
- The developer DAGs and mappings are not independent holdout, and neither method may be promoted based on this experiment. Before any publication claim, test unseen DAGs and fixed evaluation budget across both algorithms.

## Acceptance decision
A working implementation with correct parity and a passing hand oracle proves engineering functionality only. Even a favorable matched development-cohort MAPE does **not** establish a publishable FLA innovation. Do not modify `master` or switch the default algorithm.
