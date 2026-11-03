# Real sequential WorkflowSim feedback at K16: five DAG100 validation (2026-11-03)

**Research verdict:** prospective online replay feedback is promising as a general *post-search* simulator-feedback screening method, but gains are uneven and the evidence **does not** establish superior FLA v12 search. Keep `pareto-cover` default; `online-nearest-hv` is optional only. Do not change `master`.

## Immutable provenance and causal checks

- The actual Java/WorkflowSim search and simulation is [Actions run 41595600890](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41595600890), **10/10 case jobs passed**. Source commit `43ad3accbbf0fea8e36aabfadb70f0ae5c2e217e`.
- The original run aggregation step failed only because it still asserted 18 paired algorithm cases rather than the 30 expected for 5 families × 2 seeds × 3 algorithms. The 10 original case artifacts were unchanged and reprocessed in [successful recovery Actions run 41596536522](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41596536522). Aggregate artifact: `causal100-recovered-report-41596536522`, ID `13212038244`. CSVs: `causal_online_paired.csv`, `causal_online_hv.csv`.
- Independently checked the complete ordered unique planner-candidate/genotype/IEEE-double history SHA-256 equality for the two replay policies in each algorithm/case. Verified **3030 actual planner fitness calls** and **exactly K=16 actual independent WorkflowSim replay calls** per solver/policy. Starting first four replayed mappings are identical and chosen with planned Pareto coverage.
- Post-step-4 choices may read **only prior independently simulated observed outcomes** and the planned objectives of *unobserved* candidates. Every pre-replay decision records observed count, selected mapping, nearest previously observed mapping, predicted objectives and predicted HV increment. CI checks that the nearest mapping was previously observed and no selected genotype repeats.
- The separate [adversarial no-lookahead Java regression Actions 41595714450](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41595714450) passed: changing all unseen simulation labels to fabricated extreme values has **no effect on the next decision or predicted objectives**; removing a prior observed label fails closed.

## Fair real simulation and frozen HV evaluation

Five DAG families `CyberShake_100`, `Epigenomics_100`, `Inspiral_100`, `Montage_100`, `Sipht_100`; new optimizer seeds `91,92`; three equal-costseed solver arms `DAG-Pareto-FLA[v7-costseed]`, `DAG-Pareto-FLA[v12-hvbandit]`, `NSGA-II[costseed]`.

The shared per-family **evaluation** HV reference was established in an earlier independent five-seed DAG100 experiment, Actions `41572425682`, **not** fit after this new run:
- CyberShake_100 `(6806.24215,3280.0303)`
- Epigenomics_100 `(211858.3560250001,217310.76064)`
- Inspiral_100 `(11044.129825,11209.86290125)`
- Montage_100 `(568.6573,570.969505)`
- Sipht_100 `(9127.960675000002,8822.13817375)`

Note: the online selector uses a distinct internal **planned-objective-derived** reference to choose its next candidate. This frozen external-in-study evaluation reference is not passed to selection.

| Optimizer | Mean paired relative simulator-HV change, online versus Pareto-cover | Online wins / ten DAG-seed cases |
|---|---:|---:|
| FLA v7-costseed | **−0.0262%** | 8/10 |
| FLA v12-hvbandit | **+0.1994%** | 8/10 |
| Costseed NSGA-II | **+0.6222%** | 10/10 |
| **All 30 algorithm-case contrasts** | — | **26/30** |

Negative observations:
- CyberShake_100 seed 92, FLA v7: **−0.0058%**.
- Epigenomics_100 seed 91, FLA v7: **−0.7078%**.
- Inspiral_100 seed 92, FLA v12: **−0.0924%**.
- Sipht_100 seed 92, FLA v12: **−0.0002%**.

Largest single observed positive result: Sipht_100 seed 91 costseed NSGA-II **+3.5053%** real simulator HV.

## Interpretation, hypotheses and research boundaries

1. The online feedback selector is algorithm-independent and can improve NSGA-II as much as or more than FLA. Therefore **do not** claim these gains are from modifying the FLA exploration/search operator.
2. It changes the **post-optimization K-limited real simulation replay selection**, not the optimizer's original 3030-evaluation planned search. It is a genuine sequential simulator-informed replay selector, but not full simulator-feedback optimization inside FLA generations.
3. Positive cases dominate but FLA v7's average is negative, and FLA v12 has two losses. Hence **no stable broad FLA-specific performance gain** is established.
4. Only 10 DAG/seed observations across five DAG families, three solver arms correlated per observation; no statistically powered novelty or general superiority claim. Workflow families have been used for algorithm development; avoid calling them completely untouched.
5. Equal planning fitness and simulator calls do **not** imply equal elapsed time; measure policy selection, planner search and real simulation times separately.
6. Next planned mechanism ablation: compare (a) original Pareto coverage, (b) sequential selection with **planned-only** objective predictions, (c) sequential selection with the *observed simulator front but uncorrected candidate estimates*, and (d) current nearest-neighbor residual correction. Hold candidate pool, warm start, search budget, simulator calls and source SHA fixed. This separates benefits from greedy selection, already observed real front, and local residual prediction. No conclusion should be drawn until that ablation is executed.
