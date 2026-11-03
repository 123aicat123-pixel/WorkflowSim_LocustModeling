# Dual-model ready-queue disagreement objective: frozen first falsification gate (2026-11-04)

**Status when written: source and unit test implemented, no dual-mode true-HV outcomes observed.**

## Hypothesis (not a claim)
The stage-in-aware insertion estimator and event-driven ready-queue estimator have complementary failures on different DAX structures. A fixed compromise (MEAN) or conservative componentwise worst-case (WORST) may be more robust as a **search fitness evaluator**, but may also misrank Pareto points or slow search. Both models are evaluated on each candidate, and their aggregate counts as ONE search-genotype evaluation; wall time is separately required.

## Locked experiment
- Decoder objective modes `mean` and `worst` (new), compared to **archived** `old` and `ready` arms from true simulator Actions 41670356422. All four modes use same task encoding and cost seeds, evaluated under `-Dworkflowsim.planningStageInAware=true` and mode-specific switches only. New modes are OFF by default; `-Ddagfla.useReadyQueueObjective=true` and dual-model cannot be simultaneously active.
- DAX `Sipht_60`, `Montage_100`; seeds 211 and 212; `default` VM profile. Both DAGs are known development cases, not independent test families.
- Solvers: `DAG-Pareto-FLA[v12-hvbandit]` and `NSGA-II[costseed]` under mode `v12-nsga-ready-pair`.
- Each (DAG, seed, mode) invocation contains 2 solvers × exactly 3030 counted objective genotypes (population 30, 100 generations), K=16 true WorkflowSim replay calls per solver via planned Pareto-cover only. 2 DAG × 2 seeds × 2 new modes = 8 new invocations and 256 actual K16 simulator calls assuming completion. Archived old and ready arms were independently frozen before new model construction.
- Main outcome: independently recomputed **normalized actual WorkflowSim HV**, one shared reference per DAG/seed across ALL 8 solver/mode cells (old,ready,mean,worst × FLA,NSGA-II). Use 1.5x and 3.0x of combined true K16 maximum Makespan/Cost for reference sensitivity. Do NOT compare original within-run sim_hv directly.
- Secondary: search wall-time ratio vs original, true nondominated K16 count, extreme Makespan/Cost, negative and duplicate cases. Every 16 replay assignments unique within solver, actual outcomes finite and positive, exact counting audit 3030 per solver.
- No optimizer tuning after inspecting outcomes; no mode selection by future labels; no changes to master and no default promotion. Result is a *mechanistic small development factorial*, not final evidence for publication. Promote only after separately designed, prospectively held-out multi-DAG, multi-seed tests show stable improvements, and FLA-specific advantage is separated from shared-decoder advantage.

## Adverse-result policy
If mean or worst fails to dominate old FLA under matched true HV, archive negative results and do not relabel that method as improvement. Even consistent small 4-block wins would not justify publication-level claims.
