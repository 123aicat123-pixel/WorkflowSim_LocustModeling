# v16 FLA Bandit-opportunity sham local-pair negative-control development experiment — 2026-11-03

**Status: complete, 8/8 real WorkflowSim six-arm scenario jobs and aggregate report successful.** v16 is a **scientific negative control**, not a candidate scheduling algorithm and not a FLA baseline upgrade. Default settings unchanged; `master` unchanged.

## Immutable evidence

- Implementation source: [acfa8a633f32b83b7b725a57c8ec9c74dc2e2c07](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/commit/acfa8a633f32b83b7b725a57c8ec9c74dc2e2c07).
- Pilot and frozen aggregation: [b890475aa1d162478ec420e79d740828a856e11c](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/commit/b890475aa1d162478ec420e79d740828a856e11c).
- [Successful GitHub Actions run 41623075676](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41623075676): all eight matched six-arm experimental jobs and the final report job succeeded. Aggregate artifact `fla-v16-report-41623075676`, artifact ID `13225350133`, with case-level CSV, textual analysis, and raw logs; original eight job artifacts hold each solver's K16 true simulator outcomes, full history fingerprint, 101 generation snapshots and source SHA.
- Separate FLA Java CI passed against the new v16 implementation at [41622855624](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41622855624).

## Frozen setup and controls

Two previously studied DAG families `Montage_25`, `CyberShake_30` × default/staggered VM speed × two newly chosen optimizer seeds 181/182: **eight blocks**. Six arms in every block:

1. v12-hvbandit, 30 normal FLA child evaluations per generation.
2. v16-shamrandom, 16 normal +14 **counted uninformative duplicate** child evaluations; neighbor proposal consumes random-control path but neighbor itself is discarded.
3. v14-randompair, 16 normal +14 counted **actual random neighbor** evaluations.
4. v16-shamtimeline, 16 normal +14 counted uninformative duplicate child evaluations; proposed timeline neighbor discarded.
5. v14-timelinepair, 16 normal +14 counted **actual timeline neighbor** evaluations.
6. Identically cost-seeded NSGA-II.

All six arms use the exact first two deterministic seeded assignments, **3030** counted stage-in-aware PLANNING objective evaluations total, and **16** true WorkflowSim replays on unique plans via unchanged planned Pareto-cover selection. Same numerical budget does not entail equal useful information, which is the experimental mechanism under study. Original v12 has 3000 phase-bandit opportunities after 30 initial evaluations; each paired variant has **1600** such normal-child bandit opportunities +1400 local/sham evaluation calls.

The sham versions deliberately evaluate a copy of the preceding normal child a second time and verify that planned makespan/cost are equal. Each duplicate is still a real target evaluator call, counted by the source evaluation counter and recorder. Sham does NOT fabricate free fitness or retrieve an evaluation from cache. Sham does run neighbor proposal and novelty-repair pathways before discarding it; this can still alter RNG consumption and visited-set state. The experiment therefore does **not** isolate bandit credit alone, and matched stochastic trajectories are not guaranteed.

The common HV reference was predeclared for each DAG+speed as 1.5× the coordinatewise maximum of the **PLANNED** replayed objective values over all six arms and both seeds +1, with 3× reference sensitivity. Every actual simulator score is inside both; no simulator outcomes were used to tune a reference. Interpret 3× only as sensitivity, not as independent replications.

## Primary 1.5× true-simulator HV comparisons, mean of two seeds per DAG/speed

| Workflow | VM | Sham random vs v12 | Active random vs sham random | Sham timeline vs v12 | Active timeline vs sham timeline | Active timeline vs v12 | Active timeline vs seeded NSGA-II |
|---|---|---:|---:|---:|---:|---:|
| Montage_25 | default | −1.0393% | +0.7047% | −1.0504% | +0.5626% | −0.4935% | +0.4662% |
| Montage_25 | staggered | −0.8262% | +3.0909% | +1.2276% | −2.8006% | −1.6605% | −1.6538% |
| CyberShake_30 | default | −0.1059% | +1.0578% | +0.7611% | −0.5703% | +0.1800% | −0.9804% |
| CyberShake_30 | staggered | −0.9610% | −0.0120% | −2.0142% | +0.0398% | −1.9793% | −2.2216% |

Pooled **eight paired blocks** primary:

| Comparison | Mean HV difference |
|---|---:|
| Sham random vs v12 | **−0.733111%** |
| Sham timeline vs v12 | **−0.268977%** |
| Actual random neighbor vs sham random | **+1.210328%**, 7/8 wins |
| Actual timeline neighbor vs sham timeline | **−0.692116%**, 5/8 wins |
| Actual timeline neighbor vs v12 | **−0.988334%** |
| Actual timeline neighbor vs seeded NSGA-II | **−1.097386%** |

Secondary reference 3×: shamrandom vs v12 −0.252721%, shamtimeline vs v12 −0.108551%, actual random vs sham +0.441002%, actual timeline vs sham −0.324112%, actual timeline vs v12 −0.440021%, actual timeline vs NSGA-II −0.533523%. The negative primary result remains.

**Individual negative cases are material:** Montage_25 staggered seed 182, actual timeline versus its shamtimeline control **−6.9224%** despite both having the same 16+14 split; actual timeline versus v12 **−4.5812%**, versus NSGA-II **−3.6431%**. Conversely, Montage_25 default seeds 181/182, actual timeline versus the timeline sham showed +0.6626% and +0.4627%, so conclusions must be family/VM/seed-aware.

## What is and is not established

- **Supported (descriptive):** allocating 14 of 30 evaluation opportunities to uninformative duplicate proposals tended to reduce actual K16 HV relative to the normal v12, consistent with useful exploration bandwidth being lost. However, the cost is not monotone: in some configurations a sham did better than v12. That alone falsifies an unconditional opportunity-count explanation.
- **Supported (descriptive):** random genuine neighbor search improved K16 HV over its uninformative sham in seven of eight blocks, suggesting that neighborhood information can be useful relative to wasted proposals.
- **Not supported:** a general claim that timeline-guided one-gene local search beats random search, original v12, or seeded NSGA-II. It underperformed the shamtimeline control on mean true HV and underperformed v12 and NSGA-II.
- **Not identified:** separate causal contributions of phase-bandit feedback count versus independent normal offspring breadth; the sham removes both. Random-state consumption, neighborhood proposal discarded by the sham, novelty-set changes, and diverging search trajectories also mean this is not an exact single-factor causal ablation.
- **Not demonstrated:** an objective-space improvement from greater genotype Hamming diversity; the latter is a structural distance metric, not a Pareto quality metric.

These are **development** experiments with two seeds and previously examined workflows, not an untouched Q1 journal holdout. Keep v12 as principal research candidate, leave v14/v15/v16 off-by-default, and avoid retuning thresholds on this repeatedly observed corpus as if it were independent validation.

## Recommended next stage

Before adding another optimization heuristic, undertake a read-only mechanistic audit from the archived generation diagnostics, comparing sham versus actual neighbor per-generation archive admission counts and genotype diversity, and explaining which inference is actually possible. For a genuinely independent causal study, use an explicit preregistered factorial where a fixed stream of candidate proposals is shared as much as feasible and bandit updates are selectively replayed or disabled, with strict accounting of RNG state and fitness calls. Any new proposed improved FLA must eventually be verified on *unseen workflow DAG families* and independent VM settings with enough replications and real WorkflowSim outcomes.
