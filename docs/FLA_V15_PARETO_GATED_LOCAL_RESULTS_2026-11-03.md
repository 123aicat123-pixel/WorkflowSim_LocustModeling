# v15 Pareto-gated local-search survivor experiment — completed development result

**Decision: NOT a validated replacement for v12.** This is a small exploratory, fully observed negative/mixed ablation, not a proven cloud workflow scheduling innovation.

## Immutable experiment evidence

- Source implementation: `504944f47206094a6883e203b10b2ad3d760dfc8`; six-arm pilot source/workflow `79647ea952a987f04ee10d759a54e9b48dcb16bd`.
- [Actual GitHub Actions 41618003870](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41618003870): **all eight 6-arm paired WorkflowSim compare jobs succeeded and aggregate report job succeeded**. Artifact `v15-report-41618003870`, ID `13223005002`; the original eight job artifacts include simulator CSVs and raw logs.
- Original v14 independent negative ablation: [41617351880](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41617351880). The v14 original experiment matrix [41616676427](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41616676427) had 12 successful simulation jobs but a faulty script caused overall workflow failure; this is already documented and must never be conflated with simulator failure.
- `fla-baseline` branch isolated; `master` untouched.

## Precisely what changed

Both v15 variants use the identical regular counted v14 random-pair / timeline-pair neighbor evaluations, but add one explicit **post-evaluation, pre-survivor gate**: if the local trial is **strictly dominated in PLANNED makespan and cost by the already evaluated normal offspring of the same pair**, the local trial's candidate slot is replaced with a reference to that existing normal offspring. All evaluated trial assignments still remain in passive history and normal nondominated archive admission. The proposed selection introduces **no new objective fitness evaluations**; it can duplicate genotypes and reduce effective diversity. This is NOT a mathematical original FLA operator and does NOT guarantee final nondominated HV improvement.

The controls are (1) original v12-hvbandit, (2) ungated v14-randompair, (3) ungated v14-timelinepair, (4) v15-randomgate, (5) v15-timelinegate, and (6) cost-seeded NSGA-II. Every optimizer uses exactly 3030 stage-in-aware PLANNING evaluations and 16 independent true WorkflowSim schedule replays. Every v14/v15 paired variant includes 1400 charged neighbor evaluations within that same 3030 budget, versus independent exploration by the v12 and NSGA-II arms. Both deterministic initial low-cost task assignments are asserted identical for all arms.

Development settings: CyberShake_30, Montage_25, default/staggered synthetic VM speed, optimizer seeds 161/162. Familiar data families; **not a new publication holdout**. Predeclared primary simulator HV reference = 1.5× largest PLANNED makespan/cost among all six algorithms/two seeds per DAG and VM regime +1; secondary =3×. All actual simulated results inside both fixed references, no refitting based on outcomes.

## True WorkflowSim HV on predeclared primary 1.5× reference

| DAG | VM speed | v15 timeline vs ungated v14 timeline | v15 random vs ungated random | v15 timeline vs v15 random | v15 timeline vs v12 | v15 timeline vs seeded NSGA-II |
|---|---|---:|---:|---:|---:|---:|
| CyberShake_30 | default | +0.0193% | −1.1600% | +0.2403% | +0.0254% | −0.8805% |
| CyberShake_30 | staggered | −0.8645% | −1.1690% | −0.3724% | +0.0934% | −3.1986% |
| Montage_25 | default | +1.7744% | +0.0534% | +0.9397% | +0.8575% | +1.4781% |
| Montage_25 | staggered | +0.2543% | −1.7657% | −0.6008% | −2.1419% | −4.1049% |

Overall pooled 8 paired blocks, reference 1.5×:
- Timeline v15 vs ungated timeline v14: **+0.295849%**, wins **3/8**.
- Random v15 gate vs ungated random v14: **−1.010308%**.
- Gated timeline vs gated random: **+0.051707%**.
- Timeline v15 vs v12: **−0.291374%**, wins **4/8**.
- Timeline v15 vs identically seeded NSGA-II: **−1.676484%**, wins **1/8**.

Reference 3×: timeline v15 vs ungated timeline +0.180978% (4/8); gated random vs ungated random −0.500124%; gated timeline vs gated random +0.118302%; timeline v15 vs v12 −0.016765%; timeline v15 vs NSGA-II −0.815992%. The 3× score does not overturn the primary negative conclusion. The exact case-level dataset is preserved by the Actions report artifact.

Notable negative case: Montage_25 staggered, seed 161, gated timeline vs v12 **−6.1381%**, versus NSGA-II **−6.5810%**. Positive case Montage_25 default seed 161, gated timeline vs ungated timeline **+3.7458%**, versus v12 **+2.7962%**. Do not cherry-pick either.

## Mechanism, limitations, research decision

1. The local planned-Pareto gate was implemented and its rejection count per 1400 local trials was independently checked against actual strict-dominance counts in **every one** of the eight 6-arm jobs. The compiler, v14 one-call timeline regression, and 5 identical initial cost-seed assertions passed.
2. Protecting the next-generation candidate pool against locally dominated offspring is **not automatically useful**: the random-gated arm generally became worse than ungated random. Replacing dominated trials with duplicate existing normal offspring may reduce genotype diversity, and planned-objective local Pareto ordering does not imply improved final simulated HV.
3. v15 was designed after observing earlier v13/v14 negative experiments; these eight development cases cannot be represented as a prospective untouched real-family test. No general solver superiority or Q1 publication readiness claim follows.
4. Keep current default settings unchanged. Retain v12 as main research benchmark candidate, v13/v14/v15 as research-only off-by-default variants. Do not launch successive threshold-tuned v16 variants on these same studied workflows and claim cross-family innovation. A stronger next study should focus on disentangling diversity loss, task timing/caching fidelity, search operator phase interactions and compute-time fairness, with a newly predeclared unseen DAG-family benchmark and independent replications.
