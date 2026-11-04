# Pre-registered low-replay-budget same-genotype selection audit — 2026-11-04

**Frozen BEFORE any new selection outputs.** No new optimizer calls or WorkflowSim runs. Reuses exactly the 96 immutable actual WorkflowSim results from source Actions 41695356307. This is known-family retrospective evaluation of a prospective **planned-only** selection rule, not novel FLA and not unseen-family holdout.

## Motivation and source
The independent 96-mapping audit [41695748829](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41695748829) already established same-source old StageIn insertion mean Makespan MAPE 2.120330% vs READY TaskID 0.203173%, and 9 vs 0 materially wrong Makespan pair orderings across six DAX/profile blocks. Both models captured the REAL ND K16 HV at 100% on this coarse set. We must test if prediction fidelity changes which **limited subset of 1, 2, 4, or 8** mappings would be replayed and what true HV that subset captures. Do not claim these are unseen workflow families.

Input groups frozen: CyberShake_30, Epigenomics_46, Montage_50 × default/staggered, 16 algorithm-independent deterministic placement genotypes in exactly the order defined in `scripts/fla_algorithm_independent_same_mapping_rank_audit.py`. Real task-to-VM assignment, original source SHA, complete distinct mapping policies verified by its `load()`. No FLA/NSGA search, candidate-selection bias, adaptive replays or simulated-label feedback to the selectors.

## Predictive selection fixed, no peeking
For each DAX/profile group, compute one **shared, exclusively planned** 2D normalized HV reference with coordinates 1.5× the MAX Makespan and Cost over both predictor types' 16 PLANNED objective pairs (plus 1e-6). No real simulator values used in this reference. For each model OLD and READY and each K in {1,2,4,8}, enumerate ALL `C(16,K)` subsets and choose the subset with the HIGHEST **predicted** two-objective normalized HV; if scores tie within 1e-12 **absolute normalized HV**, choose the first lexicographic subset of frozen policy indices. Use the SAME exact method, candidate universe, planned reference, K and tie-breaking for BOTH models. This is a tiny exact screening selection audit, NOT an optimizer for all workflow tasks.

The **only** use of true WorkflowSim objectives is AFTER choices are frozen in code: compute one common actual normalized HV reference inside each DAG/profile block at 1.5× (and sensitivity 3.0×) the maximum actual Makespan and actual Cost among all16 candidates (plus 1e-6); evaluate the chosen model-selected K real points against the ACTUAL full-16-candidate HV. Compute an **ex-post truth-based K best attainable** actual HV by exhaustive K subsets FOR BENCHMARKING UPPER BOUND ONLY, never to select any model candidate. All actual HV and reference inputs identical between OLD and READY within blocks.

## Locked outputs / decisions
- Exactly six source blocks, 96 actual simulator points, 48 model × K selection outcomes and 24 old-vs-ready paired comparisons; four true-K ceilings per six blocks.
- For each group and K record old vs ready selected physical mapping indices/policies, intersection/Jaccard, true HV recovery of fixed 16 universe, score difference (READY − OLD), true oracle ceiling and regret-to-oracle, and 3× reference sensitivity.
- Stratify by DAG and K, report both positive and negative paired deltas, zero effects even when predictor MAPE differs sharply, and whether one model ever chooses a different subset.
- Report replay selection cost of exact enumeration separately: this is a small 16-case science calculation, NOT representative of large-population practical runtime complexity.
- If both select equal sets or real HV remains equal, record a negative conclusion: **better model MAPE does not improve this constrained K-budget selection**. Don't retune the K list or tie rules after seeing results.
- No bootstrap over correlated mapping pairs; only six DAG/profile blocks across three historically known families. No publication-quality generalization or significance claim.
- `master` remains untouched, and FLA, NSGA-II and the original FIFO runtime defaults stay intact.
