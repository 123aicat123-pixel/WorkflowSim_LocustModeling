# Active Uniform Residual K8: complete real WorkflowSim outcome (2026-11-04)

**VERDICT: implementation and original-source verification PASS; improved FLA claim FAIL. Do not promote or retune on these same seeds.**

## Frozen scientific chain
- Prospective protocol `docs/FLA_ACTIVE_UNIFORM_RESIDUAL_K8_FROZEN_2026-11-04.md`, committed at `556b35f` **before** any new true outcomes.
- New opt-in post-search ACTIVE selector: `sources/org/workflowsim/planning/ActiveUniformResidualSelector.java`; `StagedScheduleBatchEvaluator.selectActiveUniform` with real OLD/READY predictors; FLA/NSGA original search and FIFO runtime unchanged.
- Original source [GitHub Actions 41821482575](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41821482575) from SHA `ed010ea4988f61c8991bc415c5e09d3f1d3cad00`: **24/24 jobs SUCCESS**, 3 historically familiar DAGs ×2 new seeds 903/904 ×4 modes ×2 solvers ×K8 = **384 actual simulator replays**. All 3030 original optimizer objective visits per solver, OLD32 and READY mode quotas exact.
- Independent [all-case audit 41821647563 attempt 2](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41821647563) **SUCCESS**: all 24 archived source jobs, 48 solver/mode K8 actual front sets, 12 solver×DAG×seed paired comparisons, one common immutable source SHA, identical ordered N32 physical-candidate pool fingerprint across all four selector variants per solver/DAG/seed. Source outcomes not rerun or changed by the audit.
- First audit attempt failed solely because it launched before all original 24 jobs had uploaded artifacts; it correctly rejected incomplete source. The retry used the same audit script, after all original jobs completed.
- True 2D normalized HV computed with one shared 1.5× actual reference point across all eight solver×mode arms per DAG/seed; full sensitivity values for 3.0× saved in the independent artifact. No pseudo-independent K8 replay points as statistics.

## Actual K8 HV differences versus controls

| Solver | ACTIVE minus STAGED (equal T8 READY) mean | Wins/ties/losses | ACTIVE minus OLD mean | ACTIVE minus FULL READY mean |
|---|---:|---:|---:|---:|
| FLA-v12 | **-0.000003924** | 1/2/3 | **-0.000002217** | **-0.000026054** |
| NSGA-II[costseed] | +0.000981643 | 1/2/3 | +0.001011105 | -0.000180247 |

- FLA ACTIVE did **not** outperform the original OLD policy on any of six paired blocks: 0 wins, 4 ties, 2 losses.
- FLA ACTIVE did not consistently improve on equal-ready-call staged (1 win, 2 ties, 3 losses). Against FULL READY, one win, one tie, four losses.
- NSGA-II Epigenomics_100 seed 903 yields +0.00635754 HV vs both staged and old, driving its misleading positive mean. NSGA-II wins/ties/losses vs staged: **1/2/3**. Neither optimizer shows stable gains.
- Methods consume READY postsearch calls as originally fixed: OLD0, STAGED8, ACTIVE8, FULL READY32, with OLD32 common to all. This shows evaluation accounting, not full wall-time savings.

### FLA per-block true HV15

| Workflow | Seed | OLD | FULL READY | STAGED | ACTIVE |
|---|---:|---:|---:|---:|---:|
| CyberShake_50 | 903 | 0.35983292 | 0.35996570 | 0.35983292 | 0.35983292 |
| CyberShake_50 | 904 | 0.43851563 | 0.43852588 | 0.43852588 | 0.43851563 |
| Sipht_60 | 903 | 0.24516948 | 0.24516947 | 0.24516947 | 0.24516906 |
| Sipht_60 | 904 | 0.24508807 | 0.24508806 | 0.24508806 | 0.24508807 |
| Epigenomics_100 | 903 | 0.34537452 | 0.34537452 | 0.34537452 | 0.34537452 |
| Epigenomics_100 | 904 | 0.34442496 | 0.34442496 | 0.34442496 | 0.34441208 |

## Decision and limitations
- **No improved FLA claim.** Common-scale correction is an internally coherent comparison mechanism, not proof that the corrected prediction equals actual simulator truth or that its READY allocation improves selection.
- This test is after-search replay candidate screening, not a new evolutionary fitness operator; any paper must distinguish those.
- Same OLD-based 32-source candidate pool can impose a strong coverage bottleneck. No unseen-family holdout or equal-total-compute-time comparison was performed.
- Next scientific question is whether any **true-HV headroom exists in the union of four already-replayed K8 sets**, and how much of the potential improvement is from missed physical candidates vs selection misranking. A post-hoc union oracle is purely diagnostic and cannot be reported as a prospective policy.
- Preserve all raw artifacts and mixed/negative results, never adjust ACTIVE on these seeds and reuse them as an untouched confirmation test.
- No modifications to `master`, original FIFO runtime, or FLA-v12 defaults.
