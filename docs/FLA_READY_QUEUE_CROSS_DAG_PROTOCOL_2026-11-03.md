# Ready-queue decoder external-DAG / deterministic-genotype gate — frozen before execution (2026-11-03)

## Purpose
Falsify the initial favorable ready-queue result on NEW fixed-genotype mappings, not selected by any FLA/NSGA-II search and not based on any new simulator outcomes. The decoder is already frozen from its 14-physical-case development study (original Actions 41668888545 and aggregate 41669178910). NO threshold tuning, regression fitting, model modification, optimizer promotion or adaptive case replacement based on results.

## Fixed cases
- DAX instances **Inspiral_100, Montage_100, Sipht_60**; these were NOT in the first two-instance ready-queue development sample (Epigenomics_46, CyberShake_100). But the DAG families have been used in earlier platform research, so this is **a new-case extension, not a pristine research-wide unseen family holdout**.
- Four algorithm-independent deterministic assignment policies for each DAX, using original declaration-order Task IDs 1..N (per original WorkflowParser):
  - `all_vm0`: every Task on VM ID 0;
  - `all_vm12`: every Task on VM ID 12;
  - `round_robin`: Task ID i gets VM ID (i-1) mod 16;
  - `stride7`: Task ID i gets VM ID (7*(i-1)+3) mod 16.
- VM profiles default and staggered. Same frozen assignments across profiles. Total 3 DAX × 4 assignments × 2 profiles = **24 independent actual WorkflowSim replay calls**, one deterministic seed 509 for provenance (no optimizer population, no stochastic assignment search).
- Compute old stage-in insertion and new ready-queue predicted Makespan, Cost, per-task start/finish MAE on each SAME actual WorkflowSim completed mapping; enforce exact Task ID and VM mapping from simulator. Preserve every outcome, including negative and failures.
- Primary descriptive metric: per-case absolute Makespan percent prediction error difference (ready−insertion), with cases grouped by DAX and VM profile, and wins/ties/losses. Secondary: Cost prediction error, task start/finish MAE. No HV yet.
- If results contradict old vs new improvement, report the contradiction, retain alternative estimator for diagnosis only, DO NOT modify the model on this evaluation cohort and then call this cohort holdout.
- Counterexample four-task oracle, existing stage-in regression, fresh clean Java build and normal untouched default settings are required.

## Scientific limitations
Simple deterministic assignments intentionally emphasize bottleneck and placement extremes, not representative optimizer search solutions. These three known workflow families are additional instances, not independent unseen families. Predictive improvement is not optimizer search superiority; later fair FLA and seeded NSGA-II with identical modified decoder budgets, unseen DAGs, runtime and HV is required before journal claims. `master` untouched.
