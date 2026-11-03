# Frozen same-genotype VM speed research pilot — actual simulator results (2026-11-03)

**Status: completed original 32 real WorkflowSim replay calls; both jobs PASS, independent read-only 16-pair audit PASS.** Engineering and mechanistic pilot, **not** a new optimizer algorithm improvement. Original default optimizer/policy unchanged, `master` untouched.

## Immutable execution and quality checks

- Original preregistration: `docs/FLA_FIXED_MAPPING_VM_SPEED_PILOT_PROTOCOL_2026-11-03.md`, committed before any 32-call result was seen.
- First attempt [41652723759](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41652723759) FAILED because artifact download pattern was ordered incorrectly, BEFORE simulator replay. It was fixed without changing the frozen experiment cases, inputs, assignments, or outcomes.
- Successful original real simulator [41652845071](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41652845071), source SHA `0efae669dc03402ea7fc4399348eb70ac6767428`, two PASS matrix jobs and preserved CSV/log artifacts `fixed-speed-Epigenomics_46-41652845071` (artifact ID `13237009851`) and `fixed-speed-CyberShake_100-41652845071`. Java rebuilt fresh from the source tree.
- Source original default-profile archived v17 K16 candidates: [41626382711](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41626382711), seed 211. Two existing scientific workflow instances `Epigenomics_46` and `CyberShake_100`; source arms `DAG-Pareto-FLA[v12-hvbandit]` and `NSGA-II[costseed]`; first 4 archive-selected K16 original assignments for each arm. Total 2 DAGs × 2 arms × 4 unique source assignments = 16 matched pairs, **32 new true simulator replays**.
- Every new simulator replay checked original task→VM assignment identity. All **16 default-profile** replays asserted exact reproduction of prior archived planned and simulator makespan/cost within relative tolerance `1e-6`. This distinguishes actual independently rerun fidelity from mere anticipated matching.
- Read-only reanalysis from actual original job artifact CSVs: [41653086817](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41653086817), exactly 16 pair rows; did NOT run new simulator or optimizer. Complete all-pair CSV and markdown output retained.

## Main matched within-genotype result

For a fixed genotype, change is `100*(staggered/default - 1)` for planned makespan and separately actual WorkflowSim makespan. Gap in **percentage points** = planned percent change minus actual percent change. Mean absolute gap is the mean ABSOLUTE individual gap across the four original assignments, not absolute of the two cohort means.

| DAG | Original assignment source | Mean planned makespan change | Mean actual makespan change | Mean abs gap | Largest abs gap |
|---|---|---:|---:|---:|---:|
| Epigenomics_46 | v12 FLA | +53.22188% | +52.06310% | 1.15879 pp | 4.61721 pp |
| Epigenomics_46 | seeded NSGA-II | +45.54826% | +45.40419% | 0.20343 pp | 0.69432 pp |
| CyberShake_100 | v12 FLA | +35.81081% | +35.37151% | 1.90469 pp | 4.68797 pp |
| CyberShake_100 | seeded NSGA-II | +33.62781% | +34.55894% | 1.17982 pp | 3.55396 pp |

Across the eight v12-sourced mapping pairs, signed gap = **+0.79904 pp**, mean absolute gap = **1.53174 pp**. Across the eight NSGA-II-sourced pairs, signed gap = **−0.39353 pp**, mean absolute gap = **0.69163 pp**. These genotype sets were *selected* by different optimizers, not the same cross-optimizer mappings; do not call this an intrinsic algorithm causal comparison.

Large positive/negative signed gap examples:
- CyberShake_100 v12 candidate 4: planned makespan change +33.82995%, actual +29.14198%, **+4.68797 pp** gap.
- Epigenomics_46 v12 candidate 1: planned +51.70641%, actual +47.08920%, **+4.61721 pp** gap.
- CyberShake_100 seeded NSGA-II candidate 4: planned +26.63517%, actual +30.18913%, **−3.55396 pp** gap.
- CyberShake_100 v12 candidate 1: planned +35.61708%, actual +37.76396%, **−2.14688 pp** gap.

These signs show that a single global additive or multiplicative bias parameter is not justified by this sample. No statistical claim is made about larger error for FLA.

## Why this is scientifically different from the earlier audit

[Earlier read-only 1792-record audit 41652078831](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41652078831) had **zero identical selected assignments** between the two separately optimized VM-speed profile K16 sets, so their differences mixed assignment selection and VM profile effects. The new experiment **froze the same mapping first**, then independently simulated under both speed configurations, enabling a legitimate *fixed-mapping conditional* profile comparison.

## Interpretation, limitations, next research gate

- Results support a **measurable mismatch in model-predicted versus simulator-observed sensitivity** to VM speed for particular frozen assignments, with both signed directions.
- They do not isolate the internal physical or scheduling cause: VM speed may change job ordering, resource contention, stage-in timing, transfers and caching under the same mapping.
- Only two already-explored real DAG instances, one seed, and four selected candidates per optimizer. The two source arms might share some exact mappings; they must not be counted as independent family replicates. All scenarios were selected from default planned K16, not randomly from the entire 3030 candidate history.
- **Next required experiment** (new protocol before outcomes): sample identical fixed assignments *independent of algorithm* from an evaluation-history or deterministic uniformly generated genotype pool; execute both VM speed profiles under identical replay conditions, stratify by workflow DAG topology and degree of resource heterogeneity, preserve individual task timelines and stage-in costs to localize why the plan/real speed effect gap varies.
- Do not change current v12 default, install an unvalidated global makespan correction, or claim an FLA optimizer improvement. A paper-level innovation requires frozen correction/selection mechanism and prospective unseen DAG-family comparison with equal optimizer/simulator budgets, more seeds and explicit family-cluster uncertainty.

**Decision:** fixed-genotype paired simulation harness is validated. Planning-model sensitivity mismatch exists for specific schedules, but algorithm superiority and remediation remain unproven.
