# Conservative interval Pareto decision research: fixed-epsilon and family-blocked actual results (2026-11-04)

**Final verdict of this stage: The conservative interval rule is mathematically defensible CONDITIONALLY on each predicted box covering the real objectives, and its Java pure comparator passes regression. However, the family-blocked empirical maximum-error boxes fail to cover 7/96 held-out true solutions for BOTH OLD and READY, so no transferable guarantee, calibrated uncertainty, novel FLA algorithm, or verified new true HV optimization improvement is established. Preserve false-confidence and out-of-interval records.**

## Provenance and frozen evidence
1. Fixed-width original gate protocol `docs/FLA_INTERVAL_DOMINANCE_96_FROZEN_PROTOCOL_2026-11-04.md`, frozen before results at commit `8bce4b8`; reuses only 96 actual WorkflowSim outcomes from immutable [Actions 41695356307](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41695356307): three historically studied DAG instances `CyberShake_30`, `Epigenomics_46`, `Montage_50` ×2 VM speed profiles ×16 identical independent-of-optimizer Task→VM genotypes per block. The original six source artifacts, TaskID→VM mapping and Java SHA are reverified via unchanged `fla_algorithm_independent_same_mapping_rank_audit.load()`.
2. Exact fixed-width experiment [Actions 41789732628](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41789732628) **SUCCESS**, read-only, no simulator or optimizer calls. Initial [Actions 41789626826](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41789626826) failed because of an extra bracket in Python report source; corrected reporting-only syntax at `4558171`, no change to intervals, source simulation or classifier. Source audit tests five fixed widths 0.1%, 1%, 5%, 10%, 25% for each model. Strict certificate A dominates B iff the upper objective interval endpoint of A is strictly less than the lower endpoint of B on BOTH Makespan AND Cost; otherwise abstain. Real objectives are consulted only for post-decision scoring.
3. Separate family-blocked protocol `docs/FLA_INTERVAL_FAMILY_BLOCKED_FROZEN_2026-11-04.md` frozen at `280e02b` BEFORE blocked analysis. Each fold trains TWO coordinate-specific error-envelope maximums `max(|actual/planned−1|)+1e−9` using ONLY the two other DAX families (64 original source outcomes), and checks the 32 points (two VM profiles) from the held-out DAX family. [Actions 41790033417](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41790033417) **SUCCESS**, 6 family×model calibrations, 12 held-out family/speed/model blocks, 720 pair comparisons per model and zero new simulations.
4. A pure, opt-in Java `sources/org/workflowsim/planning/IntervalParetoCertificate.java` implements strictly conservative TWO-objective band comparison and separate joint box coverage. It neither guesses widths nor calls CloudSim or overrides any existing optimizer. `tests/org/workflowsim/planning/IntervalParetoCertificateTest.java` checks numerical geometry, both dominance orientations, abstention, out-of-bound real observations and invalid widths. [Dedicated Java CI 41790209355](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41790209355) **SUCCESS**, clean all-Java compile and 3 original/new regression oracles PASS.

## Fixed-width real results: six blocks of 16 identical physical mapping genotypes

| Model | Fixed planned-relative epsilon | Real objective JOINT coverage | Certified comparisons /720 | False confident certifications | Mean kept genotypes /16 | True fixed-universe HV recovered |
|---|---:|---:|---:|---:|---:|---:|
| OLD | 0.1% | 49/96 | 425/720 | **2** | 3.17 | 100% |
| OLD | 1% | 76/96 | 361/720 | 0 | 3.50 | 100% |
| OLD | 5% | 82/96 | 229/720 | 0 | 5.67 | 100% |
| OLD | 10% | 88/96 | 114/720 | 0 | 10.00 | 100% |
| OLD | 25% | 93/96 | 0/720 | 0 by abstention | 16.00 | 100% |
| READY | 0.1% | 63/96 | 430/720 | 0 | 3.17 | 100% |
| READY | 1% | 92/96 | 367/720 | 0 | 3.50 | 100% |
| READY | 5% | 95/96 | 237/720 | 0 | 5.17 | 100% |
| READY | 10% | 96/96 | 115/720 | 0 | 10.00 | 100% |
| READY | 25% | 96/96 | 0/720 | 0 by abstention | 16.00 | 100% |

- The OLD 0.1% two FALSE confident Pareto certificates were both on `Epigenomics_46` staggered VM speed: `round_robin` vs `hash_seed17`; and `four_vm_block5` vs `reverse_monotonic_vm16`. The real pairs were incomparable.
- Max observed absolute Makespan error relative to planned prediction: OLD **34.8723%** on Epigenomics_46 default/round_robin; READY **9.3040%** on Epigenomics_46 default/hash_seed17. Maximum observed Cost error **0.0494%** both models in Montage_50/default/hash_seed97. Fixed 10% READY interval covers this cohort, but is NOT a statistically calibrated future guarantee.

## Whole-family-blocked max-error transfer: the decisive failure

| Whole held-out DAG family | Model | Trained Makespan width | Trained Cost width | Held-out JOINT coverage | Certified true-policy pairs /240 | False certificates | Mean kept /16 | Observed true-HV recovery |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| CyberShake_30 | OLD | 34.872% | 0.0494% | 32/32 | 27 | 0 | 12.00 | 100% |
| CyberShake_30 | READY | 9.304% | 0.0494% | 32/32 | 73 | 0 | 5.50 | 100% |
| Epigenomics_46 | OLD | 17.482% | 0.0494% | **29/32** | 144 | 0 | 2.50 | 100% |
| Epigenomics_46 | READY | 1.043% | 0.0494% | **29/32** | 181 | 0 | 2.00 | 100% |
| Montage_50 | OLD | 34.872% | 0.0116% | **28/32** | 90 | 0 | 10.00 | 100% |
| Montage_50 | READY | 9.304% | 0.0116% | **28/32** | 139 | 0 | 6.50 | 100% |

- Total held-out joint actual coverage = **89/96 for OLD, 89/96 for READY**, across all predeclared family-blocked folds.
- READY family-blocked Pareto certification makes **393/720** strict confident decisions, none false in this small cohort, while abstaining on **327/720**. OLD certifies 261/720, none false but abstains more. Those outcomes do NOT overcome the 7/96 observed joint coverage failures.
- All family-blocked treatments happened to retain actual HV of the original finite 16-point universe; this is not proof they preserve K8 optimizer fronts, that real domination is always correctly recognized, or that any FLA search has improved. Even a wrong model might show 100% HV when all true front points remain among the retained few genotypes.
- The split is a *developer stress test*, not a new truly untouched-family validation: all 3 DAX families were familiar to prior engineering. Two VM profiles of the same DAG are dependent. The 720 pairs per model share 96 observations and do not represent 720 independent statistical trials.

## Correct research decision
1. An error band created by taking maximum observed residual from other two families **does not provide a deterministic transfer guarantee** to a new DAG family. The 7/96 failures are a concrete counterexample. Do not call it a 90%, 95% or 99% calibrated confidence region or say FLA safe certification is validated.
2. Conservatism has a real tradeoff: with READY at fixed 10%, 96/96 points were covered but only 115/720 pairs were certifiable; at 25%, exactly ZERO pairs could be certified and no genotype could be eliminated. This may be unusably conservative for real evolutionary resource allocation.
3. A new algorithm candidate needs an explicitly precommitted calibration method (and enough *independent* DAG-family calibration data), a held-out family/workflow regime, a safeguard for out-of-calibration points that calls READY instead of unsafe pruning, and equal compute-time FLA/NSGA comparisons. A wrapper or static epsilon is not an FLA-specific novelty.
4. **Do NOT wire this uncalibrated interval into the default optimizer.** The Java primitive is usable independently for future research after stronger uncertainty validation; original FLA-v12, seeded NSGA-II and FIFO runtime and all prior negative source results remain unchanged. All code, tests and protocols are confined to `fla-baseline`; `master` remains untouched.

**Disposition: deterministic conditional interval rule PASS; empirical cross-family coverage guarantee FAIL; publishable FLA algorithm evidence still missing.**
