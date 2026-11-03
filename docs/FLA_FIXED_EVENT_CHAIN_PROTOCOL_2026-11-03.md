# Frozen WorkflowSim event-chain pilot — 2026-11-03

## Scientific question
The previous 16 fixed-mapping replay traces found 9,120 same-VM ordering-inversion task-pair observations, all among DAX-unrelated tasks (count includes duplicated physical schedules). Does a task-pair inversion already exist by the time the engine marks a job ready, or does it first appear after scheduling/dispatch?

## Frozen scope (before new event results)
- Reuse original source archive run 41626382711: source profile default, seed 211, `Epigenomics_46` and `CyberShake_100`.
- Use v12 and cost-seeded NSGA-II original K16 assignment candidates **1 and 2**; both `default` and `staggered` VM MIPS profiles. Do not select cases using future event outcomes.
- 2 DAGs × 2 original assignment sources × 2 candidates × 2 VM profiles = 16 actual simulator replays, including repeated physical assignments. Do not count duplicates as independent workloads.
- Passive `-Ddagfla.fixedEventTrace=true` emits `ENGINE_READY`, `SCHEDULER_ARRIVE`, `SCHEDULER_DISPATCH`, `DATACENTER_SUBMIT`, `ENGINE_COMPLETE`, tagged by original Task ID, job ID, mapped VM ID and simulator clock. DATACENTER_SUBMIT also records actual file-transfer delay returned by the simulator.
- Existing passive `-Ddagfla.fixedTaskTrace=true` independently records actual job start and finish; compare timestamps, but do not assert that datacenter submission is identical to actual execution start.
- The event logger must not modify ready queues, policy choice, assignments, pseudorandom sequence, planned objectives, CloudSim event delay, or cost model. All original default-profile simulator objective values must continue to match archived originals within 1e-6 relative tolerance.

## Checks
1. Require five event labels exactly once per original unclustered task, correct Task ID and VM mapping, nondecreasing timestamps (`ENGINE_READY` ≤ `SCHEDULER_ARRIVE` ≤ `SCHEDULER_DISPATCH` ≤ `DATACENTER_SUBMIT` ≤ `ENGINE_COMPLETE`). Actual job starts and finishes are separately checked for time consistency. If valid CloudSim same-tick mechanics make equality frequent, preserve ties.
2. Build same-VM task pairs; evaluate comparable-pair rank inversions between planned starts and each event timestamp, plus final observed start. Use ties explicitly, never interpret event order from file row order when timestamps tie.
3. Separate DAX ancestor-related from incomparable pairs; preserve all events and worst divergences. No reward feedback or algorithm tuning in this pilot.
4. If an event is emitted more than once because of the internal engine protocol, report this as a failing/unknown trace assumption, not an optimizer defect.

This is a mechanistic pilot on known DAGs, not independent validation of novel algorithm performance.
