# Full FLA-v12 vs seeded NSGA-II OLD/READY transfer: verified actual WorkflowSim — 2026-11-06

**VERDICT: engineering/source/provenance gate PASS; stable algorithmic improvement NOT demonstrated. The earlier positive fixed-32 selected-mapping signal does not reliably transfer to full evolutionary search.** All 16 original source jobs and the independent audit completed successfully; all positive AND adverse cases preserved.

## Frozen source chain
- Pre-outcome frozen protocol: `docs/FLA_MONTAGE_FULL_SEARCH_READY_TRANSFER_FROZEN_2026-11-06.md`, commit `96663613b94f02738820730375cd1e989e540cf1`.
- Pre-outcome audit script commit `6b2fa19b798c46ae13270eb014b79914c7b2c7a4`.
- Original source workflow commit `a3e4292b6cfdcb20698d7ea9bbe6829d122cde5a`.
- [Successful original GitHub Actions run 42190857445](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42190857445): **16/16 original source jobs, 1/1 independent audit PASS**; 16 original source artifacts plus 1 comprehensive independent audit artifact, 90-day artifact retention.
- 2 known Montage DAG sizes (50 and 100), 2 VM-speed regimes (default and staggered), 2 *genuine optimization search* seeds (1601,1602), 2 objective modes (StageInAware OLD, ReadyQueue READY). Each 16 matrix cell runs BOTH `DAG-Pareto-FLA[v12-hvbandit]` and `NSGA-II[costseed]` with **exactly 3030 visited objective evaluations/solver arm**, same deterministic initial cost assignments, and K8 prospectively forecast-selected original actual FIFO WorkflowSim replays per solver. Totals: **32 full-search arms, 256 real physical simulator replays**. This experiment does NOT run the fixed population-1 no-generation mapping selector.
- Audit verifies original source SHA, frozen protocol content hash, 16 distinct required matrix jobs, 32 complete optimizer summaries, all 256 actual replay rows, distinct TaskID→VMID maps per arm, exact evaluations, positive finite original simulator objectives, and common true objective reference across **all four** algorithm×predictor arms per DAG/speed/seed block. HV reference = 1.5× each actual max + 1e-6; 3.0× sensitivity also archived. True objectives are used only after forecast-only K8 replay selection.

## Actual normalized common-reference K8 HV differences

| Original DAG | VM speed | Search seed | FLA READY − OLD | NSGA-II READY − OLD | Difference of differences |
|---|---|---:|---:|---:|---:|
| Montage_50 | default | 1601 | +0.005062565 | −0.004003679 | +0.009066244 |
| Montage_50 | default | 1602 | −0.000099887 | +0.000890506 | −0.000990393 |
| Montage_50 | staggered | 1601 | +0.005720621 | −0.004232270 | +0.009952891 |
| Montage_50 | staggered | 1602 | +0.006647873 | +0.018437168 | −0.011789295 |
| Montage_100 | default | 1601 | +0.022925165 | −0.003859932 | +0.026785097 |
| Montage_100 | default | 1602 | +0.011432001 | +0.002302186 | +0.009129815 |
| **Montage_100** | **staggered** | **1601** | **−0.033404446** | +0.004127474 | **−0.037531920** |
| Montage_100 | staggered | 1602 | −0.003001961 | +0.005359731 | −0.008361692 |

## Aggregate descriptive summaries (8 paired development blocks)

| Matched comparison | Wins / ties / losses | Mean actual normalized ΔHV |
|---|---|---:|
| FLA READY − OLD | **5 / 0 / 3** | **+0.001910241** |
| NSGA-II READY − OLD | **5 / 0 / 3** | **+0.002377648** |
| FLA − NSGA-II under OLD | 5 / 0 / 3 | +0.001272957 |
| FLA − NSGA-II under READY | 5 / 0 / 3 | +0.000805551 |
| Decoder × solver interaction | **4 / 0 / 4** | **−0.000467407** |

Actual search wall-time (source instrumented; runner-dependent and not an equal CPU time control): mean FLA OLD 873.1ms, FLA READY 943.9ms, NSGA OLD 606.0ms, NSGA READY 503.0ms. CPU accounting and equal-wall-time budget are NOT yet validated.

## Research interpretation
- This directly falsifies a simple claim that the conditional Montage_50/staggered fixed-map READY gains (+0.000867221 under original prices, +0.000554899 under linear, +0.000729274 under convex) guarantee robust improvements to real FLA evolution. The candidate generators and 8 chosen replay schedules differ with changed objective; no universal model benefit follows.
- READY is a shared decoder change tested in both algorithms, not a novel FLA-specific proposal. NSGA gains are comparable (and mean larger), and the average difference-of-differences is negative. **A paper that advertises a novel improved FLA algorithm from this trial would be unsupported.**
- The worst FLA loss in Montage_100/staggered seed1601 is material relative to most positive gains. All outcomes should remain visible; do not filter this seed or tweak VM prices/workflow rules based on its label.
- Montage family has been repeatedly seen in development; two seeds, two sizes and a fixed FIFO workload do NOT constitute a statistically independent cross-family holdout. 256 replayed physical assignments are not 256 independent statistical replicates. No p-values or stable-generalization significance are claimed.
- Future testable research should focus on *why* surrogate inaccuracies on candidate selection and queue scheduling create harmful optimization trajectories and whether an abstaining/calibrated decision mechanism or budget-matched sham can prevent worst-case losses without overfitting. A new operator must be frozen before actual labels; compare to original FLA-v12 and cost-seeded NSGA-II with equal counted visits AND measured compute-time limits, on truly independent DAG structures and 20+ seeds.

**Do not promote READY globally into default FLA. Do not represent this as a verified superior algorithm or SCI-ready improvement. All code/results on `fla-baseline`; `master` unchanged.**
