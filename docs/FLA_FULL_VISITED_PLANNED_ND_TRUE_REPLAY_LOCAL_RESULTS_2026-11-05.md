# Original complete planned-front true WorkflowSim replay — local independent source-archive analysis (2026-11-05)

**Scientific result: measured TRUE HV gains are mostly tiny.** Four clean source jobs completed, independent local original-ZIP recomputation PASS. GitHub independent 8-case HV audit [41986434656](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41986434656) was still queued at the time this report was committed; DO NOT label that GitHub audit as PASS until its actual log is verified.

## Preregistered context and original provenance
- Frozen protocol `docs/FLA_FULL_VISITED_PLANNED_ND_TRUE_REPLAY_FROZEN_2026-11-05.md` at `bc829485` before new true labels.
- Original pop30, gen100, FIFO STATIC, default VM FLA-v12 and costseed NSGA-II search: unchanged old K16 source [41985327148](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41985327148) 4/4 SUCCESS, 128 original K16 simulator replay rows; original exact pre-replay source histories and cheap planning scores exported.
- Opt-in complete **source-visited planned ND** replay from [41986249710](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41986249710) 4/4 SUCCESS, **301 actual simulator replay rows**, each solver's variable K equals its distinct planned-ND front size, range 14–65. First run [41986114143](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41986114143) failed a pre-simulator history-capture guard and is explicitly excluded; corrected run 41986249710 is the only complete source.
- These 301 fresh *replay records* contain 126 physical mappings that were also in the original K16 and **175 additional distinct per-(workflow,seed,solver) mapping observations**. Repeated mapping true results agree within relative 1e-7.
- **All eight exact ordered original search-history SHA256 fingerprints matched** between the old K16 and new complete-ND source replays. The entire original pre-replay TaskID→VMID planning objective map was checked for identity, and the exact Java non-dominated election from all first-write source visited maps matched the new actual simulator assignment set in all 8 cases. No true simulator labels were used in source selection.
- Local analysis read eight original GitHub artifact ZIP files directly; it was not copied from an aggregate report. One shared same-(workflow,seed) normalized 2D **true** HV reference (1.5× coordinatewise actual max across old K16, new full ND and both solvers) was used, avoiding self-referenced cross-arm HV scores.

## Direct matched true-HV results

| Workflow | Seed | Solver | Original K16 | Full planned ND replay budget | Extra actual normalized HV: full ND minus K16 |
|---|---:|---|---:|---:|---:|
| Montage_50 | 981 | FLA-v12 | 16 | 31 | +0.000016559 |
| Montage_50 | 981 | NSGA-II | 16 | 45 | +0.000723925 |
| Montage_50 | 982 | FLA-v12 | 16 | 45 | +0.000040048 |
| Montage_50 | 982 | NSGA-II | 16 | 40 | +0.000096920 |
| Sipht_60 | 981 | FLA-v12 | 16 | 33 | +0.000000017 |
| Sipht_60 | 981 | NSGA-II | 16 | 65 | +0.000002028 |
| Sipht_60 | 982 | FLA-v12 | 16 | 28 | +0.000000049 |
| Sipht_60 | 982 | NSGA-II | 16 | 14 | +0.000000000 |

- FLA four-block mean actual normalized ΔHV = **+0.000014168**, versus extra full-ND real simulator calls of +15, +29, +17, +12 per block. All four have positive but tiny actual gains.
- NSGA-II four-block mean ΔHV = **+0.000205718**, but mostly Montage_50 seed981 (+0.000723925); 3 positive, 1 tied. One full ND front had 14 schemes, fewer than original K16 (which included two planned-dominated schemes); its true HV still tied.
- In each case original K16 selected schemes that were ND in the full planning front were present with the same actual results. The union of the original K16 plus complete planned ND showed the same measured true HV as the complete planned ND on this cohort, even when the full ND front had fewer than 16; this is a retrospective observed-set fact, not a prospective algorithm property.

## Interpretive limit and next gate
- Unlike the earlier >99.9992% **planned** HV coverage result, this validates that the actual true HV gain from *replaying the remaining planned ND candidates* is very small in two familiar DAG families and two development seeds. It does **not** mean the FULL 3030-visited true Pareto front has saturated; most planning-dominated visited genotypes have NOT been simulated and may contain missed true-nondominated candidates.
- Extra real simulator calls are substantial and comparisons are **not budget-fair**: this is a measurement ablation, not a better FLA algorithm. This source does not support a robust published FLA superiority claim.
- The most interesting unresolved question is the unobserved **planned-dominated** sector with rank misclassifications previously evidenced by the matched random K16 study (45/939 incorrect predicted pair dominances). A defensible next experiment must preregister a selection-independent stratified simulator audit with fixed physical K across strata/families and preserve source map identity, not retune an existing epsilon heuristic on these inspected cases.
- All results on `fla-baseline`, `master` unchanged.

**Verdict: new real simulator model-coverage measurement SUCCESS; improved FLA search algorithm STILL NOT DEMONSTRATED.**
