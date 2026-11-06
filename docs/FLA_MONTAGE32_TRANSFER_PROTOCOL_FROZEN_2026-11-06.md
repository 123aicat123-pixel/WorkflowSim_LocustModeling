# Frozen Montage-family transfer gate for independent 32-map OLD vs READY selection (2026-11-06)

**Pre-registration stage; freeze before any new Montage 32-map truth replay.** This is a *new cohort for the fixed-32 physical mapping audit*, **not** a project-wide untouched DAG family: Montage has been explored elsewhere in this repository. The earlier 256 rows (Inspiral/Sipht/Epigenomics/CyberShake) remain unchanged; no method is tuned against their observed truth labels here.

## Prospective, falsifiable question
Does OLD-vs-READY forecast disagreement on an independently fixed mapping universe become an **actual difference in selected physical TaskID-to-VMID mappings** on a different DAG family? If so, does the realized paired normalized true-HV regret improve? If decisions are identical, no model superiority claim is allowed even when error metrics improve.

## Fixed independent simulator trial
- Workflow families: **Montage_50** and **Montage_100** (separate DAG sizes; same Montage family).
- VM speed profiles: **default** and **staggered**; one original WorkflowSim seed **1501**. Four independent block identifiers (not four statistically independent families or seeds).
- Each block contains all **32 immutable fixed mapping rules** as implemented by `FLAFixedMappingUniverse32.FROZEN_POLICIES` at SHA `40ff418db2589f4a8118ba77b44dc7a4bef1ca21`, yielding **128 expected genuine original WorkflowSim observations**.
- Flags: `workflowsim.planningStageInAware=true`, `dagfla.readyQueueDiagnostic=true`, `dagfla.fixedTaskTrace=true`, `dagfla.fixedVmReadyPriority=fifo`. No FLA, NSGA-II or optimized proposal mechanism generates mappings. No actual label can influence the fixed mappings.
- Original source runner checks one unique physical assignment per policy, exactly matching planned and simulator per-task TaskID→VMID, recorded start/finish timelines, finite objectives and nonempty source logs. Fail closed rather than replace missing or duplicate outcomes.
- Holdout reuse is limited: same source implementation and 32 rules as original; Montage family was used in previous experiments. This is **not** a new method, full randomized study or publication-quality generalization proof.

## Selection and reference are frozen
- Separate OLD and READY greedy marginal HV selection at K = 1, 2, 3, 4; each predictor uses only its 32 predictions and reference point `(1.5 * max predicted makespan + 1e-6, 1.5 * max predicted cost + 1e-6)`.
- Tie break: lower predicted normalized scalar sum, then lexicographic policy name.
- Realized true outcomes: both selections scored against identical per-block true reference `(1.5 * max actual makespan + 1e-6, 1.5 * max actual cost + 1e-6)`. Report actual selected HV, exact hindsight K1..K4 oracle, per-K regret, physical-prefix set differences, true Pareto count, K4 ties/saturation and first-four blind control. Oracle never selects candidate mappings.
- 32-choice exact K4 oracle enumerates C(32,4) = **35,960** combinations per block, with no surrogate labels.
- Primary gate: any different OLD/READY physical selected K1-K4 prefix among four blocks, followed by true paired regret effect. A K1-K4 same-decision null is preserved unmodified.
- No a-posteriori selection of Montage size, mapping, seed, VM speed, cost coefficient or evaluation metric after seeing realized labels. A positive finding is only exploratory and must replicate on new, truly untouched families/synthetic structural variants and 20+ blocked seeds with real runtime and literature baselines; a null remains null.
- Save source artifacts/logs, protocol SHA, branch SHA, all 128 rows, audit CSV and full K1–K4 summary. Preserve adverse results and declare missing outcomes rather than infer success.

**Changes only to `fla-baseline`; `master` remains unchanged.**
