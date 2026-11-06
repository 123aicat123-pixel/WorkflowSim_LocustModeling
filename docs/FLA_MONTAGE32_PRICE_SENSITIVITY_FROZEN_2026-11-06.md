# Precommitted Montage32 synthetic VM price sensitivity gate — 2026-11-06

**Frozen *before* any new actual simulator outcome in this matrix.** This is exploratory sensitivity analysis after observing a single positive `Montage_50 / staggered / default-price` block in run 42188466329. It is NOT an untouched holdout, no independent new DAG family, and NOT FLA optimization or 20 randomized replications.

## Why seed-sweeps are inadmissible
`FLAFixedMappingUniverse32` calls `LIWSABenchmarkExample.runPlanning` with a SINGLE externally supplied physical mapping, population size 1 and generation count 0. `LIWSAPlanningAlgorithm.initializePopulation()` first inserts that complete genotype and the evolution loop executes zero iterations; its RNG does not choose the physical map. The subsequent FIFO WorkflowSim execution uses deterministic DAX data and deterministic speed/profile inputs. Therefore simply changing `CONFIG_RANDOM_SEED` or printing 20 seed values is NOT valid independent evidence. Retain simulator seed 1501 as historical metadata, NOT a claimed random factor. This frozen gate will instead change real VM prices and speeds.

## Fixed genuine simulator trial (all outcomes, no tuning after labels)
- Keep **exact same** 32 independent TaskID→VMID policies in `examples/org/workflowsim/examples/planning/FLAFixedMappingUniverse32.java`, with no candidate additions, deletions, optimization or label-informed selection.
- Workflows: `Montage_50`, `Montage_100`; speed profiles `default`, `staggered`; price models **`linear` and `convex`**, giving **2×2×2×32=256** fresh WorkflowSim physical true replay records in eight blocks. Existing original-default-price cohort is archival context only, NOT new replication.
- Price models are the already-supported synthetic ones in `LIWSABenchmarkExample.vmPrice`: `linear = 0.15*(mips/250)`; `convex = 0.15*(mips/250)^1.5`. The prior `default` profile uses original VM rates; price models are stress tests, not public-cloud bills. Same VM pricing passed to both planners and real simulator in each block. Assert Java `VMPriceProfilesRegressionTest` PASS before replay.
- Original task-level verification flags unchanged: `workflowsim.planningStageInAware=true`, `dagfla.readyQueueDiagnostic=true`, `dagfla.fixedTaskTrace=true`, `dagfla.fixedVmReadyPriority=fifo`. No optimizer/GA/FLA search. Each run calls original WorkflowSim on exact physical VM mapping; reject duplicate mappings, missing real timeline IDs or invalid results.
- Exactly one simulator seed `1501`. Eight blocks are NOT statistically independent repeated seeds. Do not report a seed variance, a p-value, or pooled-seed statistical significance.

## Locked selection and falsification
- OLD/READY separately use the frozen prediction-only greedy marginal 2D HV selection of K=1,2,3,4 from all 32 physical maps. Each predicted reference is `(1.5*max(predicted makespan)+1e-6, 1.5*max(predicted cost)+1e-6)`; tie-break by predicted normalized scalar sum and lexicographic policy name.
- All realized selections are evaluated using the same exact actual reference per (workflow, speed, **price**) block: `(1.5*max(actual makespan)+1e-6,1.5*max(actual cost)+1e-6)`. Report actual HV and regret vs exhaustive, hindsight C(32,K) oracle, actual true Pareto cardinality, number of exact optimal K4 subsets, prefix physical map disagreement, and the signed READY−OLD paired HV difference; never use oracle to choose a map.
- Primary evidence is per-block paired signed difference and number of actually divergent chosen physical sets (K4); also report K1–K3. Include zero and adverse effects. Summarize blocked by DAG and speed, NOT by treating the 256 maps as independent replications.
- Per-price model results do NOT justify choosing one favorable profile post hoc; any comparisons must show both. No new predictor, planner, mutation or policy based on these true labels.
- The source/analysis run must verify 8/8 complete matching matrix blocks, 32 unique policies and source maps in each, 256 original true simulator rows, current source SHA equality across artifacts, nonempty real runtime logs, exact price/speed metadata, and a frozen protocol file hash. Preserve audit scripts, all artifacts and all losses on GitHub Actions.

**Stopping rule:** if improvements vanish, reverse, or do not alter actual selected mapping, report that fact; do not relabel another experiment as replication. Even positive results remain an exploratory matched physical-map mechanism test, not proof of global FLA optimization. Later SCI testing needs genuinely separate DAG structures, stochastic workload/VM variation and full FLA-vs-NSGA-II/other literature baselines under equal objective-evaluation and simulator budgets.

No file on `master` is modified.
