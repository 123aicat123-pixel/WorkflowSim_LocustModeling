# Mechanism audit: planner makespan ranking is less faithful than cost (2026-11-03)

## Evidence and reproducibility

- Original independent full-visited WorkflowSim replay, five? **four** DAG families and 2 seeds: [GitHub Actions run 41582476054](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41582476054). Eight original per-case artifacts are CyberShake_100, Epigenomics_100, Montage_100, Sipht_100, seeds 46 and 47. Each arm contributed its **complete set of distinct evaluated genotypes** from 80 true planned-objective function calls. Three solver arms per DAG/seed: v7 FLA, v12 FLA, costseed NSGA-II.
- Independent *reproduction using retrieved original Actions artifacts* was performed by [CI run 41590467870](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41590467870), source SHA `304b543b6e767d5049bfbb60e8d037627da2b5d8`. GitHub source `scripts/fla_rank_fidelity_diagnostic.py`, CI `.github/workflows/fla-planner-simulator-rank-diagnosis.yml`.
- Complete per-solver CSV and report: Actions artifact `planner-simulator-rank-fidelity-41590467870` (ID `13209399462`). The diagnostic joined *the original planned-front independently replayed points* with the extra all-visited independently simulated points. It asserts the exact unique-count and mapping uniqueness per solver and counts a candidate only once.
- An independent offline analysis of the same eight artifact ZIPs reproduced exactly the displayed mean Kendall tau-b and top-16 overlaps.

## Measured planner/simulator rank fidelity

| Objective | Mean Kendall tau-b | Mean discordant candidate pairs per solver/seed | Mean overlap of 16 planned-vs-simulator best genotypes | Mean absolute relative prediction error | Missed true single-objective extreme among planned top 16 |
|---|---:|---:|---:|---:|---:|
| Makespan | **0.93459** | **93.5** | **90.10%** | **2.2877%** | **0/24** |
| Cost | **0.99828** | **2.2** | **99.74%** | **0.0021%** | **0/24** |

The 24 solver/seed cases per objective are correlated within four DAG families and should NOT be treated as independent workflow families.

### Makespan fidelity by DAG

| DAG | Mean Kendall tau-b | Mean top16 overlap |
|---|---:|---:|
| CyberShake_100 | 0.96406 | 89.58% |
| **Epigenomics_100** | **0.84646** | **80.21%** |
| Montage_100 | 0.97940 | 97.92% |
| Sipht_100 | 0.94845 | 92.71% |

The lowest individual makespan Kendall value was **0.77669** for NSGA-II on Epigenomics_100 seed 47. On that same DAG/seed, FLA v12 had only **43.75%** overlap in the 16 best planned versus true simulator makespan genotypes. Mean absolute makespan prediction error in that arm was **7.83%**.

## Important interpretation

This confirms a **ranking distortion**: planned makespan is notably less stable than planned cost, particularly on Epigenomics. However, despite rank inversions, *the true single-objective minimum* was still captured by the top16 PLANNED single-objective assignments in each of these 80-evaluation histories. Therefore it would be incorrect to infer that every poor selected Pareto front is caused by failure to include the fastest schedule.

The separate 3030-evaluation, real K16 **extreme-band3** test [41588772142](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41588772142) was a negative ablation for v12 (mean HV vs original Pareto-cover **-0.1779%, 0/10 wins**). Its occasional improvement in minimum simulated makespan did **not** consistently increase aggregate HV. Do not recommend larger fixed extreme bands based on these same observed data.

## Next scientific gate

Before claiming novelty, formulate a *pre-simulation rank-robust Pareto screening* mechanism, trained or calibrated **only** on disjoint prior simulations. Freeze architecture and training data, then validate with 3030 planned evaluations and equal K=16 simulator calls on genuinely new DAG/VM seeds and configurations; compare Pareto-cover, scalar sweep and any learned method with family-aware uncertainty. Never use simulator outputs from unselected assignments to guide a prospective selection. Track selection overhead and how often extreme coverage trades against total simulated HV. These observations are diagnostic and do not prove FLA v12 optimizer superiority over NSGA-II.
