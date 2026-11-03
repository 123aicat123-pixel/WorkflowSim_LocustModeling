# Fixed WorkflowSim replay budget: development and new-seed validation (2026-11-03)

**Scope:** reproducible retrospective selection only, `fla-baseline`. **No claim of direct improvement in optimization or runtime.** Original `master` remains untouched.

## Provenance

- Development full-history original simulator oracle: [Actions run 41580592118](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41580592118), 3 DAG families × 2 seeds × 3 solver arms.
- New-seed, different-family simulator oracle and **successful** budgeted-screening evaluation: [Actions run 41581956200](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41581956200), source `2935ed959b0c259aa76ddafaaa64862588f2ec2b`; aggregate artifact `budget-validation-report-41581956200` ID `13205493090`. Full `replay_budget_scores.csv`, `replay_budget_winners.csv`, `replay_budget_report.md`, and per-seed replay CSVs retained as Actions artifacts.
- Executable evaluation script: `scripts/fla_replay_budget_audit.py` (selection uses **planned makespan and planned cost only**).
- Separate unit-test workflow confirmed 2D hypervolume correctness on a hand case, selection input-order invariance, exactly K unique selections, and reproducible fixed hashes. (The unit test expected HV was corrected from an erroneous 14 to 16 before the successful run.)

## Study design

Each solver (DAG-Pareto-FLA v7, DAG-Pareto-FLA v12, cost-seeded NSGA-II) has 80 **search fitness evaluations**, exactly the same two deterministic starting cost schedules, and independent WorkflowSim replays of **all its distinct visited assignments** to establish a reference oracle. A frozen HV reference for each DAG family is calculated using only originally replayed planning-nondominated assignments, and is held fixed for all algorithms, seeds, screening policies, and budgets in the same DAG family.

Four policies screen `K ∈ {8,16,24,32}` **unique** assignments per algorithm using only planning information: Pareto layer first with greedy normalized max-min diversity; half Pareto coverage and half hash-seeded random; a fixed low-discrepancy scalar-weight sweep covering extremes first; and hash-seeded random. Stochastic policies have 16 deterministic repeats per case (these repeats are NOT independent workflow observations). The held-aside-for-screening validation cohort uses Epigenomics_24 and Inspiral_30 with seeds 41, 42 and 43, distinct from the three-family development sample.

The full-history oracle has already paid for *all* simulator calls, so this tests **retrospective selection quality at hypothetical replay budget K**, not an actual saving in experimental runtime. It is not a global Pareto oracle and not an on-line adaptive simulator-in-the-loop algorithm.

## Mean HV recovery against each solver's full visited history

| Cohort | K | Pareto-cover | Half-cover/half-random | Extreme-first scalar sweep | Random |
|---|---:|---:|---:|---:|---:|
| Development (CyberShake_30, Montage_25, Sipht_30; 2 seeds) | 8 | 99.259% | 95.491% | 93.764% | 80.872% |
| Development | 16 | **99.604%** | 99.414% | 97.463% | 90.702% |
| Development | 24 | 99.861% | 99.701% | 98.772% | 94.623% |
| Development | 32 | 99.872% | 99.785% | 99.834% | 96.528% |
| New-seed cross-family validation (Epigenomics_24, Inspiral_30; 3 seeds) | 8 | 99.216% | 95.252% | 92.931% | 80.084% |
| Validation | 16 | **99.706%** | 99.345% | 97.767% | 89.015% |
| Validation | 24 | 99.983% | 99.697% | 99.135% | 92.589% |
| Validation | 32 | 99.997% | 99.796% | 99.678% | 94.217% |

Means include all three solvers and workflow/seed cases, not an aggregation of unrelated raw HV units. A cohort contains 18 unique solver-case observations; random and hybrid estimates average 16 deterministic samples per observation. Do not use these 16 draws as independent replicates in inferential tests.

### Why these results are not yet a complete win

- At **K=16**, Pareto-cover still selected the wrong *best-HV solver* in **1/6** validation cases: `Inspiral_30` seed 41, where it ranked **v7** first even though the all-visited simulator front ranked **v12** first. At K=32, this particular validation sample had **0/6** winner mismatches.
- At K=16, the lowest individual Pareto-cover recovery was **95.137%**, on `Epigenomics_24` seed 43 for seeded NSGA-II. The excellent mean masks individual errors.
- A different, predeclared extreme-first scalarization baseline achieved **97.767%** mean recovery at K=16 on validation. It is competitive and must not be described as a strawman.
- A `K=16` budget does **not** mean the optimizer performed only 16 objective evaluations: it still used **80 planning objective evaluations**, plus a hypothetical 16 simulator observations per solver.
- These new seeds are a screening-policy validation sample, not an untouched end-to-end algorithm-development dataset. The FLA variants themselves have been tuned extensively on similar workflow families.
- Improvement in fixed-budget screening **does not** show that v12 is a better workflow optimizer than NSGA-II; retention of each solver's own front is a separate question from quality of that full front.

## Next controlled scientific gate

Freeze the policy, evaluate on larger 50/100-task workflows with new seeds and diverse VM price/communication regimes, and design a **prospective** simulator-in-the-loop implementation that genuinely spends only K simulator calls while preserving separate and identical search-evaluation budgets. Compare not only HV recovery but incorrect winner rate, regret, cost/makespan extreme protection, wall-clock time, and paired uncertainty by workflow family. All unsuccessful and inconclusive results must be retained.
