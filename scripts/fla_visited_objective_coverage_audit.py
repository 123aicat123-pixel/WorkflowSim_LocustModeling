#!/usr/bin/env python3
"""Read-only complete visited planned-front vs K16 source coverage analysis.

The 3030 fitness visits are original planning model predictions, NOT WorkflowSim
truth. Validate original Java's bytewise history SHA256 and exact replay identity.
"""
import csv
import hashlib
import itertools
import math
import pathlib
import struct
import sys

DAGS=("Montage_50","Sipht_60")
SEEDS=(981,982)
SOLVERS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
RUN="41985327148"

def rows(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def dominates(a,b):
    return a[0]<=b[0] and a[1]<=b[1] and (a[0]<b[0] or a[1]<b[1])

def nondominated(points):
    ordered=sorted(set(points))
    best=float("inf");front=[]
    for p in ordered:
        if p[1]<best:
            front.append(p);best=p[1]
    return front

def hv(points,reference):
    top=reference[1];value=0.
    for m,c in nondominated(points):
        if m<reference[0] and c<top:
            value+=(reference[0]-m)*(top-c)
            top=c
    result=value/(reference[0]*reference[1])
    assert math.isfinite(result) and -1e-10<=result<=1+1e-10
    return result

def fingerprint(selected):
    digest=hashlib.sha256()
    for r in selected:
        m,c=float(r["planned_makespan"]),float(r["planned_cost"])
        def bits(v):
            return format(struct.unpack(">Q",struct.pack(">d",v))[0],"x")
        digest.update(f'{r["canonical_mapping"]}|{bits(m)}|{bits(c)}\n'.encode("utf-8"))
    return digest.hexdigest()

def map_id(replay):
    return "|".join(sorted(replay["mapping"].split("|"),key=lambda x:int(x.split(":")[0])))

def save(path,records):
    with path.open("w",newline="",encoding="utf-8") as f:
        wr=csv.DictWriter(f,fieldnames=list(records[0]))
        wr.writeheader();wr.writerows(records)

def audit(root,out):
    out.mkdir(parents=True,exist_ok=True)
    data={};source_shas=set()
    for dag,seed in itertools.product(DAGS,SEEDS):
        folder=root/f"fla-visited-coverage-{dag}-s{seed}-{RUN}"
        assert folder.is_dir(),("Missing source",str(folder))
        sha=(folder/"source-sha.txt").read_text().strip()
        assert len(sha)==40
        source_shas.add(sha)
        summary=rows(folder/"research_summary.csv")
        visits=rows(folder/"research_full_visited_objectives.csv")
        replay=rows(folder/"research_replays.csv")
        fingerprints=rows(folder/"research_visited_fingerprints.csv")
        assert len(summary)==len(fingerprints)==2 and len(replay)==32
        assert {x["algorithm"] for x in summary}==set(SOLVERS)
        assert {x["algorithm"] for x in fingerprints}==set(SOLVERS)
        assert {x["algorithm"] for x in visits}==set(SOLVERS)
        for solver in SOLVERS:
            s=next(x for x in summary if x["algorithm"]==solver)
            f=next(x for x in fingerprints if x["algorithm"]==solver)
            v=[x for x in visits if x["algorithm"]==solver]
            k=sorted([x for x in replay if x["algorithm"]==solver],
                     key=lambda x:int(x["candidate_index"]))
            assert (s["workflow"],s["seed"])==(dag,str(seed))
            assert tuple(int(s[q]) for q in ("population","generations","evaluations","captured_evaluations","replayed"))==(30,100,3030,3030,16)
            assert len(v)==int(s["distinct_observed"])==int(f["distinct_visited"])
            assert [int(x["visited_index"]) for x in v]==list(range(1,len(v)+1))
            assert len(k)==16 and len({x["mapping"] for x in k})==16
            assert len({x["canonical_mapping"] for x in v})==len(v)
            assert fingerprint(v)==f["history_sha256"],"Byte-for-byte original source fingerprint mismatch"
            dictionary={r["canonical_mapping"]:(float(r["planned_makespan"]),float(r["planned_cost"])) for r in v}
            for r in v:
                assert (r["workflow"],r["seed"])==(dag,str(seed))
                assert all(math.isfinite(float(r[q])) and float(r[q])>0 for q in ("planned_makespan","planned_cost"))
            for r in k:
                key=map_id(r)
                assert key in dictionary, "Selected replay not in original visited pool"
                a=dictionary[key]
                b=(float(r["planned_makespan"]),float(r["planned_cost"]))
                assert all(abs(x-y)<1e-9*max(1,abs(x),abs(y)) for x,y in zip(a,b))
            data[(dag,seed,solver)]=dict(full=list(dictionary.values()),
                                         selected=[dictionary[map_id(r)] for r in k],
                                         simulated=[(float(r["sim_makespan"]),float(r["sim_cost"])) for r in k],
                                         distinct=len(v),sha=sha)
    assert len(source_shas)==1,("Source code differed across blocks",source_shas)
    output=[]
    for dag,seed in itertools.product(DAGS,SEEDS):
        cases={solver:data[dag,seed,solver] for solver in SOLVERS}
        allpoints=[p for d in cases.values() for p in d["full"]]
        ref=tuple(1.5*max(p[q] for p in allpoints)+1e-6 for q in (0,1))
        actualall=[p for d in cases.values() for p in d["simulated"]]
        actualref=tuple(1.5*max(p[q] for p in actualall)+1e-6 for q in (0,1))
        for solver,d in cases.items():
            fullfront=nondominated(d["full"])
            selectedfront=nondominated(d["selected"])
            fullhv=hv(d["full"],ref)
            selectedhv=hv(d["selected"],ref)
            assert selectedhv<=fullhv+1e-10
            map_cov=sum(p in set(selectedfront) for p in fullfront)
            b=[0]*10
            lo=min(p[0] for p in fullfront);hi=max(p[0] for p in fullfront)
            for p in fullfront:
                idx=min(9,int(10*(p[0]-lo)/max(1e-12,hi-lo)))
                b[idx]+=1
            output.append(dict(workflow=dag,seed=seed,solver=solver,
                visited_unique=d["distinct"],full_planned_nd=len(fullfront),
                replay_selected_nd=len(selectedfront),
                selected_nd_overlap=map_cov,full_planned_hv15=fullhv,
                selected_planned_hv15=selectedhv,
                selected_over_full_hv=selectedhv/fullhv if fullhv else 0.,
                missing_planned_hv=fullhv-selectedhv,
                true_k16_hv15=hv(d["simulated"],actualref),
                full_nd_occupied_bins=sum(x>0 for x in b),
                full_nd_bin_counts="|".join(str(x) for x in b),
                source_sha=d["sha"]))
    assert len(output)==8
    save(out/"all_8_full_visited_planned_coverage.csv",output)
    result=["# Full visited planned-objective coverage: eight strictly audited solver cases",
            "","Original source: "+RUN,
            "No simulator truth for all visited genotypes. Ratios are within the cheap planning model only.",
            "Export was pre-replay, complete and byte-for-byte source-SHA verified.","",
            "| DAG | seed | Solver | Unique visited | Full planned ND | Selected planned ND | Selected/full predicted HV |",
            "|---|---:|---|---:|---:|---:|---:|"]
    for r in output:
        result.append(f"| {r['workflow']} | {r['seed']} | {r['solver']} | "
                      f"{r['visited_unique']} | {r['full_planned_nd']} | "
                      f"{r['replay_selected_nd']} | {r['selected_over_full_hv']:.9f} |")
    result+=["","This is a nonintrusive MODEL-SPACE diagnostic only, not a new FLA algorithm.",
              "The full visited true Pareto front is UNKNOWN because almost all assignments were not actually simulated.",
              "No unseen-family generalization, runtime parity or paper superiority claims."]
    (out/"full_visited_coverage_findings.md").write_text("\n".join(result)+"\n",encoding="utf-8")
    print("\n".join(result))

if __name__=="__main__":
    assert len(sys.argv)==3
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
