#!/usr/bin/env python3
"""Read-only v15 comparison: evaluated distinct genotypes, archive size and runtime."""
import csv,pathlib,statistics,sys,math
DAGS=("CyberShake_30","Montage_25")
SPEEDS=("default","staggered")
SEEDS=(161,162)
NAMES=("DAG-Pareto-FLA[v12-hvbandit]","DAG-Pareto-FLA[v14-randompair]",
       "DAG-Pareto-FLA[v14-timelinepair]","DAG-Pareto-FLA[v15-randomgate]",
       "DAG-Pareto-FLA[v15-timelinegate]","NSGA-II[costseed]")
def read(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))
def run(root,out):
    cases=[]
    for wf in DAGS:
        for speed in SPEEDS:
            for seed in SEEDS:
                pref=f"v15-search-{speed}-{wf}-s{seed}"
                found=list(root.rglob(pref+"_summary.csv"))
                assert len(found)==1,(pref,found)
                rows=read(found[0])
                assert len(rows)==6 and {x["algorithm"] for x in rows}==set(NAMES)
                seq=[next(x for x in rows if x["algorithm"]==name) for name in NAMES]
                for x in seq:
                    assert int(x["evaluations"])==int(x["captured_evaluations"])==3030
                    assert int(x["replayed"])==16
                    assert 0<int(x["distinct_observed"])<=3030
                    assert 0<int(x["sim_nondominated"])<=16
                x=[int(z["distinct_observed"]) for z in seq]
                nd=[int(z["sim_nondominated"]) for z in seq]
                archive=[int(z["source_archive"]) for z in seq]
                runtime=[float(z["search_ms"]) for z in seq]
                assert all(math.isfinite(z) and z>=0 for z in runtime)
                cases.append(dict(workflow=wf,vm_speed=speed,seed=seed,
                    visited_v12=x[0],visited_v14_random=x[1],visited_v14_timeline=x[2],
                    visited_v15_random=x[3],visited_v15_timeline=x[4],visited_nsga=x[5],
                    gate_random_visited_delta=x[3]-x[1],gate_timeline_visited_delta=x[4]-x[2],
                    gate_random_unique_pct=100*(x[3]/x[1]-1),
                    gate_timeline_unique_pct=100*(x[4]/x[2]-1),
                    sim_nd_v12=nd[0],sim_nd_v14_random=nd[1],sim_nd_v14_timeline=nd[2],
                    sim_nd_v15_random=nd[3],sim_nd_v15_timeline=nd[4],sim_nd_nsga=nd[5],
                    archive_v12=archive[0],archive_v14_timeline=archive[2],archive_v15_timeline=archive[4],
                    search_ms_v14_timeline=runtime[2],search_ms_v15_timeline=runtime[4]))
    assert len(cases)==8
    out.mkdir(parents=True,exist_ok=True)
    with (out/"v15_diversity_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
    lines=["# Read-only v15 Pareto-gate diversity and archive diagnostic","",
        "Reprocessed original 8 actual six-arm job summary CSVs from run 41618003870; no new search fitness/simulator calls. This measures DISTINCT FITNESS-EVALUATED GENOTYPES, not the unrecorded survivor population genotype diversity. No causal effect of the gate can be inferred from this count alone.",
        "","| DAG | VM | Mean change distinct visited gated-vs-ungated timeline | Mean change distinct visited gated-vs-ungated random | Mean simulator ND front size v14 timeline | Mean simulator ND front size v15 timeline |",
        "|---|---|---:|---:|---:|---:|"]
    for wf in DAGS:
        for speed in SPEEDS:
            z=[x for x in cases if x["workflow"]==wf and x["vm_speed"]==speed]
            lines.append(f"| {wf} | {speed} | {statistics.mean(x['gate_timeline_visited_delta'] for x in z):+.1f} | {statistics.mean(x['gate_random_visited_delta'] for x in z):+.1f} | {statistics.mean(x['sim_nd_v14_timeline'] for x in z):.2f} | {statistics.mean(x['sim_nd_v15_timeline'] for x in z):.2f} |")
    lines+=["","## Pooled descriptive",
       f"Timeline gated relative distinct evaluated genotypes: {statistics.mean(x['gate_timeline_unique_pct'] for x in cases):+.6f}% across 8 cases.",
       f"Random gated relative distinct evaluated genotypes: {statistics.mean(x['gate_random_unique_pct'] for x in cases):+.6f}% across 8 cases.",
       f"v15 timeline mean unique observed /3030 = {statistics.mean(x['visited_v15_timeline'] for x in cases)/3030*100:.6f}%.",
       "","## Raw per-case entries", "",
       "| DAG | VM | Seed | Ungated timeline unique | Gated timeline unique | Ungated random unique | Gated random unique | v12 unique |",
       "|---|---|---:|---:|---:|---:|---:|---:|"]
    for x in cases:
        lines.append(f"| {x['workflow']} | {x['vm_speed']} | {x['seed']} | {x['visited_v14_timeline']} | {x['visited_v15_timeline']} | {x['visited_v14_random']} | {x['visited_v15_random']} | {x['visited_v12']} |")
    lines+=["","## Interpretation limitations",
       "The gate replaces dominated neighbors in the next-generation candidate slots with an existing normal offspring, but all evaluated neighbors still enter candidate recording (and possible archive admission). Distinct evaluated genotype counts therefore cannot directly measure diversity inside the selected breeding population. Any observed variation mixes stochastic trajectory effects with selection replacement.",
       "The simulated nondominated count is only for K16 replayed candidates, not the exhaustive true Pareto frontier. GitHub Actions wall time/JIT effects cannot establish performance improvement. These familiar-workflow results are already-exposed development data; do not reuse as independent held-out validation."]
    (out/"v15_diversity_report.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_v15_diversity_audit.py ORIGINAL_ARTIFACTS OUT")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
