# Full-budget priority-versus-restart deconfounding: frozen first gate, 2026-11-04

**Registered before any new results. No alteration to original FLA/NSGA-II defaults, no `master` changes, and no optimizer tuning in this gate.** This is an engineering ablation, not a claim of a novel FLA algorithm.

## Motivation and precise hypotheses

Earlier priority portfolio gate 41683032206 and audited HV 41683457146 showed a one-block FLA improvement but not stable wins. It confounded **the runtime priority policy**, **three independent restarts/population size**, and **K16 candidate allocations**. We now separate those mechanisms with matching restart count and deterministic seed offsets.

- H1: at full 3030 genotype calls and K16 actual WorkflowSim replays, frozen **single policy** FIFO/SHORTEST/UPWARD, using the matching policy-aware decoder, differs in true K16 Pareto HV from original FIFO Task-ID ready decoder.
- H2: with **identical three 10×101 restart budgets** and identical 6/5/5 source K quotas, three priority policies (FIFO/SJF/UPWARD) yield a different true HV than **three FIFO-only restarts**. This isolates *policy assignment* from restart/population count in the source, but not all downstream simulator/selection interactions.
- H3: gains (if any) are separately compared to original stage-in-aware full population FLA and identically configured cost-seeded NSGA-II (both solver types receive the same treatment controls). **No result is promised to favor FLA.**

## Frozen prospective experiment, not a research-wide unseen-family holdout
- New algorithm-gate DAX instances `Inspiral_50`, `Epigenomics_46` (families were previously studied). Search seeds `821`, `822`; VM speed `staggered`, unchanged 16-VM types and prices. Not a new-family holdout.
- Both solver arms run every job: `DAG-Pareto-FLA[v12-hvbandit]` and `NSGA-II[costseed]` with exactly identical first two cost seeds per job, matched VM parameters, task mapping encoding, candidate recording, and `v12-nsga-ready-pair` experiment mode.
- Controls and intervention groups per (DAX, base seed):

| Source variant | Objective decoder | Actual ready-task priority | Population, generations | Exact evaluations / solver | True K replay quota / solver | Actual search seed |
|---|---|---|---|---:|---:|---:|
| `old_full` | Stage-in insertion | FIFO | 30 × 100 | 3030 | 16 | base |
| `ready_full` | Ready queue TASK_ID | FIFO | 30 × 100 | 3030 | 16 | base |
| `shortest_full` | Ready queue SHORTEST | SHORTEST | 30 × 100 | 3030 | 16 | base |
| `upward_full` | Ready queue UPWARD | UPWARD | 30 × 100 | 3030 | 16 | base |
| `split_fifo0` | Ready TASK_ID | FIFO | 10 × 100 | 1010 | 6 | base |
| `split_fifo1` | Ready TASK_ID | FIFO | 10 × 100 | 1010 | 5 | base+10000 |
| `split_fifo2` | Ready TASK_ID | FIFO | 10 × 100 | 1010 | 5 | base+20000 |
| `split_priority_fifo` | Ready TASK_ID | FIFO | 10 × 100 | 1010 | 6 | base |
| `split_priority_shortest` | Ready SHORTEST | SHORTEST | 10 × 100 | 1010 | 5 | base+10000 |
| `split_priority_upward` | Ready UPWARD | UPWARD | 10 × 100 | 1010 | 5 | base+20000 |

*The first FIFO split arm and the policy portfolio's first FIFO arm intentionally produce an exact reproducible duplicate run; retain as paired negative control, do not count their 12 true calls as 12 independent schedules. Other same-policy repeated genotypes across the 3 FIFO restarts are allowed and must be disclosed when computing the union's unique physical plans.*

- 2 DAX × 2 base seeds × 10 source variants = **40 original GitHub Actions jobs**; each job has FLA and NSGA-II (80 paired optimizer arms). Combined `old_full`, `ready_full`, `shortest_full`, `upward_full`, `three_FIFO_restarts`, `three_priority_islands` are **6 treatment K16 sets for each solver** in every DAX/seed block. Therefore 4 blocks × 6 treatment sets × 2 solvers × 16 true replay calls = **768 real source WorkflowSim replays**, including 48 repeated FIFO control replay calls. Total counted genotype objective calls across all source jobs = 4×2×(4×3030+6×1010)=**145440**.
- Source budgets are **exactly** counted genotype decodes, not necessarily unique physical mappings. Objective computation is more expensive for some decoders; report measured search_ms, selection_ms and replay_ms rather than calling these compute-time matched.

## Analysis frozen before any outcomes
- Refuse partial source; verify 40/40 source variants have complete independently saved original `research_summary.csv`, `research_replays.csv`, `block-id.txt`; correct source seed, DAG, VM profile, both algorithms, population and generations, 3030/1010 evaluations and captured-evaluations, K16 or K6/K5; positive finite real/planned metrics. Detect and report any within-arm or across-island repeated physical assignment+policy.
- Use **ONE** normalized true actual K16 two-objective HV reference for all 12 solver×six-treatment sets within each DAG/base-seed block; reference at 1.5× of maximum real M/C plus 1e-6, cross-check 3.0×. Do NOT compare individual run-local `sim_hv`.
- Compare within each solver (a) single policy full vs `ready_full`, (b) three-priority portfolio vs matched three-FIFO restart portfolio, (c) three-FIFO restart portfolio vs full ready, and (d) each vs `old_full`, plus FLA-vs-NSGA-II per treatment. Report signed exact per-block ΔHV, wins/ties/losses under tolerance 1e-8, mean and median differences, runtime ratios, nondominated count, duplicate physical plans, reference-point sensitivity and negative cases.
- A split-policy gain must not be interpreted as FLA-specific if it appears equally for NSGA-II. Unlike a true joint per-individual priority genome, this design only switches a **globally fixed policy per independently searched island**.
- No post-hoc selection of highest true HV among treatments to call a prospective optimizer. Results on these two historically researched DAG families are development evidence only. If no stable improvement or cost too high, keep every variant optional and design a separate mechanistically motivated strategy rather than tuning these blocks.

## Publication boundary
No `master` edits, no default change, no claim of Q1 readiness. Actual multiobjective novelty would still require a common per-genotype joint priority–VM representation, risk-aware FLA-specific operators, corresponding fair NSGA-II encoding, untouched family holdout, >20 independent RNG runs on multiple problem sizes, runtime budget matching, broad published baselines and formal sensitivity/ablation.
