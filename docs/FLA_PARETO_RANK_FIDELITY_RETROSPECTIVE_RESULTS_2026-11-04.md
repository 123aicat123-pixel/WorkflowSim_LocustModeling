# Retrospective 1,024-actual-WorkflowSim K-selected candidate rank fidelity audit — 2026-11-04

**Status: independent scientific measurement audit complete; ranking differences exist, but the observed directional asymmetry is a K-selection design effect, not a validated general law of model error.** No changes to `master`, optimizer defaults or prior archived simulations.

## Sources and exact completeness
- Frozen read-only plan: `docs/FLA_PARETO_RANK_FIDELITY_RETROSPECTIVE_PROTOCOL_2026-11-04.md`.
- [Original full restart/single-policy run 41689142588](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41689142588): **40 original completed optimizer jobs, 768 actual simulator replays** across 80 solver arms; original source SHA `95ba7a4c49c0b20aefc0900143535875627b3b58`.
- [Original v19/v18/v12/seeded NSGA-II run 41690669415](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41690669415): **4 original completed optimizer jobs, 256 actual simulator replays** across 16 solver arms; original source SHA `0ec91dbf8d1be6f77881ecabb3a7d5a417252151`.
- [Read-only independent actual model rank analysis 41692592639](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41692592639): **PASS**. Exactly **44 original jobs, 96 optimizer arms, 1024 selected actual WorkflowSim replay rows, 6320 overlapping within-arm candidate pairs** validated. Distinct physical `(DAX, source-seed, runtime-priority, task→VM mapping)` configurations = **928**; deliberate repeated FIFO controls and other duplicate physical plans are not independent evidence.
- Outputs: `all_96_optimizer_arm_rank_fidelity.csv`, `all_pareto_misclassified_pairs.csv`, `pareto_rank_fidelity_retrospective_report.md` and audit provenance all stored as GitHub Actions artifacts. NO extra simulator calls or new optimizer calls.

## Source-planned versus real simulator decision consistency
All statistics below compare the **original objective values actually used by each optimizer** (`planned_makespan/cost`) to **the actual WorkflowSim outputs for its K preselected candidates** (`sim_makespan/cost`).

| Cohort and source policy | Original solver | Arms | Mean Makespan abs percentage error | Discordant Makespan order pairs / comparable | Planned-vs-real K-selected ND Jaccard |
|---|---|---:|---:|---:|---:|
| Full old insertion/FIFO | FLA | 4 | 4.16332% | 34/480 | 0.844 |
| Full old insertion/FIFO | NSGA-II | 4 | 3.09426% | 31/480 | 0.875 |
| Full ready/FIFO | FLA | 4 | 2.08450% | 19/480 | 0.906 |
| Full ready/FIFO | NSGA-II | 4 | 2.87074% | 23/480 | 0.891 |
| Full SJF-ready | FLA | 4 | 1.33036% | 10/479 | 0.938 |
| Full SJF-ready | NSGA-II | 4 | **0.29322%** | **3/480** | **0.984** |
| Full upward-ready | FLA | 4 | 0.76987% | 10/480 | 0.891 |
| Full upward-ready | NSGA-II | 4 | 0.53563% | 4/480 | 0.953 |
| V19 experimental cohort: FLA v12 | FLA | 4 | 1.55636% | 2/480 | **0.969** |
| V19 experimental cohort: FLA v18 | FLA | 4 | 1.81432% | 13/480 | 0.891 |
| V19 experimental cohort: FLA v19 | FLA | 4 | **3.20603%** | **18/480** | **0.828** |
| V19 experimental cohort: seeded NSGA-II | NSGA-II | 4 | 0.52671% | 4/480 | 0.953 |

The 48 restart-split arms have smaller K5/K6 samples and do not align directly with full K16 arm means; their detailed results remain in the source CSV, including cases of individual 20–26.7% within-arm pair disagreement.

**Overall selected-K Pareto class disagreement:** 205/6320 = **3.244%**. Planned-vs-actual selected-K nondominated-set mean Jaccard across all 96 arms = **0.912**.

### Critical interpretation of the observed directional asymmetry
- All 205 class disagreements were cases where a pair treated as **nondominated/incomparable by the planning model** became **dominance-comparable after real WorkflowSim execution**. The original audit observed **zero** direct reversal of a planned domination and **zero** loss of a planned dominance.
- **Do NOT interpret this as “the simulator never reverses predicted Pareto dominance.”** The K16/K6/K5 candidate samples were selected by *planned Pareto-cover*, intentionally favoring planned-nondominated candidates. This greatly suppresses or eliminates planned-dominance relationships **by construction**. Consequently the apparent asymmetry (new real dominances only) is heavily affected by prospective selection. This is a methodological warning: one cannot use these 6320 overlapping selected pairs to infer general candidate-pool Pareto classification asymmetry.
- The 6320 within-arm pairs are NOT 6320 independent workflows or RNG seeds. Many points overlap and duplicates reappear across treatments. Even arm-level averages across 4 known workflow instances cannot establish inferential significance.
- For example, FLA v19's mean selected-16 Makespan absolute percentage error 3.206% and ND-Jaccard 0.828 are worse than v12's 1.556% and 0.969 on separately selected candidate sets in these blocks. This **is consistent with** v19 exploring regions its shared StageInAware target model ranks less faithfully, but it is **NOT causal proof**: v19 and v12 did not evaluate identical K16 task mappings, so fitness-model fidelity cannot be isolated from selection/distribution differences.

## Main scientific decision

1. A better absolute objective forecast does not guarantee a better Pareto-front generator; some workflows/priority policies select points with worse model ranking consistency even if the event predictor previously matched fixed-genotype simulator data.
2. **Stop inventing new FLA mutation names from aggregate HV alone.** Before testing another scheduling algorithm, assess objective *ranking fidelity on fixed, algorithm-independent candidate sets* that include dominated as well as nondominated mappings; only then compare search operations using a common, validated evaluator and time-matched budgets.
3. A defensible next engineering study is a predeclared **unselected-genotype simulator replay control** or algorithm-independent stratified collection (uniform mapping, cost extreme, critical-path extreme, moderate diversity) across fresh task and VM speed profiles. Require both positive and negative source rank labels before replay; no prospective selection using real simulator labels.
4. The prior published coevolutionary task/VM priority rule literature limits novelty claims. Any eventual paper must separate improved simulator semantics / evaluation-fidelity contributions from true FLA-specific search-operator innovation and evaluate unseen workflow families.

**Verdict: rank-fidelity diagnostics identify a real measurement issue and a concrete bias control, but neither v19 success nor SCI readiness is demonstrated.**
