#!/usr/bin/env python3
"""Locked prospective v12 vs v13 vs matched cost-seeded NSGA-II: true K16 HV."""
import csv,math,pathlib,statistics,sys
WORKFLOWS=("CyberShake_50","Montage_50","Sipht_60")
SEEDS=(141,142,143)
SPEEDS=("default","staggered")
ALG=("DAG-Pareto-FLA[v12-hvbandit]","DAG-Pareto-FLA[v13-join]","NSGA-II[costseed]")
SCALES=(1.5,3.0)
def read(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))
def hv(p,ref):
    total,last=0.,ref[1]
    for m,c in sorted(set(p)):
        if m<ref[0] and c<last:
            total+=(ref[0]-m)*(last-c);last=c
    return total
def run(root,out):
    dat={}
    for wf in WORKFLOWS:
        for speed in SPEEDS:
            for seed in SEEDS:
                pref=f"v13-search-{speed}-{wf}-s{seed}"
                files={s:list(root.rglob(pref+s)) for s in ("_summary.csv","_replays.csv","_visited_fingerprints.csv","_budget_protocol.txt")}
                assert all(len(x)==1 for x in files.values()),(pref,files)
                stats=read(files["_summary.csv"][0]); replay=read(files["_replays.csv"][0])
                history=read(files["_visited_fingerprints.csv"][0])
                assert len(stats)==len(history)==3 and len(replay)==48
                assert {x["algorithm"] for x in stats}==set(ALG)
                assert {x["algorithm"] for x in history}==set(ALG)
                protocol=files["_budget_protocol.txt"][0].read_text()
                assert "PROSPECTIVE_REPLAY_BUDGET_K=16" in protocol and "PROSPECTIVE_REPLAY_POLICY=pareto-cover" in protocol
                assert "VM_SPEED_PROFILE="+speed in protocol
                for s in stats:
                    alg=s["algorithm"]
                    assert int(s["evaluations"])==int(s["captured_evaluations"])==3030
                    assert int(s["replayed"])==16
                    selected=sorted((x for x in replay if x["algorithm"]==alg),key=lambda x:int(x["candidate_index"]))
                    assert len(selected)==16 and len({x["mapping"] for x in selected})==16
                    assert [int(x["candidate_index"]) for x in selected]==list(range(1,17))
                    planned=[(float(x["planned_makespan"]),float(x["planned_cost"])) for x in selected]
                    actual=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in selected]
                    assert all(math.isfinite(z) and z>0 for pair in planned+actual for z in pair)
                    dat[wf,speed,seed,alg]=dict(planned=planned,actual=actual,time=float(s["search_selection_replay_ms"]),
                      minimum_makespan=min(x[0] for x in actual),minimum_cost=min(x[1] for x in actual))
    cases=[]
    for wf in WORKFLOWS:
        for speed in SPEEDS:
            pool=[x for seed in SEEDS for a in ALG for x in dat[wf,speed,seed,a]["planned"]]
            maxima=(max(x[0] for x in pool),max(x[1] for x in pool))
            for factor in SCALES:
                ref=(factor*maxima[0]+1,factor*maxima[1]+1)
                assert all(m<ref[0] and c<ref[1] for seed in SEEDS for alg in ALG
                    for m,c in dat[wf,speed,seed,alg]["actual"]),("bad frozen ref",wf,speed,factor)
                for seed in SEEDS:
                    v12,v13,nsga=[dat[wf,speed,seed,a] for a in ALG]
                    h12,h13,hn=[hv(o["actual"],ref) for o in (v12,v13,nsga)]
                    assert min(h12,h13,hn)>0
                    cases.append(dict(workflow=wf,speed=speed,seed=seed,ref_factor=factor,
                        hv_v12=h12,hv_v13=h13,hv_nsga=hn,
                        v13_vs_v12_pct=100*(h13/h12-1),v13_vs_nsga_pct=100*(h13/hn-1),
                        v12_vs_nsga_pct=100*(h12/hn-1),v13_wins_v12=int(h13>h12),
                        min_makespan_v12=v12["minimum_makespan"],min_makespan_v13=v13["minimum_makespan"],
                        min_makespan_nsga=nsga["minimum_makespan"],min_cost_v12=v12["minimum_cost"],
                        min_cost_v13=v13["minimum_cost"],min_cost_nsga=nsga["minimum_cost"],
                        time_ms_v12=v12["time"],time_ms_v13=v13["time"],time_ms_nsga=nsga["time"]))
    assert len(cases)==len(WORKFLOWS)*len(SPEEDS)*len(SEEDS)*len(SCALES)
    out.mkdir(parents=True,exist_ok=True)
    with (out/"v13_search_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
    lines=["# v13 join-aware search operator: prospectively fixed development 18-case actual WorkflowSim K16 comparison","",
        "Same seeded initialization (asserted in every solver run), 3030 planner objective calls, K16 actual WorkflowSim replays and unchanged pareto-cover selection per algorithm; 3 previously studied DAG families × 2 VM-speed regimes × 3 optimizer seeds. Not independent new workflow families.",
        "Primary reference = 1.5× per-coordinate planned candidate maximum +1 across the 3 solver arms and 3 seeds within each workflow/speed. Secondary reference 3×; both require every real result inside. No actual simulator outcome is used in reference construction.","",
        "| Workflow | VM speed | v13 vs v12 HV (mean, 3 seeds) | Wins / 3 | v13 vs NSGA-II HV (mean) | v12 vs NSGA-II HV (mean) |",
        "|---|---|---:|---:|---:|---:|"]
    for wf in WORKFLOWS:
        for speed in SPEEDS:
            rr=[x for x in cases if x["workflow"]==wf and x["speed"]==speed and x["ref_factor"]==1.5]
            lines.append(f"| {wf} | {speed} | {statistics.mean(x['v13_vs_v12_pct'] for x in rr):+.4f}% | {sum(x['v13_wins_v12'] for x in rr)}/3 | {statistics.mean(x['v13_vs_nsga_pct'] for x in rr):+.4f}% | {statistics.mean(x['v12_vs_nsga_pct'] for x in rr):+.4f}% |")
    for factor in SCALES:
        rr=[x for x in cases if x["ref_factor"]==factor]
        lines.extend(["",f"## Aggregate reference {factor}x",
            f"v13 vs v12 mean paired: {statistics.mean(x['v13_vs_v12_pct'] for x in rr):+.6f}% across {len(rr)} paired scenario seeds, v13 wins {sum(x['v13_wins_v12'] for x in rr)}/{len(rr)}.",
            f"v13 vs cost-seeded NSGA-II mean paired: {statistics.mean(x['v13_vs_nsga_pct'] for x in rr):+.6f}%."])
    lines.extend(["","## Every primary-reference case (including negative results)","",
      "| Workflow | Speed | Seed | v13 vs v12 | v13 vs NSGA-II | v12 vs NSGA-II |",
      "|---|---|---:|---:|---:|---:|"])
    for x in cases:
        if x["ref_factor"]!=1.5:continue
        lines.append(f"| {x['workflow']} | {x['speed']} | {x['seed']} | {x['v13_vs_v12_pct']:+.4f}% | {x['v13_vs_nsga_pct']:+.4f}% | {x['v12_vs_nsga_pct']:+.4f}% |")
    lines.extend(["","## Caution","This is an exploratory DEVELOPMENT ablation on previously seen DAG families. One manually chosen v13 operator and only three seeds per family/speed are insufficient for algorithm generalization or statistical superiority. Observed outcomes concern selected K16 true simulated points, not all visited genotypes. Equal fitness calls do not imply equal wall-clock. The v13 arm is postulated, not an original continuous FLA rule. Do not promote unless independent new DAG/VM tests support it."])
    (out/"v13_search_report.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_v13_search_report.py ARTIFACT_ROOT OUTPUT_DIR")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
