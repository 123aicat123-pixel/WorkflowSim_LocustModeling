# Actual prospective K24 WorkflowSim budget frontier and stop-risk counterexamples (2026-11-03)

**Research decision:** K16 is a promising economical replay budget under the currently tested settings, but a planner-HV plateau is NOT a scientifically valid safety bound on true simulation-HV. Keep the default `pareto-cover` selector. Do not deploy an adaptive early-stopping rule from these post-hoc observations.

## Provenance and independent source controls

- **Prospective run:** [GitHub Actions 41592705525](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41592705525), original code SHA `31326591a672f32a72e1771bbd0cf24be3f216e9`, 10/10 Java case jobs **PASS** plus final summary **PASS**.
- Each DAG/seed: 3 algorithms (FLA v7-costseed, FLA v12-hvbandit, costseed NSGA-II), **3030 actual planning objective calls per solver**, **exactly K=24 independently executed WorkflowSim replay assignments per solver**, all source SHA and genotype-history fingerprints preserved in per-job artifacts.
- Workflows: CyberShake_100, Epigenomics_100, Inspiral_100, Montage_100, Sipht_100. New optimizer seeds: **72 and 73**.
- Aggregate original report: `progressive-summary-41592705525`, GitHub artifact **13210708891**, including `progressive_k_hv.csv`, `progressive_k_marginal.csv`, `progressive_k_report.md` and source SHA.
- **Prefix interpretation:** the first 8 and first 16 in the *already selected, prospectively simulated 24 assignment order* are scored separately to construct a nested budget frontier. This is valid because the K24 selected candidate ORDER depends ONLY on planner objectives and genotype identity, not on future simulation labels. However, it is incorrect to say these experiments actually made only 8 or 16 simulator calls: **each job truly ran 24 calls**.
- The [independent 48-case Python/Java cross-language and prefix-nested selector CI 41592965499](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41592965499) checked ordering and budget nesting on fixed precision fixtures.
- HV reference per workflow family is frozen from the earlier independent five-seed Actions run `41572425682`, not adjusted to these seeds.

## Marginal simulator HV of the K8 / K16 / K24 prefixes

| Algorithm | K8 HV as % of K24 | K16 HV as % of K24 | Mean relative gain K8 to K16 | Mean relative gain K16 to K24 | K16 retained at least 99% of K24 |
|---|---:|---:|---:|---:|---:|
| FLA v7-costseed | 99.423% | **99.911%** | +0.496% | +0.089% | 10/10 |
| FLA v12-hvbandit | 99.204% | **99.899%** | +0.707% | +0.102% | 10/10 |
| NSGA-II costseed | 98.205% | **99.830%** | +1.674% | +0.170% | 10/10 |

These are **within-matched-solver**, per-case relative percentages; do not average raw HV across DAG families. Only 10 workflow/optimizer-seed cases exist, with 3 dependent algorithm arms each. K24 is not the complete 3030-visited simulator Pareto oracle, and no claim of universal K16 sufficiency follows.

## Actual planner HV plateau may hide true simulator HV benefit

A separate post-hoc analysis from the 10 original K24 raw real-simulator artifacts reproduced in [GitHub Actions 41593420372](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41593420372), source SHA `4373470b660d41aefbb36d8ad9476a1b48fe2db4`; artifact `planned-plateau-risk-41593420372` ID **13210758484** (`planned_plateau_report.md`, `planned_plateau_cases.csv`, `planned_plateau_thresholds.csv`).

Planned K16-to-K24 HV increase is calculated from planned makespan and planned cost only, using the same pre-frozen family reference. Real increase is observed afterward from independently simulated K24 order. The following **counterfactual thresholds were NOT executed as adaptive policies**:

| Hypothetical stop at K16 when planner's forecast gain is below | Stop cases of 30 | Potential simulator calls saved | Cases that would miss >0.1% true HV gain | Worst missed true gain |
|---|---:|---:|---:|---:|
| 0.01% | 7 | 56 | 1 | 0.103% |
| 0.05% | 13 | 104 | 2 | **0.620%** |
| 0.10% | 16 | 128 | 2 | **0.620%** |
| 0.20% | 28 | 224 | 10 | **0.620%** |

**Concrete counterexamples:**

- Epigenomics_100, seed 73, NSGA-II: planned K16-to-K24 HV gain only **+0.01409%**, but actual WorkflowSim HV gain **+0.62016%**.
- Epigenomics_100, seed 72, FLA v12: planned **+0.10156%**, actual **+0.52201%**.
- Epigenomics_100, seed 72, FLA v7: planned **+0.00039%**, actual **+0.10339%**.

Thus a planner-only HV plateau is **NOT an upper bound** on real simulator HV improvement. Any proposed adaptive stopping needs a defensible, distribution-aware bound or risk-control calibration trained on separate DAGs, and truly prospective testing on new optimizer seeds, VM heterogeneity and communication conditions. Picking a threshold after inspecting the same 30 cases and claiming held-out superiority would be invalid.

## Research gate and limitations

1. Keep `pareto-cover` as default for now. Pareto coverage has positive real K16-vs-random and K16-vs-scalar controls, while the attempted fixed extreme-band and epsilon models failed to generalize.
2. A viable innovation would explicitly control the **number of actual simulator calls, estimation error, and risk of missing important simulated Pareto points**, with external calibration data and cost-aware stopping.
3. Compare actual elapsed time and payoff, not merely fixed search counts and replay-call counts; original `_summary.csv` captures search wall-clock but not a complete per-assignment simulator timing breakdown.
4. These measurements concern the post-search simulator evaluation protocol. They **do not prove FLA v12 optimizer superiority over equally initialized NSGA-II**.
