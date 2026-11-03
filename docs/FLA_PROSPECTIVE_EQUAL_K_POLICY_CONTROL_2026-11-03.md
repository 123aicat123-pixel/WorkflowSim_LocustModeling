# Prospective equal-K WorkflowSim screening: Pareto coverage vs random (2026-11-03)

**Research status:** a controlled positive *screening policy* result, not proof that DAG-FLA v12 is a generally superior optimizer. Changes are isolated to `fla-baseline`, not `master`.

## Primary evidence

- [GitHub Actions run 41584672254](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41584672254), source commit `63346dd4193457e717c0483c36a22dc22e974a79`.
- Full report and per-arm raw scores: Actions artifact `equalpolicy-report-41584672254`, ID `13207726897`. Contains `prospective_policy_report.md`, `prospective_policy_scores.csv`, `source-sha.txt` and audit log. Six per-case artifacts retain the actual Java/WorkflowSim replay CSV and all logged assertions.
- Reproduction workflow in branch: `.github/workflows/fla-prospective-policy-control.yml`.
- A second, separately authored six-case smoke workflow [run 41584797207](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41584797207) has also completed all six case-level jobs successfully under the same general experiment design. The primary quantitative values below are **from 41584672254**, not pooled across potentially differing source commits.

## Experimental design

Three workflow families `CyberShake_100`, `Inspiral_50`, `Montage_25`, seeds `53,54`. Three solver arms per paired case:
- `DAG-Pareto-FLA[v7-costseed]`
- `DAG-Pareto-FLA[v12-hvbandit]`
- `NSGA-II[costseed]`

Each policy/solver run receives exactly **3030 true objective-function fitness calls**, the same initial two cost-seeded assignments, and exactly **K=16 actual, independent WorkflowSim replay observations**. Selection policies act *after* the planned search; coverage uses planned makespan, planned cost and genotype identity, random uses genotype identity plus a deterministic random shuffle. No true simulated objective is supplied to a selection policy. Within each family the post-hoc reference point is derived from the union of K-selected simulated points across both policies, solvers and seeds, and then shared across all comparisons in that family.

## Simulator-HV relative improvement of Pareto coverage versus one random screening draw

| Solver | Mean six paired relative HV improvements | Cases where coverage beats random |
|---|---:|---:|
| DAG-Pareto-FLA v7-costseed | **+3.312%** | **6/6** |
| DAG-Pareto-FLA v12-hvbandit | **+2.617%** | **6/6** |
| Cost-seeded NSGA-II | **+8.115%** | **6/6** |
| All three solver arms | — | **18/18** |

Largest single observed increase: `Montage_25`, seed `54`, cost-seeded NSGA-II **+22.546%** relative HV.

**Important interpretation:** the improvement occurs for all three optimizers, and the relative improvement of NSGA-II is greater than that of either DAG-FLA version in this cohort. Thus it is evidence in favor of a planned Pareto-coverage *simulation screening method* rather than evidence that FLA v12 improved the actual search. The three arms are correlated observations within each of only six workflow/seed cases, not 18 independent experimental replicates.

## Scope limits and next preregistered gate

- Random control includes only **one** deterministic random draw per arm/seed. Add repeated random draws with known seeds while keeping the same K and search count; use confidence intervals clustered by workflow family.
- The common HV reference is **post-hoc**, not pre-registered. Repeat sensitivity with a frozen external reference and monitor Pareto extreme loss.
- Because policies select different candidates, equal K does not mean equal *wall-clock* cost. Measure optimizer time, selection time and independent simulator replay time separately.
- Six paired workflow/seed cases are insufficient to establish broad statistical superiority. Expand unseen DAG families, independent seeds, VM heterogeneity and cost/communication regimes.
- This is **real prospective K-limited replay**, but the search itself remains driven by the planned stage-in-aware estimator rather than simulator-in-loop feedback. Avoid calling it a fully simulator-guided optimizer.

## Independent second-run reproducibility check

- [Second GitHub Actions run 41584797207](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41584797207), source commit `3ad0109c5468ec5095ba5e9724103629c80ddd5d`, also completed **6/6 paired jobs successfully**.
- Downloaded all six independent per-case artifacts and recomputed 2D non-dominated hypervolumes from **raw actual WorkflowSim makespan/cost CSV values** under one post-hoc shared union reference per family. The recomputed mean relative benefits match the primary report to displayed three decimal places: v7 **+3.312% (6/6)**, v12 **+2.617% (6/6)**, NSGA-II **+8.115% (6/6)**.
- Exact recomputed means from the second run were **+3.31166%**, **+2.61658%**, and **+8.11508%**, respectively. A repeated deterministic run at the same seeds is **not** independent statistical replication; it does validate repeatability of the implementation and scoring procedure. Independent random seeds, pricing/VM regimes and workflow families remain necessary.
