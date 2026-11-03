# FLA cloud-workflow paper research decision register — 2026-11-04

**Status: publication-grade experimental hygiene in progress; a publication-grade superior algorithm is NOT demonstrated.** Do not cite these development runs as independent proof of an SCI-Q1 optimization advantage.

## What is validated now
1. Compilable, instrumented WorkflowSim Java baseline with fixed assignment identity and correct original Task-ID joins. Historical fixed-insertion counterexample gave 95 s, with previous impossible 65 s corrected. Stage-in-aware model and default source objective parity checked across true simulator replays.
2. The planning model's same-VM task *ordering* can disagree strongly with runtime, but dependency precedence is preserved; 1,176 time traces across two DAGs, and independently audited readiness/dispatch events. The 9,120 inversion count includes multiple correlated task pairs and duplicate physical mappings, NOT 9,120 statistical replicates.
3. A separate deterministic ReadyQueueScheduleEvaluator accurately predicts fixed mappings on some cases (14 deduplicated development physical mapping/profile cases: 4.141608% vs 1.179256% mean absolute makespan percent error) but fails in other DAG/VM regimes. This is a model fidelity result, not necessarily an improved search method.
4. A fair 3030-genotype-evaluation/K16-real-replay interface for FLA and cost-seeded NSGA-II exists, together with reference-point-aligned normalized true HV independent verification.
5. Counterexamples to naive search replacement are VALID and archived:
   - shared ready-only estimator: FLA 2 wins / 2 losses in two-DAG original fair search;
   - dual-worst model: 3/1 initial development (one negligible win), followed by 2/2 new-instance split and **−0.00089298** mean normalized true FLA HV change;
   - v18 FLA-specific disagreement-targeted relocation: 2/2, **+0.00213753** mean across four known DAG/seed blocks, but distinct signs by DAG and ~1.50× search runtime. All failures have full simulator log provenance.
6. All experimental variants remain OFF by default, baseline FLA v12 and seeded NSGA-II unchanged; `master` never mutated.

## Paper research question worth pursuing
For multiobjective cloud DAG scheduling, **when and how does incorrect event/VM readiness ranking mislead a fixed-evaluation-budget metaheuristic?** A stronger contribution must explain how to distinguish consequential rank errors along the true critical path or Pareto tradeoff from innocuous independent-task order disagreement.

Do not submit a simple FLA+decoder-swap paper claiming robust improvement; existing falsification contradicts it.

## Next *pre-registered* research gate, before implementation
- Formulate a deterministic **critical-consequence score** for a planned task: (i) predicted latest/earliest slack of its DAG path, (ii) disagreement of the two VM start rank predictors, (iii) estimated marginal cost and VM load before/after relocation. A task with high rank discrepancy but large safe slack should be downweighted; a task on a low-slack DAG join should be prioritized. This is a HYPOTHESIS, not tested evidence.
- Use a **sham control** that makes the same number of single-gene changes at random eligible tasks and has the same auxiliary model-computation budget, in addition to FLA v12 and seeded NSGA-II. Without the sham, cannot attribute value to targeted selection rather than extra search perturbation.
- Preserve EXACT 3030 target evaluations per solver, account separately for two auxiliary surrogate passes and report wall-clock/CPU compute cost. Also run an equal-wall-time-budget comparison, not only equal candidate-budget.
- Split DAG sizes/families and seeds **before learning/tuning**. Do not use Montage/CyberShake/Sipht/Epigenomics/Inspiral development outcomes as independent holdout merely because the instance size differs.
- Minimum future design: at least 4 different DAG families with at least 3 task sizes, 20+ independent random seeds per family/scenario, at least two heterogeneous VM speed regimes, multiple static-cost regimes if cost fidelity is discussed. These are recommended quality targets, not claim that trials have been done.
- Common-reference actual HV and IGD+ (with documented reference approximation), separate predicted and true Pareto ND counts, extreme Makespan and Cost, ranking correlation, ablation, time/eval budgets, worst-case losses, confidence intervals clustered by DAG scenario. Avoid pseudoreplication of task pairs or K16 candidates.
- Confirm original FLA algorithm's published formula/source fidelity before claiming \"improved FLA\" instead of an FLA-inspired method. Cite true original literature sources and distinguish new operator from baseline.

## Go/no-go decision
- **GO**: new critical-consequence operator beats both frozen FLA v12 and compute-budget-matched random sham in prospective true HV across multiple DAG families/seeds, without unacceptable runtime, while being competitive with seeded NSGA-II.
- **NO-GO**: repeated 2-win/2-loss pattern, solver advantage absent after reference parity, high slowdowns, success only on tuned DAGs, or effects smaller than family/seed uncertainty.
- Until the GO criterion, report engineering and model fidelity research, not an established SCI-Q1 optimization contribution.

## Complete reproducibility trail
- Full fixed mapping speed study: `docs/FLA_FIXED_MAPPING_VM_SPEED_PILOT_RESULTS_2026-11-03.md`
- Task order and DAG ancestry mechanism: `docs/FLA_FIXED_TASK_ORDER_MECHANISM_RESULTS_2026-11-03.md`
- Real Engine/Datacenter event and parent-release waiting study: `docs/FLA_EVENT_CHAIN_RELEASE_WAIT_RESULTS_2026-11-03.md`
- Ready queue model and initial fair true HV: `docs/FLA_READY_QUEUE_DECODER_VALIDATED_RESULTS_2026-11-03.md`
- Dual-model exploratory and next-instance adversarial outcome: `docs/FLA_DUAL_DECODER_FIRST_GATE_ACTUAL_RESULTS_2026-11-04.md`, `docs/FLA_DUAL_WORST_NEXT_INSTANCE_ACTUAL_RESULTS_2026-11-04.md`
- FLA v18-specific search experiment: `docs/FLA_V18_DISAGREEMENT_OPERATOR_ACTUAL_RESULTS_2026-11-04.md`

**Conclusion: development stage is operational and richly falsified; the next publishable contribution must satisfy truly prospective, budget-fair and DAG-generalizing evidence before manuscript claims are strengthened.**
