# Isolated ready-queue decoder: finished prediction and fair-search first gates (2026-11-03)

**Decision: keep decoder opt-in and retain the original FLA/NSGA-II defaults. The new predictor works and frequently reduces model error, but its use as an optimization objective has NOT shown stable true-HV improvement.**

## Implemented engineering
- `sources/org/workflowsim/planning/ReadyQueueScheduleEvaluator.java` is a separate, stateless per-assignment decoder. Tasks are released after their predicted parents finish, and an idle VM dispatches the first ready task by original DAX declaration Task ID. It estimates compute + stage-in and preserves per-evaluation VM cache isolation; no actual CloudSim labels are fed back.
- Hand-checked 4-task counterexample `ReadyQueueScheduleEvaluatorTest`: topological insertion predicts Makespan=21 versus ready queue=22, with an independently verifiable ready-order change; old stage-in regression passes.
- Optional read-only `-Ddagfla.readyQueueDiagnostic=true` enables same-genotype forecast comparison in `FLAFixedMappingReplay`, without replacing any optimizer's objectives.
- Optional **EXPLICIT search-research-only** `-Ddagfla.useReadyQueueObjective=true` selects the *same* ready-queue objective model for `FLAScheduleEvaluator` (FLA) and `NSGAIIPlanningAlgorithm` (seeded baseline). OFF by default. The old objective is preserved by default; no source changes to `master`.

## Gate A: two historical development DAGs, true real WorkflowSim predictions
- [Original real simulator Actions 41668888545](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41668888545): 16 real replays, source default K16 candidates, two speed profiles.
- [Read-only deduplicated physical genotype analysis 41669178910](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41669178910): 16 source-arm cases, **14 unique mapping/profile cases**, two duplicates across FLA-v12 and cost-seeded NSGA-II, zero inconsistencies.
- Makespan absolute percentage error (mean over 14 physical cases): **old 4.141608%, new 1.179256%**; **11 improved, 3 tied, 0 worse**.
- Mean absolute per-task start prediction error: **1036.218 s old, 71.568 s new**, 12 improved and 2 worsened; finish MAE **1035.913 s old, 71.568 s new**, 12 improved, 2 worsened.
- Mean absolute Cost percentage error **0.000568% for both**; this particular alternative did not materially improve the cost model.
- A difficult Epigenomics_46 staggered case still has ready-queue makespan error **16.113%**. No claim of universal accuracy.

## Gate B: three additional DAGs, algorithm-independent frozen assignments
[Original 24 real simulator replays 41669662253](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41669662253): `Inspiral_100`, `Montage_100`, `Sipht_60`; four prescribed genotypes `all_vm0`, `all_vm12`, `round_robin`, `stride7`, two VM-speed profiles, no FLA/NSGA-II optimization. Protocol frozen in `docs/FLA_READY_QUEUE_CROSS_DAG_PROTOCOL_2026-11-03.md`. These DAG families were seen in earlier wider studies and are NOT a fully untouched research-family holdout.

| DAG | VM speed | Old mean abs Makespan error | New mean abs Makespan error | Improved/tied/worse cases |
|---|---|---:|---:|---|
| Inspiral_100 | default | 1.531510% | 1.537543% | 0/3/1 |
| Inspiral_100 | staggered | 0.048518% | 0.005339% | 2/2/0 |
| Montage_100 | default | 0.066357% | 0.099081% | 0/3/1 |
| Montage_100 | staggered | 0.095427% | 0.095427% | 0/4/0 |
| Sipht_60 | default | 3.006075% | 0.005051% | 2/2/0 |
| Sipht_60 | staggered | 1.919081% | 0.005413% | 2/2/0 |

Across the 24 predeclared cases: **6 improved, 16 tied, 2 worsened**. Cost error remained nearly unchanged. Thus ready-queue semantics are promising for some DAG/mapping regimes but not a universal replacement.

## Gate C: FIRST true optimization, equal-budget two-solver decoder factorial
- Frozen in `docs/FLA_READY_QUEUE_SEARCH_FIRST_GATE_PROTOCOL_2026-11-03.md` before results.
- [Eight original full-optimizer blocks 41670356422](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41670356422): two known DAGs `Sipht_60`, `Montage_100`, two seeds 211,212, old/ready objective modes; each of 16 optimizer arms used **3030 counted evaluations**, the same two initial cost seeds for FLA and NSGA-II within each objective mode, and **K=16** actual WorkflowSim replays per arm. Original job checks passed.
- The first independent HV report [41670734127](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41670734127) **FAILED only in analysis provenance parsing** (the `DAG=... seed=... decoder=...` metadata were on one line); the source optimization and simulator jobs were successful. This failure was preserved and parsing corrected, without any new simulator computation or case removal.
- [Independent corrected true-HV analysis 41670859874](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41670859874) **SUCCESS**. Recomputed **normalized actual WorkflowSim HV** from all four solver/decoder arms in each DAG/seed block with **ONE common 1.5× reference**, and independently checked sensitivity to 3.0×. Run-local references are NOT compared across decoder modes.

| DAX | Seed | FLA old HV | FLA ready HV | FLA Δ | NSGA-II old HV | NSGA-II ready HV | NSGA Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sipht_60 | 211 | 0.26221438 | 0.26100357 | −0.00121082 | 0.26197084 | 0.26217421 | +0.00020337 |
| Sipht_60 | 212 | 0.24505747 | 0.24481377 | −0.00024370 | 0.24507731 | 0.24507435 | −0.00000297 |
| Montage_100 | 211 | 0.32229665 | 0.32599573 | +0.00369908 | 0.31673963 | 0.31626339 | −0.00047624 |
| Montage_100 | 212 | 0.31580432 | 0.31979273 | +0.00398841 | 0.32133120 | 0.32057240 | −0.00075880 |

**FLA's paired actual HV change:** mean +0.00155824; **2 wins / 2 losses**, mean search time ratio new/old = **1.10×**. **Seeded NSGA-II's paired actual HV change:** mean −0.00025866; **1 win / 3 losses**, mean search time ratio new/old = **1.00×**. These are descriptive **four-block** results, NOT statistical significance or cross-family generalization.

## Scientific decision

1. **Do not promote the alternative decoder as the default FLA search objective** based on this evidence; the 2/2 split for FLA is inconsistent, and a shared decoder is not an FLA-specific search-operator innovation.
2. The code and tests provide reproducible, useful model-fidelity engineering evidence. A *new publishable algorithm* still requires either a better validated ready/event model plus a robust search mechanism or a separate genuinely new multi-objective search contribution.
3. Follow-up must keep strict reference-point parity, K replay selection transparency, equal optimizer budgets and independent seeds, report runtime effects and negative DAG cases, and distinguish true K16 front HV from the full unknown simulator Pareto front.
4. Do not use the two selected DAXs and seeds to tune a new model and then call the same records holdout. A new proposal must be preregistered and tested on fresh instances / randomized but fixed work assignments, with cross-DAG / multiple VM regimes.

**What can be claimed now:** under some fixed mappings, ready-queue decoding predicts WorkflowSim makespan and task timelines much better than topological insertion; however, replacing the search objective has not established stable improvement in FLA's true multi-objective quality. No Q1 publication-ready advantage is demonstrated.

**Repository status:** only `fla-baseline` was modified; `master` remains untouched.
