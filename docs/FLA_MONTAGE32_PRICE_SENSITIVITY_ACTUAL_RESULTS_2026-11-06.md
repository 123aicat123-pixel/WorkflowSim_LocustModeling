# Montage32 synthetic VM-price sensitivity: verified source outcomes (2026-11-06)

**RESULT: 256 genuine WorkflowSim true fixed-map replays, 8/8 scenario source jobs plus independent exact K1–K4 audit successful. READY improves actual K4 normalized hypervolume in 2/8 blocks, ties in 6/8, negative in 0/8. These are dependent deterministic stress regimes, NOT random replications or evidence of statistical significance.**

## Frozen record and original source provenance

- Frozen before new labels: `docs/FLA_MONTAGE32_PRICE_SENSITIVITY_FROZEN_2026-11-06.md`, commit `acd33d07b4d5d09293f779fc9657115fada1cfbf`.
- Audit script commit `ee6afe889eba4bb39173c8e0f08cdb79d436500e`; frozen original source and workflow commit `5a44bd97790b610470d8c68b2c677c81b0856cd4`.
- [Original 9/9 successful Github Actions run 42189705116](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42189705116). Eight unique frozen matrices of Montage_50/Montage_100 × VM speed default/staggered × synthetic VM pricing linear/convex; each has 32 original simulator physical TaskID→VMID maps (not independent seeds). Simulator seed remains 1501 as metadata; changing it would NOT create a randomized independent physical mapping here.
- Audit preserves all eight original raw artifacts (with source trace and metadata), distinct 32 physical mapping identities per block, strict immutable protocol hash, one shared actual HV reference/block, actual simulator metrics, exhaustive hindsight true K1–K4 oracle, forecast-only OLD/READY selected physical K1–K4 prefixes, signed decision outcomes and adverse outcomes.

## Realized K4 comparison by precommitted scenario

| DAG | VM speed | Synthetic VM price | True Pareto maps out of 32 | Physically different K4 sets? | OLD true K4 regret | READY true K4 regret | READY − OLD normalized true HV |
|---|---|---|---:|---|---:|---:|---:|
| Montage_100 | default | convex | 13 | No | 0 | 0 | 0 |
| Montage_100 | default | linear | 7 | No | 0.000012166 | 0.000012166 | 0 |
| Montage_100 | staggered | convex | 13 | No | 0.001774903 | 0.001774903 | 0 |
| Montage_100 | staggered | linear | 10 | No | 0 | 0 | 0 |
| Montage_50 | default | convex | 13 | No | 0.001860390 | 0.001860390 | 0 |
| Montage_50 | default | linear | 8 | No | 0 | 0 | 0 |
| **Montage_50** | **staggered** | **convex** | **14** | **Yes** | **0.003007570** | **0.002278296** | **+0.000729274** |
| **Montage_50** | **staggered** | **linear** | **7** | **Yes** | **0.000554899** | **0** | **+0.000554899** |

Mean K4 OLD true regret = **0.000901241**, READY = **0.000740719**, mean READY−OLD true HV = **+0.000160522** across 8 descriptive conditions. These are not independent stochastic trials, and the mean is a descriptive summary only.

## Budgeted decision audit

| K | Physically different OLD and READY sets | Mean OLD actual regret | Mean READY actual regret | Mean READY−OLD true HV |
|---:|---:|---:|---:|---:|
| 1 | 1/8 | 0.000102788 | 0.000070045 | +0.000032743 |
| 2 | 1/8 | 0.000099263 | 0.000030909 | +0.000068353 |
| 3 | 1/8 | 0.000935547 | 0.000867194 | +0.000068353 |
| 4 | 2/8 | 0.000901241 | 0.000740719 | +0.000160522 |

## Interpretation and required next gate

The previous default-price exploratory Montage_50/staggered K4 READY benefit of +0.000867221 also persisted in sign under **both** precommitted synthetic-price models (+0.000554899 linear, +0.000729274 convex). This supports *conditional decision sensitivity to VM-speed heterogeneity*; it does not establish 3 independently replicated successes or a full new FLA optimizer. The other six K4 blocks tie. True Pareto cardinalities are 7–14 in several regimes, so not all K4 sets saturate the full true front; the observed lack of decision divergence in those blocks remains informative.

Crucially, the fixed 32-map source runner inserts one externally supplied genotype, sets population size=1 and generation count=0; `LIWSAPlanningAlgorithm.initializePopulation` fills no additional random candidates. Randomizing the nominal optimizer seed would be **pseudoreplication**, not new uncertainty. New evidence should manipulate real factors (structure, VM speed distribution, queue contention, costs) with frozen protocols and no result-selected configurations; for publication-level algorithm superiority, include genuine full search runs and fair objective-evaluation/time budgets vs NSGA-II and other methods.

**Do not tune maps or predictive scores to these now-seen actual labels. Do not claim SCI-level method superiority. Preserve all positive, null and negative information.** All changes remain on `fla-baseline`; `master` unchanged.
