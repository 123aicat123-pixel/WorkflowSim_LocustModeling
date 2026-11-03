# Preregistered synthetic bottleneck DAG40 K16 reliability-gate pilot — 2026-11-03

**Status: actual WorkflowSim experiment complete; exploratory, NOT publication-grade or optimizer-level improvement.**

Source commit: [aeae182b2a33e67b70f4c66a851b2c89164e89ee](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/commit/aeae182b2a33e67b70f4c66a851b2c89164e89ee). Successful independent GitHub Actions matrix plus aggregate report: [41609848454](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41609848454), report artifact `gate-bottleneck-report-41609848454`, ID `13217908309`. CI for reliability-gate code previously passed [41609483183](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41609483183). All changes isolated to `fla-baseline`; default `pareto-cover` remains unchanged.

## Frozen design and verification

- New `SynthBottleneck_40` synthetic fork/join DAG generated from seed 2026110317, unlike previously examined wide/deep examples. It has 40 tasks and two strongly concentrated joins. It is not a real unobserved scientific workflow family.
- Three unseen-for-this-study optimizer seeds 131/132/133 × default/staggered within-tier VM speed = six blocks.
- Three independent algorithms v7-costseed, v12-hvbandit, NSGA-II-costseed × three replay policies `pareto-cover`, `online-observed-hv`, `online-reliability-gated`.
- Exactly 3030 planner evaluations and 16 *actual WorkflowSim simulator replays* per algorithm/policy/block. Across policies the complete optimizer history SHA-256 and first four replay assignments match. The gate reads only previously completed replay labels. Each of six matrix jobs passed, followed by successful aggregate reference/sha/budget/trace checks.
- Predeclared primary HV reference = 1.5× maximum PLANNED pareto-cover objective across all arms/seeds for each speed +1; secondary = 3×. Both were validated to contain every actual simulated outcome, without refitting to actual labels.

## Primary true-simulator HV: mean relative change vs pareto-cover, three paired seeds

| VM speed | Algorithm | Direct observed feedback | Reliability-gated feedback | Gate wins vs cover |
|---|---|---:|---:|---:|
| default | FLA v7 costseed | +0.0052% | +0.0052% | 3/3 |
| default | FLA v12 hvbandit | +0.0105% | +0.0105% | 3/3 |
| default | NSGA-II costseed | +0.0129% | +0.0076% | 2/3 |
| staggered | FLA v7 costseed | +0.0465% | +0.0211% | 2/3 |
| staggered | FLA v12 hvbandit | +0.0174% | +0.0174% | 3/3 |
| staggered | NSGA-II costseed | +0.0983% | +0.0684% | 2/3 |

FLA v12 produces identical actual HV for the two online strategies in every new bottleneck case. No incremental value of the reliability gate itself is demonstrated for v12.

**Negative cases, explicitly retained:** staggered NSGA-II seed 131: gated vs cover −0.0031%, direct observed vs cover +0.0868%; staggered FLA v7 seed 133: gated vs cover +0.0000%, direct observed vs cover +0.0764%; default NSGA-II seed 131: gated +0.0000%, direct observed +0.0159%. Thus the gate can discard useful feedback. This is a *false-negative gate* risk, and threshold tuning on these cases would destroy prospective independence.

At 3× reference, most gains shrink by an order of magnitude. The primary reference results must remain primary; favorable secondary values are not a reason to rewrite conclusions.

## Research conclusion and required next gate

1. Keep `pareto-cover` default. Leave `online-reliability-gated` experimental opt-in.
2. **No claim** of FLA v12 superiority over NSGA-II, nor that the gate improves over `online-observed-hv` in general.
3. Investigate gate false negatives **without reusing these reported runs as held-out validation**. First inspect policy trace counts (gated-cover vs gated-observed), error distribution, and actual marginal HV of fallback decisions. These are diagnostics, not independent validation.
4. Before further optimization changes, identify real new scientific DAG families and larger disjoint cohorts/VM profiles. Pre-register one mechanism, comparator and primary scoring reference, then use new labels once.
5. This is replay-budget selection *after* optimization, not modification of the FLA generation operators. For a cloud scheduling paper claiming an improved metaheuristic, conduct separate search-operator ablations under equal wall-clock/evaluation constraints.

Artifacts retain individual per-seed objective and outcome CSVs, full replay mapping lists, source SHA, and complete negative cases. The 18 algorithm/speed/seed comparisons are correlated across algorithms, topologies and scores; do not interpret them as 18 independent workflow-family replications.
