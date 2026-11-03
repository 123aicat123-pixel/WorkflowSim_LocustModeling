# Exploratory causal real-simulator feedback K16 pilot (2026-11-03)

**Status:** PROMISING but NOT validated final algorithm. Keep existing `pareto-cover` default; `online-nearest-hv` is explicit opt-in and only used when `-Ddagfla.budgetReplayPolicy=online-nearest-hv`. Only branch `fla-baseline` was changed; master not touched.

## Reproducible provenance

- New method Java `FLAResearchExperiment.chooseOnlineFeedback()`, commit `e722d506fbe0456c3f67268ecc8cb742f550ffba`, distinct from FLA optimizer search operators.
- [Original six real WorkflowSim paired jobs, Actions 41595213775](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41595213775), exact execution SHA `66f9c2b3d77e7b5528a4fd7fe7da430ceed88988`. Each of the **six actual simulation/causal audit jobs PASSED**. The final aggregation failed **only** from a report-script filename underscore-versus-hyphen mismatch, not a simulation failure.
- Fixed aggregate path and **recovered directly from the six unchanged saved original artifacts** in [Actions 41595350785](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41595350785), summary artifact `causal-k16-recovered-summary-41595350785`, artifact ID `13211947296`. Includes exact per-case `causal_online_paired.csv`, `causal_online_hv.csv` and Markdown summary.

## Protocol and causal isolation

- Three DAGs: CyberShake_30, Inspiral_50, Montage_25; fresh optimizer seeds 81 and 82; three solver arms: DAG-Pareto-FLA v7-costseed, DAG-Pareto-FLA v12-hvbandit, NSGA-II costseed.
- Each solver/policy case: **3030 optimizer planning evaluations** and **exactly 16 actual independent WorkflowSim replay calls**; Java CI checked raw replay counts, source evaluation counters and simulated objective finiteness. The full ordered distinct planned candidate history has identical SHA256 for online and Pareto-cover policies. First **four selected assignments identical**.
- Online arm: first 4 from planned Pareto coverage, then 12 sequential decisions. Each decision accesses only previous independently simulated assignments and planned objectives of unseen candidates. The 64 planned-coverage candidate shortlist, 0.5 residual shrink, nearest-neighbor rule and 10% correction cap were fixed before these seeds. The per-decision pre-replay trace contains observed count, selected mapping, nearest previously simulated mapping and pre-replay estimated objectives/HV gain. Audit verifies no lookahead and no repeat.
- The online method uses an internal planning-derived common HV reference for **selection** and the observed simulated front; the report uses a separate **post-hoc union reference**, common across policies/algorithms within a DAG/seed, solely for **evaluation**. **Not** a preregistered externally frozen performance reference.
- Equal K simulator calls does **not** imply equal wall-clock selection overhead, which remains to measure.

## Original WorkflowSim simulator HV changes: online feedback vs Pareto-cover

| Optimizer | Mean paired relative HV change | Online wins / six |
|---|---:|---:|
| FLA v7-costseed | **+0.2548%** | 6/6 |
| FLA v12-hvbandit | **+0.1277%** | 5/6 |
| Cost-seeded NSGA-II | **+0.2014%** | 4/6 |
| **All three arms** | — | **15/18** |

Negative cases retained:
- Montage_25 seed 81 NSGA-II: **−0.0945%**
- Montage_25 seed 82 FLA v12: **−0.3808%**
- Montage_25 seed 82 NSGA-II: **−0.1037%**

This is the first **prospective causal simulator-feedback selection** pilot in this branch. It is **not** a new search algorithm, because the 3030-planning-evaluation optimizer history does not incorporate the feedback; it is a sequential *post-search* assignment replay selection method. Its positive pilot merits testing on fresh five-family DAG100 seeds using earlier frozen references and independent audit, not acceptance as the default method or a proof of FLA v12 superiority.
