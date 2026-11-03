# Negative controlled result: extreme-band3 did not improve K16 Pareto screening (2026-11-03)

**Decision: do not promote `extreme-band3` to the default screening policy.** Preserve the original `pareto-cover` as the validated candidate and keep `extreme-band3` as an optional ablation for reproducibility. Scope: branch `fla-baseline` only; do not touch master.

## Provenance and preregistered choice

- **Authoritative Actions run:** [41588772142](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41588772142), source SHA `894580f0e40f4bc74b0a8dfa45e6714ba14a9c17`; 10 paired workflow/seed jobs plus aggregation succeeded.
- Aggregated original source artifacts: `band3K16-report-41588772142` ID `13209656317` contains `band3_paired.csv`, `band3_scores.csv`, `band3_report.md`, `audit.log`, `source-sha.txt`. Per-job originals include real WorkflowSim makespan/cost per assignment, exact visited-history SHA-256 and budget logs.
- Java implementation: `FLAResearchExperiment.budgetedExtremeBand3()`, property `-Ddagfla.budgetReplayPolicy=extreme-band3`, default remains `pareto-cover`. Implementation uses planned makespan/cost only and reserves **at most three distinct planned objective points from each extreme** before filling remaining slots with standard Pareto/max-min coverage. K=16 is unchanged; search methods unchanged.
- Independent Python reference: `scripts/fla_replay_budget_audit.py:extreme_band3()`. [Cross-language CI 41588523717](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41588523717) passed **48/48** fixture/budget/policy checks for exact Java/Python selected genotype order.
- `scripts/fla_extreme_band3_analysis.py` produced frozen-reference report. Five DAG families CyberShake_100, Epigenomics_100, Inspiral_100, Montage_100, Sipht_100, new seeds **64,65**. All three algorithms (FLA v7, FLA v12 and NSGA-II) get **3030 genuine planned-objective evaluations and K=16 actual independent WorkflowSim replays** per policy.
- The per-family HV reference is fixed from an **older** benchmark Actions `41572425682`, not changed to fit this outcome. All three screening policies within a workflow/seed/algorithm used the **exact same ordered unique visited genotype and IEEE-double-bit planned-objective SHA-256**.

## Verified 100-task results

| Solver | Mean relative simulator-HV band3 versus original Pareto-cover | Band3 wins versus cover | Mean relative band3 versus scalar-sweep | Band3 wins versus sweep |
|---|---:|---:|---:|---:|
| DAG-Pareto-FLA v7-costseed | +0.1605% | **2/10** | +0.8522% | 10/10 |
| DAG-Pareto-FLA v12-hvbandit | **-0.1779%** | **0/10** | +1.0712% | 8/10 |
| NSGA-II costseed | **-0.0452%** | **1/10** | +2.2694% | 10/10 |
| **All algorithm-case contrasts** | — | **3/30** | — | **28/30** |

**Failure case to retain:** Epigenomics_100 seed 64, FLA v12, band3 simulator HV is **1.1499% lower** than standard Pareto-cover, even though band3 obtains a faster minimum simulated makespan (36361.8555 versus 37342.2300). This exposes a trade-off between preserving one objective extreme and preserving the *overall* Pareto hypervolume. Under Sipht_100 seed 64 NSGA-II, band3 does improve HV **+0.8534%** and finds a faster minimum simulated makespan (2710.4030 versus cover 2786.8075), but this isolated win does not generalize to the other 29 comparisons.

## Scientific interpretation

A hard quota for several *planned*-extreme candidate points is **not** a validated improvement over Pareto coverage, especially not for FLA v12. Protecting planned extremes does not guarantee the selected points are extreme in true simulator objectives, and it removes K-limited slots from useful diverse Pareto solutions. Do not tune the quota from these 64/65 outcomes and retest on the same seeds as though held out.

More principled next research direction: quantify the discrepancy between *planned objective ranks* and *simulator ranks* on independent full-history replay cohorts, identify the task/VM regimes that reorder candidates, and test a predeclared prediction-uncertainty or rank-correction selector on a genuinely new workflow/seed/VM regime with fixed simulator budgets. Such an approach must not read true simulation labels of unselected schedules at selection time, and must report both accuracy and wall-clock cost.

**Limits:** 30 algorithm contrasts share only 10 workflow/seed cases across five DAG families. New seeds are a conditional follow-up to observed Sipht failures and are not a fully untouched publication-quality cohort. Equal fitness-call and simulator-call budgets do not establish equal elapsed time. No claim is made that FLA v12 is generally better than NSGA-II.
