# Follow-up dispatch-opportunity mechanism audit (exploratory, frozen before diagnostic replays; 2026-11-04)

**Not a prospective unseen efficacy test.** Four cases below were chosen explicitly from the observed true WorkflowSim effects in pilot Actions 41679712071 and are used **only** to understand why the runtime ready-job policies affected true makespan. Do not evaluate any tuned priority on these cases as unseen validation.

## Frozen cases
- Sipht_60 + stride7 (upward made actual makespan +10.650698% worse than FIFO).
- Sipht_60 + round_robin (upward made actual makespan −1.364562% better).
- CyberShake_100 + round_robin (shortest made actual makespan +0.236779% worse).
- Montage_100 + stride7 (priority mode effects ~0).
- Each case receives FIFO, shortest, upward under the exact same frozen Task->VM assignment, same simulation seed 509, VM speed default and data.
- Total 4 selected pairs × 3 priority modes = 12 new real simulator replays. No optimizer search.
- Passive `-Ddagfla.priorityOpportunityTrace=true` reports only STATIC dispatch invocations at which an **IDLE VM has two or more unclustered COMPUTE jobs** already released by the engine, plus FIFO first, priority-policy first, and whether the selected COMPUTE task changes. No queue mutation besides already tested priority policy, no extra simulated events, no random draws.
- Existing `FLAReadyQueueCrossDagAudit` is extended with an optional third argument that runs ONE of four previously registered deterministic mapping policies, with the legacy two-argument four-mapping behavior unchanged.

## Must-pass integrity
- All 12 trace-mode Makespan and Cost outputs match their pre-existing nontrace pilot records from Actions 41679712071 within 1e-6 relative precision. This is crucial: traces must be observational only.
- Original Task ID/VM identity and per-task actual coverage validated by the unchanged harness.
- Only task-id original COMPUTE jobs compete at idle VMs. Stage-in job slots and VM mapping remain untouched; no child released before original parent finishes.
- Preserve raw `PRIORITY_OPPORTUNITY` CSV, source SHA, all simulation logs, count of eligible competition events, count of truly changed first choices, and true actual makespan changes.

## Interpretation
If no *changed idle-VM first choice* occurs for a case, a measured true Makespan difference cannot be attributed to the sort choice without inspecting other simulator effects or numeric noise. If changed first choices occur, this proves the intervention was active but not that it is beneficial; effects may propagate differently across DAG branches.
- This diagnostic is intentionally selected after knowing outcomes. It cannot justify publication-level effect sizes, FLA advantage, or generalization.
- Priority optimization without a priority-aware estimator is scientifically unjustified, and existing priority-rule learning literature limits novelty claims. Do NOT replace the baseline; `master` is unchanged.
