#!/usr/bin/env python3
"""Read-only, source-pinned v13 negative ablation diagnosis; zero new simulator calls."""
import csv,math,pathlib,statistics,sys,re,collections
SOURCE="40c08728eae0e46e4f678781a1689ea6b4eef62f"
WFS=("CyberShake_50","Montage_50","Sipht_60")
SPEEDS=("default","staggered")
SEEDS=(141,142,143)
ALG=("DAG-Pareto-FLA[v12-hvbandit]","DAG-Pareto-FLA[v13-join]","NSGA-II[costseed]")
def read(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))
def nd(p):
    return sorted(set(q for q in p if not any((z[0]<=q[0] and z[1]<=q[1] and z!=q) for z in p)))
def dom(p,q):
    return p[0]<=q[0] and p[1]<=q[1] and (p[0]<q[0] or p[1]<q[1])
def ratio(a,b):
    if not (a>0 and b>0):raise ValueError("invalid metric")
    return 100*(a/b-1)
def run(root,out):
    results=[]
    for wf in WFS:
        for speed in SPEEDS:
            for seed in SEEDS:
                p=f"v13-search-{speed}-{wf}-s{seed}"
                files={suffix:list(root.rglob(p+suffix)) for suffix in
                    ("_summary.csv","_replays.csv","_visited_fingerprints.csv","_budget_protocol.txt")}
                assert all(len(v)==1 for v in files.values()),(p,files)
                stat=read(files["_summary.csv"][0])
                trace=read(files["_replays.csv"][0])
                assert {x["algorithm"] for x in stat}==set(ALG),p
                assert len(trace)==48,p
                logs=list(root.rglob("ci-logs/source_sha.txt"))
                # Each job artifact has its own checkout provenance.
                parent=files["_summary.csv"][0].parent.parent
                source=parent/"ci-logs/source_sha.txt"
                assert source.is_file() and source.read_text().strip()==SOURCE,(p,str(source))
                log=parent/"ci-logs/search.log"
                assert log.is_file(),p
                ms=list(re.finditer(r"FLA_JOIN_AWARE attempted=(\d+) changed=(\d+) evaluations=(\d+)",log.read_text()))
                assert len(ms)==1,(p,len(ms))
                attempts,changes,evals=(int(x) for x in ms[0].groups())
                assert evals==3030 and 0<=changes<=attempts
                data={}
                for a in ALG:
                    sc=next(x for x in stat if x["algorithm"]==a)
                    assert int(sc["evaluations"])==3030 and int(sc["replayed"])==16
                    raw=[x for x in trace if x["algorithm"]==a]
                    assert len(raw)==16
                    points=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in raw]
                    assert all(math.isfinite(v) and v>0 for p2 in points for v in p2)
                    data[a]=dict(points=points,front=nd(points),
                        minM=min(x[0] for x in points),minC=min(x[1] for x in points),
                        time=float(sc["search_selection_replay_ms"]),search=float(sc["search_ms"]))
                x,y,z=[data[a] for a in ALG]
                f12,f13=x["front"],y["front"]
                results.append(dict(workflow=wf,speed=speed,seed=seed,
                    join_attempts=attempts,join_changes=changes,activation_pct=100*changes/attempts,
                    min_makespan_change_pct=ratio(y["minM"],x["minM"]),
                    min_cost_change_pct=ratio(y["minC"],x["minC"]),
                    min_makespan_vs_nsga_pct=ratio(y["minM"],z["minM"]),
                    min_cost_vs_nsga_pct=ratio(y["minC"],z["minC"]),
                    v13_selected_front_count=len(f13),v12_selected_front_count=len(f12),
                    v13_front_dominated_by_v12_count=sum(any(dom(b,a) for b in f12) for a in f13),
                    v12_front_dominated_by_v13_count=sum(any(dom(a,b) for a in f13) for b in f12),
                    v13_selected_front_dominated_fraction=sum(any(dom(b,a) for b in f12) for a in f13)/len(f13),
                    total_runtime_change_pct=ratio(y["time"],x["time"]),
                    search_runtime_change_pct=ratio(y["search"],x["search"])))
    assert len(results)==18
    out.mkdir(parents=True,exist_ok=True)
    with (out/"v13_diagnostic_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]))
        w.writeheader();w.writerows(results)
    lines=["# v13 join operator: source-pinned independent retrospective diagnostic (no new simulations)","",
        "Original, complete 18 successful WorkflowSim job artifacts from Actions 41612325067 are consumed read-only. Every job is verified to have source SHA "+SOURCE+" and 3030 evaluations; no outcome-guided new optimizer runs or simulator calls.",
        "This is a **post-hoc diagnostic** of a rejected method. None of the present data becomes independent held-out verification for any changed future operator.","",
        "| Family | Speed | Join changes / attempts (3 seeds) | Mean min real makespan v13 vs v12 | Mean min real cost v13 vs v12 | Mean v13 front dominated by v12 | Mean total-runtime v13 vs v12 |",
        "|---|---|---:|---:|---:|---:|---:|"]
    for wf in WFS:
        for speed in SPEEDS:
            rr=[r for r in results if r["workflow"]==wf and r["speed"]==speed]
            lines.append(f"| {wf} | {speed} | {sum(r['join_changes'] for r in rr)}/{sum(r['join_attempts'] for r in rr)} | "+
                f"{statistics.mean(r['min_makespan_change_pct'] for r in rr):+.4f}% | "+
                f"{statistics.mean(r['min_cost_change_pct'] for r in rr):+.4f}% | "+
                f"{statistics.mean(r['v13_selected_front_dominated_fraction'] for r in rr):.4f} | "+
                f"{statistics.mean(r['total_runtime_change_pct'] for r in rr):+.3f}% |")
    lines.extend(["","## Pooled descriptive (18 correlated paired cases)",
        f"Actual min-makespan change (v13 vs v12): {statistics.mean(r['min_makespan_change_pct'] for r in results):+.6f}%; v13 faster in {sum(r['min_makespan_change_pct']<0 for r in results)}/18.",
        f"Actual min-cost change (v13 vs v12): {statistics.mean(r['min_cost_change_pct'] for r in results):+.6f}%; v13 cheaper in {sum(r['min_cost_change_pct']<0 for r in results)}/18.",
        f"Fraction of v13 selected nondominated candidates strictly dominated by at least one v12 selected nondominated candidate (averaged by case): {statistics.mean(r['v13_selected_front_dominated_fraction'] for r in results):.6f}.",
        f"Total runtime paired relative mean: {statistics.mean(r['total_runtime_change_pct'] for r in results):+.6f}% (GitHub runner/JIT time is noisy).",
        f"Activation: {sum(r['join_changes'] for r in results)} changed of {sum(r['join_attempts'] for r in results)} attempted; all CyberShake cases have zero changes: {all(r['join_changes']==0 for r in results if r['workflow']=='CyberShake_50')}.",
        "","## Every case including negatives","","| Family | Speed | Seed | Changed | Min makespan | Min cost | Fraction dominated by v12 | Total runtime |",
        "|---|---|---:|---:|---:|---:|---:|---:|"])
    for r in results:
        lines.append(f"| {r['workflow']} | {r['speed']} | {r['seed']} | {r['join_changes']} | {r['min_makespan_change_pct']:+.4f}% | {r['min_cost_change_pct']:+.4f}% | {r['v13_selected_front_dominated_fraction']:.3f} | {r['total_runtime_change_pct']:+.3f}% |")
    lines.extend(["","## Boundaries",
        "Pareto-front dominance and extreme objective values are computed ONLY from each arm's 16 replayed assignments, not all optimizer-visited genotypes or the true global Pareto frontier.",
        "The run-to-run timing metrics share varying JIT/runner conditions and are not controlled microbenchmarks; do not infer causal runtime speedups.",
        "This analysis reads outcomes already seen in the first 18-case pilot, so it can diagnose failure but must not be used to tune and then claim unseen validation."])
    (out/"v13_diagnostic_report.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_v13_search_diagnostics.py SOURCE_ARTIFACT_ROOT OUTPUT_DIR")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
