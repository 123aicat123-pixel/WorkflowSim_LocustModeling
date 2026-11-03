# v17 DO-only Random: frozen different-size/seed confirmation result — 2026-11-03

**Final scientific decision: DO-only Random is a conditional research candidate, NOT a validated improvement over v12 or NSGA-II. DO phase timing does NOT have a stable matched late-74 advantage.** No production/default promotion. Do not modify `master`.

## Source and unmodified protocol

- Locked DO/late window implementation: commit `f540b0e70e9ac4d1d6f841199caf576afe240895`.
- Initial pilot on Epigenomics_24 and Inspiral_30: successful [GitHub Actions 41625790444](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41625790444), report artifact `v17-report-41625790444`.
- Separate v17 confirmation declaration before results: `docs/FLA_V17_CONFIRMATION_PROTOCOL_2026-11-03.md` (commit `3ed726044acfb8d36c6624c00fc6eaad1b7c8593`); four-arm mode commit `14f109759d8d0ddf0023a172d19418723907aa46`.
- [Successful 16/16 GitHub Actions verification 41626382711](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41626382711), all 16 case jobs plus final report successful. Artifact `v17-confirm-report-41626382711`, ID `13226821265`. Case-level true simulator CSVs and raw job logs retained for all cases.
- The v17 operator was NOT changed after the pilot, the number of DO/late active generations was NOT tuned after seeing outcome, and this confirmation used new optimizer seeds.

## Exact equal-budget controls

Different DAX instances/scales already present in repository: `Epigenomics_46`, `Inspiral_50`, `CyberShake_100`, `Sipht_100`. Two VM speed profiles default/staggered × seeds 211/212, 16 paired scenario-seed cases.

Four arms per case: frozen `v12-hvbandit`, `v17-do-random`, `v17-late-random`, identically cost-seeded NSGA-II. Every arm gets exactly 3030 counted stage-in-aware PLANNING fitness evaluations and 16 real WorkflowSim replay evaluations under the same default planned Pareto-cover selection, identical deterministic first two seeded low-rental-cost task assignments. DO and late both get 1036 charged local trials + 1964 normal FLA offspring, independently checked against 101 generation diagnostics and per-run log counters. No extra evaluator calls.

HV references frozen solely from PLANNED replay candidate coordinatewise maxima across four arms and both seeds within each DAG/VM speed +1, primary 1.5× and secondary 3×. All real simulated points were inside the references, with no refit from simulator outcomes. A fixed 3× reference is not a second independent experiment.

## True WorkflowSim K16 HV, primary 1.5× reference, means across two seeds per DAG/speed

| DAG | VM speed | DO random vs matched late random | DO random vs v12 | DO random vs seeded NSGA-II | DO wins late |
|---|---|---:|---:|---:|---:|
| Epigenomics_46 | default | −1.5446% | −0.7060% | +2.7788% | 0/2 |
| Epigenomics_46 | staggered | −1.0236% | −2.2120% | +3.5359% | 1/2 |
| Inspiral_50 | default | −0.5086% | −0.6626% | +0.0957% | 1/2 |
| Inspiral_50 | staggered | −0.3012% | −2.4470% | −0.7013% | 1/2 |
| CyberShake_100 | default | +1.3525% | +2.0227% | −1.4373% | 2/2 |
| CyberShake_100 | staggered | −0.6435% | −1.0252% | −1.2855% | 1/2 |
| Sipht_100 | default | −0.9706% | +0.1095% | +5.9082% | 0/2 |
| Sipht_100 | staggered | +5.9830% | +7.0609% | +3.9450% | 2/2 |

Pooled 16 scenario-seeds (NOT 16 independent DAG-family samples):
- DO vs equal-1036 late: **+0.292937% mean**, **8/16 wins**.
- DO vs v12: **+0.267539% mean**, **9/16 wins**.
- DO vs NSGA-II: **+1.604945% mean**, **8/16 wins**.

Secondary 3× sensitivity: DO vs late +0.135469%, 8/16 wins; DO vs v12 +0.097219%, 9/16 wins; DO vs NSGA-II +0.641119%, 8/16 wins.

## Comparison to the previous positive pilot

The earlier smaller-scale pilot on two DAG instances, each default/staggered and three seeds, yielded DO-random vs late **+1.096005% (8/12)**, vs v12 **+1.274374%**, and vs seeded NSGA-II **+2.268742%** under its independent common planned-only reference.

The new confirmation reduces the corresponding mean advantages to +0.292937%, +0.267539% and +1.604945%, with win counts 8/16, 9/16 and 8/16 respectively. **No strong replication of the original DO-timing superiority is established**, despite a small positive overall mean. In fact, Epigenomics_46 and Inspiral_50 generally do worse than v12, while staggered Sipht_100 shows larger gains. Strong negative single cases include Epigenomics_46 staggered seed212 DO vs late **−4.4397%**, vs v12 **−5.3529%**; Inspiral_50 staggered seed212 DO vs v12 **−3.3332%**; positive cases include Sipht_100 staggered seed211/212 DO vs v12 **+8.0265%/+6.0953%**. Every case remains in the original archive.

## Methodological limitations, publication consequences

1. The confirmation isolates new **workflow size and optimizer seeds**, but ALL DAG families were available in the repository; some had already been studied in prior variants. It is **not** a truly untouched new workflow-family holdout. Only two seeds per DAG/speed are insufficient to establish stochastic algorithm superiority.
2. DO/late paired windows have the same number of local fitness evaluations but do not share identical RNG trajectories, normal offspring proposals or downstream evolutionary states; time-dependent search differences are not a controlled one-variable intervention on a fixed proposal stream.
3. HV changes can be influenced by reference choice; observed 3× sensitivity results are consistently smaller. Relative percentage changes should not be mistaken for statistical effect-size precision.
4. Equal 3030 evaluation calls do NOT imply equal CPU time, stage-in simulation fidelity, energy/QoS generalization, or algorithm equation-faithfulness relative to original FLA source.
5. **Decision:** retain v12 as research benchmark, DO-only random v17 as optional candidate, and other versions as controlled ablations. Do not deploy v17 as default or claim Q1 readiness. Next study should focus on an independent true family-level experimental cohort and carefully measured per-instance predictors (DAG communication/computation structure and VM heterogeneity), with all choices predeclared before new simulator labels.
