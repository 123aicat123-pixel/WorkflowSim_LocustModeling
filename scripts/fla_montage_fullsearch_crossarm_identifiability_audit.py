#!/usr/bin/env python3
"""Retrospective OLD/READY matched physical K8 union audit; no new simulator truth.

Inputs are original immutable artifacts from the previously observed run 42190857445.
The exact union K8 hindsight ceiling is diagnostic and never a viable selector.
"""
import csv
import itertools
import math
import pathlib
import sys

from fla_independent32_k4_identifiability_audit import hv, dominates
from fla_montage_fullsearch_ready_transfer_audit import (
    DAGS, SPEEDS, SEEDS, DECODERS, ALGS, EXPECTED, read, write
)

ORIGINAL_SHA="a3e4292b6cfdcb20698d7ea9bbe6829d122cde5a"
TOL=1e-8
# Prior independently computed result. Cross-check to prevent historical-data drift.
HISTORIC_FLA={
 ("Montage_50","default","1601"):0.005062565,
 ("Montage_50","default","1602"):-0.000099887,
 ("Montage_50","staggered","1601"):0.005720621,
 ("Montage_50","staggered","1602"):0.006647873,
 ("Montage_100","default","1601"):0.022925165,
 ("Montage_100","default","1602"):0.011432001,
 ("Montage_100","staggered","1601"):-0.033404446,
 ("Montage_100","staggered","1602"):-0.003001961,
}
HISTORIC_NSGA={
 ("Montage_50","default","1601"):-0.004003679,
 ("Montage_50","default","1602"):0.000890506,
 ("Montage_50","staggered","1601"):-0.004232270,
 ("Montage_50","staggered","1602"):0.018437168,
 ("Montage_100","default","1601"):-0.003859932,
 ("Montage_100","default","1602"):0.002302186,
 ("Montage_100","staggered","1601"):0.004127474,
 ("Montage_100","staggered","1602"):0.005359731,
}

def near(a,b):
    return math.isclose(a,b,rel_tol=TOL,abs_tol=TOL)

def audit(root,out,protocol_sha):
    out.mkdir(parents=True,exist_ok=True)
    files=sorted(root.glob("fullsearch-*/research_replays.csv"))
    assert len(files)==16,("Original artifact shortfall",len(files))
    blocks={}
    source_rows=0
    seen=set()
    for path in files:
        folder=path.parent
        meta={}
        for line in (folder/"block-id.txt").read_text().splitlines():
            k,v=line.split("=",1)
            assert k not in meta
            meta[k]=v
        key=(meta["workflow"],meta["vm_speed"],meta["seed"],meta["decoder"])
        assert key in EXPECTED and key not in seen,key
        seen.add(key)
        assert folder.name==f"fullsearch-{key[0]}-{key[1]}-s{key[2]}-{key[3]}"
        assert meta["vm_price"]=="default" and meta["replay_k"]=="8"
        assert (folder/"source-sha.txt").read_text().strip()==ORIGINAL_SHA
        assert (folder/"protocol-sha.txt").read_text().strip()==protocol_sha
        log=(folder/"experiment.log").read_text(errors="replace")
        assert "RESULT" in log and "REPLAY" in log
        summary=read(folder/"research_summary.csv")
        replays=read(path)
        assert len(summary)==2 and {s["algorithm"] for s in summary}==set(ALGS)
        assert len(replays)==16
        by_solver={}
        for s in summary:
            alg=s["algorithm"]
            assert (s["workflow"],s["seed"])==(key[0],key[2])
            assert tuple(int(s[c]) for c in
              ("population","generations","evaluations","captured_evaluations","replayed")
              )==(30,100,3030,3030,8),(key,alg,s)
            selected=[r for r in replays if r["algorithm"]==alg]
            assert len(selected)==8
            assert len({r["mapping"] for r in selected})==8
            assert {int(r["candidate_index"]) for r in selected}==set(range(1,9))
            for r in selected:
                assert (r["workflow"],r["seed"])==(key[0],key[2])
                mappings={}
                for part in r["mapping"].split("|"):
                    tid,vm=map(int,part.split(":"))
                    assert tid not in mappings
                    mappings[tid]=vm
                assert set(mappings)==set(range(1,int(key[0].split("_")[1])+1))
                assert all(0<=v<16 for v in mappings.values())
                for c in ("sim_makespan","sim_cost","planned_makespan","planned_cost"):
                    assert math.isfinite(float(r[c])) and float(r[c])>0
            by_solver[alg]=selected
            source_rows+=len(selected)
        blocks[key]=by_solver
    assert seen==EXPECTED and source_rows==256

    details=[]
    for dag,speed,seed in itertools.product(DAGS,SPEEDS,SEEDS):
        case=(dag,speed,seed)
        arms={(alg,decoder):blocks[dag,speed,seed,decoder][alg]
              for alg in ALGS for decoder in DECODERS}
        actual_by_mapping={}
        all_actual=[]
        for rows in arms.values():
            for r in rows:
                mapping=r["mapping"]
                point=(float(r["sim_makespan"]),float(r["sim_cost"]))
                if mapping in actual_by_mapping:
                    older=actual_by_mapping[mapping]
                    assert all(near(a,b) for a,b in zip(older,point)),(
                         "Identical physical genotype gives different real truth",case,older,point)
                else:
                    actual_by_mapping[mapping]=point
                all_actual.append(point)
        assert len(all_actual)==32
        shared_reference=tuple(1.5*max(p[i] for p in all_actual)+1e-6 for i in range(2))
        by_solver_results={}
        for alg in ALGS:
            old=arms[alg,"old"]
            ready=arms[alg,"ready"]
            old_maps=set(r["mapping"] for r in old)
            ready_maps=set(r["mapping"] for r in ready)
            assert len(old_maps)==len(ready_maps)==8
            common=old_maps & ready_maps
            union=old_maps | ready_maps
            assert 8<=len(union)<=16
            union_actual=[actual_by_mapping[x] for x in sorted(union)]
            oracle=-1.
            optimal_sets=0
            for subset in itertools.combinations(union_actual,8):
                score=hv(subset,shared_reference)
                if score>oracle+TOL:
                    oracle=score
                    optimal_sets=1
                elif abs(score-oracle)<=TOL:
                    optimal_sets+=1
            old_hv=hv([actual_by_mapping[x] for x in old_maps],shared_reference)
            ready_hv=hv([actual_by_mapping[x] for x in ready_maps],shared_reference)
            assert oracle>=max(old_hv,ready_hv)-TOL
            nd=sum(not any(dominates(q,p) for q in union_actual if q!=p)
                   for p in union_actual)
            def errors(rows):
                return (
                  sum(abs(float(x["planned_makespan"])-float(x["sim_makespan"]))/
                      float(x["sim_makespan"]) for x in rows)/8,
                  sum(abs(float(x["planned_cost"])-float(x["sim_cost"]))/
                      float(x["sim_cost"]) for x in rows)/8
                )
            old_err=errors(old)
            ready_err=errors(ready)
            r=dict(workflow=dag,vm_speed=speed,seed=seed,
                solver=alg,old_count=8,ready_count=8,
                physical_intersection=len(common),physical_union=len(union),
                physical_jaccard=len(common)/len(union),
                union_actual_nd_count=nd,
                exact_union_oracle_k8_hv=oracle,
                exact_optimal_k8_sets=optimal_sets,
                complete_union_hv=hv(union_actual,shared_reference),
                old_actual_k8_hv=old_hv,ready_actual_k8_hv=ready_hv,
                ready_minus_old_actual_k8_hv=ready_hv-old_hv,
                old_regret_vs_union_oracle=max(0.,oracle-old_hv),
                ready_regret_vs_union_oracle=max(0.,oracle-ready_hv),
                old_chosen_makespan_mape=old_err[0],
                ready_chosen_makespan_mape=ready_err[0],
                old_chosen_cost_mape=old_err[1],
                ready_chosen_cost_mape=ready_err[1],
                source_sha=ORIGINAL_SHA)
            by_solver_results[alg]=r
            details.append(r)
        assert near(by_solver_results[ALGS[0]]["ready_minus_old_actual_k8_hv"],
                    HISTORIC_FLA[case]),("FLA prior HV changed",case)
        assert near(by_solver_results[ALGS[1]]["ready_minus_old_actual_k8_hv"],
                    HISTORIC_NSGA[case]),("NSGA prior HV changed",case)
    assert len(details)==16
    write(out/"crossarm_union_k8_retrospective_all16.csv",details)
    report=["# Retrospective OLD/READY full-search K8 overlap and exact selected-union oracle",
       "", "**Read-only reused original WorkflowSim truth. NOT a new independent trial.**",
       f"All 16 original source archives at SHA \`{ORIGINAL_SHA}\` verified; "
       "32 arms × K8 = 256 genuine historical replay rows,",
       "eight DAG/speed/seed blocks. Original shared-reference actual ΔHV values",
       "reconstructed and checked against the archived prior independent report.",
       "",
       "| DAG | Speed | Seed | Solver | Same maps / 8 | Union ND | OLD union regret | READY union regret | READY−OLD actual HV |",
       "|---|---|---:|---|---:|---:|---:|---:|---:|"]
    for r in details:
        report.append(f"| {r['workflow']} | {r['vm_speed']} | {r['seed']} | "
                      f"{'FLA' if r['solver']==ALGS[0] else 'NSGA'} | "
                      f"{r['physical_intersection']} | {r['union_actual_nd_count']} | "
                      f"{r['old_regret_vs_union_oracle']:.9f} | "
                      f"{r['ready_regret_vs_union_oracle']:.9f} | "
                      f"{r['ready_minus_old_actual_k8_hv']:+.9f} |")
    worst=next(r for r in details if r["solver"]==ALGS[0] and
               (r["workflow"],r["vm_speed"],r["seed"])==
               ("Montage_100","staggered","1601"))
    report+=["", "**Adverse-block FLA diagnostic:**",
        f"- Identical physical K8 mappings: **{worst['physical_intersection']}/8**.",
        f"- Selected-union size: **{worst['physical_union']}**, actual ND maps: "
        f"**{worst['union_actual_nd_count']}**.",
        f"- Exact selected-union K8 hindsight oracle HV: **{worst['exact_union_oracle_k8_hv']:.9f}**.",
        f"- OLD union-oracle regret: **{worst['old_regret_vs_union_oracle']:.9f}**; "
        f"READY: **{worst['ready_regret_vs_union_oracle']:.9f}**.",
        f"- OLD vs READY selected-set makespan MAPE: "
        f"**{100*worst['old_chosen_makespan_mape']:.4f}% vs "
        f"{100*worst['ready_chosen_makespan_mape']:.4f}%** "
        "(not the same genotypes if selected sets differ).",
        "",
        "This UNION is only the at-most-16 **simulated selected** genotypes,",
        "not the complete 3030-visit candidate history and not a true scheduling optimum.",
        "Retrospective selection-headroom and overlap cannot separate",
        "search trajectory effects from final K8 replay-selection effects.",
        "No model promotion, no algorithm improvement claim, no p-values."]
    (out/"crossarm_identifiability_findings.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    assert len(sys.argv)==4, "Usage: script.py ORIGINAL_SOURCE_ARTIFACT_ROOT OUT ORIGINAL_PROTOCOL_BLOB_SHA"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3])
