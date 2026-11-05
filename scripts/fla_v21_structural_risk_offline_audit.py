#!/usr/bin/env python3
"""Frozen retrospective v21 DAG structural risk K8 ablation from original labels.
The selection policy NEVER receives true simulator values, which are only used
in an independent after-selection HV audit. Not an unseen-family holdout.
"""
import csv
import hashlib
import itertools
import math
import pathlib
import random
import statistics
import struct
import sys
import xml.etree.ElementTree as ET

RUN="41990207133"
DAGS=("Montage_50","Sipht_60","CyberShake_30","Epigenomics_46")
SEEDS=(991,992)
SOLVERS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
POLICIES=("structural","near8","uniform8")
EXPECTED_SOURCE_SHA="9f4d0c4250068cf60be32aa06a92c83381bfb5b1"

def read(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def save(path,rows):
    assert rows
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def canonical(mapping):
    bits=mapping.split("|")
    entries=[tuple(int(z) for z in a.split(":")) for a in bits]
    assert len(entries)==len(set(x for x,_ in entries))
    return "|".join(f"{a}:{b}" for a,b in sorted(entries))

def decode(mapping,count):
    pairs=[tuple(int(x) for x in term.split(":")) for term in mapping.split("|")]
    ids=[i for i,_ in pairs]
    assert len(pairs)==count and set(ids)==set(range(1,count+1)),("Not original DAX task IDs",count)
    return dict(pairs)

def source_sha(rows):
    d=hashlib.sha256()
    for r in rows:
        def bits(x):
            return format(struct.unpack(">Q",struct.pack(">d",float(x)))[0],"x")
        d.update((r["canonical_mapping"]+"|"+bits(r["planned_makespan"])+"|"
                  +bits(r["planned_cost"])+"\n").encode("utf-8"))
    return d.hexdigest()

def parse_dax(path):
    root=ET.parse(path).getroot()
    jobs=[x for x in root if x.tag.rsplit("}",1)[-1]=="job"]
    assert len(jobs)>0
    names={}
    runtimes={}
    for i,job in enumerate(jobs,1):
        name=job.attrib["id"]
        assert name not in names
        names[name]=i
        runtime=max(0.1,float(job.attrib.get("runtime","0.1")))
        runtimes[i]=runtime
    assert int(root.attrib["jobCount"])==len(jobs),("DAX task count",path)
    edges=[]
    for node in root:
        if node.tag.rsplit("}",1)[-1]!="child":
            continue
        child=names[node.attrib["ref"]]
        for par in node:
            assert par.tag.rsplit("}",1)[-1]=="parent"
            edges.append((names[par.attrib["ref"]],child))
    assert len(edges)>0 and len(set(edges))==len(edges)
    return runtimes,edges

def exposure(mapping,runtimes,edges):
    assignment=decode(mapping,len(runtimes))
    vm_runtime={}
    for task,vm in assignment.items():
        vm_runtime[vm]=vm_runtime.get(vm,0.)+runtimes[task]
    queue=max(vm_runtime.values())/sum(runtimes.values())
    total=sum(runtimes[child] for _,child in edges)
    cross=sum(runtimes[child] for par,child in edges
              if assignment[par]!=assignment[child])
    edge=cross/total
    assert 0<=queue<=1+1e-10 and 0<=edge<=1+1e-10
    return queue,edge,0.5*(queue+edge)

def dominates(a,b):
    return a[0]<=b[0] and a[1]<=b[1] and (a[0]<b[0] or a[1]<b[1])

def hv(points,ref):
    best=float("inf")
    top=ref[1]
    value=0.
    for m,c in sorted(set(points)):
        if c>=best:
            continue
        best=c
        if m<ref[0] and c<top:
            value+=(ref[0]-m)*(top-c)
            top=c
    value/=ref[0]*ref[1]
    assert math.isfinite(value) and -1e-12<=value<=1+1e-12,value
    return value

def load_source(root,dag,seed):
    folder=root/f"fla-v21-dominated-{dag}-s{seed}-{RUN}"
    assert folder.is_dir(),("Missing source artifact",folder)
    assert (folder/"source-sha.txt").read_text().strip()==EXPECTED_SOURCE_SHA
    summaries=read(folder/"research_summary.csv")
    visited=read(folder/"research_full_visited_objectives.csv")
    fp=read(folder/"research_visited_fingerprints.csv")
    replay=read(folder/"research_replays.csv")
    extra=read(folder/"research_screening_samples.csv")
    assert len(summaries)==len(fp)==2 and len(replay)==len(extra)==32
    result={}
    for solver in SOLVERS:
        s=next(x for x in summaries if x["algorithm"]==solver)
        f=next(x for x in fp if x["algorithm"]==solver)
        vis=[x for x in visited if x["algorithm"]==solver]
        base=sorted([x for x in replay if x["algorithm"]==solver],
                    key=lambda x:int(x["candidate_index"]))
        additional=[x for x in extra if x["algorithm"]==solver]
        assert (s["workflow"],s["seed"])==(dag,str(seed))
        assert tuple(int(s[k]) for k in ("population","generations",
            "evaluations","captured_evaluations","replayed"))==(30,100,3030,3030,16)
        assert len(vis)==int(s["distinct_observed"])==int(f["distinct_visited"])
        assert [int(x["visited_index"]) for x in vis]==list(range(1,len(vis)+1))
        assert source_sha(vis)==f["history_sha256"],("history SHA mismatch",dag,seed,solver)
        planned={}
        for r in vis:
            k=canonical(r["canonical_mapping"])
            assert k not in planned
            planned[k]=(float(r["planned_makespan"]),float(r["planned_cost"]))
        def validate(x):
            k=canonical(x["mapping"])
            assert k in planned
            p=(float(x["planned_makespan"]),float(x["planned_cost"]))
            t=(float(x["sim_makespan"]),float(x["sim_cost"]))
            assert all(math.isfinite(v) and v>0 for v in p+t)
            assert all(abs(a-b)<=1e-9*max(1,abs(a),abs(b))
                       for a,b in zip(p,planned[k]))
            return k,t
        base_map=dict(validate(x) for x in base)
        assert len(base_map)==16
        sets={"near8":[],"uniform8":[]}
        for r in additional:
            k,t=validate(r)
            assert k not in base_map
            assert r["stratum"] in ("near-planned-front","uniform-remainder")
            subset="near8" if r["stratum"]=="near-planned-front" else "uniform8"
            assert k not in [k1 for k1,_ in sets[subset]]
            sets[subset].append((k,t))
            assert any(dominates(planned[b],planned[k]) for b in base_map),(
                "Not genuinely planned dominated",dag,seed,solver)
        assert len(sets["near8"])==len(sets["uniform8"])==8
        assert len(set(k for subset in sets.values() for k,_ in subset))==16
        result[solver]=dict(base=base_map,extra=sets,history=f["history_sha256"])
    return result

def evaluate(root,dax_root,out):
    out.mkdir(parents=True,exist_ok=True)
    result_rows=[]
    candidate_rows=[]
    for dag,seed in itertools.product(DAGS,SEEDS):
        runtimes,edges=parse_dax(dax_root/f"{dag}.xml")
        records=load_source(root,dag,seed)
        all_true=[p for x in records.values() for p in
                  list(x["base"].values())+
                  [t for subset in x["extra"].values() for _,t in subset]]
        refs={factor:tuple(factor*max(x[i] for x in all_true)+1e-6
                           for i in (0,1)) for factor in (1.5,3.)}
        for solver,d in records.items():
            baseline=list(d["base"].values())
            pool=dict(item for sub in d["extra"].values() for item in sub)
            assert len(pool)==16
            risks={key:exposure(key,runtimes,edges) for key in pool}
            # Fix all decisions BEFORE reading any simulator truth in pool:
            order=sorted(pool,key=lambda x:(-risks[x][2],x))
            structural=order[:8]
            assert len(structural)==8
            near=[x for x,_ in d["extra"]["near8"]]
            uniform=[x for x,_ in d["extra"]["uniform8"]]
            seedsalt=int(hashlib.sha256(
                f"v21-physical-sham|{dag}|{seed}|{solver}".encode("utf8")
                ).hexdigest()[:16],16)
            rng=random.Random(seedsalt)
            shams=[rng.sample(sorted(pool),8) for _ in range(32)]
            assert len(set(structural))==len(set(near))==len(set(uniform))==8
            h0=hv(baseline,refs[1.5])
            h03=hv(baseline,refs[3.])
            # Infeasible actual-label hindsight ceiling, restricted to selected pool.
            oracle=-1.
            for selection in itertools.combinations(sorted(pool),8):
                oracle=max(oracle,hv(baseline+[pool[x] for x in selection],refs[1.5])-h0)
            picks={"structural":structural,"near8":near,"uniform8":uniform}
            deltas={}
            for policy,selection in picks.items():
                vals=[pool[x] for x in selection]
                delta=hv(baseline+vals,refs[1.5])-h0
                delta3=hv(baseline+vals,refs[3.])-h03
                deltas[policy]=delta
                result_rows.append(dict(workflow=dag,seed=seed,solver=solver,
                    policy=policy,source_history_sha=d["history"],
                    original_k16_hv15=h0,real_hv_increment15=delta,
                    real_hv_increment30=delta3,
                    exact_k8_hindsight_oracle_increment15=oracle,
                    candidate_pool_size=16,simulator_replays_policy=8,
                    positive_individual_hv=sum(
                      hv(baseline+[pool[k]],refs[1.5])>h0+1e-10 for k in selection),
                    structural_minus_near15=0.,structural_minus_uniform15=0.,
                    random_sham32_mean15=0.,random_sham32_max15=0.))
            rand=[hv(baseline+[pool[k] for k in selected],refs[1.5])-h0
                  for selected in shams]
            for row in result_rows[-3:]:
                row["structural_minus_near15"]=deltas["structural"]-deltas["near8"]
                row["structural_minus_uniform15"]=deltas["structural"]-deltas["uniform8"]
                row["random_sham32_mean15"]=statistics.mean(rand)
                row["random_sham32_max15"]=max(rand)
            for k,t in pool.items():
                risk=risks[k]
                candidate_rows.append(dict(workflow=dag,seed=seed,solver=solver,
                    canonical_mapping=k,
                    source_stratum="near8" if k in near else "uniform8",
                    static_queue_pressure=risk[0],
                    weighted_dag_edge_cut=risk[1],
                    prefrozen_structural_risk=risk[2],
                    selected_top8=int(k in structural),
                    individual_true_hv_increment=hv(baseline+[t],refs[1.5])-h0))
    assert len(result_rows)==48 and len(candidate_rows)==256
    save(out/"all_48_structural_near_uniform_actual_hv.csv",result_rows)
    save(out/"all_256_original_candidates_structural_features.csv",candidate_rows)
    report=["# Fixed DAG edge-cut + VM-load risk K8: retrospective actual WorkflowSim ablation",
       "","This is post-hoc reuse of already observed source labels. NOT new prospective performance.",
       "All 8 source jobs, 16 source histories, source SHA, original strict planned-dominance",
       "and original StageInAware 3030 fitness visit budget were checked.",
       "Structural score 0.5*max-VM-runtime-fraction+0.5*weighted-DAG-edge-cut was locked",
       "before computing scores; no true label enters ranking.",
       "Pool is only original near8 UNION uniform8 source-selected candidates, not full visited history.",
       "One shared real 1.5x reference per DAG/seed across both original solvers.",
       "Comparators: each same extra K8 labels; 32 deterministic random K8 sham draws;",
       "exhaustive 12870-combination infeasible hindsight K8 oracle for headroom only.","",
       "| Workflow | Seed | Solver | structural ΔHV | near8 ΔHV | uniform8 ΔHV | structural−near | structural−uniform | oracle ΔHV |",
       "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for dag,seed,solver in itertools.product(DAGS,SEEDS,SOLVERS):
        chunk=[x for x in result_rows if (x["workflow"],x["seed"],x["solver"])==(dag,seed,solver)]
        vals={x["policy"]:x for x in chunk}
        report.append(f"| {dag} | {seed} | {solver} | "
            f"{vals['structural']['real_hv_increment15']:+.9f} | "
            f"{vals['near8']['real_hv_increment15']:+.9f} | "
            f"{vals['uniform8']['real_hv_increment15']:+.9f} | "
            f"{vals['structural']['structural_minus_near15']:+.9f} | "
            f"{vals['structural']['structural_minus_uniform15']:+.9f} | "
            f"{vals['structural']['exact_k8_hindsight_oracle_increment15']:+.9f} |")
    for solver in SOLVERS:
        rr=[x for x in result_rows if x["solver"]==solver and x["policy"]=="structural"]
        for column in ("structural_minus_near15","structural_minus_uniform15"):
            v=[r[column] for r in rr]
            report.append(f"- {solver} {column}: mean={statistics.mean(v):+.9f}; "
                f"W/T/L={sum(a>1e-10 for a in v)}/{sum(abs(a)<=1e-10 for a in v)}/"
                f"{sum(a< -1e-10 for a in v)}.")
    report+=["","Do not use these familiar source labels as a held-out training or test split.",
       "Even if structural risk beats controls here, it requires a new preregistered",
       "prospective sample design and untouched-family/size runs before claiming novelty",
       "or true scheduling improvement. High risk is NOT a calibrated uncertainty score."]
    (out/"structural_risk_offline_findings.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    assert len(sys.argv)==4,"Usage: script.py ORIGINAL_ARTIFACTS DAX_FOLDER REPORTS"
    evaluate(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),pathlib.Path(sys.argv[3]))
