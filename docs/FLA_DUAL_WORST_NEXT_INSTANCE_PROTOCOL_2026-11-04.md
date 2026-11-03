# Prospective next-instance dual-worst FLA validation — locked before runs, 2026-11-04

**What is being tested:** the previously chosen `worst` dual-model estimator, without any further weight tuning. Its favorable Montage_100 development results and adverse Sipht_60 results are published in `docs/FLA_DUAL_DECODER_FIRST_GATE_ACTUAL_RESULTS_2026-11-04.md`. Here the selection is LOCKED.

## New scenario
- Instances: `Inspiral_50`, `Epigenomics_24` (neither instance was used in dual-model development). Their DAG FAMILIES existed in earlier broader platform auditing, so these are *new-instance tests*, not fully independent family holdout.
- Seeds: **501** and **502**, neither seen in the dual-model four-block search gate; default speed profile.
- Treatments: `old` (original stage-in-aware insertion objective) and `worst` (componentwise max over original and ready-queue model); no `mean` or `ready` arm to cherry-pick.
- Per treatment invoke two solvers: DAG-Pareto-FLA v12-hvbandit and identically cost-seeded NSGA-II, initial two cost seeds identical. Population 30, generations 100: **3030 objective genotype evaluations per solver**. K16 fixed planned Pareto-cover real simulator replay selections per solver, no simulator labels in search.
- 2 DAX × 2 seeds × 2 treatments = **8 independent benchmark invocations**, 16 optimizer arms, **256 prospective real WorkflowSim replay calls** if all succeed.
- Freeze same high-level VM pool and speed. The alternative doubles internal deterministic evaluator calls; record search wall-clock and note unequal computational expense.
- Independent final HV analysis from original per-arm `_replays.csv` must use *one* 1.5× and one 3× true-simulation reference per DAG/seed block over both solver/treatment sets; no direct comparison of run-local HV.
- Output all four DAG/seed paired old-versus-worst true HV, runtime ratio, negatives, exact code SHA, complete K16 mappings and actual objectives; no retroactive selection. Parent/child assignments are not required to match across treatments because search is different; cost seeds and evaluation counts must match across solvers.
- **Success criterion for a promising follow-up** is gains in most paired blocks, across both DAGs, with acceptable slowdown and no catastrophic regression. Even success here is too little for a publication claim and cannot be called an unseen-family test.
- Failure criterion: mixed, neutral, or negative true HV in the predeclared blocks. Preserve negative outcomes and keep variant opt-in. Do NOT change `master` or default settings, regardless of result.
