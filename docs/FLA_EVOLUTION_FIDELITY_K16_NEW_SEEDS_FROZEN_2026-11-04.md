# Preregistered K16 reproduction of cache-matched evolutionary fidelity (2026-11-04)

**Status: prospective experiment design, NOT an observed result and NOT a new algorithm.** Frozen before seeing the new seeds' actual WorkflowSim outputs. The earlier K8 matched-cache 801/802 study has both positive and negative results; no source outcome or 1% gate parameter is retuned here.

## Fixed conditions

- Historically studied DAG families only: `CyberShake_50`, `Sipht_60`. They are **development/replication families, not an independent unseen-family holdout**.
- Two new optimizer seeds **901 and 902**, not the 801/802 seeds used for the original K8 source; unchanged 16 default CondorVMs, original FIFO STATIC WorkflowSim simulator, same JVM and DAX reference configuration for every arm.
- Original `DAG-Pareto-FLA[v12-hvbandit]` and seeded `NSGA-II[costseed]`, same two deterministic first genotypes as established by `v12-nsga-ready-pair`; pop=30, gens=100, exactly **3030 counted genotype fitness visits** per optimizer.
- Identical first-write TaskID->VMID genotype memoization engine in ALL arms. No dynamic score updates to previously returned genotypes:
  1. `old-cached`, READY quota 0;
  2. `ready-cached`, full quota 3030;
  3. `periodic`, READY quota 378, pre-existing fixed token release;
  4. `risk`, READY quota 378, pre-existing 1% cheap-front gate.
- Exactly **K=16** distinct planned-only `pareto-cover` selected assignments per optimizer/mode/seed/DAG, each replayed once by original WorkflowSim. No selection on true simulator labels; assignment identity and source SHA recorded.
- Primary measure: normalized **actual** 2D hypervolume (Makespan and Cost minimized). Freeze a **single 1.5x actual reference point for all 8 solver/mode arms within the same DAG and seed**, defined from all corresponding 128 simulated points. Repeat sensitivity at 3.0x. Reference varies by DAG/seed; do not compare raw HV magnitudes across families as if the reference was the same.
- Full design: 2 DAX x 2 seeds x 4 objective modes = **16 source GitHub Actions jobs**, each running 2 solvers and K16 real replays per solver. Thus **512 original WorkflowSim simulator replays** if all jobs succeed; the count is a planned budget, not yet actual execution evidence.
- Verify per solver original 3030 genotype visits; `distinct + cache_hits = visits`; OLD mode `old=distinct,ready=0`; READY mode `old=0,ready=distinct`; mixed mode `old=distinct,ready<=378`. Keep actual OLD/READY physical call counts, decoder nanoseconds, full search elapsed and simulator replay elapsed separately.
- Preserve EVERY tie and loss in paired FLA and NSGA results. Compare `periodic` and `risk` vs both cached controls. Report individual 4 DAG/seed blocks and no pseudo-independent treatment of 16 simulator replay points as 16 independent experimental units.
- No equal wall-time claim follows from equal fitness visits or READY quotas; secondary equal-compute-time validation remains necessary. No significance, no novelty, no Q1 conclusion from two familiar families x two new seeds.
- K16 extension is enabled **only via new explicit JVM opt-in** `-Ddagfla.evolutionK16Confirmation=true`; without that flag the existing original frozen K8-only guard remains unchanged. Never modify master or FIFO default.
- Abort if a source job lacks its two distinct optimizer arms, counts, original actual K16 replay records, valid finite objectives, or reproducible source SHA. Independent audit reads only archived original outcomes after the source jobs complete. No simulator truth may inform search or phenotype choice.

**Gate decision after results:** stable per-workflow improvements must survive 1.5x and 3.0x normalized true HV, realistic compute work counts and a later independent-family/time-matched test before any promotion. If not, retain negative result and do not rename the mixed method as an improved FLA.
