# Same physical 32-mapping pool K2/K4/K8: actual WorkflowSim selection and random sham (2026-11-06)

**VERDICT: 6/6 original physical simulator jobs succeeded; first audit failed closed due to an invalid assumption that DAX filename suffix equals XML <job> count; exact source XML counts independently verified and the original same-source read-only audit then PASSED. The experiment does NOT establish an improved FLA optimizer or an explanation for the prior full-search loss.**

## Source and audit chain
- Frozen protocol BEFORE new truth: `docs/FLA_SAMEPOOL32_K8_RANDOM_SHAM_FROZEN_2026-11-06.md`, commit `9a0df04850cbc628cc7ad250459e5681aab3782d`.
- Source and first audit workflow commit `658e20dfa7e63700c7336e912bdf79d534ccf299`, [Actions 42193261523](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42193261523): **six real original WorkflowSim matrix jobs PASS**, one analysis job correctly FAILED CLOSED. The first audit's `int(workflow.split('_')[-1])` check was incorrect: the frozen DAX XML has **50 jobs** for `Inspiral_50`, **47 jobs** for `Epigenomics_46` and **58 jobs** for `Sipht_60`. The labels 46 and 60 are not authoritative counts.
- Analytical-only correction `b488efa31a510a3fe98943d6669f29d2f52e9cc9`: fixed the expected task-count dictionary, verified against the original XML; **no Java planner, source mapping, VM speed, original simulator truth, or original run artifact changed**.
- Audit-only recovery workflow `92a0bec02ba28aac825d0129da0af178a875ad7a`, [Actions 42193501842 — SUCCESS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42193501842): downloads original six real artifacts of run 42193261523, verifies immutable original source SHA/protocol SHA, all 192 original physical assignments, complete per-task mapping identity, real logs and actual simulator objectives; independently verifies exact nondominated-chain K2/K4/K8 oracle by brute-force finite-subset fixtures, then executes all selections and saves raw records.
- **Six** conditions (Inspiral_50, Epigenomics_46, Sipht_60 × default/staggered), 32 fixed physical TaskID-to-VMID mappings per condition, historical simulator seed 1501 as metadata, no population evolution, one exact original true WorkflowSim outcome per physical mapping. **192** original physical truth rows, **36** forecast-selected method×K choice rows and **1,152** blind random-sham K-specific choice rows (64 permutations per block ×3 K values ×6 blocks). Sham rows **reuse** the same 192 simulator outcomes and are NOT 1,152 new real simulations or independent experimental replications.

## Actual normalized true HV results (single shared reference per physical pool)

| K | READY wins / ties / losses in six blocks | Mean READY − OLD true HV | K-reference interpretation |
|---:|---|---:|---|
| 2 | **1 / 5 / 0** | **+0.000109592** | Inspiral_50/default benefits by +0.000657553 |
| 4 | **1 / 5 / 0** | **+0.000000058** | Inspiral_50/default +0.000000346 (numerically tiny) |
| 8 | **0 / 6 / 0** | **0** | Both recover full restricted-32 true HV in all six blocks |

The true nondominated map counts by block:
- Epigenomics_46/default: **3**; staggered: **3**.
- Inspiral_50/default: **4**; staggered: **1**.
- Sipht_60/default: **2**; staggered: **1**.

The exact retrospective K8 hindsight optimum saturates the entire true HV front in all six pools. OLD and READY capture that same K8 actual HV and thus show **no decision performance differentiation** at K8 even if some redundant selected physical mapping identities differ. At K2, `Inspiral_50/default` OLD HV **0.472753128**, READY HV **0.473410681**, while both have exactly two selected mapping slots and 1/2 overlap. At K4 the same block has OLD **0.473517070**, READY **0.473517416**, nearly identical performance.

All 64 pre-frozen random permutations per block are archived including median, min, max, and empirical 5th/95th order-statistic summaries for K2/K4/K8. Sham is an unbiased-by-predictor *selection benchmark*, not an adaptive method, and 64 permutations should not be used as 64 independent simulator runs.

## Scientific interpretation / next gate
1. **Candidate selection is now isolated for this fixed physical pool.** K2 occasionally distinguishes OLD and READY, but K8 does not because all six true fronts have 1–4 nondominated points. The result is a strong identifiability warning against choosing low-complexity fixed candidates and then treating K8 as a discriminating search test.
2. The previous full-optimizer adverse READY effect **−0.033404446** (Montage_100/staggered/1601) remains unexplained. The full-search K8 selected map sets had overlap 1/8, but the fixed-32 physical pool here is not the same as either optimizer's 3030 visited candidate histories. No causal attribution between trajectory and terminal candidate selector is licensed.
3. A useful next *separately preregistered* experiment should export a fixed (possibly 32–128) **same actual optimizer-visited genotype pool** from OLD/READY search history, freeze it before actual labels, score identical genotypes by both predictors (using original Java stages), select K8 under OLD, READY and an equal-computation sham, and replay the union of selected mappings exactly once in original WorkflowSim. This more credible test can isolate terminal model ranking conditional on the **same optimizer-generated candidate pool**. Include fail-closed source/replay identity checks, no tuning with prior observations, and a sufficient true nondominated set to make K8 nontrivial.
4. No statistical/generalization claim (three familiar DAG families × two deterministic profiles), no "K8 READY advantage", no novel FLA algorithm claim. FLA-v12/NSGA-II and their defaults unchanged.

**All analysis and workflow changes remain on `fla-baseline`; `master` unchanged.**
