#!/usr/bin/env python3
"""Prespecified six-arm v16 bandit opportunity sham test, real K16 WorkflowSim."""
import csv,math,pathlib,re,statistics,sys
DAGS=("Montage_25","CyberShake_30")
SPEEDS=("default","staggered")
SEEDS=(181,182)
ALG=("DAG-Pareto-FLA[v12-hvbandit]",
"DAG-Pareto-FLA[v16-shamrandom]","DAG-Pareto-FLA[v14-randompair]",
"DAG-Pareto-FLA[v16-shamtimeline]","DAG-Pareto-FLA[v14-timelinepair]",
"NSGA-II[costseed]")
REFS=(1.5,3.0)
def read(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))
def hv(pts,ref):
    total,last=0.,ref[1]
    for m,c in sorted(set(pts)):
        if m<ref[0] and c<last:
            total+=(ref[0]-m)*(last-c);last=c
    return total
def run(root,out):
    data={}
    for dag in DAGS:
      for speed in SPEEDS:
       for seed in SEEDS:
        prefix=f"v16-opportunity-{speed}-{dag}-s{seed}"
        paths={s:list(root.rglob(prefix+s)) for s in ("_summary.csv","_replays.csv","_population_diagnostics.csv","_budget_protocol.txt","_visited_fingerprints.csv")}
        assert all(len(v)==1 for v in paths.values()),(prefix,paths)
        summary=read(paths["_summary.csv"][0]);replay=read(paths["_replays.csv"][0])
        trace=read(paths["_population_diagnostics.csv"][0]);hist=read(paths["_visited_fingerprints.csv"][0])
        assert len(summary)==len(hist)==6 and len(replay)==96 and len(trace)==505,(prefix,len(summary),len(replay),len(trace))
        assert {x["algorithm"] for x in summary}==set(ALG)
        protocol=paths["_budget_protocol.txt"][0].read_text()
        assert "PROSPECTIVE_REPLAY_BUDGET_K=16" in protocol
        assert "PROSPECTIVE_REPLAY_POLICY=pareto-cover" in protocol
        assert "VM_SPEED_PROFILE="+speed in protocol
        assert "VM_PRICE_PROFILE=default" in protocol
        jobroot=paths["_summary.csv"][0].parent.parent
        source=(jobroot/"ci-logs/source_sha.txt").read_text().strip()
        assert len(source)==40
        log=(jobroot/"ci-logs/search.log").read_text()
        matches=[tuple(map(int,x)) for x in re.findall(
            r"FLA_PAIRED_LOCAL mode=(\d+) trials=(\d+) changed=(\d+) dominates=(\d+) dominated=(\d+) incomparable=(\d+) gate=(\d+) rejected=(\d+) evaluations=(\d+)",log)]
        assert len(matches)==4 and {x[0] for x in matches}=={1,2,3,4},(prefix,matches)
        for mode,n,changed,win,lose,other,gate,rejected,ev in matches:
            assert n==1400 and ev==3030 and gate==0 and rejected==0
            assert win+lose+other==1400
            if mode in (3,4):
                assert changed==0 and win==0 and lose==0 and other==1400
            else:assert changed==1400
        for alg in ALG:
            x=next(r for r in summary if r["algorithm"]==alg)
            assert int(x["evaluations"])==int(x["captured_evaluations"])==3030
            assert int(x["replayed"])==16
            rr=sorted((r for r in replay if r["algorithm"]==alg),key=lambda r:int(r["candidate_index"]))
            assert len(rr)==16 and [int(r["candidate_index"]) for r in rr]==list(range(1,17))
            assert len({r["mapping"] for r in rr})==16
            planned=[(float(r["planned_makespan"]),float(r["planned_cost"])) for r in rr]
            real=[(float(r["sim_makespan"]),float(r["sim_cost"])) for r in rr]
            assert all(math.isfinite(v) and v>0 for z in planned+real for v in z)
            if not alg.startswith("NSGA-II"):
                tt=[z for z in trace if z["algorithm"]==alg]
                assert len(tt)==101
                assert [int(float(z["objective_evaluations"])) for z in tt]==[30*(i+1) for i in range(101)]
                use=sum(sum(int(float(z[k])) for k in ("bandit_baseline_uses","bandit_colocate_uses","bandit_critical_uses")) for z in tt)
                assert use==(3000 if alg==ALG[0] else 1600),(prefix,alg,use)
                meanham=statistics.mean(float(z["pairwise_hamming_all"]) for z in tt[1:])
                meanarchive=statistics.mean(float(z["archive_insert_events"]) for z in tt[1:])
            else:use=0;meanham=float("nan");meanarchive=float("nan")
            data[dag,speed,seed,alg]=dict(planned=planned,real=real,bandit_uses=use,
                mean_hamming=meanham,mean_archive_insertions=meanarchive,
                search_ms=float(x["search_ms"]))
    cases=[]
    for dag in DAGS:
      for speed in SPEEDS:
        pool=[z for seed in SEEDS for alg in ALG for z in data[dag,speed,seed,alg]["planned"]]
        mx=(max(z[0] for z in pool),max(z[1] for z in pool))
        for factor in REFS:
         ref=(factor*mx[0]+1,factor*mx[1]+1)
         for seed in SEEDS:
            arms=[data[dag,speed,seed,alg] for alg in ALG]
            assert all(x<ref[0] and y<ref[1] for arm in arms for x,y in arm["real"]),(
               "Invalid frozen planned-only reference",dag,speed,seed,factor)
            scores=[hv(arm["real"],ref) for arm in arms]
            assert min(scores)>0
            diff=lambda i,j:100*(scores[i]/scores[j]-1)
            cases.append(dict(workflow=dag,speed=speed,seed=seed,reference=factor,
                sham_random_vs_v12_pct=diff(1,0),sham_timeline_vs_v12_pct=diff(3,0),
                active_random_vs_sham_random_pct=diff(2,1),
                active_timeline_vs_sham_timeline_pct=diff(4,3),
                active_random_vs_v12_pct=diff(2,0),
                active_timeline_vs_v12_pct=diff(4,0),
                active_timeline_vs_active_random_pct=diff(4,2),
                active_timeline_vs_nsga_pct=diff(4,5),
                sham_timeline_vs_nsga_pct=diff(3,5),
                random_active_improves_sham=int(scores[2]>scores[1]),
                timeline_active_improves_sham=int(scores[4]>scores[3]),
                timeline_active_beats_v12=int(scores[4]>scores[0]),
                v12_hv=scores[0],shamrandom_hv=scores[1],random_hv=scores[2],
                shamtimeline_hv=scores[3],timeline_hv=scores[4],nsga_hv=scores[5],
                sham_timeline_hamming=arms[3]["mean_hamming"],timeline_hamming=arms[4]["mean_hamming"],
                sham_timeline_archive_admissions=arms[3]["mean_archive_insertions"],
                timeline_archive_admissions=arms[4]["mean_archive_insertions"]))
    assert len(cases)==16
    out.mkdir(parents=True,exist_ok=True)
    with (out/"v16_opportunity_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
    lines=["# v16 FLA normal-offspring opportunity: counted sham pair negative-control experiment","",
        "Eight development blocks: Montage_25/CyberShake_30 × default/staggered VM × seeds 181,182, all six arms. 3030 counted planner calls, 16 actual WorkflowSim replayed assignments per arm, identical first two deterministic low-cost starts. Unchanged original Pareto-cover replay selection. NO paper-level independence claim.",
        "Sham controls consume a real fitness call and the neighbor proposal RNG path but evaluate the already evaluated normal child; 1400 scored sham neighbors per arm add zero new genotype information. v12 uses 3000 FLA bandit-arm opportunities after initialization, while all paired arms use 1600 opportunities and allocate 1400 calls to pair trial/sham.",
        "Common 1.5× and 3× references are fixed exclusively by PLANNED selected K16 maxima across all six algorithms and both seeds per DAG/speed +1. Fail if real outcomes leave the reference; do not refit.","",
        "| Workflow | VM | Sham random vs v12 | Active random vs sham | Sham timeline vs v12 | Active timeline vs sham | Active timeline vs v12 | Active timeline vs seeded NSGA-II |",
        "|---|---|---:|---:|---:|---:|---:|"]
    for dag in DAGS:
     for speed in SPEEDS:
        rr=[x for x in cases if x["workflow"]==dag and x["speed"]==speed and x["reference"]==1.5]
        cols=("sham_random_vs_v12_pct","active_random_vs_sham_random_pct",
              "sham_timeline_vs_v12_pct","active_timeline_vs_sham_timeline_pct",
              "active_timeline_vs_v12_pct","active_timeline_vs_nsga_pct")
        lines.append("| "+dag+" | "+speed+" | "+" | ".join(f"{statistics.mean(z[c] for z in rr):+.4f}%" for c in cols)+" |")
    for factor in REFS:
        rr=[x for x in cases if x["reference"]==factor]
        lines+=["",f"## {factor}× reference pooled, {len(rr)} paired scenario seeds"]
        for key in ("sham_random_vs_v12_pct","sham_timeline_vs_v12_pct",
          "active_random_vs_sham_random_pct","active_timeline_vs_sham_timeline_pct",
          "active_timeline_vs_v12_pct","active_timeline_vs_nsga_pct"):
            lines.append(f"- {key}: {statistics.mean(x[key] for x in rr):+.6f}%.")
        lines.append(f"Random active beats sham: {sum(x['random_active_improves_sham'] for x in rr)}/{len(rr)}; timeline active beats sham: {sum(x['timeline_active_improves_sham'] for x in rr)}/{len(rr)}.")
    lines+=["","## All primary-reference case outcomes (negative results retained)","",
       "| Workflow | VM | Seed | Timeline sham vs v12 | Timeline active vs sham | Timeline active vs v12 | Timeline active vs NSGA-II |",
       "|---|---|---:|---:|---:|---:|---:|"]
    for x in cases:
      if x["reference"]==1.5:
        lines.append(f"| {x['workflow']} | {x['speed']} | {x['seed']} | {x['sham_timeline_vs_v12_pct']:+.4f}% | {x['active_timeline_vs_sham_timeline_pct']:+.4f}% | {x['active_timeline_vs_v12_pct']:+.4f}% | {x['active_timeline_vs_nsga_pct']:+.4f}% |")
    lines+=["","## Causal limits",
      "The sham design identifies the *combined* cost of reduced independent FLA proposals and uninformative duplicate calls. It does not separately identify effects of losing the phase-bandit credit from those of reduced search breadth. The active paired trial causes a new evolutionary path; matched first seeds and equal numbers of calls do not imply later normal-child trajectories are matched.",
      "Cross-arm descriptive associations are not publication-grade claims of superiority. Two seeds on familiar DAG families are insufficient for generality. Time and memory overhead of exact Hamming trace should be measured separately; instrumentation ON/OFF has already been shown source-neutral."]
    (out/"v16_opportunity_report.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_v16_opportunity_report.py ARTIFACT_ROOT OUTPUT_DIRECTORY")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
