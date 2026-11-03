#!/usr/bin/env python3
"""Read-only predeclared evaluation of 4-family uncertainty in v17 confirmation."""
import csv,itertools,math,pathlib,statistics,sys
def read(path):
 with path.open(newline="") as f:return list(csv.DictReader(f))
def exact_sign_p(wins,n):
 if n<0 or wins<0 or wins>n:raise ValueError("Bad sign sample")
 k=min(wins,n-wins)
 return min(1.0,2*sum(math.comb(n,i) for i in range(k+1))/2**n)
def percentile(xs,p):
 x=sorted(xs);idx=(len(x)-1)*p;lo=math.floor(idx);hi=math.ceil(idx)
 return x[lo]*(hi-idx)+x[hi]*(idx-lo) if lo!=hi else x[lo]
def main(root,out):
 pilotfiles=list(root.rglob("v17_cases.csv"))
 confirmfiles=list(root.rglob("v17_confirm_cases.csv"))
 assert len(pilotfiles)==len(confirmfiles)==1,(pilotfiles,confirmfiles)
 pilot=read(pilotfiles[0]);confirm=read(confirmfiles[0])
 assert len(pilot)==24 and len(confirm)==32
 primary=[x for x in confirm if float(x["ref_factor"])==1.5]
 assert len(primary)==16
 assert {x["workflow"] for x in primary}=={"Epigenomics_46","Inspiral_50","CyberShake_100","Sipht_100"}
 assert {int(x["seed"]) for x in primary}=={211,212}
 assert {x["speed"] for x in primary}=={"default","staggered"}
 metrics=("do_vs_late_pct","do_vs_v12_pct","do_vs_nsga_pct")
 familymeans={}
 for f in sorted({x["workflow"].split("_")[0] for x in primary}):
  rows=[x for x in primary if x["workflow"].split("_")[0]==f]
  assert len(rows)==4
  familymeans[f]={m:statistics.mean(float(x[m]) for x in rows) for m in metrics}
 assert len(familymeans)==4
 result=[]
 for metric in metrics:
  fam=[familymeans[f][metric] for f in sorted(familymeans)]
  # Exhaustive, family-level resampling with replacement (4^4 = 256 samples).
  clusterbootstrap=[statistics.mean(seq) for seq in itertools.product(fam,repeat=4)]
  loo={f:statistics.mean(x[metric] for key,x in familymeans.items() if key!=f) for f in sorted(familymeans)}
  raw=[float(x[metric]) for x in primary]
  assert abs(statistics.mean(raw)-statistics.mean(fam))<1e-10
  winners=sum(x>0 for x in raw)
  result.append(dict(metric=metric,mean_confirm=statistics.mean(raw),wins=winners,n=16,
   exact_two_sided_sign_p=exact_sign_p(winners,16),
   family_resample_2_5=percentile(clusterbootstrap,.025),
   family_resample_97_5=percentile(clusterbootstrap,.975),
   leave_one_family_out_min=min(loo.values()),leave_one_family_out_max=max(loo.values()),
   family_means=familymeans,loo=loo))
 out.mkdir(parents=True,exist_ok=True)
 with (out/"v17_family_uncertainty.csv").open("w",newline="") as f:
  w=csv.writer(f);w.writerow(["metric","confirm_mean_pct","wins_out_of_16","exact_sign_p","four_family_bootstrap_2.5","four_family_bootstrap_97.5","leave_one_family_out_min","leave_one_family_out_max"])
  for d in result:w.writerow([d["metric"],d["mean_confirm"],d["wins"],d["exact_two_sided_sign_p"],d["family_resample_2_5"],d["family_resample_97_5"],d["leave_one_family_out_min"],d["leave_one_family_out_max"]])
 lines=["# v17 confirmation: family-cluster uncertainty and sensitivity, read-only","",
  "Uses original report CSVs only, pilot Actions 41625790444 and confirmation Actions 41626382711. No new optimizer fitness calls and no new simulator replays. Confirmation family units are Epigenomics_46, Inspiral_50, CyberShake_100 and Sipht_100 (four distinct families); each has two VM settings and two seeds. The bootstrap enumerates all 4^4 family resamples with replacement. With only FOUR families it is unstable and NOT a calibrated inferential proof. Pilot and confirmation are reported separately, not treated as independent observations when they share a workflow family.","",
  "| Confirm metric | Mean paired HV % | Wins/16 | Two-sided exact sign-test p (exploratory) | Four-family bootstrap 2.5–97.5% | Leave-one-family-out range |",
  "|---|---:|---:|---:|---|---|"]
 for x in result:
  lines.append(f"| {x['metric']} | {x['mean_confirm']:+.4f}% | {x['wins']}/16 | {x['exact_two_sided_sign_p']:.4f} | [{x['family_resample_2_5']:+.4f}%, {x['family_resample_97_5']:+.4f}%] | [{x['leave_one_family_out_min']:+.4f}%, {x['leave_one_family_out_max']:+.4f}%] |")
 lines+=["","## Paired family-level means on confirmation","",
  "| Workflow family | DO vs Late | DO vs v12 | DO vs NSGA-II |",
  "|---|---:|---:|---:|"]
 for family,values in familymeans.items():
  lines.append("| "+family+" | "+" | ".join(f"{values[m]:+.4f}%" for m in metrics)+" |")
 lines+=["","## What these calculations can and cannot say",
  "The sign-test counts scenario-seeds, which share family and VM structure: its p value assumes independent signs and therefore is exploratory, NOT a valid family-level significance test. The four-family bootstrap respects family clustering but has only four clusters, making its interval highly unstable. The leave-one-family-out analysis checks sensitivity to one strong family. Workflow family, size and VM regime are confounded with some engineering choices and dataset provenance.",
  "Earlier pilot values cannot be pooled with confirmation as if they were independent six-family samples: Epigenomics and Inspiral recur. All metrics remain reference-sensitive, and the 3x HV reference adds no independent evidence. If any interval crosses zero, do not claim statistically reliable improvement.",
  "All study settings and the v17 algorithm were fixed before confirmation. No new variants or thresholds should be selected by reusing these observed cases as held-out test data."]
 (out/"v17_family_uncertainty.md").write_text("\n".join(lines)+"\n")
 print("\n".join(lines))
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("usage: script.py ORIGINAL_REPORT_ARTIFACTS OUT")
 main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
