# Planned-dominated K16 + independent K12 actual WorkflowSim Pareto-sampling experiment — 2026-11-04

**Scientific verdict: a K-selected planned Pareto front can omit real nondominated assignments, but the measured HV impact in these two DAX development instances is almost zero. This is an evaluation-fidelity finding, NOT a validated superior scheduler.**

## Frozen source and transparent error recovery
- Preregistered original protocol: `docs/FLA_PROSPECTIVE_DOMINATED_K16_PLUS_12_FROZEN_PROTOCOL_2026-11-04.md`, written at `90b130af68b9581bba2d35f9d1f82bd33068d28f` before the original simulator run.
- [Original GitHub Actions 41693332570](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41693332570), original source SHA `f963e95c952a0d3dd67a26cdefa2b5eb221d8d61`: GitHub UI **FAILED** in a Python *post-Java validation script*, due to accidental stray apostrophe in `int(x['seed'])==951'`. Every original Java source experiment had already completed and saved all planned and actual results to `research_summary.csv`, `research_replays.csv`, `research_screening_summary.csv`, `research_screening_samples.csv`. GitHub Actions retained all 4 original artifacts. **Do not misstate this source run as green** and do not redo the simulations merely to cosmetically change an Actions status.
- [Independent recover-and-audit GitHub Actions 41693970902](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41693970902) **SUCCESS**, strict original-filename+CSV checks after downloading the four IMMUTABLE source artifacts. The original dataset was used directly without any extra solver or simulator calls. The audit validated 4 original DAG/seed blocks `Montage_100`, `CyberShake_50`, seeds 951/952, 2 algorithms each FLA-v12 and seeded NSGA-II, all 8 ×3030 counted target evaluations. For each algorithm: 16 unique originally selected planned Pareto-cover task→VM genotypes and **12 completely different additional strictly planned-dominated or tied genotypes**, 6 near planned front +6 uniformly sampled remainder. All 8 ×28 real Makespan/Cost labels positive finite and exact task/VM assignment IDs. **224 actual original WorkflowSim replays, of which 96 additional diagnostic**. No actual simulator outcome was used in extra-sample selection or optimization.
- The same shared 1.5× and 3.0× actual-Makespan/Cost reference was used for all 56 real points belonging to BOTH algorithms inside each (DAG,seed) block. Primary K16 and K28 HV were recomputed using the same within-block reference, NOT compared across incompatible per-run HV scales.
- Output archived: `all_224_true_replay_candidates.csv`, `all_8_solver_original_vs_extra_rank_and_hv.csv`, `all_pareto_misclassified_pair_details.csv`, `complete_k16_plus12_actual_rank_report.md`. Complete positive/negative assignments are included.

## Actual outcomes

| DAX | Seed | Solver | Additional K12 candidates nondominated against real primary K16 | Real K16 normalized HV | Real K28 normalized HV | Difference |
|---|---:|---|---:|---:|---:|---:|
| Montage_100 | 951 | FLA v12 | 1/12 | 0.31686832 | 0.31686832 | +0.00000000 |
| Montage_100 | 951 | NSGA-II | 2/12 | 0.33644433 | 0.33644438 | +0.00000005 |
| Montage_100 | 952 | FLA v12 | 1/12 | 0.30503672 | 0.30503711 | +0.00000039 |
| Montage_100 | 952 | NSGA-II | 0/12 | 0.33034286 | 0.33034286 | +0.00000000 |
| CyberShake_50 | 951 | FLA v12 | 3/12 | 0.52439372 | 0.52439456 | +0.00000084 |
| CyberShake_50 | 951 | NSGA-II | 2/12 | 0.52325972 | 0.52326039 | +0.00000067 |
| CyberShake_50 | 952 | FLA v12 | 2/12 | 0.51011404 | 0.51011517 | +0.00000113 |
| CyberShake_50 | 952 | NSGA-II | 2/12 | 0.53106735 | 0.53106805 | +0.00000070 |

- **13 of 96** originally planned-dominated or tied extra genotypes became nondominated when COMPARED WITH the 16 previously replayed source candidates. After adding all 12 extra candidates, one of the initially useful NSGA-II CyberShake_50 s952 candidates is in turn dominated by another extra candidate; per-arm final-K28 ND counts preserved in audit CSV.
- **16** original predicted Pareto domination labels were **lost** in actual WorkflowSim (from the 8 ×16×12 = **1536** primary-extra cross-stratum candidate pairs), direct dominance reversals **0**, new real dominations missing in planned labels **4**. This directly falsifies the earlier apparent 'no lost planned dominances' asymmetry from the K16-only retrospective: selection of a planned Pareto front suppressed the original observable planned-dominance sample.
- Mean real normalized HV improvement by revealing and adding the 12 extra plans per original algorithm = **+0.00000047** (0.00000047 absolute normalized 0–1 HV, not 0.47%). K28 improved in 6/8 cases under raw double precision, but gains were extremely small and are NOT a practical performance improvement.
- This does NOT establish that the optimizer can discover or select the hidden beneficial candidates without seeing real sim labels. It only shows the planned selection process sometimes omits them, with tiny observed retrospective HV gains in these blocks.

## Interpretation / next decision

1. The large difference between primary K-selected plan/rank mismatch measures and the new K16×K12 false-dominance count demonstrates **planning-selection bias**. K-selection deliberately favors planned nondominated points; one cannot infer generalized Pareto accuracy from those points alone.
2. Since the 13 'new real ND' candidates yield minuscule normalized HV gains, the next essential **read-only sensitivity test** is to assess epsilon-Pareto robustness at relative tolerances 0.01%, 0.1% and 1% using these SAME frozen real labels, explicitly separating numerical near-ties from economically meaningful improvement. NO new WorkflowSim calls needed.
3. A future new FLA method should not be based on this result alone. The prospect of a SCI paper still needs model-ranking results on *algorithm-independent candidate ensembles*, viable evaluation-time budgets, and properly independent workflow-family/seed testing.
4. Every mutation remains on `fla-baseline`; original FLA, baseline NSGA-II, runtime FIFO and `master` remain unchanged. Research flags OFF by default.

**Result: a useful negative-size effect and methodological reproducibility finding, not a publishable multiobjective algorithm improvement.**
