#!/usr/bin/env python3
"""Evaluate real K-limited WorkflowSim policies across multiple random draws.

Reference points are LOCKED from the prior independent equal-policy pilot,
run 41584672254, before this repeat experiment. Neither its current random
draws nor the selected Pareto-cover points influence the reference.
"""
import argparse
import collections
import csv
import math
import pathlib
import re
import statistics

FROZEN_REFS = {
    "CyberShake_100": (7421.5516, 2911.5777924999998),
    "Inspiral_50": (8423.484174999998, 6833.036574999994),
    "Montage_25": (128.9026, 120.508165),
}
ALGOS = ("DAG-Pareto-FLA[v7-costseed]", "DAG-Pareto-FLA[v12-hvbandit]", "NSGA-II[costseed]")
SEEDS = (53, 54)

def read(path):
    with path.open(newline="") as fp:
        return list(csv.DictReader(fp))

def front(points):
    low, result = float("inf"), []
    for m,c in sorted(set(points)):
        if c < low:
            result.append((m,c))
            low = c
    return result

def hypervolume(points, reference):
    total,last=0.,reference[1]
    for m,c in front(points):
        if m < reference[0] and c < last:
            total += (reference[0]-m)*(last-c)
            last = c
    return total

def build(input_dir, report_dir, start, count, source_run):
    expected = {(wf, seed, rep, policy) for wf in FROZEN_REFS
                for seed in SEEDS for rep in range(start,start+count)
                for policy in ("cover","random")}
    pattern=re.compile(r"(cover|random)_(.+)_s(\d+)_r(\d+)_replays\.csv$")
    found={}
    for path in input_dir.rglob("*_replays.csv"):
        match=pattern.fullmatch(path.name)
        assert match, ("Unexpected replay CSV",path)
        policy,wf,seed,rep=match.group(1),match.group(2),int(match.group(3)),int(match.group(4))
        key=wf,seed,rep,policy
        assert key not in found,key
        found[key]=path
    assert set(found)==expected,("Incomplete/extra jobs",sorted(expected-set(found)),sorted(set(found)-expected))
    values={}
    selected={}
    records=[]
    for key in sorted(expected):
        wf,seed,rep,policy=key
        rows=read(found[key])
        by=collections.defaultdict(list)
        for row in rows:
            alg=row["algorithm"]
            assert alg in ALGOS,(key,alg)
            point=float(row["sim_makespan"]),float(row["sim_cost"])
            assert all(math.isfinite(v) and v>0 for v in point),row
            by[alg].append(point)
            selected.setdefault((wf,seed,rep,policy,alg),[]).append(row["mapping"])
        assert set(by)==set(ALGOS),key
        for alg in ALGOS:
            assert len(by[alg])==16,(key,alg,len(by[alg]))
            assert len(set(selected[(wf,seed,rep,policy,alg)]))==16
            val=hypervolume(by[alg],FROZEN_REFS[wf])
            assert val>0,(key,alg)
            values[(wf,seed,rep,policy,alg)]=val
            records.append(dict(workflow=wf,seed=seed,repeat=rep,policy=policy,algorithm=alg,
                                k=16,optimizer_evaluations=3030,sim_hv=val,
                                reference_m=FROZEN_REFS[wf][0],reference_c=FROZEN_REFS[wf][1]))
    pairs=[]
    case_rows=[]
    report=["# True K16 WorkflowSim replay: fixed-reference replicated random control",
            "",
            f"Run: {source_run}; random repeat indexes {start}..{start+count-1}.",
            "Exactly 3030 planning fitness evaluations and 16 actual simulator calls per algorithm/policy/run; CI enforces per-case budgets.",
            "Three DAG families, two paired optimizer seeds, three algorithms. Different random replay draws are conditional on the SAME deterministic optimizer history.",
            "The HV references below were fixed in the PREVIOUS real K16 controlled study (GitHub Actions 41584672254); they are not refit to new random repeats.",
            "No full-history oracle is consulted in either prospective policy.",
            "",
            "| Workflow | Ref makespan | Ref cost |",
            "|---|---:|---:|"]
    for wf in sorted(FROZEN_REFS):
        m,c=FROZEN_REFS[wf]
        report.append(f"| {wf} | {m:.9g} | {c:.9g} |")
    for wf in sorted(FROZEN_REFS):
        for seed in SEEDS:
            for alg in ALGOS:
                cover=[values[(wf,seed,rep,"cover",alg)] for rep in range(start,start+count)]
                assert max(cover)-min(cover) <= 1e-8*max(1,max(cover)),(wf,seed,alg,cover)
                random_hv=[values[(wf,seed,rep,"random",alg)] for rep in range(start,start+count)]
                draws=[tuple(sorted(selected[(wf,seed,rep,"random",alg)])) for rep in range(start,start+count)]
                assert len(set(draws))>1,(wf,seed,alg,"random repeat index has no effect")
                improvements=[100*(cover[i]/random_hv[i]-1) for i in range(count)]
                for rep,cv,rv,g in zip(range(start,start+count),cover,random_hv,improvements):
                    pairs.append(dict(workflow=wf,seed=seed,repeat=rep,algorithm=alg,
                        cover_hv=cv,random_hv=rv,cover_relative_gain_pct=g))
                case_rows.append(dict(workflow=wf,seed=seed,algorithm=alg,
                    mean_gain_pct=statistics.mean(improvements),
                    median_gain_pct=statistics.median(improvements),
                    min_gain_pct=min(improvements),max_gain_pct=max(improvements),
                    wins=sum(x>0 for x in improvements),random_draws=count,
                    cover_hv=cover[0],mean_random_hv=statistics.mean(random_hv)))
    report += ["","## Per-algorithm random-repeat advantage (not independent workflow observations)","",
        "| Algorithm | Mean of case-wise average cover/random HV gain | Cover wins / draws | Minimum paired improvement |",
        "|---|---:|---:|---:|"]
    for alg in ALGOS:
        grouped=[c for c in case_rows if c["algorithm"]==alg]
        individual=[x["cover_relative_gain_pct"] for x in pairs if x["algorithm"]==alg]
        report.append(f"| {alg} | {statistics.mean(x['mean_gain_pct'] for x in grouped):+.3f}% | "
                      f"{sum(x['wins'] for x in grouped)}/{len(grouped)*count} | {min(individual):+.3f}% |")
    report += ["","## Per-workflow-and-seed descriptive differences","",
               "| Workflow | Seed | Algorithm | Average cover/random HV % | Cover wins / random draws |",
               "|---|---:|---|---:|---:|"]
    for row in case_rows:
        report.append(f"| {row['workflow']} | {row['seed']} | {row['algorithm']} | "
                      f"{row['mean_gain_pct']:+.3f}% | {row['wins']}/{count} |")
    report += ["","## Scientific interpretation",
      "- Random repeat draws are different simulator-selected subsets, NOT additional independently sampled DAG/optimizer seeds. Do not treat the 6 × 3 × draws as independent statistical samples.",
      "- Coverage is deterministic and repeated only for an identical-search sanity check; repeated cover runs cannot be counted as new evidence.",
      "- This test evaluates selector quality conditional on fixed planned-search histories; it does not show FLA v12 is better than cost-seeded NSGA-II.",
      "- Four random draws per case are a pilot, not a publication-grade random-control distribution. Increase to at least 20–30 draws and more independent DAG/optimizer seeds with family-level uncertainty.",
      "- Different workflow families have different HV scales; only paired within-family relative effects are averaged.",
      "- References are frozen from an older pilot. They are within selected-point envelopes, not an externally justified performance bound; sensitivity checks remain necessary."]
    report_dir.mkdir(parents=True,exist_ok=True)
    (report_dir/"random_repeat_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    for name,rows in (("random_repeat_hv.csv",records),
                      ("random_repeat_paired.csv",pairs),
                      ("random_repeat_case_summary.csv",case_rows)):
        with (report_dir/name).open("w",newline="") as fp:
            writer=csv.DictWriter(fp,fieldnames=list(rows[0]))
            writer.writeheader();writer.writerows(rows)
    print("\n".join(report))

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("input",type=pathlib.Path)
    parser.add_argument("output",type=pathlib.Path)
    parser.add_argument("--repeat-start",type=int,default=0)
    parser.add_argument("--repeat-count",type=int,required=True)
    parser.add_argument("--source-run",required=True)
    args=parser.parse_args()
    build(args.input,args.output,args.repeat_start,args.repeat_count,args.source_run)
