# FLA v19 bounded queue-conflict Pareto-risk relocation: verified true WorkflowSim results — 2026-11-04

**Scientific verdict: REJECT v19 as a reliable improvement.** It was correctly implemented, internally active and evaluated with equal counted target-fitness budgets, but **its normalized actual K16 Pareto HV is lower than original v12 on average, with a 2-win / 2-loss split and extra computation overhead**. It remains opt-in, is not installed by default, and must NOT be described as SCI-ready. No changes to `master`.

## Preregistered mechanism and real-data chain
- Prior source and frozen protocol `docs/FLA_V19_QUEUE_CONFLICT_RISK_FROZEN_PROTOCOL_2026-11-04.md`, frozen before any new full-optimizer real simulator outcomes. V19 helper `QueueConflictRiskRelocation.java` targets the DAG upward-importance-weighted VM-ready queue waiting estimate, examines at most two alternative VM assignments, and accepts only if group objective improves with at most **1% deterioration in the other predicted objective**. Trigger probability 0.35, tradeoff score improvement−0.25× adverse loss; all constants frozen.
- FLA-v19 original target fitness remains StageInAware Makespan and Cost; ready model is only an EXTRA planning proposal heuristic, never fed future true simulator labels, no extra target candidate credited without the normal counted evaluate. Four-task oracle 22s→21s and rejection/cost-safety cases compiled and tested; v19 mode disabled by default.
- [Four original full optimizer/actual WorkflowSim jobs 41690669415](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41690669415): **4/4 PASS**, two DAG instances `Inspiral_100`, `Sipht_100`, two seeds 901/902, VM speed staggered. Four source algorithm arms in every job: original FLA v12, FLA v18 (max two-decoder disagreement), experimental FLA v19, and cost-seeded NSGA-II. Each one exactly **3030 counted and captured StageInAware target evaluations and K16 real prospective pareto-cover replay calls**. 16 solver arms ×16 = **256 real simulator calls**; 48,480 counted target genotype evaluations. All four solver arms share exactly identical deterministic first two cost seeds per job.
- [Independent read-only actual HV audit 41691646807](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41691646807): **PASS**, all 4 source jobs, identical original source commit `0ec91dbf8d1be6f77881ecabb3a7d5a417252151`, one 1.5×-max normalized 2D real-HV reference per DAG/seed across all FOUR K16 fronts, with 3.0× sensitivity. Audit preserved original mapping, planned/actual M/C, search_ms and K counts and verified no repeated map within selected K16 each arm; all outcomes, including harmful cases, archived.

## Primary real K16 shared-reference normalized Pareto HV

| DAX | Seed | FLA v12 | FLA v18 | FLA v19 | Seeded NSGA-II | Δ v19−v12 | Search time ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| Inspiral_100 | 901 | 0.35618538 | 0.35690320 | **0.36208377** | 0.35131658 | **+0.00589840** | 0.97× |
| Inspiral_100 | 902 | **0.38434894** | 0.38893074 | 0.36740887 | 0.37189324 | **−0.01694007** | 0.78× |
| Sipht_100 | 901 | **0.30219874** | 0.29283879 | 0.27971062 | 0.30309475 | **−0.02248811** | 1.66× |
| Sipht_100 | 902 | 0.30566745 | 0.28477747 | **0.31160268** | 0.29690896 | **+0.00593522** | 1.60× |

- V19−v12 average **−0.00689864** normalized actual HV, median **−0.00552084**, 2 win / 2 loss. Mean search wall-time ratio **1.25×**. Signs of v19-v12 are preserved under 3.0× reference.
- V19−v18 average **−0.00066106**, 2 wins / 2 losses, mean search time ratio 0.84×. V18−v12 mean **−0.00623758**, 2 wins / 2 losses. No stable 3-arm FLA advantage is established.
- V19−seeded NSGA-II average **−0.00060190**, 2 wins / 2 losses, mean search time ratio **1.69×**. Too few correlated blocks for statistical inference.

## Actual FLA-v19 mechanism activity and compute audit
The v19 trigger was active: it did not silently fall back to unmodified v12. Internal ready forecasts were NOT counted as target evaluations but were separately audited.

| DAX | Seed | V19 triggers | Accepted single-task relocations | Internal ready forecasts | Counterfactual VM forecasts |
|---|---:|---:|---:|---:|---:|
| Inspiral_100 | 901 | 1021 | 208 | 2095 | 1074 |
| Inspiral_100 | 902 | 1097 | 267 | 2638 | 1541 |
| Sipht_100 | 901 | 1048 | 20 | 2101 | 1053 |
| Sipht_100 | 902 | 1046 | 10 | 2098 | 1052 |

**Mechanism explanation (not post-hoc proof of cause):** accepted relocation rate dropped from 20–24% of triggers on Inspiral to about 1–2% on Sipht. This is consistent with the proposed 1% Pareto risk constraint being overly restrictive for some DAG VM-mapping regimes. However, it is equally possible that few queue-conflict changes would be beneficial on Sipht. We cannot identify causal explanation from these aggregated trigger counters, and we MUST NOT tune 1%, 0.35 or 0.25 using these four already-observed outcomes then describe the same records as held-out validation.

Time ratios varied 0.78×–1.66× by DAG/seed; v19 uses 1–3 extra event predictor evaluations per trigger, and equal 3030 target-genotype calls is NOT equal total computational work or a time-matched algorithm baseline.

## Research decision and next valid approach

1. **Do not deploy or claim v19 performance gain.** The two negative blocks dominate the average, and new work should not choose only favorable seeds or workflows.
2. V19 is not a joint task-priority/VM placement optimizer: it changes a VM-mapping gene with a ready-queue model but the TARGET StageInAware decoder still ignores actual runtime alternative priority. This **proposal-objective model mismatch** is a plausible structural reason for inconsistency and must be directly measured rather than guessed.
3. Earlier matched three-priority-vs-three-FIFO full-gate `docs/FLA_PRIORITY_RESTART_DECONFOUND_ACTUAL_RESULTS_2026-11-04.md` also found FLA priority islands fail to yield consistent true-HV gain. Further blind FLA mutation tuning is an inefficient research direction.
4. Next research design should FIRST establish **decision-rank fidelity** of the objective for a genuinely consistent joint ready-priority-and-VM mapping representation across new task/VM configurations, then introduce shared representation in FLA and NSGA-II, and only after that test a specific FLA Pareto operator. This is a separate development+untouched-family cycle; existing workflows/seeds are not prospective holdouts.
5. Relevant prior literature already coevolves task and VM selection rules; see `docs/FLA_CURRENT_LITERATURE_NOVELTY_GUARD_2026-11-04.md`. "FLA+task priority" alone is not new literature. If a validated improvement cannot be established, the experimentally demonstrated ready-queue model-fidelity / simulator-evaluation discrepancy can instead be positioned as a careful reproducibility/measurement paper with appropriately modest scope.

**This is a scientific falsification success and a completed reproducible experiment, NOT a successful optimizer. Keep all 4/4 original positive and negative source datasets.**
