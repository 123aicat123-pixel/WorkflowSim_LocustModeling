#!/usr/bin/env python3
"""Strict retrospective audit of PREDECLARED random K16 vs Pareto K16 source.

Never feeds simulator labels to the optimizer or replay selector. Source jobs:
planned policy 41969565802, random policy 41972072193. Identical ordered
visited-genotype SHA-256 is mandatory. Within-arm candidate pairs are
correlated and are NOT independent repetitions.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

DAGS=("CyberShake_50","Sipht_60","Epigenomics_100")
SEEDS=(951,952)
SOLVERS=("DAG-Pareto-FLA[v12-hvbandit]",
         "DAG-Pareto-FLA[v20-frontier-random]",
         "DAG-Pareto-FLA[v20-frontier-dag]",
         "NSGA-II[costseed]")
RUNS={"pareto":"41969565802","random":"41972072193"}

def read(p):
    with p.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def relation(a,b):
    if a[0]<=b[0] and a[1]<=b[1] and (a[0]<b[0] or a[1]<b[1]):return 1
    if b[0]<=a[0] and b[1]<=a[1] and (b[0]<a[0] or b[1]<a[1]):return -1
    return 0

def nd(points):
    return sorted(set(p for p in points if not any(relation(q,p)==1 for q in points)))

def hv(points,ref):
    prev=ref[1]
    val=0.
    for x,y in nd(points):
        if x<ref[0] and y<prev:
            val+=(ref[0]-x)*(prev-y)
            prev=y
    val/=ref[0]*ref[1]
    assert math.isfinite(val) and 0<=val<=1+1e-10
    return val

def write(path,rows):
    assert rows
    with path.open("w",newline="",encoding="utf-8") as f:
        out=csv.DictWriter(f,fieldnames=list(rows[0]))
        out.writeheader()
        out.writerows(rows)

def load(root,policy,dag,seed):
    run=RUNS[policy]
    prefix=("fla-v20-frontier" if policy=="pareto" else "fla-v20-random-rank")
    folder=root/f"{prefix}-{dag}-s{seed}-{run}"
    assert folder.is_dir(),("Source missing",folder)
    summary=read(folder/"research_summary.csv")
    replays=read(folder/"research_replays.csv")
    fingerprints=read(folder/"research_visited_fingerprints.csv")
    assert len(summary)==len(fingerprints)==4 and len(replays)==64
    assert {r["algorithm"] for r in summary}==set(SOLVERS)
    assert {r["algorithm"] for r in fingerprints}==set(SOLVERS)
    assert (folder/"source-sha.txt").read_text().strip()
    if policy=="random":
        assert (folder/"selection-policy.txt").read_text().strip()=="selector=random replicate=0 K=16"
    out={}
    for solver in SOLVERS:
        s=next(x for x in summary if x["algorithm"]==solver)
        f=next(x for x in fingerprints if x["algorithm"]==solver)
        rows=sorted([x for x in replays if x["algorithm"]==solver],
                    key=lambda x:int(x["candidate_index"]))
        assert len(rows)==16 and len({x["mapping"] for x in rows})==16
        assert [int(r["candidate_index"]) for r in rows]==list(range(1,17))
        assert s["workflow"]==dag and s["seed"]==str(seed)
        assert tuple(int(s[z]) for z in ("population","generations","evaluations","captured_evaluations","replayed"))==(30,100,3030,3030,16)
        assert len(f["history_sha256"])==64
        assert int(f["distinct_visited"])==int(s["distinct_observed"])
        values=[]
        for x in rows:
            planned=(float(x["planned_makespan"]),float(x["planned_cost"]))
            actual=(float(x["sim_makespan"]),float(x["sim_cost"]))
            assert all(math.isfinite(z) and z>0 for z in planned+actual)
            values.append((x["mapping"],planned,actual))
        out[solver]=dict(fingerprint=f["history_sha256"],rows=values,
                         distinct=int(s["distinct_observed"]))
    return out

def analyze(root,out):
    out.mkdir(parents=True,exist_ok=True)
    metrics=[]
    contrasts=[]
    for dag,seed in itertools.product(DAGS,SEEDS):
        loaded={p:load(root,p,dag,seed) for p in RUNS}
        all_truth=[q[2] for p,solver in itertools.product(RUNS,SOLVERS)
                   for q in loaded[p][solver]["rows"]]
        refs={factor:tuple(factor*max(pt[i] for pt in all_truth)+1e-6
                           for i in range(2)) for factor in (1.5,3.0)}
        for solver in SOLVERS:
            p=loaded["pareto"][solver]
            r=loaded["random"][solver]
            assert p["fingerprint"]==r["fingerprint"],(
                "Original search history changed",dag,seed,solver)
            assert p["distinct"]==r["distinct"]
            per={}
            for policy,record in (("pareto",p),("random",r)):
                rows=record["rows"]
                planned=[v[1] for v in rows]
                actual=[v[2] for v in rows]
                both_dominated=0
                predicted_dominance=0
                false_dominance=0
                reverse=0
                true_dominance=0
                new_true_dominance=0
                make_discordant=0
                make_comparable=0
                for i,j in itertools.combinations(range(16),2):
                    pd=relation(planned[i],planned[j])
                    td=relation(actual[i],actual[j])
                    predicted_dominance+=pd!=0
                    true_dominance+=td!=0
                    both_dominated+=(pd!=0 and td!=0)
                    false_dominance+=(pd!=0 and pd!=td)
                    reverse+=(pd!=0 and td==-pd)
                    new_true_dominance+=(pd==0 and td!=0)
                    d1=planned[i][0]-planned[j][0]
                    d2=actual[i][0]-actual[j][0]
                    if d1!=0 and d2!=0:
                        make_comparable+=1
                        make_discordant+=(d1*d2<0)
                plan_nd={i for i in range(16) if not any(
                    relation(planned[j],planned[i])==1 for j in range(16) if i!=j)}
                true_nd={i for i in range(16) if not any(
                    relation(actual[j],actual[i])==1 for j in range(16) if i!=j)}
                jac=len(plan_nd&true_nd)/len(plan_nd|true_nd)
                metric=dict(workflow=dag,seed=seed,solver=solver,policy=policy,
                    planned_dominance_pairs=predicted_dominance,
                    true_dominance_pairs=true_dominance,
                    false_predicted_dominance=false_dominance,
                    reverse_predicted_dominance=reverse,
                    planned_incomparable_became_true_dominance=new_true_dominance,
                    makespan_discordant_pairs=make_discordant,
                    makespan_comparable_pairs=make_comparable,nd_jaccard=jac,
                    true_hv15=hv(actual,refs[1.5]),
                    true_hv30=hv(actual,refs[3.0]),
                    physical_overlap=len({v[0] for v in p["rows"]}&
                                         {v[0] for v in r["rows"]}),
                    same_visited_sha=p["fingerprint"])
                metrics.append(metric)
                per[policy]=metric
            contrasts.append(dict(workflow=dag,seed=seed,solver=solver,
                random_minus_pareto_planned_dominance=
                    per["random"]["planned_dominance_pairs"]-per["pareto"]["planned_dominance_pairs"],
                random_minus_pareto_false_predicted_dominance=
                    per["random"]["false_predicted_dominance"]-per["pareto"]["false_predicted_dominance"],
                random_minus_pareto_true_hv15=
                    per["random"]["true_hv15"]-per["pareto"]["true_hv15"],
                random_predicted_pairs=per["random"]["planned_dominance_pairs"],
                pareto_predicted_pairs=per["pareto"]["planned_dominance_pairs"],
                random_false_pairs=per["random"]["false_predicted_dominance"],
                pareto_false_pairs=per["pareto"]["false_predicted_dominance"]))
    assert len(metrics)==48 and len(contrasts)==24
    write(out/"all_48_selected_rank_fidelity.csv",metrics)
    write(out/"all_24_random_vs_pareto_paired.csv",contrasts)
    report=["# Prospective randomized K16 replay selection: planner/simulator decision rank", "",
        "Six frozen DAG/seed blocks; four exact matched search-history solvers each.",
        "Two K16 predeclared selectors; 384 new random-selected physical simulator outcomes",
        "plus 384 original planned Pareto-selected outcomes. Samples overlap; do not count",
        "768 as 768 independent physical mappings. All 24 paired history SHA-256 identities checked.",""]
    for policy in RUNS:
        z=[x for x in metrics if x["policy"]==policy]
        n=sum(x["planned_dominance_pairs"] for x in z)
        f=sum(x["false_predicted_dominance"] for x in z)
        rr=sum(x["reverse_predicted_dominance"] for x in z)
        report.append(f"- {policy}: predicted comparable pairs={n}; false orientations={f}; "
                      f"direct reversals={rr}; conditional false-orientation fraction="
                      f"{f/n if n else float('nan'):.6f}. "
                      "These candidate pairs are correlated, not independent.")
    report+=["",
      "| DAG | seed | Solver | RANDOM predicted dominance | RANDOM false dominance | PARETO predicted dominance | PARETO false dominance | Random−Pareto real HV |",
      "|---|---:|---|---:|---:|---:|---:|---:|"]
    for x in contrasts:
        report.append(f"| {x['workflow']} | {x['seed']} | "
            f"{'FLA-v12' if x['solver']==SOLVERS[0] else x['solver']} | "
            f"{x['random_predicted_pairs']} | {x['random_false_pairs']} | "
            f"{x['pareto_predicted_pairs']} | {x['pareto_false_pairs']} | "
            f"{x['random_minus_pareto_true_hv15']:+.8f} |")
    report+=["","This is a methodological selection-bias diagnostic; no new optimizer",
        "or independent unseen-family generalization is asserted. All adverse results retained."]
    (out/"random_vs_pareto_fidelity_findings.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    assert len(sys.argv)==3,"Usage: audit.py ORIGINAL_ARTIFACT_ROOT OUTPUT"
    analyze(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
