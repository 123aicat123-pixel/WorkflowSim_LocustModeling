#!/usr/bin/env python3
"""Read-only, verification-grade followup to the frozen 8-block phase population experiment."""
import csv,pathlib,statistics,collections,sys,math
DAGS=("Montage_25","CyberShake_30")
SPEED=("default","staggered")
SEEDS=(173,174)
ALGS=("DAG-Pareto-FLA[v12-hvbandit]",
      "DAG-Pareto-FLA[v14-randompair]",
      "DAG-Pareto-FLA[v14-timelinepair]",
      "DAG-Pareto-FLA[v15-randomgate]",
      "DAG-Pareto-FLA[v15-timelinegate]")
PHASE={0:"DO",1:"EO",2:"SSO"}
def read(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))
def get(row,k):return float(row[k])
def main(root,out):
    rows=[];sourceShas=set()
    for dag in DAGS:
        for speed in SPEED:
            for seed in SEEDS:
                pref=f"phase-pop-{speed}-{dag}-s{seed}"
                files=list(root.rglob(pref+"_population_diagnostics.csv"))
                assert len(files)==1,(pref,files)
                batch=read(files[0]);assert len(batch)==505
                src=(files[0].parent.parent/"ci-logs/source_sha.txt")
                assert src.exists(),src
                sha=src.read_text().strip()
                assert len(sha)==40
                sourceShas.add(sha)
                for x in batch:
                    assert x["algorithm"] in ALGS
                    gen=int(get(x,"generation"))
                    assert gen in range(101)
                    phase=int(get(x,"phase"))
                    assert phase==-1 if gen==0 else phase in PHASE
                    uniques=int(get(x,"selected_unique"))
                    dupe=int(get(x,"selected_duplicate_slots"))
                    assert 1<=uniques<=30 and dupe==30-uniques
                    assert 0<=get(x,"pairwise_hamming_all")<=1
                    rows.append(dict(workflow=dag,speed=speed,seed=seed,
                        algorithm=x["algorithm"],generation=gen,phase=phase,
                        selected_unique=uniques,selected_duplicate_slots=dupe,
                        hamming=get(x,"pairwise_hamming_all"),
                        cross_group_overlap=int(get(x,"cross_group_overlap")),
                        child_pool_unique=int(get(x,"generated_unique")),
                        gate_rejected=int(get(x,"local_gate_rejections")),
                        archive_insertions=int(get(x,"archive_insert_events")),
                        archive_size=int(get(x,"archive_size"))))
    assert len(rows)==8*5*101
    assert len(sourceShas)==1,("Source drift",sourceShas)
    out.mkdir(parents=True,exist_ok=True)
    stats=[]
    for alg in ALGS:
        for phase,name in PHASE.items():
            rr=[x for x in rows if x["algorithm"]==alg and x["phase"]==phase]
            assert rr
            stats.append(dict(algorithm=alg,phase=name,observations=len(rr),
              min_selected_unique=min(x["selected_unique"] for x in rr),
              max_selected_unique=max(x["selected_unique"] for x in rr),
              mean_selected_unique=statistics.mean(x["selected_unique"] for x in rr),
              count_duplicate_generations=sum(x["selected_duplicate_slots"]>0 for x in rr),
              mean_hamming=statistics.mean(x["hamming"] for x in rr),
              mean_cross_group_overlap=statistics.mean(x["cross_group_overlap"] for x in rr),
              mean_child_pool_unique=statistics.mean(x["child_pool_unique"] for x in rr),
              total_local_gate_rejected=sum(x["gate_rejected"] for x in rr),
              total_archive_insertions=sum(x["archive_insertions"] for x in rr),
              mean_archive_size=statistics.mean(x["archive_size"] for x in rr)))
    with (out/"phase_population_exact_stats.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(stats[0]));w.writeheader();w.writerows(stats)
    lines=["# Source-pinned selected-breeding-population phase follow-up",
       "",f"Original source SHA: `{next(iter(sourceShas))}`; raw artifacts from Actions 41621527587. Read-only; no optimizer or simulator calls.",
       "All metrics come from selected post-survivor breeding groups, not cumulative evaluated distinct candidate counts.",
       "",
       "| Algorithm | Phase | Min/max unique of 30 selected | Generations with duplicates | Mean genotype Hamming | Mean new archive admissions/generation | Total local trials rejected |",
       "|---|---|---|---:|---:|---:|---:|"]
    for x in stats:
        lines.append(f"| {x['algorithm']} | {x['phase']} | {x['min_selected_unique']}/{x['max_selected_unique']} | {x['count_duplicate_generations']}/{x['observations']} | {x['mean_hamming']:.6f} | {x['total_archive_insertions']/x['observations']:.4f} | {x['total_local_gate_rejected']} |")
    notall=[x for x in rows if x["selected_unique"]!=30]
    lines+=["",f"## Exact population uniqueness: {len(notall)} selected-population generation records with fewer than 30 distinct genotypes, out of {len(rows)} total including generation zero.",
     "If all generations have 30 distinct selected genotypes, the hypothesis that v15 selection failure arises from duplicated selected breeding slots is unsupported in this experiment; duplicate local candidate slots can be filtered by the existing global unique-first survivor-selection rule.",
     "",
     "## Scientific boundaries",
     "The selected-population Hamming distance describes genotype spread, not objective-space spread, convergence, or effective search quality. Archive admissions are path-dependent, not causal per-arm credit; the baseline and local pairing schemes allocate evaluations differently. FLA phase is tied to iteration count, so DO/EO/SSO associations cannot establish why an algorithm wins or loses. A larger independent workflow-family experiment is necessary to generalize the mechanism."]
    (out/"phase_population_exact_report.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_phase_population_exact_followup.py ARTIFACT_ROOT OUT")
    main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
