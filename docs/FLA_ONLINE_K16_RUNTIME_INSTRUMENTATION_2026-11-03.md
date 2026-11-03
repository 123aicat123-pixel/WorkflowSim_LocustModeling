# Causal K16 replay screening runtime instrumentation, first smoke (2026-11-03)

**Status:** engineering profiling validation, not a statistically adequate runtime benchmark. Source is Java `FLAResearchExperiment.java`; new trailing summary CSV fields `selection_ms`, `replay_ms`, `search_selection_replay_ms` preserve existing `search_ms`.

## Provenance

- [GitHub Actions run 41597793461](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41597793461), source code SHA `7ded8d550fda711475beb558ef68fffadc8c23a4`; artifact `online-runtime-profile-41597793461`, ID `13212872410`.
- Fixed engineering smoke: `Montage_25`, seed 97, 8 population, 9 generations, **80 planned-objective evaluations** and **16 actual WorkflowSim replays** per algorithm and policy. All 4 policies/3 solvers have the **same ordered planner/genotype history SHA**. Python CI verifies `search_ms + selection_ms + replay_ms = search_selection_replay_ms` within expected millisecond rounding tolerance.
- Selector timing includes initial shortlist/coverage selection plus all sequential online choices, not search or simulation. Replay timing includes the 16 actual independent WorkflowSim calls; it is not merely time to read an archive. Search timing is the solver's existing instrumented wall-clock.
- Metrics below are per-algorithm/one-run **wall-clock samples, affected by JVM warm-up, runner CPU scheduling, cache and runtime variance**. They are not directly comparable statistical claims. Simulation wall-clock changes despite same K because different assignments can have different simulator overhead.

## One-run observed timings (milliseconds)

| Solver | Replay selection policy | Search | Selection overhead | Real simulator replay |
|---|---|---:|---:|---:|
| FLA v7 | Pareto-cover | 55 | 3.416 | 162.425 |
| FLA v7 | Online planned-only greedy HV | 47 | 13.765 | 146.133 |
| FLA v7 | Online observed-front greedy HV | 47 | 15.960 | 164.424 |
| FLA v7 | Online 1NN residual + observed-front HV | 53 | 14.351 | 152.061 |
| FLA v12 | Pareto-cover | 42 | 1.174 | 90.187 |
| FLA v12 | Online planned-only greedy HV | 37 | 6.307 | 70.631 |
| FLA v12 | Online observed-front greedy HV | 40 | 9.173 | 91.513 |
| FLA v12 | Online 1NN residual + observed-front HV | 43 | 8.877 | 93.130 |
| NSGA-II | Pareto-cover | 14 | 0.612 | 82.246 |
| NSGA-II | Online planned-only greedy HV | 12 | 5.095 | 56.332 |
| NSGA-II | Online observed-front greedy HV | 13 | 7.346 | 77.365 |
| NSGA-II | Online 1NN residual + observed-front HV | 14 | 7.743 | 82.355 |

**Interpretation:** Sequential HV greedy selection can cost several milliseconds more than Pareto coverage on this small run, but no reliable ratio for 100-task cases follows. A publication-grade runtime comparison needs multiple independent runs/seeds, CPU and VM specification, total wall-clock, exact replay count and selection/runtime distributions. The instrumentation does not validate algorithm superiority.

The running large `fla-online-factorial-100task.yml` experiment launched at an *earlier source commit* and is not claimed to contain these new timing fields. Never mix its summary schema with this later instrumentation without checking source SHA.
