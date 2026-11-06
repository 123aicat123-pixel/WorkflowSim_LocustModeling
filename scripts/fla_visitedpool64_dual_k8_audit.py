#!/usr/bin/env python3
"""Strict original-WorkflowSim 64 visited mappings / dual predictor blind K2,4,8.

Outcome-free selection is reconstructed only from physically frozen predictions;
all original simulation labels are scored later with a common actual reference.
"""
import csv
import itertools
import math
import pathlib
import random
import statistics
import sys
from fla_independent32_k4_identifiability_audit import hv,planned_greedy
from fla_samepool32_k8_random_sham_audit import exact_hv_dp,test_oracle,nd_points
from fla_montage_fullsearch_ready_transfer_audit import write

DAGS=("Montage_50","Montage_100")
SPEEDS=("default","staggered")
SEEDS=("1701","1702")
KS=(2,4,8)
TOL=1e-9
BLOCKS=set(itertools.product(DAGS,SPEEDS,SEEDS))

def read(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def case_dir(folder):
    lines=(folder/"block-id.txt").read_text().splitlines()
    x={}
    for line in lines:
        key,val=line.split("=",1)
        assert key not in x
        x[key]=val
    return (x["workflow"],x["speed"],x["seed"])

def audit(root,out,source_sha,protocol_sha,source_kind="OLD"):
    assert source_kind in ("OLD","READY")
    test_oracle()
    out.mkdir(parents=True,exist_ok=True)
    sources=sorted(root.glob("visitedpool64-*/research_pool64_frozen_predictions.csv"))
    assert len(sources)==8,("Missing original eight full FLA search pool jobs",sources)
    cases={}
    all_rows=[]
    for source in sources:
        folder=source.parent
        key=case_dir(folder)
        assert key in BLOCKS and key not in cases
        assert folder.name==f"visitedpool64-{key[0]}-{key[1]}-s{key[2]}"
        assert (folder/"source-sha.txt").read_text().strip()==source_sha
        assert (folder/"protocol-sha.txt").read_text().strip()==protocol_sha
        log=(folder/"experiment.log").read_text(errors="replace")
        assert log.count("FROZEN_BEFORE_TRUTH")==1
        assert log.count("ORIGINAL_TRUE_POOL64_PASS")==64
        assert "PASS OLD FLA 3030 real visits" in log
        budgets={}
        for line in (folder/"research_pool64_budget.txt").read_text().splitlines():
            a,b=line.split("=",1)
            assert a not in budgets
            budgets[a]=b
        assert (budgets["workflow"],budgets["seed"])==(key[0],key[2])
        assert (budgets["search_evaluations"],budgets["pool_size"],
                budgets["old_forecasts"],budgets["ready_forecasts"])==("3030","64","64","64")
        assert int(budgets["distinct_visited"])>=64
        preds=read(source)
        truth=read(folder/"research_pool64_true_replays.csv")
        assert len(preds)==len(truth)==64
        assert [int(x["pool_index"]) for x in preds]==list(range(1,65))
        assert [int(x["pool_index"]) for x in truth]==list(range(1,65))
        assert len({x["mapping"] for x in preds})==64
        count=int(key[0].rsplit("_",1)[1])
        for p,t in zip(preds,truth):
            assert (p["workflow"],p["seed"])==(key[0],key[2])
            assert (t["workflow"],t["seed"])==(key[0],key[2])
            assert (p["pool_index"],p["mapping"])==(t["pool_index"],t["mapping"])
            mapping={}
            for token in p["mapping"].split("|"):
                a,b=map(int,token.split(":"))
                assert a not in mapping
                mapping[a]=b
            assert set(mapping)==set(range(1,count+1))
            assert all(0<=v<16 for v in mapping.values())
            for k in ("old_planned_makespan","old_planned_cost",
                      "ready_planned_makespan","ready_planned_cost"):
                val=float(p[k])
                assert math.isfinite(val) and val>0
            for k in ("actual_makespan","actual_cost"):
                val=float(t[k])
                assert math.isfinite(val) and val>0
            all_rows.append(dict(workflow=key[0],speed=key[1],seed=key[2],
                       mapping=p["mapping"],source_index=p["pool_index"],
                       old_m=float(p["old_planned_makespan"]),
                       old_c=float(p["old_planned_cost"]),
                       ready_m=float(p["ready_planned_makespan"]),
                       ready_c=float(p["ready_planned_cost"]),
                       true_m=float(t["actual_makespan"]),true_c=float(t["actual_cost"])))
        cases[key]=(preds,truth)
    assert set(cases)==BLOCKS and len(all_rows)==512
    write(out/"all_512_true_replays_and_same_mapping_forecasts.csv",all_rows)
    comparisons=[]
    selections=[]
    shams=[]
    for block_idx,key in enumerate(sorted(BLOCKS)):
        preds,truth=cases[key]
        by_mapping={p["mapping"]:(p,t) for p,t in zip(preds,truth)}
        names=sorted(by_mapping)
        points={n:(float(by_mapping[n][1]["actual_makespan"]),
                   float(by_mapping[n][1]["actual_cost"])) for n in names}
        ref=tuple(1.5*max(x[j] for x in points.values())+1e-6 for j in (0,1))
        full_hv=hv(list(points.values()),ref)
        nd=len(nd_points(list(points.values())))
        order={}
        for model in ("old","ready"):
            preds2=[(float(by_mapping[n][0][f"{model}_planned_makespan"]),
                     float(by_mapping[n][0][f"{model}_planned_cost"])) for n in names]
            order[model]=planned_greedy(preds2,names,8)
        err={}
        for model in ("old","ready"):
            err[model]=sum(abs(float(by_mapping[n][0][f"{model}_planned_makespan"])-points[n][0])/points[n][0]
                           for n in names)/64
        for rep in range(64):
            seq=names[:]
            random.Random(617026+1000*block_idx+rep).shuffle(seq)
            for k in KS:
                shams.append(dict(workflow=key[0],speed=key[1],seed=key[2],
                   rep=rep,shuffle_seed=617026+1000*block_idx+rep,k=k,
                   selected=";".join(seq[:k]),true_hv=hv([points[n] for n in seq[:k]],ref)))
        for k in KS:
            oracle=exact_hv_dp(list(points.values()),ref,k)
            for model in ("old","ready"):
                selected=order[model][:k]
                hv_actual=hv([points[n] for n in selected],ref)
                selections.append(dict(workflow=key[0],speed=key[1],seed=key[2],
                   model=model,k=k,mapping_keys=";".join(selected),
                   selected_actual_hv=hv_actual,actual_regret=max(0.,oracle-hv_actual)))
            old=order["old"][:k]
            ready=order["ready"][:k]
            old_hv=hv([points[n] for n in old],ref)
            ready_hv=hv([points[n] for n in ready],ref)
            assert max(old_hv,ready_hv)<=oracle+TOL
            ctrl=[r["true_hv"] for r in shams if
                  (r["workflow"],r["speed"],r["seed"],r["k"])==(*key,k)]
            assert len(ctrl)==64
            comparisons.append(dict(workflow=key[0],speed=key[1],seed=key[2],
               k=k,source_sha=source_sha,distinct_original_flavisited=64,true_nd=nd,
               complete_pool_actual_hv=full_hv,exact_true_k_oracle=oracle,
               true_k8_headroom=max(0.,full_hv-oracle),
               old_actual_hv=old_hv,ready_actual_hv=ready_hv,
               ready_minus_old_actual_hv=ready_hv-old_hv,
               old_true_regret=max(0.,oracle-old_hv),
               ready_true_regret=max(0.,oracle-ready_hv),
               common_physical_maps=len(set(old)&set(ready)),
               sham_median=statistics.median(ctrl),sham_mean=statistics.mean(ctrl),
               sham_low=min(ctrl),sham_high=max(ctrl),
               old_all64_makespan_mape=err["old"],ready_all64_makespan_mape=err["ready"]))
    assert len(comparisons)==24 and len(selections)==48 and len(shams)==1536
    write(out/"all_24_block_k_actual_pair_differences.csv",comparisons)
    write(out/"all_48_blind_k_picks.csv",selections)
    write(out/"all_1536_random_permutation_choices.csv",shams)
    lines=[
       f"# Genuine {source_kind} FLA-visited same64 genotype selection: original true WorkflowSim K2/K4/K8",
       "",
       "**8 real FLA-v12 3030-visit searches; 512 identical-pool two-model physical simulator rows.**",
       f"Source candidate membership is frozen from {source_kind} FLA evolution BEFORE model forecasts",
       "and original simulator labels. No new algorithm or independent untouched-family proof.",
       "",
       "| DAG | VM speed | Search seed | ND /64 | K | Shared /K | OLD actual HV | READY actual HV | ΔREADY−OLD | OLD regret | READY regret | Sham median |",
       "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for r in comparisons:
        lines.append(f"| {r['workflow']} | {r['speed']} | {r['seed']} | {r['true_nd']} | "
           f"{r['k']} | {r['common_physical_maps']} | {r['old_actual_hv']:.9f} | "
           f"{r['ready_actual_hv']:.9f} | {r['ready_minus_old_actual_hv']:+.9f} | "
           f"{r['old_true_regret']:.9f} | {r['ready_true_regret']:.9f} | "
           f"{r['sham_median']:.9f} |")
    lines+=["","| K | READY wins/ties/losses among 8 blocks | Mean READY−OLD true HV | Blocks with ND >K |",
       "|---:|---|---:|---:|"]
    for k in KS:
        q=[r for r in comparisons if r["k"]==k]
        d=[r["ready_minus_old_actual_hv"] for r in q]
        lines.append(f"| {k} | {sum(x>TOL for x in d)}/{sum(abs(x)<=TOL for x in d)}/{sum(x<-TOL for x in d)} | "
                     f"{statistics.mean(d):+.9f} | {sum(r['true_nd']>k for r in q)}/8 |")
    lines+=["","Prediction errors use identical 64 mappings for each predictor,",
       "so their direct comparison does not have the old selected-set mismatch.",
       "The 64 random permutations/block reuse the same true labels and do not",
       "give 64 statistically independent simulator experiments.",
       "Exact hindsight K oracles never selected simulator calls. This does not",
       "identify effects of READY-driven search trajectories; only offline",
       f"selection given a fixed, {source_kind}-fitness FLA-visited sample."]
    (out/"visitedpool64_findings.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))

if __name__=="__main__":
    assert len(sys.argv)==5,"usage: script.py ORIGINAL_ARTIFACTS OUT SOURCE_SHA PROTOCOL_BLOB_SHA"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3],sys.argv[4])
