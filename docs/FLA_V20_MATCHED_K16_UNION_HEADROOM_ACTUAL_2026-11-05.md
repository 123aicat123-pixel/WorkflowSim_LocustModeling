# Matched Pareto K16 vs randomized K16 replay: true observed-union headroom — 2026-11-05

**Research result, not a deployable policy**: post-hoc analysis of real WorkflowSim outputs from two already completed, prospective replay-selection experiments. This document was written after outcomes were available and cannot be treated as a preregistered performance trial.

## Immutable sources
- Original Pareto-cover-selected K16 run: [41969565802](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41969565802), all 6 original jobs passed.
- Matched-history objective-independent random-selected K16 run: [41972072193](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41972072193), all 6 original jobs passed.
- Prior independent rank audit: [41972209118](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41972209118), PASS. 939 planned dominating within-K16 random candidate pairs, 45 incorrect model dominance relations (became incomparable, not a direct reversed dominance); original Pareto-cover-selected pairs contained zero planned dominance relationships by selection.
- New independent source-auditor `scripts/fla_v20_matched_union_hindsight_audit.py` reads all 12 original zipped source datasets, checks 24 exact search-history SHA fingerprints, 3030 original fitness visits per source arm, K16 unique mappings per replay selector, objective validity, and duplicate-map truth consistency. It NEVER runs optimization or simulation. Evidence will be stored in GitHub Actions `fla-v20-matched-union-headroom.yml`. Local duplicate audit `/mnt/data/v20_union_diagnostic.py` was run against the retrieved original artifacts.

## Diagnostic results (one shared 1.5× true max HV reference per DAG/seed across 4 solvers and 2 replay selectors)

- 24 solver × DAG × seed paired histories, 16 planned K and 16 random K each = **768 replay records**, only **764 within-history unique physical assignment records** after overlap (four assignment overlaps). These numbers are not 764 independent DAGs or globally deduplicated Task→VM assignments.
- **14 distinct random-only observations** had been predicted dominated by at least one originally Pareto-selected mapping but were **not truly dominated by any** Pareto-selected mapping. Each yielded a positive marginal actual hypervolume contribution if appended to that arm's original selected K16. These are observational hindsight findings, NOT verified prospective rescue decisions.
- In 18/24 paired arms, the observed union of planned and random K16 mappings has actual HV greater than planned K16 alone. The sum of individual within-block normalized HV gaps is 0.004535464, mean **0.000188978** per solver-arm block. This mean is strongly affected by one Epigenomics_100 seed952 NSGA-II case, observed gap **0.004034112**; do not use the pooled mean to claim robust improvement or statistical significance.
- **FLA-v12-specific mean observed union gap: 0.000010024** over six familiar DAG/seed blocks; maximum observed FLA-v12 gap: 0.000051573. The full observed-union HV is an optimistic ceiling only on subsets of *this observed union*. It may require >16 mappings, and is not the true population-wide oracle.
- Random-only true non-dominated relative to the fixed planned-selected set: 61 within-history observations across the 24 blocks; 59 random-only observations individually increased the true HV upon being appended. Every one of the 14 falsely excluded candidates had a positive marginal HV improvement.
- An actual-truth hindsight greedy K16 selection from the union is a diagnostic heuristic and is **not** an exact optimal size-16 subset. Its gains cannot be reported as a prospective new method, or as a mathematical upper bound on size-16 optimal HV.
- The original planned K16 and random K16 sets overlap on only 4 within-history physical assignments in total; this gives coverage contrast but precludes stable conclusions from overlap alone.

## Research decision

1. A measurable Pareto model-fidelity error exists; a method that robustly prevents these *specific* early exclusions is scientifically interesting, but 14 post-hoc cases and small observed FLA-v12 HV headroom do **not** establish that a new optimizer would achieve publishable gains.
2. The observed candidate union is not a representative unbiased audit of all feasible mappings. The random K16 sample is small relative to ~3,030 original genotype visits and reuses familiar families and optimizer seeds.
3. Next properly designed study should predeclare a new candidate-selection-independent stratified replay oracle with dominated/non-dominated candidate representation; use separate calibration and unseen-family evaluations, equal total compute budgets, and verify whether any no-truth selection mechanism actually recovers high-quality Pareto points.
4. Do NOT re-tune epsilon, OLD/READY residual model, v20 operators or selection thresholds on these already-inspected examples then rebrand them as holdout evidence. Retain adverse results and unchanged FLA-v12 defaults. `master` remains untouched.

**Verdict:** genuine planner/simulator misclassification and observable lost solutions; small and heterogeneous achievable observed-union HV headroom; still no successful SCI improvement algorithm.
