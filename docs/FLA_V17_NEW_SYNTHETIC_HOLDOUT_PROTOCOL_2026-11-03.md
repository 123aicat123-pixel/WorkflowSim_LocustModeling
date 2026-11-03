# v17 prospective new synthetic DAG topology holdout protocol, frozen before outcome observation

Purpose: independently challenge the previously selected `v17-do-random` rule **without changing its algorithm parameters** using deterministic newly generated DAGs not used in v12–v17 search development. This is evidence about **synthetic topology generalization only**, not performance on unseen real scientific applications. All labels and samples will be frozen before any real simulator results are inspected.

## Locked synthetic instance generation

Generator `scripts/fla_v17_new_synthetic_holdout.py`, fixed seed `2026121501`, exactly **60 tasks** in each DAG, two previously unused topology patterns:

- `SynthNewWide_60`: six layers of ten tasks (width 10), 2–4 randomly chosen direct dependencies from preceding layer for each non-root task; expected 10 roots, 6 layers.
- `SynthNewDeep_60`: twelve layers of five tasks (width 5), each of five continuous pipelines with deterministic-seeded occasional cross-lane edges from 2 levels prior; expected 5 roots, 12 layers.

Each DAG dependency `a→b` is encoded with its own produced output and the matching consumed input file of the SAME valid positive size. Task runtime is deterministically generated within 20–130 raw DAX units and per-edge logical file size within 2–40 MB. Source input files on root tasks have positive sizes. Graph topology and exact raw file SHA-256 must be saved to logs and archived. No optimizer feedback or observed prior HV is read by the generator. Generated files exist only inside the GitHub Actions checkout, never overwrite repository's real DAX files.

## Algorithms, budget and predeclared analysis

At each DAG topology, two VM speed profiles (`default`, `staggered`), and seeds `301, 302, 303`: 2×2×3=12 paired scenario-seed blocks. Four algorithms exactly as in the prior v17 confirmation (no retuning): `v12-hvbandit`, `v17-do-random`, `v17-late-random` matched-count timing control, and identically cost-seeded `NSGA-II[costseed]`. Each gets 3030 charged stage-in-aware planned objective evaluations and K16 true WorkflowSim replays of distinct genotype assignments using the same original Pareto-cover selection. All methods share the first two deterministic low-cost task assignments; early and late local variants each make exactly 1036 charged local evaluations and 1964 normal FLA offspring evaluations, within the 3030 total. Population 30 × 100 generations, first 30 initialization evaluations.

Freeze HV reference by DAG+VM speed: **1.5× coordinatewise maximum of PLANNED selected K16 objectives across the four arms and three seeds +1** (primary), and **3×+1** (secondary). If any actual simulator observation falls outside the frozen planned-only reference, analysis FAILS rather than refitting the reference based on outcomes. The reference is therefore constant among seeds and algorithms within each DAG/VM subgroup.

Primary comparison: DO random vs equal-local-probe last-74 random on K16 actual WorkflowSim HV, with paired per-seed win counts and mean % difference by each synthetic topology and VM speed. Secondary comparisons: DO vs v12 and seeded NSGA-II, two reference sensitivities, minimum actual makespan/cost, search compute time. All failures and negative cases must be retained, even if this disproves development-stage findings.

## No leakage or overstated publication evidence

This generator is new but its characteristics (wide vs deep, 60 tasks, runtime and file-size ranges) are chosen as a scientific stress test informed by prior observed heterogeneity. The synthetic family is not a statistically representative random sample of real workflow families. Twelve cases share two underlying topology structures; treat family as clustered and do not call twelve cases independent topological replicates. Repeated pipeline refinements based on observing these outcomes would contaminate this as a holdout. No adaptive threshold should be fitted on the results and then evaluated on the same 12 cases. A positive mean alone does not prove broad generality; a negative result is still a useful scientific outcome.

Existing Java optimizer implementation/defaults remain unchanged, `master` remains untouched. Only test harnesses, source data generator and analysis scripts are added.
