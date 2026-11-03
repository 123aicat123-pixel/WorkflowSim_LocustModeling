# FLA v12: 50-task cross-size comparison and 100-task screening sensitivity (2026-11-03)

**Repository:** `123aicat123-pixel/WorkflowSim_LocustModeling`  
**Branch:** `fla-baseline` only; **do not change master**.  
**Verification:** Real GitHub Actions artifacts downloaded and their CSV / report inspected on 2026-11-03. This is a bounded evidence update, **not** a claim that v12 is superior to NSGA-II.

## Immutable experiment references and scope

- [50-task cross-size paired test (run 41573256094)](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41573256094), source commit `3aa2650e16878b6a2fa990609098d72c88842579`; artifact `v12size50-report-41573256094` ID `13201833786`. Original CSV `v12_size50_hv.csv` and report `v12_size50_report.md`.
- [100-task planning-screen sensitivity (run 41573472744)](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41573472744), source commit `ffa03e1c2d018185752a19c2d80b2f694b83b41a`; artifact `v12screening100-pooled-41573472744` ID `13202263913`. Original CSV `v12screening100_sensitivity.csv` and report `v12screening100_sensitivity.md`.
- [Java regression CI (run 41573514859)](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41573514859), commit `78b1e37319cf0cba2a6f1b0fcfe005a7f9013a96`; artifact `fla-montage25-ci-41573514859` ID `13202078721`.

## 50-task: equal-search-budget simulator-HV comparison

All three solver arms started from the same two assignments and used **3030 genuine objective evaluations per solver**. Only planned-nondominated assignments were independently replayed in WorkflowSim. HV reference was shared among algorithms and seeds *within each DAG family*; different families' raw HV must not be averaged. Three families, five seeds per family. The datasets are not untouched held-out instances.

| DAG | v12 vs v7 mean paired simulator-HV change | v12 wins vs v7 | v12 vs costseed NSGA-II | v12 wins vs NSGA-II |
|---|---:|---:|---:|---:|
| CyberShake_50 | -0.069% | 2/5 | **-1.654%** | **0/5** |
| Inspiral_50 | +0.750% | 4/5 | +0.272% | 3/5 |
| Montage_50 | +0.560% | 3/5 | +2.598% | 3/5 |
| **All 15 paired cases** | **+0.414%** | **9/15** | **+0.405%** | **6/15** |

**Interpretation:** The small mean gain and fewer-than-half wins against NSGA-II do not establish v12 superiority. CyberShake_50 is a clear negative result. The pooled relative percent is a descriptive average across pairs, not a pooled raw HV or a confirmatory statistical estimate. Many variants have been tried, so these results are subject to selection effects.

## 100-task: quantified bias from planning-nondominated-only replay

Five DAG families × two seeds × three equal-seed algorithms; 30 paired algorithm-case records. Each algorithm received **24 extra unique, strictly planning-dominated assignments per case** (half near planned Pareto front, half deterministic sampling of the remainder). These assignments were **not** part of the 3030-evaluation search and were independently simulated *only as a sensitivity audit*. Each case kept its original shared frozen simulator reference. We do **not** add their HV to primary algorithm comparisons.

| Algorithm | Extra simulator replay count | Newly simulator-nondominated sampled assignments | Mean relative additional simulator HV |
|---|---:|---:|---:|
| DAG-Pareto-FLA[v12-hvbandit] | 240 | 22 | +0.000455% |
| DAG-Pareto-FLA[v7-costseed] | 240 | 23 | +0.001502% |
| NSGA-II[costseed] | 240 | 19 | +0.081102% |

The NSGA-II mean is dominated by `Sipht_100` seed 1 (extra HV +0.80952786%); it should not be read as a universal 0.081% disadvantage. Counterexamples show planning dominance is **not preserved** by the WorkflowSim simulator on all evaluated assignments. New non-dominated candidate counts are not equivalent to actual total Pareto cardinalities or independently validated performance improvements.

**Boundary:** This is targeted *sampling*, not full-simulator replay of all evaluated assignments. The screening policy favors near-front candidates; the reported deltas therefore neither bound exhaustive bias nor prove another selection policy is optimal. For meaningful primary algorithm superiority claims, compare algorithms under identical final simulation-screening rules and simulator evaluation budgets, or transparently report the current planned-front approximation as a threat to validity.

## Engineering regression remains a separate claim

The Java 17 CI artifact confirms all three 5-task/2-VM decoder regressions returned feasible **95.0 seconds**, rather than the previously invalid 65.0 seconds. Montage_25 summary lists LIWSA and NSGA-II selected plans with predicted makespan 35.276s and simulator makespan 35.686s, **1.163%** error by its reported convention. Four tested strategies are not a proof of universal model fidelity.

## Decision and next research gate

1. Retain v12 as a *candidate*, not a winning final algorithm. Keep negative CyberShake results in final reporting.
2. Prioritize reducing or eliminating **planning-front screening bias** in the evaluation protocol; validate any improved screening on paired cases and independent WorkflowSim replays, with equal search and replay budgets.
3. Run a locked 20–30+ independent seed experiment across task sizes, DAG families, pricing and heterogeneous VM settings; predefine reference points and statistics. Separate exploratory development from untouched final validation.
4. Preserve source SHA, logs, original per-seed CSVs and the fact that the MATLAB original FLA is discretely adapted; reconstructed MLEAO is not a source-faithful reference.

**No claim** is made that the GitHub branch byte-for-byte matches an inaccessible Windows local tree. GitHub Actions artifact retention may expire; source-run identifiers above are provided for retrieval while they remain available.
