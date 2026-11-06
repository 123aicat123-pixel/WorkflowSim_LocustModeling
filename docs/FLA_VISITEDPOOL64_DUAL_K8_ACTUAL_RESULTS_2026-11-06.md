# Genuine FLA-visited 64-map same-physical-pool dual predictor selection: original WorkflowSim actual results (2026-11-06)

**VERDICT:** Original source execution and independent exact true-HV K2/K4/K8 verification **PASS**. 8 real FLA-v12 OLD-fitness 3030-visit evolutionary searches and 512 original FIFO WorkflowSim physical replay outcomes were preserved. In this OLD-generated fixed candidate pool, READY K8 blind selection had 3 wins, 5 exact ties, 0 losses over 8 development blocks, mean normalized true ΔHV +0.000053906. **NOT** a new improved FLA optimizer or evidence of robust generalization; prior full-search READY objective failures still apply.

## Reproducibility, provenance and limits
- Protocol frozen before new source outcomes: `docs/FLA_VISITEDPOOL64_DUAL_K8_FROZEN_2026-11-06.md`, SHA `22c8c57c234532b251bee075fca8cecf9d3a9e2d`.
- Opt-in original FLA-v12 driver update `5d86f6476387238bb4115a77808f0c8acfb270d4`; original sidecar `FLAVisitedPool64Experiment.java` commit `1295078e4ff418af0289041e39c19671081a66ed`; original read-only exact audit `c9a3f31e6811440957a420794d2fee0966824437`; explicit unique visited-history capture correction `96da1e3ef8980093d5210f0f076878776b88bd7a`.
- Original source full workflow `7a0dba36a84e367be45c891eedd44dd629083455`, [Actions run **42195625222**](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42195625222): **8/8 true source jobs and 1/1 independent audit succeeded**. Eight raw source artifacts plus one complete auditor artifact, 90-day retention. Java CI for production classes was checked.
- 8 source DAG×speed×search seed blocks: Montage_50/Montage_100 × default/staggered VM speed × source search seeds 1701/1702, original default VM cost and FIFO real runtime. Each original source job runs **one genuine FLA-v12 OLD fitness search** with 30 population, 100 generations, **exactly 3030 objective evaluations** and at least 64 distinct observed genotypes. Candidates were sampled as 64 distinct mappings uniformly from the encounter-ordered unique visited list with a frozen Java PRNG shuffle. No predicted score or actual label affected candidate pool membership.
- Two read-only predictor models (OLD stage-in-aware and READY event-driven FIFO) each evaluate **all same 64 mapping genotypes** BEFORE the first original actual simulator call, with a source log `FROZEN_BEFORE_TRUTH` and separate immutable prediction CSV. All 64 fixed mappings are subsequently replayed via original `LIWSABenchmarkExample.runPlanning`, pop=1/gen=0, actual task-level mapping identity verified. Source budget files report 3030 target search visits and exactly 64 OLD+64 READY standalone diagnostic forecasts; this extra forecasting compute must NOT be represented as equal CPU time to old-only full optimizer search.
- Independent exact scoring checks SHA, protocol content hash, eight block identities, 64 distinct full physical task mappings, predicted and real objective positivity, source logs, all 512 original simulator records and finite future outcome separation. Same-block true-HV reference is `1.5×max(actual on all 64)+1e-6` per objective; exact 2D K oracle by nondominated-chain DP independently unit-tested against brute force, never used for selecting mappings. OLD and READY each use only own forecast to select K2/K4/K8 greedy marginal predicted HV with deterministic ties; 64 frozen blind permutation sham draws are evaluated on the **same** real labels per block, not independent new simulations.

## All eight paired true K8 outcomes

| DAG | VM speed | Search seed | True ND /64 | Physical K8 overlap | OLD real HV | READY real HV | READY−OLD normalized true HV |
|---|---|---:|---:|---:|---:|---:|---:|
| Montage_100 | default | 1701 | 8 | 8/8 | 0.347548690 | 0.347548690 | 0 |
| Montage_100 | default | 1702 | 13 | 8/8 | 0.345965091 | 0.345965091 | 0 |
| **Montage_100** | **staggered** | **1701** | **20** | **7/8** | **0.413522691** | **0.413654421** | **+0.000131731** |
| Montage_100 | staggered | 1702 | 21 | 8/8 | 0.280471628 | 0.280471628 | 0 |
| Montage_50 | default | 1701 | 10 | 8/8 | 0.394792646 | 0.394792646 | 0 |
| **Montage_50** | **default** | **1702** | **14** | **5/8** | **0.376689585** | **0.376902046** | **+0.000212462** |
| Montage_50 | staggered | 1701 | 17 | 8/8 | 0.343241608 | 0.343241608 | 0 |
| **Montage_50** | **staggered** | **1702** | **21** | **7/8** | **0.296847163** | **0.296934221** | **+0.000087058** |

## K2/K4/K8 selection and identifiability

| K | READY wins / ties / losses | Mean READY−OLD true HV | Blocks with true nondominated size > K |
|---:|---|---:|---:|
| 2 | 0 / 8 / 0 | 0 | 8/8 |
| 4 | 1 / 7 / 0 | +0.000024278 | 8/8 |
| 8 | **3 / 5 / 0** | **+0.000053906** | **7/8** |

The previous algorithm-independent fixed32 pool had only 1–4 real nondominated maps and K8 was fully saturated in all six study cases. In this **genuine optimizer-visited** pool, 7/8 K8 blocks contain >8 nondominated maps, so the evaluation can discriminate K8 selection. Nevertheless the observed differences are small: the biggest K8 gain is +0.000212462, not the order of magnitude of the older −0.033404446 full-search loss.

## Attribution, scientific restrictions
- Holding candidate membership constant makes READY-vs-OLD a legitimate *terminal selection model* comparison under a particular OLD-FLA-generated source distribution. This is **not** a matched run of READY fitness evolution; it cannot explain away the adverse original independent READY search trajectory. The old and ready predictor forecasts were computed for identical physical maps, so paired prediction error comparisons are meaningful, unlike old-only versus ready-only chosen-genotype MAPE.
- The previous READY full-search severe loss on Montage_100/staggered/seed1601 in [run 42190857445](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42190857445) remains fully valid and is not contradicted by this **different-seed, fixed OLD-history** mechanism test.
- No claim of a novel FLA operator, multi-family unseen holdout, significant superiority or equal CPU-time algorithm fairness is supported. Both Montage DAX sizes are one historically explored family; 1701/1702 give only two stochastic search seeds; 512 real mappings and random sham permutations are NOT independent blockwise replicates.
- Next decisive prospective trial: freeze and compare separate fixed visited pools sourced from (A) OLD-FLA, (B) READY-FLA and (C) cost-seeded NSGA-II at matched search visits and physically matched old/ready/blind selector budgets, then run fixed candidate truth to distinguish candidate source from selector. Also compare simple equal-work sham, real source walltime, multiple new DAG structures and 20+ independent search seeds before algorithm upgrade.

**Default FLA-v12, NSGA-II, READY settings and `master` are unchanged. All work is on `fla-baseline`.**
