# v17 preregistered DO-only versus equal-local-budget late-74 K16 pilot — 2026-11-03

**Outcome:** DO-only RANDOM neighborhood is a promising experimental candidate, NOT confirmed general superiority or a new default. Keep v12 as default experiment reference and v17 variants opt-in. The DO-only TIMELINE neighbor is not uniformly beneficial. No changes to `master`.

## Source, execution, evidence

- Experimental v17 generation masks and 8-arm mode source: commit `f540b0e70e9ac4d1d6f841199caf576afe240895`.
- Frozen evaluation scorer `a6ffec5c241023a39f53df7131858f44f5ad7d42`.
- Actual matrix + score workflow: commit `56a0569d0368c95e0deb7e15ba9f7fbe90f8b04c`.
- [GitHub Actions 41625790444](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41625790444): **all 12/12 separate eight-arm simulated cases completed successfully**, final aggregate-report job also successful. Report artifact `v17-report-41625790444`, ID `13225791228`, and 12 job artifacts hold all actual simulator candidate replays and source logs. `FLAPairedSearchWindowTest`, `FLAPopulationDiagnosticsTest`, `TimelineParetoNeighborTest` ran inside each matrix job; each also asserts K16 and fixed opportunity masks.

## Frozen study and equality

DAG files `Epigenomics_24.xml` and `Inspiral_30.xml`, both already in source repository but not used in the immediately previous v13–v16 pilot series. Two VM speed profiles: default/staggered. Three optimizer seeds 191/192/193. Twelve scenario-seed blocks, eight algorithms per block: v12, full v14 random, DO-only v17 random, late-74 v17 random, full v14 timeline, DO-only v17 timeline, late-74 v17 timeline and seeded NSGA-II.

Every arm has exactly **3030 charged stage-in-aware PLANNING objective calls** and **16 real WorkflowSim simulation replays** under unchanged Pareto-cover selection. Initial deterministic two low-rental-cost task assignments match NSGA-II across every FLA arm. Each DO-only and late-74 matched variant has exactly **1036 local neighbor fitness calls and 1964 regular phase-bandit-eligible FLA child calls**, with no extra oracle. DO phase uses generations 1–74, late control generations 27–100. Full local pair uses 1400/1600, unmodified v12 uses 0/3000. Seven FLA arms retain 101 passive generation diagnostics.

**Primary HV reference:** 1.5× coordinatewise maximum PLANNED K16 makespan and cost across all eight algorithms/seeds, independently per DAG+VM speed, +1. The 3× reference is sensitivity. Every real simulator point fits both prespecified bounds; neither reference used actual simulator labels to adjust its size.

## Actual true-simulator K16 HV, primary reference, paired means of three seeds

| DAG | VM speed | DO random vs equal-count late random | DO timeline vs equal-count late timeline | DO random vs v12 | DO timeline vs v12 | DO random vs seeded NSGA-II | DO timeline vs seeded NSGA-II |
|---|---|---:|---:|---:|---:|---:|
| Epigenomics_24 | default | +0.0803% | +0.0136% | −0.0112% | −0.0998% | +0.2886% | +0.1999% |
| Epigenomics_24 | staggered | +1.0427% | +0.0280% | +1.6409% | +1.5515% | +4.0739% | +3.9823% |
| Inspiral_30 | default | +0.5518% | +0.1653% | +0.0711% | −1.2446% | +2.3121% | +0.9633% |
| Inspiral_30 | staggered | +2.7092% | −2.2781% | +3.3968% | −0.7171% | +2.4004% | −1.6153% |

Pooled 12 paired blocks, **primary 1.5× reference**:
- DO-random vs matched late random: **+1.096005%**, 8/12 wins.
- DO-timeline vs matched late timeline: **−0.517806%**, 6/12 wins.
- DO-random vs v12: **+1.274374%**.
- DO-timeline vs v12: **−0.127480%**.
- DO-random vs equally cost-seeded NSGA-II: **+2.268742%**.
- DO-timeline vs seeded NSGA-II: **+0.882546%**.

At the **secondary 3× reference**, DO-random vs late random +0.508389% (7/12 wins), vs v12 +0.587962%, vs NSGA-II +1.042715%; timeline vs late timeline −0.234113% (6/12), vs v12 −0.029337%, vs NSGA-II +0.429359%. These are the same simulator assignments scored differently, NOT new independent observations.

**Individual negative observations:** Epigenomics_24 default seed191 DO random vs v12 −0.0296% and seed192 −0.0057%; Inspiral_30 default seed193 DO random vs late random −1.4624%, v12 −1.0480%; Inspiral_30 staggered seed192 DO-random vs NSGA-II −0.2414%. The strong individual positives (e.g. Inspiral staggered seeds192/193 vs v12 +5.9140%/+3.6259%) must NOT suppress negative cases.

## Scientific interpretation and next decision

This is the first in the phase-window sequence with favorable average HV for **DO-only RANDOM** against the equal-local-evaluation late control, original v12 and seeded NSGA-II across these 12 paired development cases. The same timing rule for the TIMELINE neighborhood does not yield an average advantage against its late control. Thus phase timing plausibly interacts with local proposal quality, but the mechanism is not a demonstrated causal effect: windows differ in RNG history and offspring trajectories, and different DAG/VM profiles can reverse benefits.

The DO-only versus matched late control is the primary *timing* comparison; comparisons with full v14 conflate the count and timing of local calls. The data is small and pre-existing workflows, so this is **development evidence only**. The hypothesis had been generated from previous development results, and additional equal-budget truly held-out workflow instances and independent VM heterogeneity are required before publication-level superiority, FLA equation fidelity, or promotion to defaults. No tuning of the 74-generation rule on this now-observed cohort.

Recommended next: freeze DO-only RANDOM exactly as implemented, run a separate preregistered independent confirmation with new DAG instances/scales/seeds and compare with matched late-random, v12 and NSGA-II; include family-level uncertainty and computational runtime. Report failures and leave v12 default unchanged until confirmation.
