#!/usr/bin/env python3
"""Retrospective TRUE-WorkflowSim union headroom from original matched K16 runs.

Inputs: six original planned-Pareto and six original random-replay archives.
Every numeric simulator label is used AFTER selection; this is NOT an
executable Pareto policy, causal treatment effect, global optimum or test set.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

PLANNED_RUN="41969565802"
RANDOM_RUN="41972072193"
DAGS=("CyberShake_50","Sipht_60","Epigenomics_100")
SEEDS=(951,952)
SOLVERS=("DAG-Pareto-FLA[v12-hvbandit]",
         "DAG-Pareto-FLA[v20-frontier-random]",
         "DAG-Pareto-FLA[v20-frontier-dag]",
         "NSGA-II[costseed]")

def csvread(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def dominates(a,b):
    return a[0]<=b[0] and a[1]<=b[1] and (a[0]<b[0] or a[1]<b[1])

def pareto(points):
    x=list(points)
    return sorted(set(z for z in x if not any(dominates(q,z) for q in x)))

def hv(points,reference):
    ceiling=reference[1]
    area=0.0
    for x,y in pareto(points):
        if x<reference[0] and y<ceiling:
            area+=(reference[0]-x)*(ceiling-y)
            ceiling=y
    value=area/(reference[0]*reference[1])
    assert math.isfinite(value) and -1e-12<=value<=1+1e-12
    return value

def read_block(root,policy,dag,seed):
    run=PLANNED_RUN if policy=="pareto" else RANDOM_RUN
    prefix="fla-v20-frontier" if policy=="pareto" else "fla-v20-random-rank"
    folder=root/f"{prefix}-{dag}-s{seed}-{run}"
    assert folder.is_dir(),("Missing original job artifact",str(folder))
    summary=csvread(folder/"research_summary.csv")
    replay=csvread(folder/"research_replays.csv")
    fingerprints=csvread(folder/"research_visited_fingerprints.csv")
    source=(folder/"source-sha.txt").read_text().strip()
    assert len(source)==40 and len(summary)==len(fingerprints)==4 and len(replay)==64
    assert {r["algorithm"] for r in summary}==set(SOLVERS)
    assert {r["algorithm"] for r in fingerprints}==set(SOLVERS)
    if policy=="random":
        assert (folder/"selection-policy.txt").read_text().strip()=="selector=random replicate=0 K=16"
    result={}
    for solver in SOLVERS:
        a=next(r for r in summary if r["algorithm"]==solver)
        f=next(r for r in fingerprints if r["algorithm"]==solver)
        rows=sorted((r for r in replay if r["algorithm"]==solver),
                    key=lambda x:int(x["candidate_index"]))
        assert a["workflow"]==dag and a["seed"]==str(seed)
        assert tuple(int(a[z]) for z in
                     ("population","generations","evaluations","captured_evaluations","replayed"))==(30,100,3030,3030,16)
        assert len(rows)==16 and [int(r["candidate_index"]) for r in rows]==list(range(1,17))
        assert len({r["mapping"] for r in rows})==16 and len(f["history_sha256"])==64
        assert int(f["distinct_visited"])==int(a["distinct_observed"])
        observations={}
        for r in rows:
            plan=tuple(float(r[k]) for k in ("planned_makespan","planned_cost"))
            actual=tuple(float(r[k]) for k in ("sim_makespan","sim_cost"))
            assert all(math.isfinite(z) and z>0 for z in plan+actual)
            observations[r["mapping"]]=(plan,actual)
        result[solver]=dict(observations=observations,source=source,
                            history=f["history_sha256"])
    return result

def write(path,records):
    assert records
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

def audit(root,out):
    out.mkdir(parents=True,exist_ok=True)
    all_results=[]
    source_shas={"pareto":set(),"random":set()}
    for dag,seed in itertools.product(DAGS,SEEDS):
        original=read_block(root,"pareto",dag,seed)
        random=read_block(root,"random",dag,seed)
        for policy,record in (("pareto",original),("random",random)):
            source_shas[policy].add(next(iter(record.values()))["source"])
        # One reference shared by 4 original solvers × 2 replay policies.
        all_truth=[v[1] for record in (original,random) for solver in SOLVERS
                   for v in record[solver]["observations"].values()]
        reference=tuple(1.5*max(z[i] for z in all_truth)+1e-6 for i in (0,1))
        for solver in SOLVERS:
            a=original[solver]
            b=random[solver]
            assert a["history"]==b["history"],("Optimizer search histories diverged",dag,seed,solver)
            P=a["observations"]
            R=b["observations"]
            union=dict(P)
            for mapping,(p,t) in R.items():
                if mapping in union:
                    old_p,old_t=union[mapping]
                    assert all(abs(old_p[i]-p[i])<=1e-8*max(1,abs(p[i])) for i in range(2))
                    assert all(abs(old_t[i]-t[i])<=1e-8*max(1,abs(t[i])) for i in range(2))
                else:
                    union[mapping]=(p,t)
            planned_pts=[v[1] for v in P.values()]
            planned_scores=[v[0] for v in P.values()]
            planned_hv=hv(planned_pts,reference)
            random_hv=hv((v[1] for v in R.values()),reference)
            union_hv=hv((v[1] for v in union.values()),reference)
            assert union_hv+1e-10>=max(planned_hv,random_hv)
            false_excluded=0
            random_nondominated=0
            positive_gain=0
            for mapping,(pred,true) in R.items():
                if mapping in P:continue
                true_dominated=any(dominates(q,true) for q in planned_pts)
                predicted_dominated=any(dominates(q,pred) for q in planned_scores)
                improvement=hv(planned_pts+[true],reference)-planned_hv
                if not true_dominated:random_nondominated+=1
                if improvement>1e-10:positive_gain+=1
                if predicted_dominated and not true_dominated:
                    # Quantifies observed erroneous exclusion, NOT an actual
                    # prospective candidate retention policy.
                    assert improvement>1e-10
                    false_excluded+=1
            all_results.append(dict(workflow=dag,seed=seed,solver=solver,
                planned_true_hv15=planned_hv,random_true_hv15=random_hv,
                hindsight_union_all_true_hv15=union_hv,
                observed_union_hv_headroom=union_hv-planned_hv,
                distinct_observed_union=len(union),
                overlap_planned_random=len(set(P)&set(R)),
                random_only_nondominated_vs_planned=random_nondominated,
                random_only_positive_hv_gain=positive_gain,
                falsely_excluded_nondominated_random_only=false_excluded,
                original_history_sha256=a["history"]))
    assert len(all_results)==24
    assert all(len(shas)==1 for shas in source_shas.values()),("Differing source SHA within study",source_shas)
    assert sum(r["distinct_observed_union"] for r in all_results)==764
    assert sum(r["falsely_excluded_nondominated_random_only"] for r in all_results)==14
    write(out/"all_24_matched_k16_union_headroom.csv",all_results)
    total=sum(r["falsely_excluded_nondominated_random_only"] for r in all_results)
    improved=sum(r["observed_union_hv_headroom"]>1e-10 for r in all_results)
    report=[
      "# v20 matched-search Pareto-vs-random K16 TRUE union diagnostic","",
      "Original immutable planned run: "+PLANNED_RUN+"; original immutable random run: "+RANDOM_RUN+".",
      "All 12 original artifacts, 24 SHA-identical solver histories and 768 K16 replay records audited.",
      "Within solver/DAG/seed deduplicated distinct physical assignments total: "
         +str(sum(r["distinct_observed_union"] for r in all_results))
         +" (not 764 globally independent workflows).",
      "Actual false-excluded candidates (random-only, planned-dominated by a planned-selected candidate, "
        "but NOT truly dominated by any planned-selected candidate): "+str(total)+".",
      "All 14 contributed a positive singleton marginal TRUE HV in hindsight, "
        "but the magnitude and search feasibility of an actual prospective selector are unproven.",
      "Observed union has greater true HV than planned K16 in "
        +str(improved)+"/24 solver/DAG/seed blocks.",
      "Mean normalized union-all-minus-original K16 HV = "
        +format(statistics.mean(r["observed_union_hv_headroom"] for r in all_results),"+.9f")+".",
      "Note: union-all HV uses 16–32 true-labeled assignments and is an optimistic upper "
        "bound ONLY over their observed union, NOT an achievable K16 guarantee, "
        "not a global true Pareto bound, and not a prospective algorithm.","",
      "| DAG | Seed | Solver | Union unique | False-excluded | Planned HV | Union-all HV | Gap |",
      "|---|---:|---|---:|---:|---:|---:|---:|"
    ]
    for r in all_results:
        report.append("| "+str(r["workflow"])+" | "+str(r["seed"])+" | "+str(r["solver"])
            +" | "+str(r["distinct_observed_union"])+" | "
            +str(r["falsely_excluded_nondominated_random_only"])+" | "
            +format(r["planned_true_hv15"],".8f")+" | "
            +format(r["hindsight_union_all_true_hv15"],".8f")+" | "
            +format(r["observed_union_hv_headroom"],"+.8f")+" |")
    report+=["","Methods were inspected on three familiar DAG families and two already observed seeds. "
             "The 24 arms and their internal pairs are correlated; no SCI significance "
             "or unseen-family model calibration can be asserted. Original negative results retained."]
    (out/"hindsight_union_findings.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))
if __name__=="__main__":
    assert len(sys.argv)==3,"Usage: python script.py ORIGINAL_ARTIFACT_ROOT REPORT_DIR"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
