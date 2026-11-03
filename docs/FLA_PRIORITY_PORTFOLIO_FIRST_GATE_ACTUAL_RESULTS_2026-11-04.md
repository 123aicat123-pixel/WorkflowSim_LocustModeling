# First equal-3030 priority portfolio FLA/NSGA-II true-HV research gate — actual results (2026-11-04)

**Decision: this fixed 6/5/5 three-policy portfolio is NOT a validated improvement to original FLA. Preserve code as opt-in and experimental data, DO NOT replace the original default. A small within-portfolio FLA-over-NSGA observation merits independent investigation but is not an established cross-DAG algorithm superiority or novel joint encoding.**

## Exact original evidence
- Preregistered before outcome in `docs/FLA_PRIORITY_PORTFOLIO_FIRST_GATE_PROTOCOL_2026-11-04.md`.
- Original full optimization and **384 true WorkflowSim replay calls**: [GitHub Actions 41683032206](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41683032206), **20/20 source jobs PASS**. All source artifacts archived including original Pareto-cover-selected genotype maps, policy, actual and planned Makespan/Cost, SHA, runtime, unit and CI logs. 2 DAX instances `CyberShake_30`, `Sipht_30`; seeds 711,712, original VM speed/prices.
- Independent read-only common-reference actual-HV analysis: [Actions 41683457146](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41683457146), **PASS**. Its `scripts/fla_priority_portfolio_first_gate_hv_audit.py` failed closed on missing source blocks, checked all source labels, original population/generations, exactly 3030 counted and captured genotype evaluations and exactly **K16 real simulator replays per solver/treatment** with positive finite real objectives, no repeated placement genotype within the same policy island, and one common normalized reference per DAX/seed from all six solver/treatment K16 clouds.
- Three treatments for BOTH FLA-v12 and exactly low-cost-seeded NSGA-II:
  - Original `old`: stage-in-aware insertion objective, FIFO runtime, pop=30, gens=100, K=16 planned Pareto cover.
  - `ready`: original TaskID ready-queue objective, FIFO runtime, pop=30, gens=100, K=16.
  - `priority-portfolio`: independently optimize fixed runtime `fifo` (pop10, gens100,K6), `shortest` (pop10,gens100,K5), `upward` (pop10,gens100,K5). Each island uses an opt-in policy-aware decoder AND exactly the same runtime simulator policy. Per solver: **3×1010=3030** genotype objective calls and **6+5+5=16** actually simulated distinct *placement+priority* compound candidates. All FLA/NSGA algorithm mechanism settings remain unchanged within each original solver. Crucially this is a portfolio of separate optimizers, **NOT per-individual joint priority genome co-evolution**.
- Across four (DAG, seed) blocks and six solver/treatment groups per block = **24 assembled K16 actual sets**, 72,720 counted genotype objective calls, 384 actual WorkflowSim simulator replays.

## True WorkflowSim normalized K16 Pareto HV (single six-arm reference per block, 1.5× actual maxima)

| DAG | Seed | FLA-original old | FLA FIFO-ready | FLA three-priority portfolio | Δ FLA portfolio − old | Seeded NSGA-II original | Seeded NSGA-II portfolio |
|---|---:|---:|---:|---:|---:|---:|---:|
| CyberShake_30 | 711 | 0.49910878 | 0.50843535 | 0.50903894 | **+0.00993016** | 0.51197004 | 0.50802178 |
| CyberShake_30 | 712 | 0.51358445 | 0.50530895 | 0.51130017 | **−0.00228428** | 0.51324157 | 0.50805188 |
| Sipht_30 | 711 | 0.15701159 | 0.15701159 | 0.15701158 | −0.00000001 | 0.15701158 | 0.15693234 |
| Sipht_30 | 712 | 0.15666686 | 0.15666686 | 0.15666685 | around −0.00000000 | 0.15666685 | 0.15666685 |

**FLA portfolio vs FLA old**: mean normalized Δ K16 actual true HV **+0.00191147** across four tiny blocks, nominal wins/ties/losses **1/0/3** (two losses in Sipht are practically zero, not consequential). The mean increase is dominated by a single CyberShake_30 seed; clearly NOT a stable positive effect. Mean measured search-time ratio portfolio/old = **1.46×**. Under a secondary 3× reference the paired effect signs did not flip in the original analyzer.

**Seeded NSGA-II portfolio vs its own old**: mean actual normalized Δ **−0.00230430**, 0/0/4 nominal, with many very small differences. Mean measured search-time ratio portfolio/old **0.89×** (reflecting different optimizer overheads, NOT equal compute cost).

**FLA versus seeded NSGA-II within identical portfolios**: FLA actual normalized HV is larger in **all 4/4** paired blocks, mean margin **+0.00108618**. By contrast, the FLA old-vs-NSGA old mean margin was **−0.00312959** despite 3/4 nominal FLA wins (unequal effect sizes). This isolated interesting four-block observation is **not** a significant, robust or general FLA superiority claim; the portfolio still fails to improve FLA over its own original control consistently.

## Novelty and fairness limits
1. Equal **genotype evaluator counts** do not mean equal internal schedule-model calculations or equal wall-clock cost. Original old stage-in insertion search does less per genotype than priority portfolio, and the candidate uses three separately initialized subpopulations (pop10) instead of one pop30. Cannot isolate the causal effect of priority selection from population splitting/restarts based on this study alone.
2. The policy K quota `fifo=6,shortest=5,upward=5` was fixed in the preregistration, not adapted to the real CloudSim labels. This sacrifices replay coverage of potentially good FIFO configurations and can explain some observed harm.
3. True HV is the union of just K16 planned-cover selected simulator replays, not the entire unknown actual attainable Pareto set. The sensitivity reference is shared across all six groups WITHIN each workflow/seed; results across DAG blocks are not a single pooled normalized global reference.
4. Only two historically familiar DAX families, two seeds and default VM speed; insufficient for inferential claims or SCI Q1. Earlier already-known 2024 joint task priority / VM-rule coevolution published in Computers & Operations Research, DOI 10.1016/j.cor.2024.106805: jointly optimizing scheduling rules itself is not established new literature novelty.
5. The original ready-priority model does capture large fixed-mapping runtime differences under UPWARD in separate simulated cases (`docs/FLA_PRIORITY_AWARE_CROSS_INSTANCE_ACTUAL_RESULTS_2026-11-04.md`), but model fidelity **does not guarantee** the Pareto-cover selection/search achieves higher real K16 HV. Prior CyberShake SJF sign-error case remains a negative counterexample.

## Research decision and next valid experiment
- **Reject automatic promotion** of this fixed-split portfolio; retain `fla-baseline` diagnostic flags and source for reproducibility. `master`, FIFO runtime default, and original FLA/NSGA objectives remain untouched.
- The next worthwhile study must remove the population-size/restart confound, **without** policy tuning on these four blocks: compare full-budget single-priority policies (FIFO/UPWARD/SHORTEST, each pop30/gens100) and independent matched control for restart allocation, all under fixed K16 source replay budgets. Prefer new DAG instances/independent seeds and at least one VM regime not seen in the present gate.
- A credible publishable *FLA-specific* innovation requires a clear adaptive task-priority genotype/operator or risk-aware mechanism beyond known ready-queue and HEFT/SJF, linked to critical path **and actual Pareto** decisions, a fair common encoding with NSGA-II, equal compute-time and evaluation budgets, independent unseen-DAG family holdout and ablation against published scheduling-rule learners. This engineering demonstration is not sufficient yet.

**Final verdict for this gate: priority control & prediction are empirically real; the current priority-island combination is NOT a stable true-Pareto optimizer improvement.**
