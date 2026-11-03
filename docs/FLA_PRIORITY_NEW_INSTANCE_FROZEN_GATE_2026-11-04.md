# Priority-aware decoder new-instance generalization gate (preregistered 2026-11-04)

## Frozen code and prior known observations
`ReadyQueueScheduleEvaluator.QueuePolicy` and all code are frozen from the 36 actual simulator development-case results (original 41681448520; verified independent 41681867124). Those developer examples were CyberShake_100, Montage_100, and Sipht_60. The model correctly forecast two large Sipht priority effects, but mispredicted the sign of a CyberShake SJF effect. No fitted parameters were learned. **No source code or decision-rule modification is allowed after this gate produces outcomes**, unless a new separate development and holdout cycle is declared.

## Independent new-instance assessment
- DAX: `Inspiral_30` and `Epigenomics_100`, not present in the specific 36-instance development gate. Their workflow families have appeared elsewhere in earlier research, hence these are new *instances*, NOT research-wide unseen families.
- Two VM speed profiles: `default`, `staggered`.
- Two preselected deterministic placement vectors: `round_robin`, `stride7`, built from original Task IDs 1..N. No FLA or NSGA-II search, no selection on simulator outcomes.
- Three runtime ready-job policies: `fifo`, `shortest`, `upward`, identical for both VM profiles, seed 509.
- **2 DAX × 2 VM speeds × 2 fixed placements × 3 policies = 24 actual independent WorkflowSim replay calls**, 8 match-paired 3-policy groups.
- The two estimated models recorded for each exact fixed assignment and policy are the historical original Task-ID ready decoder (does not use policy) and the frozen priority-aware ready decoder (knows only fixed policy, DAG, VM, files). True simulator Makespan/Cost are never used as predictor inputs.
- Old 4-task queue and new priority-mode hand-oracle tests must pass; original FIFO remains default and the simulator's entire static scheduling/VM assignment/cost setup is unchanged.

## Primary metrics
1. For all 24 policy/speed/placement instances, mean absolute percentage Makespan prediction error of original ready vs policy-aware ready; report **per-case** wins/ties/losses (absolute error tolerance 1e-8 percentage points) and negative cases. Secondary: Cost error and observed per-Task start/finish MAE.
2. 16 alternative-priority-vs-FIFO matched pairs: forecast-vs-actual signed Makespan change, absolute speed-profile- and DAX-stratified error in percentage points; specifically report whether true effect exceeds 0.1%, whether predictor gets sign right, and errors on all cases. The 0.1% practical screen is predetermined here as a reporting threshold, not statistical inference.
3. Preserve actual simulator outputs for every mapping; assert every original Task ID and VM mapping fully recovered, all predicted and actual objectives finite and positive, no changing code after reading outcomes.
4. If the new instances provide almost no materially changed priority outcomes, state that prediction of large priority effects is untested here. Do not oversell low MAPE dominated by no-effect cases.

## Decision gate
If new predictive model fails to improve or frequently mis-signs material priority effects, **do not put it inside a joint FLA+priority optimization**. If results are favorable, proceed to a frozen equal-budget FLA vs seeded NSGA-II joint resource+priority portfolio feasibility experiment, keeping true HV, IGD+, runtime and per-model computational costs transparent. A shared decoder is not FLA-specific novelty. No claim of Q1 readiness follows from this 24-call diagnostic.
