#!/usr/bin/env python3
"""Frozen four-arm v17 synthetic-wide/deep prospective topology test."""
import csv,pathlib,math,statistics,sys,re
DAGS=("SynthNewWide_60","SynthNewDeep_60")
SPEED=("default","staggered")
SEEDS=(301,302,303)
ALG=("DAG-Pareto-FLA[v12-hvbandit]","DAG-Pareto-FLA[v17-do-random]","DAG-Pareto-FLA[v17-late-random]","NSGA-II[costseed]")
def rows(p):
 with p.open(newline="") as f:return list(csv.DictReader(f))
def hv(points,ref):
 total=0.;last=ref[1]
 for m,c in sorted(set(points)):
  if m<ref[0] and c<last:
   total+=(ref[0]-m)*(last-c);last=c
 return total
def main(root,out):
 data={}
 for dag in DAGS:
  for speed in SPEED:
   for seed in SEEDS:
    pref=f"v17-synthetic-{speed}-{dag}-s{seed}"
    fs={suffix:list(root.rglob(pref+suffix)) for suffix in ("_summary.csv","_replays.csv","_budget_protocol.txt","_population_diagnostics.csv")}
    assert all(len(x)==1 for x in fs.values()),(pref,fs)
    st=rows(fs["_summary.csv"][0]);rr=rows(fs["_replays.csv"][0]);tr=rows(fs["_population_diagnostics.csv"][0])
    assert len(st)==4 and len(rr)==64 and len(tr)==303
    assert {x["algorithm"] for x in st}==set(ALG)
    pt=fs["_budget_protocol.txt"][0].read_text()
    assert "PROSPECTIVE_REPLAY_BUDGET_K=16" in pt
    assert "PROSPECTIVE_REPLAY_POLICY=pareto-cover" in pt
    assert "VM_SPEED_PROFILE="+speed in pt
    job=fs["_summary.csv"][0].parent.parent
    assert (job/"ci-logs/source_sha.txt").is_file()
    log=(job/"ci-logs/experiment.log").read_text()
    windows=[tuple(map(int,x)) for x in re.findall(r"FLA_PAIRED_WINDOW mode=(\d+) activeGenerations=(\d+) localTrials=(\d+) normalBanditSlots=(\d+)",log)]
    assert sorted(windows)==[(1,74,1036,1964),(2,74,1036,1964)],(pref,windows)
    for alg in ALG:
     row=next(x for x in st if x["algorithm"]==alg)
     assert int(row["evaluations"])==int(row["captured_evaluations"])==3030
     assert int(row["replayed"])==16
     outrows=sorted((x for x in rr if x["algorithm"]==alg),key=lambda x:int(x["candidate_index"]))
     assert len(outrows)==16 and [int(x["candidate_index"]) for x in outrows]==list(range(1,17))
     assert len({x["mapping"] for x in outrows})==16
     plan=[(float(x["planned_makespan"]),float(x["planned_cost"])) for x in outrows]
     actual=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in outrows]
     assert all(math.isfinite(v) and v>0 for pair in plan+actual for v in pair)
     if not alg.startswith("NSGA-II"):
      t=[x for x in tr if x["algorithm"]==alg]
      assert len(t)==101
      uses=sum(int(float(x[k])) for x in t for k in ("bandit_baseline_uses","bandit_colocate_uses","bandit_critical_uses"))
      assert uses==(3000 if alg==ALG[0] else 1964),(pref,alg,uses)
     data[dag,speed,seed,alg]=dict(plan=plan,actual=actual,min_m=min(x[0] for x in actual),min_c=min(x[1] for x in actual),time=float(row["search_ms"]))
 cases=[]
 for dag in DAGS:
  for speed in SPEED:
   pool=[x for seed in SEEDS for alg in ALG for x in data[dag,speed,seed,alg]["plan"]]
   refmax=(max(x[0] for x in pool),max(x[1] for x in pool))
   for factor in (1.5,3.0):
    ref=(factor*refmax[0]+1,factor*refmax[1]+1)
    for seed in SEEDS:
     arm=[data[dag,speed,seed,x] for x in ALG]
     assert all(x<ref[0] and y<ref[1] for a in arm for x,y in a["actual"]),("invalid preregistered planned ref",dag,speed,seed,factor)
     val=[hv(x["actual"],ref) for x in arm]
     assert min(val)>0
     pct=lambda a,b:100*(val[a]/val[b]-1)
     cases.append(dict(workflow=dag,speed=speed,seed=seed,ref_factor=factor,
      do_vs_late_pct=pct(1,2),do_vs_v12_pct=pct(1,0),do_vs_nsga_pct=pct(1,3),
      do_beats_late=int(val[1]>val[2]),do_beats_v12=int(val[1]>val[0]),do_beats_nsga=int(val[1]>val[3]),
      min_makespan_do=arm[1]["min_m"],min_makespan_v12=arm[0]["min_m"],
      min_cost_do=arm[1]["min_c"],min_cost_v12=arm[0]["min_c"],
      search_ms_do=arm[1]["time"],search_ms_v12=arm[0]["time"],
      hv_v12=val[0],hv_do=val[1],hv_late=val[2],hv_nsga=val[3]))
 assert len(cases)==24
 out.mkdir(parents=True,exist_ok=True)
 with (out/"v17_synthetic_cases.csv").open("w",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
 lines=["# Frozen v17 DO-only random on newly generated wide and deep synthetic DAG topologies","",
 "Two newly generated synthetic DAG topologies each with 60 jobs, two VM regimes, and three frozen NEW seeds: 12 matched blocks and four solver arms. These are not real scientific application families. Each arm exactly 3030 planner target evaluations and K16 actual WorkflowSim replays. DO and late each 1036 neighbor probes and 1964 normal FLA offspring. Common PLANNED-only reference within each workflow/VM over all four arms and two seeds; 1.5x+1 primary, 3x+1 sensitivity. If any actual point violates it, fail, do not refit.","",
 "| Workflow | VM | DO vs late (3-seed mean) | DO vs v12 | DO vs NSGA-II | DO wins late/3 |",
 "|---|---|---:|---:|---:|---:|"]
 for dag in DAGS:
  for speed in SPEED:
   xs=[x for x in cases if x["workflow"]==dag and x["speed"]==speed and x["ref_factor"]==1.5]
   lines.append(f"| {dag} | {speed} | {statistics.mean(x['do_vs_late_pct'] for x in xs):+.4f}% | {statistics.mean(x['do_vs_v12_pct'] for x in xs):+.4f}% | {statistics.mean(x['do_vs_nsga_pct'] for x in xs):+.4f}% | {sum(x['do_beats_late'] for x in xs)}/3 |")
 for factor in (1.5,3.):
  xs=[x for x in cases if x["ref_factor"]==factor]
  lines+=["",f"## {factor}x prespecified reference",
  f"DO vs late: mean {statistics.mean(x['do_vs_late_pct'] for x in xs):+.6f}%, wins {sum(x['do_beats_late'] for x in xs)}/{len(xs)}.",
  f"DO vs v12: mean {statistics.mean(x['do_vs_v12_pct'] for x in xs):+.6f}%, wins {sum(x['do_beats_v12'] for x in xs)}/{len(xs)}.",
  f"DO vs NSGA-II: mean {statistics.mean(x['do_vs_nsga_pct'] for x in xs):+.6f}%, wins {sum(x['do_beats_nsga'] for x in xs)}/{len(xs)}."]
 lines+=["","## Every primary case including negatives","",
 "| Workflow | VM | Seed | DO vs late | DO vs v12 | DO vs NSGA-II |",
 "|---|---|---:|---:|---:|---:|"]
 for x in cases:
  if x["ref_factor"]==1.5:
   lines.append(f"| {x['workflow']} | {x['speed']} | {x['seed']} | {x['do_vs_late_pct']:+.4f}% | {x['do_vs_v12_pct']:+.4f}% | {x['do_vs_nsga_pct']:+.4f}% |")
 lines+=["","## Scientific boundaries",
 "These are independently generated synthetic data structures (NOT new real scientific workflow families), using one fixed wide and one fixed deep topology and three optimizer seeds. Twelve scenarios are not twelve independent DAG topology samples. This is a prespecified structural stress test of the previously chosen DO rule, not a publication-level generalization proof. Relative percent HV is reference-sensitive. Unchanged v17 search code and matching local budgets reduce, but do not eliminate, stochastic path confounds. No production-default promotion follows."]
 (out/"v17_synthetic_report.md").write_text("\n".join(lines)+"\n")
 print("\n".join(lines))
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("usage: report.py ARTIFACT_ROOT OUT")
 main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
