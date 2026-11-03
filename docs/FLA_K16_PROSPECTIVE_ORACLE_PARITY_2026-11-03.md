# Prospective K=16 vs exhaustive visited-set WorkflowSim oracle: exact agreement (2026-11-03)

**Status:** independently verified engineering and retrospective-quality gate; NOT general multiobjective optimizer superiority. All changes are isolated to `fla-baseline` (master SHA checked as `c24d538300c6d3749f3149dd7495e7b3cdc3a4fa`).

## Provenance

- Cross-language precision mismatch discovery: [failure run 41583895407](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41583895407). Java and Python selector orders diverged in **8 of 16** synthetic case-budget tests. Ties used different serialized genotype keys, and Java previously treated tiny nonzero max-min spacing differences as ties with `1e-15` tolerance while Python used exact comparison.
- Java semantic correction: commit `e85935a9817bcfb8d75e321bebb4cb9033591766`. Java now uses the same task:vm genotype string tie-break and exact double spacing comparison as Python.
- [Cross-language parity CI success 41584019811](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41584019811): **16/16** exact selected-genotype order configurations agree across four stress distributions (including objective ties and near-double-precision ties), budgets K=8,16,24,32.
- [Actual prospective K16 regression success 41584082211](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41584082211): six workflow/seed cases, 3 arms each, **80 actual planned-objective fitness evaluations** and **exactly 16 independently executed WorkflowSim replays** per arm.
- **Decisive independent double-run evidence:** [Actions run 41584247162](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41584247162), source commit `dc942d67d8592082d2922f176dca51cf93ac046d`, 6 per-case original CSV and compiler/log artifacts. Each case runs two fresh experiments **from the same source SHA**: (a) *all unique visited assignments* independently replayed, (b) actual prospective K16 replay selected with planned objectives only. Script: `scripts/fla_prospective_oracle_parity.py`. All **18 algorithm-case assertions** checked exact selected genotype *and order* against the independent Python oracle, then verified each selected mapping's planned and independently simulated makespan/cost matched the complete oracle. All six cases passed.

## Experiment protocol

- Three independent DAG families, **CyberShake_30, Inspiral_50, Montage_25**, 2 paired seeds, three solvers per pair (`DAG-Pareto-FLA[v7-costseed]`, `DAG-Pareto-FLA[v12-hvbandit]`, `NSGA-II[costseed]`).
- Each arm: 8 population, 9 generations, **80 optimizer objective evaluations**. The same first two cost-seed schedules were asserted for all three algorithms.
- Prospective run: selection uses **planned objectives and genotype mappings only**, then incurs exactly **K=16 actual WorkflowSim replays per algorithm**. It does **not** obtain simulator labels from the full experiment while selecting.
- Full independent experiment: all unique visited genotypes independently replayed to construct the **post-hoc** reference oracle; this expensive diagnostic cost is not included in K16 runtime.
- The reporter freezes one reference per DAG family from **only the original planned-nondominated replay points** across both seeds and all three algorithms, `(max_m * 1.05+1, max_cost * 1.05+1)`; it never adjusts the reference after observing extra points. All HV recovery ratios are within matched algorithm, workflow and seed, avoiding pooled absolute HV across workflows.
- Equal replay-call budget applies to the **prospective K16 arms**; retrospective full-history replay is a validation oracle, not a deployable optimization budget.

## New actual prospective HV versus complete visited-history HV

| DAG family | Mean K16 / full-visited HV over its 6 arm-seed pairs | Lowest arm recovery |
|---|---:|---:|
| CyberShake_30 | **99.9967%** | 99.9895% |
| Inspiral_50 | **99.9828%** | 99.9056% |
| Montage_25 | **99.2425%** | 95.4651% |
| **18 total algorithm-case observations** | **99.7407%** | **95.4651%** |

- All six workflow/seed cases retained the **same best-HV solver** before and after prospective K16 screening, using the frozen same-family reference.
- The worst case is `DAG-Pareto-FLA[v12-hvbandit]` on `Montage_25` seed 2, 95.4651% HV recovery; this explicitly prevents any false claim of perfect recovery.
- The 18 algorithm-arm measurements are **not** 18 independent workflow replicates: 3 arms share each of six workflow-seed cases.

## Limits and next gate

This successfully bridges Python retrospective selector, Java real prospective selection and actual independent simulator results with exact mapping identity. Nevertheless, the result does not constitute 100-task prospective validation, nor does it imply 16 simulation calls are sufficient for arbitrary workflows. The observed 80 + K budgeting is **two distinct costs**, and a full runtime comparison should account for optimizer evaluation time, simulator time, and the heavy validation-oracle cost separately. Evaluated FLA variants underwent extensive exploratory development; these families cannot be called untouched confirmation data. Next preregister fresh seeds, scale K, task counts and VM heterogeneity, and report family-level uncertainty, wall-clock overhead, missed extremes and Pareto-regret in addition to HV recovery. Never present K16 screening fidelity as a claim that FLA v12 statistically beats NSGA-II.
