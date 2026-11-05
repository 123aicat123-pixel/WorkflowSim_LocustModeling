# Frozen K12+4 Boundary-Four: independently audited actual WorkflowSim results (2026-11-05)

**Verdict: empirical boundary identification beats random exploration in aggregate, but the fixed-K16 policy FAILS to improve original Pareto-cover. No successful FLA innovation; do not promote or tune on these blocks.**

## Immutable evidence and validation

- Protocol frozen **before these actual labels** in `docs/FLA_BOUNDARY_FOUR_K16_FROZEN_2026-11-05.md` at commit `a8dd27e`.
- First launch `41975442523` failed at the original Java policy allowlist; preserved as an implementation failure, **NOT** counted as simulated outcomes.
- Corrected complete original [source run 41975729241](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41975729241), source SHA `197ffc5ddb828425b25280a1f83d9911cf21d3f3`: **24/24 source jobs SUCCESS**. Four DAX instances (Montage_50, Inspiral_50, CyberShake_30, Epigenomics_46) × new seeds 971/972 × three replay selectors; two original optimizers per job (FLA-v12, seeded NSGA-II), original 3030 search target fitness visits per optimizer, **K16 real FIFO WorkflowSim replays** per solver and policy, 24×2×16=**768 actual replay records**.
- Independent immutable [audit run 41975775235, second attempt SUCCESS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41975775235): first attempt retrieved zero artifacts because source job uploads were incomplete, then the **same audit script** was rerun after all 24 source jobs succeeded; validated 24 original artifact ZIPs, original search-history SHA-256 identity within the three selector arms for every workflow/seed/solver, exact matched first 12 physical TaskID→VMID assignments for boundary and random controls and initial Pareto baseline, correctly predicted dominated four exploratory mappings, exactly 3,030 source target-fitness calls and 16 actual replay assignments per solver, finite actual Makespan and Cost, and common per-(DAG,seed) normalized 1.5× reference with 3× sensitivity.
- The source selection code reads **only planned Makespan and Cost**, does not use WorkflowSim labels in the choice, and does not change the FLA/NSGA original search. Four additional non-baseline candidates strictly dominated by one of the original first K12 anchors are chosen by nearest normalized domination boundary or stratified random controls; both replace exactly four K16 slots.
- No new family holdout: the DAX families were already studied historically. No equal total CPU-time or 20-seed significance claim. Replayed K16 candidates are not independent blocks.

## Primary true Pareto HV: complete source-audited result

| Comparison | Mean normalized real HV difference | Wins/Ties/Losses across 16 (DAG,seed,solver) blocks |
|---|---:|---:|
| Boundary-Four − original 16 Pareto-cover | **−0.000569495** | **2/0/14** |
| Boundary-Four − equally budgeted K12+4 stratified random | +0.000201198 | 9/6/1 |
| Random-Four − original 16 Pareto-cover | −0.000770693 | 0/0/16 |

Under the 3× objective reference: Boundary−original mean **−0.000286907**, 2 wins /14 losses; Boundary−random mean **+0.000197617**, 9 wins /6 ties /1 loss. Thus the **qualitative negative** result is robust to this reference sensitivity.

### Crucial FLA-v12-only interpretation

- FLA-v12 Boundary−original has **1 win / 0 ties / 7 losses** across eight DAG/seed blocks and an approximate mean **−0.00063808** normalized HV (computed from audit display to 8 decimals; exact unrounded values are in the original independent CSV).
- FLA-v12 Boundary−random has **4 wins / 3 ties / 1 loss** but approximately **−0.00002928** mean due to a substantial Epigenomics_46 seed 971 loss. Therefore the overall cross-solver 9/6/1 boundary-vs-random pattern cannot be advertised as reliable FLA improvement.
- Explicit negative source cases: Epigenomics_46 seed971 FLA original=0.44624838, boundary=0.44356135, random=0.44392452; CyberShake_30 seed972 FLA original=0.53053161, boundary=0.52848382, random=0.52848382.
- One positive FLA source case: Epigenomics_46 seed972 FLA original=0.34505737, boundary=0.34516000, random=0.34503947. That isolated win is not a global model superiority result.
- An NSGA-II outlier Montage_50 seed972 drives much of the **positive** aggregate Boundary−random effect: original=0.30769888, boundary=0.31098405, random=0.30756228. Report this adverse/positive heterogeneity explicitly rather than inferring a stable FLA effect.

## Scientific decision and follow-up

The original prospective objective was to show both (1) improvement over the original full Pareto-cover K16 baseline and (2) improvement over a matched K12+4 random-dominated exploration ablation. **Condition (1) failed decisively**. A partial gain over random exploration does **not** validate new FLA search.

The loss has a clear structural explanation to test: sacrificing four of the strongest planned Pareto-cover candidates creates opportunity cost, and the rare true rescued near-boundary candidates usually do not make up the true-HV reduction. Do not conclude that the entire unobserved 3,030 visited history has no useful overlooked candidates; the true labels of most remain unknown.

The next defensible research gate is a *decision-theoretic*, label-free cost-benefit test of when an extra candidate **replaces** an existing Pareto candidate only when its predicted true-HV gain has credible out-of-sample evidence exceeding displacement loss. Existing uniform epsilon, ridge/RF residual correction, and active-1NN heuristics have failed and must not be relabeled as novel. An alternative is a reproducibility/selection-bias paper focused on empirical Pareto decision fidelity without algorithm-superiority claims.

**Archive all positive and negative evidence, source run IDs, exact random controls and fixed CPU assumptions. No modifications to master.**
