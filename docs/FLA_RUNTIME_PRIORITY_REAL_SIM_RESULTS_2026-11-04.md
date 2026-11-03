# FLA runtime ready-job priority: 36 real WorkflowSim interventions and dispatch-conflict validation (2026-11-04)

**Scientific decision: runtime priority is a genuinely actionable control dimension on fixed task-to-VM mappings, but no constant priority heuristic is reliable across mappings, and no FLA-specific new optimizer has been demonstrated.** Retain `fifo` as default; all new behavior is opt-in on `fla-baseline`. No changes to `master`.

## Why this follow-up was necessary
Earlier stage-in/ready decoder and FLA-v18 experiments localized DAG-unrelated same-VM planned/real order disagreements, but did not establish that priority could be controlled within the real simulator or that doing so materially changed total workflow outcomes. A separate already-completed v18 [negative cross-DAG gate](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/blob/fla-baseline/docs/FLA_V18_DISAGREEMENT_OPERATOR_ACTUAL_RESULTS_2026-11-04.md) yielded two Montage wins and two CyberShake losses: merely targeting decoder disagreement did not justify an optimizer claim.

## Implementation / isolation
- New `sources/org/workflowsim/scheduling/FLAFixedVmReadyPriority.java`: opt-in `-Ddagfla.fixedVmReadyPriority=fifo|shortest|upward`. Original `fifo` remains default and preserves pending order. `shortest` sorts ready original compute Tasks by MI ascending; `upward` sorts by downstream longest task-MI chain descending, with deterministic original Task ID tie-breaking.
- Minimal change in `StaticSchedulingAlgorithm.java`: sort only the candidate list's existing COMPUTE-job positions (never alter stage-in/noncompute slots); no changes to `WorkflowEngine` dependency-release conditions, VM assignments, CloudSim job events, FLA v12 or NSGA-II search.
- New unit `FLAFixedVmReadyPriorityTest`: verifies original FIFO queue identity, two recognized task rankings, noncompute positions unchanged, no original pending-list mutation and unknown-policy rejection. All full Java CI returns to SUCCESS after one newly added diagnostic logger lacked a `CondorVM` import; the failure was preserved and repaired at commit `49a8aaf`.
- Separate `-Ddagfla.priorityOpportunityTrace=true`: passive log emitted only when an IDLE VM has **2 or more COMPUTE jobs** released by the engine. Records original task-id chosen under FIFO vs priority, count of competing ready jobs, and whether the actual first dispatch choice changes. Tracing disabled by default.

## Frozen original pilot: reproducibility, real makespan and cost
- Preregistration before original outcomes: `docs/FLA_RUNTIME_PRIORITY_FROZEN_PILOT_2026-11-04.md`.
- **36 complete real WorkflowSim replays** on 3 previously known DAXs (`CyberShake_100`, `Montage_100`, `Sipht_60`) × 4 predetermined algorithm-independent VM assignment vectors (`all_vm0`, `all_vm12`, `round_robin`, `stride7`) × 3 priority modes (`fifo`, `shortest`, `upward`) with original VM speed profile and seed 509.
- Original [GitHub Actions 41679712071](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41679712071) **3/3 matrix jobs PASS**. Original Task ID/VM mapping identity and same fixed-genotype *planned* Makespan/Cost unchanged across runtime policies, so changed actual results cannot be attributed to different VM mapping or different planned evaluator. Historical original FIFO results for Montage and Sipht match archived [41669662253](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41669662253) within relative 1e-6.
- Independent read-only all-case [Actions 41680104295](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41680104295) PASS, verified every original objective pair and every delta. 36 simulator jobs yield only **24 alternative-policy-vs-FIFO comparisons** across **3 DAG instances**. Do not treat cases or task pairs as 36 independent workflow families.
- A >0.1% absolute makespan-effect screen is descriptive (not preregistered), retaining every original near-zero and harmful case. **3/24** comparisons crossed this practical-effect screen:
  - `Sipht_60 / stride7 / upward`: FIFO **9344.8895 s**, upward **10340.1855 s**, **+10.650698% WORSE**; real Cost **−0.001718%**.
  - `Sipht_60 / round_robin / upward`: FIFO **12066.8060 s**, upward **11902.1470 s**, **−1.364562% BETTER**; Cost **−0.000495%**.
  - `CyberShake_100 / round_robin / shortest`: FIFO **1604.8715 s**, shortest **1608.6715 s**, **+0.236779% WORSE**; Cost **−0.000011%**.
- The remaining **21/24** alternatives made ≤0.1% absolute Makespan difference. In particular, all Montage_100 cases changed at most **0.000284%** despite some ready-queue priority changes. No consistent "upward" or "shortest" policy superiority is supported.
- No true Hypervolume comparison is meaningful here because no new joint map+priority FLA or equal-encoding NSGA-II search has been developed.

## Independent actual dispatch-opportunity probe
- Pre-committed, explicitly post-outcome-selected explanatory protocol: `docs/FLA_PRIORITY_DISPATCH_OPPORTUNITY_PROTOCOL_2026-11-04.md`. Four cases were chosen **after seeing** the first pilot's gains/losses; they are not an unseen holdout.
- First run [41680518522](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41680518522) failed at Java compile because of missing import, **not** an experimental result; code corrected. Re-run [41680630820](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41680630820) **4/4 jobs PASS**, **12 actual simulator replays** (4 fixed DAG/mapping pairs × FIFO/shortest/upward); all 12 real Makespan/Cost outputs reproduced the uninstrumented original records within relative 1e-6. This validates that additional event tracing is passive.
- At idle-VM decision events, multiple already-released COMPUTE jobs were indeed competing:

| Frozen DAX / placement | FIFO multi-job VM opportunities | Shortest (opportunities / changed first choice) | Upward (opportunities / changed first choice) | Observed priority effect |
|---|---:|---:|---:|---|
| Sipht_60 / stride7 | 27 | 27 / 11 | **26 / 19** | Upward +10.650698% (harmful) |
| Sipht_60 / round_robin | 27 | 26 / 10 | **26 / 19** | Upward −1.364562% (helpful) |
| CyberShake_100 / round_robin | 15 | **13 / 10** | 17 / 7 | Shortest +0.236779% (harmful) |
| Montage_100 / stride7 | 28 | 28 / 19 | **28 / 18** | Both effects ~0 |

This rules out the simpler explanation "nothing actually changed in the runtime dispatch order." It also shows **changed dispatch decisions are necessary but not sufficient for improved final Makespan**; even 18/28 upward first-choice differences on Montage had nearly zero whole-workflow effect. These are simulator event counts, not independent samples or a causal decomposition of critical-path impacts.

## Scientific implications and next gate
1. First control dimension is **VM assignment**; the second is **priority of already-ready jobs competing at each idle VM**. Their interaction is real and DAG-specific, so an optimizer that controls BOTH is a plausible next research implementation target.
2. However, choosing "upward" or "shortest" after seeing each real simulator result is an **oracle** and cannot be sold as an optimizer. A fair planner must predict scheduling quality before seeing true replay outcomes. The existing `ReadyQueueScheduleEvaluator` uses original Task ID priority and does **not** yet predict upward/shortest runtime rules correctly.
3. Prior work already co-evolves task-priority and VM selection rules: e.g. *A cooperative coevolutionary genetic programming hyper-heuristic for multi-objective makespan and cost optimization in cloud workflow scheduling* (Computers & Operations Research, 2024, DOI: 10.1016/j.cor.2024.106805). Joint encoding alone is therefore **not** an established new Q1 contribution. A distinctive and reproducible search representation, prediction-uncertainty handling, or computation-aware Pareto mechanism would be necessary, and should be compared with contemporary rule-learning and NSGA-II baselines.
4. Before training a joint policy or adapting FLA, the next mandatory engineering gate is a **priority-aware, simulator-fidelity-validated decoder**, which predicts VM-ready selection under FIFO/SJF/upward, using only known DAX task lengths, parents and VM parameters (NO future true WorkflowSim labels). Measure same-mapping forecast error and ranking fidelity across other DAX families and VM speed regimes. If the decoder cannot predict the large ±10% task-priority effects, adding a priority gene to an optimizer will just optimize a false model.
5. After that gate, compare a *shared* priority+mapping representation and objective budget for FLA-v12 and seeded NSGA-II, include time-matched experiments, standard heuristics and a fully untouched holdout set with multiple seeds, actual HV and IGD+ reference disclosure, ablations and failure cases.

**Decision: keep default FIFO and original baseline; do NOT promote v18, dual-worst, upward or shortest policy as an algorithm improvement. Mechanistic feasibility is PROVEN on specific frozen assignments; an improved multi-objective scheduler is NOT.**
