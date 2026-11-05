# GitHub independently confirmed complete planned-front true-HV coverage (2026-11-05)

**CONFIRMED.** Source archived 4/4 SUCCESS [41986249710](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41986249710); independently audited read-only GitHub [41986434656, attempt 2 SUCCESS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41986434656); local separate ZIP-based HV calculations agreed with the completed GitHub script.

1. Frozen hypothesis before full-front simulator outcomes: `docs/FLA_FULL_VISITED_PLANNED_ND_TRUE_REPLAY_FROZEN_2026-11-05.md`.
2. The source earlier run [41985327148](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41985327148) captured all original 3030 genotype evaluations per algorithm, with K16 actual true replays, across Montage_50 and Sipht_60, seeds 981/982, FLA-v12 and seeded NSGA-II.
3. The new opt-in full planned-nondominated diagnostic never chose a candidate based on simulator truth. It recorded the complete original visited TaskID->VMID history and replayed ALL strictly PLANNED non-dominated original observed mappings, including candidates omitted by original K16.
4. All **eight entire original search-history SHA256 values matched**, the complete original visited planned objective-value dictionaries matched, all original selected physical TaskID->VMID genotypes were checked, and the exact source Java nondomination set was reproduced for each arm. 126 within-arm overlapping physical mappings had consistent independent true simulator objectives.
5. Full front required **301 actual WorkflowSim replay records** versus original **128 K16 records**, including 175 additional within-arm physical genotypes not simulated in original K16. This is a larger oracle-budget diagnostic, NOT equal-K16 optimizer superiority.

## Independently recomputed common-reference true HV

One common 1.5× actual reference per (workflow,seed) across both solvers, original K16 AND full ND replays.

| Workflow | Seed | Solver | Full true replays | Extra distinct maps vs K16 | Extra individually positive actual-HV additions | Full ND − K16 actual normalized HV |
|---|---:|---|---:|---:|---:|---:|
| Montage_50 | 981 | FLA-v12 | 31 | 15 | 10 | +0.000016559 |
| Montage_50 | 981 | NSGA-II | 45 | 29 | 25 | +0.000723925 |
| Montage_50 | 982 | FLA-v12 | 45 | 29 | 25 | +0.000040048 |
| Montage_50 | 982 | NSGA-II | 40 | 24 | 13 | +0.000096920 |
| Sipht_60 | 981 | FLA-v12 | 33 | 17 | 12 | +0.000000017 |
| Sipht_60 | 981 | NSGA-II | 65 | 49 | 38 | +0.000002028 |
| Sipht_60 | 982 | FLA-v12 | 28 | 12 | 9 | +0.000000049 |
| Sipht_60 | 982 | NSGA-II | 14 | 0 | 0 | +0.000000000 |

- FLA-v12 four-block mean ΔHV = **+0.000014168** (all four positive but minuscule).
- NSGA-II mean = **+0.000205718**, concentrated in Montage_50 seed981. One original K16 contains two additional planning-dominated maps beyond the full planned ND set; both sets yield the same true HV in that case.
- Exactly **301+128 original simulator replay records** were compared across experiments, not 429 independent genotypes. Reusing simulator-truth outcomes only occurs in **retrospective analysis**.
- The first full-ND source run [41986114143](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41986114143) failed before replay due to disabled history capture in K=0, then the code was corrected and source run 41986249710 completed. The first independent audit attempt ran before the four source archives were complete and rejected missing evidence; retry attempt 2 SUCCEEDED with unchanged audit logic. Both failure cases are preserved.

## Research implication and stop rule

This gives unusually direct support for **real simulator HV saturation of the PLANNING-nondominated set, within these two familiar DAG families and two seeds**, not just an artifact of using planning objectives. Paying 15–49 additional real simulator calls per case yields tiny true HV improvements in most cases.

**Do not infer that the full 3030-genotype visited true Pareto front is saturated**, since planning-dominated assignments remain mostly unobserved. An independently stratified true-label audit of the dominated sector might find meaningful ranking errors (previous source observed 45 incorrect predicted dominances among 939 comparable pairs), but this is a separate hypothesis needing fixed-K and prospective sampling. No SCI FLA-superiority claim, no unseen-family holdout or equal-total-compute-time advantage.

Next target: decision consequence of model misranking on planning-dominated candidates, NOT more K16 frontend coverage tricks or Hamming-only novelty operators. `master` remains unchanged.
