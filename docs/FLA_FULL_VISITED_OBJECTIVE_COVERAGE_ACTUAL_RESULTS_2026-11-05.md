# Full source visited planning-Pareto coverage: actual diagnostic results (2026-11-05)

**Outcome: PASS full source/exact-history audit; post-search K16 ALREADY saturates PLANNING model hypervolume, but TRUE full-visited Pareto quality remains unobserved. No improved FLA claim.**

## Evidence
- Research protocol predeclared BEFORE new outcomes: `docs/FLA_VISITED_OBJECTIVE_COVERAGE_FROZEN_2026-11-05.md` (commit `b66e620`).
- Original real-simulator [source run 41985327148](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41985327148): 4/4 jobs SUCCESS, `Montage_50` and `Sipht_60` × new optimizer seeds 981/982, original `DAG-Pareto-FLA[v12-hvbandit]` and `NSGA-II[costseed]` unchanged. Each 3030 counted planning-model evaluations and K16 actual original FIFO WorkflowSim replays. Total **128 true simulator replay records** and ~2,600–3,000 distinct planning-visited maps per solver.
- Passive `-Ddagfla.exportVisitedObjectiveSpace=true` records ALL first-write distinct original visited TaskID→VMID assignments and full-precision planned Makespan, Cost BEFORE any actual simulator output is available. It does not call READY, the scheduler again, or the real simulator.
- Independent [audit run 41985408148 attempt 2 SUCCESS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41985408148): original run 4 source archives recovered, the full ordered unique genotype history SHA256 reproduced byte-for-byte using the canonical mapping and exact Java double bits, and K16 selected mappings matched their original planned objective records. Identical source Git SHA across all four source jobs. First audit attempt launched while Sipht source artifacts were still uploading and correctly rejected missing blocks; rerun after 4/4 source success did not change audit code.
- A separate [export-ON/OFF nonintrusion Actions run 41985594827 SUCCESS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41985594827) repeated source Montage_25 pop8 gen9 K2 both ways: original ordered genotype fingerprints, summary numerical objectives/HV and exact TaskID→VMID true K2 replay rows were identical. Only passive extra CSV and timing differed.

## Source-complete planning model results

One shared 1.5× reference based on the coordinatewise maximum of ALL visited PLANNED points across both solvers in each (workflow,seed) block; never use actual simulator labels to define or tune the planned front.

| Workflow | Seed | Solver | Distinct source visited | Full visited planned ND points | K16 selected planned ND points | K16 / full visited planned normalized HV |
|---|---:|---|---:|---:|---:|---:|
| Montage_50 | 981 | FLA-v12 | 2992 | 31 | 16 | 0.999995230 |
| Montage_50 | 981 | NSGA-II | 2822 | 45 | 16 | 0.999992450 |
| Montage_50 | 982 | FLA-v12 | 3000 | 45 | 16 | 0.999992258 |
| Montage_50 | 982 | NSGA-II | 2833 | 40 | 16 | 0.999992592 |
| Sipht_60 | 981 | FLA-v12 | 2851 | 33 | 16 | 0.999999996 |
| Sipht_60 | 981 | NSGA-II | 2659 | 65 | 16 | 0.999999509 |
| Sipht_60 | 982 | FLA-v12 | 2968 | 28 | 16 | 0.999999991 |
| Sipht_60 | 982 | NSGA-II | 2624 | 14 | 14 | 1.000000000 |

All K16/total-PREDICTED-HV ratios exceed 0.999992. The ratio is high even when the full planned front has >16 nondominated objective values; this does NOT mean K16 contains every ND point or that 16 covers all tradeoff diversity. The tiny objective-space HV difference is a property of the frozen StageInAware PLANNING model and the chosen common reference, not a measured true front ceiling.

## Mechanistic decision

1. **Reject a purely planning-HV-enhancing post-search selector as the immediate SCI algorithm route.** Under the same model and source visited set, the K16 selector already captures >99.9992% of all visited planned HV in all eight development cases. Simply changing how 16 are picked has low available predicted-HV leverage.
2. The still-open scientific question is the true simulator behavior of the **unreplayed full planned nondominated set** (and, separately, planning-dominated false exclusions). The full visited true Pareto front is unknown and no upper bound over its true HV follows from these ratios.
3. Future prospectively frozen diagnostic could replay each *not-yet-simulated* full-visited planned ND mapping with a different explicit physical simulator budget and compare the true-HV gain to K16. Control for source population identity, source SHA, and distinguish extra simulator expense from an equal-K selector.
4. If the extra true-HV gain is also tiny across families, spending more time on cheap-front coverage heuristics is unsupported. If sizeable, investigate model fidelity rather than simply invent another diversity mutation.
5. This does not prove FLA-v12 superiority or original published FLA formula fidelity. It is a development data diagnostic (two familiar DAG families, two seeds), not independent-paper holdout. No CPU parity or statistical significance claim.

**Disposition: completed 4/4 source, 128 actual replays, ON/OFF noninterference PASS, full source SHA audit PASS, no new superior optimization method.**
