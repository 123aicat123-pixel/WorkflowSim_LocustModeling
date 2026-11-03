#!/usr/bin/env python3
"""Frozen six-arm Pareto local gate test; read original WorkflowSim observations."""
import csv,math,pathlib,re,statistics,sys
DAGS=("CyberShake_30","Montage_25")
SEEDS=(161,162)
SPEEDS=("default","staggered")
ALGS=("DAG-Pareto-FLA[v12-hvbandit]","DAG-Pareto-FLA[v14-randompair]",
"DAG-Pareto-FLA[v14-timelinepair]","DAG-Pareto-FLA[v15-randomgate]",
"DAG-Pareto-FLA[v15-timelinegate]","NSGA-II[costseed]")
FACTORS=(1.5,3.0)
def read(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))
def hv(p,ref):
    total,last=0.,ref[1]
    for m,c in sorted(set(p)):
        if m<ref[0] and c<last:
            total+=(ref[0]-m)*(last-c);last=c
    return total
def run(root,out):
    data={}
    for dag in DAGS:
        for speed in SPEEDS:
            for seed in SEEDS:
                pref=f"v15-search-{speed}-{dag}-s{seed}"
                files={s:list(root.rglob(pref+s)) for s in
                   ("_summary.csv","_replays.csv","_budget_protocol.txt")}
                assert all(len(v)==1 for v in files.values()),(pref,files)
                stat=read(files["_summary.csv"][0])
                replay=read(files["_replays.csv"][0])
                assert len(stat)==6 and len(replay)==96
                assert {s["algorithm"] for s in stat}==set(ALGS)
                protocol=files["_budget_protocol.txt"][0].read_text()
                assert "PROSPECTIVE_REPLAY_BUDGET_K=16" in protocol
                assert "PROSPECTIVE_REPLAY_POLICY=pareto-cover" in protocol
                assert f"VM_SPEED_PROFILE={speed}" in protocol
                assert "VM_PRICE_PROFILE=default" in protocol
                jobroot=files["_summary.csv"][0].parent.parent
                log=(jobroot/"ci-logs/search.log").read_text()
                counts=[tuple(map(int,x)) for x in re.findall(
                   r"FLA_PAIRED_LOCAL mode=(\d+) trials=(\d+) changed=(\d+) dominates=(\d+) dominated=(\d+) incomparable=(\d+) gate=(\d+) rejected=(\d+) evaluations=(\d+)",log)]
                assert len(counts)==4,(pref,counts)
                assert {(x[0],x[6]) for x in counts}=={(1,0),(2,0),(1,1),(2,1)}
                for mode,trials,changed,win,lose,tie,gate,rejected,ev in counts:
                    assert trials==1400 and changed<=trials and win+lose+tie==trials and ev==3030
                    assert rejected==(lose if gate else 0),(pref,mode,gate,rejected,lose)
                for s in stat:
                    alg=s["algorithm"]
                    assert int(s["evaluations"])==int(s["captured_evaluations"])==3030
                    assert int(s["replayed"])==16
                    rr=sorted((x for x in replay if x["algorithm"]==alg),key=lambda x:int(x["candidate_index"]))
                    assert len(rr)==16 and [int(x["candidate_index"]) for x in rr]==list(range(1,17))
                    assert len({x["mapping"] for x in rr})==16
                    planned=[(float(x["planned_makespan"]),float(x["planned_cost"])) for x in rr]
                    actual=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in rr]
                    assert all(math.isfinite(z) and z>0 for a in planned+actual for z in a)
                    data[dag,speed,seed,alg]=(planned,actual,float(s["search_selection_replay_ms"]))
                data[dag,speed,seed,"gate"]=counts
    cases=[]
    for dag in DAGS:
        for speed in SPEEDS:
            points=[z for seed in SEEDS for alg in ALGS
                    for z in data[dag,speed,seed,alg][0]]
            bounds=(max(z[0] for z in points),max(z[1] for z in points))
            for factor in FACTORS:
                ref=(factor*bounds[0]+1,factor*bounds[1]+1)
                for seed in SEEDS:
                    arms=[data[dag,speed,seed,a] for a in ALGS]
                    assert all(x<ref[0] and y<ref[1] for a in arms for x,y in a[1]),(
                       "Frozen planned-only reference invalid",dag,speed,factor,seed)
                    vals=[hv(a[1],ref) for a in arms]
                    assert min(vals)>0
                    diff=lambda a,b:100*(vals[a]/vals[b]-1)
                    cases.append(dict(workflow=dag,vm_speed=speed,seed=seed,reference=factor,
                        v15_timeline_vs_v14_timeline_pct=diff(4,2),
                        v15_random_vs_v14_random_pct=diff(3,1),
                        v15_timeline_vs_v15_random_pct=diff(4,3),
                        v15_timeline_vs_v12_pct=diff(4,0),
                        v15_timeline_vs_nsga_pct=diff(4,5),
                        v14_timeline_vs_v14_random_pct=diff(2,1),
                        v15_timeline_wins_v14_timeline=int(vals[4]>vals[2]),
                        v15_timeline_wins_v12=int(vals[4]>vals[0]),
                        v15_timeline_wins_nsga=int(vals[4]>vals[5]),
                        gate_timeline_rejected=next(x[7] for x in data[dag,speed,seed,"gate"] if x[0]==2 and x[6]==1),
                        gate_random_rejected=next(x[7] for x in data[dag,speed,seed,"gate"] if x[0]==1 and x[6]==1)))
    assert len(cases)==len(DAGS)*len(SPEEDS)*len(SEEDS)*len(FACTORS)
    out.mkdir(parents=True,exist_ok=True)
    with (out/"v15_search_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
    lines=["# v15 Pareto-gated budget-neutral search: six-arm development report","",
      "8 blocks (two previously studied DAG families, 2 VM speed profiles, seeds 161/162), six algorithms per block. Exact 3030 stage-in-aware objective evaluations and 16 REAL WorkflowSim K16 replays per solver. Every paired variant has exactly 1400 charged local trials, v15 rejects only truly planned-Pareto-dominated trials from its next-generation survivor slot. Original default v12 and NSGA-II unchanged.",
      "HV reference was predefined from PLANNED candidate maxima across all six algorithms and both seeds per DAG+speed, 1.5x+1 primary, 3.0x+1 sensitivity. All actual points fit within both; simulator outcomes never used to move reference.",
      "","| DAG | VM | v15 timeline vs ungated v14 timeline | v15 random vs ungated random | v15 timeline vs v15 random | v15 timeline vs v12 | v15 timeline vs NSGA-II |",
      "|---|---|---:|---:|---:|---:|---:|"]
    for dag in DAGS:
        for speed in SPEEDS:
            rr=[x for x in cases if x["workflow"]==dag and x["vm_speed"]==speed and x["reference"]==1.5]
            lines.append(f"| {dag} | {speed} | "+
              f"{statistics.mean(x['v15_timeline_vs_v14_timeline_pct'] for x in rr):+.4f}% | "+
              f"{statistics.mean(x['v15_random_vs_v14_random_pct'] for x in rr):+.4f}% | "+
              f"{statistics.mean(x['v15_timeline_vs_v15_random_pct'] for x in rr):+.4f}% | "+
              f"{statistics.mean(x['v15_timeline_vs_v12_pct'] for x in rr):+.4f}% | "+
              f"{statistics.mean(x['v15_timeline_vs_nsga_pct'] for x in rr):+.4f}% |")
    for factor in FACTORS:
        rr=[x for x in cases if x["reference"]==factor]
        lines.extend(["",f"## Pooled reference {factor}x across {len(rr)} matched cases",
          f"v15 timeline vs v14 timeline mean: {statistics.mean(x['v15_timeline_vs_v14_timeline_pct'] for x in rr):+.6f}%; wins {sum(x['v15_timeline_wins_v14_timeline'] for x in rr)}/{len(rr)}.",
          f"v15 random vs v14 random mean: {statistics.mean(x['v15_random_vs_v14_random_pct'] for x in rr):+.6f}%.",
          f"v15 timeline vs v15 random mean: {statistics.mean(x['v15_timeline_vs_v15_random_pct'] for x in rr):+.6f}%.",
          f"v15 timeline vs v12 mean: {statistics.mean(x['v15_timeline_vs_v12_pct'] for x in rr):+.6f}%; wins {sum(x['v15_timeline_wins_v12'] for x in rr)}/{len(rr)}.",
          f"v15 timeline vs seeded NSGA-II mean: {statistics.mean(x['v15_timeline_vs_nsga_pct'] for x in rr):+.6f}%; wins {sum(x['v15_timeline_wins_nsga'] for x in rr)}/{len(rr)}."])
    lines.extend(["","## Individual primary-reference outcomes (all losses retained)","",
        "| Workflow | VM | Seed | Timeline gate effect | Random gate effect | Timeline vs random gated | Timeline gated vs v12 | Timeline gated vs NSGA-II |",
        "|---|---|---:|---:|---:|---:|---:|---:|"])
    for x in cases:
        if x["reference"]!=1.5:continue
        lines.append(f"| {x['workflow']} | {x['vm_speed']} | {x['seed']} | "+
          f"{x['v15_timeline_vs_v14_timeline_pct']:+.4f}% | "+
          f"{x['v15_random_vs_v14_random_pct']:+.4f}% | "+
          f"{x['v15_timeline_vs_v15_random_pct']:+.4f}% | "+
          f"{x['v15_timeline_vs_v12_pct']:+.4f}% | "+
          f"{x['v15_timeline_vs_nsga_pct']:+.4f}% |")
    lines.extend(["","## Limitations",
       "This is a development-stage test on studied workflow families and only two seeds, so neither positive nor negative pooled differences establish broad statistical superiority. The v15 survivor gate duplicates normal-child genotype references when a local trial is dominated; genotype diversity may shrink. All evaluated genotypes are still recorded for audit and considered by the nondominated archive. Every neighbor fitness call is charged. Compare random gate to disentangle gate effect from timeline guidance. Prechosen reference sensitivity is part of the report, not independent runs."])
    (out/"v15_search_report.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_v15_search_report.py RAW_ARTIFACT_ROOT OUT")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
