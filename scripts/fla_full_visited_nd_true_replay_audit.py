#!/usr/bin/env python3
"""Immutable, independent actual-WorkflowSim audit of all visited planned ND.

Original K16 run 41985327148, extra all-planned-ND run 41986249710.
Only read original artifacts; no simulator/optimizer execution.
"""
import csv
import itertools
import math
import pathlib
import sys

DAGS=("Montage_50","Sipht_60")
SEEDS=(981,982)
SOLVERS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
OLD_RUN="41985327148"
NEW_RUN="41986249710"

def read(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def canonical(mapping):
    return "|".join(sorted(mapping.split("|"),key=lambda a:int(a.split(":")[0])))

def dominates(a,b):
    return a[0]<=b[0] and a[1]<=b[1] and (a[0]<b[0] or a[1]<b[1])

def nondominated(points):
    s=sorted(set(points))
    out=[];best=float("inf")
    for p in s:
        if p[1]<best:
            out.append(p)
            best=p[1]
    return out

def hv(points,ref):
    top=ref[1];area=0.
    for m,c in nondominated(points):
        if m<ref[0] and c<top:
            area+=(ref[0]-m)*(top-c)
            top=c
    value=area/(ref[0]*ref[1])
    assert math.isfinite(value) and 0<=value<=1+1e-10
    return value

def put(path,rows):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)

def parse(root,dag,seed,mode):
    run=OLD_RUN if mode=="k16" else NEW_RUN
    label="fla-visited-coverage" if mode=="k16" else "fla-full-planned-nd"
    folder=root/f"{label}-{dag}-s{seed}-{run}"
    assert folder.is_dir(),("Missing source",folder)
    sha=(folder/"source-sha.txt").read_text().strip()
    assert len(sha)==40
    summary=read(folder/"research_summary.csv")
    fingerprints=read(folder/"research_visited_fingerprints.csv")
    visits=read(folder/"research_full_visited_objectives.csv")
    replay=read(folder/"research_replays.csv")
    assert len(summary)==len(fingerprints)==2
    assert {s["algorithm"] for s in summary}==set(SOLVERS)
    assert {s["algorithm"] for s in fingerprints}==set(SOLVERS)
    assert {s["algorithm"] for s in visits}==set(SOLVERS)
    data={}
    for solver in SOLVERS:
        s=next(x for x in summary if x["algorithm"]==solver)
        f=next(x for x in fingerprints if x["algorithm"]==solver)
        vs=[x for x in visits if x["algorithm"]==solver]
        rs=[x for x in replay if x["algorithm"]==solver]
        assert (s["workflow"],s["seed"])==(dag,str(seed))
        assert int(s["evaluations"])==int(s["captured_evaluations"])==3030
        assert len(vs)==int(s["distinct_observed"])==int(f["distinct_visited"])
        assert len(rs)==int(s["replayed"])
        assert len({x["mapping"] for x in rs})==len(rs)
        expected={}
        for v in vs:
            key=v["canonical_mapping"]
            point=(float(v["planned_makespan"]),float(v["planned_cost"]))
            assert all(math.isfinite(x) and x>0 for x in point)
            assert key not in expected
            expected[key]=point
        actual={}
        for v in rs:
            key=canonical(v["mapping"])
            assert key in expected,("Unknown physical genotype",key)
            p=(float(v["planned_makespan"]),float(v["planned_cost"]))
            assert all(abs(a-b)<=1e-9*max(1,abs(a),abs(b))
                       for a,b in zip(p,expected[key]))
            a=(float(v["sim_makespan"]),float(v["sim_cost"]))
            assert all(math.isfinite(x) and x>0 for x in a)
            actual[key]=a
        if mode=="k16":
            assert len(actual)==16
        else:
            assert 1<=len(actual)<=80
            # Match original Java plannedNondominated: first unique objective
            # point in original ordered history wins any exact objective tie.
            ordered=sorted(enumerate(vs),key=lambda pair:(
                float(pair[1]["planned_makespan"]),
                float(pair[1]["planned_cost"]),pair[0]))
            expected_nd=set()
            best=float("inf")
            for _,v in ordered:
                cost=float(v["planned_cost"])
                if cost<best:
                    expected_nd.add(v["canonical_mapping"])
                    best=cost
            assert set(actual)==expected_nd,("Not exact source visited ND",dag,seed,solver)
        data[solver]=dict(sha=sha,fingerprint=f["history_sha256"],
                          visited=expected,truth=actual)
    return data

def audit(root,out):
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    source_shas={"k16":set(),"full":set()}
    for dag,seed in itertools.product(DAGS,SEEDS):
        original=parse(root,dag,seed,"k16")
        allnd=parse(root,dag,seed,"full")
        pool=[point for solver in SOLVERS
              for d in (original[solver],allnd[solver])
              for point in d["truth"].values()]
        ref15=tuple(1.5*max(p[i] for p in pool)+1e-6 for i in (0,1))
        ref30=tuple(3.0*max(p[i] for p in pool)+1e-6 for i in (0,1))
        for solver in SOLVERS:
            old=original[solver];full=allnd[solver]
            source_shas["k16"].add(old["sha"])
            source_shas["full"].add(full["sha"])
            assert old["fingerprint"]==full["fingerprint"],(
                "Source optimizer history changed",dag,seed,solver)
            assert old["visited"]==full["visited"],("Cheap model scores changed",dag,seed,solver)
            common=set(old["truth"])&set(full["truth"])
            for k in common:
                x=old["truth"][k];y=full["truth"][k]
                assert all(abs(x[i]-y[i])<=1e-7*max(1,abs(x[i]),abs(y[i]))
                           for i in (0,1)),("Actual simulator mismatch for same physical mapping",dag,seed,solver,k)
            union=dict(old["truth"]);union.update(full["truth"])
            a=hv(old["truth"].values(),ref15)
            b=hv(full["truth"].values(),ref15)
            c=hv(union.values(),ref15)
            assert c+1e-10>=max(a,b)
            # Distinguish extra full ND simulator calls from K16 budget:
            # this union is an after-the-fact diagnostic and not an executable K16.
            new_nd=set(full["truth"])-set(old["truth"])
            valuable=sum(hv(list(old["truth"].values())+[full["truth"][k]],ref15)>a+1e-10
                         for k in new_nd)
            rows.append(dict(workflow=dag,seed=seed,solver=solver,
                same_ordered_search_sha=old["fingerprint"],
                original_k16_replays=len(old["truth"]),
                full_planned_nd_replays=len(full["truth"]),
                overlapping_physical_assignments=len(common),
                new_full_nd_assignments=len(new_nd),
                new_individual_actual_hv_contributors=valuable,
                original_k16_true_hv15=a,full_nd_true_hv15=b,
                union_observed_true_hv15=c,
                full_nd_minus_k16_hv15=b-a,
                optimistic_union_minus_k16_hv15=c-a,
                full_nd_minus_k16_hv30=hv(full["truth"].values(),ref30)-
                                        hv(old["truth"].values(),ref30),
                source_original_sha=old["sha"],source_full_sha=full["sha"]))
    assert len(rows)==8
    assert all(len(s)==1 for s in source_shas.values())
    put(out/"all_8_full_planned_nd_true_replay.csv",rows)
    findings=["# Complete source-visited planned ND TRUE WorkflowSim outcome", "",
        "Original immutable K16 source "+OLD_RUN+"; all-planned-ND source "+NEW_RUN+".",
        "Both original optimizers and their entire ordered genotype histories match SHA256 for every block.",
        "The full planned ND arm pays a VARIABLE higher simulator budget and is NOT a fair K16 algorithm.",
        "Shared same-(workflow,seed) actual HV reference across two solvers and two replay sources.","",
        "| DAG | Seed | Solver | Original K16 | Full planned ND | Additional unique | Extra actual-HV contributors | Full ND − K16 real HV | Observed union − K16 HV |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        findings.append(f"| {r['workflow']} | {r['seed']} | {r['solver']} | "
            f"{r['original_k16_replays']} | {r['full_planned_nd_replays']} | "
            f"{r['new_full_nd_assignments']} | {r['new_individual_actual_hv_contributors']} | "
            f"{r['full_nd_minus_k16_hv15']:+.9f} | "
            f"{r['optimistic_union_minus_k16_hv15']:+.9f} |")
    findings+=["","The planning-dominated source genotypes remain true-simulator unobserved.",
        "Neither observed union nor all planned ND is a global true Pareto bound.",
        "Do not claim improved FLA performance or equal simulator budget from this diagnostic."]
    (out/"all_planned_nd_true_replay_findings.md").write_text("\n".join(findings)+"\n",encoding="utf-8")
    print("\n".join(findings))

if __name__=="__main__":
    assert len(sys.argv)==3
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
