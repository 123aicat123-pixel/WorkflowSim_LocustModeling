#!/usr/bin/env python3
"""Separate predicted parent-release error from after-release VM wait error.

Read-only immutable fixed-assignment actual simulator Actions 41664213940.
Identity: original Task IDs in DAX job-order, not simulator Job IDs.
"""
import csv
import math
import pathlib
import statistics
import sys
from xml.etree import ElementTree as ET
from collections import defaultdict
from fla_fixed_event_chain_audit import WORKFLOWS, ARMS, SPEEDS, parse_event_blocks, load, compare, EPS

def parents_from_dax(path):
    root=ET.parse(path).getroot()
    local=lambda e:e.tag.rsplit("}",1)[-1]
    jobs=[j.attrib["id"] for j in root if local(j)=="job"]
    id_by_job={j:i+1 for i,j in enumerate(jobs)}
    if len(id_by_job)!=len(jobs):raise AssertionError("duplicate job ID")
    parents={i+1:set() for i in range(len(jobs))}
    for e in root:
        if local(e)!="child":continue
        c=id_by_job[e.attrib["ref"]]
        for p in e:
            if local(p)=="parent":
                parents[c].add(id_by_job[p.attrib["ref"]])
    return parents

def case(wf,arm,speed,k,rows,events,parents):
    if len(rows)!=len(parents):raise AssertionError("incomplete original task schedule")
    task={int(r["task_id"]):r for r in rows}
    if set(task)!=set(parents):raise AssertionError("DAX mismatched task IDs")
    ready=defaultdict(list)
    for ev,t,j,vm,clock,stage in events:
        if ev=="ENGINE_READY":ready[t].append(clock)
    if set(ready)!=set(task) or any(len(v)!=1 for v in ready.values()):
        raise AssertionError("missing/duplicated engine ready events")
    data={}
    for t,r in task.items():
        pred_release=max((float(task[p]["planned_finish"]) for p in parents[t]),default=0.0)
        observed_parent_end=max((float(task[p]["actual_finish"]) for p in parents[t]),default=0.0)
        actual_ready=ready[t][0]
        predicted_start=float(r["planned_start"])
        actual_start=float(r["actual_start"])
        planned_wait=predicted_start-pred_release
        actual_wait=actual_start-actual_ready
        if planned_wait < -1e-5 or actual_wait < -1e-5:
            raise AssertionError(("invalid predicted or measured waiting interval",wf,arm,speed,k,t,planned_wait,actual_wait))
        if actual_ready < observed_parent_end-1e-5:
            raise AssertionError(("DAG engine releases before parent finished",wf,t,actual_ready,observed_parent_end))
        actual_start_error=actual_start-predicted_start
        ready_error=actual_ready-pred_release
        wait_error=actual_wait-planned_wait
        if not math.isclose(actual_start_error,ready_error+wait_error,rel_tol=1e-9,abs_tol=1e-6):
            raise AssertionError("start error decomposition identity failed")
        data[t]=dict(task_id=t,vm_id=int(r["vm_id"]),
            predicted_release=pred_release,actual_engine_ready=actual_ready,
            actual_parent_last_finish=observed_parent_end,
            ready_error=ready_error,planned_wait=planned_wait,actual_wait=actual_wait,
            wait_error=wait_error,start_error=actual_start_error,
            engine_release_lag=actual_ready-observed_parent_end,
            predicted_start=predicted_start,actual_start=actual_start)
    # Per-same-VM predicted release rank vs actual engine ready rank.
    vm_groups=defaultdict(list)
    for t,d in data.items():vm_groups[d["vm_id"]].append(t)
    n0=n1=tie0=tie1=0
    for tasks in vm_groups.values():
        for i,a in enumerate(tasks):
            for b in tasks[i+1:]:
                p=compare(data[a]["predicted_release"],data[b]["predicted_release"])
                r=compare(data[a]["actual_engine_ready"],data[b]["actual_engine_ready"])
                q=compare(data[a]["predicted_start"],data[b]["predicted_start"])
                s=compare(data[a]["actual_start"],data[b]["actual_start"])
                if p and r:
                    n0+=1;tie0+=int(p!=r)
                if q and s:
                    n1+=1;tie1+=int(q!=s)
    result=dict(workflow=wf,arm=arm,speed=speed,candidate=k,tasks=len(data),
        mean_abs_ready_error=statistics.mean(abs(x["ready_error"]) for x in data.values()),
        mean_abs_wait_error=statistics.mean(abs(x["wait_error"]) for x in data.values()),
        mean_abs_start_error=statistics.mean(abs(x["start_error"]) for x in data.values()),
        mean_engine_release_lag=statistics.mean(x["engine_release_lag"] for x in data.values()),
        max_engine_release_lag=max(x["engine_release_lag"] for x in data.values()),
        ready_dominates_task_n=sum(abs(x["ready_error"])>abs(x["wait_error"]) for x in data.values()),
        ready_vs_observed_inversions=tie0,ready_vs_observed_comparable=n0,
        planned_start_vs_actual_inversions=tie1,planned_start_vs_actual_comparable=n1)
    return result,list(data.values())

def audit(root,daxroot,out):
    out.mkdir(parents=True,exist_ok=True)
    summary=[]
    detail=[]
    for wf in WORKFLOWS:
        groups=[p for p in root.iterdir() if p.is_dir() and wf in p.name]
        if len(groups)!=1:raise AssertionError(("missing frozen artifact",wf))
        folder=groups[0];parents=parents_from_dax(daxroot/(wf+".xml"))
        for tag,arm in ARMS.items():
            for speed in SPEEDS:
                rows=load(folder/f"{tag}_{speed}_tasks.csv")
                blocks=parse_event_blocks(folder/f"{tag}_{speed}.log")
                for k in (1,2):
                    r=[row for row in rows if int(row["candidate_index"])==k]
                    metrics,d=case(wf,tag,speed,k,r,blocks[k],parents)
                    summary.append(metrics)
                    for t in d:detail.append(dict(workflow=wf,arm=tag,speed=speed,candidate=k,**t))
    if len(summary)!=16 or len(detail)!=1176:
        raise AssertionError(("expected all original task records",len(summary),len(detail)))
    for file,items in [("release_wait_cases.csv",summary),("release_wait_all_tasks.csv",detail)]:
        with (out/file).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
    report=["# Fixed-VM predictor parent-release error versus observed post-release waiting error","",
      "Source: immutable real WorkflowSim events Actions 41664213940; 16 fixed-assignment replays and 1176 original Task-ID rows.",
      "All task-start errors exactly decompose into (actual Engine ready - predicted parent release) + ((actual start - actual ready) - (planned start - predicted release)).",
      "This arithmetic decomposition is descriptive, not a causal test, and per-task contributions can have opposite signs.",
      "",
      "| DAX | Source | VM speed | Mean abs predicted-vs-real release error (s) | Mean abs after-release waiting error (s) | Mean abs task-start error (s) | Estimated release-rank inversions |",
      "|---|---|---|---:|---:|---:|---:|"]
    for wf in WORKFLOWS:
        for tag in ARMS:
            for speed in SPEEDS:
                x=[r for r in summary if (r["workflow"],r["arm"],r["speed"])==(wf,tag,speed)]
                if len(x)!=2:raise AssertionError("missing two frozen candidates")
                a=lambda key:statistics.mean(v[key] for v in x)
                report.append(f"| {wf} | {tag} | {speed} | {a('mean_abs_ready_error'):.3f} | "
                    f"{a('mean_abs_wait_error'):.3f} | {a('mean_abs_start_error'):.3f} | "
                    f"{sum(v['ready_vs_observed_inversions'] for v in x)}/{sum(v['ready_vs_observed_comparable'] for v in x)} |")
    report+=["","## Diagnostics",
      f"- Rows where |predicted-vs-actual parent-release error| exceeds |post-release waiting error|: "
      f"{sum(abs(r['ready_error'])>abs(r['wait_error']) for r in detail)} / {len(detail)} task rows (correlated observations).",
      f"- Maximum actual ENGINE_READY - max(parent actual finish): "
      f"{max(r['engine_release_lag'] for r in detail):.6f} s.",
      "- Source-specific repeat mappings can share identical event traces and are not independent replicates.",
      "- Predicted parent release is max predicted FINISH of directly preceding DAX tasks from StageInAwareScheduleEvaluator; actual ready is independently logged WorkflowEngine release timestamp.",
      "- Estimated release rank inversions include dependent and independent task pairs on the same VM; zero/tied predicted-release times are excluded. Do not equate rank inversions to simulator violations.",
      "- This does not prove a newly implemented decoder or improve true HV; next experiment requires a frozen predictive implementation and unseen DAG validation."
    ]
    out_text="\n".join(report)+"\n"
    (out/"release_wait_report.md").write_text(out_text,encoding="utf-8")
    print(out_text)

if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("usage: script.py ARTIFACT_ROOT DAX_DIR OUTPUT_DIR")
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),pathlib.Path(sys.argv[3]))
