# Full 24-draw REAL K16 random-screening control, FLA v7/v12/NSGA-II (2026-11-03)

**Research status:** matched prospective simulator-call screening policy evidence, NOT evidence of optimizer superiority or independent 432-DAG statistical significance. Work only on `fla-baseline`; do not modify `master`.

## Three independently archived GitHub Actions cohorts

All three batches used the same planned-search code and policy, with four, eight and twelve NEW deterministic random replay repeats, respectively. The repeat index changes random screening only, not the optimizer seed. Java `budgetReplayReplicate=0` maintains historical compatibility; 1..23 select different pseudorandom genotypes. Pareto-cover is deterministic. Each case checked **3030 actual planned fitness evaluations** and **K=16 actual WorkflowSim independent replays per algorithm and policy**.

1. [Repeats 0–3, Actions 41585685819](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41585685819), original aggregate artifact `repeats-summary-41585685819` ID `13208195045`, SHA `e2c78948ff0d0b7485c46eb6e3a0d74734a2ee6c`.
2. [Repeats 4–11, Actions 41586015547](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41586015547), original aggregate artifact `repeats-summary-41586015547` ID `13207967884`, SHA `0393a579af99c20d6a85d7f7936c78b6806aa700`.
3. [Repeats 12–23, Actions 41586314881](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41586314881), original aggregate artifact `repeats-summary-41586314881` ID `13208310917`, SHA `d167e9b108a6f29979729d49ef5595915e8c1d05`.

**Evidence:** all three successful batch aggregates contain `random_repeat_paired.csv`, `random_repeat_hv.csv`, `random_repeat_case_summary.csv`, `random_repeat_report.md`, `source-sha.txt`; original per-job simulation objective CSVs and source manifests are also retained. Three batches contain exactly **72 + 144 + 216 = 432** selected-simulator-HV paired observations, with repeat indices 0..23 without overlap.

## Frozen reference and protocol

Three fixed DAGs, two fixed optimizer seeds each: CyberShake_100, Inspiral_50, Montage_25 and seeds 53/54. Three algorithms: DAG-Pareto-FLA v7-costseed, DAG-Pareto-FLA v12-hvbandit, cost-seeded NSGA-II. The two low-cost starting assignments are identical across solvers. Under each optimizer's same deterministic 3030-evaluation search history, Pareto-cover selects K=16 planned Pareto-layer/max-min diverse genotype assignments, whereas the random baseline selects K=16 without inspecting simulator outcomes. Both undergo **genuine separate WorkflowSim replay**, not simply offline evaluation of precomputed labels.

HV reference fixed *before this three-batch study* from [prior Actions run 41584672254](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41584672254):
- CyberShake_100: (7421.5516, 2911.5777924999998)
- Inspiral_50: (8423.484174999998, 6833.036574999994)
- Montage_25: (128.9026, 120.508165)

Raw HV across different DAG families is **never** averaged; all differences below are paired within-workflow relative HV percentages. The references are prior-data-derived, not externally mandated objective bounds.

## Exact results, computed from all three ORIGINAL per-draw CSV archives

| Algorithm | Mean cover-vs-random relative HV gain | Cover wins / 144 random screening draws | Minimum gain | Maximum gain |
|---|---:|---:|---:|---:|
| FLA v7-costseed | **+3.185044%** | **144/144** | +0.080426% | +17.756363% |
| FLA v12-hvbandit | **+3.081378%** | **144/144** | +0.529900% | +14.115069% |
| Cost-seeded NSGA-II | **+9.596128%** | **144/144** | +0.819600% | +42.655258% |
| **All arms and draws** | — | **432/432** | — | — |

Per-family mean across all three algorithms and 24 random draws per six solver-case combinations: CyberShake_100 **+4.497865%**, Inspiral_50 **+4.094097%**, Montage_25 **+7.270589%** (descriptive only).

**Interpretation:** The Pareto-diversity selector consistently improves *the quality of the simulated subset under a fixed real K=16 budget* compared to the deliberately simple uniformly random comparator within these fixed search histories. The larger benefit on NSGA-II demonstrates that this is a general post-optimization screening effect, not proof of a novel FLA search win.

## Boundaries and next gates

1. The 24 random draws are **conditionally repeated random screening**, not 24 independent optimizer seeds, DAGs, VM scenarios or workloads. The **432/432 count is not a statistical sample size for a significance test**. There are only three DAG families, six optimizer-seed cases, and three correlated optimizer arms.
2. Re-running the deterministic cover search multiple times is only a reproducibility check, not new independent evidence. These data cannot establish FLA v12 outperforming NSGA-II.
3. The comparison against a stronger **extreme-first scalar-sweep** selector is separate; it must be reported regardless of positive or negative results and should use new seeds and pre-frozen HV reference points.
4. Additional independent DAG families, seeds, heterogeneity/cost regimes, run-time accounting, and family-level uncertainty are needed before publication claims.
5. Source-level implementation and FLA original MATLAB-to-discrete fidelity limitations remain explicitly in `docs/FLA_RESEARCH_EVIDENCE.md`.
