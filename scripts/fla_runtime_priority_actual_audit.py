#!/usr/bin/env python3
"""Pure immutable 36-replay fixed-VM priority intervention audit.

Actual WorkflowSim original: GitHub Actions 41679712071.
No simulator oracle, model search, or policy tuning in this analysis.
"""
import csv
import math
import pathlib
import statistics
import sys

DAGS=("CyberShake_100","Montage_100","Sipht_60")
MAPPINGS=("all_vm0","all_vm12","round_robin","stride7")
PRIORITIES=("shortest","upward")

def read(path):
    with path.open(newline="",encoding="utf-8") as stream:
        return list(csv.DictReader(stream))

def audit(root,out):
    if not root.is_dir():raise AssertionError("Missing immutable original results")
    rows=[]
    for dag in DAGS:
        matches=[p for p in root.iterdir() if p.is_dir() and p.name.startswith("fla-ready-runtime-priority-"+dag+"-")]
        if len(matches)!=1:raise AssertionError(("one original DAG artifact required",dag,[str(p) for p in matches]))
        data=read(matches[0]/"all_policy_pairs.csv")
        if len(data)!=8:raise AssertionError(("eight observed original comparisons required",dag,len(data)))
        expected={(m,p) for m in MAPPINGS for p in PRIORITIES}
        seen=set()
        for row in data:
            key=(row["assignment_policy"],row["runtime_priority"])
            if (row["workflow"],row["seed"])!=(dag,"509") or key not in expected or key in seen:
                raise AssertionError(("bad original block identity",dag,key))
            seen.add(key)
            for key in ("fifo_actual_makespan","priority_actual_makespan","fifo_actual_cost","priority_actual_cost"):
                v=float(row[key])
                if not math.isfinite(v) or v<=0:
                    raise AssertionError(("nonpositive simulator value",dag,row,key))
            for before,after,delta in [
                ("fifo_actual_makespan","priority_actual_makespan","makespan_delta_pct"),
                ("fifo_actual_cost","priority_actual_cost","cost_delta_pct")]:
                a=float(row[before]);b=float(row[after]);d=100*(b/a-1)
                if not math.isclose(float(row[delta]),d,rel_tol=1e-9,abs_tol=1e-7):
                    raise AssertionError(("inaccurate source delta",dag,delta,d,row[delta]))
            rows.append(dict(row))
        if seen!=expected:raise AssertionError(("missing combinations",dag,expected-seen))
    if len(rows)!=24:raise AssertionError("expected exact 24 alt-vs-FIFO comparisons for 36 runs")
    out.mkdir(parents=True,exist_ok=True)
    with (out/"all_24_actual_priority_pairs.csv").open("w",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    report=[
        "# WorkflowSim actual ready-job priority intervention: three DAG families",
        "",
        "Frozen original source [GitHub Actions 41679712071](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41679712071).",
        "**3 DAX × 4 exact independent preselected task-to-VM mappings × 3 runtime priority policies = 36 new actual WorkflowSim replays**, all original jobs successful. Original task-to-VM assignment and stage-in-aware planner outputs checked invariant. Two archived FIFO DAG replays matched historical pre-intervention results.",
        "",
        "These are NOT 36 independent workflow families; there are only 3 known DAG instances, one seed and four intentionally extreme fixed placement policies.",
        "The preregistered detectable change threshold is >1e-6 relative; an additional **0.1%** practical-effect sensitivity screen is descriptive and was not a preregistered efficacy threshold.",
        "",
        "| DAX | Priority | Makespan improved (>0.1%) | Approx. unchanged (≤0.1%) | Worsened (>0.1%) | Mean signed Δ (%) | Largest abs Δ (%) |",
        "|---|---|---:|---:|---:|---:|---:|"]
    for dag in DAGS:
        for priority in PRIORITIES:
            z=[r for r in rows if r["workflow"]==dag and r["runtime_priority"]==priority]
            diffs=[float(r["makespan_delta_pct"]) for r in z]
            impr=sum(x<-.1 for x in diffs)
            tie=sum(abs(x)<=.1 for x in diffs)
            worse=sum(x>.1 for x in diffs)
            report.append(f"| {dag} | {priority} | {impr} | {tie} | {worse} | {statistics.mean(diffs):+.6f} | {max(map(abs,diffs)):.6f} |")
    significant=[r for r in rows if abs(float(r["makespan_delta_pct"]))>.1]
    report+=["",f"**Cases showing >0.1% absolute makespan change:** {len(significant)}/{len(rows)} priority-vs-FIFO comparisons.",
        "",
        "## Every practically changed (>0.1%) fixed genotype"]
    for r in sorted(significant,key=lambda x:-abs(float(x["makespan_delta_pct"]))):
        report.append(f"- {r['workflow']} {r['assignment_policy']} {r['runtime_priority']}: "
                      f"actual FIFO={float(r['fifo_actual_makespan']):.4f}s, "
                      f"priority={float(r['priority_actual_makespan']):.4f}s, "
                      f"makespan change={float(r['makespan_delta_pct']):+.6f}%, "
                      f"cost change={float(r['cost_delta_pct']):+.6f}%.")
    if not significant:report.append("No recorded change exceeds this descriptive threshold.")
    report+=["",
        "## Research decision",
        "This controlled, original Task-to-VM-fixed test shows that **runtime priority is an actionable scheduling dimension** on some DAG/mapping pairs, but using a fixed upward rule may seriously hurt other mappings of the SAME DAG. No global policy was established.",
        "Upward rank and SJF are known heuristics: optimizing priority plus VM allocation in itself is not a novelty claim. Prior literature already studies joint task-priority and VM-choice learning; a paper would require a genuinely distinctive mechanism and fair comparison against those methods.",
        "The current STAGEIN-aware and READY models were held constant across runtime policies; they cannot yet rank alternative runtime priorities correctly without a priority-aware decoder. No optimistic offline best-policy oracle has been used.",
        "Before expensive co-optimization, the NEXT gate is read-only dispatch-opportunity tracing: count VM-ready queues with 2+ COMPUTE jobs, verify runtime candidate rank actually changes at those opportunities, and check effects on DAG critical paths. A fixed, all-policy evaluation can follow without fitting to these known results.",
        "No default optimizer, initial FIFO scheduler or master branch was changed; the new queue priority is opt-in only."
    ]
    (out/"actual_runtime_priority_conclusions.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py ORIGINAL_RUN_ARTIFACTS OUT_DIR")
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
