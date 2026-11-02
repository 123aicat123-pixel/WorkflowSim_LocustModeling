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
4. Expand to more DAG sizes, pricing regimes, VM heterogeneity, and independent workload families. Preserve development/held-out distinction after tuning.
5. Add a pre-registered reference point, IGD+ or epsilon indicator when justified, cost/makespan front visualization, runtime overhead, and stronger statistical power (more independent seeds/workloads).
6. Candidate screening by planned nondominance may lose assignments that become non-dominated **after** simulation; quantify this approximation or replay every distinct candidate on selected small tests.
7. This repository branch is not verified byte-for-byte identical to the user's local Windows source tree.

**Conservative current claim:** V6 novelty repair improves FLA search efficiency and achieves positive simulated-HV gains against FLA-3W and reconstructed MLEAO on tested workloads; it is broadly competitive with NSGA-II, but cannot claim superiority. No journal acceptance/publishability is guaranteed.
