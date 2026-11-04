#!/usr/bin/env python3
"""Read-only Java GREEDY staged source selections vs locked exact-HV staged study."""
import csv
import math
import pathlib
import statistics
import sys

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import fla_algorithm_independent_same_mapping_rank_audit as frozen

DAGS=frozen.DAGS
SPEEDS=frozen.SPEEDS
KS=(2,4)
TS=(4,8)
TOL=1e-8

def read(path):
    with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def run(original,old_exact,greedy_file,out):
    verified,sha=frozen.load(original)
    exact_files=list(old_exact.rglob("all_24_paired_staged_vs_old_ready.csv"))
    if len(exact_files)!=1:raise AssertionError(("One original exact staged result required",exact_files))
    old=read(exact_files[0])
    new=read(greedy_file)
    def index(rows,name):
        result={}
        for r in rows:
            key=(r["workflow"],r["vm_speed"],int(r["K"]),int(r["T"]))
            if key in result:raise AssertionError(("Duplicate result",name,key))
            result[key]=r
        return result
    originals=index(old,"exact")
    model=index(new,"greedy")
    expected={(d,s,k,t) for d in DAGS for s in SPEEDS for k in KS for t in TS}
    if set(originals)!=expected or set(model)!=expected:
        raise AssertionError(("Missing whole frozen comparison",len(originals),len(model)))
    compared=[]
    for key in sorted(expected):
        a=originals[key];b=model[key]
        if int(b["ready_calls"])!=key[3]:
            raise AssertionError(("Unexpected expensive callback count",key))
        for field in ("old_real_hv15_pct","full_ready_real_hv15_pct","staged_real_hv15_pct",
                      "staged_minus_ready_pp","staged_minus_old_pp"):
            x=float(b[field])
            if not math.isfinite(x):raise AssertionError(("Nonfinite true score",key,field))
        group=verified[(key[0],key[1])]
        assert len(group)==16
        for field,length in (("old_indices",key[2]),("full_ready_indices",key[2]),
                             ("screen_indices",key[3]),("staged_indices",key[2])):
            ids=[int(x) for x in b[field].split("|")]
            if len(ids)!=length or len(set(ids))!=length or any(x<1 or x>16 for x in ids):
                raise AssertionError(("Impossible selected source mapping index",key,field,b[field]))
        h_original=float(a["staged_hv15"])
        h_new=float(b["staged_real_hv15_pct"])
        full_original=float(a["full_ready_hv15"])
        full_new=float(b["full_ready_real_hv15_pct"])
        old_original=float(a["old_hv15"])
        old_new=float(b["old_real_hv15_pct"])
        compared.append(dict(workflow=key[0],vm_speed=key[1],K=key[2],T=key[3],
            ready_calls=key[3],source_sha=sha,
            exact_staged_real_hv15_pct=h_original,greedy_staged_real_hv15_pct=h_new,
            greedy_minus_exact_staged_pp=h_new-h_original,
            exact_full_ready_real_hv15_pct=full_original,
            greedy_full_ready_real_hv15_pct=full_new,
            greedy_minus_exact_full_ready_pp=full_new-full_original,
            exact_old_real_hv15_pct=old_original,
            greedy_old_real_hv15_pct=old_new,
            greedy_minus_exact_old_pp=old_new-old_original,
            greedy_staged_minus_greedy_ready_pp=h_new-full_new,
            greedy_staged_minus_greedy_old_pp=h_new-old_new,
            greedy_screen_indices=b["screen_indices"],
            greedy_selected_indices=b["staged_indices"],
            exact_selected_indices=a["staged_chosen"],
            actual_mapping_selection_same=int(b["staged_indices"]==a["staged_chosen"])))
    out.mkdir(parents=True,exist_ok=True)
    with (out/"all_24_java_greedy_vs_python_exact_comparisons.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(compared[0]));w.writeheader();w.writerows(compared)
    report=[
      "# Scalable Java greedy staged screening vs exact combinatorial staged K-HV (same archived true WorkflowSim)",
      "",
      "Immutable original 96 true WorkflowSim source Actions 41695356307, verified by frozen physical task→VM assignment loader. Exact model-only staged selector source Actions 41775295948. New Java GREEDY selector calls READY lazily **exactly T times** per case; original true simulation results appear only after selection. NO new simulator or optimizer calls.",
      "This comparison changes the K/T selector from exhaustive combinatorial HV maximization to simple sequential marginal-HV greedy. That is a standard heuristic, not new optimization novelty. Same OLD-only planned HV reference and same actual 1.5x real reference in both experiments.",
      "",
      "| K | T | Mean exact staged actual HV recovery | Mean GREEDY staged actual HV recovery | GREEDY−exact staged (pp) | GREEDY vs exact staged wins/ties/losses | GREEDY−GREEDY full-READY (pp) |",
      "|---:|---:|---:|---:|---:|---:|---:|"]
    for k in KS:
        for t in TS:
            z=[x for x in compared if (x["K"],x["T"])==(k,t)]
            delta=[x["greedy_minus_exact_staged_pp"] for x in z]
            report.append(f"| {k} | {t} | "
              f"{statistics.mean(x['exact_staged_real_hv15_pct'] for x in z):.7f}% | "
              f"{statistics.mean(x['greedy_staged_real_hv15_pct'] for x in z):.7f}% | "
              f"{statistics.mean(delta):+.7f} | "
              f"{sum(d>TOL for d in delta)}/{sum(abs(d)<=TOL for d in delta)}/{sum(d< -TOL for d in delta)} | "
              f"{statistics.mean(x['greedy_staged_minus_greedy_ready_pp'] for x in z):+.7f} |")
    report+=["","## All results, including negative improvements"]
    for row in compared:
        report.append(f"- {row['workflow']} {row['vm_speed']} K={row['K']} T={row['T']}: "
            f"exact staged={row['exact_staged_real_hv15_pct']:.7f}%, "
            f"greedy staged={row['greedy_staged_real_hv15_pct']:.7f}%, "
            f"greedy−exact={row['greedy_minus_exact_staged_pp']:+.7f} pp; "
            f"selected physical K identical={bool(row['actual_mapping_selection_same'])}.")
    report+=["",
       "## Guardrails",
       "The Java staged class is a caller-level API for OLD model results and a lazy READY callback; it is NOT yet connected into actual FLA or NSGA-II iterative genotype fitness evaluation. Count parity and demonstrated selection at 16 candidate genotypes is necessary but insufficient for publishable search improvement.",
       "The greedy selector can have worse predicted HV than exact subset enumeration, and worse actual HV due to model error. This study archives all cases and does not tune objective weights or choice order afterward.",
       "Real search speed and full WorkflowSim HV remain untested for the new greedy API; master/default FIFO/source original FLA and NSGA-II are unchanged."
    ]
    (out/"greedy_staged_exact_comparison_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=5:raise SystemExit("usage: audit.py ORIGINAL_SOURCE EXACT_STAGE_ARCHIVE JAVA_GREEDY_CSV REPORT_DIR")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),
        pathlib.Path(sys.argv[3]),pathlib.Path(sys.argv[4]))
