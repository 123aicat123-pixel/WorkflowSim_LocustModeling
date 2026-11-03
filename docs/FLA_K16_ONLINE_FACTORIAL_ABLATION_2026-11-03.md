# Four-way prospective K16 online replay-selection mechanism ablation (2026-11-03)

**Research finding:** The incremental value of a nearest-neighbor residual correction is small and inconsistent. Much of the apparent online-feedback gain is attributable to **greedy HV candidate selection using planner objectives**, not to a reliably learned simulator error model. Preserve `pareto-cover` as the default pending further confirmation; these experimental methods remain opt-in. `master` unchanged.

## Original complete reproducible evidence

- [GitHub Actions run 41597067028](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41597067028), exact source commit `c35cd043452bdc2ccf8d350cbbf5f0d20655fa5b`, **six of six real Java/WorkflowSim case jobs and aggregate PASSED**.
- Original artifact `causal-factorial-k16-report-41597067028`, GitHub artifact ID `13212463371`, provides `online_factorial_hv.csv`, `online_factorial_paired.csv`, `online_factorial_report.md`, aggregate log and source SHA. Per-job archives include complete candidate history SHA-256, all actual replay objective CSVs and online decision traces.
- Three worklow DAGs: Montage_25, CyberShake_30, Inspiral_50; new optimizer seeds 93 and 94; three solver arms FLA v7-costseed, FLA v12-hvbandit, NSGA-II costseed.
- Four policies per solver: (1) `pareto-cover`, planned-objective Pareto-layer/max-min screening; (2) `online-planned-hv`, sequential HV greedy using **only planned objectives**, not replay labels, even though 16 replays are actually performed; (3) `online-observed-hv`, HV greedy against the **previously observed actual simulator front**, but still uses raw planner objectives to predict unseen candidates; (4) `online-nearest-hv`, adds half-shrunk/capped nearest-neighbor observed makespan residual to policy 3.
- Every arm/policy run: **3030 true optimizer planning evaluations and exactly K16 independently executed WorkflowSim replays**, four identical initial planned Pareto coverage genotypes, same complete ordered candidate history SHA-256 across policies, original Java independent-planner objective cross-check.
- **Reference is post-hoc**, shared across all four policies and solvers within each workflow/seed, constructed from the selected simulator objective union solely for scoring. It is NOT a predeclared external HV threshold and must not be passed to selection.

## Mean paired relative simulator HV gain versus original Pareto coverage (six DAG-seed cases)

| Solver | Planned-only greedy HV | Observed-front greedy HV | Observed-front + 1NN residual HV |
|---|---:|---:|---:|
| FLA v7-costseed | **+0.1817%** (6/6 wins) | **+0.5740%** (5/6) | **+0.5766%** (5/6) |
| FLA v12-hvbandit | **+0.2034%** (6/6) | **+0.2291%** (5/6) | **+0.2436%** (5/6) |
| Costseed NSGA-II | **+0.5466%** (5/6) | **+0.5725%** (6/6) | **+0.5725%** (6/6) |

**Mechanism interpretation:** The largest incremental effect frequently comes from changing the selection rule itself to sequential HV greedy; conditioning the greedy score on previously observed actual simulator front can add gains in some cases (especially Montage_25 seed 94 FLA v7, observed-front +2.7015% vs planned-only +0.0974%), but does NOT monotonically improve every case. The nearest-neighbor residual correction barely changes most selected results, especially NSGA-II, and sometimes hurts.

**Negative cases preserved:** `Montage_25` seed 93 FLA v7, observed-front **−0.1234%** and 1NN correction **−0.1737%** relative to default; FLA v12 observed-front **−0.0999%**; NSGA-II planned-only **−0.0556%**. Do not promote a winner based on only the best case.

## Research decision and next gate

1. Avoid claiming novelty solely from 1NN residual correction. Its extra benefit is unproven. More complex residual modeling is not justified by these data.
2. Predeclare `online-planned-hv` versus `online-observed-hv` versus `pareto-cover` on independent 100-task DAG families/seeds with **pre-frozen evaluation references**, actual equal K16 simulator calls, and search SHA commitments. Show improvements and regressions side by side.
3. Assess wall-clock selection overhead separately from simulation time; equal fitness and simulator-call budgets alone do not imply equal computational cost.
4. These are improvements of **K-limited post-search simulator replay selection**, not improvements in FLA optimizer exploration/exploitation or generations. Applicability to NSGA-II supports generality but prohibits assigning the screening gain to FLA search.
5. Six workflow-seed blocks with three correlated arms are insufficient for inferential significance; the families have been seen in prior development. Do not overstate publication readiness.
