# v21 dominated near8/uniform8: FINAL independent source-audited result, 2026-11-05

**Original source 8/8 SUCCESS and independent audit PASS. The near-front proxy DOES NOT robustly improve original FLA-v12 actual hypervolume; many false planning-dominance observations are not valuable HV contributions. Do not promote as an SCI optimizer.**

## Exact provenance
- Frozen preregistration before simulator outcomes: `docs/FLA_V21_DOMINATED_NEAR_UNIFORM_FROZEN_2026-11-05.md`.
- Original [source workflow 41990207133](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41990207133): all 8 scenario jobs SUCCESS, original SHA `9f4d0c4250068cf60be32aa06a92c83381bfb5b1`, four familiar workflows Montage_50, Sipht_60, Epigenomics_46, CyberShake_30, seeds 991,992; original FLA-v12 and seeded NSGA-II 3030 original fitness visits each. Original K16 actual replays plus 8 planning-dominated near and 8 planning-dominated uniform source-replay candidates, **512 actual simulator replay records**.
- Independent frozen [GitHub audit 41990449010 attempt 2 SUCCESS](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41990449010), artifact `fla-v21-dominated-independent-hv-41990449010`, ID 13398956780: all 8 raw archives present, exact 16 ordered original source-history SHA256 from complete visited planned objectives, 16 ordinary K16 and correct 8+8 extra strict planned-dominated unique mappings per optimizer, one original source SHA, positive actual objectives, new shared same-(workflow,seed) true-HV reference, negative findings retained.
- Audit first attempt failed before inputs were available (0 downloaded artifacts) and the SAME original audit was rerun after all source artifacts had been uploaded. A separate local analysis directly parsed the 8 GitHub source ZIPs and reproduced all 16 paired actual HV values without relying on the formal summary.

## Source-confirmed actual HV contrasts

Near8 − uniform8 additional real HV, 1.5× common *actual* reference:

| Workflow | Seed | FLA-v12 | NSGA-II |
|---|---:|---:|---:|
| Montage_50 | 991 | +0.000000000 | +0.000000000 |
| Montage_50 | 992 | +0.000008066 | +0.000003812 |
| Sipht_60 | 991 | +0.000000016 | +0.000000000 |
| Sipht_60 | 992 | +0.000000000 | +0.000000001 |
| Epigenomics_46 | 991 | −0.000088700 | +0.000000027 |
| Epigenomics_46 | 992 | **−0.001241504** | +0.000000105 |
| CyberShake_30 | 991 | +0.000000000 | +0.000000000 |
| CyberShake_30 | 992 | −0.000010838 | +0.000000746 |

- **FLA-v12**: mean **−0.000166620**, wins/ties/losses **2/3/3**.
- **NSGA-II**: mean +0.000000586, wins/ties/losses **6/2/0**, numerically tiny gains. These are only extra K8 simulator diagnostic increments, not head-to-head full optimizer performance.
- Particularly clear mismatch between *false planned dominance count* and true HV: for Montage_50 seed991 FLA, near8 found **7** false planned exclusions but increased actual HV **0**; uniform8 found 0. Sipht_60 seed991 FLA near8 found **5** false exclusions but its actual HV gain was only **+0.000000016**.
- Epigenomics_46 seed992 FLA near8 found 1 false exclusion, uniform8 found 2; uniform8 added **+0.001241941** actual HV vs near8's +0.000000437. This case drives much of the negative mean. The prior simple planned normalized objective-distance-to-front is not an effective general true-HV rescue priority rule.
- A planned strict dominator becoming truly incomparable is not equivalent to a globally useful candidate: the point may still be truly dominated by another K16 point or cover negligible unoccupied objective area.

## Publication and next decision
Do **not** tune near8/uniform8 quotas or thresholds on seen 991/992 source outcomes then call them held out. Replays are in familiar DAG families and do not constitute independent out-of-family proof; no 20-seed statistical inference or matched total K16 physical simulator budget result follows. This study strengthens the methodology/reliability evidence of planning-vs-simulator Pareto selection error, but does not establish a superior FLA optimizer.

Next defensible step: **validate consequence-aware false-dominance risk** with physical DAG/event-queue features and a separate full K16 selector plus a fixed-cost random/sham comparison. First identify whether any safe planned-only score predicts actual marginal HV better than near-front distance on calibration families, then freeze it before untouched-family testing. Equally defensible is pivoting to a methodological scheduling-evaluation-fidelity paper based on source-verified negative results.

All changes and evidence stay on `fla-baseline`; `master` unchanged.
