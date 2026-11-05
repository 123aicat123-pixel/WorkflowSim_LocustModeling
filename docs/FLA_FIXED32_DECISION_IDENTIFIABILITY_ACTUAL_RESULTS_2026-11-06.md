# Fixed 32 physical VM-map universe: complete true-HV outcome and decision-identifiability gate (2026-11-06)

**VERDICT: original 256 physical WorkflowSim results verified, exact K4 TRUE-HV oracle PASS, and independent true-front discrimination audit PASS. No OLD-vs-READY actual decision divergence. No demonstrated FLA algorithm improvement. The 32-map K4 test has substantial power/identifiability limits, especially where the true Pareto front is <= K.**

## Frozen prospective sources
- Precommitted experimental protocol `docs/FLA_INDEPENDENT_32_MAPPING_K4_DIVERGENCE_FROZEN_2026-11-05.md`, commit `d91f242`, fixed before any new simulator outcomes. Original first 16 physical mapping rules plus 16 novel deterministic VM/Task mapping rules. No score-informed or true-label-informed policy additions after freezing.
- Original FIFO WorkflowSim [8/8 source run 42019263313](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42019263313), source SHA `9cf14220409bb2f574c624f6e8a26297e09eb9c5`; 4 existing DAG families with new sizes `Inspiral_30`, `Sipht_30`, `Epigenomics_100`, `CyberShake_50`, default and staggered VM profiles, simulator seed 1501. Exactly **256 new physical TaskID→VMID true replay rows**. No optimizer, FLA search, or READY-guided candidate generation.
- Primary [independent K4 audit 42019608367, attempt 2 SUCCESS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42019608367). Attempt 1 failed because only two original source artifacts had been uploaded; the same source-identity audit was rerun after 8/8 original jobs passed. It verified eight immutable artifacts, same source SHA, same-physical-identity OLD/READY predictions, truthful simulator objectives, original 16 policies plus frozen additional 16, one shared per-(DAG,VM-profile) actual HV reference, predicted-only fixed HV greedy K4, blind and restricted original-first16 K4 controls, 32 deterministic blind random K4 samples, and **exact 35,960 combinations (C(32,4)) true-label hindsight K4 oracle** per scenario.
- Primary result: OLD vs READY chosen physical K4 sets **identical in 8/8**, both true normalized HV at the restricted best K4 in **8/8**. Both models' true K4 regret 0.000000000; blind first 4 mean regret **0.036657026**, original first16-only model regret mean **0.007665508**. READY reduced planned strict false dominance from OLD **16** to **8** among 2,420 OLD and 2,405 READY within-block forecast strictly dominated pairs respectively. Neither had direct reversed true dominance. Importantly, more accurate predicted dominance had **zero observed actual K4 decision effect**.
- All 32-genotype outcomes are on *known workflow families* and one simulator seed, so this is NOT an untouched-family holdout or statistical publication-level evidence.

## Additional independent K1-K4 identifiability validation

Source derived from the independently audited 256 true rows, with no new original simulator labels. [Independent exact finite-front and K1-K4 audit 42082119723 SUCCESS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42082119723), script `scripts/fla_independent32_k4_identifiability_audit.py` independently reconstructs actual HV and nondominance and reruns the frozen OLD and READY **predicted-only** greedy HV policy to verify every selection PREFIX K1,K2,K3,K4 against the original independent decision CSV.

| Workflow | VM speed | True ND map count (out of 32) | Max true K4 - max true K3 normalized HV | Complete true 32-set - max true K4 HV | Distinct optimal four-sets among 35,960 |
|---|---|---:|---:|---:|---:|
| Inspiral_30 | default | 3 | 0 | 0 | 29 |
| Inspiral_30 | staggered | 6 | +0.000351942 | +0.000147578 | 1 |
| Sipht_30 | default | 3 | 0 | 0 | 29 |
| Sipht_30 | staggered | 3 | 0 | 0 | 29 |
| Epigenomics_100 | default | 4 | +0.000003042 | 0 | 1 |
| Epigenomics_100 | staggered | 1 | 0 | 0 | **4,495** |
| CyberShake_50 | default | 10 | +0.006010117 | +0.001475984 | 1 |
| CyberShake_50 | staggered | 5 | +0.000528357 | +0.000047613 | 1 |

- **5/8** scenario blocks have actual original 32-set Pareto cardinality **<=4**, so a K4 policy may cover the entire finite front.
- **4/8** blocks gain essentially zero TRUE HV from the fourth map versus optimal K3; the K4 outcome is effectively saturated for those blocks.
- **4/8** blocks admit multiple exactly true-HV-optimal K4 subsets: in `Epigenomics_100/staggered`, the sole nondominated assignment is enough to obtain the entire restricted true front; **4,495/35,960** different four-subsets tie for optimal HV.
- Recomputed OLD/READY *ordered* greedy choice for K1,K2,K3,K4 is **identical, not merely equal HV** in all eight blocks (0/8 prefix-set disagreements for EACH K). The 8/8 true K4 optimum is not informative about which planner makes better decisions when their decisions never differ.
- This is a **retrospective diagnostic on seen true labels**. It does not refute all StageInAware/READY differences in other families, dynamic queue regimes, workflow schedules or future truly independent studies, and cannot be represented as a new scheduling algorithm.

## Publication gate and decision

The newly documented weakness is **evaluation identifiability**. The study should now distinguish (a) full-32 frontier cardinality, (b) the effective K budget required to capture its true HV, (c) rate of actual OLD-vs-READY decision divergence, and (d) their real decision regret. Without these, low regret and low forecast error can be scientifically uninformative.

A next SOURCE-LEVEL independent experiment could prospectively enrich a candidate universe for **predictor disagreement using only OLD and READY planning predictions** (never true simulator labels), but must report the selection-induced enrichment bias; retain a second objective-independent mapping control arm, explicitly matched VM/profile/workload and true simulator budget, and include unseen task-family or queue regimes. Candidate policy rules and target K must be frozen before labels. If no meaningful decision disagreement or true regret impact exists, stop rather than manufacturing claims of a model benefit.

The present evidence supports a reproducibility/methodology study of **planning/simulator Pareto dominance fidelity, candidate-selection bias and *when decision regret is measurable***. It does **not** validate an SCI-improved FLA optimizer, new novel risk scoring algorithm, or cross-family generalization. Keep original adverse findings, do not tune the original 32 mappings using these observed labels.

**All files on `fla-baseline`, `master` unchanged.**
