#!/usr/bin/env python3
"""Pure read-only v17 verification of planned vs actual replay fidelity and runtime.

No new objective or WorkflowSim calls; compares existing K16 candidate pairs only.
"""
import csv
import math
import pathlib
import statistics
import sys

ARMS=("DAG-Pareto-FLA[v12-hvbandit]","DAG-Pareto-FLA[v17-do-random]",
      "DAG-Pareto-FLA[v17-late-random]","NSGA-II[costseed]")
GROUPS=(
 ("real-sizes",("Epigenomics_46","Inspiral_50","CyberShake_100","Sipht_100"),(211,212),"v17-confirm"),
 ("synthetic-wide-deep",("SynthNewWide_60","SynthNewDeep_60"),(301,302,303),"v17-synthetic"),
)
SPEEDS=("default","staggered")

def read(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))

def rank_inversion_rate(pts):
    disagree=comparable=ties=0
    for i in range(len(pts)):
        for j in range(i+1,len(pts)):
            p=pts[i][0]-pts[j][0]
            a=pts[i][1]-pts[j][1]
            if abs(p)<1e-10 or abs(a)<1e-10:
                ties+=1
                continue
            comparable+=1
            if (p>0)!=(a>0):disagree+=1
    return (100*disagree/comparable if comparable else None),comparable,ties

def mean_or_empty(vals):
    z=[x for x in vals if x is not None]
    return statistics.mean(z) if z else None

def main(root,out):
    records=[]
    for label,names,seeds,prefix in GROUPS:
        for dag in names:
            for speed in SPEEDS:
                for seed in seeds:
                    name=f"{prefix}-{speed}-{dag}-s{seed}"
                    summary=list(root.rglob(name+"_summary.csv"))
                    replay=list(root.rglob(name+"_replays.csv"))
                    assert len(summary)==len(replay)==1,(name,summary,replay)
                    sr=read(summary[0]);rr=read(replay[0])
                    assert len(sr)==4 and len(rr)==64
                    assert {x["algorithm"] for x in sr}==set(ARMS)
                    for arm in ARMS:
                        stat=next(x for x in sr if x["algorithm"]==arm)
                        z=sorted((x for x in rr if x["algorithm"]==arm),key=lambda x:int(x["candidate_index"]))
                        assert len(z)==16 and [int(x["candidate_index"]) for x in z]==list(range(1,17))
                        assert len({x["mapping"] for x in z})==16
                        assert int(stat["evaluations"])==int(stat["captured_evaluations"])==3030
                        assert int(stat["replayed"])==16
                        pred_m=[float(x["planned_makespan"]) for x in z]
                        true_m=[float(x["sim_makespan"]) for x in z]
                        pred_c=[float(x["planned_cost"]) for x in z]
                        true_c=[float(x["sim_cost"]) for x in z]
                        assert all(math.isfinite(x) and x>0 for x in pred_m+true_m+pred_c+true_c)
                        mpe_m=[100*(p-t)/t for p,t in zip(pred_m,true_m)]
                        mpe_c=[100*(p-t)/t for p,t in zip(pred_c,true_c)]
                        inv_m,com_m,tie_m=rank_inversion_rate(list(zip(pred_m,true_m)))
                        inv_c,com_c,tie_c=rank_inversion_rate(list(zip(pred_c,true_c)))
                        runtime=float(stat["search_ms"])
                        assert math.isfinite(runtime) and runtime>=0
                        records.append(dict(cohort=label,dag=dag,speed=speed,seed=seed,algorithm=arm,
                            evals=3030,k16=16,
                            makespan_mape_pct=statistics.mean(map(abs,mpe_m)),
                            cost_mape_pct=statistics.mean(map(abs,mpe_c)),
                            makespan_signed_error_pct=statistics.mean(mpe_m),
                            cost_signed_error_pct=statistics.mean(mpe_c),
                            makespan_rank_inversion_pct=inv_m if inv_m is not None else "",
                            cost_rank_inversion_pct=inv_c if inv_c is not None else "",
                            comparable_makespan_pairs=com_m,comparable_cost_pairs=com_c,
                            ties_makespan_pairs=tie_m,ties_cost_pairs=tie_c,
                            search_ms=runtime))
    assert len(records)==(16+12)*4
    out.mkdir(exist_ok=True,parents=True)
    with (out/"v17_fidelity_runtime_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]))
        w.writeheader();w.writerows(records)
    lines=["# v17 planning-vs-actual K16 fidelity and CPU-search-time: read-only archived analysis","",
        "This is a post-hoc audit of originally archived K16 WorkflowSim replays, not a new evaluation. Two cohorts: original different-size real DAX archive (Actions 41626382711) and newly preregistered synthetic wide/deep DAG archive (Actions 41631739331). Each arm gets exactly 3030 planned evaluations and K16 actual replay assignments, with four arms per scenario.",
        "**MAPE** is mean absolute percentage difference between the PLANNED objective for the exact selected assignment and its ACTUAL simulator result, denominator ACTUAL. A high MAPE would warn against treating planning objectives as exact true costs. **Rank inversion** is the fraction of K16 within-arm candidate pairs with opposite planned vs actual rankings, excluding ties; it is not Pareto HV or a Kendall statistic on all visited genotypes. When no comparable pairs exist, the cell is blank.",
        "Search runtime is from the optimizer's logged Java search_ms, and is confounded by serial solver order, JVM warmup and hosted runner noise. It cannot establish hardware-normalized runtime superiority.",
        "","| Cohort | Algorithm | Mean K16 makespan MAPE | Mean cost MAPE | Mean makespan inversion | Mean cost inversion | Mean search wall-time (ms) |",
        "|---|---|---:|---:|---:|---:|---:|"]
    for cohort,*_ in GROUPS:
        for arm in ARMS:
            samples=[x for x in records if x["cohort"]==cohort and x["algorithm"]==arm]
            assert samples
            m_inv=mean_or_empty([x["makespan_rank_inversion_pct"] if x["makespan_rank_inversion_pct"]!="" else None for x in samples])
            c_inv=mean_or_empty([x["cost_rank_inversion_pct"] if x["cost_rank_inversion_pct"]!="" else None for x in samples])
            fm=lambda x:("NA" if x is None else "%.3f%%"%x)
            lines.append("| "+cohort+" | "+arm+" | "+" | ".join((
                fm(statistics.mean(x["makespan_mape_pct"] for x in samples)),
                fm(statistics.mean(x["cost_mape_pct"] for x in samples)),
                fm(m_inv),fm(c_inv),
                "%.1f"%statistics.mean(x["search_ms"] for x in samples)
            ))+" |")
    lines+=["","## Explicit scientific limits",
        "These model-fidelity figures describe ONLY the 16 Pareto-cover-selected assignments per optimizer and scenario; they do not estimate error on unsampled search proposals. Task and VM units, file locality and communication/cache semantics require separate audit before interpreting signed biases as physical phenomena. The four solvers can select different areas of the objective space, so solver-specific MAPE is not a controlled same-assignment comparison.",
        "Search runtime must be measured with randomized solver execution order, isolated hardware, repetitions, and a normalized JVM warmup protocol for fair comparisons. Equal evaluation count does not imply equal runtime. Do not infer cause of v17 family-specific HV results from these observational biases alone."]
    (out/"v17_fidelity_runtime_report.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: script.py ORIGINAL_ARTIFACT_ROOT OUTPUT_DIR")
    main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
