# Prospective dual-worst next-instance FLA and NSGA-II test: negative generalization result (2026-11-04)

**Decision: dual-worst is NOT a validated general FLA improvement; remain opt-in and do not promote.** Both required new-instance DAG/seed cases were run, true HV independently recomputed, and adverse outcomes preserved.

## Preregistered scope and exact source
- Frozen before runs: `docs/FLA_DUAL_WORST_NEXT_INSTANCE_PROTOCOL_2026-11-04.md`. Candidate dual worst was selected based on earlier Montage/Sipht exploratory results; **no adaptation during the new-instance gate**.
- [New original optimizer and actual simulator Actions 41673209577](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41673209577): 8/8 PASS, two new DAX instances `Inspiral_50`, `Epigenomics_24`, new optimizer seeds 501 and 502, old and worst objectives, each invocation paired original FLA-v12 and identically cost-seeded NSGA-II. Each optimizer arm enforced exactly **3030 unique counted genotype-objective calls** (same source evaluation counter and recorder, duplicates count as separate calls, not necessarily 3030 unique mappings) and 16 actual WorkflowSim replay calls, 256 true K16 replay calls in this new test.
- [Independent read-only, common-HV-reference audit 41673393959](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41673393959) PASS. Within each DAX/seed, both solvers and both decoders share a single normalizing reference based on four complete original K16 real Pareto sets, evaluated at 1.5× and 3× source maxima. Does NOT compare independently calculated run-local HV across policies.
- No changes to original solver default or `master`; `dagfla.dualModelMode` remains OFF by default.

## Actual WorkflowSim normalized HV under 1.5× shared reference

| DAG | Seed | Solver | Old baseline HV | Dual-worst HV | Δ HV (worst−old) | Search-time ratio |
|---|---:|---|---:|---:|---:|---:|
| Inspiral_50 | 501 | FLA-v12 | 0.31521935 | 0.31279801 | **−0.00242133** | 1.15× |
| Inspiral_50 | 502 | FLA-v12 | 0.31436800 | 0.31314882 | **−0.00121919** | 1.27× |
| Epigenomics_24 | 501 | FLA-v12 | 0.27642127 | 0.27642516 | **+0.00000389** | 1.52× |
| Epigenomics_24 | 502 | FLA-v12 | 0.27600359 | 0.27606829 | **+0.00006470** | 1.21× |
| Inspiral_50 | 501 | seeded NSGA-II | 0.32218232 | 0.32350326 | **+0.00132094** | 1.25× |
| Inspiral_50 | 502 | seeded NSGA-II | 0.30110641 | 0.30989927 | **+0.00879285** | 1.74× |
| Epigenomics_24 | 501 | seeded NSGA-II | 0.27105149 | 0.27602154 | **+0.00497005** | 1.99× |
| Epigenomics_24 | 502 | seeded NSGA-II | 0.27612471 | 0.27098348 | **−0.00514123** | 3.30× |

- FLA paired mean Δ normalized actual true HV = **−0.00089298**, **2 wins / 2 losses** (the two Epigenomics positive differences are extremely small), mean search-time ratio **1.29×**.
- Seeded NSGA-II mean Δ normalized true HV = **+0.00248565**, **3 wins / 1 loss**, mean search-time ratio **2.07×** (highly uneven).
- All signs for FLA are preserved under alternative 3.0× reference in the original audit.

## Formal research conclusion
1. The previous exploratory first-gate worst-case FLA mean gain **+0.00349619** (Montage benefit) did NOT generalize to these two new-instance examples: FLA overall now slightly negative on average and specifically worse on BOTH Inspiral seeds.
2. This result is consistent with a structural difference between DAGs; it does NOT by itself establish which structural features explain it. Never infer a learned mapping-feature selector from four blocks and validate it on the same four blocks.
3. Even improvements to fixed-genotype Makespan prediction and task timing do not guarantee better search ranking or actual Pareto-HV performance.
4. Every model change added internal deterministic evaluation compute and usually increased wall-time; future comparisons must include matched time budgets, not only matching counts of fitness calls.
5. A shared decoder is NOT FLA search-operator innovation. Avoid any claim that this is publication-ready; no evidence of stable cross-DAG FLA optimization improvement or Q1 publication advantage yet.
6. Next method should focus on an independently specified **FLA-specific exploratory operator or Pareto-diversity mechanism** with a strict equal-cost-seeded NSGA-II/FLA baseline, or develop an explicitly bounded **offline** model-disagreement-aware candidate reranker that does not alter search and tests both algorithms equally. Both require new prospective protocols and unseen/screened DAG cases before publication.

**Preserve the negative result as a falsification success; do not install `dual-worst` by default.**
