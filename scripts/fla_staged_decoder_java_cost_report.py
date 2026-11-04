#!/usr/bin/env python3
"""No simulation: summarize benchmark of ACTUAL Java decoder implementations."""
import csv
import itertools
import math
import pathlib
import statistics
import sys

def run(path,out):
    out.mkdir(parents=True,exist_ok=True)
    with path.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    if len(rows)!=108:raise AssertionError(("Exactly 108 original timing rounds required",len(rows)))
    grouped={}
    for r in rows:
        n=int(r["task_count"]);graph=r["graph"];model=r["model"];round_id=int(r["round"])
        key=(n,graph,model)
        if n not in (30,100,200) or graph not in ("chain","forked","independent") or model not in ("old","ready") or round_id not in range(6):
            raise AssertionError(("Unregistered benchmark",r))
        if int(r["vm_count"])!=16 or int(r["calls"])!=128:raise AssertionError("Workload changed")
        value=float(r["ns_per_candidate"])
        if not math.isfinite(value) or value<=0:raise AssertionError("Invalid timings")
        if not math.isclose(float(r["total_ns"])/128,value,rel_tol=1e-9,abs_tol=.0001):
            raise AssertionError("Inconsistent timing data")
        grouped.setdefault(key,{})
        if round_id in grouped[key]:raise AssertionError("Repeat round")
        grouped[key][round_id]=value
    assert len(grouped)==18
    result=[]
    for n,graph in itertools.product((30,100,200),("chain","forked","independent")):
        old=grouped[(n,graph,"old")];ready=grouped[(n,graph,"ready")]
        assert set(old)==set(ready)==set(range(6))
        a=statistics.median(old.values());b=statistics.median(ready.values())
        old_total=16*a
        full=16*b
        st4=16*a+4*b
        st8=16*a+8*b
        result.append(dict(task_count=n,graph=graph,
            old_median_ns_per_candidate=a,
            ready_median_ns_per_candidate=b,
            ready_vs_old_eval_ratio=b/a,
            old_only_16_us=old_total/1000,
            full_ready_16_us=full/1000,
            staged_T4_model_only_us=st4/1000,
            staged_T8_model_only_us=st8/1000,
            T4_vs_full_ready_ratio=st4/full,
            T8_vs_full_ready_ratio=st8/full,
            T4_model_only_time_saved_pct=100*(1-st4/full),
            T8_model_only_time_saved_pct=100*(1-st8/full)))
    with (out/"java_model_cost_all_nine_workloads.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    report=[
        "# Actual Java decoder synthetic microcost: OLD, READY, STAGED4, STAGED8",
        "",
        "Both genuine Java evaluation classes measured (not modeled in Python). Original 108 timing records: 3 n × 3 DAG topologies × 2 decoders × 6 alternating-order 128-call rounds, 16 VMs, synthetic tasks without files. Each case warmed up four 16-candidate passes per evaluator.",
        "This is a MICROBENCHMARK on synthetic DAGs, not realistic DAX/WorkflowSim runtime and not an end-to-end scheduler throughput experiment. 16 OLD + T READY sums below are measured-decoder-work PROXIES, excluding exact HV selection enumeration and any simulator costs.",
        "",
        "| Tasks | Synthetic DAG | READY / OLD median unit time | OLD 16 (µs) | Full READY 16 (µs) | Staged T4 proxy (µs) | Staged T8 proxy (µs) | T4 vs full time change | T8 vs full time change |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in result:
        report.append(f"| {r['task_count']} | {r['graph']} | {r['ready_vs_old_eval_ratio']:.3f}× | "
          f"{r['old_only_16_us']:.2f} | {r['full_ready_16_us']:.2f} | "
          f"{r['staged_T4_model_only_us']:.2f} | {r['staged_T8_model_only_us']:.2f} | "
          f"{-r['T4_model_only_time_saved_pct']:+.1f}% | {-r['T8_model_only_time_saved_pct']:+.1f}% |")
    report+=["",
      "## Reproducibility and reporting boundary",
      "The table's negative percentage denotes lower model-only work than full READY; positive percentage indicates more work. READY evaluation calls reduce 75% at T4 or 50% at T8, but full workload time need not.",
      "Model-level median time can fluctuate due to JIT/GC/runner contention. The measured value is median of six full model blocks; 6 rounds are not six independent machines.",
      "The earlier 96 real WorkflowSim HV results were not used to decide timings or synthetic workload shape after source simulation; none of these 108 timings represents a new real CloudSim evaluation.",
      "The staged strategy cannot be claimed faster until an END-TO-END Java implementation is measured on real DAX and equivalent search budgets, or until genuine decoder savings outweigh its initial OLD and selection overhead. No default or master change."
    ]
    (out/"java_model_cost_microbenchmark_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: report.py TIMING_CSV OUTDIR")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
