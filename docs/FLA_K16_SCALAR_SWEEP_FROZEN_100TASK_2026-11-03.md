# Frozen-reference REAL WorkflowSim K16: Pareto coverage versus extreme-first scalar sweep (2026-11-03)

**Verdict:** A stronger, deterministic control confirms an overall but **nonuniversal** Pareto-cover screening advantage. There are real negative cases. This is evidence for **post-search simulation screening**, NOT statistical proof of superior FLA optimization.

## Experimental provenance

- [Authoritative successful 15-case run 41586916588](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41586916588), source commit `a047023c431c586a0281f9c30c1fb1bb164bf41f`.
- Final aggregate artifact: `sweepK16-report-41586916588`, artifact ID `13207989528`. It contains the complete `scalar_k16_report.md`, `scalar_k16_paired.csv`, `scalar_k16_scores.csv`, compiler/source SHA and audit output. Every workload/seed artifact preserves actual independently simulated assignments and budgets.
- A prior initial run `41586887562` failed because a workflow check looked for `ci-logs/random.log` while the scalar policy wrote `ci-logs/scalar-sweep.log`. The assertion path was corrected before the authoritative complete rerun. This was a CI naming error, not evidence of an algorithm failure.
- The Java scalar implementation is in `examples/org/workflowsim/examples/planning/FLAResearchExperiment.java`; the independent Python oracle is `scripts/fla_replay_budget_audit.py:sweep()`. [Cross-language parity CI 41586537341](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41586537341) passed **32/32 fixture-policy-budget configurations**, including objective ties and near-double-precision ties.

## Fair comparison

- Five DAGs: CyberShake_100, Epigenomics_100, Inspiral_100, Montage_100, Sipht_100; **new search seeds 61,62,63**.
- Three algorithms each: DAG-Pareto-FLA v7-costseed, DAG-Pareto-FLA v12-hvbandit, NSGA-II costseed.
- Two prospectively executed screening policies per algorithm/seed: (1) planned-Pareto-layer plus normalized max-min spacing, and (2) minimum-planned-cost / minimum-planned-makespan extreme-first scalar sweep using deterministic low-discrepancy Van der Corput weights.
- Each algorithm/policy run uses **3030 actual planning objective evaluations and exactly K=16 independently executed WorkflowSim replays**; both policies use identical starting low-cost schedules, DAG, seed, VM setup and search algorithm.
- **Pre-frozen common HV reference** per DAG family is taken from the *earlier* five-seed 100-task full-fairness [Actions 41572425682](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41572425682), pooled artifact `v12full-report-41572425682` ID `13201439731`, NOT refitted to this experiment:
  - CyberShake_100: (6806.24215, 3280.0303).
  - Epigenomics_100: (211858.3560250001, 217310.76064).
  - Inspiral_100: (11044.129825, 11209.86290125).
  - Montage_100: (568.6573, 570.969505).
  - Sipht_100: (9127.960675000002, 8822.13817375).

## Actual HV outcomes (Pareto-cover relative to scalar sweep)

| Solver | Mean paired within-DAG relative gain | Cover wins / 15 | Sweep wins / 15 |
|---|---:|---:|---:|
| FLA v7-costseed | **+1.482%** | **14/15** | 1/15 |
| FLA v12-hvbandit | **+1.647%** | **13/15** | 2/15 |
| Cost-seeded NSGA-II | **+1.523%** | **14/15** | 1/15 |
| **Total** | — | **41/45** | **4/45** |

**The four negative observations must remain visible:**

| DAG | Seed | Algorithm | Pareto-cover relative HV loss | Actual minimum simulated makespan, cover vs sweep | Minimum simulated cost comparison |
|---|---:|---|---:|---|---|
| Epigenomics_100 | 63 | NSGA-II | **−0.272014%** | 55396.9955 vs **55395.7925** | Same, 181591.12245 |
| Sipht_100 | 62 | FLA v12 | **−0.051478%** | Same, 3020.7830 | Same, 7822.62315 |
| Sipht_100 | 63 | FLA v7 | **−0.229347%** | 3444.7425 vs **3426.2105** | Same, 7822.62315 |
| Sipht_100 | 63 | FLA v12 | **−0.112442%** | 3255.4575 vs **3243.7590** | Same, 7822.62315 |

These cases suggest that protection of the *real* low-makespan edge is an unresolved failure mode of the planner-space Pareto coverage heuristic. However, the selector cannot know true simulator outcomes in advance. Do not assume a simple two-extreme reservation always solves it. Test any revised policy separately on a development cohort, then lock and validate on genuinely new seeds and other VM/communication settings.

## Independent exact-search-history fairness verification

A separate new experiment added a SHA-256 commitment to **the ordered list of all unique evaluated genotypes and the exact IEEE-754 bits of their planned makespan/cost**. [GitHub Actions run 41587616144](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41587616144), source `e88ffffd4fe4cace1cff42fdc0ff311fbf16a697`, checked the real K16 Pareto-cover, scalar-sweep, random draw 0 and random draw 1 on Montage_25 seed 1, with 80 search evaluations per solver: all three solver histories had identical 64-hex-digit SHA-256 across the four policy/draw conditions. Different random draws selected different actual genotypes while keeping exactly K=16 replays per solver. This is a stronger fairness invariant than matching archive size alone.

## Scientific boundaries

- 45 algorithm-case values share only **15 workflow/seed cases across five DAG families** and are correlated across solvers; do not report an artificial sample size of 45 independent DAGs.
- HV references are pre-frozen relative to this new cohort but came from previous studies; they are not externally mandated objective thresholds.
- The new seeds and all five families are more stringent than the original single-random-baseline cohort; they do not qualify as untouched independent FLA *variant* validation, since many variants were tried before.
- Equal 3030 planned fitness evaluations + equal 16 true simulator replay calls is not equal wall-clock runtime; report search time, selection time, simulation time and total time separately.
- Both strategies are pre-simulation screening, **not** online simulator-guided optimization. Screening advantages do not establish statistical or general FLA v12 superiority over NSGA-II.
