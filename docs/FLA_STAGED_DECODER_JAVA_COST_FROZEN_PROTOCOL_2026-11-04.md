# Java model-cost microbenchmark frozen before timing results — 2026-11-04

The retrospective 96 fixed-mapping staged-decoder study (original real WorkflowSim source 41695356307, analyzer 41775295948) produced identical selected-K and actual normalized HV to FULL-READY in 6/6 blocks for K2/T4, and 6/6 for K4/T8. K4/T4 missed one block by 0.0699021 percentage points. READY-model *call count* is not Java wall-clock speedup.

**Predeclared no-simulator benchmark**: use the REAL `StageInAwareScheduleEvaluator` and `ReadyQueueScheduleEvaluator` Java classes and actual `Task` and `CondorVM` objects (not Python surrogates), but deterministic **synthetic** DAGs of 30, 100 and 200 tasks, 16 VMs, no file input transfer, and three predeclared parent patterns: chain (i−1), forked (i−1 when i%3==0 and i−4 when i>=4), independent (none). 16 deterministic complete mappings per case. Note synthetic tasks **do not replicate real DAX file I/O**, VM contention or CloudSim wall-clock; timed figures apply only to these controlled evaluator workloads.

Before measurement initialize both evaluator objects, verify their per-mapping Makespan and Cost finite positive and deterministically repeated. Warm up exactly 4×16 evaluations per class and case. Then 6 rounds of 8 repeats ×16 mappings per model with alternating old→ready and ready→old model ordering by round, using `System.nanoTime` around ALL 16 per-model calculations, volatile checksums to prevent JIT dead-code elimination. Do not print within timed loops. Record all 18 per-model round-level timings (3 DAG sizes × 3 structures × 2 models × 6 rounds = 108 records), and median ns per candidate per model.

Derived computational work for identical 16 candidate genotypes:
- OLD-only = 16×median old ns;
- FULL-READY = 16×median ready ns;
- STAGED T4 = 16×old + 4×ready;
- STAGED T8 = 16×old + 8×ready.
These are sum-of-model timing PROXIES only, **not measured end-to-end** pipeline runtime; selection enumeration, HashMap generation, VM simulation and I/O overhead omitted, and Java JIT may change timings. A result showing STAGED heavier than FULL-READY disproves a simplistic speedup claim even if it reduces high-fidelity calls.

All original default FLA/NSGA and FIFO paths remain untouched; data is not new real WorkflowSim optimization evidence. Timing variation, negative speedups and all cases must be archived. No promotion based on this synthetic timing.
