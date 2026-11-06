#!/usr/bin/env python3
"""Blind independent cross-mode actual-HV reconstruction from real full FLA searches.
No true WorkflowSim label is available to either optimizer before its K8 choice.
"""
import csv
import itertools
import math
import pathlib
import sys
from fla_independent32_k4_identifiability_audit import hv

DAGS=("Montage_50","Montage_100")
SPEEDS=("default","staggered")
SEEDS=("1601","1602")
DECODERS=("old","ready")
ALGS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
EXPECTED=set(itertools.product(DAGS,SPEEDS,SEEDS,DECODERS))
TOL=1e-10

def read(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write(path, rows):
    assert rows
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def audit(root,out,sha,protocol):
    out.mkdir(parents=True,exist_ok=True)
    paths=sorted(root.glob("fullsearch-*/research_replays.csv"))
    assert len(paths)==16,("expected sixteen REAL original-source jobs",len(paths))
    by_block={}
    source_summaries=[]
    source_replays=[]
    seen=set()
    for path in paths:
        folder=path.parent
        fields={}
        for line in (folder/"block-id.txt").read_text(encoding="utf-8").splitlines():
            key,val=line.split("=",1)
            assert key not in fields,(folder,key)
            fields[key]=val
        key=(fields["workflow"],fields["vm_speed"],fields["seed"],fields["decoder"])
        assert key in EXPECTED and key not in seen,key
        seen.add(key)
        assert folder.name==f"fullsearch-{key[0]}-{key[1]}-s{key[2]}-{key[3]}"
        assert fields["vm_price"]=="default" and fields["replay_k"]=="8"
        assert (folder/"source-sha.txt").read_text().strip()==sha
        assert (folder/"protocol-sha.txt").read_text().strip()==protocol
        log=(folder/"experiment.log").read_text(errors="replace")
        assert "RESULT" in log and "REPLAY" in log and len(log)>100
        summary=read(folder/"research_summary.csv")
        replays=read(path)
        assert len(summary)==2 and {r["algorithm"] for r in summary}==set(ALGS)
        assert len(replays)==16
        assert {r["algorithm"] for r in replays}==set(ALGS)
        by_alg={}
        for r in summary:
            name=r["algorithm"]
            assert r["workflow"]==key[0] and r["seed"]==key[2]
            assert (int(r["population"]),int(r["generations"]),
                    int(r["evaluations"]),int(r["captured_evaluations"]),
                    int(r["replayed"]))==(30,100,3030,3030,8),(key,r)
            assert 0<int(r["distinct_observed"])<=3030
            assert math.isfinite(float(r["search_ms"])) and float(r["search_ms"])>0
            selected=[x for x in replays if x["algorithm"]==name]
            assert len(selected)==8
            assert {int(x["candidate_index"]) for x in selected}==set(range(1,9))
            assert all(x["workflow"]==key[0] and x["seed"]==key[2] for x in selected)
            assert len({x["mapping"] for x in selected})==8
            for x in selected:
                mapping={}
                for entry in x["mapping"].split("|"):
                    tid,vm=map(int,entry.split(":"))
                    assert tid not in mapping
                    mapping[tid]=vm
                assert len(mapping)==int(key[0].split("_")[1])
                assert set(mapping)==set(range(1,len(mapping)+1))
                assert all(0<=v<16 for v in mapping.values())
                for z in ("sim_makespan","sim_cost",
                          "planned_makespan","planned_cost",
                          "independent_planned_makespan","independent_planned_cost"):
                    v=float(x[z])
                    assert math.isfinite(v) and v>0,(key,name,z,v)
                source_replays.append(dict(workflow=key[0],vm_speed=key[1],seed=key[2],
                                           decoder=key[3],algorithm=name,
                                           index=x["candidate_index"],mapping=x["mapping"],
                                           actual_makespan=x["sim_makespan"],
                                           actual_cost=x["sim_cost"],
                                           planned_makespan=x["planned_makespan"],
                                           planned_cost=x["planned_cost"]))
            by_alg[name]=selected
            source_summaries.append(dict(workflow=key[0],vm_speed=key[1],seed=key[2],
                                         decoder=key[3],algorithm=name,
                                         search_ms=r["search_ms"],evaluations=r["evaluations"],
                                         distinct_observed=r["distinct_observed"]))
        by_block[key]=by_alg
    assert seen==EXPECTED and len(source_replays)==256 and len(source_summaries)==32
    write(out/"all_256_real_search_replays_provenance.csv",source_replays)
    write(out/"all_32_source_search_budgets.csv",source_summaries)
    rows=[]
    for dag,speed,seed in itertools.product(DAGS,SPEEDS,SEEDS):
        arms={}
        for decoder in DECODERS:
            key=(dag,speed,seed,decoder)
            for alg in ALGS:
                arms[alg,decoder]=by_block[key][alg]
        all_points=[(float(x["sim_makespan"]),float(x["sim_cost"]))
                    for values in arms.values() for x in values]
        assert len(all_points)==32
        record=dict(workflow=dag,vm_speed=speed,seed=seed,
                    source_sha=sha,actual_replay_count=32)
        for factor,tag in ((1.5,"15"),(3.0,"30")):
            ref=tuple(factor*max(p[i] for p in all_points)+1e-6 for i in (0,1))
            scores={}
            for alg in ALGS:
                for decoder in DECODERS:
                    points=[(float(x["sim_makespan"]),float(x["sim_cost"]))
                            for x in arms[alg,decoder]]
                    scores[alg,decoder]=hv(points,ref)
            fla_old=scores[ALGS[0],"old"]
            fla_ready=scores[ALGS[0],"ready"]
            nsga_old=scores[ALGS[1],"old"]
            nsga_ready=scores[ALGS[1],"ready"]
            record.update({f"ref_m_{tag}":ref[0],f"ref_cost_{tag}":ref[1],
                 f"fla_old_hv_{tag}":fla_old,f"fla_ready_hv_{tag}":fla_ready,
                 f"nsga_old_hv_{tag}":nsga_old,f"nsga_ready_hv_{tag}":nsga_ready,
                 f"fla_ready_minus_old_{tag}":fla_ready-fla_old,
                 f"nsga_ready_minus_old_{tag}":nsga_ready-nsga_old,
                 f"fla_minus_nsga_old_{tag}":fla_old-nsga_old,
                 f"fla_minus_nsga_ready_{tag}":fla_ready-nsga_ready,
                 f"decoder_solver_interaction_{tag}":
                     (fla_ready-fla_old)-(nsga_ready-nsga_old)})
        for alg,short in ((ALGS[0],"fla"),(ALGS[1],"nsga")):
            for decoder in DECODERS:
                s=next(r for r in source_summaries if (r["workflow"],r["vm_speed"],r["seed"],
                     r["decoder"],r["algorithm"])==(dag,speed,seed,decoder,alg))
                record[f"{short}_{decoder}_search_ms"]=float(s["search_ms"])
        rows.append(record)
    assert len(rows)==8
    write(out/"all_8_paired_fullsearch_true_hv.csv",rows)
    report=[
        "# Prospective full-search OLD/READY Montage heterogeneity: actual WorkflowSim audit",
        "",
        "**Original full evolutionary search (NOT population-1 fixed-mapping selection).**",
        "16/16 original jobs, 32/32 full 3030-visit search arms, 256 actual FIFO",
        "WorkflowSim K8 replays. Joint reference across all 4 arms of every",
        "exact DAG/speed/seed block. Earlier Montage selection discovery means",
        "this is hypothesis-driven development, NOT independent family holdout.",
        "",
        "| DAG | VM speed | Search seed | FLA READY−OLD actual HV | NSGA READY−OLD actual HV | Interaction |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        report.append(f"| {r['workflow']} | {r['vm_speed']} | {r['seed']} | "
              f"{r['fla_ready_minus_old_15']:+.9f} | "
              f"{r['nsga_ready_minus_old_15']:+.9f} | "
              f"{r['decoder_solver_interaction_15']:+.9f} |")
    report+=["","| Comparison | Wins / 8 | Ties / 8 | Losses / 8 | Mean paired true HV difference |",
             "|---|---:|---:|---:|---:|"]
    for field,name in (
        ("fla_ready_minus_old_15","FLA READY − OLD"),
        ("nsga_ready_minus_old_15","NSGA READY − OLD"),
        ("fla_minus_nsga_old_15","FLA − NSGA with OLD"),
        ("fla_minus_nsga_ready_15","FLA − NSGA with READY"),
        ("decoder_solver_interaction_15","Decoder×solver interaction"),
    ):
        diffs=[r[field] for r in rows]
        report.append(f"| {name} | {sum(v>TOL for v in diffs)} | "
                     f"{sum(abs(v)<=TOL for v in diffs)} | "
                     f"{sum(v< -TOL for v in diffs)} | {sum(diffs)/len(diffs):+.9f} |")
    for key in ("fla","nsga"):
        for mode in DECODERS:
            times=[r[f"{key}_{mode}_search_ms"] for r in rows]
            report.append(f"- Mean {key.upper()} {mode} source search wall ms: "
                          f"{sum(times)/len(times):.1f}; actual runner variation and "
                          "forecast model compute costs are not equalized.")
    report+=["",
       "True HV from K8 forecast-selected real replays, NOT all visited genotype truth.",
       "If both solvers benefit, this supports a shared decoder mechanism, not unique FLA.",
       "All negative, zero and positive cases are retained; no p-values or SCI superiority.",
       "The original 32-map fixed selection result may fail to transfer to full search."]
    (out/"fullsearch_actual_findings.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    assert len(sys.argv)==5,"Usage: audit.py SOURCE_DIR REPORT_DIR SOURCE_SHA PROTOCOL_BLOB_SHA"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3],sys.argv[4])
