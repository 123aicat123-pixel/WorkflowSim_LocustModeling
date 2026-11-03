#!/usr/bin/env python3
"""Read-only v16 phase-bandit exposure versus archive and selected diversity."""
import pathlib,csv,statistics,sys
NAMES=["DAG-Pareto-FLA[v12-hvbandit]","DAG-Pareto-FLA[v16-shamrandom]","DAG-Pareto-FLA[v14-randompair]","DAG-Pareto-FLA[v16-shamtimeline]","DAG-Pareto-FLA[v14-timelinepair]"]
SOURCE="b890475aa1d162478ec420e79d740828a856e11c"
def read(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(exist_ok=True,parents=True)
allrows=[]
for dag in ("Montage_25","CyberShake_30"):
 for speed in ("default","staggered"):
  for seed in (181,182):
   pref=f"v16-opportunity-{speed}-{dag}-s{seed}_population_diagnostics.csv"
   found=list(root.rglob(pref));assert len(found)==1,(pref,found)
   p=found[0]
   assert (p.parent.parent/"ci-logs/source_sha.txt").read_text().strip()==SOURCE
   r=read(p);assert len(r)==505
   for alg in NAMES:
    rr=sorted((x for x in r if x["algorithm"]==alg),key=lambda z:int(float(z["generation"])))
    assert len(rr)==101
    assert all(int(float(x["selected_unique"]))+int(float(x["selected_duplicate_slots"]))==30 for x in rr)
    for phase,label in ((0,"DO"),(1,"EO"),(2,"SSO")):
     sample=[x for x in rr[1:] if int(float(x["phase"]))==phase]
     assert sample
     uses=sum(int(float(x[k])) for x in sample for k in ("bandit_baseline_uses","bandit_colocate_uses","bandit_critical_uses"))
     assert uses==len(sample)*(30 if alg==NAMES[0] else 16)
     allrows.append(dict(dag=dag,speed=speed,seed=seed,algorithm=alg,phase=label,
         generations=len(sample),bandit_uses=uses,
         archive_admissions_per_generation=statistics.mean(float(x["archive_insert_events"]) for x in sample),
         hamming=statistics.mean(float(x["pairwise_hamming_all"]) for x in sample),
         selected_unique=statistics.mean(float(x["selected_unique"]) for x in sample),
         generated_unique=statistics.mean(float(x["generated_unique"]) for x in sample)))
with (out/"v16_phase_cases.csv").open("w",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
lines=["# Read-only v16 phase diagnostics",f"Source SHA: {SOURCE}. Eight original jobs, zero new optimizer or simulator calls.","",
 "| FLA phase | v12 bandit opportunities | Paired bandit opportunities | Random active−sham archive admissions/gen | Timeline active−sham archive admissions/gen | Random active−sham Hamming | Timeline active−sham Hamming |",
 "|---|---:|---:|---:|---:|---:|---:|"]
for phase in ("DO","EO","SSO"):
 s=[x for x in allrows if x["phase"]==phase]
 def mean(i,k):return statistics.mean(x[k] for x in s if x["algorithm"]==NAMES[i])
 u=lambda i:sum(x["bandit_uses"] for x in s if x["algorithm"]==NAMES[i])
 lines.append(f"| {phase} | {u(0)} | {u(1)} | {mean(2,'archive_admissions_per_generation')-mean(1,'archive_admissions_per_generation'):+.4f} | {mean(4,'archive_admissions_per_generation')-mean(3,'archive_admissions_per_generation'):+.4f} | {mean(2,'hamming')-mean(1,'hamming'):+.6f} | {mean(4,'hamming')-mean(3,'hamming'):+.6f} |")
lines.extend(["","All figures are descriptive. Phase correlates with generation. Sham discards proposed neighbors after RNG consumption and novelty-set operations, and thus does not isolate bandit credit alone. Archive admissions are not real simulator HV. Previously studied DAGs and two seeds are not a publication holdout."])
(out/"v16_phase_report.md").write_text("\n".join(lines)+"\n")
print("\n".join(lines))
