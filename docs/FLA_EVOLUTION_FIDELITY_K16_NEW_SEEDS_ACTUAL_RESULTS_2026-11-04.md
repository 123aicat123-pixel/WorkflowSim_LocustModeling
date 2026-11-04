# Prospective new-seed K16 cache-matched evolutionary fidelity: ACTUAL WorkflowSim outcome (2026-11-04)

**Scientific verdict: source execution PASS, independent real-HV reconstruction PASS, stable improvement FAIL.** No novelty/SCI/Q1 performance claim. The adverse results are essential evidence and must not be discarded.

## Immutable provenance and scopes

- Predeclared **before actual outcomes** in `docs/FLA_EVOLUTION_FIDELITY_K16_NEW_SEEDS_FROZEN_2026-11-04.md` (commit `40da370`).
- K16-specific flag and no change to historical K8 default introduced at `125d123`.
- Actual original [source Actions 41816731197](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41816731197), source commit `7e7bed5306a644ff6a209dce8f55905bfc76f70d`: **16/16 original GitHub Actions jobs SUCCESS**.
- 2 historically familiar DAG families (`CyberShake_50`, `Sipht_60`) ×2 new original optimizer seeds (901,902) ×4 objective modes =16 source jobs; each invokes actual FLA-v12 and seeded NSGA-II, 3030 original counted genotype fitness visits **per solver**, 16 original FIFO WorkflowSim assignments per solver, making **512 actual WorkflowSim replay solutions**.
- All originals evaluated identical `pop30 gen100`, default VM speed profile, `pareto-cover` planned-only K16 selection and per-genotype first-write physical mapping cache. Modes `old-cached`, `ready-cached`, `periodic`, `risk` are unchanged from prior K8. The mixed modes have up to 378 READY calls. Different search trajectories and actual unique mapping counts are expected: *fixed same caching rule* does not mean identical genotype search paths.
- Independent read-only [all-case Actions 41816856033 (second attempt SUCCESS)](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41816856033) downloaded all **16 actual source artifacts** and checked complete source SHA identity, 32 solver/mode K16 sets, 16 paired comparisons, positive actual objectives and physical decoder-call budgets. It recomputed shared-reference true normalized 2D HV (common 1.5x actual max per DAG/seed across all eight solver/mode arms; independent sensitivity 3x). It did **not** rerun or alter any source simulation, optimizer, parameter, or replay assignment.
- First read-only audit attempt failed because it was launched while only eight original CyberShake source artifacts existed; it correctly rejected missing Sipht source records. After all 16 source jobs completed, the failed job was rerun unchanged and SUCCEEDED. The failed attempt remains auditable, not reclassified as a model failure.

## Real K16 normalized HV differences (each compared within its exact DAG/seed block)

| Solver | Mode | Mean ΔHV versus OLD, 1.5x | Wins/Ties/Losses vs OLD | Mean ΔHV versus FULL READY, 1.5x | Mean ΔHV versus OLD, 3x |
|---|---|---:|---:|---:|---:|
| FLA-v12 | PERIODIC | **-0.009496735** | **0/0/4** | -0.008369749 | -0.008055728 |
| FLA-v12 | RISK | -0.003495191 | 2/0/2 | -0.002368205 | -0.002463854 |
| NSGA-II | PERIODIC | -0.004754652 | 2/0/2 | +0.001835128 | -0.004155550 |
| NSGA-II | RISK | -0.006425206 | 2/0/2 | +0.000164574 | -0.005409343 |

These are **actual WorkflowSim Pareto HV of the sampled K16 set**, not predicted HV and not the attainable global Pareto front. Mean differences summarize four correlated DAG/seed blocks; no statistical generalization follows.

### All FLA-v12 actual K16 HV15 by block

| DAG | Seed | OLD cached | FULL READY cached | PERIODIC | RISK |
|---|---:|---:|---:|---:|---:|
| CyberShake_50 | 901 | 0.468295 | 0.460984 | 0.443730 | 0.463259 |
| CyberShake_50 | 902 | 0.478060 | 0.480457 | 0.471067 | 0.468704 |
| Sipht_60 | 901 | 0.261871 | 0.262274 | 0.255820 | 0.262266 |
| Sipht_60 | 902 | 0.245365 | 0.245368 | 0.244986 | 0.245381 |

### Cost and mechanistic findings

- FLA PERIODIC underperformed both OLD-cached and FULL READY-cached in **all four paired blocks**, the strongest negative test for simply mixing fidelities during evolution.
- FLA RISK beats OLD on only the two Sipht blocks (one advantage just ~0.000016 in HV); it loses on both CyberShake blocks. Its mean ΔHV against both cache-matched FLA controls is negative. No robust FLA search improvement was demonstrated.
- NSGA-II PERIODIC and RISK have positive differences vs FULL READY on some blocks but **both have negative average differences vs OLD**. This does not rescue a FLA-specific novelty claim.
- FLA PERIODIC and RISK each spent exactly **378 READY evaluations** in every tested block; NSGA PERIODIC spent 378 throughout, NSGA RISK spent 377 or 378. The 1%-near-skyline criterion rarely suppresses READY use relative to periodic, so it **does not demonstrate meaningful adaptive budget allocation**.
- Average FLA FULL READY decoder calls per block were **2939.25** versus RISK 378, but lower high-model call count is not evidence of lower complete search time: same nominal visits do not equal equal wall/CPU cost. The source output includes measured search and decoder times, which vary by DAG/runner and algorithm.
- Sensitivity with the shared 3x actual reference does not reverse the negative **average** ΔHV against OLD for any mixed mode.

## Research decision

**Do not promote PERIODIC or RISK to an improved FLA version.** The original matching K8 work already showed instability and this genuinely new K16 seed replication confirms it. The current risk gate is not an informative allocation mechanism, and heterogeneous OLD/READY objective values still introduce incomparable search ranking risk.

Future novel policy must (1) calibrate comparable objective estimates or explicitly abstain and consume READY calls when uncertainty matters, (2) distinguish uncertainty selection from periodic spending with a meaningful budget/use ablation, (3) validate on independent unseen DAG family/workload regimes with K16 or larger true replays, and (4) compare both equal counted visits and **equal measured compute budget**. Do not tune on this study and call the resulting values independent. All original negative results, exact assignment source files and independent metrics remain archived. `master` and default FIFO remain untouched.

**Disposition: 512-real-replay confirmation PASS; FLA adaptive superiority FAIL.**
