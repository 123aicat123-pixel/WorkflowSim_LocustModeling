# Real K16 cross-VM speed, reference sensitivity and independently generated synthetic DAG topologies (2026-11-03)

**Decision:** do **not** promote `online-observed-hv` as universally beneficial or claim FLA v12 generally beats NSGA-II. Keep `pareto-cover` default. Everything in this note is isolated to `fla-baseline`; `master` is unchanged.

## 1. 20-case alternate-size WorkflowSim VM-speed study — VERIFIED

- [Original complete 20/20 successful matrix run 41603751878](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41603751878), execution source commit `fc3af642965572c9422da46777bfb53efed4dc0d`, aggregate artifact `crossvm-summary-41603751878` ID `13214994112`. Per-case original artifacts preserve candidate simulation labels, full history fingerprints, timing logs, VM profile protocol.
- DAX instances: CyberShake_50, Epigenomics_46, Inspiral_30, Montage_50, Sipht_60; **different sizes within five previously explored workflow families**, not entirely unseen real-world families. Two optimization seeds 113,114, two machine-speed regimes: baseline default and synthetic within-tier staggered (65%,80%,90%,100% of tier MIPS, 16 VMs, original rental costs), three algorithms v7/v12/NSGA-II. Each policy/solver independently executes 3030 planner fitness evaluations and exactly K16 true WorkflowSim replay calls. The same source SHA, exact solver visited genotype/planned-double history SHA-256 and four warm-start candidates match across the two K16 policies in each regime.
- Added code: `LIWSABenchmarkExample.vmMips`, property `-Dliwsa.vmSpeedProfile=staggered`, default `default`; source preserves the existing 250,500,1000,2000 MIPS ×4 table when property absent. `VMSpeedProfilesRegressionTest` confirms exact default unchanged, staggered speed factors, VM IDs, default/convex rental cost and invalid profile rejection.
- Primary evaluation reference deliberately constructed from ONLY baseline Pareto-cover **PLANNED** values across seeds and algorithms per DAX/speed, coordinatewise `3×max+1`. No true simulation labels or online selected candidates influence it. This intentionally conservative distance can obscure HV differences.

| VM speed | Solver | Average online-observed vs cover simulator HV | Wins /10 |
|---|---|---:|---:|
| default | FLA v7 | +0.1100% | 8/10 |
| default | FLA v12 | **+0.0062%** | 7/10 |
| default | NSGA-II | +0.2434% | 10/10 |
| staggered | FLA v7 | +0.1468% | 8/10 |
| staggered | FLA v12 | **+0.0025%** | 8/10 |
| staggered | NSGA-II | +0.0136% | 9/10 |

The online selector can add CPU overhead; its total running time was not consistently lower. Negative FLA-v12 example Epigenomics_46 staggered seed 113: −0.0444% HV.

## 2. HV reference-point robustness — VERIFIED, NO NEW SIMULATIONS

- [Reanalysis run 41604765542](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41604765542), artifact `crossvm-reference-audit-41604765542` ID `13216700033`, source `scripts/fla_cross_vm_reference_audit.py`. All 10 workflow/speed reference sets at factors **1.10,1.25,1.50,2.00,3.00× planned baseline maxima +1** contained every original real simulator outcome; no after-the-fact reference rescue or clipping.
- FLA v12 **default** mean online relative HV changes from **−0.1789% at 1.10×**, −0.0634% at 1.25×, −0.0161% at 1.50× to **+0.0062% at 3.00×**. Therefore the *SIGN of mean improvement* depends on the legitimate scoring reference, not on rerunning/altering a single candidate.
- FLA v12 **staggered** mean online gain ranges +0.0140% at 1.10× to +0.0025% at 3.00×, still extremely small. Within staggered regime, average improvement of actual minimum makespan and minimum cost is **zero** for FLA v12. Reference-free strict Pareto dominance comparisons also preserved in the artifact.
- Do NOT select a favorable reference after observing these numbers and claim preregistered superiority. All scale values were diagnostic on existing evidence.

## 3. Direct FLA v12 versus NSGA-II search comparison — VERIFIED

- [Independent 20-case rescore Actions 41605075669](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41605075669), source `scripts/fla_cross_vm_solver_gate.py`. It consumes the pinned reference audit and makes zero new simulation calls.
- Under the 1.50× reference, mean paired FLA v12 versus costseed NSGA-II selected-real-HV advantage was **+0.3273% (baseline VM/cover)**, **−0.2523% (baseline VM/online)**, **−1.2368% (staggered VM/cover)**, **−1.3177% (staggered VM/online)**.
- For **all five** tested reference factors and **both** replay policies, the *mean* matched FLA-v12 relative HV in the staggered VM regime was negative. Some individual matched cases favored v12 (e.g. six wins out of ten under 1.50×), so do not overinterpret the average as universal inferiority.
- This is an equal evaluation / same first two cost-seed / equal real K replay comparison on **selected** outcomes, not an exhaustive simulator oracle of all visited/genotypic possibilities.

## 4. Planner-to-simulator makespan ranking error — VERIFIED

- [Independent K16 regression Actions 41605317560](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41605317560), artifact `crossvm-rank-fidelity-41605317560` ID `13216451074`, source `scripts/fla_cross_vm_rank_fidelity.py`, original 20 per-job data only.
- In cover-selected K16 cases, mean planner actual-makespan relative error was **1.4006% (default)** versus **1.7550% (staggered)**; Kendall tau-b **0.9633 vs 0.9517**. Corresponding cost MAPE **0.0028% vs 0.0020%**.
- FLA v12 in Epigenomics_46 is an especially poor makespan proxy: **7.8108%** default, **9.0173%** staggered average relative error; Kendall **0.6833/0.7500**. These are **selected K16** statistics, not complete-visited rank studies. As speed changes, optimizer histories also change, so this is not an isolated causal speed-to-error coefficient.

## 5. Newly generated, topologically distinct synthetic DAGs — VERIFIED, NOT REAL UNSEEN FAMILIES

- Deterministic DAX generator `scripts/fla_locked_synthetic_dax.py`, fixed topology RNG seed **20261103**, creates `SynthWide_40` (5 layers × 8 nodes, 2–3 previous-layer predecessors) and `SynthDeep_40` (four mostly serial 10-task chains with cross-lane edges), both with 40 valid CloudSim/Pegasus jobs.
- [Four of four actual WorkflowSim preflight cases passed, Actions 41605666507](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41605666507), including DAX SHA-256 and both VM speed profiles.
- [Full eight of eight three-policy K16 experiment jobs and aggregate PASSED, Actions 41605963046](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41605963046), source SHA `02cbf01673c86b8fc75c214458d5085b656de279`, aggregate artifact `synth-holdout-report-41605963046` ID `13217450395`.
- Each synthetic topology × speed × seed 121/122 block compares **three** policies: `pareto-cover`, `online-planned-hv`, `online-observed-hv`. All solvers get **3030 planner calls + 16 true simulator replays per policy**, same exact SHA candidate search histories and same four warm-start assignments. References were fixed before scoring as `1.5×` baseline cover PLANNED maxima +1 primary and `3×` secondary; all actual points fit both.
- FLA v12 observed-front vs cover mean actual K16 HV at primary reference:

| New synthetic topology | Default VMs | Staggered VMs |
|---|---:|---:|
| SynthWide_40 | +0.0349% (2/2 wins) | +0.0877% (2/2 wins) |
| SynthDeep_40 | +0.9965% (1/2 wins) | **−0.1543% (0/2 wins)** |

- For **SynthDeep_40 + staggered VMs**, FLA v12 observed-front also lost **−0.1594% average versus the simpler planned-only greedy selector**. This shows a real failure mode of simulator feedback even where selection decisions use only previously observed true labels. In other regimes and algorithms online observed feedback sometimes helped substantially (e.g. NSGA-II SynthDeep default +1.1479% versus cover).
- This is a **locked synthetic-topology sensitivity study**, not external validation using new real scientific workflow families. Only two topology structures and two optimizer seeds; uncertain generalization and no publication-grade p-value.

## Overall scientifically defensible outcome and next gate

1. Keep baseline `pareto-cover` default and all online modes explicit opt-in, especially because online feedback can lose under deep-serial DAG × within-tier VM speed heterogeneity.
2. The value of observed-front feedback beyond planner-only greedy HV is highly dependent on DAG topology, resource regime and search solver; a universal positive effect is **not demonstrated**.
3. HV gains can switch sign when the evaluation reference changes, even with fixed simulator data. Publish the exact reference definition and robustness grid, as well as reference-free extreme and dominance measures.
4. Do not assert that FLA v12 surpasses NSGA-II under heterogeneous cloud infrastructure. It had negative *mean* selected HV across all tested reference scales in the staggered-VM 20-case study.
5. A further **prespecified and independently evaluated** risk-aware selector might decide whether to trust early observed simulator fronts, but must use only earlier labels; avoid tuning on the negative cases above and retesting them as independent evidence.
6. External scientific DAG instance families, realistic heterogeneity/cost and larger seeds/family-level inference are still needed. No search optimizer improvements were established by these post-search K16 candidate replay policies.
