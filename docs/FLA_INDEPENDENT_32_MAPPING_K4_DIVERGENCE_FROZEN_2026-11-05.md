# Precommitted fixed 32-mapping OLD vs READY K4 decision-divergence gate (2026-11-05)

**This prospective gate is frozen before running its first new original WorkflowSim truth label. It tests prediction-driven selection, NOT a new FLA optimization operator. No instance-size data is a genuinely unseen DAG family.**

## Why expand the original independent placement pool
- Previous original fixed 16-genotype [42002749849](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42002749849), strict decision audit [42003163567](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42003163567) showed OLD and READY select EXACTLY the same K4 physical mapping set in all 8 blocks (Epigenomics_24/default differed in order only). Consequently both earned exactly identical real HV regardless of READY's 0 versus OLD's 5 wrong strict dominance claims.
- Candidate-universe saturation, not necessarily intrinsic model equivalence, is the active hypothesis. To test it, freeze additional mapping policies *independently of OLD/READY and simulator outcomes* before running any true label. Both models must predict on the **same exact 32 physical TaskID→VMID** genotypes, with full true WorkflowSim/FIFO labels for all 32.

## Original source and prospective cases
- New self-contained Java `FLAFixedMappingUniverse32.java` is a safe variant of existing `FLAAlgorithmIndependentMappingUniverse.java`, retaining the original first 16 deterministic mappings exactly; it uses the identical original WorkflowSim LIWSA fixed-VM replay with OLD StageInAware and READY TASK_ID planner readouts, and unchanged FIFO runtime. Source flags: `-Dworkflowsim.planningStageInAware=true -Ddagfla.readyQueueDiagnostic=true -Ddagfla.fixedTaskTrace=true -Ddagfla.fixedVmReadyPriority=fifo`; VM profiles `default` and `staggered`. Original simulator seed **1501**. No FLA/NSGA optimizer involved, no true label used in mapping creation.
- Frozen next sixteen policy names (TaskID integer 1..N, t=ID−1, VMIDs 0..15; mixedHash is the original public deterministic hash): 
  17. `cyclic_step3`: `(3*t+2)%16`
  18. `cyclic_step9`: `(9*t+5)%16`
  19. `two_vm_alt_3_11`: `(t%2==0?3:11)`
  20. `two_vm_block3_3_11`: `((t/3)%2==0?3:11)`
  21. `four_vm_shift_round`: `{2,6,10,14}[t%4]`
  22. `four_vm_shift_block`: `{2,6,10,14}[(t/3)%4]`
  23. `eight_vm_odd_round`: `(2*t+1)%16`
  24. `eight_vm_odd_block`: `(2*(t/3)+1)%16`
  25. `vm0_vm12_skew90`: `(t%10==0?12:0)`
  26. `vm12_vm15_skew90`: `(t%10==0?15:12)`
  27. `reverse_round_robin`: `15-t%16`
  28. `reverse_stride7`: `15-(7*t+3)%16`
  29. `hash_seed211`: original `mixedHash(TaskID,211)`
  30. `hash_seed307`: original `mixedHash(TaskID,307)`
  31. `monotonic_vm8`: `2*min(7,8*t/N)`
  32. `reverse_monotonic_vm8`: `15-2*min(7,8*t/N)`
- All 32 policies must produce unique, valid length-N TaskID→VMID strings; **fail closed**, never silently remove duplicate genotypes.
- Four new DAX instance-size tests `Inspiral_30`, `Sipht_30`, `Epigenomics_100`, `CyberShake_50`, both VM speed profiles default/staggered. **4×2×32=256 new WorkflowSim true replay records**, eight DAG/VM case blocks. Families are familiar, so not a blind family holdout or a 20-seed paper trial. Preserve source SHA and per-task actual trace identities.

## Predeclared decision and error analysis
- OLD and READY separately choose K4 greedily by marginal `HV` over their own 32 *predicted* (makespan,cost) values with `1.5*maximum+1e-6` per-axis predicted reference. Exact ties: lowest predicted normalized scalar sum (each objective divided by its predicted max), then lexicographic mapping-policy string. Neither sees simulator truth.
- Controls: `blind_first_four` original policy-list positions 1–4, original first-16-only K4 choice (same 32-run real labels but restriction to old subuniverse), 32 deterministic random K4 subsets (same candidate pool, hashed seed independent of true labels), and the **infeasible C(32,4)=35,960 true-label hindsight oracle** for a 32-candidate restricted ceiling. Oracle never enters predictor selection.
- Realized **2D actual HV** uses one common true reference per (DAX,VM profile) across all 32 physical truth points; `1.5*true-max +1e-6` and sensitivity factor 3.0. Report true decision regret to exact restricted K4 oracle, OLD vs READY realized K4, matched chosen map set identical/nonidentical, true gain relative to fixed blind and first-16 model control, individual and block mean. Report dominated-class lost/new/reversed, makespan/cost sign disagreements, material true >0.1% dominance errors and nondominated-index-set Jaccard.
- **Primary mechanism gate:** at least one OLD-vs-READY K4 physical chosen-map set difference among eight cases. If all sets still match, stop treating READY as a superior selection policy even if absolute error improves. If any differ, evaluate actual K4 HV quality before claiming prediction model benefit, preserving negative signs.
- Predeclared stop: if READY fails to obtain a reproducible positive actual decision HV effect vs OLD in this small cohort, do NOT tune 32 policy definitions or selection heuristics on its labels. Even if positive, this is still familiar-family pilot work needing independent new-family/VM regime and 20+ blocked seeds, CPU overhead audit and external literature review for publication.

All new files and opt-in flags stay in `fla-baseline`, original `FLAAlgorithmIndependentMappingUniverse.java`, original FLA/NSGA optimizers and `master` remain untouched.
