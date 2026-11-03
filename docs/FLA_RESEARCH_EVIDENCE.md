# DAG-Pareto-FLA research evidence (GitHub branch `fla-baseline`)

**Status:** reproducible simulator-backed **research candidate**, NOT yet a verified publication claim. This file records successes, negative results, and scope limits.

## Scope and non-negotiable isolation

- Repository: `123aicat123-pixel/WorkflowSim_LocustModeling`.
- Experiment branch: `fla-baseline`. The `master` branch remains unchanged.
- The developer's local Windows directory is not byte-wise compared to this branch. **Do not claim local/GitHub SHA identity.**
- Algorithms: FLA-3W (discrete adaptation of continuous MATLAB-v1.0 scalar FLA, three objectives weights), DAG-Pareto-FLA (proposed discrete multiobjective adaptation), NSGA-II, reconstructed MLEAO.
- All four are evaluated using the same **stage-in-aware** planning objective in `-Dworkflowsim.planningStageInAware=true` mode, and candidate objective values are independently replayed in WorkflowSim.
- Histories are captured passively using `UnifiedCandidateRecorder`; the final *simulated* Pareto front is computed from assignments that were **planned-nondominated** in the recorded search. Planning-dominated candidates are NOT simulated, so this is not an exhaustive simulator front.
- Hypervolume (HV) uses one reference point per DAG family, shared by solvers/seeds within each experiment. Raw HV magnitudes across different workflows or independent experiment batches **must not be compared**.

## Why evaluation-model fidelity was repaired

An important mismatch on CyberShake arose because WorkflowSim charges VM-occupied stage-in file-loading duration but the old surrogate omitted most of this overhead.

The read-only stage-in-aware audit, 7 workflow instances x 5 seeds (35 paired schedules) showed:

| Workflow | Old median absolute makespan error (simulator denominator) | Stage-in-aware median error |
|---|---:|---:|
| CyberShake_30 | 66.144% | 0.108% |
| CyberShake_50 | 61.641% | 0.132% |
| CyberShake_100 | 51.414% | 0.093% |
| Epigenomics_24 | 0.581% | 0.017% |
| Montage_25 | 1.150% | 1.511% |

Overall, 30/35 makespan predictions and 35/35 cost predictions improved. Montage is a known counterexample for makespan, not hidden.

Evidence: [Stage-in fidelity audit](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41501564409).

## Algorithm evolution — failed ablations are retained

- `v2-global`: non-dominated global elite selection over two FLA groups. Compared with v2 no-cross, +2.671% mean paired simulator HV over 10 held-out Epigenomics/Inspiral pairs, 6/10 wins. This is only a within-family operator result, not a NSGA-II comparison. [Holdout](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41504496093).
- `v3-archive`: random archived non-dominated candidate contributes a short VM-gene block. +2.522% mean paired HV over 10 held-out pairs against v2-global, 6/10 wins. [Holdout](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41507118883).
- `v4-crowding`: replacing rank-plus-preference selection with NSGA-II-style rank/crowding **reduced** HV by 3.803% in nine development comparisons to v3-archive. [Negative ablation](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41508089777).
- `v5-dagblock`: dependency-connected archived-gene transfer **reduced** HV by 2.677% on nine development comparisons; preference-based archived donors also failed to help. [Negative ablation](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41509862381).
- `v6-pop`: **pre-evaluation novelty repair** resamples one feasible VM gene if a proposed FLA child duplicates a genotype within its generation's parent/child pool. The operator never adds an extra objective evaluation. `v6-global` protects the whole evaluated assignment history, but did not achieve higher development HV than `v6-pop`. Development results: v6-pop +2.258% mean paired HV vs v3-archive, 7/9 wins. The unique schedule/evaluation ratio increased from roughly 47.7% to roughly 98.4% on three development families. [V6 development](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41510519977).

**V6 held-out verification**: after selecting v6-pop on CyberShake_30/Montage_25/Sipht_30, we tested Epigenomics_24 and Inspiral_30: +11.283% / +15.787% respective mean paired HV vs v3-archive; pooled +13.535%, 10/10 held-out wins. [Held-out evaluation](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41510995900).

## Four-algorithm v6 confirmation (simulator HV)

Population=30, nominal generations=100, ~3000 fitness evaluations per solver, 5 DAG families, 5 paired seeds. Evaluation-count invariants and exact-assignment replays are asserted.

| V6 compared with | Mean of 25 within-workflow paired relative simulator HV changes | V6 wins |
|---|---:|---:|
| NSGA-II | **−0.221%** | 12/25 |
| FLA-3W | **+3.239%** | 20/25 |
| MLEAO | **+5.921%** | 23/25 |

Source: [Full 25-run matrix and frozen HV aggregate](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41511138304).

A workflow-resampled exploratory bootstrap yields these 95% intervals:

- Compared with NSGA-II: **[−1.159%, +0.657%]** — difference not established.
- Compared with FLA-3W: **[+1.129%, +5.372%]**.
- Compared with MLEAO: **[+1.533%, +11.383%]**.

**Caveat:** there are only five workflow families; resampled uncertainty intervals are exploratory. Seed comparisons within one DAG are correlated as workflow-family evidence, and multiple iterations of variant selection were tried. These are NOT definitive manuscript p-values. [Statistical analysis](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41511827222).

## Larger unseen DAG instances (50–60 tasks)

A dedicated out-of-sample scalability run used five larger workflow instances, three paired seeds, 30x100 evaluations per solver, and one frozen HV reference per family.

| V6 compared with | Mean paired simulator-HV change across 15 cases | V6 wins |
|---|---:|---:|
| NSGA-II | +0.033% | 7/15 |
| FLA-3W | +4.094% | 12/15 |
| reconstructed MLEAO | +15.558% | 14/15 |

These data corroborate FLA/ML-based baseline improvements at larger task counts but still show **no overall superiority to NSGA-II**. Inspiral_50 favored NSGA-II by ~2.54%; Montage_50 favored v6 by ~3.09% in paired relative HV. [Larger-DAG replay and frozen HV](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41511726130).

## Additional 100-task scaling probe

We also evaluated **five 100-task DAG instances** (CyberShake_100, Epigenomics_100, Inspiral_100, Montage_100, Sipht_100), with two paired seeds per instance. This is deliberately described as a scalability **probe** because two seeds are insufficient for meaningful statistical confidence.

| V6 compared with | Mean within-DAG paired simulated-HV change across 10 cases | V6 wins |
|---|---:|---:|
| NSGA-II | **+0.186%** | 5/10 |
| FLA-3W | **−1.500%** | 6/10 |
| reconstructed MLEAO | **+35.491%** | 9/10 |

- CyberShake_100 favored v6 over NSGA-II (+2.228% mean paired HV).
- Sipht_100 favored NSGA-II (v6 −5.857%).
- Montage_100 favored FLA-3W over v6 (v6 −21.167%), an explicit counterexample to any across-all-sizes FLA superiority claim.
- Workload structure has a pronounced effect; larger-instance results must not be pooled carelessly with 25/50-task benchmarks without matched family-level stratification.

[100-task simulator replay and frozen HV evidence](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41512322414).

## Completed 100-task evaluation (all five seeds — authoritative aggregate)

The two preliminary runs (seeds 1–2 and seeds 3–5) were combined after checking that the four core algorithm and evaluator source blobs had identical SHA values between commits. A single reference point per 100-task DAG was recomputed across all 5 seeds and all four algorithms. **This table supersedes the preliminary two-seed 100-task percentages above.**

| v6-pop compared with | Mean within-workflow paired simulator-HV change across 25 runs | v6 wins | Exploratory workflow-and-seed bootstrap 95% interval |
|---|---:|---:|---:|
| NSGA-II | **−0.433%** | **12/25** | **[−3.729%, +2.583%]** |
| FLA-3W | **−2.877%** | **12/25** | **[−12.874%, +6.159%]** |
| reconstructed MLEAO | **+34.120%** | **23/25** | **[+13.291%, +55.334%]** |

Representative family effects versus NSGA-II: CyberShake_100 +0.423%; Epigenomics_100 +1.275%; Inspiral_100 +3.144%; Montage_100 −3.022%; Sipht_100 −3.987%.

Counterexamples versus FLA-3W are stronger at 100 tasks: Montage_100 **−21.237%** mean paired HV (0/5 wins), Inspiral_100 −4.670%, Sipht_100 −1.586%. CyberShake_100 favors v6 by +11.668%.

All 25 original five-seed cases had their solver objective counts checked, candidate assignments replayed through the actual WorkflowSim simulator, and the final HV recalculated from those observed objectives.

- [Final five-seed 100-task results and reproducible frozen-HV CSV](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41514085317)
- [First 100-task cohort (seeds 1–2)](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41512322414)
- [Additional 100-task cohort (seeds 3–5)](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41513299770)

**Interpretation:** v6 has credible search-efficiency improvements and often improves upon FLA-3W at small/medium DAG sizes, but the 100-task evidence does not support stable superiority over FLA-3W or NSGA-II. These family effects, including negative ones, must be reported explicitly.

## Search efficiency and end-to-end deliverable

From the same 25 matched 30x100 runs:

- V6-pop: **98.269%** distinct visited assignments, mean 23.44 planned-ND replay candidates, median recorded optimizer search time **445 ms**.
- NSGA-II: **88.283%** distinct, mean 26.92 planned-ND candidates, median optimizer search time **420 ms**.
- FLA-3W: **60.225%** distinct, mean 30.56 planned-ND candidates, median optimizer search time **450 ms**.

The v6 novelty repair is not evaluation-free in CPU time; it only adds **zero additional objective evaluations**. Measurements are indicative across shared GitHub runners, not controlled CPU microbenchmarking. [Runtime and uniqueness audit](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41512670998).

The selected variant has a dedicated explicit entry point, `DAGParetoFLAV6Example.java`, which sets all research options and runs an actual WorkflowSim simulation. The legacy `DAG_PARETO_FLA` behavior is NOT silently reconfigured; using the standalone v6 entry point is necessary for an unmistakable version selection. [Executable end-to-end smoke test](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41512522545).

```bash
java -cp 'build/classes:lib/*' \
  org.workflowsim.examples.planning.DAGParetoFLAV6Example Montage_25 1 30 100
```

## Exact commands for independent reproduction (Linux GitHub checkout)

Compile all Java files fresh, not from stale `bin`:

```bash
mkdir -p build/classes Output\&Results
find sources examples tests -type f -name '*.java' | sort > sources.txt
javac -nowarn -encoding UTF-8 -cp 'lib/*' -d build/classes @sources.txt
java -Dworkflowsim.planningStageInAware=true \
     -Ddagfla.comparisonVariant=v6-pop \
     -cp 'build/classes:lib/*' \
     org.workflowsim.examples.planning.FLAResearchExperiment \
     Montage_25 1 30 100 'Output&Results/v6_montage25_s1'
```

The output contains a summary CSV, a full set of simulator-replayed candidate assignments, and an explicit limitations text file. Other workflow family files reside under `config/dax`. Baseline and audit workflows in `.github/workflows` reproduce the remaining comparisons.

## Barriers before claiming journal-quality superiority

1. NSGA-II is currently **statistically unresolved** relative to v6; do not describe v6 as consistently superior.
2. The original continuous FLA source/parameter fidelity still requires independently verifiable equation-to-code documentation. It is not scientifically sound to call the discrete FLA implementation a faithful original baseline.
3. The MLEAO baseline is a reconstruction, not a source-faithful implementation. Do not advertise it otherwise.
4. We have tested 25–30, 46–60, and 100 task scales, including **five paired seeds** per 100-task DAG. Still expand independent seeds, pricing regimes, VM heterogeneity, and workload families. Preserve development/held-out distinction after tuning.
5. Add a pre-registered reference point, IGD+ or epsilon indicator when justified, cost/makespan front visualization, runtime overhead, and stronger statistical power (more independent seeds/workloads).
6. Candidate screening by planned nondominance may lose assignments that become non-dominated **after** simulation; quantify this approximation or replay every distinct candidate on selected small tests.
7. This repository branch is not verified byte-for-byte identical to the user's local Windows source tree.

**Conservative current claim:** V6 novelty repair improves FLA search efficiency and is broadly competitive with NSGA-II at 25–100 tasks, without establishing superiority. It improves simulated HV against FLA-3W on 25–60 task workloads, but this advantage does not generalize to all five 100-task workflows; reconstructed MLEAO is an imperfect baseline. No journal acceptance/publishability is guaranteed.


## Planning-front screening sensitivity: newly validated methodological caveat (2026-11-03)

The previous research protocol passively recorded every evaluated assignment but only **replayed the assignments not dominated in the planning surrogate objective**. We tested whether this changes the simulator Pareto front; code and archive experiments are on `fla-baseline` only.

**Moderate-budget sensitivity, population 30 × 100 generations**: three workflows (Montage_25, CyberShake_30, Sipht_30), seeds 1 and 2. For each of four algorithms, 12 additional UNIQUE, strictly planning-dominated assignments were selected: half nearest the planned front, half deterministic random from the remainder. These are **post-search diagnostic replays**, not extra objective-search evaluations. Under the *original frozen simulator HV reference*, average HV changes across six paired runs were:

| Solver | Extra simulator replays | Newly nondominated against the original simulated front | Mean extra HV |
|---|---:|---:|---:|
| DAG-Pareto-FLA v6-pop | 72 | 18 | +0.104672% |
| NSGA-II | 72 | 16 | +0.101342% |
| FLA-3W | 72 | 11 | +0.030915% |
| reconstructed MLEAO | 72 | 12 | +0.017558% |

Sipht_30 showed larger effects: mean extra HV **+0.310912%** (v6-pop) and **+0.298352%** (NSGA-II). A sampled extra candidate might be nondominated relative to the original front but subsequently be dominated by a different extra candidate, so these counts should not be mistaken for net archive-cardinality increases.

[Moderate-budget screening-bias data and artifacts](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41517581864).

**Exhaustive observed-genotype pilot, population 8 × 9 generations:** all unique evaluated task-to-VM genotypes (including equal planned-objective ties) were replayed for three families, two paired seeds, and all four optimizers. The observed simulator Pareto front over the VISITED candidate set is now exact for that deliberately small search budget; it is not the globally optimal schedule set.

- FLA v6-pop: **+0.793632%** mean extra simulated HV over six runs; 20 previously filtered candidates were nondominated versus the original simulated front.
- NSGA-II: **+0.713691%** mean extra HV; two newly nondominated-versus-original candidates.
- The largest per-run changes included **+4.699853%** for FLA v6 (Montage_25 seed 1) and **+4.282149%** for NSGA-II (Montage_25 seed 2).
- The overall top-HV algorithm **did not change in any of the six small-budget cases (0/6)**. This does NOT establish ranking stability for the 30 × 100 or 100-task runs.

[Full replay coverage assertions, CSVs, and winner-change report](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41518305713).

**Statistical conclusion:** filtering by planned Pareto dominance can systematically understate the HV achievable among evaluated schedules under actual simulator objectives. Our larger-budget simulator HV results are therefore **screening-dependent lower bounds**, not exhaustive observed-search simulator HV. This caveat applies to every solver, not just FLA. A two-seed 100-task sensitivity audit is also available as `fla-screening-100task.yml`; its outcomes must be checked separately rather than guessed.

**Recorder correction:** `UnifiedCandidateRecorder.Capture.uniqueEvents()` now exposes each independent solver run's unique evaluated assignments for read-only audits. The FLA-3W summary's distinct-assignment count is deduplicated **across all three scalar weight runs**; earlier historical reports calculated the sum of per-weight distinct counts, which can overstate global distinctness if the same task assignment occurs under different weights. The previous reported 60.225% figure should therefore be labeled a historical, non-union count pending rerun, not a rigorously measured across-weight novelty rate.

All screening-audit switches are disabled by default, so they do not silently alter the original experiment results.

## Frozen simulated-HV reference sensitivity (100-task, all five seeds)

The 100-task solver comparison was independently recomputed using **the same immutable WorkflowSim replay candidates** from the two five-seed source-consistent cohorts, but five distinct **common** reference multipliers. Every alternative remains shared across all four algorithms and all five seeds within the same workflow.

| Multiplier of each workflow's worst observed makespan and cost (+1) | v6 relative to NSGA-II (25-case mean) | v6 relative to FLA-3W (25-case mean) | Winner changes vs multiplier 1.05 |
|---|---:|---:|---:|
| 1.02 | −0.205% | −4.085% | 1/25 |
| 1.05 (original report) | −0.433% | −2.877% | 0/25 |
| 1.10 | −0.617% | −1.730% | 1/25 |
| 1.20 | −0.727% | −0.694% | 3/25 |
| 1.50 | −0.672% | +0.082% | 4/25 |

**Interpretation:** v6 has no demonstrated overall advantage over NSGA-II across these tested references. The *sign* of the small v6–FLA-3W difference changes under the loosest reference, so an isolated percentage with an undisclosed reference point would be misleading. Across the candidate-based benchmark, four per-seed top-algorithm winners also change at the 1.50 reference. These alternatives are an explicitly **post hoc sensitivity check**, not evidence that the reference point was preregistered.

[Five-reference-point robustness check and full per-seed CSV](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41519102169).

Both filtering bias and reference-point sensitivity should be addressed before claiming statistically robust algorithm superiority.

## V7 cost-seeding: measured gains and fair-NSGA counterfactual (2026-11-03)

**Motivation from independent 100-task front geometry**: On Montage_100 (five paired seeds), v6-pop's simulated Pareto front from planned-nondominated replay had **9.2** nondominated points on average, versus **38.2** for FLA-3W. V6 found better minimum makespan (**126.008** versus **133.270**), but much worse minimum cost (**514.026** versus **486.077**). Therefore increasing genotype novelty alone did not ensure coverage of the low-cost extreme. [Actual 100-task front-geometry report and raw CSV](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41560133441).

V7 introduces two *optional* changes, both off by default and limited to the DAG-FLA experimental driver:

- `v7-costseed`: replace **two** random initial population members (not additional evaluations) with task-wise low estimated computation-plus-real-input-stage-in cost assignments and lowest-VM-price assignments. The low-cost proxy is used only for proposals; all objectives are evaluated by the existing stage-in-aware shared objective.
- `v7-extreme`: a stochastic minimum-cost archive member becomes the group-2 reference during certain iterations. `v7-both` combines both operators.

**V7 development ablation**: Montage_100, CyberShake_100, Sipht_100, three seeds each, population 30, generations 100, **3030 actual objective evaluations per variant**; all HV values are simulator-replayed with a single per-family frozen reference point across variants and seeds.

| V7 compared with v6-pop | Mean paired simulator-HV change over 9 development cases | Positive cases |
|---|---:|---:|
| v7-costseed | **+14.105%** | **9/9** |
| v7-extreme | +2.618% | 7/9 |
| v7-both | +10.910% | 8/9 |

For v7-costseed, family-level mean paired changes versus v6 were CyberShake_100 **+4.722%**, Montage_100 **+33.554%**, Sipht_100 **+4.040%**. All observations use the same planned-front screening limitation as the original protocol. **This is a tuned development comparison, not evidence of generalization or NSGA-II superiority.**

[Full v7 control-variant simulation replay data, unique-genotype metrics, and fixed-reference report](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41560504749).

**Fair initialization counterfactual**: We also added a default-OFF `NSGAIIPlanningAlgorithm.CONFIG_COST_SEEDING` that constructs the **same two deterministic proposals** in NSGA-II's own task order before its random initial population. Standard unseeded NSGA-II is unchanged, and both v7 and seeded NSGA-II retain their original 3030 objective evaluations and otherwise unchanged optimizer search. We used a five-way direct comparison (v7, canonical unseeded NSGA-II, NSGA-II[costseed], FLA-3W, MLEAO) on CyberShake_100 and Montage_100 with three paired seeds and a common simulator HV reference within each family.

| V7 compared with | Mean relative HV difference over six pairs | V7 positive cases |
|---|---:|---:|
| Unseeded NSGA-II | **+7.366%** | **6/6** |
| Matched `NSGA-II[costseed]` | **+0.019%** | **2/6** |

CyberShake_100: the same-initialization NSGA-II defeated v7 on all 3/3 paired seeds, with v7 averaging **−1.566%** relative HV. Montage_100: v7 averaged **+1.605%** versus same-initialization NSGA-II (2/3 wins), but FLA-3W was the highest-HV solver in all three seeds.

[Matched-cost-initialization counterfactual and 30 actual simulator run records](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41561522053).

**Scientific implication:** v7's gain versus unseeded NSGA-II should NOT be described as FLA-specific optimizer superiority. Giving the same low-cost seeds to NSGA-II largely eliminates that gain in this limited six-pair probe. The initialization should be treated as a **shared heuristic baseline** in further scientific comparisons, and a stronger FLA-specific operator is still unproven. The current five-workflow, five-seed direct confirmation workflow `fla-v7-costseed-confirm.yml` must also be evaluated before any manuscript claim.

V7 output and the counterfactual are purely experimental; the default `DAG_PARETO_FLA` and default NSGA-II planners have not been silently reconfigured.

## V7 complete five-family confirmation and uncertainty (2026-11-03)

The selected `v7-costseed` was compared directly to standard NSGA-II, discrete-adapted `FLA-3W`, and reconstructed `MLEAO` on **five 100-task DAX workflow instances × five seeds**. Search used population 30 and nominal 100 generations, with actual objective evaluations asserted between 2980 and 3060 (3030 for DAG-FLA and NSGA-II). All replayed scheduling assignments were independently run through WorkflowSim and checked for decoder consistency. One **common frozen simulator-HV reference per workflow** was used across all four algorithms and all five seeds; raw cases and reference coordinates are archived.

| V7 costseed versus | Mean paired simulator-HV % across 25 cases | V7 wins |
|---|---:|---:|
| Unseeded NSGA-II | **+4.464%** | **17/25** |
| FLA-3W | **+1.632%** | **12/25** |
| reconstructed MLEAO | +41.811% | 22/25 |

V7's relative HV versus unseeded NSGA-II by workflow: CyberShake_100 **+7.636% (5/5 wins)**, Epigenomics_100 **−0.463% (2/5)**, Inspiral_100 **+6.967% (5/5)**, Montage_100 **+11.650% (5/5)**, Sipht_100 **−3.473% (0/5)**. FLA-3W remains better on Montage_100 by **9.263%** (v7 0/5 wins) despite v7's gains over earlier FLA variants.

[25 complete five-family simulator replay runs, aggregated frozen HV and raw CSV](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41561219538).

**More conservative family-based uncertainty** calculated independently from immutable simulator replay CSVs:

| V7 versus | Mean paired % | Exploratory 95% family-block bootstrap interval | Five-family sign-flip two-sided p |
|---|---:|---:|---:|
| NSGA-II | +4.464% | **[−0.649%, +9.108%]** | 0.2500 |
| FLA-3W | +1.632% | [−5.833%, +11.455%] | 1.0000 |
| reconstructed MLEAO | +41.811% | [+16.613%, +70.693%] | 0.1250 |

With only five workflow families, these tests are coarse and **not confirmatory**, especially because earlier variants were repeatedly tuned on similar families. No stable superiority to NSGA-II/FLA-3W is established.

**Frozen reference sensitivity (same exact observed simulation points)**:

| Common worst-observed reference multiplier | V7 minus NSGA-II, mean paired % | V7 minus FLA-3W, mean paired % |
|---|---:|---:|
| 1.02 | +6.854% | +2.177% |
| 1.05 | +4.464% | +1.632% |
| 1.10 | +2.253% | +1.022% |
| 1.20 | +0.297% | +0.344% |
| 1.50 | **−1.099%** | **−0.317%** |

Thus a larger common reference point reverses the mean ranking of v7 versus NSGA-II even without changing a single schedule. Four of the 25 per-seed top-algorithm rankings changed under 1.50 versus 1.05. This sensitivity should be included in any paper. [Cluster-level statistics and five-reference-point robustness artifacts](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41561971589).

**Non-negotiable fairness caveat:** matched `NSGA-II[costseed]` is an opt-in counterfactual (not canonical NSGA-II) using the same two cost-efficient initial VM mappings. The initial six-case control found v7 **+0.019%** mean paired HV and only **2/6** wins versus cost-seeded NSGA-II, whereas v7 beat unseeded NSGA-II by +7.366% and 6/6 in those same cases. Therefore the observed improvement is substantially explained by giving an optimizer better starting solutions; a FLA-specific search advantage **has not yet been isolated**.

**Research status:** Engineering validation and objective evaluation are much stronger, but these experiments do not yet justify claiming Q1 journal publication or statistically significant superiority. The FLA code is a disclosed categorical-DAG adaptation, and MLEAO remains a reconstruction rather than a source-faithful independent replication. Primary simulated HV remains derived from planned-nondominated replay subsets rather than all visited schedules.

## Identical v7 and NSGA-II cost seeding was directly verified

A new independent GitHub Actions Java/WorkflowSim test invoked the explicit `fair-pair` experiment mode at a small 8×6 population-generation search. It asserts the **first two task-ID → VM-ID assignment maps from the passive objective recorder are exactly equal** for FLA v7 and `NSGA-II[costseed]`. The test also checks 56 actual target-function evaluations on each side and successful simulator replay.

The test passed; thus the counterfactual does not merely use two similarly named heuristics: both optimizers start from the exact same two deterministic task assignments. Other random initial members and the optimizer-specific search rules remain different, as expected. The feature is disabled in unseeded NSGA-II and DAG-FLA variants.

[Actual code assertions, Java build and simulator output](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41562447756).

An extended **five DAG × five seed** paired comparison of FLA v7 against identically cost-seeded NSGA-II was configured in `.github/workflows/fla-v7-full-fairness.yml`; retain its computed results and limitations separately rather than inferring conclusions from an in-progress run.

## Full 25-pair matched-cost-initialization fairness result

A full run of `FLAResearchExperiment ... fair-pair` compared the selected FLA `v7-costseed` against `NSGA-II[costseed]` using **identical first two low-cost initial task-to-VM assignment proposals** and **3030 fitness evaluations for EACH optimizer**, for all five 100-task DAG families and paired seeds 1 through 5. Every planned-nondominated candidate was independently replayed in WorkflowSim under the same stage-in-aware objective, with one common frozen simulator HV reference per workflow across BOTH solvers and all seeds.

| 100-task DAG family | Mean v7 HV relative to NSGA-II[costseed] | V7 positive paired seeds |
|---|---:|---:|
| CyberShake_100 | **−1.767%** | 1/5 |
| Epigenomics_100 | **−1.264%** | 1/5 |
| Inspiral_100 | **−2.870%** | 0/5 |
| Montage_100 | +1.528% | 4/5 |
| Sipht_100 | +0.896% | 3/5 |
| **All 25 paired cases** | **−0.695%** | **9/25** |

An exploratory family-block bootstrap over the five family means produced **95% [−2.107%, +0.743%]**; the exact five-family sign-flip two-sided value was **p=0.4375**. This is not a confirmatory inferential analysis, because only five correlated families and tuned search variants are studied. The main scientific implication is unambiguous within the evaluated cases: **v7 did NOT demonstrate superiority to NSGA-II when the latter received exactly the same two low-cost proposal schedules.**

[Complete 25-case pairwise replay logs, source SHA, per-candidate CSVs and common-reference HV aggregate](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41562247912).

Crucial distinctions:

- The earlier **+4.464%** v7 improvement over *unseeded* NSGA-II under the four-algorithm 1.05 reference is valid for that comparison, but must not be advertised as a FLA-specific operator improvement.
- The `NSGA-II[costseed]` control has a different common reference point because its observed candidate outcomes differ from those of the original unseeded four-algorithm experiment. Compare **paired relative changes within each analysis**, not absolute HV values across different experiments.
- A separate Java/WorkflowSim regression test passed an assertion that the **first TWO complete task-ID → VM-ID mappings are exactly equal** for both algorithms; neither received extra objective-search evaluations. [Seed identity verification](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41562447756).
- FLA's search mechanisms, even with this promising initialization technique, still require an independently demonstrated gain over a fair equally initialized NSGA-II. The next experimental option, `v8`, explores FLA-specific Pareto extreme survivor preservation. It remains hypothetical until actual logs confirm any improvement.

The default `NSGA-II` remains unseeded; `CONFIG_COST_SEEDING` is an opt-in fairness-test switch. Do not describe this GitHub fork as bit-identical to a user's local Windows checkout.

## V8 Pareto-extreme survivor retention: negative ablation (2026-11-03)

Hypothesis: the much narrower Pareto front of v6/v7 on Montage_100 might be improved by **FLA-specific environmental retention** of the best observed cost solution and/or best observed makespan solution. All V8 variants inherited the **identical v7-costseed initial proposals**, v6 population novelty repair, FLA archive recombination, and the same 3030 target-function evaluations, so the comparison is specifically about survivor selection and its interaction with guidance. All variants are default-OFF except when explicitly selected by the experiment driver.

A controlled v8 development run used Montage_100, CyberShake_100, Sipht_100 × seeds 1–3, population 30 and generations 100. All four variants completed with true WorkflowSim-replayed candidate fronts and one common frozen simulator-HV reference per DAG family across all seeds.

| v8 compared with v7-costseed | Mean paired simulated-HV change over 9 runs | v8 wins |
|---|---:|---:|
| v8-cost: reserve lowest-cost survivor | **−3.746%** | **3/9** |
| v8-dual: reserve cost and makespan extremes | −2.500% | 2/9 |
| v8-dual-guide: also use min-cost archive guide | −2.156% | 3/9 |

Family-level paired changes illustrate instability:

| DAG family | v8-cost vs v7 | v8-dual vs v7 | v8-dual-guide vs v7 |
|---|---:|---:|---:|
| CyberShake_100 | +0.109% | +1.018% | +2.266% |
| Montage_100 | **−8.995%** | −3.566% | −4.538% |
| Sipht_100 | −2.353% | −4.953% | −4.196% |

All methods visited roughly 98–99.5% unique assignments per evaluated candidate, so this negative result was not resolved by existing novelty repair. Retaining extreme individuals in one generation did not guarantee improved final global simulated Pareto coverage. **V8 is REJECTED as the selected FLA version on this development set**, but its negative ablation is preserved. No held-out v8 test or claims of v8 improvement should be inferred from successful CI. V7-costseed remains the strongest tested FLA *candidate*, but the full 25-case matched-seed comparator still found **−0.695% mean HV and 9/25 wins versus NSGA-II[costseed]**, so we have not isolated an improved FLA-specific optimizer.

[Actual 9-case v8 experiment, raw replay CSVs, evaluation-count assertions, and aggregate](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41562936100).

### Publication decision constraint

The project has useful reproducible engineering contributions and negative/positive algorithm ablations. It does **not** currently establish generally superior multiobjective DAG workflow optimization over a fair, equally initialized NSGA-II. Further studies should pre-register family, VM configuration, budget, comparator, shared reference points, and an untouched validation partition to avoid progressive tuning on the same small set of DAG families. No result here proves that a Q1 paper will be accepted.

## VM price-profile stress test with fair initializations (2026-11-03)

To assess whether the FLA-v7 versus `NSGA-II[costseed]` fairness result was specific to the original VM prices, we added **optional** `-Dliwsa.vmPriceProfile=linear|convex` synthetic cost regimes. The original VM rates `[0.15, 0.30, 0.60, 0.90]` remain the **unchanged default**, protected by a Java regression test. Synthetic profiles adjust only VM per-unit-time prices, and both solvers and the simulator see the SAME `CondorVM.getCost()`. The `linear` profile uses `0.15*(MIPS/250)`, and the `convex` profile uses `0.15*(MIPS/250)^1.5`. These are NOT verified cloud-provider rates or real cloud validation.

Both optimizers received the SAME first two deterministic task-to-VM mappings, confirmed by a runtime assertion. The same stage-in-aware planning evaluator and independent WorkflowSim replays were used; **each optimizer used exactly 3030 target-function evaluations**. Three 100-task DAG families (CyberShake, Montage, Sipht) × three seeds × two price regimes = **18 paired optimization comparisons**, all completed. HV is recomputed with one shared frozen reference **within each price regime and DAG across both algorithms and seeds**. Cross-regime *absolute* HV magnitudes are not comparable.

| Synthetic VM price regime | Mean paired v7 minus identically initialized NSGA-II simulated HV | v7 wins |
|---|---:|---:|
| Linear VM prices | **−0.836%** | **2/9** |
| Convex VM prices | **−0.753%** | **3/9** |

More detailed within-regime results:

| Profile | CyberShake_100 | Montage_100 | Sipht_100 |
|---|---:|---:|---:|
| Linear: v7 paired HV difference | −1.812% (0/3) | −1.153% (0/3) | +0.457% (2/3) |
| Convex: v7 paired HV difference | −1.627% (1/3) | +0.690% (2/3) | −1.321% (0/3) |

The fair-NSGA result under original prices in the separate five-family/five-seed report was **−0.695%** for v7 (9/25 wins). The different synthetic pricing choices tested here did not reverse the negative pooled mean. This is descriptive sensitivity only: two deliberately constructed profiles, three pre-studied families and three seeds per profile, not a preregistered independent real-cloud test.

**Research conclusion:** better initial schedules are transferable across optimizers; neither v7 cost initialization nor v8 environmental selection has established a FLA-specific advantage over a properly initialized NSGA-II. These results should be reported, not hidden in a publication attempt.

[Original logs, complete 18 paired WorkflowSim replays, equal-seed assertions, and frozen-reference per-profile CSVs](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41564175609).

The research branch remains isolated from `master`; no identity between GitHub and the user's local working tree has been verified.


## Two-by-two cost-initialization factorial: separating initialization from solver (2026-11-03)

We added a *controlled four-arm comparison* to avoid inferring that low-cost warm-start benefits are FLA-specific. The `costseed-factorial` mode runs the four arms within the same real WorkflowSim experimental session:

1. **DAG-Pareto-FLA v6-pop**, no cost-efficient seeds.
2. **DAG-Pareto-FLA v7-costseed**, two task-to-VM cost-efficient seeds.
3. **Canonical unseeded NSGA-II**.
4. **NSGA-II[costseed]**, with the SAME first two task-to-VM seeds as v7.

All four search arms use 3030 actual objective evaluations, the same stage-in-aware cost/time evaluator, and simulator replay of each recorded planned-nondominated solution. The implementation checks exact equality of the two deterministic seed assignments for arms 2 and 4. Every solver/seed in a DAG shares one frozen simulator-HV reference point. The default optimizers are NOT silently reconfigured.

**Factorial development pilot:** CyberShake_100, Montage_100, Sipht_100 × 3 seeds (9 paired cases).

| 100-task DAG | Within FLA: v7 vs v6 seed benefit | Within NSGA-II: seed benefit | v7 versus identically seeded NSGA-II |
|---|---:|---:|---:|
| CyberShake_100 | +6.343% | +6.852% | −1.368% |
| Montage_100 | +35.408% | +19.681% | +3.027% |
| Sipht_100 | +4.304% | −2.899% | −0.473% |
| **Pooled nine cases** | **+15.352%** | **+7.878%** | **+0.395%** |

The mean paired percentage improvement from the common seeds is larger within FLA than within NSGA-II in this three-family development pilot (+7.474 percentage-point difference-of-benefits), but the FLA and NSGA-II algorithms remain **essentially tied when both seeded** (+0.395% pooled; this is not a statistical superiority claim). This result is consistent with previously documented full-five-family matched-seed validation where v7 was **−0.695%** and won 9/25. Seed benefit is workload-specific and not necessarily positive for every solver (NSGA-II on Sipht).

**Important:** these are four observed search outcomes, not a formal ANOVA interaction. Initialization changes downstream stochastic trajectories. A follow-up two-family factorial with the same untouched variant code (Epigenomics_100 and Inspiral_100) was triggered separately; do not extrapolate this development result to those families until its Actions logs and CSV confirm completion.

[Four-arm live WorkflowSim factorial results, cost-seed identity assertion, and common-reference HV CSV](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41564848874).

No evidence so far proves that v7 has a general FLA-specific advantage over a properly initialized NSGA-II.


## Held-out factorial cost-seed verification: two additional 100-task families

The same frozen FLA v6/v7/NSGA-II/seeded NSGA-II four-arm 2×2 experiment was repeated on two *additional* 100-task DAX instances, Epigenomics_100 and Inspiral_100, seeds 1–3. They were not used for choosing v7 in the preceding three-family factorial but had been studied earlier in other experiments; they do **not** constitute an entirely fresh publication holdout.

All six paired jobs and the aggregate passed after an initial workflow-only CSV output-prefix mistake was fixed. The earlier failed workflow `41565463657` resulted from the mismatched prefix between the command's written CSV and the assertion's expected file. It was **not** an algorithm or evaluator failure. The corrected workflow `41565588764` compiled and ran all 24 solver evaluations with exactly 3030 fitness calls per arm, verified the identical two low-cost seed assignments, independently replayed all planned-nondominated candidates in WorkflowSim, and recomputed a single frozen reference per DAG family for all four arms.

| 100-task family | FLA seed benefit (v7 vs v6) | NSGA-II seed benefit | v7 minus identical-seed NSGA-II |
|---|---:|---:|---:|
| Epigenomics_100 | −1.990% | +0.911% | −0.995% |
| Inspiral_100 | +7.592% | +12.986% | −1.742% |
| **Six holdout pairs** | **+2.801%** | **+6.948%** | **−1.368%** |

Unlike the 3-family development factorial (+0.395% v7 versus equally seeded NSGA-II over 9 pairs), these two other families favor **equally seeded NSGA-II**. Combining the development and the held-out-for-factorial 15 cases as a purely *descriptive* equal-weight average gives approximately **−0.310%** v7 versus equally seeded NSGA-II. This is **not** a pooled 5-family, 5-seed confirmation and does not overturn the previously completed full five-family 25-case result (v7 −0.695%, 9/25 wins).

The relative benefit of giving low-cost seeds to FLA is also not stable across workflows: it is negative for Epigenomics_100. The between-algorithm difference remains small, workflow-dependent, and statistically unresolved. This is not evidence that v7's optimization operators beat NSGA-II.

[Six corrected held-out factorial runs, identical-seed assertion, exact evaluation counts, full replay CSV and report](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41565588764).

This finding reinforces the publication constraint: **cost-efficient initialization is a useful transferable heuristic but not, by itself, a demonstrated FLA-specific search contribution**. Both variants should remain separately labeled, and the negative result must be retained.


## v9 DAG-edge operators and fair-seeded Pareto geometry (2026-11-03)

**Proposed v9 operators** are optional FLA-only gene edits: co-locate high-transfer DAG parent/child jobs on one VM, separate co-located parent/child jobs to increase potential parallelism, or choose by the FLA objective-preference subgroup. They are NOT from the original FLA equations and are OFF unless explicitly selected. They never add a separate fitness call. A dedicated Java/WorkflowSim test checked actual assignment changes in 8×6 experiments: 56 evaluations per solver, **0** edge-change events for v7, **11** for v9-colocate, **20** for v9-separate and **17** for v9-adaptive. [Activation and budget assertions](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41566984094).

**Development set:** CyberShake_100, Montage_100, Sipht_100, seeds 1–3, population 30, generations 100, 3030 evaluations per candidate algorithm, same simulator-HV reference per family, independent WorkflowSim replay.

| Operator versus v7-costseed | Average paired HV across nine runs | Positive runs |
|---|---:|---:|
| v9-colocate | **+0.665%** | 5/9 |
| v9-separate | **−3.360%** | 3/9 |
| v9-adaptive | **−0.569%** | 6/9 |

v9-colocate was chosen *on the development set only* for extra-family testing. The extra-family test covered Epigenomics_100 and Inspiral_100, each seeds 1–3, unchanged 3030 evaluations and true WorkflowSim replay.

| Additional workflow family | v9-colocate paired HV versus v7 |
|---|---:|
| Epigenomics_100 | **−2.574%** |
| Inspiral_100 | **−0.125%** |
| **All six extra-family pairs** | **−1.350%, 1/6 positive** |

**v9 REJECTED** as a replacement: development-set improvement does not generalize to the two extra families. Do not label the v9 operators as a demonstrated performance contribution, and keep them opt-in and disabled by default.

[Development run and full CSV](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41566649425) · [Extra-family validation](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41567315386).

**Diagnosis using the existing complete 25-case identically cost-seeded FLA v7 versus NSGA-II reference run** `41562247912`, without any new optimizer evaluations: compare 100-task DAGs × five paired seeds with the SAME initial two cost seed solutions, the SAME 3030 evaluation budget, and objective values from actual independent WorkflowSim replays. For each algorithm/seed, compute the simulator nondominated subset from the already-planned-screened replay candidates, minimum observed makespan, minimum observed cost, cross-front domination fraction and unique genotype fraction.

- Across 25 paired cases, **FLA v7's minimum simulated makespan was on average 9.186% WORSE than identically cost-seeded NSGA-II**. The per-family differences were CyberShake +12.240%, Epigenomics +7.462%, Inspiral +15.016%, Montage +10.115%, Sipht +1.099%. Makespan is minimized, so all positive values are unfavorable to FLA.
- Across all five families, **minimum observed cost was equal** between the two algorithms (average +0.000%), consistent with the shared low-cost starting assignments.
- FLA's average simulator-nondominated front size was **45.96** points compared with seeded NSGA-II **48.92**. By contrast FLA actually explored **99.14% distinct VM assignments** versus seeded NSGA-II **93.54%**. Increasing assignment novelty alone is thus not an evidence-based repair.
- The cross-front dominance fractions were mixed: 37.81% of replayed-FLA-front points were dominated by at least one seeded-NSGA front point, whereas 46.13% of seeded-NSGA points were dominated by a FLA point; HV and extreme objective coverage cannot be inferred from dominance counts alone.
- These are **subset-front statistics**, NOT the globally achievable simulator Pareto front, because the original recorder replays only planning-nondominated visited schedules. The “makespan gap” is a practical diagnostic on the chosen benchmark procedure, not a proven mechanism or guaranteed optimizer weakness under exhaustive replay.

**Engineering interpretation and next experiment:** The low-cost extreme is shared almost exactly thanks to identical initial cost seeds; FLA's harder challenge appears to be improving the **minimum makespan extreme** while maintaining cost Pareto quality, not generating more distinct assignments. Any proposed makespan-targeted operator must receive a separate controlled ablation and be compared to a similarly initialized NSGA-II, not only to a weaker unseeded baseline.

[Immutable 25-case simulated-front geometry analysis and raw table](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41567489035).
