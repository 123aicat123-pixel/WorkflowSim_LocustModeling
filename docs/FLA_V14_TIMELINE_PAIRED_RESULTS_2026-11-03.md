# v14 stage-in-aware timeline-guided pair search — failed development ablation

**Status: completed. Reject v14 timeline variant as a replacement for v12.** Equal-budget randomized local-control search performed better on the predeclared primary HV score.

## Actual source and reproducibility

- v14 implementation: [7d1bc83b9ad1634ab0aa15f988ea9c8fdefd8740](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/commit/7d1bc83b9ad1634ab0aa15f988ea9c8fdefd8740), corrected DAG parent-readiness and tested in the [subsequent v14 source commits](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/commits/fla-baseline/).
- Original locked true simulator four-arm experiments: [Actions run 41616676427](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41616676427). **All 12 independent compare jobs completed successfully**. Its overall workflow is **marked failure** because the reporting Python script initially had an unmatched parenthesis. That is a report-script syntax failure, not a simulator failure. Do NOT mislabel the original workflow as overall successful.
- Corrected reporting script and independent **read-only** scoring from the original 12 job artifacts: [Actions run 41617351880](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41617351880) — **SUCCESS**. Report artifact `v14-readonly-report-41617351880`, ID `13221014501`, includes all 24 scale-specific cases and explicit negative cases.
- Java CI passed at [41616392233](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41616392233), including the v14 one-call stage-in-aware trace, DAG parent-ready-time, and immutable snapshot tests.

## Frozen comparison protocol

Previously studied 3 DAG families and instance sizes: `CyberShake_50`, `Montage_50`, `Sipht_60` (last file actually declares 58 jobs). Two VM speed regimes `default` / synthetic `staggered`, two optimizer seeds 151 / 152, 12 scenario blocks. Four arms: (1) FLA v12-hvbandit, (2) v14 random-pair, (3) v14 timeline-pair, and (4) identically cost-seeded NSGA-II.

- All four optimizer arms use exactly 3030 stage-in-aware PLANNING objective evaluations.
- Each variant gets exactly 16 real WorkflowSim replay evaluations of distinct selected assignments via unchanged `pareto-cover` policy. Same initial two cost-seed assignments are asserted for all four arms.
- Each v14 pair variant allocates exactly 1400 of those **3030 counted** target evaluations to local one-gene neighbor trials: this is a reallocation of search breadth, not a bonus 1400 uncharged objective calls. The random-pair control has exactly the same split and budget.
- The first child gets one normal stage-in-aware evaluation plus detached exact **planning-model** schedule starts/finishes. Its neighbor is chosen by latest finish and estimated insertion gap versus uniform random task/VM for control, and receives one counted stage-in-aware target evaluation. The trace is NOT a true WorkflowSim simulator timeline.
- Planned-only, common per-workflow/per-speed 1.5× coordinatewise selected-PLANNED-objective maxima +1 primary HV reference (all arms and two seeds), secondary 3×. Both were checked to enclose all actual simulator scores with no post-hoc refitting.

## Real simulator HV changes, paired across two seeds

| Workflow | Speed | v14 timeline vs v12 | Timeline vs random-pair | Random pair vs v12 | Timeline vs cost-seeded NSGA-II |
|---|---|---:|---:|---:|---:|
| CyberShake_50 | default | −0.8317% | −0.4501% | −0.3839% | −2.1254% |
| CyberShake_50 | staggered | −0.3966% | −0.0732% | −0.3114% | −2.0362% |
| Montage_50 | default | +0.8478% | −1.0031% | +1.8703% | +0.4806% |
| Montage_50 | staggered | +1.1946% | −1.3800% | +2.6290% | +1.4484% |
| Sipht_60 | default | −0.0088% | −0.0882% | +0.0795% | −0.0844% |
| Sipht_60 | staggered | −4.8156% | −5.3625% | +0.5729% | −5.2992% |

**Overall primary 1.5× reference across 12 paired cases:** timeline vs v12 **−0.668389%** (3/12 wins), timeline vs random **−1.392842%** (1/12 wins), timeline vs equally cost-seeded NSGA-II **−1.269390%**. **Secondary 3× reference:** timeline vs v12 **−0.195812%** (6/12 wins), timeline vs random **−0.509632%** (2/12 wins), timeline vs NSGA-II **−0.556810%**. Do not choose the more favorable reference post-hoc.

Worst case: Sipht_60 staggered seed 152, timeline vs v12 **−8.4346%**, vs random **−8.8333%**, vs NSGA-II **−11.5195%**.

## Exact counted local-pair diagnosis

Across 12 cases × 1400 counted pair probes per variant = 16,800 trials each:

| Diagnostic versus its own normal offspring | Timeline-pair | Random-pair |
|---|---:|---:|
| Changed one feasible genotype | 16,800 | 16,800 |
| Neighbor strictly Pareto-dominated the normal child | 1,818 | 1,275 |
| Neighbor strictly Pareto-dominated **by** the normal child | 9,762 | 8,481 |
| Neither strictly dominated the other | 5,220 | 7,044 |

Time-axis guidance is **not merely inactive**: it more often creates a locally better offspring than random selection, but also creates more clearly inferior neighbors. Since every probe consumes a real search evaluation, it sacrifices independent exploration; local per-pair improvement frequency alone does not predict final archive or independent simulator HV.

## Scientific interpretation and boundaries

- This does not establish that the true timeline oracle is intrinsically bad. The latest-finishing-task choice, optimistic stage-in/cache approximation for the proposed VM, single-gene-only neighborhood, per-pair search allocation, and global archive/survivor selection are all possible causes. **None has been causally isolated** by this experiment.
- Do **not** call this a Pareto-acceptance-gated local search. The evaluated local trial is archived/searched under the original nondominated archive and group survivor logic; no direct rejection of a dominated trial before global survivor selection is done. A later guarded variant would be distinct.
- The v14 time axis is the **stage-in-aware planning evaluator**, whose fidelity has been measured but is not identical to real simulator dispatch. Read-only planning diagnostics must be distinguished from true simulator outcome measurement.
- Equal numerical evaluation budgets do not imply equal elapsed time or generalization to previously unseen workflow families. The two seeds and previously researched DAG families are development-only, not statistical confirmation.
- **Recommendation:** keep v12 as current experimental search candidate, leave both v14 variants opt-in and default-off. If pursuing a new v15, first preregister an explicit acceptance-gated policy and an equal-budget random-pair acceptance control; test on new seeds/topologies without retroactively treating the observed v14 failures as independent validation.
