# Retrospective K8 selected-union headroom diagnostic (2026-11-04)

**PASS** read-only original simulation archive audit [GitHub Actions 41822256060](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41822256060); source originals [41821482575](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41821482575), 24/24 PASS. No additional simulator calls and no optimizer modification.

The diagnostic asks **whether OLD, FULL READY, STAGED T8 and ACTIVE T8 actually select different physical mappings**, and computes both the HV of ALL unique observed mappings combined and a hindsight TRUE-score greedy K8 heuristic over that observed union. Both use real simulator results which were NOT available to the prospective selector. The union-all HV is an optimistic ceiling for subsets of that observed union, but may need more than K8 mappings. The hindsight greedy K8 is a heuristic, NOT a provable upper bound on optimum K8.

## Observed actual replay union (shared per-DAG/seed 1.5x HV reference)

| DAG | Seed | Solver | Unique assignments across 4×K8 | ACTIVE overlap with OLD | ACTIVE HV | Observed union-all HV | Hindsight greedy K8 HV |
|---|---:|---|---:|---:|---:|---:|---:|
| CyberShake_50 | 903 | FLA-v12 | 10 | 8/8 | 0.35983292 | 0.36002730 | 0.35996570 |
| CyberShake_50 | 903 | NSGA-II | 11 | 6/8 | 0.37745173 | 0.37903513 | 0.37819110 |
| CyberShake_50 | 904 | FLA-v12 | 9 | 8/8 | 0.43851563 | 0.43880374 | 0.43852588 |
| CyberShake_50 | 904 | NSGA-II | 9 | 8/8 | 0.45412832 | 0.45429590 | 0.45429354 |
| Sipht_60 | 903 | FLA-v12 | 10 | 7/8 | 0.24516906 | 0.24516948 | 0.24516948 |
| Sipht_60 | 903 | NSGA-II | 11 | 7/8 | 0.24515337 | 0.24515511 | 0.24515442 |
| Sipht_60 | 904 | FLA-v12 | 9 | 8/8 | 0.24508807 | 0.24508807 | 0.24508807 |
| Sipht_60 | 904 | NSGA-II | 10 | 7/8 | 0.24507117 | 0.24507340 | 0.24507306 |
| Epigenomics_100 | 903 | FLA-v12 | 8 | 8/8 | 0.34537452 | 0.34537452 | 0.34537452 |
| Epigenomics_100 | 903 | NSGA-II | 10 | 7/8 | 0.33874340 | 0.33874340 | 0.33874340 |
| Epigenomics_100 | 904 | FLA-v12 | 11 | 6/8 | 0.34441208 | 0.34442496 | 0.34442496 |
| Epigenomics_100 | 904 | NSGA-II | 8 | 8/8 | 0.33619515 | 0.33619515 | 0.33619515 |

## Interpretation

1. The source deterministic planned-only N32 pool is the same across the four selectors for each identical DAG/seed/solver, independently source SHA and pool fingerprints verified.
2. Four K8 selectors return **only 8–11 distinct physical mappings per solver/DAG/seed** from up to 32 theoretically possible slots. Thus changing the post-search selection rule produces relatively few fresh true simulator observations. This strongly suggests concentration of the existing selection strategies, although it does NOT prove that all unobserved N32 mappings are poor.
3. For FLA Epigenomics_100 seed903, union has only 8 physical assignments and its HV equals ACTIVE HV. No already-replayed alternative can improve this particular K8 selected set; whether an unobserved original N32 mapping could improve it is UNKNOWN.
4. For FLA CyberShake_50 seed904, ACTIVE HV 0.43851563, observed union-all HV 0.43880374, hindsight greedy K8 0.43852588: some observed selection headroom exists, but marginal improvements and measured relevance are limited. Future experiments must not use true hindsight labels for candidate selection.
5. The result suggests that repeatedly fitting a new T8 selector to the same `budgetedPlannedCoverage` N32 source pool has low demonstrated leverage. **A changed candidate generation or a larger/unbiased candidate pool is a more defensible next hypothesis than continuously tuning residual weights.** Such a modification would affect the original search/pool and must be treated as a new, separately preregistered experiment.

## Claims not supported
No claim about full 3030-visited-set or global Pareto ceiling: only assignments previously selected and replayed by the four policies have actual labels. The union-all HV uses all distinct known maps (sometimes >8), not a feasible K8 decision. The hindsight greedy K8 uses simulator truth unavailable to the actual planner; it is explanatory, never a deployable baseline.

No unknown-family significance, no calibrated uncertainty guarantee, no proof of wall-time superiority, and no improved FLA accepted. Retain original adverse results; `master` unchanged.
