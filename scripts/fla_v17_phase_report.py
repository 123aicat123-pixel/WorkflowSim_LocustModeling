#!/usr/bin/env python3
import csv,math,pathlib,re,statistics,sys
DAGS=("Epigenomics_24","Inspiral_30");SPEED=("default","staggered");SEEDS=(191,192,193)
ALG=["DAG-Pareto-FLA["+v+"]" for v in ("v12-hvbandit","v14-randompair","v17-do-random","v17-late-random","v14-timelinepair","v17-do-timeline","v17-late-timeline")]+["NSGA-II[costseed]"]
def rows(p):
 with p.open(newline="") as f:return list(csv.DictReader(f))
def hv(pts,ref):
 out=0.;last=ref[1]
 for m,c in sorted(set(pts)):
  if m<ref[0] and c<last:out+=(ref[0]-m)*(last-c);last=c
 return out
def main(root,out):
 data={}
 for dag in DAGS:
  for speed in SPEED:
   for seed in SEEDS:
    prefix=f"v17-phase-{speed}-{dag}-s{seed}"
    files={s:list(root.rglob(prefix+s)) for s in ("_summary.csv","_replays.csv","_population_diagnostics.csv","_budget_protocol.txt")}
    assert all(len(p)==1 for p in files.values()),(prefix,files)
    stats=rows(files["_summary.csv"][0]);replay=rows(files["_replays.csv"][0]);trace=rows(files["_population_diagnostics.csv"][0])
    assert len(stats)==8 and len(replay)==128 and len(trace)==707
    assert {x["algorithm"] for x in stats}==set(ALG)
    proto=files["_budget_protocol.txt"][0].read_text()
    assert "PROSPECTIVE_REPLAY_BUDGET_K=16" in proto and "PROSPECTIVE_REPLAY_POLICY=pareto-cover" in proto and "VM_SPEED_PROFILE="+speed in proto
    job=files["_summary.csv"][0].parent.parent
    assert (job/"ci-logs/source_sha.txt").is_file()
    log=(job/"ci-logs/experiment.log").read_text()
    match=[tuple(map(int,x)) for x in re.findall(r"FLA_PAIRED_WINDOW mode=(\d+) activeGenerations=(\d+) localTrials=(\d+) normalBanditSlots=(\d+)",log)]
    assert sorted(match)==[(1,74,1036,1964)]*2+[(2,74,1036,1964)]*2,(prefix,match)
    for alg in ALG:
     s=next(x for x in stats if x["algorithm"]==alg)
     assert int(s["evaluations"])==int(s["captured_evaluations"])==3030 and int(s["replayed"])==16
     rr=sorted((x for x in replay if x["algorithm"]==alg),key=lambda x:int(x["candidate_index"]))
     assert len(rr)==16 and [int(x["candidate_index"]) for x in rr]==list(range(1,17))
     assert len({x["mapping"] for x in rr})==16
     planned=[(float(x["planned_makespan"]),float(x["planned_cost"])) for x in rr]
     actual=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in rr]
     assert all(math.isfinite(y) and y>0 for x in planned+actual for y in x)
     if not alg.startswith("NSGA-II"):
      tr=[x for x in trace if x["algorithm"]==alg]
      assert len(tr)==101
      use=sum(int(float(x[k])) for x in tr for k in ("bandit_baseline_uses","bandit_colocate_uses","bandit_critical_uses"))
      assert use==(3000 if alg==ALG[0] else 1600 if alg in (ALG[1],ALG[4]) else 1964),(prefix,alg,use)
     data[dag,speed,seed,alg]=(planned,actual)
 cases=[]
 for dag in DAGS:
  for speed in SPEED:
   pool=[x for seed in SEEDS for alg in ALG for x in data[dag,speed,seed,alg][0]]
   bounds=(max(x[0] for x in pool),max(x[1] for x in pool))
   for f in (1.5,3.):
    ref=(f*bounds[0]+1,f*bounds[1]+1)
    for seed in SEEDS:
     real=[data[dag,speed,seed,a][1] for a in ALG]
     assert all(x<ref[0] and y<ref[1] for r in real for x,y in r),("bad planned-only reference",dag,speed,seed,f)
     score=[hv(x,ref) for x in real]
     assert min(score)>0
     diff=lambda i,j:100*(score[i]/score[j]-1)
     cases.append(dict(workflow=dag,speed=speed,seed=seed,reference=f,
      do_random_vs_late_random_pct=diff(2,3),do_timeline_vs_late_timeline_pct=diff(5,6),
      do_random_vs_full_random_pct=diff(2,1),do_timeline_vs_full_timeline_pct=diff(5,4),
      do_random_vs_v12_pct=diff(2,0),do_timeline_vs_v12_pct=diff(5,0),
      do_random_vs_nsga_pct=diff(2,7),do_timeline_vs_nsga_pct=diff(5,7),
      do_random_wins_late=int(score[2]>score[3]),do_timeline_wins_late=int(score[5]>score[6])))
 assert len(cases)==24
 out.mkdir(exist_ok=True,parents=True)
 with (out/"v17_cases.csv").open("w",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
 lines=["# v17 DO-only versus equal-1036-local-trial last-74 control — true WorkflowSim K16","",
 "Two previously existing but new-to-this-series DAX families × two VM regimes × three seeds. Eight matched algorithms per case; 3030 counted PLANNING evaluations and K16 actual simulated assignments each. DO-only and last-74 both have 1036 charged local trials and 1964 normal FLA offspring; full pair uses 1400 local, baseline uses none. Common planned-only HV reference fixed at 1.5x+1 primary and 3x+1 sensitivity; no true-label refit.","",
 "| DAG | VM | DO-random vs late | DO-timeline vs late | DO-random vs v12 | DO-timeline vs v12 | DO-random vs NSGA-II | DO-timeline vs NSGA-II |",
 "|---|---|---:|---:|---:|---:|---:|"]
 keys=("do_random_vs_late_random_pct","do_timeline_vs_late_timeline_pct","do_random_vs_v12_pct","do_timeline_vs_v12_pct","do_random_vs_nsga_pct","do_timeline_vs_nsga_pct")
 for dag in DAGS:
  for speed in SPEED:
   rr=[x for x in cases if x["workflow"]==dag and x["speed"]==speed and x["reference"]==1.5]
   lines.append("| "+dag+" | "+speed+" | "+" | ".join(f"{statistics.mean(x[k] for x in rr):+.4f}%" for k in keys)+" |")
 for f in (1.5,3.):
  rr=[x for x in cases if x["reference"]==f]
  lines+=["",f"## Reference {f}x"]
  for k in keys:lines.append(f"- {k}: {statistics.mean(x[k] for x in rr):+.6f}%.")
  lines.append(f"- DO-random beats equal-count late random: {sum(x['do_random_wins_late'] for x in rr)}/{len(rr)}.")
  lines.append(f"- DO-timeline beats equal-count late timeline: {sum(x['do_timeline_wins_late'] for x in rr)}/{len(rr)}.")
 lines+=["","## All primary reference outcomes","",
 "| DAG | VM | Seed | DO-random vs late | DO-timeline vs late | DO-random vs v12 | DO-timeline vs v12 | DO-random vs NSGA-II | DO-timeline vs NSGA-II |",
 "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
 for x in cases:
  if x["reference"]==1.5:
   lines.append(f"| {x['workflow']} | {x['speed']} | {x['seed']} | "+" | ".join(f"{x[k]:+.4f}%" for k in keys)+" |")
 lines+=["","## Limitations","These workflow files already existed in the repo. Only three seeds per workflow-speed and two families; results are development data, not Q1-grade independent validation. DO-only versus late-74 matches number of local calls but not RNG trajectories; full versus DO also differs in total local calls. No current algorithm/default promotion is implied."]
 (out/"v17_report.md").write_text("\n".join(lines)+"\n")
 print("\n".join(lines))
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("usage: report.py ROOT OUT")
 main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
