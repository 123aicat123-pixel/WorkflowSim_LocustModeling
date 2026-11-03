# Fixed-assignment default/staggered WorkflowSim paired pilot (locked before new replay)

**Status on creation:** prospective development pilot specification; no new replay outcomes inspected.

## Motivation
Read-only v17 K16 original-artifact audit Actions 41652078831 loaded 1792 archived replay rows and found **zero** exact task-to-VM mapping overlaps between the default and staggered VM-speed profiles in each matching DAG, optimizer seed, and algorithm. That audit correctly made no causal cross-speed claim. To study VM-speed effects, freeze original default-profile K16 assignments and replay each *identical genotype* under both profiles, rather than rerunning an optimizer separately.

## Frozen input and cases
- Source: original v17 four-arm confirmation Actions 41626382711; no synthetic results needed in this pilot.
- Workflow families/instances: `Epigenomics_46` and `CyberShake_100`.
- Optimizer seed: **211**, source profile **default** only.
- Source optimizer arms: `DAG-Pareto-FLA[v12-hvbandit]` and `NSGA-II[costseed]`.
- Candidate indices: **1,2,3,4** as originally ordered in each source arm's default K16 replay CSV. This is 2 families × 2 arms × 4 genotypes = **16 selected original assignment identities**; each receives exactly two fresh real simulator replays (32 replay calls).
- Profiles: `default` and `staggered`, identical VM IDs, tier prices, storage, host parameters, CloudSim seed and source DAX. Only the documented VM MIPS profile changes.
- Source values, selected candidate order and VM mapping must remain immutable. If the original row or source assignment is missing, reject; no replacement based on outcome.

## Primary engineering validation and descriptive outcome
1. For every replay, independently reconstruct the original task-id -> VM-id assignment and assert it exactly equals the simulator's final assignment (fail closed on mismatch).
2. For default-profile replays, assert makespan/cost and independent planning objectives equal the originally archived default-profile replay values within relative tolerance 1e-6 (necessary historical reproducibility gate).
3. Pair default vs staggered by exact (workflow, seed, algorithm, candidate index, mapping); require 16 valid pairs and 32 actual simulator calls, zero missing pairs or duplicate mappings. Verify different optimizer arm assignments aren't treated as statistically independent new workflow families.
4. Primary descriptive metrics: mean paired actual makespan change in %, mean paired planned makespan change in %, and mean absolute planned-minus-actual speed-effect discrepancy (percentage points). Report signed and absolute errors separately, per DAG and arm, and retain ALL cases, including contradictions and negative changes.
5. Confirm actual cost difference and reference integrity; do not force the actual makespan to increase or decrease under staggering because scheduling/order/transfer effects may interact with VM MIPS.
6. Preserve full raw stdout, original run ID, source commit, 16 pairs, source replays, and complete output CSVs. Use separately executed independent WorkflowSim calls, not counterfactual predictions.

## Limitations
Development instances and seed were chosen after other family effects were previously observed. This is a diagnostic fixed-mapping study, **not independent publication holdout**. Paired VM-speed profiles do not control differences in task execution order or host contention and should not be used to infer a single physical cause. Two DAGs/one seed cannot establish algorithm superiority, significance, or Q1 readiness. Search optimization budgets do not apply to these pure fixed-mapping replays; never present these 32 simulator calls as equal 3030-call FLA/NSGA-II search comparisons. Keep `master` untouched, do not modify source optimizer or defaults.
