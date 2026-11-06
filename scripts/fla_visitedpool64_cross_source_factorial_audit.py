#!/usr/bin/env python3
"""Retrospective cross-source common-reference OLD/READY predictor selection.

Input: immutable previously observed OLD source run 42195625222 and newly
frozen READY source run 42196301442, both with identical physical replay
source format. Source identities and labels are verified before comparison.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys
from fla_independent32_k4_identifiability_audit import hv,planned_greedy
from fla_samepool32_k8_random_sham_audit import exact_hv_dp,nd_points,test_oracle
from fla_montage_fullsearch_ready_transfer_audit import write

DAGS=("Montage_50","Montage_100")
SPEEDS=("default","staggered")
SEEDS=("1701","1702")
SOURCE_SHA={
 "old":"7a0dba36a84e367be45c891eedd44dd629083455",
 "ready":"1209a4ba790ba4d9e81a15bd9edaef1a05688b49"
}
SOURCES=("old","ready")
MODELS=("old","ready")
TOL=1e-8

def read(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def build(root,source_kind,proto):
    found={}
    for path in sorted((root/source_kind).glob(
            "visitedpool64-*/research_pool64_frozen_predictions.csv")):
        folder=path.parent
        tags={}
        for line in (folder/"block-id.txt").read_text().splitlines():
            a,b=line.split("=",1)
            assert a not in tags
            tags[a]=b
        key=(tags["workflow"],tags["speed"],tags["seed"])
        assert key in set(itertools.product(DAGS,SPEEDS,SEEDS)) and key not in found
        assert folder.name==f"visitedpool64-{key[0]}-{key[1]}-s{key[2]}"
        assert (folder/"source-sha.txt").read_text().strip()==SOURCE_SHA[source_kind]
        assert (folder/"protocol-sha.txt").read_text().strip()==proto
        log=(folder/"experiment.log").read_text(errors="replace")
        assert log.count("FROZEN_BEFORE_TRUTH")==1
        assert log.count("ORIGINAL_TRUE_POOL64_PASS")==64
        assert "PASS OLD FLA 3030 real visits" in log
        budgets={}
        for line in (folder/"research_pool64_budget.txt").read_text().splitlines():
            a,b=line.split("=",1)
            assert a not in budgets
            budgets[a]=b
        assert budgets["search_evaluations"]=="3030" and budgets["pool_size"]=="64"
        assert budgets["old_forecasts"]=="64" and budgets["ready_forecasts"]=="64"
        assert (budgets["workflow"],budgets["seed"])==(key[0],key[2])
        predictions=read(path)
        truth=read(folder/"research_pool64_true_replays.csv")
        assert len(predictions)==len(truth)==64
        assert len({p["mapping"] for p in predictions})==64
        mapping={}
        for p,t in zip(predictions,truth):
            assert (p["pool_index"],p["mapping"])==(t["pool_index"],t["mapping"])
            assert p["workflow"]==t["workflow"]==key[0]
            assert p["seed"]==t["seed"]==key[2]
            actual=(float(t["actual_makespan"]),float(t["actual_cost"]))
            assert all(math.isfinite(v) and v>0 for v in actual)
            preds={m:(float(p[f"{m}_planned_makespan"]),
                      float(p[f"{m}_planned_cost"])) for m in MODELS}
            assert all(math.isfinite(v) and v>0 for row in preds.values() for v in row)
            ids={}
            for item in p["mapping"].split("|"):
                task,vm=map(int,item.split(":"))
                assert task not in ids
                ids[task]=vm
            assert set(ids)==set(range(1,int(key[0].rsplit("_",1)[1])+1))
            assert all(0<=v<16 for v in ids.values())
            mapping[p["mapping"]]=(actual,preds)
        found[key]=mapping
    assert set(found)==set(itertools.product(DAGS,SPEEDS,SEEDS))
    return found

def audit(root,out,old_protocol,ready_protocol):
    test_oracle()
    out.mkdir(parents=True,exist_ok=True)
    all_cases={
       "old":build(root,"old",old_protocol),
       "ready":build(root,"ready",ready_protocol)
    }
    comparisons=[]
    picks=[]
    for key in sorted(all_cases["old"]):
        source_pools={src:all_cases[src][key] for src in SOURCES}
        true={}
        for src,mappings in source_pools.items():
            for mapping,(actual,pred) in mappings.items():
                if mapping in true:
                    previous=true[mapping]
                    assert all(math.isclose(a,b,rel_tol=TOL,abs_tol=TOL)
                               for a,b in zip(previous,actual)),(
                                 "same physical mapping has inconsistent simulator label",key)
                true[mapping]=actual
        all_actual=list(true.values())
        assert 64<=len(true)<=128
        reference=tuple(1.5*max(p[j] for p in all_actual)+1e-6 for j in (0,1))
        sets={source:set(pool) for source,pool in source_pools.items()}
        assert len(sets["old"])==len(sets["ready"])==64
        results={}
        oracle={}
        for source,pool in source_pools.items():
            names=sorted(pool)
            oracle[source]=exact_hv_dp([v[0] for v in pool.values()],reference,8)
            for model in MODELS:
                prediction=[pool[n][1][model] for n in names]
                selected=planned_greedy(prediction,names,8)
                assert len(set(selected))==8 and set(selected)<=sets[source]
                true_hv=hv([true[n] for n in selected],reference)
                assert true_hv<=oracle[source]+TOL
                results[source,model]=true_hv
                picks.append(dict(workflow=key[0],speed=key[1],seed=key[2],
                     source=source,selector=model,true_hv=true_hv,
                     regret=max(0.,oracle[source]-true_hv),
                     physical_maps=";".join(selected)))
        old_effect=results["old","ready"]-results["old","old"]
        ready_effect=results["ready","ready"]-results["ready","old"]
        comparisons.append(dict(workflow=key[0],speed=key[1],seed=key[2],
            unique_in_two_sources=len(true),
            source_pool_overlap=len(sets["old"]&sets["ready"]),
            shared_ref_m=reference[0],shared_ref_cost=reference[1],
            oldsource_oldselector=results["old","old"],
            oldsource_readyselector=results["old","ready"],
            readysource_oldselector=results["ready","old"],
            readysource_readyselector=results["ready","ready"],
            oldpool_k8_oracle=oracle["old"],readypool_k8_oracle=oracle["ready"],
            ready_minus_old_selector_on_old_source=old_effect,
            ready_minus_old_selector_on_ready_source=ready_effect,
            selector_source_interaction=ready_effect-old_effect,
            ready_source_minus_old_source_under_old_selector=results["ready","old"]-results["old","old"],
            ready_source_minus_old_source_under_ready_selector=results["ready","ready"]-results["old","ready"]))
    assert len(comparisons)==8 and len(picks)==32
    write(out/"cross_source_four_arm_common_reference_K8.csv",comparisons)
    write(out/"all_32_cross_source_blind_K8_choices.csv",picks)
    report=[
      "# Matched source-pool × terminal selector factorial on original true WorkflowSim labels",
      "",
      "**Eight paired development blocks, 1024 original source replay observations**",
      "(512 previously observed OLD-fitness FLA-sourced + 512 new READY-fitness",
      "FLA-sourced). Original source runs are distinct but correlated by DAG/speed/seed;",
      "the old source outcome was seen before READY follow-up was frozen.",
      "",
      "| DAG | Speed | Seed | Same maps /64 | OLD source: READY−OLD selector | READY source: READY−OLD selector | Interaction | READY source − OLD source with READY selector |",
      "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in comparisons:
        report.append(f"| {r['workflow']} | {r['speed']} | {r['seed']} | "
          f"{r['source_pool_overlap']} | "
          f"{r['ready_minus_old_selector_on_old_source']:+.9f} | "
          f"{r['ready_minus_old_selector_on_ready_source']:+.9f} | "
          f"{r['selector_source_interaction']:+.9f} | "
          f"{r['ready_source_minus_old_source_under_ready_selector']:+.9f} |")
    report+=["","| Descriptive contrast | Wins / 8 | Ties / 8 | Losses / 8 | Mean normalized paired ΔHV |",
        "|---|---:|---:|---:|---:|"]
    for name,keyname in [
       ("READY selector effect on OLD pool","ready_minus_old_selector_on_old_source"),
       ("READY selector effect on READY pool","ready_minus_old_selector_on_ready_source"),
       ("Source × selector interaction","selector_source_interaction"),
       ("READY vs OLD source at OLD selector","ready_source_minus_old_source_under_old_selector"),
       ("READY vs OLD source at READY selector","ready_source_minus_old_source_under_ready_selector")]:
        delta=[r[keyname] for r in comparisons]
        report.append(f"| {name} | {sum(x>TOL for x in delta)} | "
          f"{sum(abs(x)<=TOL for x in delta)} | {sum(x< -TOL for x in delta)} | "
          f"{statistics.mean(delta):+.9f} |")
    report+=["","Each block's FOUR arms use ONE true reference from the union of all",
      "128 source mappings (or fewer if overlap). This is the only valid way",
      "to compare actual HV across distinct physical source pools.",
      "The K8 oracle is retrospective and limited to each physical64 pool.",
      "Differences in source pools reflect actual different search trajectories",
      "PLUS a fixed random subsample of visited genotypes, not an isolated",
      "novel operator. Both solvers here are unchanged FLA-v12.",
      "NO statistical significance, unseen DAG generalization or algorithm promotion."]
    (out/"cross_source_actual_findings.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    assert len(sys.argv)==5,"usage: audit.py ORIGINALS OUT OLD_PROTO_SHA READY_PROTO_SHA"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3],sys.argv[4])
