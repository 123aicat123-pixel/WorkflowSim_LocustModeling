# Full ORIGINAL FLA-v12 3030-visit search-history fingerprint reproducibility and OLD/READY overlap: verified actual (2026-11-06)

**VERDICT: 16/16 genuine search-only original source jobs succeeded, exact 64-sample original physical genotype sequence reproduction PASS on all 16, independent full-history SHA-256 read-only audit PASS. NO additional true physical WorkflowSim calls were made. The two source fitness objectives substantially diverge in the actual set of genotypes visited, while EVERY block has some shared genotypes.**

## Full immutable provenance and failure transparency

- Pre-analysis frozen read-only diagnostic protocol `docs/FLA_VISITEDPOOL64_FULL_HISTORY_FINGERPRINT_FROZEN_2026-11-06.md`, commit `ec05b219d928c29f5bbbb6a573fc60c55c1f5217`, completed after observing the original old/ready pool64 true outcomes. It is retrospective source-mechanism analysis, not an untouched validation of an algorithm hypothesis.
- Sidecar `examples/org/workflowsim/examples/planning/FLAVisitedFullHistorySnapshot.java` commit `0c690b1f880d1b4ca7bb536d2f5e795531dcfd5c`; research-only no-simulator opt-in added `e87ab5b23c8e8c755fc0de328ca1fcc88e238ff0`.
- Original [source Actions 42197512311](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42197512311), source SHA `83b792ebf2a743d7be63f8f55c698c51c12efe76`: **ALL 16 original full FLA 3030-visit search-history runs PASSED**. The initial independent audit job failed because its Python script was committed after the workflow source revision, i.e. the original checkout could not load it. It is a packaging failure, NOT a scientific result or source simulation failure.
- Independent Python `scripts/fla_full_history_visitedpool64_identity_audit.py`, commit `a34fcb9445cf281c5b8d834cfe81887d4547d613`, and [read-only recovery Actions 42197770671](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42197770671), recovery commit `9552567a1e1f03000ba8996adab90d37e3939a8c`: **PASSED** using ALL 16 immutable original search-only artifacts from run 42197512311 (no source reruns), plus exact original frozen 64 physical mapping input archives from OLD run 42195625222 and READY run 42196301442.
- Audit reproduces exact **64 distinct original sampled physical mapping sequences in all 16 blocks**, computing cryptographic SHA-256 from canonical TaskID→VMID mapping keys independently in Python. Checks full original 3030 fitness visits, positive full unique mapping counts, 16 source identities, source SHA and frozen protocol SHA, zero new actual simulator replay files, all 64 source samples present in the complete unique set. It reports full unique genotype-history overlap as unique mapping fingerprint identity.

## Eight full unique search-history comparisons (same DAG/speed/seed)

| Original DAG | VM speed | Search seed | OLD unique visited | READY unique visited | Common full-history physical assignments | Full-history Jaccard | Common of sampled 64 |
|---|---|---:|---:|---:|---:|---:|---:|
| Montage_100 | default | 1701 | 3020 | 3021 | 30 | 0.004991 | 0 |
| Montage_100 | default | 1702 | 3022 | 3022 | 83 | 0.013924 | 4 |
| Montage_100 | staggered | 1701 | 3004 | 3012 | 84 | 0.014160 | 0 |
| Montage_100 | staggered | 1702 | 3014 | 3006 | 67 | 0.011255 | 0 |
| Montage_50 | default | 1701 | 3001 | 2992 | 156 | 0.026726 | 0 |
| Montage_50 | default | 1702 | 3007 | 2986 | 57 | 0.009602 | 0 |
| Montage_50 | staggered | 1701 | 2964 | 2972 | 93 | 0.015916 | 0 |
| Montage_50 | staggered | 1702 | 2975 | 2979 | 41 | 0.006934 | 0 |

- **Mean full-history Jaccard 0.012939** (1.2939%); mean **76.38** shared unique physical genotypes. **0/8** full histories are completely disjoint, whereas **7/8** frozen 64-map sample pairs had zero shared mappings. Thus the low 64-sample overlap does reflect small *whole-history Jaccard* here, but zero observed sampled overlaps cannot be stated as entirely disjoint search paths.
- Each FLA source actually evaluates 3030 genotypes and visits about 2964–3022 distinct TaskID→VMID maps; nearly the whole budget is distinct in these cases. The two objectives have markedly different full search exposure within the tested Montage source regime.
- Fingerprint identity is map identity only. It does not measure when a map appeared (generation), different predictions for the same genotype, crossover lineage or Pareto front quality. The earlier four-arm true HV evidence **6 wins, 2 losses** for READY-generated source relative to OLD-generated source at fixed READY terminal selector remains mixed, not an algorithm superiority claim.
- The original 1024 true physical simulator labels from the old/ready source runs were NOT re-observed or supplemented by this fingerprint study. Re-executed full search histories were deterministic under same frozen software/method/configuration and agreed exactly with all original source selected samples; no unseen DAG family or independent statistical evidence is introduced.

## Next scientific falsification
This result motivates an explicit, preregistered search stability mechanism that manages objective-induced exploration drift (e.g., calibrated source-objective abstention or controlled OLD/READY search allocation) under identical model-calls and CPU-time budgets, with random/sham control; it does **not** itself validate such a mechanism. Any new scheme must be evaluated prospectively on unseen DAG structures beyond Montage, with enough independent seeds, plus actual original WorkflowSim K8–K16 truth replays and a matched NSGA-II solver comparator; preserve original negative results and do not tune on this retrospective dataset.

**All research-only code and data stay on `fla-baseline`. `master`, default FLA-v12, NSGA-II, and real FIFO runtime are unchanged.**
