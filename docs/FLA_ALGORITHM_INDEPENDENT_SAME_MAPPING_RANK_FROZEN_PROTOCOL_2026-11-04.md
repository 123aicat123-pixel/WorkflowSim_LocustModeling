# Algorithm-independent fixed-VM mapping universe: preregistered same-genotype real simulator ranking gate (2026-11-04)

## Why this study is necessary
Earlier true Pareto rank fidelity audits on 1024 selected source replays mixed **different optimizer-selected genotype distributions**, and retrospective planned K16 vs extra planned-dominated/tied study found only tiny extra HV gains. A new FLA mutation cannot credibly be justified until the intended objective function can rank **exactly the same** candidate mappings without K16 planned-front selection bias.

## Frozen independently generated VM assignment universe
- No FLA or NSGA-II optimizing or seeding selects the candidate genotype. Fixed original Task IDs 1..N map to one of 16 original WorkflowSim VMs by these **16 completely deterministic policies**, frozen before any simulator labels:
  1. `all_vm0`
  2. `all_vm12`
  3. `round_robin`
  4. `stride7` (original historical formulas)
  5. `evenodd_vm0_vm12`
  6. `block4_vm0_vm12`
  7. `four_vm_round` (0,4,8,12)
  8. `four_vm_block5` (0,4,8,12)
  9. `vm0_vm12_skew75`
  10. `vm12_vm15_skew75`
  11. `prime_step5`: VM ID=(5*(TaskID−1)+1) mod16
  12. `prime_step11`: (11*(TaskID−1)+7) mod16
  13. `hash_seed17` deterministic xorshift-style integer hash TaskID+17
  14. `hash_seed97` deterministic integer hash TaskID+97
  15. `monotonic_vm16`: VM index floor(16*(TaskID−1)/N) clipped15
  16. `reverse_monotonic_vm16`: 15−floor(16*(TaskID−1)/N)
- All 16 physical mapping strings must be **distinct per DAG** (fail rather than silently drop duplicate cases). No future real CloudSim label, global optimization, current decoded HV result, or algorithm-specific archive affects mapping policy.
- DAX `CyberShake_30`, `Epigenomics_46`, `Montage_50` (historically seen families; these are NOT an untouched family-level holdout). VM speed profiles `default` and `staggered`, fixed original VM prices and bandwidth. Simulator seed 1501, static FIFO runtime for every candidate. 3 DAG instances × 2 VM speed profiles × 16 frozen VM mappings = **96 truly independent simulator *replays***, but **only 3 DAX families and 6 DAG/speed blocks**, NOT 96 independent workflow families.
- For every original Task ID exactly verify actual fixed VM ID matches source mapping, complete per-task start/finish actual timeline; enforce no missing duplicate Task IDs or VM identities. Each actual result must have real makespan/cost positive finite.
- For each exact fixed genotype independently compute StageInAware insertion planned Makespan/Cost and ReadyQueue TASK_ID event estimator planned Makespan/Cost in read-only mode. Both predict BEFORE true simulator is executed; actual WorkflowSim job outcomes are not given to either planner.
- Do not adapt the policies to observed outcomes; no candidate exclusion based on actual fitness. Archive exact TaskID-to-VM mapping and original source SHA.

## True decision-rank endpoints
With 16 common genotype candidates within EACH (DAX,speed) block, compute independently for each predictor:
- mean absolute percentage prediction error for makespan and cost;
- for all 120 candidate pairs, Makespan and Cost concordant/discordant/tied order, using relative floating tolerance 1e-8; Pareto dominance classification errors (lost/new/reversed) under exact componentwise minimization;
- planned-vs-actual nondominated K16 index set Jaccard, precision/recall;
- actual real quality of planned-front selection. Epsilon weak-dominance robustness at 0.01% and0.1% for any wrongly classified dominance, to avoid mistaking tiny numeric differences for impactful scientific gains.
- One shared normalized 1.5× and 3.0× reference of all 16 true outcomes per block, used to compute each MODEL's plan-selected true front HV against the actual full 16-candidate ND front reference; not a full real search space Pareto optimum. No model tuned using these outcomes.
- Show every source block and negative sign. Pair candidates from the same DAX/profile are not independent scientific subjects.

## Scientific decision
A model choice for a joint priority/VM optimizer must be based on **prospective same-genotype ordering and meaningful misrankings across DAG/VM regimes**, not model-specific optimizer archives or a lucky four-block HV. If READY still fails to rank same candidates, repair scheduler semantics/measurement before inventing FLA-v20. If READY does rank consistently better, still separate shared decoder accuracy from any new FLA-specific operator benefit and design an untouched family-level holdout later. `master` and all default FLA/NSGA/FIFO behavior unchanged; this is an original audit executable, not a changed optimizer.
