# Frozen algorithm-independent K4 Pareto decision-consequence experiment — ACTUAL results (2026-11-05)

**Original true WorkflowSim source 8/8 SUCCESS; independent source-verified K4 exact-oracle audit PASS. Key negative result: READY avoids five OLD planned-dominance errors, but provides ZERO observed K4 selection-quality improvement over OLD in these eight blocks. This is a decision-fidelity measurement, not a successful new FLA optimizer.**

## Frozen sources and strict provenance

- Prospective protocol `docs/FLA_FIXED_UNIVERSE_K4_DECISION_CONSEQUENCE_FROZEN_2026-11-05.md`, committed at `d14bf82` before new original true simulator outcomes.
- [Source run 42002749849](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42002749849) **8/8 SUCCESS**, exact `FLAAlgorithmIndependentMappingUniverse.java` original 16 frozen physical placement policies. Four previously studied DAG **families** with new instance sizes: `Inspiral_100`, `Sipht_100`, `Epigenomics_24`, `CyberShake_100`; `default` and `staggered` VM regimes; simulator seed 1501, original WorkflowSim FIFO and fixed actual TaskID→VMID identity. **128 actual WorkflowSim genotype replays**, with OLD and READY predictions obtained on the SAME assignments before truth labels. No FLA/NSGA search picks the candidate universe.
- [Independent audit run 42003163567](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42003163567) **SUCCESS**, artifact `fla-independent-k4-true-regret-42003163567` (ID 13402794476). Source inputs require exactly eight original artifacts, a SINGLE original source SHA across all eight, all original 16 strategy names, 16 distinct TaskID→VMID maps with original Task IDs 1..N and VM IDs 0..15, positive finite planned and true objectives, frozen source identity and simulator regime.
- Decision policies PREDECLARED: for OLD and READY independently, greedily select 4 of 16 using predicted normalized HV (with predicted-only fixed 1.5x reference), tie break fixed normalized scalar sum then policy label; blind control chooses first four frozen policies without predicted scores. True-label **exhaustive C(16,4)=1820** K4 oracle is retrospective ceiling ONLY.
- True comparison uses one common actual objective 1.5x max reference **within each exact DAG/VM block** across OLD, READY, blind and oracle, with a 3x sensitivity column in the raw artifact. The 128 replay data points are NOT 128 statistically independent workflow scenarios; eight workflow/profile blocks are all known families.

## Full eight-block original physical K4 decision outcome

| DAG | VM profile | OLD real K4 HV | READY real K4 HV | blind fixed K4 HV | actual hindsight K4 oracle HV | OLD and READY regret |
|---|---|---:|---:|---:|---:|---:|
| Inspiral_100 | default | 0.47621254 | 0.47621254 | 0.47355378 | 0.47621254 | 0 |
| Inspiral_100 | staggered | 0.51815407 | 0.51815407 | 0.48609433 | 0.51815407 | 0 |
| Sipht_100 | default | 0.46413045 | 0.46413045 | 0.45823378 | 0.46413045 | 0 |
| Sipht_100 | staggered | 0.48890278 | 0.48890278 | 0.47036148 | 0.48890278 | 0 |
| Epigenomics_24 | default | 0.47312137 | 0.47312137 | 0.45795009 | 0.47312137 | 0 |
| Epigenomics_24 | staggered | 0.54694479 | 0.54694479 | 0.45906939 | 0.54694479 | 0 |
| CyberShake_100 | default | 0.47799610 | 0.47799610 | 0.44565840 | **0.47885960** | **0.00086350** |
| CyberShake_100 | staggered | 0.48418811 | 0.48418811 | 0.46156486 | 0.48418811 | 0 |

- **OLD**: 634 predicted strictly dominating within-block candidate pairs; **5 false** planned strict dominance relations; 0 direct orientation reversals, all 5 had >0.1% true objective separation under the preregistered materiality criterion. Mean true K4 HV regret **0.000107937**, restricted full-16 exact oracle achieved in 7/8 blocks.
- **READY**: 627 predicted strictly dominating pairs; **0 false** strict dominance relationships; 0 direct reversals. Mean true K4 HV regret **0.000107937**; actual restricted oracle also achieved in **7/8** blocks.
- The OLD and READY **realized K4 HV is exactly the same in 8/8**; no achieved decision-quality gain despite READY's more accurate pairwise strict dominance labels. The independent fixed-blind K4 control is worse than both models: mean realized true HV regret **0.027253450** and 0/8 restricted exact oracle matches. Both OLD and READY mean K4 true HV gain over blind = **+0.027145513**.
- CyberShake_100 default is a required negative exemplar: BOTH models miss the restricted hindsight oracle by ~0.00086350 true normalized HV. These source errors cannot be fixed or downweighted after outcomes and reused as a fresh prospective test.
- A K4 score being optimal among these **16 predefined genotypes** is NOT global workflow Pareto optimality. The fixed source pool deliberately contains extreme-all-VM and regular/hash strategies and does not represent the thousands of solutions FLA visited. READY being exact on all planned dominance signs does NOT ensure K4 greedy HV optimality.
- The 8 original DAG/profile blocks are not eight unseen families. They share four previously examined family mechanisms, and the one simulator seed is fixed. K4 decision outcomes are not a robust statistical proof; unrelated historical fairness and CPU/runtime parity remain open.

## Research/SCI consequence

This experiment identifies two DISTINCT measurable questions: (1) pairwise planning/simulator Pareto dominance **fidelity**, and (2) resulting **decision regret** when selecting constrained K4 subsets. Improving (1) does not automatically improve (2); model selection should be judged on (2) under the actual simulator and physical candidate universe. This is not an original new optimization operator and not yet a publishable paper on its own.

Potential methodological-paper structure: original WorkflowSim identity/execution semantics, frozen mapping universes, candidate selection bias, model pairwise ranking tests, realized Pareto decision regret, adverse counterexamples, costs and compute consequences. Crucially distinguish prospective original frozen source block tests from posthoc audits and avoid treating repeated candidate pairs as independent replicates.

Next research gate: robust instance/VM-family holdout and time-matched, true-simulator-labeled decision regret across diverse mapping universes with more nontrivial OLD/READY decision disagreements. If the two planners always choose the same plans, report null decision benefit even if individual forecasting metrics improve. Do not automatically create new FLA v22 optimizer or tune on this examined CyberShake case.

All code and docs remain on `fla-baseline`. `master` was not modified.

**Verdict: original 128-real-label experimental infrastructure and K4 decision-consequence methodology PASS; algorithm performance advantage NOT established.**
