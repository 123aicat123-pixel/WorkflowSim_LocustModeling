# Full-search OLD/READY source K8 overlap and exact selected-union identifiability: audited results (2026-11-06)

**STATUS: source identity PASS, 256 original historical simulator replay rows PASS, 8 original block references and true ΔHV reconstructed, all 16 exact selected-union K8 oracles PASS. Retrospective mechanistic diagnosis only: NO NEW REAL SIMULATOR LABELS, NO algorithm improvement claim.**

## Exact provenance
- Frozen read-only analysis plan: `docs/FLA_MONTAGE_FULLSEARCH_CROSSARM_IDENTIFIABILITY_PROTOCOL_2026-11-06.md`, commit `6d040abbb884c9f3c46a404b2a3c0f29a2419318`.
- Audit implementation: `scripts/fla_montage_fullsearch_crossarm_identifiability_audit.py`, commit `6719bf83b3315f4651694a04fdeaaf0933674e2b`.
- Audited CI implementation: `.github/workflows/fla-fullsearch-crossarm-readonly.yml`, commit `95ae8447fa3e91b61ee83e2de8d7bba86b7915f3`.
- [Original real full-search WorkflowSim source 42190857445](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42190857445), immutable source SHA `a3e4292b6cfdcb20698d7ea9bbe6829d122cde5a`: 16 original source jobs, 32 separate 3030-visit search arms, eight simulator-labeled maps per arm = 256 historical real rows.
- [Strict read-only independent audit 42192092799 SUCCESS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42192092799): downloaded all 16 original source artifacts (not only their prior summary), verified source SHA and historical frozen protocol blob, original summary evaluator counts and 8 valid real replays/arm, exact task-to-VM mapping identities, source label agreement when a mapping repeats in a block, and original four-arm shared actual HV results against the historical independently archived ΔHV (1e-8 tolerance).
- Every historical DAG/VM-speed/seed block has 4 algorithm×decoder arms and a shared actual 1.5x reference. Separate retrospective exact K8 hindsight oracles use only the at-most-16 actual-labeled OLD+READY selected mappings **within one solver**, never to choose original candidates.

## Exact real K8 selected physical map overlaps and hindsight union-oracle regrets

| DAG | Speed | Seed | Solver | Shared physical K8 maps | Actual union ND | OLD hindsight K8 regret | READY hindsight K8 regret | READY−OLD true HV |
|---|---|---:|---|---:|---:|---:|---:|---:|
| Montage_50 | default | 1601 | FLA | 1/8 | 11 | 0.005144315 | 0.000081750 | +0.005062565 |
| Montage_50 | default | 1601 | NSGA | 1/8 | 9 | 0.000050193 | 0.004053872 | −0.004003679 |
| Montage_50 | default | 1602 | FLA | 1/8 | 11 | 0.000301755 | 0.000401642 | −0.000099887 |
| Montage_50 | default | 1602 | NSGA | 1/8 | 12 | 0.001109171 | 0.000218665 | +0.000890506 |
| Montage_50 | staggered | 1601 | FLA | 1/8 | 12 | 0.005720621 | 0 | +0.005720621 |
| Montage_50 | staggered | 1601 | NSGA | 1/8 | 12 | 0.000215027 | 0.004447297 | −0.004232270 |
| Montage_50 | staggered | 1602 | FLA | 1/8 | 13 | 0.007364009 | 0.000716136 | +0.006647873 |
| Montage_50 | staggered | 1602 | NSGA | 1/8 | 12 | 0.020350575 | 0.001913407 | +0.018437168 |
| Montage_100 | default | 1601 | FLA | 1/8 | 12 | 0.022934216 | 0.000009051 | +0.022925165 |
| Montage_100 | default | 1601 | NSGA | 1/8 | 12 | 0.000212893 | 0.004072825 | −0.003859932 |
| Montage_100 | default | 1602 | FLA | 1/8 | 8 | 0.011432001 | 0 | +0.011432001 |
| Montage_100 | default | 1602 | NSGA | 1/8 | 9 | 0.002308234 | 0.000006047 | +0.002302186 |
| **Montage_100** | **staggered** | **1601** | **FLA** | **1/8** | **14** | **0.000839452** | **0.034243898** | **−0.033404446** |
| Montage_100 | staggered | 1601 | NSGA | 1/8 | 15 | 0.004373166 | 0.000245692 | +0.004127474 |
| Montage_100 | staggered | 1602 | FLA | 1/8 | 11 | 0.003452987 | 0.006454948 | −0.003001961 |
| Montage_100 | staggered | 1602 | NSGA | 1/8 | 14 | 0.005551434 | 0.000191703 | +0.005359731 |

## Mechanistic interpretation and limits
- The selected physical K8 overlap is consistently **1 of 8** for both solvers in all eight source blocks, indicating that objective mode changes are accompanied by materially different *selected* real replay sets. **This does not itself prove which stage caused the difference:** each objective produced a different search trajectory and the final planned-only selection changed too.
- The worst historical FLA case, Montage_100/staggered/1601, contains **15 unique** OLD+READY selected physical mappings, **14 true nondominated**, and exact 15-map-union K8 hindsight oracle HV **0.345916490**. OLD regret is **0.000839452**, READY regret **0.034243898**, while READY has lower selected-set makespan MAPE (**0.2179%** vs OLD **0.5327%**), computed on DIFFERENT genotypes. This underscores that a lower selected-set forecast MAPE does not establish better optimization outcomes.
- Oracle is a retrospective finite selected-union ceiling; it **does not** know all 3030 visited candidate true outcomes or the entire feasible scheduling front, and never affected original FLA/NSGA searches. There are too few independent DAG families and seeds for publication-grade inference. Reporting each K8 mapping or task as an independent statistical replicate would be pseudoreplication.
- Data integrity, source log and historical reference parity passed; this is **diagnostic success**, not algorithm efficacy.

## Next independent causal gate (NOT executed by this audit)
Pre-register a frozen search-history pool test, export candidate snapshots and predicted OLD+READY scores for the exact **same physical genotypes**, and apply blind K8 selection independently under each predictor (no simulator oracle before selection). Contrast (A) fixed candidate-pool predictor effect against (B) separate objective-driven FLA evolution with full actual K8 replays. Include a random K8 sham and equal model compute budgets; preserve negative signs and replay identity. Existing historical true K8 records can support design, but cannot be promoted to new validation. A novel reliable gate needs genuine unseen DAG structures, multiple search seeds and equal compute-time comparisons before claiming superiority.

**Keep READY OFF by default. Do not overwrite historical evidence. All changes on `fla-baseline`; `master` unchanged.**
