# DAG100 causal simulator-feedback K16: four-mode mechanism ablation and HV reference robustness (2026-11-03)

**Decision:** Preserve `pareto-cover` as the default. The experimentally simpler `online-observed-hv` is a promising optional **post-search simulator replay selector**, and **nearest-neighbor residual correction is NOT supported as a general improvement**. None of these results establishes FLA v12 search superiority or final paper novelty. Only `fla-baseline` is changed; `master` remains unmodified.

## Primary real simulator evidence

- [Full GitHub Actions 41597521884](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41597521884), exact source SHA `2ebaf8e76c128781c2773838edeaf4e535344c53`, **10/10 case jobs and final report PASSED**.
- Aggregate artifact `causal-factorial100-k16-report-41597521884`, ID `13214121051`, contains `online_factorial_report.md`, `online_factorial_hv.csv`, `online_factorial_paired.csv`, source SHA and audit log. All 10 per-case artifacts contain original real WorkflowSim makespan/cost and candidate decision trace CSVs.
- Five DAGs: CyberShake_100, Epigenomics_100, Inspiral_100, Montage_100, Sipht_100. Seeds **95/96**. Three solvers: DAG-Pareto-FLA v7-costseed, v12-hvbandit, cost-seeded NSGA-II. Every solver/policy arm has **3030 real planner objective evaluations, exactly 16 independent WorkflowSim replays**, identical original visited-candidate SHA-256 and identical first four replayed schedules.
- Four policies: (1) planned Pareto/max-min coverage, (2) sequential HV greedy with **only planned objectives** (`online-planned-hv`), (3) sequential greedy with **previously observed true simulator Pareto front** but uncorrected planned objectives of unseen candidates (`online-observed-hv`), (4) (3) plus capped half-shrunk nearest-neighbor makespan residual (`online-nearest-hv`). Simulator labels of unseen candidates are never used.
- [GitHub Actions 41597427016](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41597427016), source `f5d5831885bd2c780d496fed2f93690a6131c661`, verifies the **three online policies' causal isolation** against poisoning future simulation labels. The planned-only policy stays identical even when *all* observed true simulator labels are changed or absent; the observed variants fail closed when earlier simulation observations are missing.
- Per-DAG-family HV reference for evaluation was fixed BEFORE seeds 95/96 from earlier study [Actions 41572425682](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41572425682). No policy uses this evaluation reference during selection.

## Mean real simulated HV difference from Pareto-cover (10 paired DAG-seed cases per algorithm)

| Solver | Planned-greedy only | Observed actual front, no residual | Observed front + local residual |
|---|---:|---:|---:|
| FLA v7-costseed | **+0.0792%** (9/10 wins) | **+0.2715%** (8/10) | +0.0802% (7/10) |
| FLA v12-hvbandit | **+0.0698%** (9/10) | **+0.2827%** (6/10) | +0.0528% (5/10) |
| Costseed NSGA-II | **+0.4669%** (9/10) | **+0.5604%** (10/10) | +0.4718% (8/10) |

The 1NN residual component is not a reliable added improvement. Important negative examples: Inspiral_100 seed95 FLA v7 **−0.7749%** with 1NN, and Epigenomics_100 seed96 NSGA-II **−0.5376%**, although their nonresidual observed-front versions improved **+0.4107%** and **+0.1287%**, respectively. The observed-front version itself loses on CyberShake_100 seeds95/96 FLA v12 and Sipht_100 seeds95/96 FLA v12, so it is not uniformly beneficial.

## Independently recomputed evaluation reference robustness

- [Successful GitHub Actions 41599147990](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41599147990); original 10 per-case simulator artifacts reused, **no new simulated labels or runs**, aggregate artifact `online-reference-robustness-41599147990` ID `13213591699`, source `scripts/fla_online_reference_robustness.py`.
- Multiply BOTH earlier frozen makespan/cost reference components by 1.00, 1.10 or 1.25, report all results under each setting.

| Solver | Observed-front mean gain 1.00× | 1.10× | 1.25× | Online wins unchanged |
|---|---:|---:|---:|---:|
| FLA v7 | +0.2715% | +0.2430% | +0.2078% | 8/10 |
| FLA v12 | +0.2827% | +0.2420% | +0.2024% | 6/10 |
| NSGA-II | +0.5604% | +0.4870% | +0.4042% | 10/10 |

Signs of mean changes remain positive under these three tested reference settings, **not** an assertion of reference-independent performance. Mean effect sizes shrink as the reference grows, and the same cases are reused; no new independent evidence is created by scoring multiple times.

## Cost-accounting implementation and initial pilot

- Java now records `search_ms`, `selection_ms`, `replay_ms`, and `search_selection_replay_ms` independently in trailing CSV columns; instrumented smoke [Actions 41597793461](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41597793461) checked reconciliation and equal candidate histories; see `docs/FLA_ONLINE_K16_RUNTIME_INSTRUMENTATION_2026-11-03.md`.
- This measurement was added **after** the frozen-source 100-task ablation run, so the primary run cannot be presented as having new timing columns. Do not infer matched runtime from matched search/replay call counts.

## Research gate before promotion

1. Keep original default Pareto coverage unchanged. Prioritize further validation of **observed-front greedy without local residual correction**, rather than trying additional per-DAG correction parameters on inspected seeds.
2. Run truly new optimizer seeds with equal 3030 planned evaluations and K16 real WorkflowSim calls, full SHA parity, fixed HV reference, runtime instrumented for BOTH policies and a family-level paired report.
3. Assess failures and Pareto extreme retention, not just average HV. With only five families × two seeds, the observed positive mean is not statistically compelling.
4. The screening innovation is **algorithm-agnostic**, not new FLA generations or exploration physics. A paper centered on FLA search improvement still needs separate equal-budget, independent holdout evidence that FLA outperforms NSGA-II, which is currently missing.
