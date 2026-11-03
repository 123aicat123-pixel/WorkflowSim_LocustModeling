# Fixed assignment per-task timeline tracing — frozen validation protocol (2026-11-03)

**Pre-outcome scope.** Research-only opt-in trace, no optimizer changes. Source mappings and real replay original source are locked to the successful fixed-speed study (original v17 default archive Actions 41626382711, seed 211). Two workflow instances (`Epigenomics_46`, `CyberShake_100`), two assignment sources (`DAG-Pareto-FLA[v12-hvbandit]`, `NSGA-II[costseed]`), original candidate indices **1 and 2**, two VM-speed profiles (`default`, `staggered`), exactly 16 fresh single-schedule WorkflowSim replays across 8 unique frozen assignments.

## Trace and join definitions
- Java opt-in `-Ddagfla.fixedTaskTrace=true` saves post-selection `StageInAwareScheduleEvaluator.Result.starts/finishes` in the planning algorithm's detached last-run snapshot. These are *planning estimates* in the same topological task order as the original Task IDs.
- Each completed *unclustered COMPUTE* Job's `getTaskList().get(0).getCloudletId()` supplies the **original Task ID**, not `job.getCloudletId()` (which is a different indexing scheme). Track actual `Job.getExecStartTime()`, `Job.getFinishTime()`, `Job.getActualCPUTime()`, VM ID, and original task cloudlet length; do not read unobserved future simulator labels.
- `cpu_minus_compute_seconds = job actual CPU time - (original task total length/VM MIPS)` is only a **residual proxy**, not independently measured stage-in and not a causal decomposition. It can include simulator accounting peculiarities; negative beyond tolerance fails.
- Compute `actual_start-planned_start` and `actual_finish-planned_finish` per Task. The actual job start may not match submission time; do not silently attribute differences to stage-in.
- Preserve the default/off behavior: with `fixedTaskTrace=false`, no trace CSV is written, original FLA and NSGA search remain unchanged. The existing whole-run makespan/cost parity assertions remain active.

## Validation and analysis
1. Compile all Java source fresh, test the new diagnostic mode on archived **same** mappings under both speed profiles.
2. Require exact mapping identity for each simulator replay; require original default-profile objective parity (relative 1e-6).
3. Require exactly the expected 8 frozen genotypes × 2 profiles and one task-trace record for every original mapping Task ID. No duplicate task ID in one replay, valid predicted and actual timing, valid VM ID.
4. For each task, report absolute start error and finish error; surface top outliers **without** claiming they are caused by stage-in or VM queueing. Preserve all CSVs and raw replay stdout.
5. Compare stages with the profile in a descriptive way; no model fitting, no search threshold retuning or task-time correction in this pilot.
6. Maintain `master` unchanged; do not promote variant, claim an algorithm win or paper-level significance.

**Limitations:** source mappings are selected default-profile K16 prefixes from previously explored DAGs, and thus not an untouched holdout. The observed task timings do not alone identify why the planned decoder or WorkflowSim disagree (possible dispatch, file-cache, stage-in, event scheduling); later mechanism tests need direct independent stage-in logs and a controlled replay.
