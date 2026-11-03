#!/usr/bin/env python3
"""Prospective K16 Pareto-cover vs extreme-first scalar-sweep using real WorkflowSim.

HV reference values were extracted from PRIOR 100-task 5-seed v12 fair
confirmation run 41572425682, artifact v12full-report-41572425682,
before the new 61..63 seed cohort. No policy is scored using a newly fit ref.
"""
import csv
import pathlib
import collections
import statistics
import math

REFS={
    "CyberShake_100": (6806.24215, 3280.0303),
    "Epigenomics_100": (211858.3560250001, 217310.76064),
    "Inspiral_100": (11044.129825, 11209.86290125),
    "Montage_100": (568.6573, 570.969505),
    "Sipht_100": (9127.960675000002, 8822.13817375),
}
SEEDS=(61,62,63)
ALGOS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
POLICIES=("pareto-cover","scalar-sweep")

def load(p):
    with p.open(newline="") as f:
        return list(csv.DictReader(f))

def front(points):
    pts=sorted(set(points))
    low=float("inf")
    out=[]
    for m,c in pts:
        if c<low:
            out.append((m,c))
            low=c
    return out

def hv(points,ref):
    area,last=0.,ref[1]
    for m,c in front(points):
        if m<ref[0] and c<last:
            area+=(ref[0]-m)*(last-c)
            last=c
    return area

def run(root,dest):
    expected={(w,s,p) for w in REFS for s in SEEDS for p in POLICIES}
    histories={}
    sim={}
    for wf,seed,policy in sorted(expected):
        p=root/(policy+"_"+wf+"_s"+str(seed))
        # Matrix artifacts are nested by download-artifact; locate uniquely.
        a=list(root.rglob(p.name+"_summary.csv"))
        b=list(root.rglob(p.name+"_replays.csv"))
        assert len(a)==len(b)==1,(wf,seed,policy,a,b)
        summary=load(a[0]);replays=load(b[0])
        assert len(summary)==3 and {r["algorithm"] for r in summary}==set(ALGOS)
        assert len(replays)==48
        for r in summary:
            assert int(r["evaluations"])==int(r["captured_evaluations"])==3030
            assert int(r["replayed"])==16
            histories[(wf,seed,policy,r["algorithm"])]=(
                r["source_archive"],r["distinct_observed"],r["distinct_planned_nondominated"])
        for r in replays:
            alg=r["algorithm"]
            assert alg in ALGOS
            m,c=float(r["sim_makespan"]),float(r["sim_cost"])
            assert math.isfinite(m) and math.isfinite(c) and m>0 and c>0
            sim.setdefault((wf,seed,policy,alg),[]).append((m,c))
    assert len(sim)==len(histories)==len(expected)*len(ALGOS)
    assert all(len(x)==16 for x in sim.values())
    score_rows=[]
    paired=[]
    for wf in sorted(REFS):
        for seed in SEEDS:
            for alg in ALGOS:
                assert histories[(wf,seed,POLICIES[0],alg)]==histories[(wf,seed,POLICIES[1],alg)],(wf,seed,alg)
                score={}
                for policy in POLICIES:
                    pts=sim[wf,seed,policy,alg]
                    score[policy]=hv(pts,REFS[wf])
                    score_rows.append(dict(workflow=wf,seed=seed,algorithm=alg,policy=policy,
                        evaluations=3030,replay_k=16,sim_hv=score[policy],
                        min_sim_makespan=min(x[0] for x in pts),min_sim_cost=min(x[1] for x in pts),
                        ref_m=REFS[wf][0],ref_c=REFS[wf][1]))
                a,b=score[POLICIES[0]],score[POLICIES[1]]
                paired.append(dict(workflow=wf,seed=seed,algorithm=alg,cover_hv=a,sweep_hv=b,
                    cover_minus_sweep_hv=a-b,cover_gain_pct=100*(a/max(1e-12,b)-1),
                    cover_wins=int(a>b),sweep_wins=int(b>a),
                    cover_min_makespan=min(x[0] for x in sim[wf,seed,POLICIES[0],alg]),
                    sweep_min_makespan=min(x[0] for x in sim[wf,seed,POLICIES[1],alg]),
                    cover_min_cost=min(x[1] for x in sim[wf,seed,POLICIES[0],alg]),
                    sweep_min_cost=min(x[1] for x in sim[wf,seed,POLICIES[1],alg])))
    report=["# Equal real K16 WorkflowSim: planned Pareto coverage versus extreme-first scalar sweep",
        "",
        "New optimizer seeds 61,62,63 on five different 100-task DAG families. Each solver/policy case has identical initial cost seeds, 3030 actual planning objective evaluations and 16 independent simulator replays.",
        "Both policies select from the same evaluated genotype history using PLANNED objectives only; neither accesses true simulator values before selecting.",
        "Scalar-sweep protects minimum planned cost and minimum planned makespan, then uses deterministic Van der Corput weights. Pareto-cover uses planned Pareto layers and max-min spacing.",
        "The same fixed per-family HV references were established in an EARLIER run 41572425682 (5-seed 100-task full fairness), not recomputed from any of these new 61..63 seed results.",
        "No full-history oracle is simulated in this comparison.",
        "",
        "| Algorithm | Mean paired cover vs scalar HV advantage | Pareto-cover wins | Sweep wins |",
        "|---|---:|---:|---:|"]
    for alg in ALGOS:
        obs=[r for r in paired if r["algorithm"]==alg]
        report.append(f"| {alg} | {statistics.mean(r['cover_gain_pct'] for r in obs):+.3f}% | "
                      f"{sum(r['cover_wins'] for r in obs)}/{len(obs)} | {sum(r['sweep_wins'] for r in obs)}/{len(obs)} |")
    report += ["","## Per-family paired comparisons",
        "",
        "| Family | Algorithm | Mean cover vs scalar HV advantage | Cover wins |",
        "|---|---|---:|---:|"]
    for wf in sorted(REFS):
        for alg in ALGOS:
            obs=[r for r in paired if r["workflow"]==wf and r["algorithm"]==alg]
            report.append(f"| {wf} | {alg} | {statistics.mean(r['cover_gain_pct'] for r in obs):+.3f}% | "
                          f"{sum(r['cover_wins'] for r in obs)}/{len(obs)} |")
    report += ["","## Limits",
        "The HV references are pre-frozen against this cohort, but are inherited from earlier tested seeds and not externally determined optimization targets.",
        "The 45 algorithm-case observations are correlated within 15 workflow-seed cases and just five DAG families; do not infer significance by treating them as independent.",
        "Preliminary 100-task-scale search results are sensitive to workflow family and evaluation-model fidelity. A screening win is NOT proof of FLA v12 vs NSGA-II superiority.",
        "The scalar policy is a serious, deterministic two-extreme heuristic; any negative Pareto-cover results must be kept. Both policies may have different wall-clock selection overhead despite equal 16 simulator calls."]
    dest.mkdir(parents=True,exist_ok=True)
    for name,rows in (("scalar_k16_scores.csv",score_rows),("scalar_k16_paired.csv",paired)):
        with (dest/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (dest/"scalar_k16_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    import sys
    if len(sys.argv)!=3:
        raise SystemExit("usage: fla_scalar_sweep_control.py ARTIFACT_ROOT REPORT_FOLDER")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
