# Negative research gates: cross-DAG makespan correction and epsilon-dominance screening (2026-11-03)

**Status: reproducible negative results. Neither method is promoted to the default scheduler/screening policy.** The current default remains `pareto-cover` on `fla-baseline`. `master` is untouched.

## Immutable provenance

- Independently simulated complete distinct visited history from [Actions 41582476054](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41582476054): original DAG100 CyberShake, Epigenomics, Montage and Sipht, seeds 46 and 47, three algorithms v7/v12/NSGA-II.
- [Reproduced from the SAME eight original GitHub artifact bundles in Actions 41592323639](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41592323639) using analysis SHA `94a09079f650fff5f5059c97a9e3540689d29de0`, artifact `rank-robustness-negative-gates-41592323639`, ID `13210382416`.
- Source scripts: `scripts/fla_rank_generalization_gate.py` and `scripts/fla_epsilon_dominance_gate.py`. The Actions artifact preserves exact Python dependencies, original source pointer, all fold and case CSVs and both reports.
- Full oracle contains **1,859 distinct-within-solver observations** across 24 solver-case histories. Different algorithms may revisit the same genotype; do not mistake these for 1859 independent DAGs.
- No simulation labels of held-out workflow families were supplied to the correction models at training time. Simulation labels were used *after selection* to score the epsilon heuristic only.

## Gate A: leave-one-whole-DAG-family-out makespan residual correction

Models use planned makespan/cost, 16-VM allocation fractions and mapping-derived load concentration/variance/switching. Hyperparameters were fixed before the analysis: median global residual, standardized Ridge alpha 100 and RF 100 trees max-depth 5, min-leaf 25. Four folds, each holding out an entire DAG family.

| Method | Overall held-out mean absolute relative makespan error |
|---|---:|
| **Original planner (no correction)** | **2.2843%** |
| Global median residual shift | 2.2892% |
| Ridge regression | 5.3426% |
| Random forest | 4.4190% |

The original planner also retained better Kendall ordering and planned-versus-true top16 alignment than the learned regressors on these held-out families. The result **does not rule out all learning methods**, but demonstrates that these fixed generic allocation features are an unsafe unvalidated correction on heterogeneous DAG families. In particular, Epigenomics has markedly different error structure.

## Gate B: epsilon makespan-dominance uncertainty screening (old full oracle, K=16)

Selection on planned objectives ONLY: candidate A can exclude B under the epsilon rule if `A.planned_makespan*(1+epsilon) < B.planned_makespan` and `A.planned_cost <= B.planned_cost`. Epsilon=0 is the original Pareto-layer/max-min diversity selector. All candidates' simulator outcomes came from the historical complete visited-genotype oracle; the script selects K16 without using them, then measures K-selected simulated HV relative to the full history. The same frozen per-family reference points were inherited from earlier Actions 41572425682.

| Fixed makespan tolerance | Mean recovered oracle HV | Difference versus original, percentage points | Win/loss/tie versus original (24 arm-cases) |
|---|---:|---:|---:|
| 0% (original) | **98.6958%** | 0 | — |
| 0.5% | 98.6019% | **−0.0939** | 7/14/3 |
| 1% | 98.5848% | **−0.1110** | 6/16/2 |
| 2% | 98.3178% | **−0.3779** | 5/17/2 |
| 3% | 97.9124% | **−0.7834** | 4/19/1 |
| 5% | 98.4151% | **−0.2807** | 5/19/0 |

Some Sipht cases improve; Montage and Epigenomics often degrade. Do not optimize the epsilon on these same already-inspected cases and call the result held out.

## Decision / next research step

1. Keep original Pareto coverage as the default validated prospective K16 screening policy. Do not add a general residual correction or fixed epsilon band solely based on past simulator labels.
2. Rather than inventing another correction formula, measure the **marginal real simulator HV** from actual ordered K8, K16, K24 replay budgets with a prospectively fixed scoring reference and fresh DAG100 optimizer seeds 72/73. A nested K24 run simulates all 24 candidates once; its K8/K16 prefix scores may be calculated afterward without using future labels to choose earlier candidates. These nested curves are **not independently executed K8 or K16 runs**.
3. Explore mechanism-specific features or pretraining on truly disjoint DAG families/VM configurations only if larger simulator-labeled training data justify the added complexity. Pre-register the trained model and validate on new independent configurations.

**Scientific boundary:** all these results concern simulator replay selection, not the FLA search operator itself; they cannot substantiate FLA v12 superiority over NSGA-II.
