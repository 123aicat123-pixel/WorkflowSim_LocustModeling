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
