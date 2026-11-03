#!/usr/bin/env python3
"""Read-only per-VM task-order audit on exact fixed-assignment real WorkflowSim traces.

Original immutable job artifacts: GitHub Actions run 41660167042.
No new simulator/evaluator/search calls; no claim that inversions alone cause the error.
"""
import csv
import math
import pathlib
import statistics
import sys
from collections import defaultdict

WORKFLOWS={"Epigenomics_46":47,"CyberShake_100":100}
ARMS={"v12":"DAG-Pareto-FLA[v12-hvbandit]","nsga":"NSGA-II[costseed]"}
SPEEDS=("default","staggered")
EPS=1e-8

def csv_rows(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def order_inversion(rows):
    """Compare task-pair execution starts on the SAME VM. Excludes either tied start."""
    inverted=comparable=ties=0
    for i,a in enumerate(rows):
        for b in rows[i+1:]:
            x=float(a["planned_start"])-float(b["planned_start"])
            y=float(a["actual_start"])-float(b["actual_start"])
            if abs(x)<=EPS or abs(y)<=EPS:
                ties+=1
            else:
                comparable+=1
                inverted+=((x>0)!=(y>0))
    return int(inverted),int(comparable),int(ties)

def mapping_key(rows):
    if len(rows)!=len({int(r["task_id"]) for r in rows}):
        raise AssertionError("duplicate original task ID")
    return tuple(sorted((int(r["task_id"]),int(r["vm_id"])) for r in rows))

def check_case(rows, summary):
    workflow=summary["workflow"]
    if len(rows)!=WORKFLOWS[workflow]:
        raise AssertionError(("wrong task count",workflow,len(rows)))
    identity=mapping_key(rows)
    source_mapping=tuple(sorted(tuple(map(int,p.split(":"))) for p in summary["mapping"].split("|")))
    if identity!=source_mapping:
        raise AssertionError("task IDs/VMs differ from frozen original genotype")
    for row in rows:
        p_start=float(row["planned_start"])
        p_finish=float(row["planned_finish"])
        a_start=float(row["actual_start"])
        a_finish=float(row["actual_finish"])
        cpu=float(row["actual_cpu_time"])
        nominal=float(row["nominal_compute_seconds"])
        residual=float(row["cpu_minus_nominal_compute_signed_seconds"])
        if not all(math.isfinite(v) for v in (p_start,p_finish,a_start,a_finish,cpu,nominal,residual)):
            raise AssertionError("nonfinite task trace")
        if p_finish<p_start or a_finish<a_start or cpu<0 or nominal<0:
            raise AssertionError("invalid task time")
        if not math.isclose(residual,cpu-nominal,rel_tol=1e-8,abs_tol=1e-6):
            raise AssertionError("raw signed CPU accounting residual inconsistency")
        if not math.isclose(float(row["start_error"]),a_start-p_start,rel_tol=1e-8,abs_tol=1e-6):
            raise AssertionError("start mismatch")
        if not math.isclose(float(row["finish_error"]),a_finish-p_finish,rel_tol=1e-8,abs_tol=1e-6):
            raise AssertionError("finish mismatch")
    observed_max=max(float(r["actual_finish"]) for r in rows)
    recorded_makespan=float(summary["fixed_replay_actual_makespan"])
    if not math.isclose(observed_max,recorded_makespan,rel_tol=1e-7,abs_tol=1e-5):
        raise AssertionError(("task final time does not recover observed makespan",observed_max,recorded_makespan))
    vm_groups=defaultdict(list)
    for row in rows:
        vm_groups[int(row["vm_id"])].append(row)
    inv=comp=ties=0
    by_vm=[]
    for vm,group in sorted(vm_groups.items()):
        a,b,c=order_inversion(group)
        inv+=a;comp+=b;ties+=c
        by_vm.append(dict(vm_id=vm,task_n=len(group),inverted=a,comparable=b,ties=c,
                         max_abs_finish_error=max(abs(float(r["finish_error"])) for r in group)))
    max_finish=max(abs(float(r["finish_error"])) for r in rows)
    mean_abs_finish=statistics.mean(abs(float(r["finish_error"])) for r in rows)
    mean_abs_start=statistics.mean(abs(float(r["start_error"])) for r in rows)
    duration_deltas=[(float(r["actual_finish"])-float(r["actual_start"]))-
                     (float(r["planned_finish"])-float(r["planned_start"])) for r in rows]
    worst=sorted(rows,key=lambda r:-abs(float(r["finish_error"])))[:4]
    return dict(identity=identity,workflow=workflow,seed=summary["seed"],speed=summary["speed"],
                arm=summary["algorithm"],candidate=summary["source_candidate_index"],
                tasks=len(rows),active_vms=len(vm_groups),inverted=inv,comparable=comp,ties=ties,
                inverted_pct=100*inv/comp if comp else None,
                mean_abs_finish_error=mean_abs_finish,max_abs_finish_error=max_finish,
                mean_abs_start_error=mean_abs_start,
                mean_abs_duration_error=statistics.mean(map(abs,duration_deltas)),
                worst=worst,vm=by_vm)

def analysis(root,out):
    cases=[]
    for wf in WORKFLOWS:
        folders=[p for p in root.iterdir() if p.is_dir() and wf in p.name]
        if len(folders)!=1:raise AssertionError(("expected one original artifact folder",wf,folders))
        folder=folders[0]
        for tag,alg in ARMS.items():
            for speed in SPEEDS:
                summaries=csv_rows(folder/f"{tag}_{speed}.csv")
                task_rows=csv_rows(folder/f"{tag}_{speed}_tasks.csv")
                if len(summaries)!=2 or len(task_rows)!=2*WORKFLOWS[wf]:
                    raise AssertionError(("bad original per-task count",wf,tag,speed))
                for candidate in (1,2):
                    summary=next(r for r in summaries if int(r["source_candidate_index"])==candidate)
                    rows=[r for r in task_rows if int(r["candidate_index"])==candidate]
                    if summary["algorithm"]!=alg or summary["speed"]!=speed or summary["workflow"]!=wf:
                        raise AssertionError("original arm/profile mismatch")
                    case=check_case(rows,summary)
                    cases.append(case)
    if len(cases)!=16:raise AssertionError(("expected 16 actual replays",len(cases)))
    # Duplicated physical schedules from different search arms do not provide independent evidence.
    physical=defaultdict(list)
    for c in cases:
        physical[(c["workflow"],c["seed"],c["speed"],c["identity"])].append(c)
    conflicts=[]
    for key,arms in physical.items():
        if len(arms)>1:
            first=arms[0]
            for other in arms[1:]:
                if not math.isclose(other["mean_abs_finish_error"],first["mean_abs_finish_error"],
                        rel_tol=1e-8,abs_tol=1e-6):
                    conflicts.append((key,"finish_error"))
                if (other["inverted"],other["comparable"])!=(first["inverted"],first["comparable"]):
                    conflicts.append((key,"order"))
    out.mkdir(parents=True,exist_ok=True)
    summary_rows=[{k:v for k,v in c.items() if k not in ("identity","vm","worst")}
                  for c in cases]
    with (out/"task_order_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(summary_rows[0]))
        w.writeheader();w.writerows(summary_rows)
    vm_rows=[]
    for c in cases:
        for r in c["vm"]:
            vm_rows.append(dict(workflow=c["workflow"],seed=c["seed"],speed=c["speed"],
                                algorithm=c["arm"],candidate=c["candidate"],**r))
    with (out/"task_order_by_vm.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(vm_rows[0]))
        w.writeheader();w.writerows(vm_rows)
    lines=["# Original Task-ID matched fixed-mapping per-VM execution order audit","",
      "Read-only original observed WorkflowSim task traces: GitHub Actions 41660167042; no new simulator calls.",
      f"Checked **{len(cases)}** replays, **{sum(c['tasks'] for c in cases)}** task trace rows, "
      f"**{len(physical)}** distinct profile-specific physical assignment observations; "
      f"cross-arm same-assignment consistency conflicts **{len(conflicts)}**.",
      "Every task ID, VM assignment, signed CPU residual, start error and finish error was checked against raw original CSVs.",
      "Every replay's maximum actual job finish was cross-checked against the same original replay's recorded true makespan.",
      "",
      "| Workflow | Assignment source | VM profile | Task rows | Same-VM planned/actual order inversion pairs | Comparable pairs | Inversion % | Mean abs start error (s) | Mean abs finish error (s) | Mean abs duration error (s) |",
      "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for wf in WORKFLOWS:
        for arm in ARMS.values():
            for speed in SPEEDS:
                sub=[x for x in cases if x["workflow"]==wf and x["arm"]==arm and x["speed"]==speed]
                inv=sum(x["inverted"] for x in sub)
                cmp=sum(x["comparable"] for x in sub)
                lines.append(f"| {wf} | {arm} | {speed} | {sum(x['tasks'] for x in sub)} | "
                             f"{inv} | {cmp} | {100*inv/cmp if cmp else float('nan'):.3f}% | "
                             f"{statistics.mean(x['mean_abs_start_error'] for x in sub):.3f} | "
                             f"{statistics.mean(x['mean_abs_finish_error'] for x in sub):.3f} | "
                             f"{statistics.mean(x['mean_abs_duration_error'] for x in sub):.3f} |")
    lines+=["","## Max-error diagnostic cases"]
    for c in sorted(cases,key=lambda c:-c["max_abs_finish_error"])[:6]:
        worst=c["worst"][0]
        lines.append(f"- {c['workflow']} {c['arm']} {c['speed']} candidate {c['candidate']}: "
          f"task {worst['task_id']} on VM {worst['vm_id']}, actual-start minus planned-start "
          f"{float(worst['start_error']):+.3f} s; finish difference {float(worst['finish_error']):+.3f} s; "
          f"{c['inverted']}/{c['comparable']} VM-pair rank reversals.")
    lines+=["","## Interpretation boundaries",
      "A within-VM planned-vs-actual ordering inversion establishes a schedule-order mismatch for fixed assignments, not its precise cause.",
      "Duration discrepancies cannot be identified as stage-in without separate real data-transfer events. CloudSim CPU accounting residual is SIGNED and not synonymous with stage-in.",
      "Task timing and dispatch may differ because of simulated dependencies, task-ready events, VM scheduling, caches, data stage-in and tie-breaking. Observed absolute per-task time error can be much larger than final workflow makespan error.",
      "Source candidates are original default-profile K16 prefixes (two DAGs, seed 211); duplicated assignments across v12 and NSGA-II are not independent evidence. No algorithm improvement or statistical significance follows.",
      "Do NOT fit a new correction or claim all error is due to stage-in from this post-hoc pilot."
    ]
    if conflicts:
        lines.append(f"WARNING: {len(conflicts)} cross-arm physical schedule conflicts, so investigate before causal claims.")
    (out/"task_order_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_fixed_task_order_audit.py ORIGINAL_ARTIFACT_ROOT OUTDIR")
    analysis(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
