# Near-tie and epsilon-Pareto robustness check on frozen 224 actual simulations — frozen 2026-11-04

This is strictly READ-ONLY. It draws its complete candidate universe from immutable source WorkflowSim Actions 41693332570 and independently verified dataset 41693970902, not from any newly optimized candidate or simulator call.

**Scientific question:** earlier added K12 dominated/tied planner candidates yielded 13/96 real nondominated-vs-original-K16 cases, yet extremely tiny mean +0.00000047 normalized actual HV increase. Determine whether these apparent Pareto improvements survive finite relative Makespan/Cost decision tolerances.

Define for an additional candidate x and existing real K16 solution r an explicit *relative weak epsilon cover*: r weakly epsilon-covers x if
  r.makespan <= (1+epsilon) * x.makespan AND
  r.cost <= (1+epsilon) * x.cost.
At epsilon=0 this includes equality as covered (the same as Pareto nondominance against K16, counting duplicates as covered). Let d(x)=min_r max(0, r.makespan/x.makespan-1, r.cost/x.cost-1). The additional candidate is robustly uncovered at epsilon iff d(x)>epsilon, with strict numerical tolerance 1e-12 to avoid float equality. Report all 96 x, including those exactly covered at epsilon=0, and total uncovered at epsilon=0, 0.0001 (=0.01%), 0.001 (=0.1%), and 0.01 (=1%). Display d(x) in percent (100*d), not as absolute normalized HV.
Note: relative weak epsilon cover is a practical robustness diagnostic, NOT a formal stochastic confidence interval, Pareto ε-indicator proof, or test of optimizer superiority. Do not compare this with unequal reference HV or let it choose a new strategy after observing real simulator scores.

Validate exact eight source arms, 16 primary and12 extra unique placements per arm, correct original task/VM and 224 positive finite real objective pairs. Preserve all per-candidate epsilon critical thresholds, no cherry-picking; indicate if raw real ND candidates are only tiny near-ties. Report per-DAG and per-algorithm results; relative cost units unchanged. All original default FLA, NSGA-II, FIFO and master remain untouched.
