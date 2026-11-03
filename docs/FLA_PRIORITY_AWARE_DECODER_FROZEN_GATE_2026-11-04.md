# Priority-aware ready-queue forecast falsification, frozen 2026-11-04

## Prerequisites
Original fixed-VM actual scheduling interventions Actions 41679712071 (36 simulator calls) and independent audit Actions 41680104295 found runtime task priority can change actual Makespan by both +10.650698% and −1.364562% within Sipht_60 depending on VM mapping. Passive actual idle-VM queue logs Actions 41680630820 verified real competing jobs and changed first-choice decisions, with zero trace-induced Makespan/Cost drift. This study does NOT resample outcomes; historical effects were observed *before* creating the new predictor, so all cases are development/falsification, NOT an unseen holdout.

## Fixed predictor code
- Extend `ReadyQueueScheduleEvaluator` with explicit QueuePolicy=TASK_ID/SHORTEST/UPWARD, preserving original 2-arg TASK_ID constructor and all unmodified optimizer defaults. SHORTEST sorts original task MI ascending; UPWARD sorts original DAG longest downstream MI sum descending; ties by original Task ID.
- The predictor advances task completion events under a frozen VM mapping, and models compute and stage-in/cache as existing ready decoder. It reads NO true simulator labels, and is computed only AFTER the original committed mapping has been selected, via `-Ddagfla.priorityAwarePredictionDiagnostic=true`.
- Original real simulator runtime priority remains controlled independently by `-Ddagfla.fixedVmReadyPriority=fifo|shortest|upward`; the code has NO search objective replacement or FLA-specific mutation in this test.

## Frozen tests and checks
- Cases: CyberShake_100, Montage_100, Sipht_60; same algorithm-independent four fixed allocations `all_vm0`, `all_vm12`, `round_robin`, `stride7`, VM speed default, seed 509; all three priority modes.
- 3 DAX × 4 genotypes × 3 runtime policies = **36 new actual WorkflowSim replays** with the new predictor measured on the same outcomes. No optimizer search. Exact original Task ID-to-VM identity and per-task actual coverage required.
- All 36 new actual Makespan/Cost outputs must match the immutably archived previous uninstrumented outcomes from Actions 41679712071 within 1e-6 relative tolerance. The new diagnostics must not change the simulator.
- 4-task deterministic priority forecast regression must pass: default TASK_ID=22s, explicit TASK_ID=22s, SHORTEST=22s, UPWARD=21s. Existing StageInAware and ReadyQueue tests and `FLAFixedVmReadyPriorityTest` must pass on a clean Java compile.
- For each fixed exact mapping and priority mode record real Makespan/Cost, old ready-queue predicted M/C, and new priority-aware predicted M/C; task start/finish mean absolute error. CSV output records all positive and negative cases without selection.
- Primary development falsification criterion: number of assignments/policies whose new absolute Makespan percent prediction error is lower than historical ready model (wins/ties/losses, tolerance 1e-8 percentage points). Secondary Cost error and mean task start/finish error; report predictions of the ±10.65/−1.36% Sipht interventions explicitly, not only overall mean.
- Never call the observed best policy for each mapping an optimized policy. A future optimizer must predict the effect before observing true replay results; its priority/mapping decisions need a fair NSGA-II and known scheduling-heuristic baseline.

## Science / novelty boundaries
These are historically known DAGs and selected development cases with one seed and static CloudSim configuration. No independent unseen families, no FLA HV, no publication-level statistical significance. Prior 2024 work already evolves task priority and VM selection together (C&O Research 172:106805); joint optimization without substantive new mechanism is not novel by itself. If this fixed predictor fails to forecast runtime priority effects, do not add a priority gene to a metaheuristic based on it. No `master` or default policy change.
