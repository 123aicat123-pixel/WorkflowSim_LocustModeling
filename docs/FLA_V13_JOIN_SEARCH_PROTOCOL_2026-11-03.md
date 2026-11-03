# v13 DAG fan-in join locality — frozen exploratory search-operator experiment

Status: New, experimental, off by default. This changes an **optimizer offspring operator**, unlike previous K16 post-search replay selectors. It is NOT an equation-faithful original FLA mechanism.

The FLA v12 DO/EO/SSO UCB controller has three arms: base FLA, DAG edge co-location, and cheap critical-task relocation. In v13 only arm three is replaced with a bounded DAG high-incoming-transfer join locality operation (up to two VM assignments, on a fan-in task and optionally a parent). All existing operator choice, UCB and planned-archive HV reward are unchanged. The proposal uses static DAG/VM metadata and the current child's assignment. It performs **zero** evaluator calls. Every child consumes **exactly one** stage-in-aware optimizer objective call, equal to v12 and equally cost-seeded NSGA-II.

The new proposal is not guaranteed to improve actual scheduling time or rental cost. The purpose is to test whether DAG fan-in targeting improves simulated Pareto coverage more reliably than the old critical-path proxy; keep all losses.

Primary exploratory evaluation protocol: CyberShake_50, Montage_50, Sipht_60, seeds 141,142,143, baseline and staggered VM-speed profiles, three solvers (v12, v13, NSGA-II costseed), exactly pop30 × gen100 => 3030 shared objective evaluations per arm, and 16 actual simulator candidate replays using unchanged planned Pareto-cover policy. All three use exactly the same first two cost-seed assignments; references fixed from PLANNED pareto-cover candidates at 1.5×max+1 separately per workflow/speed across all algorithms/seeds. 3×max+1 sensitivity. Do NOT rescue a reference failing to cover real outcomes; fail and report. No primary outcome may be selected after observing results.

Given these three families were previously explored, these tests are DEVELOPMENT, not publishable untouched holdout. Do not auto-promote v13 if positive: genuine new DAG family/VM profiles and more independent seeds are required. No publication claim until comparison on actual simulator traces with family-level uncertainty, runtime, and external dataset.
