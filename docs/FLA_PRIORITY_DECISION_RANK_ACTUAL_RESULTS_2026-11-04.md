# Priority-policy decision rank and regret: original simulator archive, complete read-only results (2026-11-04)

**Verdict: The predictor correctly ordered all eight MATERIAL policy pairs in the selected new-instance cohort, but it simply selected FIFO in every 3-policy decision. Its near-zero decision regret is exactly the same as the FIFO no-optimization control. Thus this is NOT evidence that model-guided priority selection improves upon FIFO or that adding task priority to FLA is valuable.**

## Original source and independent execution
- Frozen before this analysis in `docs/FLA_PRIORITY_DECISION_RANK_FROZEN_PROTOCOL_2026-11-04.md` at commit `0500fba`.
- Immutable original exact 24 real WorkflowSim outcomes from [Actions 41682109356](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41682109356): 2 DAX instances (`Inspiral_30`, `Epigenomics_100`) × 2 VM regimes × 2 exact predetermined placements × 3 runtime policies, all previously archived. Source was reused without changing Task→VM maps, runtime or search.
- Independent read-only decision-rank audit [Actions 41767278601](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41767278601) **PASS**. Cross-checked original per-policy actual and predicted raw CSV, complete source labels and case count, reconstructing forecast choice before actual outcome. Outputs include 24 original simulator/model points, 24 policy pairwise comparisons, and 8 actual decision-regret blocks. No new simulator or optimizer calls.
- Decision algorithm fixed before reading outcomes: min predicted Makespan over FIFO/SJF/UPWARD; near-ties at relative 1e-9 resolved FIFO first, SJF second, UPWARD third. Ex post best *actual* policy appears ONLY in the evaluation denominator; no oracle feedback to selection.

## Result: meaningful sign matching, but NO improvement over FIFO
- Among all 24 distinct within-placement policy comparisons, 8 have **>0.1% actual Makespan separation**; predictor chose the correct ordering sign on **8/8 material comparisons**. The remaining 16 pairs have small true effects and are not counted as useful classification successes or mistakes.
- Predicted winner in each one of the **8 fixed (DAX, VM profile, placement) blocks was FIFO** (8/8), so it never proposed SJF or UPWARD.
- Measured prediction-only policy-choice actual regret relative to the best observed policy: mean **0.000001%**, median **0%**, worst **0.000006%**; no case with >0.1% regret.
- Crucially, **the independent always-FIFO control has exactly the same mean, median, worst regret and true workflow outcomes** in these eight cases. Therefore the predictor has *zero demonstrated marginal benefit* for policy choice on this cohort.
- This is partly a constrained test: significant priority effects in the selected Epigenomics runs were all **harmful UPWARD** effects; avoiding harmful interventions only recovers FIFO. Inspiral priority effects were all negligible. The set does not contain a meaningful beneficial non-FIFO case to measure whether the model can act to improve real makespan.
- The old CyberShake_100 fixed round-robin SJF case was a **KNOWN significant opposite-sign error**, actual +0.236779% worse vs predicted −0.019895% better; it was not a member of these eight new-instance decision blocks and must remain a negative counterexample in the final model validity report.

## Publication / next decision
1. Predictor success at detecting harmful UPWARD interventions (Epigenomics +6.86–8.67%) is scientifically useful for fidelity, but the eight-policy-block rank score is not a validation of improved optimization or FLA v20.
2. An efficient next discriminative gate should fix a new, optimizer-independent set with REAL candidate diversity, ensuring costs and placement remain part of the decision; record model-based Pareto dominance and rank errors on the same physical input genotypes. **Do not select test cases by observed positive intervention outcome**.
3. Importantly, a previous algorithm-independent 96 fixed Task→VM mapping source study was already completed: [Actions 41695748829](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41695748829), comparing two placement predictors on the same mapping points. That measures *mapping* fidelity, not priority-policy decision regret. Do not rerun the same 96 cases as if new science.
4. The available evidence supports a model-fidelity engineering research artifact and a negative result for priority-portfolio algorithms, but **does not demonstrate stable FLA-specific Pareto HV gains or publication readiness**.
5. Retain all original FLA v12, seeded NSGA-II, FIFO defaults, `fla-baseline` opt-in priority flags, original raw data, full negative controls and immutable GitHub Actions provenance. No changes to `master`.

**Do not automatically promote the priority-aware policy selector into FLA search.**
