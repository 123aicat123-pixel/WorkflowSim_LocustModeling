# v21 DAG structural risk K8 offline assessment: audit-confirmed mixed result (2026-11-05)

**Gate verdict: REJECT current static structural-risk heuristic as a validated improved FLA selector.** It is better than the already failing near-front proxy for FLA, but not reliably better than uniform exploration, has inconsistent cross-family results, and reuses already observed v21 real-simulator labels. This is retrospective methodological evidence, NOT a new prospective optimizer success.

## Original sources and frozen decision

- Protocol fixed BEFORE the new structural scoring calculation: `docs/FLA_V21_STRUCTURAL_RISK_OFFLINE_K8_FROZEN_2026-11-05.md`, commit `cda14478`.
- Original v21 true WorkflowSim source [41990207133](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41990207133) 8/8 SUCCESS, original source SHA `9f4d0c4250068cf60be32aa06a92c83381bfb5b1`. Four already studied workflow families `Montage_50`, `Sipht_60`, `CyberShake_30`, `Epigenomics_46` × seeds 991/992 × original FLA-v12 and seeded NSGA-II. Per arm: 3030 counted planned fitness evaluations, K16 original actual simulator replays, 8 source `near-planned-front` and 8 source `uniform-remainder` strict planned-dominated additional *actual* WorkflowSim evaluations. Total 512 source replay records; not 512 independent workflow observations.
- Independent original source rank audit [41990449010](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41990449010) PASS.
- New read-only [DAG structural K8 audit 41998201621](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41998201621) **SUCCESS**; artifact ID `13401840641`. `scripts/fla_v21_structural_risk_offline_audit.py` reconstructs original TaskID 1…N from committed DAX XML job occurrence order, reads DAG parent-child edges, validates 8 source archives, 16 exact original ordered candidate-history SHA256 checks, original FLA/NSGA fitness counts, exact physical mapping and source planned objective values, strict planned-dominated sample membership, and shared reference. This is a new retrospective **analysis** of already existing original true-label observations. No new simulator calls, optimizer changes, READY model or learned weights.
- Fixed scoring before looking at newly computed rankings: **0.5×VM max work fraction + 0.5×DAX child-runtime-weighted fraction of cross-VM dependency edges**; higher is higher static risk. These features are *proxies*, not measured real queue delay or network transfer. Top8 of the EXACT union of previously selected near8 and uniform8 candidates; held K16 baseline unchanged, exactly eight additional original simulator labels per compared policy.
- Controls: original near8, original uniform8, **32 deterministic original-score-blind random K8 selections** from the same 16 previously true-evaluated candidates, and infeasible **exact true-label hindsight C(16,8)=12,870 subset oracle** per block. One shared 1.5× actual reference per (DAG,seed), two solvers, with 3× sensitivity. The complete machine-readable 48 policy-case HV rows, 256 original candidate structural features and original untouched source CSV are retained in GitHub Action artifact.
- Source labels were already inspected before design, so this is NOT prospective performance validation, even if scorer did not directly read true labels.

## Actual normalized HV (STRUCTURAL − comparator), FLA-v12 only

| Source DAG | seed | static structural K8 actual gain over K16 | near8 gain | uniform8 gain |
|---|---:|---:|---:|---:|
| Montage_50 | 991 | +0.000000000 | +0.000000000 | +0.000000000 |
| Montage_50 | 992 | +0.000008066 | +0.000008066 | +0.000000000 |
| Sipht_60 | 991 | +0.000000016 | +0.000000016 | +0.000000000 |
| Sipht_60 | 992 | +0.000000000 | +0.000000000 | +0.000000000 |
| CyberShake_30 | 991 | +0.000000000 | +0.000000000 | +0.000000000 |
| CyberShake_30 | 992 | **+0.000000000** | +0.000000000 | **+0.000010838** |
| Epigenomics_46 | 991 | +0.000169406 | +0.000120906 | +0.000209606 |
| Epigenomics_46 | 992 | **+0.001242137** | +0.000000437 | +0.001241941 |

Primary FLA-v12:
- Structural−near8: mean **+0.000161275**, 2 wins/6 ties/0 losses. Note that the existing near8 policy was already proven weak.
- Structural−uniform8: mean **−0.000005345**, 3 wins/3 ties/2 losses. Therefore the frozen gate requiring beating BOTH comparators fails.
- Mean absolute marginal structural-K8 true HV increment **+0.000177453** vs original 32-sham random-K8 mean **+0.000097277**. However these figures are driven by one `Epigenomics_46` seed992 high-impact case, and structural is worse than sham average for `CyberShake_30` seed992 and `Epigenomics_46` seed991. Eight familiar blocked cases do not support external generalization or statistical significance.
- Mean exact hindsight `C(16,8)` true-label oracle gain +0.000198792, an impossible retrospective upper ceiling on the already selected 16 maps, **not** the global optimizer optimum or unknown un-replayed history.
- NSGA-II structural−near8 mean **−0.000000493** (0/3/5), structural−uniform8 mean +0.000000094 (3/5/0). The model is not algorithm-invariant.
- Many near-predicted-front / queue-exposure cases produce zero true HV because a false planned-dominance relation does not guarantee a valuable uncovered true Pareto region.

## Scientific decision

**Do not tune 50/50 weights, sign, thresholds, or VM/DAG feature variants to this observed v21 cohort and reuse its true simulator labels as holdout data.** A next experimental opportunity requires a *new prospective K16-equal-budget selector and genuinely untouched source simulator outcomes/family or simulator regime*, pre-frozen classifier risk assumptions, independent RNG, at least 20 seeds and equal measured total compute. These retrospective observations alone do not establish that a DAG queue-exposure score predicts true candidate value.

The defensible present research contribution is a transparent and reproducible **Pareto decision fidelity / sample-selection bias methodology**, with independently audited positive AND negative controls, rather than an unsupported improved-FLA-optimizer claim. Preserve original unchanged FLA-v12 and seeded NSGA-II baselines. All code and documentation remain only on `fla-baseline`; `master` untouched.

**PASS reproducible structural diagnostic, FAIL superior scheduling method.**
