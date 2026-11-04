# First actual DURING-EVOLUTION dual-fidelity FLA/seeded NSGA-II pilot: result and rejection decision (2026-11-04)

**Status: implementation, original FLA and NSGA search passes, exact K8 real simulator replay and independent HV audit PASS. Claim of stable FLA algorithm superiority FAIL. The simple fixed 1%-near-skyline gate almost always exhausts its READY budget and does NOT demonstrate useful fidelity resource targeting. Do not promote into default or call it FLA v20.**

## Immutable preregistration and original execution
- Frozen prior to outcomes in `docs/FLA_EVOLUTION_FIDELITY_FIRST_GATE_FROZEN_2026-11-04.md`, commit `f8bb8103`. Two known historical DAX instances CyberShake_50 and Sipht_60, one seed 801, 16 default VMs, normal FIFO runtime. Population 30, generations 100, exact 3030 original FLA-v12 or NSGA-II source fitness visits, and exactly K8 actual WorkflowSim simulator assignments per solver/mode.
- Four locked modes for BOTH optimizers: `old` original stage-in insertion; `full-ready` original unbudgeted READY TaskID; `periodic` mixed fidelity with progressively earned maximum 378 READY decoder calls; `risk` the same mixed fidelity with 1% Pareto-near cheap-skyline gate. Both mixed modes use a first-write cache mapping each physical Task→VM assignment to one immutable returned fitness per optimizer run; duplicate visits still count toward 3030 but return the first score. Same code `BudgetedEvolutionFidelityObjective` instantiated in both original optimizer decoders, opt-in only via `dagfla.evolutionFidelity`.
- Original real execution [Actions 41780754595](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41780754595) **8/8 jobs SUCCESS**, exact 3030 original counted fitness visits and K8 assignment-identity-confirmed actual WorkflowSim replays per solver/mode, therefore **128 real simulations**, 16 solver-mode actual K8 sets.
- Original independent all-case audit attempt [41780979446](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41780979446) failed before analysis due to an **extra closing bracket in an analysis-only Python report definition**, not a source Java/optimizer/simulator failure. Fixed only Python report syntax in commit `0d49acd`, no model, search, fitness or actual source changes.
- [Successful independent complete 128-actual audit 41781120539](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41781120539) PASS. Checks all 8 immutable source artifacts, 3030 original fitness records, finite actual Makespan/Cost, 8 unique Task→VM simulator assignments per arm, valid exact measured evolutionary cheap/READY/cache trace and READY quota ≤378. Scores true normalized K8 HV on ONE shared 1.5× (plus archived 3.0× sensitivity) actual reference from all 8 solver×mode K8 sets *within each DAG*.
- `tests/org/workflowsim/planning/BudgetedEvolutionFidelityObjectiveTest.java` verifies duplicate genotype immutable returned objectives, maximum released READY tokens per counted visit, both modes, cheap/READY/cache budget accounting and explicit context cleanup. Existing `FLAScheduleEvaluator` and `NSGAIIPlanningAlgorithm` original default fitness remain unchanged with `dagfla.evolutionFidelity=off`. The adapted `FLAResearchExperiment` exports an opt-in independent `_evolution_fidelity.csv` with recorded visits/cheap calls/ready calls/cache hits/budget/time.

## Full real K8 Pareto HV (common true 1.5× reference within each workflow)

| Workflow | Solver | Original OLD | Full READY | Mixed periodic | Mixed risk | Periodic READY calls | Risk READY calls |
|---|---|---:|---:|---:|---:|---:|---:|
| CyberShake_50 | FLA v12 | **0.48354338** | 0.48166510 | 0.48010942 | 0.48012167 | 378 | 378 |
| CyberShake_50 | NSGA-II seeded | 0.49143415 | **0.49666053** | 0.48914731 | 0.49233501 | 378 | 378 |
| Sipht_60 | FLA v12 | 0.24464343 | **0.26246421** | 0.25991996 | 0.26126097 | 378 | 378 |
| Sipht_60 | NSGA-II seeded | **0.26264292** | 0.26264248 | 0.26260760 | 0.26263311 | 378 | 377 |

This is actual simulator K8 HV, NOT the 3030 planned objective values or a complete attainable true Pareto front.

## Paired true objective gains/losses
- CyberShake_50 FLA: periodic−OLD **−0.00343396**; risk−OLD **−0.00342171**; periodic−full READY **−0.00155568**, risk−full READY **−0.00154343**. The original cheap decoder beats BOTH budgeted methods.
- CyberShake_50 NSGA-II: periodic−OLD **−0.00228684**, risk−OLD **+0.00090087**; full READY remains best; risk−full READY **−0.00432552**.
- Sipht_60 FLA: periodic−OLD **+0.01527653**, risk−OLD **+0.01661754**, but neither beats full READY; risk−full READY **−0.00120324**. This strongly configuration-dependent direction is exactly why a single good DAG cannot support a new solver claim.
- Sipht_60 NSGA-II: both budgeted modes have small HV losses vs OLD and full READY.
- The risk gate consumed 378/378 ready calls in 3 of 4 solver×DAG cases, and **377/378** in the fourth; the 1% cheap-skyline rule did not materially reduce fidelity spending relative to fixed periodic scheduling. Its tendency to consume almost every earned token means it cannot yet claim meaningful adaptive budget targeting.

## Computation cost / fairness warnings
- This is TRUE inside-evolution two-fidelity mixed scoring, not merely post-search K8 selection. Original counted genotype *visits* remain 3030, but repeated mappings are served from the first-write cache in mixed modes while OLD and FULL READY do not cache, so matched nominal visits do **NOT** imply equal actual decoder computations. Computational CPU parity is **unproven**.
- Different genotypes may have original OLD versus READY fitness, which may differ enough to distort exact Pareto comparisons. First-write caching solves contradictory repeat scores, but DOES NOT mathematically calibrate the two objective landscapes; this limitation must not be hidden.
- Observed original source searchWallClockMillis are noisy across runner jobs. CyberShake_50 original FLA 664 ms vs full READY 792 ms vs periodic 845 ms vs risk 966 ms; Sipht_60 28,888 ms OLD vs 34,033 ms READY vs 20,345 ms periodic vs 36,115 ms risk. This small-run variance and different CPU work cannot establish a consistent speedup.
- Only 2 historically used DAG families and one RNG seed, K8 simulator replay subset, no unseen family holdout, no uncertainty calibration test or matched end-to-end CPU-time budget. No statistical paper-level inference; this is a narrow negative / mixed engineering pilot.

## Decision
1. **Do not promote** the naive risk gate or mixed-fidelity algorithm into default search. Both fail to establish a stable FLA or NSGA-II Pareto HV advantage, and risk-mode high-fidelity call placement is not demonstrably superior to a simple periodic budget.
2. The key remaining mathematical issue is **comparable objective scales under mixed fidelity**. Candidate research should make cross-genotype fitness consistent, e.g. cheap objective plus a separately calibrated forecast/error-bound representation, then only high-fidelity ranking refinements with a common comparable score. Do NOT claim a calibrated model until training and strict unseen-family validation have occurred.
3. To isolate fidelity selection, next benchmark should compare **a matched cache in OLD, FULL READY, PERIODIC and RISK arms** and give every algorithm both equal counted evaluations and an explicit second CPU-time-matched control. Avoid selecting gate parameters post hoc from these two pilot DAGs.
4. Any full validation needs independent new DAG-family holdouts, additional seeds, multiple VM speed/price regimes, actual K16+ true HV/IGD+, and published non-FLA multi-fidelity baselines. Related work already exists: a different genotype representation alone is not publication novelty.
5. All code, regression tests, CI, and negative raw data preserved on `fla-baseline`; `master`, default FIFO and original validated FLA-v12/NSGA-II mode stay intact.

**Final verdict: genuine inside-evolution engineering integration PASS; adaptive quality improvement NOT demonstrated.**
