# FLA/NSGA-II first REAL-optimizer staged ready-decoder batch K8 gate: source verified actual results (2026-11-04)

**VERDICT: opt-in two-fidelity batch screening successfully connects to both original optimizers and saves 24 of 32 READY calls per 32-candidate batch, but does NOT robustly improve actual Pareto HV. The favorable cost-vs-fidelity tradeoff is a demonstrable engineering property, not yet a publishable improved FLA method. `master` is unchanged.**

## Original immutable source and failure history
- Protocol frozen before the original outcomes: `docs/FLA_STAGED_REAL_OPTIMIZER_K8_FROZEN_PROTOCOL_2026-11-04.md`, commit `9ab9d6d`. This specifically fixes three historically familiar DAG instances `CyberShake_50`, `Sipht_60`, `Epigenomics_100`, two original RNG seeds 801/802, 30×101=3030 original counted genotype evaluations per solver, 32 planned-coverage original genotypes per solver, K8 original WorkflowSim replays and 3 EXACT selector strategies (OLD-only greedy, FULL READY greedy, STAGED greedy T8).
- First source [Actions 41777491741](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41777491741) failed **ONLY a post-simulation CSV assertion**: the newly introduced staged-selection header contained the literal characters `\n` rather than a newline, causing `csv.DictReader` to treat the first data row as part of the header. The actual original full FLA+NSGA search and simulator replays ran. Minimal reproducible diagnostic [41777821251](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41777821251) directly printed 2 original summary rows, 16 original real replay rows and the malformed 1-row staged CSV. `FLAResearchExperiment` then corrected only CSV newline serialization at `73c2bf6`; **no model, search, selection, T/K or simulation semantics changed**.
- Corrected original source [Actions 41777916573](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41777916573) **18/18 jobs PASS**: 3 DAX ×2 seed ×3 prospective selector modes, each source job runs the paired `DAG-Pareto-FLA[v12-hvbandit]` and `NSGA-II[costseed]`. Each source solver/mode has 3030 original genotype fitness evaluations and **8 real WorkflowSim replays**, totaling **288** original actual simulator calls.
- Earlier independent audit [41778013108](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41778013108) failed because it started before the slowest Epigenomics artifacts existed. It did **NOT** demonstrate any algorithm failure. The corrected independent read-only [Actions 41778249874](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41778249874) **PASS**, checking all 18 source artifacts, 36 solver×mode source solutions, 12 paired comparisons, positive finite actual objective values, source policy labels, 32 unique selected source genotype pool hashes identical across modes within each exact solver/DAG/seed, and exactly 3030 source optimizer evaluations. It recomputed real normalized Pareto HV at shared 1.5× and 3.0× actual reference within EACH source DAG/seed block from all six solver×mode K8 sets. No new simulations or fitted decision rules in this audit.

## Actual Pareto results: normalized K8 shared-reference WorkflowSim HV (1.5×)

| Workflow | Seed | Solver | OLD greedy | FULL READY greedy | STAGED greedy (T8) | STAGED−FULL READY |
|---|---:|---|---:|---:|---:|---:|
| CyberShake_50 | 801 | FLA-v12 | 0.33469571 | **0.33471388** | 0.33470518 | −0.00000870 |
| CyberShake_50 | 801 | NSGA-II seeded | **0.34788342** | 0.34771498 | **0.34788342** | +0.00016844 |
| CyberShake_50 | 802 | FLA-v12 | 0.41628716 | **0.41638929** | 0.41628716 | −0.00010213 |
| CyberShake_50 | 802 | NSGA-II seeded | **0.42953719** | 0.42950653 | 0.42950653 | 0 |
| Sipht_60 | 801 | FLA-v12 | **0.24466160** | 0.24357812 | 0.24357723 | −0.00000090 |
| Sipht_60 | 801 | NSGA-II seeded | **0.26264560** | 0.26264553 | 0.26264553 | 0 |
| Sipht_60 | 802 | FLA-v12 | **0.25622803** | 0.25622782 | 0.25622760 | −0.00000021 |
| Sipht_60 | 802 | NSGA-II seeded | **0.26908281** | 0.26908276 | 0.26908276 | 0 |
| Epigenomics_100 | 801 | FLA-v12 | 0.35887714 | 0.35887714 | 0.35887714 | 0 |
| Epigenomics_100 | 801 | NSGA-II seeded | 0.33701774 | 0.33701774 | 0.33701774 | 0 |
| Epigenomics_100 | 802 | FLA-v12 | 0.33456725 | 0.33456725 | 0.33456725 | 0 |
| Epigenomics_100 | 802 | NSGA-II seeded | 0.32289508 | **0.32523295** | 0.32519794 | −0.00003501 |

All values are true simulator K8 HV, not planned HV; each DAX/seed has one common reference across all six source arms (references differ between DAG/seed blocks). Original full source data and planned selections in the [Actions 41777916573 artifacts](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41777916573); independent all-case CSV, negative outcomes and reference sensitivity archived in the [Actions 41778249874 artifact](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41778249874).

### Paired observed means (six correlated DAG/seed blocks per original optimizer)
- Original FLA-v12: STAGED minus FULL READY mean true normalized HV **−0.00001866**; nominal 0 wins, 2 ties, 4 losses. STAGED minus OLD mean **−0.00017922**, driven mainly by Sipht_60 seed 801, where OLD achieved 0.24466160 vs STAGED 0.24357723.
- Seeded NSGA-II: STAGED minus FULL READY mean **+0.00002224**; 1 win, 4 ties, 1 loss. STAGED minus OLD mean **+0.00037868**, mainly Epigenomics_100 seed 802. Neither outcome establishes stable algorithm superiority, and no test is an unseen-family holdout.

## Real Java call counts and time
- Each optimizer treatment uses exact same original planned source genotype pool (SHA-256 fingerprint matches 3/3 selector policies per solver/DAG/seed).
- Source search budget is **3030 counted original fitness evaluations** per solver in ALL modes. The separate post-search selector has exactly:
  - OLD-only: 32 OLD post-search decoder calls, **0** READY calls;
  - FULL READY: 32 OLD post-search reference decodes + **32** READY decodes;
  - STAGED T8: 32 OLD post-search reference decodes + **8** READY decodes.
- Both old and ready decode implementations are the actual Java `StageInAwareScheduleEvaluator` / `ReadyQueueScheduleEvaluator` using the same Task→VM assignment and 16 original CondorVMs; `UnifiedCandidateRecorder` captures original Task/VM objects **only when `dagfla.stagedReplayContext=true`**. No change to original target fitness, seeding, mutation, population size, original simulator runtime or FIFO default.
- Measured **post-search batch model+selection wall clock**, STAGED/FULL READY mean ratio across six original blocks: **0.714× for FLA**, **0.823× for NSGA-II**. Some individual blocks were actually SLOWER (CyberShake_50 seed 801 NSGA-II ratio 1.127×; Epigenomics_100 seed 801 NSGA-II ratio 1.433×), despite exactly 24 fewer READY calls. These observed timings are per-job JIT/runner-dependent and do NOT imply a 28.6% or 17.7% reduction in complete FLA or NSGA-II search+simulator run time.
- The new selector runs **after** the 3030 original search fitness evaluations; its reduced READY calls are in post-search candidate selection, not optimizer evolution. Thus, no claim of a novel multi-fidelity FLA evolutionary optimization method is allowed.

## Final research decision and next gate
1. The previous retrospective 16-genotype experiments demonstrated cheap OLD shortlist can usually retain FULL READY real HV. This *real optimizer population* K8 study shows that such perfect preservation is NOT stable. The model can select different physical assignments with slightly worse true HV, and when full READY itself loses to OLD (e.g. Sipht_60), STAGED may also lose.
2. **Do NOT promote staged K8 as a universal HV improvement or FLA v20.** It has demonstrated constrained post-search model-evaluation efficiency and acceptable near-READY fidelity in several instances, not general search superiority. Keep all adverse and tie results.
3. Next defensible advance requires **actually integrating an uncertainty- or risk-controlled two-fidelity fitness policy DURING evolution**, counting every OLD and READY decode and matching both total computation budget and true K16 final replay budget for FLA and NSGA-II. This is scientifically different from the present K8 post-search replay screening, and should be registered separately with a truly untouched independent DAG-family holdout. An ablation must distinguish multi-fidelity screening effect from changing the initial FLA genotype search trajectory.
4. Existing 2024 rule-learning and multiobjective cloud workflow literature already studies task rules and resource assignment. Any SCI Q1 claim requires a distinctive, substantiated mechanism, independent hypervolume gains and cost-time evidence beyond this engineering gate.
5. No merges to `master`. The opt-in source `StagedScheduleBatchEvaluator`, `GreedyStagedParetoSelector`, original FLA v12/seeded NSGA-II baseline and all historical failures remain auditable on `fla-baseline`.

**Decision: end-to-end candidate replay integration PASS, stable FLA improvement FAIL. Publishable FLA novelty remains UNPROVEN.**
