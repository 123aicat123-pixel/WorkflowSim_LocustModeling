# Full-precision fixed-replay-budget audit: version 2 (2026-11-03)

**Authoritative screening analysis.** This document **supersedes** the retrospective numerical HV recovery claims in `docs/FLA_SCREENING_BUDGET_VALIDATION_2026-11-03.md` and earlier run summaries where candidate planned objectives had mixed CSV precision. It does **not** supersede the original independent WorkflowSim simulations themselves.

## Provenance and experimental source integrity

We corrected `FLAResearchExperiment.java` to emit **17 significant digits** (Java `%.17g`) for both base replay and formerly omitted-candidate planned and simulated objectives. Previously, `_replays.csv` used 10 decimal places and `_screening_samples.csv` used 9 decimal places; this could break numerical tie/dominance/ordering decisions in Python even though the Java simulator had computed higher-precision values. The new precision is an output-protocol repair, not an FLA optimizer change.

- Java experiment source blob SHA (identical across all four refreshed cohorts): `d8d7f9bfd23333934b8f9aaa102dd7b558657f44`.
- Python screening evaluator blob SHA (identical across all four): `c41383f7d40fa373c344a66688ea399e1b2769e8`.
- [Full-precision development cohort 41583717514](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41583717514): CyberShake_30, Montage_25, Sipht_30, 2 seeds.
- [Full-precision cross-family validation 41583697452](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41583697452): Epigenomics_24, Inspiral_30, 3 distinct seeds.
- [Full-precision 50-task cohort 41583704442](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41583704442): CyberShake_50, Inspiral_50, Montage_50, 2 new seeds.
- [Full-precision 100-task cohort 41583710961](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41583710961): CyberShake_100, Epigenomics_100, Montage_100, Sipht_100, 2 new seeds.
- Each GitHub Actions run completed all per-seed **actual WorkflowSim** full-visited replay jobs and its final Python budgeted-screening aggregation successfully. Each aggregate stores `replay_budget_scores.csv`, `replay_budget_winners.csv`, and `replay_budget_report.md`, plus source SHA; individual matrix artifacts retain per-candidate CSVs.

## Frozen replay-selection protocol

The three algorithms were v7-costseed FLA, v12-hvbandit FLA, and costseed NSGA-II. They each received 80 native planner objective evaluations per workflow/seed and identical two cost-seed initial assignments. Every unique visited assignment was independently simulated to establish the retrospectively known full-visited HV oracle. All budgeted selections used **planned makespan, planned cost and genotype identity only**, never true simulated outcomes. Policies and candidate budgets were frozen before new validation and scale runs.

Pareto-cover: successive planned non-dominated layers, selecting the minimum-makespan extreme first, then normalized max-min planned-objective coverage. Competitors: Pareto+random hybrid, extreme-first low-discrepancy scalar sweep, and 16 hash-seeded repetitions of random selection (repeat draws are not independent workflows).

The HV reference is fixed within each DAG family across algorithms and its seed cohort, constructed from the original planned-front-only replays **before** adding extra candidate simulations. Recovery = selected K simulator front HV divided by the full unique-visited simulator front HV, not the global DAG scheduling optimum.

## Corrected primary results, K=16 per algorithm

| Cohort | Workflow families | Paired seeds per family | Pareto-cover mean HV recovery | Random mean HV recovery | Wrong top-HV solver vs full visited |
|---|---:|---:|---:|---:|---:|
| Original development | 3 | 2 | **99.607%** | 90.702% | 1/6 |
| Other-family validation | 2 | 3 | **99.706%** | 89.015% | 1/6 |
| New seeds at 50 tasks | 3 | 2 | **99.920%** | 87.359% | 0/6 |
| New seeds at 100 tasks | 4 | 2 | **98.829%** | 90.086% | 0/8 |

Mean recovery across algorithm/case records is descriptive, not a pooled raw HV or an independent-sample inferential estimate. In 100-task data, Epigenomics_100 seeded NSGA-II achieves only approximately **91.94%** mean recovered HV at K=16; this important failure case remains explicit.

### Additional key corrected budgets

| Cohort | K=8 Pareto-cover mean recovery | K=24 | K=32 |
|---|---:|---:|---:|
| Development | 99.321% | 99.609% | 99.620% |
| Other-family validation | 99.229% | 99.714% | 99.997% |
| 50 tasks | 99.061% | 99.996% | 99.996% |
| 100 tasks | 96.561% | 99.199% | 99.247% |

Even when the mean is high, an algorithm-specific front may be worse. A fixed K may be insufficient for large workflow fronts; adaptive replay budgeting is a hypothesis, not a validated new algorithm.

## Prospective K-real-call implementation and independent identity audit

A **default-OFF** Java option `-Ddagfla.budgetReplayK=16` selects K distinct visited assignments by the same planned-only Pareto-cover rule, **before** true WorkflowSim calls. Each solver still has 80 search objective evaluations but makes exactly 16 simulator replays instead of precomputing all. [Actual K=16 budget CI 41583046697](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41583046697): 6 workflow/seed cases, 3 solver arms, 48 independent simulations per case, all assertions passed.

To eliminate uncertainty from earlier serialization and tie ordering, the [full-precision Python/Java selected-genotype-set and objective identity CI 41583594925](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41583594925) ran full-history oracle and real K=16 prospective replay on the **same checked-out source**. Across Montage_25 and CyberShake_30, seeds 1 and 2, all **12/12 solver-case pairs selected identical sets of 16 genotypes**, and the same selected genotype's actual planned/simulator objectives agreed within explicit tolerance. One intermediate experiment `41583460785` failed a more stringent **sequence order** assertion on an equal-distance ordering: the set was identical; that assertion was corrected to set identity and the entire workflow rerun successfully.

These facts establish functional end-to-end K-budget enforcement and exact genotype consistency in the tested conditions. They do **not** demonstrate the total application runtime benefits of K or a better final HV than standard NSGA-II.

## Why publication-strength claims remain premature

1. There are only 2–3 independent seeds per family; selecting among 16 random repeats does not increase independent workflow sample size.
2. The workflow families and the FLA variants have been studied through development. Cohorts are unseen to the *screening policy* but not necessarily untouched for the wider multi-algorithm study.
3. Retrospective oracle labels were generated through **full** independent simulation and only *then* subset-selected. The prospective K mode executes fewer simulations, but its 3030-evaluation quality, wall-clock time, and cross-family performance still require dedicated testing.
4. The greedy Pareto-cover policy is a combination of familiar principles. Its measured effectiveness is a useful method finding but does not establish algorithmic novelty by itself.
5. Cost/makespan objective fidelity, VM availability and pricing stress, reference-point robustness, uncertainty, convergence, and fair baseline simulation budgets require validation.
6. Keep the 100-task Epigenomics weakness and the 1/6 wrong-solver rankings explicit.

**Proposed next gate:** evaluate **real** K-limited replay after full 3030 optimizer evaluations on 25/50/100-task workflows against equal-K alternative screening policies, holding solver initialization, independent search budget, true simulator calls, and HV reference consistent. Neither a green CI nor selective relative HV is publication proof.
