# v20 frontier-novelty DAG search: independently verified REAL K16 results (2026-11-05)

**Scientific decision: DO NOT PROMOTE v20.** All **six original experiments passed**, but the new DAG novelty search yields **negative average true Pareto HV relative to original v12 and to the matched random novelty comparator**. This is a successful falsification and reproducible negative result, not a superior SCI optimizer.

## Original, preregistered scientific chain

1. Fixed prospective design (before new actual results): `docs/FLA_V20_FRONTIER_NOVELTY_FROZEN_PROTOCOL_2026-11-04.md`, source commit `93992cf`. The v20 DAG and random mechanisms are opt-in and preserve original `master`, v12 defaults, original FIFO and seeded NSGA-II.
2. Four-arm original actual simulator [GitHub Actions 41969565802](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41969565802) **6/6 SUCCESS**, original identical source SHA `54e48c539d5bf22bb01ae47054d17300c0701549`. Scenarios: three PREVIOUSLY STUDIED workflow families `CyberShake_50`, `Sipht_60`, `Epigenomics_100`, seeds 951/952, same default VM profile. Each scenario tests original FLA-v12, v20 random, v20 DAG, cost-seeded NSGA-II; **3030 counted StageInAware target genotype fitness evaluations per algorithm** and **16 actual WorkflowSim replays per algorithm**. Therefore 6×4×16=**384 true actual simulator outputs**, 24 solver-arm fronts.
3. Independent immutable [GitHub Actions 41969698627, second attempt SUCCESS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41969698627): re-downloaded all SIX original source artifacts after their uploads completed; asserts count, correct original physical TaskID->VM mapping, source SHA, real objective values, original evaluation count; recomputes common per-DAG/seed normalized 2D real HV under 1.5× and 3× actual-max reference. It never evaluates the optimizer or simulates a new solution.
4. First audit attempt FAILED because only the first source artifact was available when download occurred. That premature attempt correctly rejected five missing source blocks. An unchanged independent audit rerun SUCCEEDED after 6/6 jobs finished.
5. A separate local independent audit directly parsed the original six source ZIP files and exactly reproduced the GitHub HV and paired delta numbers. A machine-readable local CSV is available alongside the GitHub original and audit report artifacts.

## Primary normalized K16 actual WorkflowSim HV (common 1.5× reference within DAG/seed)

| Workflow | Seed | v12 | v20 random | v20 DAG | NSGA-II | DAG − v12 | DAG − random |
|---|---:|---:|---:|---:|---:|---:|---:|
| CyberShake_50 | 951 | 0.44554345 | 0.45480512 | 0.43569066 | 0.45432202 | **−0.00985279** | **−0.01911447** |
| CyberShake_50 | 952 | 0.47705942 | 0.48093009 | 0.48994664 | 0.49309833 | +0.01288722 | +0.00901656 |
| Sipht_60 | 951 | 0.26157755 | 0.26230579 | 0.26254670 | 0.26262102 | +0.00096915 | +0.00024091 |
| Sipht_60 | 952 | 0.26210014 | 0.26209663 | 0.26210079 | 0.26190795 | +0.00000065 | +0.00000416 |
| Epigenomics_100 | 951 | 0.35246614 | 0.34887883 | 0.34586010 | 0.33944036 | −0.00660604 | −0.00301872 |
| Epigenomics_100 | 952 | 0.34579316 | 0.34045268 | 0.34365166 | 0.32577855 | −0.00214150 | +0.00319898 |

- **DAG vs v12**: mean ΔHV **−0.000790552**; wins/ties/losses **3/0/3**.
- **DAG vs equally triggered four-proposal RANDOM novelty**: mean ΔHV **−0.001612097**; wins/ties/losses **4/0/2**. The large CyberShake seed951 loss dominates average. Reporting only win counts would be misleading.
- **RANDOM novelty vs v12**: mean +0.000821545; wins/ties/losses 3/0/3, not robust.
- **DAG vs seeded NSGA-II**: mean +0.000438052; wins/ties/losses 3/0/3, not robust.
- Actual 3× reference sensitivity preserves the negative mean: DAG−v12 **−0.000749365**, DAG−random **−0.001220391**.

## Mechanistic observation: greater visited novelty is not reliable Pareto gain

Unique physical mapping count out of the 3030 charged original target-fitness visits:

| Workflow | Seed | v12 unique | Random unique | DAG unique |
|---|---:|---:|---:|---:|
| CyberShake_50 | 951 | 3002 | 3021 | 3018 |
| CyberShake_50 | 952 | 3022 | 3024 | 3019 |
| Sipht_60 | 951 | 2873 | 2973 | 2852 |
| Sipht_60 | 952 | 2755 | 2966 | 2968 |
| Epigenomics_100 | 951 | 3018 | 3030 | 3026 |
| Epigenomics_100 | 952 | 3009 | 3024 | 3022 |

- RANDOM exploration increased unique visited mappings in **6/6 blocks**, but HV wins/losses were split **3/3**. DAG increased unique mappings in **4/6** blocks, with true HV also **3/3** vs v12. This directly disproves the simplistic assumption that increasing Hamming diversity alone guarantees real Pareto improvement.
- The v20 four proposals are ONLY genotype/parent-population comparisons, not extra target evaluations. They still consume compute; equal target-evaluation counts are **not** total compute-time parity. Per-source `search_ms` varied materially with scenario and algorithm order; do not advertise v20 CPU speedups without dedicated time-matched, order-randomized measurement.
- FLA already contains alternative DAG block, V6 novelty repair, global Pareto crowding, v14 timeline and v18/19 planning proposals. Novelty claims must distinguish new v20 population-minimum Hamming mechanism and test against prior work; simply adding task graph structure and diversity is NOT sufficient originality.

## Decisions

1. **Reject current v20 as an improved FLA SCI candidate** on observed development family data. Do not tune trigger 0.35, four proposals, or co-location on these exact blocks then reuse them as prospective holdouts.
2. Stop layering shallow operators on v12. The more credible research bottleneck is planner/simulator decision fidelity and meaningful objective-space Pareto discovery, which needs a new, controlled formulation, not just more unique genotypes.
3. A publication-oriented follow-up should first pin down an independently testable mechanism or a defensible reproducibility/model-fidelity paper. Require unstudied DAG families and size regimes, equally seeded and compute-time matched baselines, strong external solvers, predeclared 20+ seeds, IGD+/HV sensitivity, and full negative results.
4. No true Pareto optimum or global search headroom is inferred from 16 replays per arm. Six DAG/seed blocks are not six independent unseen-family observations. No Q1 or SCI algorithm-superiority claim is currently supported.
5. All work remains on `fla-baseline`; `master` untouched.

**Verdict: v20 engineering/true evaluation PASS; v20 improved optimization claim FAIL.**
