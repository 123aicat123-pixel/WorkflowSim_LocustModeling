# FLA real K16 replay: four-draw controlled random benchmark (2026-11-03)

**Purpose:** Address the single-random-draw weakness of previous Pareto-cover versus random comparison. This is a pilot, not inferential publication-grade confirmation.

**Primary executed experiment:** [GitHub Actions 41585685819](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41585685819), source commit `e2c78948ff0d0b7485c46eb6e3a0d74734a2ee6c`. Artifact `repeats-summary-41585685819` (ID `13208195045`) preserves `random_repeat_report.md`, `random_repeat_case_summary.csv`, `random_repeat_paired.csv`, `random_repeat_hv.csv` and `source-sha.txt`; 24 per-job artifacts have exact Java source manifests, planning logs, actual WorkflowSim replay outputs and control protocol.

**Protocol:** Montage_25, Inspiral_50, CyberShake_100; search seeds 53 and 54; algorithms DAG-Pareto-FLA v7-costseed, v12-hvbandit and cost-seeded NSGA-II; four different random selector repeats 0..3 per solver-seed. Each *policy run* uses 3030 real planning objective evaluations and exactly 16 real WorkflowSim simulations, checked by its CI job. The Java random selector receives repeat index using `-Ddagfla.budgetReplayReplicate` (default 0 to preserve all historical runs); Pareto-cover is deterministic. Source revision `8fd480b156185d65f81148e052cdb3e598f07ac3` added the replay-only repeat salt without altering optimizer search.

**HV reference is pre-frozen from PRIOR Actions run 41584672254**, not from observed repeat results: CyberShake_100=(7421.5516,2911.5777924999998), Inspiral_50=(8423.484174999998,6833.036574999994), Montage_25=(128.9026,120.508165). Raw HV across DAG families is not averaged; relative improvements are computed within each paired case.

| Optimizer | Mean within-case paired relative HV gain, Pareto-cover vs random | Positive matched comparisons | Worst paired gain |
|---|---:|---:|---:|
| DAG-Pareto-FLA v7-costseed | **+3.350%** | **24/24** | +0.080% |
| DAG-Pareto-FLA v12-hvbandit | **+2.864%** | **24/24** | +0.705% |
| NSGA-II costseed | **+8.231%** | **24/24** | +2.923% |

This totals 72/72 positive *draw-level* comparisons but only six distinct workflow/optimizer-seed cases, with three correlated algorithm arms each. Four repeats are conditional on one deterministic optimizer history, not four independent DAG instances; don't use these 72 as the denominator for statistical tests treating them as independent. Search selection is still guided by the stage-in-aware planning estimate, not simulated objective feedback. Optimizer superiority of v12 over NSGA-II remains unproven. The stronger average gain for NSGA-II illustrates why the result belongs to **general Pareto screening under fixed simulation budgets**, not FLA novelty.

**Next pre-specified check:** increase repeats to 20+ without changing the selector or HV reference; add independent optimizer seeds and workflow families, a competitive extreme-first screening baseline, and family-aware uncertainty estimates. Keep negative cases rather than altering K or reference after seeing results.
