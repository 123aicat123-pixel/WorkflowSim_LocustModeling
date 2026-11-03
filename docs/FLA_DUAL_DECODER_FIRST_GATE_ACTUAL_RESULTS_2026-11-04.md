# Dual-model FLA-v12/seeded-NSGA-II first true-HV factorial results — 2026-11-04

**Outcome: candidate worst-case dual-model promising but unproven. No default promotion.**

## Frozen original experiment and provenance
- Preregistration before new outcomes: `docs/FLA_DUAL_DECODER_SEARCH_FROZEN_PROTOCOL_2026-11-04.md`.
- New separate opt-in `DualModelScheduleObjective` evaluates both `StageInAwareScheduleEvaluator` and `ReadyQueueScheduleEvaluator` on the SAME genotype without touching real simulation labels; `mean` and componentwise `worst` variants selectable via `-Ddagfla.dualModelMode=mean|worst`. OFF by default.
- Both DAG-Pareto-FLA v12 and cost-seeded NSGA-II run exactly the same mode and deterministic cost-seed protocol. Each optimizer arm uses 3030 counted genotype objective evaluations, the alternative performs two internal decodes per counted genotype, and 16 independently executed actual WorkflowSim K16 replays selected only using the planned objective and a fixed pareto-cover rule.
- [New original 8-invocation, 16 optimizer-arm actual true simulator run 41672213156](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41672213156): 8/8 jobs PASS, a total of 256 K16 actual simulator replays across mean/worst treatments (plus 256 original old/ready from earlier run).
- [Historical original old/ready run 41670356422](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41670356422): 8/8 PASS; saved prior to dual-mode construction and not changed.
- First read-only summary [41672364876](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41672364876) FAILED because it began before the Sipht_60 original jobs finished/uploaded, correctly refusing incomplete original artifacts. It was later rerun without source search/simulator changes.
- [Verified independent complete four-mode common-reference true-HV audit 41672872206](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41672872206) PASS. Uses a shared normalized 1.5× reference from the FULL set of eight actual solver/mode K16-point samples in each DAG/seed block; additionally checks 3× reference sensitivity. Recomputed from archived CSV rather than comparing each original run's different `sim_hv` reference.

## FLA actual HV (1.5× common reference, normalized)

| DAG | Seed | Original old | Ready only | Dual mean | Dual worst | Worst − old |
|---|---:|---:|---:|---:|---:|---:|
| Sipht_60 | 211 | 0.26221438 | 0.26100357 | 0.26221387 | 0.26221453 | +0.00000014 |
| Sipht_60 | 212 | 0.24555949 | 0.24531524 | 0.24558362 | 0.24539382 | −0.00016567 |
| Montage_100 | 211 | 0.32229665 | 0.32599573 | 0.31438704 | 0.32803559 | +0.00573894 |
| Montage_100 | 212 | 0.31846860 | 0.32249275 | 0.32517415 | 0.32687993 | +0.00841132 |

FLA first-stage mean Δ normalized true HV (1.5×): ready +0.00156704 (2 win,2 loss), dual mean −0.00029511 (2 win,2 loss), dual worst **+0.00349619** (3 win,1 loss; one of 3 wins is only +0.00000014 and practically tied). FLA mean search-time ratios vs old: ready 1.10×; mean 1.84×; worst **1.69×**.

## Seeded NSGA-II summary under identical shared dual decoders
- ready: mean true HV difference −0.00026246; 1 win / 3 loss; mean search ratio 1.00×.
- mean: mean true HV difference +0.00243335; 2 win / 2 loss; search ratio 1.91×.
- worst: mean true HV difference −0.00022685; 2 win / 2 loss; search ratio 1.57×.
- These are **very small and heterogeneous four-block data**, not formal inference and do not prove FLA superiority.

## Scientific decision
1. The worst-case dual-model candidate is worth **prospective cross-DAG falsification** because Montage_100 gains appeared with two seeds, but Sipht_60 remains neutral or negative.
2. The extra factor ~1.69 search runtime matters. A double-model evaluator can have the same **number** of genotype evaluations but different wall-clock costs and twice the internal model computations. Report both; equal evaluation budget alone is NOT fully equal computation budget.
3. The mean alternative failed to reliably improve FLA's true HV and should not be promoted. Do not tune model weights on these two DAGs and then call the same blocks validation.
4. A significant predictor/robustness improvement shared by FLA and NSGA-II is a **decoder innovation**, not an FLA-specific search-operator contribution. A paper will need ablation and genuine algorithm-level gains.
5. The K16 replays sample only a planned-cover subset, not the unknown full simulator Pareto set. True HV is valid for exactly those sampled sets under the shared reference, not a global optimum proof.
6. All modifications are on `fla-baseline`. No `master` changes; `dagfla.dualModelMode` is OFF by default.

**Publication decision: not ready; proceed with a separate frozen cross-DAG validation before choosing any algorithm.**
