# v18 FLA-specific disagreement-targeted relocation: frozen first experiment (2026-11-04)

**Preoutcome:** v18 source implemented, but no true-HV search result has been seen. Its success or failure will be reported unchanged. Previous shared-decoder variants were not stably beneficial.

## New candidate and motivation
- In FLA only, use both independent deterministic planning models on the *already-proposed* child genotype to locate the original Task ID with largest absolute predicted start-time discrepancy; if at least one VM alternative is allowed, propose ONE relocation toward a low-service/low-load VM for latency-focused FLA subgroup or low-cost/load VM for cost-focused subgroup. Proposal probability is locked at **0.35** per child, and the highest disagreement task is chosen deterministically with original topological tie order.
- Original FLA v12 diffusion, equilibrium, steady-state operators, diversity archive, cost seeds, Pareto-HV bandit and one final objective evaluation per generated child are retained. v18's extra dual-model predictions count as auxiliary **proposal overhead**, not additional main objective evaluation; measure the extra wall time and active relocation count explicitly. Neither prediction uses actual WorkflowSim labels.
- v18 default flag `CONFIG_DISAGREEMENT_RELOCATION=false`; only the explicit variant `v18-disagreement` enables it. No other variant changes. `master` untouched.
- No modified shared search objective; all three comparison arms use the ORIGINAL `-Dworkflowsim.planningStageInAware=true` insertion objective. This isolates a genuinely FLA-specific *search proposal* rather than a common decoder replacement.

## Locked experimental first gate
- Cases: `CyberShake_50` and `Montage_50`; seeds **211,212**, default VM speed. Prior platform has studied these families; they are NOT independent family holdouts.
- Every case is a single 3-arm run `v18-disagreement-three-arm`: FLA v12 original, FLA v18, cost-seeded NSGA-II. Identical two deterministic initial cost-seed assignments for all arms, same VM/task encoding.
- 30 population × 100 generations = **3030 counted target objective evaluations/arm**, all recorded and asserted; prospective K16 true simulator calls/arm under planned-only Pareto-cover, no search-time true simulation feedback.
- 2 DAG × 2 seeds = four benchmark invocations; 12 full optimizer runs, total **192 true WorkflowSim replay calls** if all succeed.
- One *common true HV reference per DAG/seed across all three real K16 sets*; 1.5× primary and 3.0× sensitivity based on merged actual maxima. Do not compare per-run HV at distinct reference points.
- The planned outcome metrics are paired v18-v12 normalized true K16 HV, solver performance relative to seeded NSGA-II, search runtime overhead, task/VM proposal count and actual changes; all negative cases preserved.
- Hypothesis falsification: 0 or negative gains, high runtime, empty proposed changes, or poor cross-DAG transfer rejects the v18 operator. Four blocks are development research, not statistical evidence for publication.
- No model/trigger-rate changes after seeing these outcomes; no default promotion or master edits.
