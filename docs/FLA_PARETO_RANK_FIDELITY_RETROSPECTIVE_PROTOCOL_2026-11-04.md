# Retrospective Pareto decision-rank fidelity audit of existing true WorkflowSim K-limited replays — 2026-11-04

**A read-only methodological investigation, NOT a prospective holdout or a new optimization claim.** All simulator labels and several aggregate HV outcomes exist before this script is written; this is explicitly an exploratory consistency audit, not new data. It must not be used to tune a new model and then call the same records prospective validation.

## Frozen sources and completeness
- Original [FLA priority/restart 40-job actual simulator Actions 41689142588](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41689142588): two known DAX `Inspiral_50`, `Epigenomics_46`, seeds 821/822, staggered VM configuration. Every source variant includes both cost-seeded FLA-v12 and NSGA-II, total **768 actual WorkflowSim K16/6/5 replay calls**; deliberate 48 mirrored FIFO source candidates across treatments.
- Original [v19/v18/v12/seeded NSGA-II actual simulator Actions 41690669415](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41690669415): two known DAX `Inspiral_100`, `Sipht_100`, seeds 901/902, all 4 arms pop30/K16, **256 actual simulator calls**.
- Total exactly **44 original source jobs, 96 optimizer arms and 1024 actual simulator replay rows**, including deliberate duplicates. All archived CSVs include `planned_makespan`, `planned_cost` (the model used for source optimization), `independent_planned_makespan`, `independent_planned_cost` (read-only fixed-mapping stagein replay), `sim_makespan`, `sim_cost`, exact original Task ID to VM mapping. Fail closed on missing archive or malformed source.
- No new optimizer runs, no additional simulator calls, no new source parameter tuning.

## Predefined decision-fidelity statistics
For the **K actually selected and simulated candidates of EACH original solver source arm**, independently:
1. Mean absolute percent prediction error of makespan and cost (relative to simulator truth).
2. For every unordered candidate pair, compare predicted Makespan order to real Makespan order with tie tolerance `1e-8 × max(1,|a|,|b|)`; count concordant, discordant, and tied pairs; analogous for Cost. Do not treat 16 choose 2 overlapping within-arm pairs as independent samples.
3. Pareto dominant pair sign under exact componentwise objectives (`a` dominates `b` only if no worse in both and strictly better in one). Count how many predicted dominance classifications differ from actual within K (loss of a predicted dominance, newly observed dominance, and direct reversal). Report predicted-vs-actual nondominated subset overlap, Jaccard, precision/recall for the **selected K only**.
4. Decision reversal of the predicted fastest candidate vs true fastest among same selected K, and corresponding actual Makespan regret, as a diagnostic **offline-only oracle upper bound**, never an optimizer decision or a "future proof" claim.
5. For historical `independent_planned_...`, report magnitude of separation from searched objective `planned_...` as a *model disagreement*, not a ground-truth label.
6. Aggregate by group, solver and workflow family; report mixed/negative cases. Keep raw per-arm results and pair-level mismatches, including duplicate candidate identifiers. Check complete original row counts.

## Interpretation
A near-zero mean absolute Makespan error may coexist with wrong candidate ordering or erroneous Pareto dominance, especially near ties. Conversely, a modest absolute bias need not imply misranking. Since source K candidates are selected by planned objectives, ranking results **cannot** be extrapolated to unselected optimizer population or the entire true search space. Large differences between algorithms or DAGs may be selection effects, not causal model quality. The audit can identify whether improved ranking fidelity warrants a future separate preregistered model/FLA strategy test; it cannot prove that a heuristic is novel or a paper is ready. All existing source code defaults and `master` remain untouched.
