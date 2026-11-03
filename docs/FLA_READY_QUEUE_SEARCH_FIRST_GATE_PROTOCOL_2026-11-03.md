# First controlled ready-queue objective *search* experiment — frozen protocol, 2026-11-03

**Preoutcome status:** new decoder had favorable prediction-fidelity results on a two-DAG development sample and mixed/negative on 3 additional known DAG instances. This document locks the first small full search experiment BEFORE results. Its objective is falsification, not model promotion.

## Treatments and control
2×2 factorial experiment on the SAME platform:
- Solvers: `DAG-Pareto-FLA[v12-hvbandit]` and equally cost-seeded `NSGA-II[costseed]`;
- Decoder objectives: `old` = existing shared stage-in-aware insertion, `ready` = experimental event-driven ready queue (`-Ddagfla.useReadyQueueObjective=true`).
- All four cells use exactly the same task encoding, VM pool, cost model, initial two cost seeds, source DAG, pseudo-random seed, assignment map and **3030 allowed objective calls** (population=30, generations=100), with new mode `v12-nsga-ready-pair`. No extra real WorkflowSim oracle calls inside search.
- Both `old` and `ready` have `-Dworkflowsim.planningStageInAware=true`; the new objective flag overrides ONLY the candidate evaluation when enabled. Default is OFF. Existing regression behavior is unchanged.
- Every solver receives exactly **K=16** prospective true WorkflowSim replays selected ONLY using its planned Pareto-cover policy; the K16 true simulation outputs do not influence which genotype is subsequently optimized or replayed. `-Ddagfla.budgetReplayK=16`, `-Ddagfla.budgetReplayPolicy=pareto-cover`.

## Locked workload, samples and claim level
- DAX: `Sipht_60` and `Montage_100`; one had strong positive independent-genotype decoder fidelity and one had neutral/negative fidelity. This is a deliberately contradictory known-DAG development test, NOT an independent final holdout.
- Seeds: 211,212 (original search-randomization seeds).
- VM speed configuration: default only for this limited first controlled search gate, to limit 3030-evaluation runtime. No speed-profile claims.
- 2 DAGs × 2 seeds × 2 decoder policies = **8 separate benchmark invocations**, each containing 2 solvers and 16 actual replay calls per solver (planned total **256 true replay calls**, assuming all jobs complete). 16 full optimization arms × 3030 counted evaluations is expected.
- Preserved outputs: complete K16 `_replays.csv` and `_summary.csv`, raw logs, source SHA, search evaluations, replay counts, all negative cases.

## Analysis locked
1. All same-DAG/seed cross-mode results share a **single true WorkflowSim HV reference** computed from the union of the four actual K16 front points; do not compare HV values obtained under distinct independently computed reference points. Also calculate a 1.5× and 3.0× reference-point sensitivity from the common per-block maxima.
2. Compare paired `FLA-ready vs FLA-old`, `NSGA-ready vs NSGA-old`; compare FLA vs NSGA under each decoder, including negative results, compute costs and runtime.
3. Distinguish improvement due to the shared decoder (appears in both solvers) from algorithm-specific FLA improvement. Do NOT call a shared decoder improvement a unique FLA search innovation.
4. Four block-level observations (2 DAG × 2 seeds) are insufficient for publication-level statistical inference, and two known DAGs are not unseen generalization.
5. If the new decoder improves prediction MAPE but does not improve true HV, or increases runtime too far, retain it only as diagnostic. No automatic replacement of the default or retuning on this evaluation set.

## Fidelity and engineering gates
- Full clean Java build and the four-task ready-queue oracle pass.
- Seeded cost assignments identical within each arm pair; objective evaluation counts equal and consistent with captured candidate recorder counts.
- Simulator replays use frozen same platform and original actual objective reader; no use of true labels before the end-of-run selection.
- No mutation to `master`; all experimental changes only to `fla-baseline`.
