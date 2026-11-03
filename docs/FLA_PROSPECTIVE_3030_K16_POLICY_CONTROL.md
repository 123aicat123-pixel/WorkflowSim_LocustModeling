# Real K=16 WorkflowSim replay policy control after 3030 optimizer evaluations

**Experiment date:** 2026-11-03. **Branch:** `fla-baseline` (do not touch `master`). This file records a **prospective** simulator-call-limited control, as distinct from the retrospective full-oracle screening studies.

## Provenance

- [Actual GitHub Actions run 41584672254](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41584672254): six three-arm paired workflow/seed jobs plus aggregation, all completed successfully.
- Source commit: `63346dd4193457e717c0483c36a22dc22e974a79`.
- Pooled report artifact `equalpolicy-report-41584672254`, ID `13207726897`, contains `prospective_policy_report.md` and `prospective_policy_scores.csv`. All six per-case artifacts contain the complete original summaries, actual K replay objective CSVs, search logs, compilation logs and source SHA.
- Reusable implementation: `examples/org/workflowsim/examples/planning/FLAResearchExperiment.java` using `-Ddagfla.budgetReplayK=16` with `-Ddagfla.budgetReplayPolicy=pareto-cover` or `random`. Comparator analysis: `scripts/prospective_policy_compare.py`.

## What was actually controlled

Three algorithms: DAG-Pareto-FLA v7-costseed, DAG-Pareto-FLA v12-hvbandit and NSGA-II costseed; three workflow families Montage_25, Inspiral_50 and CyberShake_100; two paired seeds 53, 54 per DAG. Each policy had its own **3030 actual planning objective evaluations per algorithm** and **exactly 16 real independent WorkflowSim simulator replays per algorithm**. Thus each solver receives the same two budget dimensions in the policy comparison. The two policies' optimizer runs were repeated with the same deterministic seeds/initial schedules. The CI asserts equality of each matched solver's source archive, distinct evaluated genotype count and planned non-dominated archive count across both screening policies. It also asserts replay assignment validity, independent planned objective fidelity and precise replay counts.

- **Pareto-cover** selects from evaluated distinct genotypes by planned Pareto layers and normalized max-min spread, without consulting simulator labels.
- **Random** selects from the same planned history using deterministic genotype ordering and a per-solver/seed pseudorandom permutation. One random draw per case, not a distribution of 30 independent controls.
- All HV comparisons in this experiment use one common **per-DAG-family reference**, constructed from the union of the two policies' selected K simulated assignments across solvers and both paired seeds. This is a common comparison reference but is **post hoc**, not a preregistered external objective bound. Raw HV across families is never averaged.

## Actual simulator-HV gain of Pareto-cover over random at equal K=16

| Workflow | Seed | v7 | v12 | NSGA-II |
|---|---:|---:|---:|---:|
| CyberShake_100 | 53 | +1.532% | +1.484% | +4.332% |
| CyberShake_100 | 54 | +0.722% | +4.741% | +3.127% |
| Inspiral_50 | 53 | +1.585% | +4.265% | +6.260% |
| Inspiral_50 | 54 | +1.731% | +2.846% | +6.470% |
| Montage_25 | 53 | +5.627% | +0.979% | +5.956% |
| Montage_25 | 54 | +8.673% | +1.385% | +22.546% |
| **Mean paired relative advantage** | | **+3.312%** | **+2.617%** | **+8.115%** |
| **Positive paired cases** | | **6/6** | **6/6** | **6/6** |

**Interpretation:** All **18/18 algorithm–case comparisons** had greater actual K16 WorkflowSim HV under the Pareto-cover selector than under the single deterministically seeded random control. This provides stronger evidence than the earlier retrospective screening only: the simulator budget was genuinely enforced during each run and no full-oracle simulator labels were used to pick schedules.

**Crucial limitation:** the result is **Pareto-cover screening vs one random draw**, not FLA superiority over NSGA-II and not a claim of statistically significant gains across independently sampled workflows. In particular, the separate [3030×K16 solver comparison 41584279115](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41584279115) found v12 averaged **−0.227%** relative simulated HV against equally initialized NSGA-II over six pairs. Screening improvements should not be wrongly attributed to the FLA search operator.

## Publication-quality next requirements

1. Replace the single random control draw with 20–30 independently seeded random screening draws *per fixed optimizer history*, keeping exactly K simulator evaluations each (and report the underlying stochastic uncertainty without counting repeated draws as separate DAGs).
2. Compare against a serious equal-K extreme-first scalarized and/or knee/uncertainty-aware selector, not only random. Preserve equal search, simulation, and execution-time reporting.
3. Expand DAG families, seeds, VM heterogeneity, pricing, data-transfer bottlenecks and objectives before manuscript claims; use family-clustered uncertainty/paired statistics with caveats about multiple variant selection.
4. Test adaptive K budgets and externally fixed HV reference points, measuring cost/makespan extremes and actual total wall-clock time rather than only HV.
5. Keep the known negative CyberShake v12 comparisons and precision-correction provenance, and keep the MATLAB-to-discrete FLA fidelity and MLEAO source-reconstruction caveats explicit.

**Conservative claim:** a planned-Pareto-and-diversity replay selector can improve the actual, budget-constrained simulation-observed Pareto front over a deterministically seeded uniform random selector on these six examples, for the same search and replay evaluation budgets. Further evidence is required for broad practical, statistical or algorithm-novelty claims.
