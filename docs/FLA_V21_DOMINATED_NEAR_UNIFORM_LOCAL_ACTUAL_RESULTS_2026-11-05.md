# v21 frozen dominated-near8 vs uniform8: local independent actual-HV diagnostic, 2026-11-05

**Research outcome: proposed near-planned-front distance proxy FAILS for FLA-v12, although NSGA-II exhibits a tiny positive mean. This is not a new evolutionary algorithm or demonstrated SCI improvement.**

## Source and audit status

- Prospective protocol `docs/FLA_V21_DOMINATED_NEAR_UNIFORM_FROZEN_2026-11-05.md` was frozen before original simulator labels.
- Original true WorkflowSim [run 41990207133](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41990207133): all eight workflow×seed source jobs **SUCCESS**, with eight archived source ZIPs, all from exactly source SHA `9f4d0c4250068cf60be32aa06a92c83381bfb5b1`.
- Eight scenarios: Montage_50, Sipht_60, CyberShake_30, Epigenomics_46 × new seeds 991/992. Each has FLA-v12 and cost-seeded NSGA-II: original 3030 counted cheap planning fitness visits each, plus **16 original K16 actual WorkflowSim replays, then 8 nearby planned-dominated and 8 uniform-remainder dominated replay calls** per solver; total 8×2×32 = **512 original true simulator replay records**. These are not 512 statistically independent workflows.
- Independent local audit directly downloaded all eight original ZIPs and recalculated the same-(workflow,seed) common 1.5× actual-Makespan/Cost-max normalized 2D hypervolume for both solvers and both cohorts, using the 512 source replay rows. It asserted equal 16+8+8 source-row strata, consistent two solvers and single source SHA. The local analysis did **not** yet independently rehash complete original search-history SHA or verify every planned-dominance orientation. Those additional requirements remain delegated to the source-auditor `scripts/fla_v21_dominated_near_uniform_actual_audit.py`.
- The first formal GitHub independent [audit run 41990449010](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41990449010) failed because it launched before the eight original job artifacts were downloadable (the step found ZERO artifacts). Identical audit script was re-queued using GitHub Actions rerun-failed-jobs after verifying all eight original artifacts were present. **DO NOT state this GitHub audit has passed until its actual successful log is checked.**

## Independently recomputed near8 minus uniform8 true-HV differences

| Workflow | Seed | FLA-v12 | NSGA-II |
|---|---:|---:|---:|
| CyberShake_30 | 991 | +0.000000000 | +0.000000000 |
| CyberShake_30 | 992 | −0.000010838 | +0.000000746 |
| Epigenomics_46 | 991 | −0.000088700 | +0.000000027 |
| Epigenomics_46 | 992 | **−0.001241504** | +0.000000105 |
| Montage_50 | 991 | +0.000000000 | +0.000000000 |
| Montage_50 | 992 | +0.000008066 | +0.000003812 |
| Sipht_60 | 991 | +0.000000016 | +0.000000000 |
| Sipht_60 | 992 | +0.000000000 | +0.000000001 |

For scientific decisions, tolerances of 1e-10 distinguish ties:
- **FLA-v12: mean near−uniform ΔHV −0.000166620**, 2 wins, 3 ties, 3 losses. A very consequential Epigenomics_46 seed992 negative dominates the mean.
- **NSGA-II: mean +0.000000586**, 6 wins, 2 ties, 0 losses, but absolute improvements are small and an unstudied external family holdout has NOT been tested.
- A candidate's distance to the *predicted* Pareto front is NOT a reliable proxy for its true HV contribution. The near8 heuristic cannot be declared a robust, beneficial FLA replay policy.
- These sample sets have **extra simulator calls on top of the same original K16**. Do not advertise the near8 diagnostic as K16 budget-fair algorithm improvement; it also reuses historically familiar DAG families. No p-values based on the repeated within-family candidates.

## Research decision

Reject a new FLA optimizer motivated ONLY by near-front 2D Euclidean distance or shallow novelty. The next prospective mechanism would need a sharper hypothesis relating false planning dominance to DAG dispatch/cost consequences, plus a matched compute-time and real-K16 selector with an independent unseen family. Do not tune on these already observed seeds. A rigorous scientific **methodology and model-fidelity paper** may be more attainable than claiming superior multiobjective scheduling at this stage. Retain all negative FLA and positive NSGA-II observations.

All work is on `fla-baseline`; `master` untouched.
