> **Superseded evidence notice, 2026-11-03:** This protocol was written without first noticing that the repository had ALREADY completed this precise selected-population diagnosis. The existing implementation is `sources/org/workflowsim/planning/FLAPopulationDiagnostics.java`; the existing results are `docs/FLA_POPULATION_PHASE_MECHANISM_RESULTS_2026-11-03.md`. Original 8-block Actions run 41621527587 and exact follow-up 41621825653 measured 4,040 selected-population snapshots (8 blocks × five FLA variants × 101 generations), and **every snapshot contained 30 distinct selected genotypes**. Hence the population-duplication hypothesis in this document is **falsified on that cohort**, not an outstanding unmeasured mechanism. No duplicate implementation or v16 optimizer work should be performed on the basis of this stale protocol. v17 prospective synthetic tests also failed to establish stable superiority; see `docs/FLA_V17_DAG_STRUCTURE_SYNTHETIC_FIDELITY_RESULTS_2026-11-03.md`. The next independent question is matched-genotype planner-vs-simulator fidelity and whether a PREDECLARED selection correction improves true HV on genuinely unseen samples.\n\n# FLA population-level diversity diagnostic — preregistered protocol (2026-11-03)

## Decision and scope
This document defines the next **diagnostic study**, not v16 performance claims. As of this document, v15 is NOT a demonstrated improvement over v12 or equally cost-seeded NSGA-II. The original v15 paired eight-block study and its negative results remain immutable in `docs/FLA_V15_PARETO_GATED_LOCAL_RESULTS_2026-11-03.md`.

Do not alter `master`. Do not change the default solver or optimize v16 thresholds on previously observed workloads. The first implementation change should be **read-only generation-level tracing** on `fla-baseline`; no new fitness calls, different pseudorandom draws, archive admission changes, survivor changes, or changed seed handling.

## Hypothesis under test
H1: v15 post-evaluation strict planned-Pareto survivor gating duplicates offspring used in the **selected breeding population** and thereby reduces genotype diversity in some generations, potentially reducing final simulator HV. This mechanism was not measured by the earlier distinct-*evaluated*-assignment counter. H1 is not assumed true.

Null: v15 gated and matched ungated variants exhibit no consistent decrease in selected population genotype diversity; HV differences must have other explanations.

## Required trace schema (one row per generation, arm, workflow, regime, seed)
- `experiment_id,workflow,vm_regime,seed,arm,generation,population_size`.
- `selected_unique_assignments`: distinct canonical task-index-to-VM-index vectors among actual selected parents/survivors that breed next generation.
- `selected_unique_fraction = selected_unique_assignments/population_size`; count duplicate individuals, not merely repeated objective pairs.
- `selected_entropy`: Shannon entropy of canonical assignment genotype frequencies in the selected population; zero when all genotypes identical.
- `selected_pairwise_hamming`: mean normalized assignment Hamming distance over all unordered distinct individual pairs (0 for identical vectors).
- `local_trials_evaluated,local_trials_dominated,offspring_duplicate_count`: incremental per-generation counters, not cumulative totals.
- `evaluations_so_far,archive_nondominated_count,planned_archive_hv`: planning-only metrics with an **unchanged predeclared** reference point; never label as actual simulator HV.
- `rng_state_checksum_before,rng_state_checksum_after` if available by a non-mutating method; do **not** consume the RNG to calculate these fields.

Canonical genotype must use the same task order and VM index mapping for all algorithms and variants. For each generation define **precisely** whether selection occurs before or after elitism/replacement; collect only the population that supplies the next generation's breeding events. Explicitly record the initial population (generation 0) separately. If population sizes vary, report counts and fractions.

## Determinism and isolation checks (required BEFORE scientific interpretation)
1. Run instrumented and uninstrumented variants with the same instance/seed. Verify exact equality of counted evaluation budget, final planned objective tuples, chosen VM mappings, and all simulated K16 objective tuples, including ordering where deterministic.
2. Verify trace has `generation 0` and a row for every breedable generation, with valid diversity bounds (unique count in [1,N], Hamming in [0,1], entropy in [0, ln(N)]).
3. Compare gated v15 timeline against ungated v14 timeline and gated random v15 against ungated random v14 **within each matched workload/regime/seed**. Also report v12 and seeded NSGA-II as context, but do not equate their different operators.
4. Keep original planning budget 3030 and independent true WorkflowSim K16 replay unchanged. Preserve the original 1.5× and 3× reference policies, computed before seeing simulation outcomes.
5. CI success alone is not an algorithm-correctness or reproducibility guarantee: archive source commit IDs, job IDs, inputs, simulator CSVs, complete trace CSVs, and aggregate script.

## Analysis (no post hoc change of primary criterion)
- Primary mechanism metric: `delta_unique_fraction = mean_generation(v15) - mean_generation(v14)` within the paired block, with per-block values and pooled descriptive mean.
- Secondary: entropy and normalized Hamming diversity; duplicate-slot rate. Summarize first/middle/last third of generations and diversity-versus-evaluation curves.
- Plot paired end-of-run true simulated HV differences against paired diversity differences, but correlation is **not** causal proof.
- Include every development block, failures and zero/negative improvements; report counts and intervals. Because the eight blocks come from two familiar DAG families, do not present them as cross-family generalization or use isolated positive cases to justify tuning.
- Alternative mechanisms to examine if H1 is unsupported: planned-versus-simulated local dominance reversals, archive admission behavior, task timing/caching differences, operator-phase interactions, and CPU-time fairness.

## Publication holdout gate
Only after instrumentation, fixed code, fixed budget, and fixed analysis scripts pass regression, predeclare unseen DAG families, instances and seeds **before executing** the holdout; use multiple independent seeds and baseline parity in initialization/evaluation budget/VM model. Report true simulator HV and IGD+ (reference front declared transparently), runtime, Wilcoxon paired comparisons with multiple-testing correction, effect sizes and failures. No claim of superiority or journal readiness unless supported by independent holdout data.

## Existing evidence
- Original v15 six-arm run: https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41618003870
- Read-only evaluated-candidate audit: https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41618415780
- v15 decision/report: `docs/FLA_V15_PARETO_GATED_LOCAL_RESULTS_2026-11-03.md`

**Status:** protocol documented; generation-level instrumented code, CI, and new measurements are **not yet executed** by this document.
