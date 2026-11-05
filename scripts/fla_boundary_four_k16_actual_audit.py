#!/usr/bin/env python3
"""Independent K16 fixed-source prospective boundary-four audit.
Only source archived real WorkflowSim outputs, no source/simulator re-execution.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

RUN="41975729241"
WORKFLOWS=("Montage_50","Inspiral_50","CyberShake_30","Epigenomics_46")
SEEDS=(971,972)
POLICIES=("pareto-cover","boundary-four","dominated-random-four")
SOLVERS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")

def read(p):
    with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def dominates(a,b):
    return a[0]<=b[0] and a[1]<=b[1] and (a[0]<b[0] or a[1]<b[1])

def hv(points,ref):
    nd=sorted(set(p for p in points if not any(dominates(q,p) for q in points)))
    upper=ref[1]
    area=0.
    for a,b in nd:
        if a<ref[0] and b<upper:
            area+=(ref[0]-a)*(upper-b)
            upper=b
    h=area/(ref[0]*ref[1])
    assert math.isfinite(h) and -1e-10<=h<=1+1e-10
    return h

def save(path,rows):
    assert rows
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)

def load(root,dag,seed,policy):
    folder=root/f"fla-boundary-four-{dag}-s{seed}-{policy}-{RUN}"
    assert folder.is_dir(),("Missing source artifact",str(folder))
    metadata=dict(a.split("=",1) for a in (folder/"block-id.txt").read_text().split())
    assert metadata==dict(DAG=dag,seed=str(seed),policy=policy,K="16",visits="3030",VM="default"),metadata
    sha=(folder/"source-sha.txt").read_text().strip()
    assert len(sha)==40
    ss=read(folder/"research_summary.csv")
    replays=read(folder/"research_replays.csv")
    fingerprint=read(folder/"research_visited_fingerprints.csv")
    assert len(ss)==len(fingerprint)==2 and len(replays)==32
    assert {x["algorithm"] for x in ss}==set(SOLVERS)
    assert {x["algorithm"] for x in fingerprint}==set(SOLVERS)
    result={}
    for solver in SOLVERS:
        summary=next(x for x in ss if x["algorithm"]==solver)
        fp=next(x for x in fingerprint if x["algorithm"]==solver)
        rr=sorted((x for x in replays if x["algorithm"]==solver),key=lambda x:int(x["candidate_index"]))
        assert summary["workflow"]==dag and summary["seed"]==str(seed)
        assert tuple(int(summary[z]) for z in ("population","generations","evaluations","captured_evaluations","replayed"))==(30,100,3030,3030,16)
        assert len(rr)==16 and len({x["mapping"] for x in rr})==16
        assert [int(x["candidate_index"]) for x in rr]==list(range(1,17))
        assert len(fp["history_sha256"])==64
        assert int(fp["distinct_visited"])==int(summary["distinct_observed"])
        pairs=[]
        for x in rr:
            planned=(float(x["planned_makespan"]),float(x["planned_cost"]))
            actual=(float(x["sim_makespan"]),float(x["sim_cost"]))
            assert all(math.isfinite(t) and t>0 for t in planned+actual)
            pairs.append((x["mapping"],planned,actual))
        total=float(summary["search_selection_replay_ms"])
        search=float(summary["search_ms"])
        select=float(summary["selection_ms"])
        assert all(math.isfinite(x) and x>=0 for x in (total,search,select))
        result[solver]=dict(sha=sha,history=fp["history_sha256"],rows=pairs,
                            unique=int(summary["distinct_observed"]),
                            total_ms=total,search_ms=search,selection_ms=select)
    return result

def audit(root,out):
    out.mkdir(parents=True,exist_ok=True)
    by={}
    source_shas=set()
    for dag,seed,policy in itertools.product(WORKFLOWS,SEEDS,POLICIES):
        case=load(root,dag,seed,policy)
        for solver in SOLVERS:
            d=case[solver]
            source_shas.add(d["sha"])
            by[dag,seed,policy,solver]=d
    assert len(by)==48 and len(source_shas)==1,("Different source code across jobs",source_shas)
    data=[]
    comparisons=[]
    for dag,seed in itertools.product(WORKFLOWS,SEEDS):
        all_truth=[row[2] for policy,solver in itertools.product(POLICIES,SOLVERS)
                   for row in by[dag,seed,policy,solver]["rows"]]
        references={f:tuple(f*max(p[j] for p in all_truth)+1e-6 for j in range(2))
                    for f in (1.5,3.0)}
        for solver in SOLVERS:
            records={policy:by[dag,seed,policy,solver] for policy in POLICIES}
            assert len({r["history"] for r in records.values()})==1,(
                "Optimizer search changed across selectors",dag,seed,solver)
            original=records["pareto-cover"]["rows"]
            boundary=records["boundary-four"]["rows"]
            random=records["dominated-random-four"]["rows"]
            assert [x[0] for x in boundary[:12]]==[x[0] for x in random[:12]],(
                "Not matched K12 first samples",dag,seed,solver)
            assert [x[0] for x in boundary[:12]]==[x[0] for x in original[:12]],(
                "K12 changed relative to original K16",dag,seed,solver)
            for policy,run in records.items():
                own=run["rows"]
                other=[r[2] for r in own]
                true_nd=sum(not any(dominates(q,p) for q in other)
                            for p in other)
                dominated_four=sum(
                    any(dominates(p[1],r[1]) for p in own[:12])
                    for r in own[12:])
                if policy!="pareto-cover":
                    assert dominated_four==4,("Exploration not dominated by K12 in planning",
                                              policy,dag,seed,solver)
                data.append(dict(workflow=dag,seed=seed,solver=solver,policy=policy,
                    hv15=hv(other,references[1.5]),hv30=hv(other,references[3.0]),
                    true_nondominated_count=true_nd,
                    dominated_exploration_four=dominated_four,
                    count_real_replays=16,
                    unique_visited=run["unique"],
                    search_ms=run["search_ms"],
                    selection_ms=run["selection_ms"],
                    search_selection_replay_ms=run["total_ms"],
                    history_sha=run["history"],source_sha=run["sha"]))
            values={p:next(x for x in data if (x["workflow"],x["seed"],x["solver"],x["policy"])==
                (dag,seed,solver,p)) for p in POLICIES}
            base=values["pareto-cover"]; boundary=values["boundary-four"];random=values["dominated-random-four"]
            comparisons.append(dict(workflow=dag,seed=seed,solver=solver,
                baseline_hv15=base["hv15"],boundary_hv15=boundary["hv15"],
                random_hv15=random["hv15"],
                delta_boundary_baseline_15=boundary["hv15"]-base["hv15"],
                delta_boundary_random_15=boundary["hv15"]-random["hv15"],
                delta_random_baseline_15=random["hv15"]-base["hv15"],
                delta_boundary_baseline_30=boundary["hv30"]-base["hv30"],
                delta_boundary_random_30=boundary["hv30"]-random["hv30"],
                boundary_selection_ms=boundary["selection_ms"],
                random_selection_ms=random["selection_ms"],
                baseline_selection_ms=base["selection_ms"]))
    assert len(data)==48 and len(comparisons)==16
    save(out/"all_48_actual_k16_hv.csv",data)
    save(out/"all_16_paired_deltas.csv",comparisons)
    summary=[
        "# Frozen boundary-four K16 actual WorkflowSim results","",
        "All 24 source jobs, 48 solver-arm fronts, 768 REAL K16 replay rows audited.",
        "Same original 3030 counted fitness evaluations and exact ordered visited-history SHA per 3 policies.",
        "The first K12 physical placements match across three selectors for every case.",
        "Boundary and stratified random each use four pre-replay planned-dominated mappings; no true label is used in selection.",
        "Source SHA and positive true objectives verified; one shared reference per workflow/seed across all solver/policy arms.",
        "No independent unseen-family or equal CPU evidence; do not treat K16 points as independent observations.","",
        "| DAG | seed | solver | Pareto HV15 | boundary HV15 | random HV15 | boundary−Pareto | boundary−random |",
        "|---|---:|---|---:|---:|---:|---:|---:|"]
    for x in comparisons:
        summary.append(f"| {x['workflow']} | {x['seed']} | {x['solver']} | "
            f"{x['baseline_hv15']:.8f} | {x['boundary_hv15']:.8f} | "
            f"{x['random_hv15']:.8f} | {x['delta_boundary_baseline_15']:+.8f} | "
            f"{x['delta_boundary_random_15']:+.8f} |")
    for field in ("delta_boundary_baseline_15","delta_boundary_random_15",
                  "delta_random_baseline_15","delta_boundary_baseline_30",
                  "delta_boundary_random_30"):
        vals=[x[field] for x in comparisons]
        summary.append(f"- {field}: mean {statistics.mean(vals):+.9f}, "
            f"wins/ties/losses {sum(v>1e-10 for v in vals)}/"
            f"{sum(abs(v)<=1e-10 for v in vals)}/{sum(v< -1e-10 for v in vals)}.")
    summary+=["","Any negative result is kept; post-hoc tuning on these seeds is not independent validation.",
              "This is a post-search replay policy test, NOT a demonstrated improved FLA evolutionary operator."]
    (out/"boundary_four_actual_findings.md").write_text("\n".join(summary)+"\n",encoding="utf-8")
    print("\n".join(summary))
if __name__=="__main__":
    assert len(sys.argv)==3,"Usage: audit.py ORIGINAL_ARTIFACT_ROOT REPORTS"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
