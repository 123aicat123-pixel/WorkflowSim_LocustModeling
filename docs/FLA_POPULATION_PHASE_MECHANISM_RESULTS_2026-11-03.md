# FLA selected breeding-population and DO/EO/SSO mechanism verification — 2026-11-03

**Status: PASS, passive instrumentation validated; major original hypothesis falsified on this cohort.** No search-operator variant was promoted. v12 stays the main experimental candidate; v14/v15 are opt-in only. `master` was not modified.

## Reproducibility evidence

1. Instrumentation source [9767a348](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/commit/9767a348a7cc1d5a92227f19bc301486f66e0e85), opt-in `-Ddagfla.populationDiagnostics=true`, direct counts from post-environment-selection FLA group1/group2, plus individual DO/EO/SSO bands. Unit regressions passed Java CI [41620937009](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41620937009).
2. [Strict ON/OFF identity test 41621195545](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41621195545) ran v12-hvbandit and v15-timelinegate with identical Montage_25 seed 171, 3030 counted objective calls per optimizer and K16 real WorkflowSim replays. **Full ordered visited-candidate SHA-256 equal**, all sixteen simulator replay CSV rows identical, planned/archive/actual summary equal, and 101 valid detached generation snapshots. v15 rejected 1267 dominated local trial slots during this identity test; v12 rejected zero. Instrumentation itself was observational, not a changed optimizer or extra oracle.
3. [Actual 8-block, 6-algorithm phase-population study 41621527587](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41621527587) **SUCCESS**: Montage_25/CyberShake_30 × default/staggered VM speeds × seeds 173/174. Each of five FLA variants provided 101 post-selected generation records, with 3030 target evaluations and K16 true WorkflowSim replays each for all six algorithms (including cost-seeded NSGA-II). Source SHA `339f078e88da09bfc5957540143fe56280512a3e`. Aggregated report artifact `fla-phase-pop-report-41621527587`, ID `13222718920`. Full `phase_population_cases.csv`, `phase_population_paired.csv`, and objective-side `phase_population_hv_cases.csv` retained.
4. [Read-only exact follow-up 41621825653](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41621825653) **SUCCESS** and checked all original 8 job artifacts had the SAME source SHA; original artifact `fla-phase-exact-report-41621825653`, ID `13224385401`. All analyses use the exact recorded genotype arrays, no added objective or simulator calls.

## Main falsification: no loss of selected-population genotype uniqueness

Across 8 scenario blocks × five FLA variants × 101 snapshots = **4,040 selected-population observations**, **0 had fewer than 30 unique genotypes**. Every observed *breeding population after survivor selection* had exactly 30 distinct genotypes, even though the v15 gate replaced many dominated local offspring in the candidate pool with a duplicate normal offspring.

Therefore the specific hypothesis “v15 fails because it increases duplicate genotypes **in the selected breeding population**” is NOT supported in these scenarios. This is distinct from the previous `distinct_observed` metric, which counted all evaluated proposals, even rejected ones. It aligns with the actual `selectGlobalCrowding` implementation: environmental selection first takes distinct genotypes by Pareto rank/crowding and only falls back to duplicates if too few distinct candidates exist. In this cohort, the fallback was unnecessary.

Different proposed mechanisms (loss of exploration breadth, eliminated candidates changing diversity in objective space, bandit feedback exposure, variation in true simulator vs planned objective fidelity) remain unverified.

## Per-stage metrics

Phases run for 74 DO, 14 EO and 12 SSO generations in this 100-generation setup, with 8 scenario blocks. (Observed stage-row counts: 592 DO, 112 EO, 96 SSO, per variant.)

| Phase | v15 timeline minus ungated v14 timeline unique selected slots | v15 random minus ungated v14 random unique selected slots | v15 timeline minus ungated timeline pairwise Hamming |
|---|---:|---:|---:|
| DO (diffusion) | 0.0000 | 0.0000 | +0.000986 |
| EO (equilibrium) | 0.0000 | 0.0000 | +0.041404 |
| SSO (steady state) | 0.0000 | 0.0000 | +0.048135 |

Gate rejection counts for v15 timeline: **4,637 DO**, **991 EO**, **856 SSO** across the eight blocks. These are counts across different numbers of generations; never interpret their absolute size as a direct relative per-stage propensity without normalizing by each stage's number of local trials.

Additional archive insertion events per generation (not total final archive-size growth, and not true-simulator HV change):

| Variant | DO | EO | SSO |
|---|---:|---:|---:|
| v12 baseline | 7.1098 | 6.3304 | 4.6562 |
| v14 timeline ungated | 5.7770 | 6.3036 | 4.8125 |
| v15 timeline gated | 5.8885 | 4.8750 | 5.0312 |
| v14 random ungated | 6.3632 | 6.0179 | 4.8229 |
| v15 random gated | 6.3345 | 4.7857 | 3.9688 |

A gate-associated change in archive admission does not establish cause for a final true-simulator HV change. The bandit reward and survivor-selection dynamics also evolve over time.

## Actual WorkflowSim outcomes for context

Common preplanned primary HV reference uses 1.5× max PLANNED selected K16 objective over six solvers and both seeds per workflow/VM regime +1, with all real simulated points inside this fixed reference. v15 timeline versus equally cost-seeded NSGA-II **lost in all eight scenario/seed cases**. Against v12, four specific cases were worse and four better; against ungated v14 timeline, results were mixed. In particular:

- Montage_25 default seeds 173/174: v15 timeline vs v12 **−3.8522%, −0.8434%**.
- Montage_25 staggered seeds 173/174: **+3.4375%, +3.7809%**.
- CyberShake_30 default seeds 173/174: **−1.2957%, −1.3873%**.
- CyberShake_30 staggered seeds 173/174: **−1.6503%, −0.4649%**.

These are newly executed development seeds but already-studied DAG families, not independent holdout evidence of broad superiority.

## Important future mechanism: bandit exposure

At population 30, v12 creates 30 normal FLA offspring per generation, whereas paired v14/v15 create 16 FLA-normal offspring +14 counted local neighbor evaluations per generation. Each regular FLA-normal offspring can activate a phase bandit arm, but paired local neighbor trials do not call the FLA bandit operator. Therefore the number of **eligible FLA bandit opportunities falls from 30 to 16 per generation** under pairing (a 46.67% reduction), even though both designs have exactly 30 charged evaluations/generation. This is a controlled reallocation of search effort, not extra fitness access; it is a plausible competing hypothesis for changed archive progress. The current study records per-generation normal bandit uses but does not causally separate lost exposure from local-trial quality.

## Limitations and decisions

- Continue to leave v12/v14/v15 original defaults unchanged; the measurement switch is OFF by default.
- Treat selected genotype uniqueness, pairwise Hamming distance, and archive insertion as different quantities; none alone establishes objective-space exploration quality or real-simulator superiority.
- DO/EO/SSO stage comparisons are observational and strongly confounded by iteration time. The phase association alone cannot prove why v15 is worse.
- The full experimental corpus has been inspected; it cannot be reused as an untouched publication holdout for a tuned v16.
- A subsequent test, if justified, should isolate **local trial evaluation allocation versus phase-bandit exposure**, without claiming that repeated algorithm tweaks on familiar DAGs establish a paper-level innovation.
