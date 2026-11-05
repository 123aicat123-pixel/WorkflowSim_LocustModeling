#!/usr/bin/env python3
"""Source-only frozen v21 dominated near8 vs uniform8 true WorkflowSim audit.

No additional optimizer, planned evaluator or simulator execution. These are extra
8 simulator calls in each stratum, NOT budget-parity K16 algorithms.
"""
import collections
import csv
import hashlib
import itertools
import math
import pathlib
import statistics
import struct
import sys

RUN="41990207133"
DAGS=("Montage_50","Sipht_60","Epigenomics_46","CyberShake_30")
SEEDS=(991,992)
SOLVERS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")

def read(p):
    with p.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def save(p,rs):
    assert rs
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]))
        w.writeheader()
        w.writerows(rs)

def mapping(s):
    return "|".join(sorted(s.split("|"),key=lambda a:int(a.split(":")[0])))

def dominates(a,b):
    return a[0]<=b[0] and a[1]<=b[1] and (a[0]<b[0] or a[1]<b[1])

def nd(ps):
    result=[]
    best=float("inf")
    for p in sorted(set(ps)):
        if p[1]<best:
            result.append(p);best=p[1]
    return result

def hv(ps,ref):
    upper=ref[1]
    area=0.
    for m,c in nd(ps):
        if m<ref[0] and c<upper:
            area+=(ref[0]-m)*(upper-c)
            upper=c
    result=area/(ref[0]*ref[1])
    assert math.isfinite(result) and 0<=result<=1+1e-10
    return result

def source_sha(rows):
    dig=hashlib.sha256()
    for r in rows:
        def bits(value):
            return format(struct.unpack(">Q",struct.pack(">d",float(value)))[0],"x")
        line=(r["canonical_mapping"]+"|"+bits(r["planned_makespan"])+
              "|"+bits(r["planned_cost"])+"\n")
        dig.update(line.encode("utf-8"))
    return dig.hexdigest()

def data(root,dag,seed):
    folder=root/f"fla-v21-dominated-{dag}-s{seed}-{RUN}"
    assert folder.is_dir(),("Missing source",folder)
    sha=(folder/"source-sha.txt").read_text().strip()
    assert len(sha)==40
    summary=read(folder/"research_summary.csv")
    fingerprint=read(folder/"research_visited_fingerprints.csv")
    visited=read(folder/"research_full_visited_objectives.csv")
    original=read(folder/"research_replays.csv")
    extra=read(folder/"research_screening_samples.csv")
    detail=read(folder/"research_screening_summary.csv")
    assert len(summary)==len(fingerprint)==len(detail)==2
    assert len(original)==len(extra)==32
    assert {r["algorithm"] for r in summary}=={r["algorithm"] for r in fingerprint}==set(SOLVERS)
    result={}
    for solver in SOLVERS:
        s=next(x for x in summary if x["algorithm"]==solver)
        f=next(x for x in fingerprint if x["algorithm"]==solver)
        d=next(x for x in detail if x["algorithm"]==solver)
        visits=[v for v in visited if v["algorithm"]==solver]
        base=sorted((r for r in original if r["algorithm"]==solver),
                    key=lambda r:int(r["candidate_index"]))
        add=[r for r in extra if r["algorithm"]==solver]
        assert s["workflow"]==dag and s["seed"]==str(seed)
        assert tuple(int(s[z]) for z in ("population","generations","evaluations","captured_evaluations","replayed"))==(30,100,3030,3030,16)
        assert [int(r["candidate_index"]) for r in base]==list(range(1,17))
        assert len(visits)==int(s["distinct_observed"])==int(f["distinct_visited"])
        assert source_sha(visits)==f["history_sha256"],("Original historical SHA mismatch",dag,seed,solver)
        assert collections.Counter(r["stratum"] for r in add)=={
            "near-planned-front":8,"uniform-remainder":8}
        assert int(d["strict_planned_dominated"])>=16
        history={}
        for r in visits:
            key=r["canonical_mapping"]
            assert key not in history
            history[key]=(float(r["planned_makespan"]),float(r["planned_cost"]))
        samples={}
        for row in base:
            key=mapping(row["mapping"])
            assert key in history
            samples[key]=row
        strata={"near-planned-front":[],"uniform-remainder":[]}
        for row in add:
            key=mapping(row["mapping"])
            assert key in history and key not in samples
            samples[key]=row
            strata[row["stratum"]].append(row)
        assert len(samples)==32
        for row in base+add:
            key=mapping(row["mapping"])
            p=(float(row["planned_makespan"]),float(row["planned_cost"]))
            a=(float(row["sim_makespan"]),float(row["sim_cost"]))
            assert all(math.isfinite(x) and x>0 for x in p+a)
            assert all(abs(x-y)<=1e-9*max(1,abs(x),abs(y)) for x,y in zip(p,history[key]))
        baseline_planned=[(float(r["planned_makespan"]),float(r["planned_cost"])) for r in base]
        baseline_actual=[(float(r["sim_makespan"]),float(r["sim_cost"])) for r in base]
        for row in add:
            proposed=(float(row["planned_makespan"]),float(row["planned_cost"]))
            assert any(dominates(p,proposed) for p in baseline_planned),(
                "Extra was not strictly planning-dominated by the K16 baseline",dag,seed,solver)
        result[solver]=dict(original=base,strata=strata,sha=sha,history=f["history_sha256"])
    return result

def audit(root,out):
    out.mkdir(parents=True,exist_ok=True)
    sample_rows=[]
    case_rows=[]
    all_source_shas=set()
    for dag,seed in itertools.product(DAGS,SEEDS):
        cases=data(root,dag,seed)
        pooled=[(float(x["sim_makespan"]),float(x["sim_cost"]))
                for d in cases.values()
                for x in d["original"]+sum(d["strata"].values(),[])]
        refs={f:tuple(f*max(p[i] for p in pooled)+1e-6 for i in (0,1))
              for f in (1.5,3.0)}
        for solver,d in cases.items():
            all_source_shas.add(d["sha"])
            baseline=d["original"]
            bp=[(float(x["planned_makespan"]),float(x["planned_cost"])) for x in baseline]
            bt=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in baseline]
            h0=hv(bt,refs[1.5])
            for label,rows in d["strata"].items():
                sample_points=[]
                false_count=0
                true_survivors=0
                hv_contributors=0
                for x in rows:
                    m=(float(x["planned_makespan"]),float(x["planned_cost"]))
                    t=(float(x["sim_makespan"]),float(x["sim_cost"]))
                    planned_dominators=[i for i,p in enumerate(bp) if dominates(p,m)]
                    assert planned_dominators
                    false_all=all(not dominates(bt[i],t) for i in planned_dominators)
                    actually_nd=all(not dominates(p,t) and p!=t for p in bt)
                    gain=hv(bt+[t],refs[1.5])-h0
                    false_count+=int(false_all)
                    true_survivors+=int(actually_nd)
                    hv_contributors+=int(gain>1e-10)
                    sample_points.append(t)
                    sample_rows.append(dict(workflow=dag,seed=seed,solver=solver,
                        stratum=label,mapping=mapping(x["mapping"]),
                        planned_dominators=len(planned_dominators),
                        all_planned_dominators_false=int(false_all),
                        true_nondominated_vs_k16=int(actually_nd),
                        individual_delta_hv15=gain))
                h=hv(bt+sample_points,refs[1.5])
                h30=hv(bt+sample_points,refs[3.0])
                case_rows.append(dict(workflow=dag,seed=seed,solver=solver,
                    stratum=label,source_sha=d["sha"],history_sha=d["history"],
                    original_k16_hv15=h0,
                    eight_additional_hv15=h,
                    incremental_true_hv15=h-h0,
                    incremental_true_hv30=h30-hv(bt,refs[3.0]),
                    false_exclusion_count=false_count,
                    true_k16_nondominated_count=true_survivors,
                    individually_positive_hv_count=hv_contributors,
                    real_replay_budget_base=16,extra_replay_budget=8))
    assert len(sample_rows)==256 and len(case_rows)==32
    assert len(all_source_shas)==1,("Mixed source code revisions",all_source_shas)
    save(out/"all_256_dominated_true_candidate_outcomes.csv",sample_rows)
    save(out/"all_32_near_uniform_extra8_audits.csv",case_rows)
    paired=[]
    for dag,seed,solver in itertools.product(DAGS,SEEDS,SOLVERS):
        n=next(x for x in case_rows if (x["workflow"],x["seed"],x["solver"],x["stratum"] )==(dag,seed,solver,"near-planned-front"))
        u=next(x for x in case_rows if (x["workflow"],x["seed"],x["solver"],x["stratum"] )==(dag,seed,solver,"uniform-remainder"))
        paired.append(dict(workflow=dag,seed=seed,solver=solver,
            near_delta_hv15=n["incremental_true_hv15"],uniform_delta_hv15=u["incremental_true_hv15"],
            near_minus_uniform_delta_hv15=n["incremental_true_hv15"]-u["incremental_true_hv15"],
            near_false_exclusions=n["false_exclusion_count"],
            uniform_false_exclusions=u["false_exclusion_count"],
            near_true_nd=n["true_k16_nondominated_count"],uniform_true_nd=u["true_k16_nondominated_count"],
            near_positive_hv=n["individually_positive_hv_count"],
            uniform_positive_hv=u["individually_positive_hv_count"]))
    save(out/"all_16_solver_block_paired_deltas.csv",paired)
    report=["# Frozen prospective dominated near8 vs uniform8 actual WorkflowSim audit","",
      "8 workflow-seed blocks; 2 unchanged source optimizers; 3030 original counted planning fitness visits each.",
      "512 true simulator replay records: 256 original K16 + 128 near8 + 128 uniform8.",
      "16 original histories validated bytewise against export SHA256, single identical source SHA across eight jobs.",
      "Near and uniform are extra-budget source-only diagnostics, not matched total K16 scheduling algorithms.","",
      "| DAG | seed | Solver | Near8 true ΔHV | Uniform8 true ΔHV | Near−uniform | Near/Uniform false exclusions |",
      "|---|---:|---|---:|---:|---:|---:|"]
    for r in paired:
        report.append(f"| {r['workflow']} | {r['seed']} | {r['solver']} | "
                      f"{r['near_delta_hv15']:+.9f} | {r['uniform_delta_hv15']:+.9f} | "
                      f"{r['near_minus_uniform_delta_hv15']:+.9f} | "
                      f"{r['near_false_exclusions']}/{r['uniform_false_exclusions']} |")
    for solver in SOLVERS:
        rr=[p for p in paired if p["solver"]==solver]
        differences=[p["near_minus_uniform_delta_hv15"] for p in rr]
        report.append(f"- {solver}: near−uniform mean={statistics.mean(differences):+.9f}, "
                      f"wins/ties/losses {sum(x>1e-10 for x in differences)}/"
                      f"{sum(abs(x)<=1e-10 for x in differences)}/"
                      f"{sum(x< -1e-10 for x in differences)}.")
    report+=["","This is a description of newly sampled but familiar DAG families and seeds.",
      "All candidates are genuinely PLANNED-dominated; true labels are never used to select.",
      "Observed near-vs-uniform sample contrasts are exploratory and not causal policy superiority.",
      "Individual candidates and pair relationships are correlated; do not treat them as independent seeds.",
      "All wins, null results and losses are retained. No SCI FLA improvement claim."]
    (out/"v21_dominated_true_fidelity_findings.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))
if __name__=="__main__":
    assert len(sys.argv)==3
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
