# Causal online K16 simulator feedback: AB/BA runtime control and two-cohort replication (2026-11-03)

**Research verdict:** independently simulated observed-front feedback yields a **modest descriptive HV gain** on the evaluated DAG100 configurations, including FLA v12; **no reliable runtime speedup** or FLA-search-specific superiority has been established. Preserve `pareto-cover` as the default. The opt-in method is `online-observed-hv`; `master` remains untouched.

## Part A — Actual JVM invocation-order runtime control

- [Successful GitHub Actions run 41602010023](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41602010023), exact source SHA `fe2b89269f15e7a6fd5605aab86a4667111f989c`.
- Artifact `abba-summary-41602010023`, ID `13215026324`, original CSVs `abba_paired.csv`, `abba_runtime_rows.csv`, full report `abba_runtime_report.md`; six original per-DAG/seed Java artifacts include source SHA, replay identities, simulator objectives and instrumented timing.
- Three small previously studied DAGs Montage_25, CyberShake_30, Inspiral_50; optimizer seeds 108/109, three cost-seeded algorithm arms. Every arm/method JVM process executed **3030 true planned objective evaluations and K16 independently simulated WorkflowSim replays**.
- AB invokes `pareto-cover` first then `online-observed-hv`; BA reverses the independent Java process order. **All 6 paired jobs and the final report passed**. Per DAG/seed/algorithm, the four runs have the same complete ordered planner genotype/fitness SHA; within each policy, AB and BA selected identical replay genotypes and produced identical real simulator objective values to numerical tolerance. Therefore, AB-vs-BA timing variations cannot be attributed to changing the selected objective outcomes.

| Algorithm | Median additional selection time AB | Median additional selection time BA | Median combined online total-time difference AB | BA |
|---|---:|---:|---:|---:|
| FLA v7 | +19.701 ms | +19.299 ms | +7.545% | +9.024% |
| FLA v12 | −3.533 ms | +15.797 ms | −7.815% | −0.060% |
| NSGA-II | +3.435 ms | +6.538 ms | +14.082% | +21.431% |

The `−3.533ms` small-sample selection timing anomaly for v12 when A precedes B is precisely why single-process order measurements should not be overinterpreted as a computational improvement. Total time counts planner search + replay selection + actual simulator replay time (instrumented), **not** Java compilation or GitHub scheduling. JVM warmup, runner load, GC and lack of repeated independent hardware samples limit precision.

## Part B — Two independently executed 100-task cohorts, reference-frozen

- [Original complete real four-policy DAG100 Actions 41597521884](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41597521884), source `2ebaf8e76c128781c2773838edeaf4e535344c53`; artifact `causal-factorial100-k16-report-41597521884`, ID `13214121051`. Take only `online-observed-hv` versus `pareto-cover` from four-arm ablation.
- [Original independent instrumented DAG100 Actions 41600766954](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41600766954), source `4a9e535644b8613a073bb9b69b9739c3e50cc2c1`; aggregate artifact `online-runtime100-k16-report-41600766954`, ID `13215350172`.
- A **separate complete reanalysis using only the original two pinned aggregate artifacts** was executed in [GitHub Actions 41602401801](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41602401801); source `493073ccb337f1f813b6e8615a048c21d6ef3d25`, artifact `online-two-cohorts-41602401801` ID `13215491138`, includes `online_two_cohorts_report.md`, all 60 per-algorithm paired cases, solver/family/leave-one-family-out CSVs.
- The two cohorts share the **same external-in-study HV reference frozen from earlier run 41572425682**, equal 3030 planned objective calls + K16 independently executed WorkflowSim replays per method/solver and exact within-source search histories across policies. They have **different code commit SHA** (runtime instrumentation added between them) and are not guaranteed byte-for-byte identical policy implementations.
- Five DAG100 families, four optimizer seeds 95/96/101/102, three correlated solver arms. **20 DAG/seed blocks, 60 algorithm-arm contrasts; only five DAG families**. This is not 60 independent workflow instances.

| Solver | Descriptive 20-case mean online simulator-HV gain vs cover | Median | Positive cases | Worst loss |
|---|---:|---:|---:|---:|
| FLA v7 | +0.1571% | +0.0011% | 13/20 | −0.1921% |
| **FLA v12** | **+0.3481%** | +0.0686% | **15/20** | −0.2004% |
| Costseed NSGA-II | +0.3632% | +0.1033% | 17/20 | −0.1207% |

FLA v12 per-DAG means: CyberShake_100 **−0.0124%** (2/4 wins), Epigenomics_100 **+0.4302%** (4/4), Inspiral_100 **+0.7846%** (4/4), Montage_100 **+0.0743%** (4/4), Sipht_100 **+0.4640%** (1/4); the Sipht mean is influenced by one unusually large positive case.

Leave-one-entire-DAG-family-out descriptive remaining mean gains for FLA v12 are **+0.2390% to +0.4383%**, which is reassuring against one-family mean domination but is **not** a confidence interval, independent external validation, or proof of robust benefit under different VM/communication regimes.

## Consequences for publication framing

1. **Do not present this as a superior FLA search operator.** The selected candidate *history* is already produced by the full planner-based optimizer before real simulator feedback is used; the selection improvement belongs to post-search replay screening. NSGA-II also benefits.
2. The simpler observed-front feedback mechanism is a more defensible candidate than the unreliable 1NN residual correction, but negative cases are real and MUST be retained.
3. The runtime evidence is noisy and order-sensitive. A reliable time-efficiency claim needs independent repeated runner/hardware conditions, randomized process ordering and distributional uncertainty; equal simulator call counts are not enough.
4. The five DAG families have already been seen in development and no heldout cross-VM heterogeneity evaluation is yet documented. Maintain `pareto-cover` as safe default until those external gates are completed.
5. These results are exploratory. Do not compute naive p-values treating 60 correlated algorithm-arm comparisons as 60 independent workflow draws.
