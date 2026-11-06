# Genuine FLA OLD/READY-source visited64 factorial: audited original physical WorkflowSim outcomes (2026-11-06)

**VERDICT: both source simulator runs PASS; both independent actual-HV audits PASS; four-arm joint-reference cross-source audit PASS. Candidate-source effect is substantially larger than terminal predictor-selection effect on these sampled, familiar Montage developmental regimes, but results are mixed (6 wins / 2 losses) and do NOT demonstrate a robust new algorithm.**

## Original reproducibility chain
- OLD-FLA pool64 pre-outcome protocol: `docs/FLA_VISITEDPOOL64_DUAL_K8_FROZEN_2026-11-06.md`, commit `22c8c57c234532b251bee075fca8cecf9d3a9e2d`.
- OLD full original [source + exact audit run 42195625222 — PASS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42195625222), source commit `7a0dba36a84e367be45c891eedd44dd629083455`. Eight ordinary original OLD-fitness FLA-v12 search runs, 3030 actual genotype evaluations per run, 64 unique randomly sampled visited TaskID→VMID mappings × eight = **512 original true FIFO WorkflowSim outcomes**. OLD/READY read-only predictions are frozen before source simulator truth for every identical pool.
- READY follow-up protocol frozen after OLD results were seen but BEFORE READY true labels: `docs/FLA_READY_SOURCE_VISITEDPOOL64_FROZEN_2026-11-06.md`, commit `1a5f5f33d80a8d0eba1d62d86f71e7483ad683ae`. New isolated READY fitness mode at `f81ea7c22bc55a43c2ee5bd371a1597310edfa01`; no change to default FLA.
- READY full original [source + first audit run 42196301442 — PASS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42196301442), source commit `1209a4ba790ba4d9e81a15bd9edaef1a05688b49`. Eight original READY-fitness FLA-v12 full 3030-visit evolution searches, matching DAG/speed/seeds to OLD source, and **512 additional original FIFO true simulator outcomes**, same 64-unique-map sampling and original per-task mapping checks.
- READY first audit's reporting label incorrectly displayed `OLD` due calling the generic source-kind default (data were still from READY-fitness source and numerically audited). The independently fixed, strictly **read-only** [READY source-labeled audit 42196730694 — PASS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42196730694) uses the intended `fla_ready_source_visitedpool64_audit.py` wrapper and only reuses original READY source artifacts. No Java or physical truth change.
- Cross-source [four-arm common-reference independent audit 42196764123 — PASS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42196764123), script `scripts/fla_visitedpool64_cross_source_factorial_audit.py`, commit `a26f5c48a29b69cd27977a3fa327de127ecb32ed`; immutable 16 source artifact archives and two independent protocol hashes plus 8 matched DAG/speed/seed block identities, 64 complete distinct mapping identities per source per block and **1024 original true simulator outcome rows**, double-checked identical original true objectives for a mapping if it appeared in both sources. Each quartet uses ONE shared actual normalized HV reference computed from the union of both physical 64-map pools, not independent arm-specific baselines.

## Four-arm K8 true-HV, common-reference signed contrasts
- `OLD pool / OLD selector`, `OLD pool / READY selector`, `READY pool / OLD selector`, `READY pool / READY selector` are all reconstructed by blind greedy predicted-HV selection over each same 64-source physical pool before any true-HV scoring.
- Two candidate-pool sources both contain actual FLA-v12 3030-visit evolution histories, but use different candidate fitness objectives. This is NOT a new operator; both source pools were sampled with the same deterministic Java shuffle rule.

| DAG | VM speed | Search seed | Identical 64-sample mappings | OLD pool READY−OLD selector ΔHV | READY pool READY−OLD selector ΔHV | Source × selector interaction | READY source − OLD source with READY selector |
|---|---|---:|---:|---:|---:|---:|---:|
| Montage_100 | default | 1701 | 0 | 0 | 0 | 0 | +0.005757807 |
| Montage_100 | default | 1702 | 4 | 0 | 0 | 0 | +0.009395177 |
| Montage_100 | staggered | 1701 | 0 | +0.000089371 | 0 | −0.000089371 | **−0.004666527** |
| Montage_100 | staggered | 1702 | 0 | 0 | +0.000153134 | +0.000153134 | +0.021532212 |
| Montage_50 | default | 1701 | 0 | 0 | +0.000126112 | +0.000126112 | +0.005648378 |
| Montage_50 | default | 1702 | 0 | +0.000190052 | +0.000001441 | −0.000188611 | **−0.008236676** |
| Montage_50 | staggered | 1701 | 0 | 0 | 0 | 0 | +0.006366343 |
| Montage_50 | staggered | 1702 | 0 | +0.000046619 | +0.000029722 | −0.000016898 | +0.005910599 |

## Descriptive aggregates

| Matched contrast | Wins / ties / losses | Mean normalized actual ΔHV across eight development cases |
|---|---|---:|
| READY selector on OLD-fitness source | 3 / 5 / 0 | +0.000040755 |
| READY selector on READY-fitness source | 4 / 4 / 0 | +0.000038801 |
| Source×selector interaction | 2 / 3 / 3 | −0.000001954 |
| READY-fitness source vs OLD-fitness source at OLD terminal selector | 6 / 0 / 2 | +0.005215369 |
| READY-fitness source vs OLD-fitness source at READY terminal selector | **6 / 0 / 2** | **+0.005213414** |

The primary mechanism signal is that which objective guides full evolution materially changes **the sampled resulting physical candidate distribution**; in seven of eight paired sources the selected 64-map samples have zero overlap and the remaining one has only four overlaps. **This sample-overlap finding does NOT imply the entire 3030-visit histories are disjoint**: each source samples only 64 genotypes and the full original unique visited lists were not archived. This limitation must not be overclaimed. The cross-source difference is bigger than the within-fixed-pool selection effect in this set of developmental blocks, but sources differed in their optimization trajectories, and sampling plus incomplete full history prevent a clean isolated causal attribution.

## Limitations and next research
- The OLD source outcomes were known before READY source protocol was frozen; the cross-source interaction is descriptive, not an independently blinded confirmation of a discovered benefit.
- The 8 blocks are only Montage sizes 50 and 100 × two VM speed regimes × two source search seeds. They are NOT eight unrelated DAG families, and 1024 physical maps are not 1024 independent statistical replications. Full FLA-v12 solver versus NSGA-II under matched CPU-time budgets is not proven; the standalone 64+64 read-only forecasts have additional wall cost.
- READY-fitness source worsened K8 actual HV under READY selection on two blocks (Montage_100/staggered/1701 and Montage_50/default/1702). The severe original full-READY v12 search result on Montage_100/staggered seed1601 from run 42190857445 remains valid; do not delete or tune away the negative source cases.
- A next strictly read-only **full visited-history fingerprint** audit could distinguish a truly disjoint evolution candidate distribution from the observed low overlap of the 64 sampled candidates; it must verify reproducibility against frozen source samples but must NOT relabel re-executed search histories as new simulator truth.
- Publication-grade claims require a new precommitted operator against sham controls, truly unseen DAG families, more seeds and independent actual compute budgets, with all adverse and null cases and common true references retained.

**All changes limited to `fla-baseline`; `master` and default solver parameters unchanged.**
