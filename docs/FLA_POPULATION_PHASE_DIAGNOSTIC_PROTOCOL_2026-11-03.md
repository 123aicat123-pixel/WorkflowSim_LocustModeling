# Read-only FLA phase and selected-breeding-population measurement, 2026-11-03

This is INSTRUMENTATION ONLY. Every existing FLA search variant and experimental/default operator remain unchanged. The new `-Ddagfla.populationDiagnostics=true` flag captures exactly one detached row AFTER each actual survivor selection plus a generation-0 row. It performs zero objective or simulator evaluations, zero RNG calls, and no selection/offspring mutations.

For each generated population: actual selected genotype unique count, duplicate selected slots, unique counts in both FLA groups, number of genotype overlaps across groups, exact normalized pairwise Hamming, number of distinct genotypes in the **child survivor-input pool**, new planned Pareto archive insertion events, newly rejected v15 local trial slots, FLA phase (0 diffusion DO, 1 equilibrium EO, 2 steady SSO), per-phase three-arm bandit normal-child uses (local paired trials are NOT bandit assignments), archive size and planned extreme makespan/cost, cumulative objective evaluation count. Parent group sizes remain identical.

The archive insertion counter measures actual admissions, not necessarily archive size growth or HV gain; removed/dominated archive members can reduce size. Selected-population unique count directly diagnoses v15 gate duplication whereas prior `distinct_observed` measured ALL evaluated genotypes, including rejected trial candidates.

Two-stage validation before any conclusion:
1. Unit tests on exact manually countable repeated genotypes; assert no mutation of input and size/matching.
2. A paired same-seed same-variant probe with the flag OFF and ON must have identical SHA-256 fingerprint of ALL uniquely evaluated planned assignments, exactly equal 3030 fitness calls, identical K16 selected task-VM fingerprints and **actual** simulator scores. Any mismatch rejects the diagnostic implementation.
3. Only after this identity gate passes, run a multi-arm mechanism-only development study. Compare each generation's selected-population unique slots under v12, v14 and v15, by DO/EO/SSO. Avoid claims of independent algorithm superiority or causal stage influence from a descriptive phase alignment.

This instrumentation does NOT change any FLA math or make the original FLA equations faithful. The original v12/v13/v14/v15 outcome reports remain as observed. Fresh development seeds and WorkflowSim outcomes are for diagnosis, not unseen independent publication holdout.
