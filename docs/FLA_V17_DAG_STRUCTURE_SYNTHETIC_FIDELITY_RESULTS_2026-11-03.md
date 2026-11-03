# FLA v17 research evidence synthesis: DAG structure, synthetic holdout and model fidelity — 2026-11-03

**Engineering status: measured, reproducible, no demonstrated general algorithm superiority.** The original FLA v12 experimental baseline stays the primary reference. v17 DO-only random remains an opt-in candidate only. No default promotion; `master` unmodified.

## Immutable evidence and exact scope

1. [All-repository DAX structural audit 41630971648](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41630971648): **22 source DAX files**, **8 pure-Python unit tests passed**, exact graph parsing, longest path, topology metrics, file-size provenance and invalid metadata flags. Script `scripts/fla_dax_structure.py` and `scripts/test_fla_dax_structure.py`. Output file `dax_structure.csv` inside original archived Actions artifact.
2. [Frozen original v17 real-DAX confirmation 41626382711](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41626382711): 16 scenario-seed blocks, new DAX instance sizes of four existing families. Primary v17 DO-random vs matched late-74 local-search control +0.292937% K16 actual HV (8/16 wins), vs v12 +0.267539% (9/16 wins), vs seeded NSGA-II +1.604945% (8/16 wins). Four-family resampling intervals all crossed zero: [family uncertainty 41627443794](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41627443794). This is NOT a positive generality confirmation.
3. [Source-audited DAG feature/v17 outcome join 41631164374](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41631164374): first direct descriptive comparison of real parsed structural properties with real K16 simulated outcomes. Read-only; no newly fitted thresholds or unseen claims.
4. [Prospectively frozen NEW synthetic DAG generator preflight 41631520229](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41631520229): fixed generation seed 2026121501, two never previously optimized **synthetic** topology families with 60 tasks each. Wide: 146 dependency edges, six layers, ten root tasks, DAX SHA-256 `2e6eb90255ba3bf4147044fab96d837d74e5f0be6216a72eeef60271c62f7b24`. Deep: 82 edges, twelve layers, five roots, SHA-256 `709b55b67d7c34a9038c87c1ce1a98ef1f14f8efa3d64e3050e16d10f6b7d78c`. The generator, seeds, experiment arms and HV rule were documented BEFORE simulator outcomes in `docs/FLA_V17_NEW_SYNTHETIC_HOLDOUT_PROTOCOL_2026-11-03.md`. These are not new real scientific application families.
5. [All 12 new synthetic four-arm experiment jobs and final report SUCCESS, 41631739331](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41631739331). Every solver: 3030 counted stage-in-aware PLANNING target evaluations and K16 independently simulated WorkflowSim assignments, identical initial two cost seeds. v17 DO and late both exactly 1036 counted local probes, 1964 normal offspring. [Read-only corrected three-seed report 41632100333](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41632100333): original three random seeds were 301/302/303; previous header wrongly said two, but raw matrix and all figures were already based on three. The corrected report reused original artifacts, with zero new optimization/simulation calls.
6. [Read-only planning/real fidelity and search-time analysis 41632443623](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41632443623): original real-size and synthetic cohorts, 28 scenario-seed blocks × 4 algorithms × 16 replays = **1792 recorded candidate-level planning/real comparisons**, without new calls. Per-solver results can reflect different chosen candidate distributions, not a controlled identical-assignment intervention.

## Key data quality findings

- The DAX filename is NOT a reliable task count. Actual `Epigenomics_46` has 47 jobs; `Sipht_100` 97; `Sipht_1000` 968; `Sipht_60` 58; `Sipht_30` 29.
- `HEFT_paper` declares 25 jobs/20 child blocks but has 10 job elements and 9 child blocks. The header mismatch is logged, never repaired by inventing tasks.
- `Epigenomics_997` has 57 invalid negative runtime values and 209 invalid negative file-size references. Preserve its DAG topology (997 tasks, 1234 dependency edges), but suppress critical-runtime and runtime-derived indicators and exclude invalid file sizes from proxy transfer volumes. Do not take absolute values or replace with zero as though meaningful.

## Primary K16 simulated HV outcomes on new preregistered synthetic topology

| Synthetic DAG | VM regime | DO-random vs matched late-random | DO-random vs original v12 | DO-random vs seeded NSGA-II |
|---|---|---:|---:|---:|
| SynthNewWide_60 | default | +2.1065% | +1.3570% | +0.1177% |
| SynthNewWide_60 | staggered | −0.8172% | −0.7778% | −0.7097% |
| SynthNewDeep_60 | default | −0.9222% | −0.1293% | −1.1689% |
| SynthNewDeep_60 | staggered | +1.7537% | −0.5480% | +2.1225% |

Pooled 12 case-seeds under predeclared 1.5× planned-only shared HV reference:
- DO vs late **+0.530212%**, **6/12** wins.
- DO vs original v12 **−0.024543%**, **5/12** wins.
- DO vs NSGA-II **+0.090429%**, **7/12** wins.

Secondary 3× planned-only reference: vs late +0.218275% (5/12), vs v12 +0.009137% (5/12), vs NSGA-II **−0.117792%** (5/12). Reference sensitivity changes the sign of the comparison against NSGA-II. Thus these new synthetic stress tests do **not** support a stable v17 superiority claim.

## Planning-to-simulator fidelity: real source DAX size-confirmation cohort

On the same K16 selected assignments, makespan mean absolute percentage error (denominator actual) and planned-vs-actual comparable-pair rank inversion percentages:

| Algorithm | Mean Makespan MAPE | Mean Makespan rank inversion |
|---|---:|---:|
| v12-hvbandit | 2.779% | 4.844% |
| v17-do-random | **4.331%** | **7.292%** |
| v17-late-random | 2.823% | 4.428% |
| NSGA-II[costseed] | 1.809% | 1.510% |

In synthetic wide/deep cohort, corresponding v17 DO-only MAPE = **1.290%** and comparable pair inversion = **1.806%**. Cost MAPE rounded near zero in both cohorts. These per-algorithm groups do NOT evaluate identical assignments, and therefore do not establish that the planner works better for NSGA-II or worse intrinsically for v17. K16 Pareto-cover selection imposes selection bias; the measured error cannot be generalized to every candidate that was evaluated but never replayed.

Search wall time is logged, but GitHub Actions JVM warmup, serial arm evaluation order and shared hosted runners confound fair comparisons. A dedicated randomized-order, warmed-up benchmark is required to make timing superiority claims.

## Scientific decision and next validation stage

1. **Do not tune a v18 or a DAG-feature threshold from these exposed examples**, then call an evaluation on the same family/VM samples independent. Four real DAX families and two single generated synthetic graphs are nowhere near enough for a credible per-DAG meta-selector or a journal-level claim.
2. A more relevant next research bottleneck is **makespan rank fidelity**: a more accurate simulator-aligned evaluator or robust selection procedure may outperform additional metaheuristic moves. However, any new fidelity correction must be causal and tested on EXACTLY matched assignments with distinct held-out simulator labels, not on a favorable post-hoc filter.
3. Before submitting a high-ranked paper, use genuinely independent workflow instances/families (or several randomly generated topologies per family), multiple seeds and VM price/speed regimes, preregistered evaluation budgets, fixed reference points, and clustered uncertainty analysis. Report time, memory, actual makespan/cost and explicit simulator-vs-planner discrepancies in addition to HV.
4. Keep v12 research benchmark unchanged and v17 opt-in for continued investigations. These experiments **validate engineering and reveal generalization limitations**, not a novel FLA equation or a proven superior scheduling method.

## Explicit audit boundaries

The structural script computes DAX edge-file-volume and critical-runtime proxies, not actual consumed network traffic or VM-adjusted critical paths. Source FLA MATLAB equations remain incompletely verified at the original-equation level. The source DAX dataset contains malformed historical metadata; make cleaned exclusion policy explicit in any manuscript. This report is an engineering and research record, not a claim of scientific finality.
