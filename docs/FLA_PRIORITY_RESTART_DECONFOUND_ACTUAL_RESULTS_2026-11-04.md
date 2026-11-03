# Equal-budget priority policy vs matched-restart actual WorkflowSim Pareto study — verified results (2026-11-04)

**Scientific verdict: the three-island fixed-priority portfolio DOES NOT improve FLA consistently once one controls for the repeated population initialization and K replay split. Keep the original FLA default, FIFO runtime and all alternatives off. On these four limited blocks, SJF may benefit NSGA-II more than FLA; NOT an FLA-specific publication-level novelty.**

## Preregistration and immutable original evidence

- Protocol fixed before outcomes: `docs/FLA_PRIORITY_RESTART_DECONFOUND_FROZEN_PROTOCOL_2026-11-04.md` at `8136f0d`.
- [Original 40-job full actual WorkflowSim Actions 41689142588](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41689142588): **40/40 SUCCESS**. Four (DAG,seed) blocks: `Inspiral_50`, `Epigenomics_46`, seeds 821 and 822, staggered VM speed. Each job executed both original `DAG-Pareto-FLA[v12-hvbandit]` and low-cost-seeded `NSGA-II[costseed]`. All outcomes include source mapping, planned and actual M/C, runtime, and SHA; exactly 3030 or 1010 counted genotype objective calls depending on full vs island arm, and fixed K16 or K6/K5 actual calls.
- [Independent read-only HV / exact-budget / repeat-identity Actions 41689570828](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41689570828): **SUCCESS**, recomputes actual normalized 2D HV under one shared 1.5× actual-maximum reference per (DAG, seed) across **ALL 12 solver/treatment sets**, plus alternative 3.0× sensitivity. **40 source jobs**, 48 assembled K16 sets, **768 actual WorkflowSim calls** (some intentional duplicates), **145,440 counted genotype evaluations**. The **48 repeated FIFO replay candidate pairs** from exactly identically configured first islands were checked for same physical assignment and true M/C, and all matched. Independently reports duplicate physical placements in K16 unions, never counts duplicates as unique Pareto samples. All source CSVs and audit reports archived.

Six treatments per solver per DAG/seed all use 3030 counted genotype evaluations and 16 true simulator replays:
1. full-budget insertion/FIFO default (`old_full`: 30×101 objectives, K16),
2. full ready-queue/FIFO (`ready_full`: 30×101, K16),
3. full SJF ready queue (`shortest_full`: 30×101, K16),
4. full upward rank (`upward_full`: 30×101, K16),
5. three independent FIFO islands (`fifo_restarts`: 10×101 each, K6/K5/K5; seeds base/+10000/+20000),
6. three exactly matched priority islands (FIFO/SJF/upward at same seed offsets, K6/K5/K5).

The two restart portfolios now have **the SAME population size, counted objective budget, source seed offsets and K quota by island**. This addresses the population-splitting/restart confound in the previous unpaired priority portfolio, but it is not a true joint per-genotype priority gene, and **CPU time** is still not matched just by evaluator-call count.

## Source true WorkflowSim normalized HV (1.5× reference shared across all 12 arms per block)

| DAX | Seed | Solver | Original insertion/FIFO | Ready/FIFO | Full SJF | Full upward | Three FIFO restarts | Three priority islands |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| Inspiral_50 | 821 | FLA v12 | 0.38191391 | 0.37526647 | 0.38025026 | 0.36037008 | 0.36552109 | 0.36507089 |
| Inspiral_50 | 821 | NSGA-II | 0.35707799 | 0.35768675 | 0.36551856 | 0.36225872 | 0.35068082 | 0.35384760 |
| Inspiral_50 | 822 | FLA v12 | 0.35905742 | 0.35025534 | 0.35797525 | 0.35164253 | 0.37353069 | 0.36877892 |
| Inspiral_50 | 822 | NSGA-II | 0.35174962 | 0.35818020 | 0.36790373 | 0.36919241 | 0.34917391 | 0.34548118 |
| Epigenomics_46 | 821 | FLA v12 | 0.36909229 | 0.37436428 | 0.36727302 | 0.35032505 | 0.37652760 | 0.37477917 |
| Epigenomics_46 | 821 | NSGA-II | 0.36227875 | 0.36308984 | 0.37485849 | 0.35215420 | 0.35302207 | 0.36251094 |
| Epigenomics_46 | 822 | FLA v12 | 0.37539759 | 0.37621092 | 0.37713960 | 0.36125355 | 0.36631384 | 0.37235118 |
| Epigenomics_46 | 822 | NSGA-II | 0.34594808 | 0.34994857 | 0.36407069 | 0.35656106 | 0.35352040 | 0.35229737 |

## Primary causal-factor observation (within four correlated blocks)

**Matched three-priority islands minus three FIFO islands**:
- FLA mean **−0.00022826** actual normalized HV, **1 win / 3 losses**, mean search wall-time ratio **0.95×** between these two restarted groups.
- NSGA-II mean **+0.00193497**, **2 wins / 2 losses**, mean search-time ratio **0.98×**.
- Therefore **no robust universal priority-portfolio gain** and nothing uniquely attributable to FLA. Both fixed policy groups use identical number of islands, seed offsets, evaluation calls and K quota, removing the prior major confound.

**Single full-budget policies against FIFO-ready**:
- FLA SJF mean **+0.00163528**, **3 wins / 1 loss** (search time ratio ~0.92×); FLA upward **−0.01312645**, **1 win / 3 losses**, mean ratio ~1.05×.
- Cost-seeded NSGA-II SJF mean **+0.01086153**, **4 wins / 0 losses**, search ratio ~1.06×; upward mean **+0.00281526**, 3 wins / 1 loss.
- This is limited two-DAG development evidence that SJF may help the existing NSGA-II baseline, rather than proof FLA algorithm operators are superior. A known fixed shortest-task rule is NOT new algorithm novelty.
- Full old insertion/FIFO versus full ready/FIFO: FLA mean ready−old **−0.00234105**, 2 wins / 2 losses; NSGA-II **+0.00296273**, 4 wins / 0 losses (3× sensitivity noted one sign reversal for NSGA).
- Three FIFO restarts vs single FIFO-ready FLA mean +0.00144905, **2 wins / 2 losses**: independent restarts themselves change outcomes, supporting the need for matched controls.

Solver comparison in same policy: FLA−NSGA-II mean HV **+0.01710169** on original FIFO/insertion, **+0.01179791** on ready/FIFO, **+0.00257166** on full SJF, **−0.00414379** on full upward, **+0.01887401** on three FIFO restarts, **+0.01671077** on three-priority restarts. These descriptive margins fluctuate by policy, and multiple prior gates gave opposite conclusions; do not treat them as a robust FLA-vs-NSGA-II victory.

## Necessary honesty, scope, and publication decision

1. Only two previously studied DAG families and two seeds, with repeated same VM type set and a staggered speed profile. Multiple selected/related K16 points per block are NOT independent workflow-family samples. No hypothesis-test significance is justified.
2. **K16 true HV** is real simulator output for 16 prospectively selected planner candidates, not an exhaustive simulator Pareto optimum, full-front HV, or general proof.
3. Equal **counted genotype calls** is not CPU-matched fitness cost or number of all internal model forecasts. Full vs split can change search diversity. Search_ms, replay_ms, independent seed offsets and duplicate physical policy+mapping counts were retained for audit.
4. Existing v18 "max decoder disagreement" relocation had mixed Montage vs CyberShake results and substantial additional runtime. Reusing that mechanism without a critical-path Pareto reason is unsupported. Literature already co-evolves task-priority and VM choice, so naive joint encoding alone is not novel.
5. Hold unchanged: **`master`**, original FLA v12 and NSGA-II default objective, runtime FIFO, and experimental ready/priority flags OFF. All source changes remain on `fla-baseline`.

**Next sound step:** If further FLA innovation is attempted, preregister an *FLA-specific* queue-conflict critical-path and Pareto-budgeted proposal mechanism with strict no-leakage rules, equal true simulator budget, explicit internal prediction-computation counter and time-matched baseline, and test on new DAX instances/independent seeds before promoting. A minor SJF or portfolio HV increase on the current two DAGs is NOT publication-ready.
