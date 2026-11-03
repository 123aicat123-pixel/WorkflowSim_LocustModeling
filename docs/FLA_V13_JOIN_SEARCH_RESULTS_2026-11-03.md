# v13 DAG fan-in join locality — development search-operator pilot (2026-11-03)

**Decision: REJECT v13 as a promoted optimizer variant. Keep v12 and the prior default settings unchanged.** This is a completed negative result, not a successful FLA innovation.

## Immutable source, real execution, reproduction

- Source pilot implementation: [77066e9ab](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/commit/77066e9ab2a487ab6a9768f6292f8d55a17608f4).
- Frozen v13 experiment workflow / analyzer: [40c08728](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/commit/40c08728eae0e46e4f678781a1689ea6b4eef62f).
- [Successful 18/18 actual simulator matrix and aggregate report, Actions 41612325067](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41612325067), artifact `v13-search-report-41612325067` ID `13220205776`.
- [Successful v13 source compilation / inherited regression CI, Actions 41612044262](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41612044262).
- Branch `fla-baseline` only; `master` not changed.

## New operator, compared without extra optimizer calls

v13 preserves the v12 DO/EO/SSO FLA phase-wise UCB operator selector and its actual PLANNED-archive HV reward, but substitutes one UCB arm. Instead of v12 cheap critical-task surrogate reassignment, it chooses high-incoming-cross-VM-transfer fan-in DAG tasks and considers co-locating join/parent tasks using approximate network traffic, optimistic service time and a weak cost guard. The proposal never calls the shared objective evaluator itself: every offspring still gets exactly one real stage-in-aware planning evaluation. This is a NEW discretized heuristic, not an original mathematical FLA equation.

Predeclared development design: previously seen CyberShake_50, Montage_50, Sipht_60 × two VM speed configurations (`default`, synthetic within-tier `staggered`) × three fresh algorithm seeds (141,142,143). Per 18 scenario blocks, three algorithms `v12-hvbandit`, `v13-join`, `NSGA-II[costseed]` used identical first two low-cost assignment seeds (asserted), exactly 3030 optimizer evaluations, `pareto-cover` K16 true WorkflowSim replays, and the same simulator scoring reference for all three. The primary HV reference per DAG/speed uses 1.5× the maximum **PLANNED** selected makespan and cost across all algorithms and seeds +1; 3× secondary. The independent aggregate asserts all actual points are within bounds; it does not refit the reference to true outcomes.

## Results (actual K16 simulator HV, mean of three independent algorithm seeds)

| Workflow | VM regime | v13 vs v12 | v13 wins /3 | v13 vs NSGA-II | v12 vs NSGA-II |
|---|---|---:|---:|---:|---:|
| CyberShake_50 | default | −0.7630% | 0/3 | −3.0697% | −2.3199% |
| CyberShake_50 | staggered | −0.0463% | 1/3 | −1.1639% | −1.1207% |
| Montage_50 | default | −0.6369% | 1/3 | −0.3439% | +0.2912% |
| Montage_50 | staggered | **−5.9717%** | **0/3** | −5.1459% | +0.8688% |
| Sipht_60 | default | −2.2421% | 2/3 | −2.5736% | −0.3279% |
| Sipht_60 | staggered | −0.7329% | 1/3 | −2.2071% | −1.4987% |

- Pooled **primary** 1.5× reference, 18 paired cases: v13 versus v12 **−1.732129%** (5/18 wins); v13 versus seeded NSGA-II **−2.417361%**.
- **Secondary** 3× reference: v13 versus v12 **−0.821612%** (6/18 wins); versus seeded NSGA-II **−1.161262%**.
- Individual negative cases include Montage_50 staggered seed 143 **−8.9274%** versus v12 and Sipht_60 default seed 141 **−7.7982%**. Keep them in the source CSV; do not suppress outliers.
- The experiment is a DEVELOPMENT ablation on previously explored families; no statistical superiority or generalized inferential claim is supported.

## Separate source-log verification: v13 operator attempted vs changed

I inspected all 18 actual successful compare-job logs (not the aggregate HV reporter) for `FLA_JOIN_AWARE attempted=... changed=... evaluations=3030`. Totals: **18,015 attempted activations** and **11,758 changed offsprings**, spanning 12 of the 18 blocks. Exactly **zero changes in all six CyberShake_50 blocks**, although bandit attempts ranged 978–1091 by run. For Montage_50 and Sipht_60, all 12 blocks had nonzero changes; examples Montage default seed 142 had 1164 attempts and 1160 changes, Sipht staggered seed 142 had 1091 attempts and 1075 changes.

This proves the candidate operator often materially altered search genotypes on Montage/Sipht and did not do so in CyberShake, explaining why aggregate improvement should not be attributed to universally active DAG sensitivity. **It does not prove why** CyberShake failed to change (e.g., transfer-size semantics, graph fan-in, zero effective measured traffic, or metadata extraction). A targeted no-search inspection of DAX joins and incoming file-edge metadata is needed to distinguish those mechanisms.

## Targeted read-only DAX structure diagnosis (no additional optimization or simulator calls)

Parsed original `config/dax/CyberShake_50.xml`, `Montage_50.xml` and `Sipht_60.xml` directly from the same `fla-baseline` branch. Counted each DAX `child`'s incoming `parent` links and matched each parent's declared OUTPUT filename with the child's INPUT filename exactly (the same dependency-file matching principle used by `prepareCriticalProxy`).

| DAX | Declared jobs | Multi-parent join nodes | Parent edges entering joins | Matching positive-size producer→consumer file edges entering joins |
|---|---:|---:|---:|---:|
| CyberShake_50 | 50 | 2 | 44 | **0** |
| Montage_50 | 50 | 32 | 96 | **96** |
| Sipht_60 | 58 (despite filename) | 8 | 58 | **58** |

Both CyberShake joins (`ID00000` and `ID00001`) have 22 listed parents but none has a matching declared producer OUTPUT file consumed as an INPUT by the join. Thus the operator's strict requirement for positive measured cross-VM parent-to-child traffic provides a direct structural explanation for its 0/6 genotype-change cases **under the original DAX metadata**, assuming WorkflowSim's parser retains these relationships as declared. This is a read-only source-file diagnosis, not a separate runtime instrumentation proof. The other DAGs have multiple join nodes with matched transfer files and exhibited positive operator changes.

Important: `Sipht_60.xml` declares **58 jobs**, not 60. Benchmark labels should report actual DAX job count, and never silently assume the filename equals task count.

## Consequences

1. **Reject v13 for production/default selection.** Do not silently set v13 as an improvement over v12. Its positive cases are insufficient given the prespecified negative mean and large regressions.
2. Keep `v13-join` in the experimental variant selector for scientific negative ablations only.
3. If exploring DAG-affinity heuristics further, first diagnose the CyberShake no-op cause and why active Montage locality repair degraded the simulator front. Avoid treating the same 18 now-inspected scenarios as independent held-out validation for threshold-tuned v14.
4. Distinguish real search operator changes from K16 post-search candidate replay policies, and compare all search methods to equally initialized NSGA-II. Publication claims require entirely independent scientific DAGs, VM regimes, broader seeds, and uncertainty at workflow-family level.
