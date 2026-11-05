# Prospective v20: frontier-novelty DAG edge search vs random novelty (2026-11-04)

**Locked before any v20 search/simulator outcomes.** This protocol concerns a NEW opt-in proposal operator applied DURING the actual FLA optimizer, not post-search K selector tuning. It does NOT guarantee better real Pareto HV or constitute a paper novelty claim.

## Why this is nonduplicative
Earlier V5 DAG blocks, V6 random novelty repair, V9 edge co-location, V14 time-line neighbor, and V18/V19 queue-predictor moves were already tested, with mixed/negative true HV. An independently audited 4,040 selected-population snapshots yielded exactly 30 distinct selected genotypes in every observed generation. Thus **duplicate selected individuals is not the hypothesis**. The proposed v20 intervention tests whether actively maximizing *minimum genotype-Hamming distance from the current selected breeding population* (rather than merely checking exact duplicates) improves observed Pareto solution quality. A four-proposal choice isolates the novelty-selection effect and a causal DAG edge source; it cannot read simulated outcomes or READY model predictions.

## Three original FLA arms and NSGA-II
- `v12-hvbandit`: unchanged control.
- `v20-frontier-random`: at each eligible normal FLA child, with frozen 0.35 trigger, construct exactly **four** distinct VM-gene random proposals, score each by minimum normalized Hamming distance to CURRENT parent population (without any objective decode), and apply the most novel legal candidate before the normal single target objective evaluation.
- `v20-frontier-dag`: identical trigger, four proposals, same Hamming selector and RNG API, but proposal targets DAG parent→child edges. Makespan-search group preferentially co-locates a child with its DAG parent; cost-search group preferentially assigns edge child to a minimum-price eligible VM (fixed tie rule). If this cannot produce a changed VM assignment, falls back to a feasible random VM change. This combines DAG structure with genotype-space novelty but does not yet prove new algorithm originality.
- `NSGA-II[costseed]`: existing seeded competitor, unchanged. Every FLA arm inherits EXACTLY the existing v12 pipeline, archive, FLA phase-bandit, V6 duplicate prevention and cost seeding; only the optional v20 proposal step differs. No READY decoder callbacks or true-simulator labels inside v20.

## Fixed experiment and consistency
- Development-only: three previously studied instances `CyberShake_50`, `Sipht_60`, `Epigenomics_100`, optimizer seeds **951,952** (not used in the active K8 study); default 16 VM profile and original FIFO WorkflowSim runtime.
- Fixed pop30, gen100, original **3030 target objective evaluations per solver**. Identical deterministic first two seeded FLA/NSGA Task→VM assignments; no independent extra fitness calls for any of the four proposals. Count trigger attempts and actual changed-genotype moves, separated from charged target evaluations.
- **K16** distinct planned-only `pareto-cover` replay assignments each of the four arms per scenario; 3 DAX ×2 seed ×4 solvers ×16 = **384 actual WorkflowSim replay outcomes** if 6 source jobs PASS.
- Freeze common 1.5× *actual* objective reference per DAG/seed across all four solver arms, additionally 3× sensitivity; report raw M/C, ND size, pairwise real K16 HV, unique visited mapping count, selected K16, original search time and v20 action rates. Do NOT use one per-arm self-referenced HV for comparative claims.
- Same source SHA per job, equal original counted evals, no changed original FIFO runtime, no hidden predictor calls, no retrospective changing of trigger, proposal count or objective. Actual FLA vs NSGA, v20 DAG vs v20 random vs v12 full ablation are mandatory. No "best seed" selection, no promotion on these familiar DAGs. Significant publication claim would require truly untouched DAG families and equal CPU/time validation.

## Go/no-go
- Required: effect on original optimizer-visited genotype spread (a separate diagnostic, not just selected-population uniqueness), real K16 HV compared within each DAG/seed block, total measured CPU/wall costs, reproducible source/CI evidence.
- Reject any new v20 enhancement claim if gains are mixed or cannot beat a random-novelty comparator; no param tuning on these seed results.
- All modifications ONLY `fla-baseline`; `master` and default original v12 remain unchanged.
