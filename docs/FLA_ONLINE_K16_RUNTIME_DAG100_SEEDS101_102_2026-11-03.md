# Frozen-reference prospective DAG100 K16 observed-front versus Pareto-cover: true HV and actual measured wall-clock (2026-11-03)

**Scientific outcome:** sequential replay selection conditioned on *previously observed true simulator outcomes* is promising for **FLA v12 (mean +0.4136% HV, 9/10 positive cases)**, but remains inconsistent for other solvers and is **NOT proven faster** under wall-clock. This is a post-search replay policy, **not** a modification to FLA generations. Default `pareto-cover` remains unchanged. Keep `master` untouched.

## Reproducible source of truth

- [GitHub Actions run 41600766954](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41600766954), exact execution SHA `4a9e535644b8613a073bb9b69b9739c3e50cc2c1`. All 10 matrix cases and aggregate report **passed**.
- Aggregate original artifact `online-runtime100-k16-report-41600766954`, ID `13215350172`, contains `online_runtime_report.md`, `online_runtime_paired.csv`, aggregate log, source SHA. The 10 original per-DAG/seed Actions artifacts contain `_replays.csv`, `_summary.csv`, full ordered unique genotype history SHA-256, and causal online decision traces.
- Source: `scripts/fla_online_runtime_dag100.py` and `.github/workflows/fla-online-hv-runtime-dag100.yml`. The Java instrumentation was introduced and unit-checked in prior [Actions run 41597793461](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41597793461).
- Workflow families: CyberShake_100, Epigenomics_100, Inspiral_100, Montage_100, Sipht_100; new optimizer seeds **101/102**. Algorithms: DAG-Pareto-FLA v7-costseed, v12-hvbandit and NSGA-II costseed.
- Exact equal budget: **3030 actual planner objective evaluations** and **K16 true independent WorkflowSim replay calls**, per algorithm and policy. Same complete ordered visited-candidate/genotype/planned objective SHA-256 and identical warm-up first 4 real replayed genotypes. The online version reads only **previously simulated selected schedules**, never labels for unobserved candidates. Prior causal no-lookahead test is [41597427016](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41597427016).
- The common per-family evaluation HV reference was frozen from **previous** Actions 41572425682, independent of new scores. This scoring reference is never passed to the online selector.

## Exactly measured paired scores

| Optimizer | Mean paired simulator-HV change (online observed-front vs cover) | HV win cases | Median additional selection time | Median relative combined wall-clock change | Cases online has shorter total time |
|---|---:|---:|---:|---:|---:|
| **FLA v7** | **+0.0427%** | **5/10** | **+13.372 ms** | **+0.784%** | 5/10 |
| **FLA v12** | **+0.4136%** | **9/10** | **+4.177 ms** | **−0.880%** | 6/10 |
| **NSGA-II** | **+0.1659%** | **7/10** | **+2.047 ms** | **−1.952%** | 5/10 |

Most important positive on FLA v12: `Sipht_100` seed 101, **+2.0007%** true simulator HV. Negative FLA v12: `Sipht_100` seed 102, **−0.0249%**. Other notable negative examples: FLA v7 `Inspiral_100` seed 102 **−0.1921%**; NSGA-II `Sipht_100` seed 102 **−0.1207%**.

The online selector incurred additional selection time in the majority of cases, and total time varies both ways. The ratio comparisons include solver search, candidate choice and actual simulator replay, **not** CI checkout, Java compilation, or GitHub queue delay. These are single JVM-run wall-clock measurements per fixed policy/seed and do not establish statistically reliable speedup: separate JVM processes, warmup and runner contention can influence timing.

## Decision and next gate

1. Do not promote the observed-front policy as generally superior yet. Continue to keep the nonfeedback `pareto-cover` as the default, with online observed-front explicitly opt-in.
2. Preserve all negative cases; specifically distinguish **ranking effectiveness** from **wall-clock efficiency**. A method can improve simulator HV and still cost more computation.
3. Before claiming a runtime improvement, alternate the JVM run order between methods and repeat on independently seeded runs, and document runner hardware/Java version. Compare selection time and combined time separately.
4. Evaluate on new DAG instances / VM configurations beyond families repeatedly used during development. Ten optimizer-seed/DAG cases with three correlated solvers each are not a powered test of broad superiority.
5. The observed-front feedback occurs **after** the full planned optimization history, not inside the iterative FLA optimizer search. Its gains cannot be claimed as an improved FLA search algorithm, and FLA v12 versus NSGA-II superiority remains unestablished.
