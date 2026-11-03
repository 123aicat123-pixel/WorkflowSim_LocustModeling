# Frozen first equal-genotype-budget FLA/NSGA-II priority portfolio feasibility gate — 2026-11-04

## Scientific intent, NOT a publication claim
Previous strictly fixed-VM actual WorkflowSim interventions established that the order of already-ready compute tasks is an actionable second scheduling variable; an opt-in policy-aware DAG/VM decoder accurately predicted substantial harmful UPWARD effects on separate Inspiral_30 and Epigenomics_100 DAX instances, but CyberShake_100 SJF had a sign error. Upward/SJF are established heuristics and priority+VM cooptimization already exists in the literature. This is an **engineering portfolio feasibility / falsification** of search informed by runtime priority, NOT a new FLA v19 method or novel joint priority encoding.

Source code already locked: `ReadyQueueScheduleEvaluator.QueuePolicy`, `FLAFixedVmReadyPriority`, shared opt-in flags in `FLAScheduleEvaluator` and `NSGAIIPlanningAlgorithm`. No future real simulator labels enter the optimization.

## Block and treatment definition (frozen before any new outcome)
- DAX `CyberShake_30`, `Sipht_30`, prior known families but different instance sizes vs the core 36-case priority development experiment.
- Two optimizer RNG seeds **711, 712**; identical input DAX, 16 fixed CloudSim VMs, default MIPS and price profiles in each block. No DAG/VM adaptation based on observed true labels.
- Both methods: `DAG-Pareto-FLA[v12-hvbandit]`, `NSGA-II[costseed]`, running `FLAResearchExperiment` mode `v12-nsga-ready-pair`. Enforced exact seeded mapping parity within each paired invocation.
- Three treatment portfolios, each targeting exactly **3030 counted genotype-objective evaluations per solver and exactly 16 actual K-limited WorkflowSim replay calls**:
  1. `old`: original stage-in-aware insertion decoder; fixed runtime `fifo`, population30 × (generation100+1) = 3030; prospective K=16 Pareto-cover.
  2. `ready`: Task-ID ready-queue decoder, runtime `fifo`, population30 × 101 = 3030; K=16 Pareto-cover.
  3. `priority-portfolio`: three independently optimized, preallocated conditional islands under `-Ddagfla.priorityAwareSearch=true -Ddagfla.useReadyQueueObjective=true` with matching ACTUAL fixed runtime priority in each island. `fifo` = population10 ×101=1010 evaluations and K=6 actual independent true simulator replays; `shortest` = pop10 ×101=1010 and K=5; `upward` = pop10 ×101=1010 and K=5. Exact totals 3030 genotype evaluations and **16** simulator calls per FLA/NSGA-II solver. The same property and model rules apply to both optimizers. Archive each candidate's priority label and Task→VM genotype.
- All first two deterministic cost-seeded maps are identical between FLA and NSGA-II WITHIN each island. The repeated seeds across islands count as a separate genotype+priority compound configuration; they are not extra simulator calls.
- Original baseline has one population of size30; portfolio three independent populations size10. These are **structurally different search algorithms** and evaluation-count parity does NOT imply equal internal decoder calls or equal wall-clock compute; measure sum of actual source `search_ms`, plus selection and replay times, and explicitly discuss the distinction. The portfolio has up to 3× as many seeded starts. Do not claim the policy effect is causally isolated from island/population-size differences.

Four (DAG,seed) blocks × 5 original benchmark jobs = 20 jobs. Four blocks × 3 treatments × 2 solvers × 16 real simulator replays = **384 real WorkflowSim calls** (assuming every job finishes). 24 solver-treatment aggregate K16 sets; exactly 72720 total counted genotype evaluations (4 blocks × 3 treatments × 2 solvers × 3030), with 3 independent sub-islands for each portfolio set.

## Strict evidence analysis
- Inside EACH workflow/seed block calculate the true WorkflowSim 2D normalized HV of each of the six solver-treatment K16 sets against ONE common reference point derived from ALL SIX sets' actual objective points, 1.5× extrema; also 3.0× reference-point sensitivity. No comparison of original per-job `sim_hv` which uses nonshared references.
- Prospective K=6/5/5 frozen Pareto-cover selection within each island, before actual WorkflowSim outcomes; union of 16 actual points by solver, retaining source priority label; no best-of-real K exploitation.
- Record original `_summary.csv`, `_replays.csv`, job logs, SHA, exactly K unique Task→VM maps within island, no simulated label leakage, positive finite Makespan/Cost. Fail closed on incomplete blocks. For portfolio verify exact priorities and 3030 total objective calls; for control verify 3030 and 16. Distinct physical scheduling decisions are (DAX, seed, assignment, priority), not assignment alone.
- Pair portfolio vs old (primary), portfolio vs ready (secondary), FLA vs cost-seeded NSGA-II in every treatment. Report true HV gains/losses including negative, minimum M/C, real Pareto nondominated count, runtime/mode overhead, spread across DAGs. Do not interpret four blocks as independent-family significance.
- No automatic policy/model promotion or change to `master`/default FIFO/FLA. No re-optimization/tuning of outcomes on these four blocks and then rebranding as holdout. This pilot is informative only; a new FLA-specific algorithm with proper priority genotype, critical-path-risk gate and genuinely untouched DAG-family holdout is still required for Q1-level publication.

## Failure criteria and decision
Reject this fixed split portfolio as an algorithm performance improvement if true HV is not consistently better or runtime substantially worse, irrespective of improvements in fixed-genotype predicted Makespan. Even if gains happen on all four cases, do NOT claim generalization or novelty: underpowered known-family developer gate.
