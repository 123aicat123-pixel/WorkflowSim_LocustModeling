#!/usr/bin/env python3
"""Frozen fixed-32 same-physical-pool OLD/READY and 64 random sham K2/4/8.

Original true labels are used ONLY for post-selection evaluation and hindsight
oracle. Random shams are random selections, not independent simulator runs.
"""
import csv
import itertools
import math
import pathlib
import random
import statistics
import sys

from fla_independent32_k4_identifiability_audit import hv, dominates, planned_greedy
from fla_montage32_transfer_audit import POLICIES, SOURCE_COLUMNS, write

DAGS=("Inspiral_50","Epigenomics_46","Sipht_60")
SPEEDS=("default","staggered")
KS=(2,4,8)
N_SHAM=64
TOL=1e-9
EXPECTED=set(itertools.product(DAGS,SPEEDS))

def nd_points(points):
    unique=sorted(set(points))
    return [x for x in unique if not any(
        dominates(y,x) for y in unique if y!=x)]

def exact_hv_dp(points, ref, k):
    """Exact 2D K-point dominated hypervolume: nondominated ordered-chain DP.

    In sorted nondominated (m ascending, c descending) coordinates, consecutive
    selected points yield first rectangle (R_m-m_i)*(R_c-c_i), and each new
    point j after i adds (R_m-m_j)*(c_i-c_j).
    """
    assert k>=1
    frontier=nd_points(points)
    assert frontier and all(0<p[0]<ref[0] and 0<p[1]<ref[1] for p in frontier)
    n=len(frontier)
    if n<=k:
        return hv(frontier,ref)
    dp=[(ref[0]-m)*(ref[1]-c) for m,c in frontier]
    best=max(dp)
    for _ in range(2,min(k,n)+1):
        nxt=[float("-inf")]*n
        for j in range(1,n):
            m,c=frontier[j]
            nxt[j]=max(dp[i]+(ref[0]-m)*(frontier[i][1]-c)
                       for i in range(j))
        dp=nxt
        best=max(best,max(dp))
    value=best/(ref[0]*ref[1])
    assert 0<=value<=1+TOL
    return value

def test_oracle():
    toysets=(
        [(2,9),(4,7),(6,4),(8,2)],
        [(3,8),(4,9),(5,7),(7,3),(7,3)],
        [(1,8),(2,7),(3,6),(4,5),(8,4),(9,1)],
        [(2,8),(3,8),(4,8),(5,8)],
    )
    for pts in toysets:
        ref=(12.,12.)
        for k in range(1,min(4,len(pts))+1):
            brute=max(hv(s,ref) for s in itertools.combinations(pts,k))
            dynamic=exact_hv_dp(pts,ref,k)
            assert abs(brute-dynamic)<1e-12,(pts,k,brute,dynamic)
    for seed in range(25):
        rng=random.Random(9000+seed)
        pts=[(rng.uniform(1,9),rng.uniform(1,9)) for _ in range(9)]
        for k in (1,2,3,4,8):
            brute=max(hv(s,(12.,12.)) for s in itertools.combinations(pts,k))
            dynamic=exact_hv_dp(pts,(12.,12.),k)
            assert abs(brute-dynamic)<1e-12,(seed,k,brute,dynamic)
    print("PASS exhaustive finite-subset K-HV vs non-dominated-chain exact DP")

def audit(root,out,source_sha,protocol_hash):
    test_oracle()
    out.mkdir(parents=True,exist_ok=True)
    files=sorted(root.glob("samepool32-*/same_mapping_true_replays.csv"))
    assert len(files)==6,("missing original true source blocks",files)
    blocks={}
    all_source=[]
    for path in files:
        folder=path.parent
        meta={}
        for line in (folder/"block-id.txt").read_text().splitlines():
            k,v=line.split("=",1)
            assert k not in meta
            meta[k]=v
        case=(meta["workflow"],meta["vm_speed"])
        assert case in EXPECTED and case not in blocks
        assert folder.name==f"samepool32-{case[0]}-{case[1]}"
        assert meta["vm_price"]=="default" and meta["seed"]=="1501"
        assert (folder/"source-sha.txt").read_text().strip()==source_sha
        assert (folder/"protocol-sha.txt").read_text().strip()==protocol_hash
        with path.open(newline="",encoding="utf-8") as f:
            reader=csv.DictReader(f)
            assert reader.fieldnames==list(SOURCE_COLUMNS),reader.fieldnames
            records=list(reader)
        assert len(records)==32
        assert {r["mapping_policy"] for r in records}==set(POLICIES)
        assert len({r["task_vm_mapping"] for r in records})==32
        expected_n=int(case[0].split("_")[1])
        for r in records:
            assert (r["workflow"],r["vm_profile"],r["seed"])==(case[0],case[1],"1501")
            assert int(r["task_count"])==expected_n
            mapping={}
            for x in r["task_vm_mapping"].split("|"):
                a,b=map(int,x.split(":"))
                assert a not in mapping
                mapping[a]=b
            assert set(mapping)==set(range(1,expected_n+1))
            assert all(0<=x<16 for x in mapping.values())
            for col in SOURCE_COLUMNS[5:15]:
                val=float(r[col])
                assert math.isfinite(val) and (val>=0 if col.endswith("_mae") else val>0)
            all_source.append(dict(**r))
        log=(folder/"source.log").read_text(errors="replace")
        assert log.count("FROZEN_MAP_UNIVERSE_PASS")==32
        assert "PASS thirty-two disjoint algorithm-independent source genotypes" in log
        blocks[case]=records
    assert set(blocks)==EXPECTED and len(all_source)==192
    write(out/"all_192_original_workflowsim_truth.csv",all_source)
    cases=sorted(EXPECTED)
    comparisons=[]
    chosen_rows=[]
    sham_rows=[]
    for idx,case in enumerate(cases):
        rec=blocks[case]
        source={r["mapping_policy"]:r for r in rec}
        names=sorted(source)
        true={n:(float(source[n]["actual_makespan"]),float(source[n]["actual_cost"]))
              for n in names}
        ref=tuple(1.5*max(p[j] for p in true.values())+1e-6 for j in (0,1))
        all_hv=hv(list(true.values()),ref)
        nd=len(nd_points(list(true.values())))
        choices={}
        for model in ("old","ready"):
            forecast=[(float(source[n][f"{model}_planned_makespan"]),
                       float(source[n][f"{model}_planned_cost"])) for n in names]
            order=planned_greedy(forecast,names,8)
            assert len(order)==8 and len(set(order))==8
            choices[model]=order
            for k in KS:
                selected=order[:k]
                chosen_rows.append(dict(workflow=case[0],vm_speed=case[1],
                    predictor=model,k=k,selected_policies="|".join(selected),
                    actual_hv=hv([true[n] for n in selected],ref)))
        # 64 predeclared independent *selection permutations* on one deterministic truth pool.
        permutations=[]
        for rep in range(N_SHAM):
            perm=names[:]
            random.Random(5202606+1000*idx+rep).shuffle(perm)
            assert len(perm)==32 and len(set(perm))==32
            permutations.append(perm)
            for k in KS:
                sham_rows.append(dict(workflow=case[0],vm_speed=case[1],
                    replicate=rep,shuffle_seed=5202606+1000*idx+rep,k=k,
                    policies="|".join(perm[:k]),actual_hv=hv([true[n] for n in perm[:k]],ref)))
        for k in KS:
            oracle=exact_hv_dp(list(true.values()),ref,k)
            old=choices["old"][:k]
            ready=choices["ready"][:k]
            oldhv=hv([true[n] for n in old],ref)
            readyhv=hv([true[n] for n in ready],ref)
            assert max(oldhv,readyhv)<=oracle+TOL
            shams=[x["actual_hv"] for x in sham_rows if
                   (x["workflow"],x["vm_speed"],x["k"])==(case[0],case[1],k)]
            assert len(shams)==N_SHAM
            old_mape=sum(abs(float(source[n]["old_planned_makespan"])-true[n][0])/true[n][0]
                         for n in names)/len(names)
            ready_mape=sum(abs(float(source[n]["ready_planned_makespan"])-true[n][0])/true[n][0]
                           for n in names)/len(names)
            comparisons.append(dict(workflow=case[0],vm_speed=case[1],k=k,
                 source_sha=source_sha,source_count=32,true_nd_size=nd,
                 full_true_hv=all_hv,oracle_true_hv=oracle,
                 oracle_saturation_gap=max(0.,all_hv-oracle),
                 old_hv=oldhv,ready_hv=readyhv,ready_minus_old_hv=readyhv-oldhv,
                 old_regret=max(0.,oracle-oldhv),ready_regret=max(0.,oracle-readyhv),
                 overlap=len(set(old)&set(ready)),
                 sham_mean=statistics.mean(shams),sham_median=statistics.median(shams),
                 sham_min=min(shams),sham_max=max(shams),
                 sham_p05=sorted(shams)[3],sham_p95=sorted(shams)[60],
                 old_all32_makespan_mape=old_mape,
                 ready_all32_makespan_mape=ready_mape))
    assert len(comparisons)==18 and len(chosen_rows)==36 and len(sham_rows)==1152
    write(out/"all_18_paired_actual_hv_and_exact_oracles.csv",comparisons)
    write(out/"all_36_outcome_blind_predictor_choices.csv",chosen_rows)
    write(out/"all_1152_outcome_blind_random_sham_choices.csv",sham_rows)
    lines=[
      "# Same-physical-32 OLD/READY K2,K4,K8 with random permutation sham",
      "",
      "**Original WorkflowSim real replay, no optimizer search; 6 blocks, 192 true physical maps.**",
      "64 pseudorandom *selection* permutations/block (not independent simulator repeats).",
      "Historical DAG families and one deterministic seed; no SCI algorithm improvement claim.",
      "",
      "| DAG | Speed | K | True ND | OLD true HV | READY true HV | READY−OLD | OLD regret | READY regret | Sham median | Same maps |",
      "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for r in comparisons:
        lines.append(f"| {r['workflow']} | {r['vm_speed']} | {r['k']} | {r['true_nd_size']} | "
          f"{r['old_hv']:.9f} | {r['ready_hv']:.9f} | {r['ready_minus_old_hv']:+.9f} | "
          f"{r['old_regret']:.9f} | {r['ready_regret']:.9f} | "
          f"{r['sham_median']:.9f} | {r['overlap']}/{r['k']} |")
    lines+=["",
       "| K | READY wins/ties/losses (6 conditions) | Mean READY−OLD actual HV | Mean exact K8 headroom (for chosen K) |",
       "|---:|---|---:|---:|"]
    for k in KS:
        rr=[r for r in comparisons if r["k"]==k]
        differences=[r["ready_minus_old_hv"] for r in rr]
        lines.append(f"| {k} | {sum(x>TOL for x in differences)}/"
              f"{sum(abs(x)<=TOL for x in differences)}/"
              f"{sum(x< -TOL for x in differences)} | "
              f"{statistics.mean(differences):+.9f} | "
              f"{statistics.mean(r['oracle_saturation_gap'] for r in rr):.9f} |")
    lines+=["",
       "Same fixed candidate set across OLD and READY eliminates trajectory confounding",
       "IN THIS SPECIFIC POOL, but does NOT identify the cause of historical full FLA loss.",
       "Oracle and sham scores are retrospective only. Never use source truth to choose K8.",
       "Full raw observations, labels, sham permutations and negative findings are archived."]
    (out/"samepool32_findings.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))

if __name__=="__main__":
    assert len(sys.argv)==5,"usage: script.py ORIGINAL_ROOT REPORT_DIR SOURCE_SHA PROTOCOL_HASH"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3],sys.argv[4])
