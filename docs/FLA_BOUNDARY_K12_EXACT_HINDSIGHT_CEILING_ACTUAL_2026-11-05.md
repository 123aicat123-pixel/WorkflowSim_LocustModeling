# Exact K12+4 replacement oracle over original true WorkflowSim replays (2026-11-05)

**INDEPENDENT AUDIT SUCCESS. Scientific decision: abandon further calibrated replacement-gate tuning on the already inspected fixed-K12, observed-tail corpus. The FLA-v12 real-HV headroom is too small to support an ambitious performance claim.**

## Frozen evidence and method

- Original precommitted experimental protocol `docs/FLA_BOUNDARY_FOUR_K16_FROZEN_2026-11-05.md`, true simulator source 24-job [run 41975729241](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41975729241) from SHA `197ffc5ddb828425b25280a1f83d9911cf21d3f3`: 24/24 SUCCESS, **768 K16 replay records** across 4 workflow sizes, 2 seeds, 2 original solvers, 3 selection policies.
- Source already independently audited in [41975775235 attempt 2 SUCCESS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41975775235), including source SHA, search-history SHA, identical first K12 baseline assignments, K16 count and physical true outcomes.
- New [exact hindsight audit 41981439412 SUCCESS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41981439412): `scripts/fla_boundary_k12_exact_oracle_audit.py` reads all 24 *archived original* artifact source folders, checks all identities and source SHA, and **exhaustively enumerates every four-mapping subset** from the up-to-12 distinct already replayed final-four alternatives across baseline, boundary-four and random-four. No optimizer/READY/WorkflowSim execution in audit.
- The fixed first K12 physical TaskID→VMID maps are preserved; the oracle is allowed to change ONLY the last four. It optimizes actual normalized 2D makespan-cost HV with the common same-(DAG,seed) 1.5× actual reference across BOTH solvers and ALL 3 policies, with 3× sensitivity included in the CSV. This is an exact maximum **within the restricted observed candidate-tail union and frozen first K12**; it is NOT the globally optimal workflow scheduling front, not an upper bound over the full 3030 visited genotypes, and not a deployable or prospective algorithm.
- In the source tail union, each block had exactly **12 distinct tail mapping choices**, so the audit evaluated `C(12,4)=495` combinations per solver/seed/DAG block. It also evaluated the best single exchange, often matching nearly all the attainable improvement.

## Exact true-label oracle vs original unchanged Pareto-cover K16

| Workflow | Seed | FLA exact oracle real-HV gain | NSGA-II exact oracle real-HV gain |
|---|---:|---:|---:|
| Montage_50 | 971 | +0.000004952 | +0.000005056 |
| Montage_50 | 972 | +0.000000782 | +0.003416220 |
| Inspiral_50 | 971 | +0.000000000 | +0.000000000 |
| Inspiral_50 | 972 | +0.000000112 | +0.000000000 |
| CyberShake_30 | 971 | +0.000000000 | +0.000000000 |
| CyberShake_30 | 972 | +0.000000000 | +0.000000000 |
| Epigenomics_46 | 971 | +0.000287363 | +0.000000000 |
| Epigenomics_46 | 972 | +0.000120531 | +0.000000000 |

- FLA-v12: **mean maximum hindsight ΔHV = +0.000051718**, 5 positive/3 zero of the 8 blocks; largest +0.000287363.
- NSGA-II: mean +0.000427660, positive in only 2/8 blocks. The mean is driven by NSGA-II Montage_50 seed972 alone (+0.003416220), not a general algorithm effect.
- Best exact hindsight swap is an *unachievable control using simulator truth*. It must never be reported as a new selection method or prospective result. A deployable boundary selector must do worse or at most equal this narrowly constrained ceiling under the SAME observed candidate union.
- The source Boundary-Four prospective policy itself **FAILED**: vs original Pareto-cover mean -0.000569495 across 16 paired blocks, 2 wins/14 losses; FLA-only 1 win/7 losses.

## Stop decision

**No additional epsilon/risk/READY replacement gate should be tuned on these 971/972 cases.** The observed limited improvement potential makes such tuning an unpromising basis for an SCI algorithm-superiority paper. The small exact ceiling applies only to the already simulated up-to-12 tail mappings, NOT the unobserved remaining search history or other DAGs; do not generalize this as proof that better candidate pools do not exist.

Next valid research route should change and independently measure **objective-space candidate generation/search quality**, or separate a methodological **planner-vs-simulator Pareto decision fidelity** paper without unsupported superiority claims. Any new generation operator must have a distinct preregistered mechanism and strong baseline/ablation comparison, as simply maximizing Hamming diversity (v20) was already negative. New original DAG family sizes, untouched seeds and actual equal compute-time are required.

All original adverse outcomes retained; `master` unchanged, all experiment code opt-in on `fla-baseline`.

**Verdict: exact, reproducible observed-tail ceiling PASS; worthwhile FLA K12+4 rescue gain NOT demonstrated.**
