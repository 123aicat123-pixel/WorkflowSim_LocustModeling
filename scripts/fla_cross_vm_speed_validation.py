#!/usr/bin/env python3
"""Cross-instance, within-tier VM speed heterogeneity K16 online-feedback audit.

No simulator result is used for candidate selection or for constructing the
per-family/profile reference: the latter comes ONLY from the planned objective
bounds of original fixed Pareto-cover K16 replay candidates, scaled x3+1.
No post-hoc rescue / enlargement is allowed if any real point exceeds bounds.
"""
import collections
import csv
import math
import pathlib
import statistics
import sys

WORKFLOWS=("CyberShake_50","Epigenomics_46","Inspiral_30","Montage_50","Sipht_60")
SEEDS=(113,114)
SPEEDS=("default","staggered")
POLICIES=("pareto-cover","online-observed-hv")
ALGOS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")

def read(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))

def hv(pts,reference):
    total,last=0.,reference[1]
    for m,c in sorted(set(pts)):
        if m<reference[0] and c<last:
            total+=(reference[0]-m)*(last-c)
            last=c
    return total

def run(root,out):
    data={}
    for wf in WORKFLOWS:
        for seed in SEEDS:
            for speed in SPEEDS:
                for policy in POLICIES:
                    prefix=f"{policy}-{speed}-{wf}-s{seed}"
                    paths={suffix:list(root.rglob(prefix+suffix))
                        for suffix in ("_summary.csv","_replays.csv","_visited_fingerprints.csv",
                                       "_budget_protocol.txt")}
                    assert all(len(v)==1 for v in paths.values()),(prefix,paths)
                    stat=read(paths["_summary.csv"][0])
                    replay=read(paths["_replays.csv"][0])
                    hashes=read(paths["_visited_fingerprints.csv"][0])
                    assert len(stat)==len(hashes)==3 and len(replay)==48,(prefix,len(replay))
                    assert {r["algorithm"] for r in stat}==set(ALGOS)
                    fingerprint={r["algorithm"]:r["history_sha256"] for r in hashes}
                    protocol=paths["_budget_protocol.txt"][0].read_text()
                    assert f"VM_SPEED_PROFILE={speed}" in protocol
                    assert "VM_PRICE_PROFILE=default" in protocol
                    assert "PROSPECTIVE_REPLAY_BUDGET_K=16" in protocol
                    assert f"PROSPECTIVE_REPLAY_POLICY={policy}" in protocol
                    for r in stat:
                        alg=r["algorithm"]
                        assert int(r["evaluations"])==int(r["captured_evaluations"])==3030
                        assert int(r["replayed"])==16
                        assert math.isfinite(float(r["selection_ms"]))
                        assert math.isfinite(float(r["replay_ms"]))
                        assert float(r["replay_ms"])>0
                        rr=sorted((x for x in replay if x["algorithm"]==alg),
                                  key=lambda x:int(x["candidate_index"]))
                        assert len(rr)==16 and len({x["mapping"] for x in rr})==16
                        assert [int(x["candidate_index"]) for x in rr]==list(range(1,17))
                        p=[(float(x["planned_makespan"]),float(x["planned_cost"])) for x in rr]
                        t=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in rr]
                        assert all(math.isfinite(v) and v>0 for pair in p+t for v in pair)
                        data[wf,seed,speed,policy,alg]=dict(planned=p,true=t,hash=fingerprint[alg],
                            first4=[x["mapping"] for x in rr[:4]],
                            time_ms=float(r["search_selection_replay_ms"]))
    assert len(data)==len(WORKFLOWS)*len(SEEDS)*len(SPEEDS)*len(POLICIES)*len(ALGOS)
    refs={}
    for wf in WORKFLOWS:
        for speed in SPEEDS:
            # Pre-simulator-only reference, coverage PLANNED points, never actual labels.
            pool=[point for seed in SEEDS for alg in ALGOS
                for point in data[wf,seed,speed,"pareto-cover",alg]["planned"]]
            refs[wf,speed]=(3*max(p[0] for p in pool)+1,3*max(p[1] for p in pool)+1)
    paired=[]
    for wf in WORKFLOWS:
        for seed in SEEDS:
            for speed in SPEEDS:
                for alg in ALGOS:
                    a=data[wf,seed,speed,"pareto-cover",alg]
                    b=data[wf,seed,speed,"online-observed-hv",alg]
                    assert a["hash"]==b["hash"],(wf,seed,speed,alg,"history")
                    assert a["first4"]==b["first4"],(wf,seed,speed,alg,"warmup")
                    ref=refs[wf,speed]
                    for point in a["true"]+b["true"]:
                        assert point[0]<ref[0] and point[1]<ref[1],(
                            "Planned-only reference does not enclose actual objective",wf,speed,point,ref)
                    av,bv=hv(a["true"],ref),hv(b["true"],ref)
                    assert av>0 and bv>0
                    paired.append(dict(workflow=wf,seed=seed,speed_profile=speed,algorithm=alg,
                        cover_hv=av,online_hv=bv,gain_pct=100*(bv/av-1),
                        online_wins=int(bv>av),relative_total_time_pct=100*(b["time_ms"]/a["time_ms"]-1),
                        reference_m=ref[0],reference_c=ref[1]))
    assert len(paired)==60
    out.mkdir(parents=True,exist_ok=True)
    with (out/"cross_vm_paired.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(paired[0]));w.writeheader();w.writerows(paired)
    report=["# New-DAX-size and within-tier VM heterogeneity: real K16 online feedback validation",
        "",
        "Five additional DAX *instance sizes* (CyberShake_50, Epigenomics_46, Inspiral_30, Montage_50, Sipht_60) from FIVE previously studied workflow FAMILIES; NOT new unseen families.",
        "Each speed configuration uses 16 real VM instances: default four machines at each 250/500/1000/2000 MIPS tier, or synthetic staggered 65/80/90/100% of tier speed within each tier. Default VM rental rates fixed. Both planning and actual simulator receive the same CondorVM values.",
        "Two new seeds 113/114, three solver arms, two K16 policies, 3030 planned evaluations and 16 actual independent WorkflowSim replays for EVERY solver/policy case. Fingerprints assert identical genotype history within each paired regime.",
        "COMMON HV reference for BOTH policies and both seeds at each workflow/speed is determined by 3 × per-coordinate maximum of ONLY the original baseline Pareto-cover PLANNED objective values + 1. It is defined without simulation values or online selected planned points; all real results must fit strictly inside the reference or the audit FAILS.",
        "Do not compare raw HV across workload sizes or speed regimes. This is exploratory sensitivity, not true external new-DAG-family validation.",
        "",
        "| VM speed | Solver | Mean paired online relative simulator-HV change | Wins /10 | Mean relative total-time change |",
        "|---|---|---:|---:|---:|"]
    for speed in SPEEDS:
        for alg in ALGOS:
            rows=[x for x in paired if x["speed_profile"]==speed and x["algorithm"]==alg]
            report.append(f"| {speed} | {alg} | {statistics.mean(x['gain_pct'] for x in rows):+.4f}% | "+
                f"{sum(x['online_wins'] for x in rows)}/{len(rows)} | "+
                f"{statistics.mean(x['relative_total_time_pct'] for x in rows):+.3f}% |")
    report+=["","## Full matched workload and speed conditions, including all negative results","",
       "| Workflow | Seed | Speed | Algorithm | Online vs cover HV | Total-time difference |",
       "|---|---:|---|---|---:|---:|"]
    for r in paired:
        report.append(f"| {r['workflow']} | {r['seed']} | {r['speed_profile']} | {r['algorithm']} | "+
                      f"{r['gain_pct']:+.4f}% | {r['relative_total_time_pct']:+.3f}% |")
    report+=["","## Scope limits",
        "Ten workflow-seed blocks per speed profile and three correlated algorithms per block, not 60 statistically independent DAGs.",
        "This alters REAL VM MIPS within existing machine tiers; no new synthetic DAG topology or newly unseen DAG family is introduced.",
        "Evaluation HV reference is a reproducible planner-derived data-dependent bound, not an external theoretical bound. Scaling affects reported HV gains.",
        "Equal K16 simulator calls do not imply equal elapsed runtime. Java runner/JIT variance persists.",
        "This evaluates post-search simulator-aware replay selection. It does not improve the FLA search generation operators nor prove v12 superiority over NSGA-II."]
    (out/"cross_vm_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_cross_vm_speed_validation.py ROOT OUT")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
