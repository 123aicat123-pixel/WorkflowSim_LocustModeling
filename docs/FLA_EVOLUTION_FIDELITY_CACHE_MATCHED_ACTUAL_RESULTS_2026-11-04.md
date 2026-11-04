# Evolutionary fidelity FIRST-WRITE CACHE MATCHED true WorkflowSim results — 2026-11-04

**Primary finding: matching all four modes to the SAME genotype cache changes the fairness interpretation but does NOT establish a robust FLA improvement. Fixed periodic and the 1% risk gate each beat OLD-cached on Sipht_60, and each loses to OLD-cached on CyberShake_50, for BOTH frozen seeds. No method universally wins. The naive risk gate consumes almost its entire 378 high-fidelity budget, not a meaningful adaptivity achievement.**

## Original immutable scientific chain and scope
- Preregistered before outcomes: `docs/FLA_EVOLUTION_FIDELITY_CACHE_MATCHED_FROZEN_2026-11-04.md`, commit `306611c2`, defines two DAX instances CyberShake_50/Sipht_60 (both known development families), two random seeds 801/802, same original 16 VM profile, FIFO runtime, 30 population × (100 generations+initialization) = **3030 counted genotype fitness visits per solver**, exact K8 prospectively selected simulation replays.
- Original [Actions 41784901304](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41784901304) **16/16 original source jobs PASS**. Each original source run invokes BOTH FLA-v12-hvbandit and NSGA-II[costseed], with exactly eight distinct physical VM assignments per solver replayed in actual WorkflowSim; **256 real simulator calls**. All four modes use SAME immutable first-write Task→VM genotype cache implementation `BudgetedEvolutionFidelityObjective`; OLD-cached and READY-cached baselines have been introduced explicitly and both have the same cache-hit behavior for duplicate mappings as PERIODIC and RISK.
- Source fidelity engine and tests: `sources/org/workflowsim/planning/BudgetedEvolutionFidelityObjective.java`, `tests/org/workflowsim/planning/BudgetedEvolutionFidelityObjectiveTest.java`. Full original Java CI and per-job clean compile/pass were checked. Each solver/mode source `_evolution_fidelity.csv` records unique-mapping count, visit count, cache hits, cheap/ready actual decoder calls, budget, model nanoTime and full solver search milliseconds. The independent all-case audit verifies `visits = distinct + cache_hits = 3030`, all 8 simulator replay genotypes distinct, actual costs/makespans finite and positive, exact mode-specific decoder constraints, two algorithm labels and one source SHA across all treatment jobs.
- First read-only report [Actions 41785125139](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41785125139) failed only due to an extra closing Python list bracket in reporting source; this was repaired in commit `816c728` without touching Java logic or any source simulation. The successful [independent full real HV audit 41785343850](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41785343850) **PASS**: 16 original jobs → 32 true K8 point-sets → 16 paired hybrid-vs-control comparisons, using a single 1.5× true objective reference for all 8 solver×mode arms in each exact DAG/seed block; also archived all 3.0× true-reference sensitivity values and raw negative cases.

## ALL actual WorkflowSim K8 normalized Pareto HV (1.5× shared real reference per DAX/seed)

| Workflow | Seed | Solver | OLD cached | FULL READY cached | PERIODIC | RISK | PERIODIC READY model calls | RISK READY calls |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| CyberShake_50 | 801 | FLA-v12 | **0.48354338** | 0.48166510 | 0.48010942 | 0.48012167 | 378 | 378 |
| CyberShake_50 | 801 | NSGA-II[costseed] | 0.49143415 | **0.49666053** | 0.48914731 | 0.49233501 | 378 | 378 |
| CyberShake_50 | 802 | FLA-v12 | **0.52112090** | 0.52054140 | 0.52040697 | 0.51822747 | 378 | 378 |
| CyberShake_50 | 802 | NSGA-II[costseed] | 0.52813175 | 0.52346684 | 0.52576016 | **0.52997029** | 378 | 378 |
| Sipht_60 | 801 | FLA-v12 | 0.24464343 | **0.26246421** | 0.25991996 | 0.26126097 | 378 | 378 |
| Sipht_60 | 801 | NSGA-II[costseed] | **0.26264292** | 0.26264248 | 0.26260760 | 0.26263311 | 378 | 377 |
| Sipht_60 | 802 | FLA-v12 | 0.25143815 | 0.26774608 | **0.26880779** | 0.26721344 | 378 | 378 |
| Sipht_60 | 802 | NSGA-II[costseed] | **0.26921542** | 0.26918283 | 0.26878534 | 0.26914009 | 377 | 377 |

This is true WorkflowSim normalized HV for an *actually replayed K8 subset*, not planned HV or the entire feasible scheduler Pareto set. References differ by DAG/seed and are shared only within each block; never compare row values across different blocks as if they used the same reference.

## Fairness matched-cache paired results
- **FLA PERIODIC** minus OLD-cached average true HV across four blocks = **+0.00712457**, but nominal wins/ties/losses **2/0/2** (both Sipht wins, both CyberShake losses). Relative to FULL-READY-cached mean **−0.00079316**. Mean actual READY model calls / FULL-READY actual calls **0.126×**. Mean FLA full search wall-time **14,829 ms** (not comparable to decoder-only nanoTime).
- **FLA RISK** minus OLD-cached average true HV **+0.00651943**, also **2/0/2** with the same DAG-dependent sign. Relative to FULL-READY-cached **−0.00139831**. READY fraction **0.126×**, mean full search time **18,715 ms**.
- **NSGA-II PERIODIC** minus OLD-cached mean true HV **−0.00128096**, **0/0/4**. Relative to FULL-READY-cached **−0.00141307**. READY fraction **0.136×**, mean search time **12,926.5 ms**.
- **NSGA-II RISK** minus OLD-cached mean true HV **+0.00066357**, **2/0/2**. Relative to FULL-READY-cached **+0.00053146** in the mean but the advantage is not consistent by DAG/seed. READY fraction **0.136×**, mean search time **18,196.5 ms**.
- Risk-gated READY calls: **378/378** for 3 of 4 solver×DAG pairs on seed 801, **377/378** for the other; seed802 risk similarly consumes 378 on both CyberShake and 378 FLA/377 NSGA on Sipht. Thus there is NO substantial budget allocation efficiency difference relative to precommitted PERIODIC 378 count. The mixed-fidelity policy fails a distinguishing test against a simple schedule.
- Both mixed modes may encounter different numbers of unique genotypes, and FULL READY also uses different actual decoder calls when unique mappings differ. Their nominal visit budgets are now matched but their CPU utilization is still not budget-matched, and risk alters optimization trajectory through uncalibrated heterogeneous objective values.

## Research decision, avoiding false-positive claims
1. This study **resolves the first-cache unfairness confound**: all FOUR evaluators use the same canonical Task→VM first-write memoization and record explicit cheap/ready physical calls. The old unmatched pilot 41780754595 is retained as historical data, not silently replaced or relabeled as a scientific success.
2. **Do not automatically promote PERIODIC or RISK to FLA v20**: despite interesting Sipht effects and much fewer high-fidelity evaluations, there is no stable increase across both workflow families, and the complete READY model is generally strongest or equally good on Sipht FLA.
3. The remaining mathematical problem is how to compare predicted means/costs from OLD versus READY across distinct solutions under a common calibrated scale and make Pareto decisions only when the confidence margin is actionable. First-write caching prevents inconsistent scores on repeated solutions but does NOT fix incorrect selection between two differently modeled candidates.
4. A future study must implement a frozen error-aware or dominance-uncertainty mechanism, against matched-cache OLD, READY and PERIODIC baselines, then validate on truly independent unseen DAG families, multiple seeds and K16+ actual HV/IGD+, with a second equal actual compute-time budget. The 1% gate should not be tuned on this developer sample and called independent validation.
5. This is two familiar DAG families × 2 seeds, high dependence, not enough statistical power for reliable publication claims. `master` and default FIFO, FLA-v12, NSGA-II remain untouched; all code, protocol, raw positive/tied/negative results and audit live only on `fla-baseline`.

**Verdict: Cache-matched evolutionary fidelity engineering gate PASS. Stable improved FLA Pareto optimizer NOT demonstrated.**
