# Fixed-VM runtime-priority policy ranks: actual Pareto classification and epsilon sensitivity (2026-11-04)

**Result: the opt-in priority-aware decoder predicts meaningful signed Makespan effects on some known instances, but its exact 2-objective Pareto dominance classifications are NOT sufficiently reliable to justify automatic optimizer promotion. Model-selected 3-policy front actual HV is nearly equal to the full 3-policy universe, but in most cases FIFO alone achieves almost the same HV. No robust new FLA search algorithm is established.**

## Original immutable true WorkflowSim evidence and reproducibility
- Protocol frozen first: `docs/FLA_PRIORITY_PARETO_POLICY_RANK_FROZEN_2026-11-04.md`.
- 36 REAL original simulator runs [Actions 41681448520](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41681448520): `CyberShake_100`, `Montage_100`, `Sipht_60` × 4 exact unoptimized Task→VM allocations × FIFO/SJF/UPWARD policies. Both predicted `policy_model_makespan/cost` and actual `actual_makespan/cost` were archived from the same original runs; these DAXs are familiar development workflows, NOT untouched research-family data.
- [Initial independent full classification 41767594023](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41767594023) PASS; [same original data with explicit 0.01%/0.1% materiality analysis 41767701274](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41767701274) PASS; no new simulator, optimization or estimator tuning. All original Task IDs and VM allocation validation were enforced in source replay.
- For each fixed assignment only THREE possible runtime-policy candidates were compared. Predicted nondominated policies were selected using strictly pre-existing plan Makespan and Cost, and evaluated by true simulator values **only afterward**. Within-block 1.5×/3× normalized actual HV use one reference derived from all three actual points (three-policy universe only).

## Exact and practical error accounting
- Across 12 fixed-assignment groups, 36 policy-pair exact Pareto dominance comparisons, **20/36** planner-vs-simulator class disagreements (often microscopic numerical differences). Mean predicted ND vs real ND set Jaccard **0.666667**.
- Only **8/36** pairs had at least one actual objective different by more than **0.01%**; **3/8** of these had exact dominance classification mismatches.
- Only **6/36** pairs had at least one actual objective different by more than **0.1%**; **3/6** of these had exact dominance classification mismatches. These three include:
  1. `CyberShake_100 round_robin FIFO/SJF`: planner incorrectly expected SJF to dominate FIFO; true Makespan SJF **+0.236779% worse**, Cost difference **0.000011%**, real policies incomparable.
  2. `Sipht_60 stride7 FIFO/UPWARD`: predicted FIFO dominates upward; true upward Makespan **+10.650698% worse**, but real Cost **0.001718% lower**, so two real policies incomparable under *exact* Pareto definition.
  3. `Sipht_60 stride7 SJF/UPWARD`: predicted SJF dominates upward; true upward Makespan **+10.650746% worse** but real Cost **0.001412% lower**, so real policies incomparable. These last two exact-class errors do not imply the Makespan predictor mis-signed the large degradation—indeed the priority-aware model correctly forecast it; they arise from tiny Cost shifts that matter in strict Pareto logic.
- The classification error count therefore **must not** be described as 20 practically serious ranking mistakes, nor as three 10%-scale directional mistakes. Both exact Pareto definitions and epsilon materiality must be reported honestly.

## Real HV of predicted policy front vs FIFO-only control
- Across 12 fixed Task→VM groups, mean actual 1.5× normalized HV fraction of all three actually observed policies captured by **model-selected predicted nondominated policy set**: **0.999993**.
- Mean fraction captured by **always FIFO alone**: **0.997683**. The difference is mostly from one or few cases, not an established general gain; model-selected actual HV is higher than FIFO in **5/12**, tied **6/12**, and lower **1/12**.
- `Sipht_60 round_robin` is one illustrative successful policy-case: model-selected upward priority achieves actual full three-policy HV, FIFO-only achieves 0.973424 fraction; `Montage_100 stride7` is one adverse case: forecast selection achieves 0.999945 fraction while FIFO achieves 0.999986.
- This is a three-policy *fixed VM genotype* comparison, not the complete mapping+priority scheduling Pareto front, so values near 1 do NOT mean the solver has discovered globally near-optimal scheduling.

## Relation to separately verified rank result
- [Source Actions 41767278601](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41767278601): in 8 new DAX instance/VM speed/placement blocks, predictor's scalar Makespan ranking got 8/8 >0.1% material pairs right, **but chose FIFO in all 8**; its regret was identical to FIFO baseline. This demonstrates why high sign accuracy or low Makespan MAPE alone does NOT establish useful adaptive priority decisions.
- Previous equal counted target-evaluator studies: [matched restart and full SJF/UPWARD study 41689570828](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41689570828) and [FLA v19 real HV audit 41691646807](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41691646807) found no stable FLA-specific true HV improvement.

## Decision
1. Do NOT promote SJF/UPWARD, an unconditional policy selector, dual-model worst decoder, fixed priority islands or FLA v19. The decision input must be consistent in Task→VM mapping, runtime priority, and BOTH Makespan and Cost, with practical Pareto-margin robustness.
2. A legitimate future algorithm study needs a truly common (priority, VM) chromosome/search budget across FLA and NSGA-II, a Pareto-margin-aware model-rank fidelity gate on independent candidates, real K16+ true HV and independent DAG-family evaluation. However, published 2024 coevolutionary rule learners already optimize task and VM decisions jointly; simply representing the priority decision is NOT novel.
3. Current completed evidence is sufficient to frame a nuanced, reproducible **simulator/planner fidelity and selection-bias research study**. It is NOT evidence of a strong novel SCI Q1-ready FLA optimizer.
4. Keep `master` and original runtime FIFO/FLA/NSGA-II settings untouched; all code/data on research `fla-baseline`, with raw positive and negative cases retained.

**No user action required; never equate source CI PASS with algorithm superiority.**
