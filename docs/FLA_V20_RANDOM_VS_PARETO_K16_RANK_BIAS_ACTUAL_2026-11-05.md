# V20 matched-search random-vs-planned Pareto K16 selection-bias audit — ACTUAL results (2026-11-05)

**VERIFIED scientific finding: planned Pareto-cover replay sampling suppressed ALL observable predicted-dominance comparisons; an independent precommitted RANDOM K16 control exposed actual false planned-dominance relationships. This is a measurement finding, not an improved scheduling algorithm or SCI-ready innovation.**

## Frozen source and strict evidence

1. Protocol frozen before new random simulator outputs in `docs/FLA_V20_K16_RANDOM_VS_PARETO_SELECTION_BIAS_FROZEN_2026-11-05.md`, commit `174edae`. No optimizer changes, no simulated truth in planned candidate selection.
2. Original four-arm Pareto-selected K16 run: [Actions 41969565802](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41969565802), **6/6 SUCCESS**, 384 actual WorkflowSim replays.
3. New prospective RANDOM-selected K16 run: [Actions 41972072193](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41972072193), **6/6 SUCCESS**, 384 more original WorkflowSim replays; fixed `dagfla.budgetReplayPolicy=random` and replicate 0 after unchanged FLA-v12/v20-random/v20-DAG/seeded-NSGA search. 3 familiar DAGs (`CyberShake_50`, `Sipht_60`, `Epigenomics_100`) × 2 seeds 951/952 × 4 optimizer arms.
4. Independent read-only rank-audit [Actions 41972209118, attempt 2 SUCCESS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41972209118). The initial attempt correctly failed because two random Sipht artifacts were not yet available. After 6/6 source jobs completed, the exact same analysis reran successfully.
5. **All 24 exact per-solver ordered distinct original candidate-history SHA-256 comparisons PASS** across the two replay policies. Each original solver has exactly 3030 source search evaluations and each policy replays K16 distinct TaskID→VMID mappings. Analysis uses the original true simulated makespan and cost, original planned objective scores and fixed relative objective-dominance definitions. Source artifact and script maintained; no new simulator calls during audit.
6. Each treatment supplies 24 solver histories ×16 original actual WorkflowSim K-selected assignments =384 replays per policy (768 replay records total). These may contain overlap within paired policies; 768 is **not** the number of independent physical assignments, and 120 pairs inside each arm are not independent observational units.

## The decisive bias control

| Matched replay selector | Planned objective strictly dominates in K16 pair | Predicted dominance FALSE in real simulator | Direct reversed dominance | False planned-dominance fraction among predicted-dominating pairs |
|---|---:|---:|---:|---:|
| Original planned Pareto-cover | **0** | **0** | **0** | **Undefined; no positive predicted pairs exist** |
| Objective-independent random K16 | **939** | **45** | **0** | **45/939 = 4.7923%** |

- Those **45 incorrect predictions** were **planned strict dominance that became true incomparability**, rather than actual reverse strict dominance. This distinction matters; there is **no observed direct reversal** in the random test, and the study cannot assert that reversed domination is impossible.
- It is invalid to use the original planner-selected K16's zero bad examples as empirical evidence of universal Pareto rank accuracy. The planned selector picked candidates so that not a single within-arm K16 pair was planned strict dominance; zero false planned dominance was therefore tautological for this finite chosen set.
- Random sampling exposes a **nonzero planning/simulator Pareto decision mismatch**, not necessarily a loss of the actual best K16 front: random-picked labels are not used to optimize search, and the candidate pool's full unobserved true Pareto front remains unknown.
- The 4.79% is a descriptive, conditional fraction **among the 939 comparable pairs in this selected cohort**, not a population misclassification rate, not 939 independent experiments, and not a proven confidence interval. Each set is within a known DAG/seed/solver and the workflows have been studied extensively.
- This result agrees qualitatively with the earlier 1,024 planned K-selected record audit's warned design bias, but is the first directly matched v20 same-exact-history random K16 control after predeclaring the policy. The earlier 1,859 full-visited study already measured rank distortion with different finite candidate distributions. Do NOT claim first-ever discovery of this issue.

## Per-block examples and selection performance
- RANDOM predicted-dominating pair counts vary considerably, for example `Epigenomics_100` seed951 FLA-v12 **33** predicted dominating with **9** false; `Sipht_60` seed951 v20 DAG **66** predicted dominating with **9** false. Other blocks have zero false in small samples.
- Random replay K16 true HV is **not** an improved optimizer claim. It is lower than planned K16 on most matched blocks, as expected when abandoning planned Pareto-focused selection. There are positive exceptions (e.g. Epigenomics seed952 NSGA-II), retained in the independent `all_24_random_vs_pareto_paired.csv` artifact.
- Comparisons use a common actual 1.5× max reference within (DAG, seed) across both replay selectors and all four algorithms, with 3× sensitivity. Do not compare the original standalone v20 report's per-block HV numerical values directly to this new joint-reference HV: the sets defining reference maxima differ.

## Next predeclared research gate, not yet a validated algorithm

The correct new *research hypothesis* is whether **risky planned dominated candidates near a predicted Pareto boundary can be identified without true simulator labels**, and whether reviewing them with limited READY/model evaluation improves actual K16 selection quality versus both objective-independent random and strong planned Pareto-cover controls. Existing static epsilon and median/Ridge/RF model correction have FAILED on other original datasets; simply retesting or renaming them as a new algorithm is not justified.

Before another optimizer change, collect a statistically meaningful fixed-VM-placement, candidate-selection-independent oracle with positive and negative planned dominance, and separate *rank misclassification detection* from actual HV selection gain. Preregister calibration families, candidate stratification and an untouched family. Under existing evidence, a focused reproducibility/evaluation-fidelity paper may be more defensible than the unsupported claim “improved FLA.”

All six source artifacts, 48 per-arm/policy fidelity rows, 24 paired summaries, exact protocol and negative cases remain available via GitHub Actions. **No modifications to `master`; all code and docs on `fla-baseline`.**

**Verdict: strict new ranking measurement SUCCESS; improved FLA optimizer NOT demonstrated.**
