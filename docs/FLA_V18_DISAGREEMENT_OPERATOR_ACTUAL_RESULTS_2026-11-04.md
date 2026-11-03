# FLA v18 disagreement-targeted relocation: complete first true simulator gate (2026-11-04)

**Scientific decision: do NOT promote v18. A mechanistically motivated FLA-specific operator has been implemented and exercised >1000 times per block, but its true Pareto-HV benefit does NOT generalize across the two tested DAGs.**

## Implementation and isolation
- `sources/org/workflowsim/planning/DAGParetoFLAPlanningAlgorithm.java` new opt-in `CONFIG_DISAGREEMENT_RELOCATION=false` default. Variant `v18-disagreement` evaluates stage-in insertion and ready-queue *planning* starts on an already proposed child genotype, chooses the eligible task with maximum disagreement, and reassigns it once to an alternative VM based on low local service/workload or low cost/workload subgroup. No actual WorkflowSim labels ever inform proposals. Probability **0.35**, locked before first run.
- `examples/org/workflowsim/examples/planning/FLAResearchExperiment.java` runs `v18-disagreement-three-arm` (FLA v12, FLA v18, seeded NSGA-II). Both FLA versions and NSGA-II use exactly the ORIGINAL stage-in-aware fitness; the model discrepancy is only an FLA candidate-proposal heuristic, NOT a decoder-objective replacement.
- The two extra model forecasts for proposal targeting are NOT counted as genotype objective evaluations, so computational cost parity is NOT established merely by 3030 counted objective calls. Wall time and number of activated proposals/actual gene moves must be reported.

## Frozen experiment and provenance
- Prior protocol `docs/FLA_V18_DISAGREEMENT_OPERATOR_FROZEN_PROTOCOL_2026-11-04.md`; two DAX instances CyberShake_50, Montage_50, seeds 211,212, same price/speed VM configuration, same first two deterministic cost seeds, population 30, generations 100, **3030 target objective calls per arm** and **K16 actual WorkflowSim replays per arm**.
- [Original 4×3-arm optimizer/simulator Actions 41674106990](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41674106990): 4/4 PASS; **192 true simulator replay calls**, 12 full search arms, 36,360 counted genotype objective evaluations. Original K16 selected using planned Pareto-cover only, before future simulator labels.
- [Independent actual true HV validation 41674276413](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41674276413): PASS; same 1.5×/3× normalized real-HV reference within each three-arm DAG/seed block; original full replay/archive CSVs and logs preserved.

## True normalized HV and operator actions

| DAX | Seed | FLA v12 | FLA v18 | Seeded NSGA-II | Δ v18−v12 | Search time ratio | Moves/proposals |
|---|---:|---:|---:|---:|---:|---:|---:|
| CyberShake_50 | 211 | 0.47534732 | 0.47523416 | 0.49258546 | −0.00011316 | 1.35× | 1063/1063 |
| CyberShake_50 | 212 | 0.44337975 | 0.43820795 | 0.44316917 | −0.00517180 | 1.02× | 1074/1074 |
| Montage_50 | 211 | 0.30465758 | 0.30919182 | 0.30219855 | +0.00453424 | 1.89× | 1062/1062 |
| Montage_50 | 212 | 0.28984442 | 0.29914528 | 0.27912496 | +0.00930086 | 1.74× | 1035/1035 |

- FLA v18 mean observed Δ normalized actual K16 HV **+0.00213753**, **2 wins / 2 losses**, mean search wall-time ratio **1.50×**.
- Signs all consistent under 3× reference-point sensitivity; Montage positive, CyberShake negative, and seeded NSGA-II bests/loses vary by case.
- The operator executed **4234 actual single-task relocations out of 4234 attempted proposals** across four runs. This proves the trigger was active, but also indicates lack of discrimination under this sample: every attempted target yielded a legal move. It does NOT prove those moves improved objectives.
- In both CyberShake blocks, original seeded NSGA-II HV was at least as good as FLA-v18; thus no general FLA advantage or robust superiority is demonstrated.

## Research decision and recommendations
1. **Reject v18 as a publication-ready standalone contribution.** DAG-dependent opposite signs demonstrate that maximizing disagreement alone is not a validated target for useful relocation. Do not tune 0.35, load coefficient or subgroup rule on these same four blocks and relabel them holdout.
2. Preserve the valuable original model-fidelity mechanism dataset (1176 Task IDs, event-ready and waiting decomposition) and cross-DAG negative controls, especially Montage/Sipht/CyberShake limitations.
3. Next proposal must state *why a predicted conflict is on the true critical path or Pareto frontier*, not just that the two predictors differ. Design and independently validate a risk/reward gating mechanism using only historical planned DAG/VM information, an explicit compute-budget matched baseline, multiple unseen instances, a reference-point sensitivity analysis and at least 20 independent seeds/workload blocks.
4. Do not claim Q1 readiness. Separate shared decoder innovation from true FLA-specific operator improvement. Existing evidence supports an excellent reproducibility/model-fidelity engineering study but NOT a proven superior multi-objective scheduler.
5. No changes to `master`, original FLA v12 default, or seeded NSGA-II default. v18, ready-only and dual-worst remain explicit opt-in research variants; full negative evidence is archived.

**Summary:** v18 true-HV effect is conditional and costly; retain code/test/logs as negative benchmark and move to a scientifically preregistered method rather than blind operator iteration.
