# Same-placement exact K1/K2/K4/K8 prospective-only selection: completed actual WorkflowSim result (2026-11-04)

**Scientific decision: lower model Makespan error can improve true Pareto HV at a TIGHT replay budget, but the effect here is small, concentrated in CyberShake, and disappears once K=8 of 16. This is selection evidence on a limited finite mapping universe; not evidence of FLA-specific superiority or new SCI-ready algorithm.**

## Preregistered provenance
- Frozen BEFORE running analysis `docs/FLA_SAME_MAPPING_LOW_K_SELECTION_FROZEN_PROTOCOL_2026-11-04.md`, commit `553ddd3`.
- Original **96 real WorkflowSim simulation points** already archived in [Actions 41695356307](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41695356307), source Java SHA `e51e161e42e3852b159a453e3c1480c19ff99d4f`, 3 known DAX families (`CyberShake_30`, `Epigenomics_46`, `Montage_50`) ×2 VM speed profiles ×16 unique unoptimized algorithm-independent deterministic Task→VM maps. Prior same-map predictor audit [41695748829](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41695748829) passed and reported original insertion mean Makespan MAPE **2.120330%** vs TASK-ID READY mean MAPE **0.203173%**, material (>0.1%) Makespan pair-order mistakes **9/720** old vs **0/720** READY. Both models' full planned nondominated sets nevertheless captured **100%** of the actual fixed-16 universe HV in each DAX/profile block.
- Independent low-K selection [Actions 41768405985](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41768405985) **SUCCESS**. It reuses validated `base.load()` full 96 source mapping/provenance checks. All 48 predictor ×K selection sets and 24 within-block old/ready comparisons archived, with every selected exact policy index and actual replay truth. **No new simulator or optimizer calls.**
- Both models select their K from identical 16 original genotype maps using `exact_max_subset`: maximize predicted 2D normalized Pareto HV over all size-K combinations; reference 1.5× maximum PLANNED Makespan and Cost across BOTH models within the DAX/profile group (never uses actual future data). Near ties within absolute HV 1e-12 resolved lexicographically by fixed policy order. Objective references used to score selected points are shared actual within-block 1.5× max (3.0× sensitivity is fully archived), not the planned selection reference. The hindsight real best-K choice is an EVALUATION ceiling only.

## Primary true normalized HV recovery of full 16-case actual fixed mapping universe

| Prospective true replay K | Old StageIn selection | READY TaskID selection | Mean READY−OLD (percentage points) | Paired wins/ties/losses | Same selected physical K-subset |
|---|---:|---:|---:|---|---:|
| 1 | 97.1002313% | 97.1002313% | 0.0000000 | 0 / 6 / 0 | 6 of 6 |
| 2 | 98.9675504% | **98.9894813%** | **+0.0219309** | 1 / 5 / 0 | 5 of 6 |
| 4 | 99.8883832% | **99.9272100%** | **+0.0388268** | 2 / 4 / 0 | 4 of 6 |
| 8 | 100.0000000% | 100.0000000% | 0.0000000 | 0 / 6 / 0 | 6 of 6 |

### Exactly which independent source cases changed
- CyberShake_30/default, K=2: real HV coverage **94.5624278% old** → **94.6940133% READY**, gain **+0.1315854 pp**.
- CyberShake_30/default, K=4: **99.5629431% old** → **99.7260018% READY**, gain **+0.1630587 pp**.
- CyberShake_30/staggered, K=4: **99.7673559% old** → **99.8372580% READY**, gain **+0.0699021 pp**.
- All other 21 within-block/K comparisons tied on actual HV. Epigenomics_46 and Montage_50 both had zero additional true HV coverage despite significantly better Makespan MAPE.
- At K=8, every block's selected subset fully captured the REAL fixed-16 front HV regardless of predictor. This does not mean either algorithm can recover the actual full workflow scheduling Pareto front.

## Research decision and limitations
1. Better forecast accuracy can matter to **very limited retrospective replay budgets**, but the effect is **0.022–0.039 percentage points averaged over six cases**, not a convincing new FLA multiobjective optimization result. A more expensive estimator cannot be justified by average MAPE alone; log all internal model compute calls and true search wall-time before claiming efficiency.
2. The 16 frozen placement patterns include unrealistic all-on-one-VM assignments and may not represent an optimizer's Pareto archive. Exact enumeration of 16 choose 8 candidate sets is research-only, not a scalable FLA selection algorithm.
3. Only three already-known DAX families, six highly correlated speed blocks, not an untouched family holdout. This analysis reused real labels known from past results, although the selection rule used only planned values. Treat as a locked read-only **retrospective experiment**, NOT independent prospective validation.
4. Prior equal-evaluator FLA priority portfolio [41683457146](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41683457146) and matched restart tests [41689570828](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41689570828) did not show stable FLA gain; FLA v19 [41691646807](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41691646807) also failed its primary mean true HV target. Do not reverse these decisions on the basis of low-K result.
5. Next defensible technical design question is **compute-aware decoding**: can selective READY evaluation, triggered by a pre-specified ambiguous predicted ranking margin and measured internal-cost budget, achieve almost the full READY selection gain at lower runtime, when compared to full READY and full OLD using identical genotypes? Such a design requires separate development and untouched-family testing to support a new algorithm claim, and may still be too small in practical effect to warrant publication.

**Decision: archive the low-K result and do not promote a new FLA search operator. Keep `master`, default FIFO, old FLA and NSGA-II unchanged. All experimental work remains on `fla-baseline`.**
