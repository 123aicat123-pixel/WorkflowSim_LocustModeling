#!/usr/bin/env python3
"""Predeclared v14 search budget-neutral paired-neighbor stage-in-aware simulator HV report."""
import csv
import pathlib
import math
import statistics
import re
import sys

WFS=("CyberShake_50","Montage_50","Sipht_60")
SEEDS=(151,152)
SPEEDS=("default","staggered")
ALG=("DAG-Pareto-FLA[v12-hvbandit]",
     "DAG-Pareto-FLA[v14-randompair]",
     "DAG-Pareto-FLA[v14-timelinepair]",
     "NSGA-II[costseed]")
FACTORS=(1.5,3.0)

def read(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))

def hv(points,ref):
    total,last=0.,ref[1]
    for m,c in sorted(set(points)):
        if m<ref[0] and c<last:
            total+=(ref[0]-m)*(last-c)
            last=c
    return total

def run(root,out):
    data={}
    for wf in WFS:
        for speed in SPEEDS:
            for seed in SEEDS:
                prefix=f"v14-search-{speed}-{wf}-s{seed}"
                files={s:list(root.rglob(prefix+s))
                       for s in ("_summary.csv","_replays.csv","_budget_protocol.txt",
                                 "_visited_fingerprints.csv")}
                assert all(len(v)==1 for v in files.values()),(prefix,files)
                summary=read(files["_summary.csv"][0])
                replay=read(files["_replays.csv"][0])
                hashes=read(files["_visited_fingerprints.csv"][0])
                assert len(summary)==len(hashes)==4 and len(replay)==64,(prefix,len(summary),len(replay))
                assert {x["algorithm"] for x in summary}==set(ALG)
                assert {x["algorithm"] for x in hashes}==set(ALG)
                protocol=files["_budget_protocol.txt"][0].read_text()
                assert "PROSPECTIVE_REPLAY_BUDGET_K=16" in protocol
                assert "PROSPECTIVE_REPLAY_POLICY=pareto-cover" in protocol
                assert "VM_SPEED_PROFILE="+speed in protocol
                assert "VM_PRICE_PROFILE=default" in protocol
                parent=files["_summary.csv"][0].parent.parent
                log=(parent/"ci-logs/search.log").read_text()
                source=(parent/"ci-logs/source_sha.txt").read_text().strip()
                assert len(source)==40 and all(c in "0123456789abcdef" for c in source)
                loc={}
                for z in re.finditer(r"FLA_PAIRED_LOCAL mode=(\d+) trials=(\d+) changed=(\d+) dominates=(\d+) dominated=(\d+) incomparable=(\d+) evaluations=(\d+)",log):
                    vals=tuple(map(int,z.groups()))
                    assert vals[0] in (1,2) and vals[0] not in loc
                    assert vals[1]==1400 and vals[2]<=vals[1] and sum(vals[3:6])==vals[1] and vals[6]==3030
                    loc[vals[0]]=vals
                assert set(loc)=={1,2},(prefix,loc)
                for s in summary:
                    alg=s["algorithm"]
                    assert int(s["evaluations"])==int(s["captured_evaluations"])==3030
                    assert int(s["replayed"])==16
                    selected=sorted((r for r in replay if r["algorithm"]==alg),
                                    key=lambda r:int(r["candidate_index"]))
                    assert len(selected)==16 and [int(x["candidate_index"]) for x in selected]==list(range(1,17))
                    assert len({x["mapping"] for x in selected})==16
                    planned=[(float(x["planned_makespan"]),float(x["planned_cost"])) for x in selected]
                    actual=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in selected]
                    assert all(math.isfinite(v) and v>0 for p in planned+actual for v in p)
                    data[wf,speed,seed,alg]=dict(planned=planned,real=actual,
                        time=float(s["search_selection_replay_ms"]),search=float(s["search_ms"]),
                        minimum_makespan=min(x[0] for x in actual),
                        minimum_cost=min(x[1] for x in actual),
                        source=source)
                data[wf,speed,seed,"_paired"]=loc
    assert len(data)==len(WFS)*len(SPEEDS)*len(SEEDS)*5
    cases=[]
    for wf in WFS:
        for speed in SPEEDS:
            points=[p for seed in SEEDS for alg in ALG for p in data[wf,speed,seed,alg]["planned"]]
            maxima=(max(x[0] for x in points),max(x[1] for x in points))
            for factor in FACTORS:
                ref=(factor*maxima[0]+1,factor*maxima[1]+1)
                for seed in SEEDS:
                    arms=[data[wf,speed,seed,a] for a in ALG]
                    assert all(p[0]<ref[0] and p[1]<ref[1] for arm in arms for p in arm["real"]),(
                        "frozen reference excludes actual objective",wf,speed,seed,factor)
                    v=[hv(arm["real"],ref) for arm in arms]
                    assert min(v)>0
                    loc=data[wf,speed,seed,"_paired"]
                    cases.append(dict(workflow=wf,vm_speed=speed,seed=seed,reference_multiplier=factor,
                        hv_v12=v[0],hv_randompair=v[1],hv_timelinepair=v[2],hv_nsga=v[3],
                        timeline_vs_v12_pct=100*(v[2]/v[0]-1),
                        timeline_vs_random_pct=100*(v[2]/v[1]-1),
                        random_vs_v12_pct=100*(v[1]/v[0]-1),
                        timeline_vs_nsga_pct=100*(v[2]/v[3]-1),
                        timeline_wins_v12=int(v[2]>v[0]),
                        timeline_wins_random=int(v[2]>v[1]),
                        min_makespan_timeline_vs_v12_pct=100*(arms[2]["minimum_makespan"]/arms[0]["minimum_makespan"]-1),
                        min_cost_timeline_vs_v12_pct=100*(arms[2]["minimum_cost"]/arms[0]["minimum_cost"]-1),
                        timeline_local_changed=loc[2][2],
                        random_local_changed=loc[1][2],
                        timeline_local_dominates=loc[2][3],
                        random_local_dominates=loc[1][3],
                        timeline_local_dominated=loc[2][4],
                        random_local_dominated=loc[1][4],
                        timeline_runtime_ms=arms[2]["time"],
                        random_runtime_ms=arms[1]["time"],
                        v12_runtime_ms=arms[0]["time"]))
    assert len(cases)==len(WFS)*len(SPEEDS)*len(SEEDS)*len(FACTORS)
    out.mkdir(parents=True,exist_ok=True)
    with (out/"v14_search_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
    report=["# v14 counted stage-in-aware paired local search vs random pair, v12 and seeded NSGA-II",
        "","All 12 experiment cases use 3030 counted planned objective evaluations per optimizer and K=16 true WorkflowSim replays per optimizer; v14 pair modes split normal and neighbor evaluations within the SAME budget. The original v12 and cost-seeded NSGA-II do not have an added search allowance.",
        "Predeclared primary reference = 1.5× planned K16 candidate maxima +1 across all four arms and two seeds, per workflow/speed; 3× secondary, both validated against actual data without refitting.",
        "These are familiar DAG families at new size/seed profiles, NOT genuinely untouched independent workflow families.",
        "","| Workflow | VM speed | Timeline vs v12 (mean, 2 seeds) | Wins / 2 | Timeline vs RANDOM pair | Random pair vs v12 | Timeline vs NSGA-II |",
        "|---|---|---:|---:|---:|---:|---:|"]
    for wf in WFS:
        for speed in SPEEDS:
            rr=[r for r in cases if r["workflow"]==wf and r["vm_speed"]==speed and r["reference_multiplier"]==1.5]
            report.append(f"| {wf} | {speed} | {statistics.mean(r['timeline_vs_v12_pct'] for r in rr):+.4f}% | {sum(r['timeline_wins_v12'] for r in rr)}/2 | {statistics.mean(r['timeline_vs_random_pct'] for r in rr):+.4f}% | {statistics.mean(r['random_vs_v12_pct'] for r in rr):+.4f}% | {statistics.mean(r['timeline_vs_nsga_pct'] for r in rr):+.4f}% |")
    for factor in FACTORS:
        rr=[r for r in cases if r["reference_multiplier"]==factor]
        report.extend(["",f"## Pooled descriptive at {factor}x reference",
            f"Timeline vs v12: {statistics.mean(x['timeline_vs_v12_pct'] for x in rr):+.6f}% ({sum(x['timeline_wins_v12'] for x in rr)}/{len(rr)} wins).",
            f"Timeline vs random-pair: {statistics.mean(x['timeline_vs_random_pct'] for x in rr):+.6f}% ({sum(x['timeline_wins_random'] for x in rr)}/{len(rr)} wins).",
            f"Timeline vs equally seeded NSGA-II: {statistics.mean(x['timeline_vs_nsga_pct'] for x in rr):+.6f}%."])
    r=[x for x in cases if x["reference_multiplier"]==1.5]
    report.extend(["","## Pair-level correctness and Pareto direction (12 experiment cases)",
        f"Timeline changed genotypes {sum(x['timeline_local_changed'] for x in r)}/{len(r)*1400} trials, locally dominates base normal child {sum(x['timeline_local_dominates'] for x in r)} times, dominated by normal child {sum(x['timeline_local_dominated'] for x in r)} times.",
        f"Random control changed genotypes {sum(x['random_local_changed'] for x in r)}/{len(r)*1400} trials, locally dominates base normal child {sum(x['random_local_dominates'] for x in r)} times, dominated {sum(x['random_local_dominated'] for x in r)} times.",
        "Every pair still enters archive only through normal existing Pareto admission and the following global survivor selection; no uncounted objective oracle.",
        "","## Individual primary-reference comparisons (negative outcomes retained)",
        "","| DAG | VM | Seed | Timeline vs v12 | Timeline vs random | Random vs v12 | Timeline vs NSGA-II |",
        "|---|---|---:|---:|---:|---:|---:|"])
    for x in cases:
        if x["reference_multiplier"]!=1.5:continue
        report.append(f"| {x['workflow']} | {x['vm_speed']} | {x['seed']} | {x['timeline_vs_v12_pct']:+.4f}% | {x['timeline_vs_random_pct']:+.4f}% | {x['random_vs_v12_pct']:+.4f}% | {x['timeline_vs_nsga_pct']:+.4f}% |")
    report.extend(["","## Scope and scientific limitations",
      "The timeline comes from the stage-in-aware PLANNING decoder in the one normal counted evaluation; it is NOT a WorkflowSim simulator trace, and the local gap proposal is an optimistic one-gene surrogate. The second neighbor is independently counted as another optimizer evaluation.",
      "Pair search reallocates independent offspring exploration into local trials, so both direct v12 and budget-matched RANDOM pair must be reported. It does not preserve the same offspring search distribution as v12.",
      "Only 2 seeds and 3 familiar DAG families in two VM profiles: exploratory ablation, not a new publication holdout or inferential proof. Runtime is subject to runner/JIT noise. Treat negative results as decisively rejecting early promotion rather than retuning thresholds on these observed cases."])
    (out/"v14_search_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_v14_search_report.py ORIGINAL_ARTIFACT_ROOT OUTPUT_DIR")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
