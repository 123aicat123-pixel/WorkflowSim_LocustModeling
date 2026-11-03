# Exhaustive visited-set simulator validation for FLA v12 (2026-11-03)

**Scope:** `fla-baseline` only. No changes to `master`. This is a *methodological sensitivity result*, not a claim of overall algorithm superiority.

## Source provenance and reproducible run

- Source commit: `4df0214f75b1aca1a09528e7d09908a126a860f1`
- [Complete successful GitHub Actions run 41580592118](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41580592118)
- Report artifact: `exactv12-report-41580592118`, GitHub artifact ID `13206195672`; contains `full_visited_v12.md` and `full_visited_v12.csv`.
- Six per-case artifacts: `exactv12-{Montage_25,CyberShake_30,Sipht_30}-s{1,2}-41580592118` (original logs, source SHA, planned front replay, and omitted-visited-genotype replay CSVs).
- A preceding run `41580416168` had all six solver cases **PASS**, but its final *aggregation task failed* because a glob unintentionally counted both `_summary.csv` and `_screening_summary.csv`. Workflow-only fix was committed, followed by the fully successful run above. Keep this failure visible for provenance.

## Search and independent simulator replay

- Three algorithms: `DAG-Pareto-FLA[v7-costseed]`, `DAG-Pareto-FLA[v12-hvbandit]`, `NSGA-II[costseed]`.
- Each has the *same first two deterministic low-cost assignments*, population 8, generations 9, **80 actual objective evaluations** per paired case.
- Three workflow families (CyberShake_30, Montage_25, Sipht_30), two seeds each, six cases.
- The full set of **distinct visited genotypes** is independently simulated in WorkflowSim. Each audit checks `unique_visited == original_replayed + additional_replayed`, including strict planning-dominated, planning ties and other candidates missing from the reported archive. This is exhaustive **over visited solutions**, not over the full combinatorial search space.
- A per-workflow HV reference is *frozen using only original front replays* across all solvers and both seeds (1.05× max +1, two objectives), not recalculated from added genotypes. A ranking is computed before and after extra replays. Different algorithms may have different numbers of unique visited genotypes, hence different **post-search simulator replay** costs. The 80 evaluations are *optimization* objective calls, not the total simulation-call count.

## Paired simulator HV relative difference: v12 compared with cost-seeded NSGA-II

| Workflow | Seed | Planned-front-only relative HV | Full-visited relative HV |
|---|---:|---:|---:|
| CyberShake_30 | 1 | +5.933% | +5.941% |
| CyberShake_30 | 2 | +6.506% | +6.506% |
| Montage_25 | 1 | **−14.465%** | **−14.457%** |
| Montage_25 | 2 | +7.797% | +12.988% |
| Sipht_30 | 1 | +6.401% | +6.394% |
| Sipht_30 | 2 | **−3.026%** | **−3.175%** |
| **Unweighted mean across six paired relative differences** | | **+1.524%** | **+2.366%** |

The mean percentages are descriptive; don't average raw HV across families with different scales. The changed average does **not** imply a statistically significant improvement, especially after selection across numerous previous experimental variants.

### Ranking change

- **One of six paired cases changed its top-HV solver:** `Sipht_30` seed 2, from `NSGA-II[costseed]` to `DAG-Pareto-FLA[v7-costseed]` after all-visited replay.
- This rank flip does **not** imply that v12 won the case; v12 was still lower than cost-seeded NSGA-II there.
- Montage_25 seed 2 shows substantial v12 sensitivity: full-history replay boosts its HV enough to move v12-versus-NSGA-II relative gain from +7.797% to +12.988%.
- The observed distinction is a direct counterexample to the assumption that the planning-front-only rule always preserves the highest-HV algorithm.

## Research boundary

1. These results are **small-search-budget**, and cannot be substituted for the 3030-evaluation, 50/100-task studies. Don't claim v12 dominates NSGA-II generally.
2. This experiment controls optimizer objective evaluations, but post-hoc simulator evaluations increase with the count of unique visited genotypes. A real simulator-in-the-loop optimization must control simulator calls and wall-clock time as well.
3. The two-seed, three-family test is not an untouched, statistically powered validation cohort.
4. The selected HV reference is frozen from baseline points but was not preregistered before algorithm development; evaluate reference robustness and confidence intervals on larger benchmarks.
5. Next scientific gate: predefine a uniform replay/simulation evaluation budget and compare cost-aware screening policies against exhaustive replay on manageable subproblems, then confirm on a locked larger benchmark without further variant tuning.
