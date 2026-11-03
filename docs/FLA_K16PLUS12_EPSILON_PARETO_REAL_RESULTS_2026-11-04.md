# Independent ε-Pareto robustness of K16+K12 real WorkflowSim extra candidates — 2026-11-04

**Important negative-size finding: ALL 13 initially real-nondominated added K12 candidates are within 0.1% relative Makespan+Cost tolerance of some ORIGINAL K16 actual schedule.** The model's missed exact Pareto labels are real at floating precision, but none of the 96 extras remain epsilon-uncovered at the prespecified 0.1% practical tolerance. This sharply reduces the case for a new FLA algorithm aimed only at rescuing those candidates.

## Exact immutable source and analysis record
- Preregistration of this read-only numerical robustness analysis, before performing it: `docs/FLA_K16PLUS12_EPSILON_PARETO_FROZEN_PROTOCOL_2026-11-04.md`, commit `67c527397d3c8d02aa651039b59f0cd4008822b6`.
- Original Java real simulator source GitHub Actions [41693332570](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41693332570), original source SHA `f963e95c952a0d3dd67a26cdefa2b5eb221d8d61`: GitHub UI red because a *post-simulation* Python quote typo, not a simulator data-generation failure; four original complete immutable artifacts exist.
- Independent completed source recovery [41693970902](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41693970902) PASS, exactly 8 full source arms (four DAG/seed cases × FLA/NSGA) × (K16 original +K12 additional planned-dominated/tied) = **224 actual WorkflowSim simulation points**. Exactly 96 extra source points, with all original task→VM mapping and recorded truth preserved.
- Relative epsilon diagnostic reuses ONLY this frozen 224-row source CSV, without any new optimizer/simulator calls, script `scripts/fla_k16plus12_epsilon_pareto_sensitivity.py`. First optional analysis workflow [41694426710](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41694426710) FAILED because the single downloaded GitHub artifact was extracted under its artifact-name subdirectory, but path incorrectly assumed it was directly under `original/`. No output cherry-picked; a deterministic path correction was committed and [independent epsilon sensitivity Actions 41694566851](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41694566851) **SUCCESS**. Data and script archived.
- Explicit definition: an original K16 schedule r epsilon-covers new K12 candidate x iff `r.Makespan <= (1+ε) x.Makespan` AND `r.Cost <= (1+ε) x.Cost`; equality counts as covered. The minimum ε making a candidate covered is `min_r max(0, r.M/x.M−1, r.C/x.C−1)`. Report thresholds in PERCENT, e.g. 0.1% means ε=0.001. This is relative weak epsilon cover, **not a confidence interval** or significance test.

## Robustness results, all 96 extra candidates

| Source | Exact real uncovered | Uncovered at ε=0.01% | Uncovered at ε=0.1% | Uncovered at ε=1% | Largest uncovered threshold |
|---|---:|---:|---:|---:|---:|
| CyberShake_50 s951, FLA | 3/12 | 2/12 | 0/12 | 0/12 | 0.0478699% |
| CyberShake_50 s951, NSGA-II | 2/12 | 1/12 | 0/12 | 0/12 | 0.0198394% |
| CyberShake_50 s952, FLA | 2/12 | 1/12 | 0/12 | 0/12 | 0.0126189% |
| CyberShake_50 s952, NSGA-II | 2/12 | 2/12 | 0/12 | 0/12 | 0.0224668% |
| Montage_100 s951, FLA | 1/12 | 0/12 | 0/12 | 0/12 | 0.0000033% |
| Montage_100 s951, NSGA-II | 2/12 | 0/12 | 0/12 | 0/12 | 0.0000567% |
| Montage_100 s952, FLA | 1/12 | 0/12 | 0/12 | 0/12 | 0.0003223% |
| Montage_100 s952, NSGA-II | 0/12 | 0/12 | 0/12 | 0/12 | 0.0000000% |
| **TOTAL** | **13/96** | **6/96** | **0/96** | **0/96** | **0.04786985%** |

The originally recovered [K16+K12 actual HV audit 41693970902](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41693970902) found mean normalized HV increase only **+0.00000047** when adding K12 after K16, confirming weak practical impact on these two task graph instances. This epsilon test is consistent with the near-zero effect: the **largest relative threshold is under 0.05%**, even before considering simulator model rounding.

## Scientific implications
1. Original K16-only archive's 205/6320 Pareto classification disagreements mostly represented additional real dominance due to selection bias, and K16+K12 showed 16 planned-dominance losses. But these later newly recovered "missed" real nondominated candidates were **not materially distinct at a 0.1% two-objective tolerance**; therefore an algorithm-paper novelty claim solely based on their rescue is unsound.
2. The experiment has only two historically studied DAG families, two seeds, and 96 correlated extra candidates. It establishes NOTHING about all possible unselected candidate Pareto errors in a different VM/task regime, nor about larger time/cost differences.
3. A stronger next scientific direction must not blindly design v20 from v19's failure or use retrospective 224 real labels as a training oracle and then call them a holdout. Instead build an algorithm-independent DAG/VM **test universe** with multiple planned-dominated strata, predefined meaningful separation thresholds, and unviewed new DAG-family instances. Measure **significant** forecast-rank errors (e.g. >0.1% or >1% objective deltas) and truth-supported schedule variation before investing in FLA-specific heuristic proposals. Alternatively, turn already verified model mismatch, fair replay and negative results into a suitably modest **reproducibility/measurement paper**, not a claimed new superior algorithm.
4. `fla-baseline` only, master unchanged, FIFO and old FLA defaults intact, all new search variants opt-in. Negative findings preserved, no selective cherry-picking or new simulator calls in epsilon robustness audit.

**Decision: DO NOT prioritize rescuing exact but near-identical Pareto points. Prioritize meaningful effect sizes and reliable cross-DAG generalization before declaring algorithm innovation.**
