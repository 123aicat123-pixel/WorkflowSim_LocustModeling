# v16 bandit-opportunity sham-pair negative controls — predeclared development experiment, 2026-11-03

The previous v14/v15 experiments discovered that replacing 14 of 30 normal offspring evaluations with local pair evaluations reduces phase-bandit eligible normal offspring from 30 to 16 each generation, yet keeps the same 30 total *counted* planning fitness evaluations. This v16 experiment is **only a negative-control mechanism test**, NOT a promoted algorithm.

Two new opt-in modes: `v16-shamrandom` and `v16-shamtimeline`. Each produces exactly the same kind of eligible proposal and consumes the corresponding random- or timeline-neighbor proposal RNG path as the active v14 comparator. Each performs normal novelty-repair proposal path, then DISCARDs the neighbor and evaluates a copy of the already evaluated normal child. That second evaluation is counted and recorded, and the child's identical objective vector is checked. This deliberately yields no new search information, while preserving the per-generation split of 16 FLA normal evaluations + 14 paired evaluations, with the exact same 3030 evaluation total as v12. Sham variants do **not** use a hidden shortcut, and this "wasted probe" should never be presented as a competitive real scheduling method.

Frozen six arms: v12 FLA (30 normal evals/gen); v16 shamrandom; v14 randompair; v16 shamtimeline; v14 timelinepair; cost-seeded NSGA-II. All solvers have the same 3030 planned evaluation budget, the same first two deterministic seeded task assignments, and 16 real WorkflowSim replays of unique chosen assignments under unchanged pareto-cover. All five FLA arms enable passive per-generation diagnostic tracing previously demonstrated ON/OFF-neutral.

Comparisons:
- v12 vs sham variants estimates the **combined opportunity-loss + duplicate/wasted evaluation** effect; it cannot strictly isolate bandit credit from generic search breadth.
- active v14 random vs shamrandom and v14 timeline vs shamtimeline estimates the added information from the respective neighborhood under a fixed opportunity split. Downstream trajectories diverge after selection and should not be described as identical normal-offspring histories.
- random-vs-timeline active search provides guidance control.
- all arms vs cost-seeded NSGA-II is a common external benchmark, not a proof of FLA source-equation fidelity.

Primary development pilot: Montage_25, CyberShake_30, VM speeds default/staggered, fresh seeds 181/182 (8 blocks), population=30, generations=100, 3030 counted planning evaluations, 16 real WorkflowSim simulations, fixed primary shared reference from 1.5× coordinatewise largest PLANNED replayed makespan and cost across all arms and seeds within each DAG/VM regime +1, 3× secondary. Do not use simulator labels to choose references. Exact source hash, phase-bandit uses, 101 selected-population traces, 1400 paired trials per sham/active, and every negative outcome must be retained. Familiar DAG families and tiny seed N mean this is NOT untouched publication validation.

Prior experiment evidence: Actions 41621527587 and 41621825653. No existing default changes; `master` unchanged.
