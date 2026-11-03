#!/usr/bin/env python3
"""Read-only common-reference true K16 HV: FLA v12 vs v18 vs seeded NSGA-II.

All three solvers are from SAME original run per DAG/seed, and are compared
under the same 1.5x and 3.0x union-of-real-values references. No retuning.
"""
import csv
import math
import pathlib
import re
import statistics
import sys

WORKFLOWS=("CyberShake_50","Montage_50")
SEEDS=(211,212)
ARMS=("DAG-Pareto-FLA[v12-hvbandit]",
      "DAG-Pareto-FLA[v18-disagreement]","NSGA-II[costseed]")

def csvrows(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def non_dominated(points):
    pts=sorted(set(points))
    return [p for p in pts if not any(
        q[0]<=p[0] and q[1]<=p[1] and q!=p for q in pts)]

def normal_hv(points,reference):
    m,c=reference
    front=non_dominated([p for p in points if p[0]<m and p[1]<c])
    area=0.0;prior_c=c
    for time,price in front:
        if price>=prior_c:continue
        area+=(m-time)*(prior_c-price)
        prior_c=price
    return area/(m*c)

def audit(root,out):
    out.mkdir(parents=True,exist_ok=True)
    blocks={}
    for dir in root.iterdir():
        if not dir.is_dir() or not (dir/"block-id.txt").exists():continue
        src=dict(x.split("=",1) for x in (dir/"block-id.txt").read_text().split())
        wf=src["DAG"];seed=int(src["seed"])
        if wf not in WORKFLOWS or seed not in SEEDS or (wf,seed) in blocks:
            raise AssertionError(("unregistered or duplicated block",wf,seed))
        summaries=csvrows(dir/"research_summary.csv")
        replays=csvrows(dir/"research_replays.csv")
        assert len(summaries)==3 and len(replays)==48
        assert {x["algorithm"] for x in summaries}==set(ARMS)
        experiment=(dir/"experiment.log").read_text()
        matches=re.findall(r"V18_DISAGREEMENT proposals=(\d+) actualRelocations=(\d+)",experiment)
        assert len(matches)==1
        proposals,moves=map(int,matches[0])
        assert proposals>0 and moves<=proposals
        arms={}
        for s in summaries:
            a=s["algorithm"]
            assert all(int(s[x])==value for x,value in
                (("evaluations",3030),("captured_evaluations",3030),("replayed",16)))
            z=sorted((r for r in replays if r["algorithm"]==a),
                     key=lambda r:int(r["candidate_index"]))
            assert len(z)==len({r["mapping"] for r in z})==16
            assert [int(r["candidate_index"]) for r in z]==list(range(1,17))
            points=[(float(r["sim_makespan"]),float(r["sim_cost"])) for r in z]
            assert all(math.isfinite(v) and v>0 for pair in points for v in pair)
            arms[a]=dict(points=points,search_ms=float(s["search_ms"]),
                         true_nd=len(non_dominated(points)),
                         replay_ms=float(s["replay_ms"]))
        allpoints=[p for a in ARMS for p in arms[a]["points"]]
        m=max(x for x,y in allpoints);c=max(y for x,y in allpoints)
        for a in ARMS:
            arms[a]["hv15"]=normal_hv(arms[a]["points"],(1.5*m+1e-6,1.5*c+1e-6))
            arms[a]["hv30"]=normal_hv(arms[a]["points"],(3*m+1e-6,3*c+1e-6))
        blocks[(wf,seed)]=dict(arms=arms,proposals=proposals,moves=moves)
    if set(blocks)!={(wf,seed) for wf in WORKFLOWS for seed in SEEDS}:
        raise AssertionError(("missing source DAG/seed blocks",blocks.keys()))
    rows=[]
    for (wf,seed),block in sorted(blocks.items()):
        baseline=block["arms"][ARMS[0]]
        experimental=block["arms"][ARMS[1]]
        baseline_nsga=block["arms"][ARMS[2]]
        rows.append(dict(workflow=wf,seed=seed,
          v12_hv15=baseline["hv15"],v18_hv15=experimental["hv15"],
          nsga_hv15=baseline_nsga["hv15"],
          delta_hv15=experimental["hv15"]-baseline["hv15"],
          delta_hv30=experimental["hv30"]-baseline["hv30"],
          v12_search_ms=baseline["search_ms"],v18_search_ms=experimental["search_ms"],
          nsga_search_ms=baseline_nsga["search_ms"],
          v18_v12_search_time_ratio=experimental["search_ms"]/baseline["search_ms"],
          v18_proposals=block["proposals"],v18_actual_moves=block["moves"],
          v12_true_nd=baseline["true_nd"],v18_true_nd=experimental["true_nd"],
          nsga_true_nd=baseline_nsga["true_nd"]))
    with (out/"all_block_hv.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    win=sum(r["delta_hv15"]>1e-9 for r in rows)
    tied=sum(abs(r["delta_hv15"])<=1e-9 for r in rows)
    lost=len(rows)-win-tied
    report=["# v18 disagreement-targeted FLA operator versus v12 and seeded NSGA-II",
      "", "Original optimizer and simulator source Actions 41674106990: 4 blocks × 3 algorithms × 3030 objective genotype decodes × K16 real WorkflowSim replay calls = 192 actual simulator calls.",
      "All true simulator HVs are normalized against a single union 1.5× reference within each 3-arm DAG/seed block, with independent 3× sensitivity.",
      "",
      "| DAG | Seed | FLA-v12 true HV | FLA-v18 true HV | Cost-seeded NSGA-II true HV | v18−v12 Δ HV | v18−v12 Δ at 3.0× | v18/v12 search time | Relocation moves/proposals |",
      "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        report.append(f"| {r['workflow']} | {r['seed']} | {r['v12_hv15']:.8f} | "
           f"{r['v18_hv15']:.8f} | {r['nsga_hv15']:.8f} | "
           f"{r['delta_hv15']:+.8f} | {r['delta_hv30']:+.8f} | "
           f"{r['v18_v12_search_time_ratio']:.2f}× | "
           f"{r['v18_actual_moves']}/{r['v18_proposals']} |")
    report+=["",f"FLA-v18 paired wins/ties/losses: **{win}/{tied}/{lost}**; "
       f"mean Δ normalized HV = **{statistics.mean(r['delta_hv15'] for r in rows):+.8f}**; "
       f"mean search-time multiplier **{statistics.mean(r['v18_v12_search_time_ratio'] for r in rows):.2f}×**.",
       "",
       "## Limitations and acceptance gates",
       "The additional two model predictions for proposal targeting are NOT counted as objective calls; elapsed time and actual operator activations are reported separately.",
       "Both FLA versions and NSGA-II use exactly the same ORIGINAL stage-in-aware fitness model. Only the FLA-v18 proposal operator differs from FLA-v12.",
       "K16 real replays are planned-cover-selected subsets of a 3030-evaluation history and not full true Pareto fronts. No prior real labels affect selection.",
       "Four blocks from two known DAG families and two seeds are insufficient for significance or publication. Positive means development promise only; negative falsifies this particular v18 proposal.",
       "Do not change default FLA, baseline NSGA-II, or master based on this limited gate."]
    (out/"v18_true_hv_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: script.py ORIGINAL_ARTIFACT_ROOT OUTPUT_DIR")
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
