#!/usr/bin/env python3
"""Read-only fixed-assignment WorkflowSim event chain and same-VM pair audit.

Source: archived original actual simulator Actions 41664213940.
Task identity is original DAX Task ID, not a WorkflowSim Job ID.
"""
import csv
import math
import pathlib
import re
import statistics
import sys
from collections import defaultdict
from xml.etree import ElementTree as ET

ARMS={"v12":"DAG-Pareto-FLA[v12-hvbandit]","nsga":"NSGA-II[costseed]"}
WORKFLOWS={"Epigenomics_46":47,"CyberShake_100":100}
SPEEDS=("default","staggered")
EVENTS=("ENGINE_READY","SCHEDULER_ARRIVE","SCHEDULER_DISPATCH",
        "DATACENTER_SUBMIT","ENGINE_COMPLETE")
ORDER_STAGES=("planned_start",*EVENTS[:-1],"actual_start")
EPS=1e-8

def load(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def ancestry(dax):
    root=ET.parse(dax).getroot()
    loc=lambda t:t.rsplit("}",1)[-1]
    jobs=[x.attrib["id"] for x in root if loc(x.tag)=="job"]
    identifiers={v:i+1 for i,v in enumerate(jobs)}
    if len(identifiers)!=len(jobs):raise AssertionError("DAX repeated job id")
    ps={i+1:set() for i in range(len(jobs))}
    for node in root:
        if loc(node.tag)!="child":continue
        child=identifiers[node.attrib["ref"]]
        for parent in node:
            if loc(parent.tag)=="parent":ps[child].add(identifiers[parent.attrib["ref"]])
    done={}
    in_progress=set()
    def visit(t):
        if t in done:return done[t]
        if t in in_progress:raise AssertionError("cyclic DAG")
        in_progress.add(t)
        acc=set(ps[t])
        for p in ps[t]:acc.update(visit(p))
        in_progress.remove(t);done[t]=acc
        return acc
    for t in ps:visit(t)
    return done

def parse_event_blocks(path):
    """Each invocation contains two fresh simulator runs; FIXED_MATCHED closes one."""
    blocks=[]
    cur=[]
    for line in path.read_text(encoding="utf-8",errors="replace").splitlines():
        if line.startswith("FIXED_EVENT,"):
            p=line.split(",")
            if len(p)!=7:raise AssertionError(("event row length",line))
            _,name,tid,jid,vm,clock,transfer=p
            if name not in EVENTS:raise AssertionError(("bad event",name))
            cur.append((name,int(tid),int(jid),int(vm),float(clock),float(transfer)))
        elif line.startswith("FIXED_MATCHED "):
            m=re.search(r" k=(\d+) speed=(\S+)",line)
            if m is None:raise AssertionError(("bad replay completion",line))
            blocks.append((int(m.group(1)),m.group(2),cur))
            cur=[]
    if cur or len(blocks)!=2 or [k for k,_,_ in blocks]!=[1,2]:
        raise AssertionError(("event block boundaries",path,len(blocks),len(cur)))
    return {k:rows for k,_,rows in blocks}

def compare(p,q):
    a=float(p);b=float(q)
    if abs(a-b)<=EPS:return 0
    return -1 if a<b else 1

def audit_case(wf,arm,speed,candidate,task_rows,events,summary,reach):
    identity=tuple(sorted((int(t),int(v)) for t,v in
        (part.split(":") for part in summary["mapping"].split("|"))))
    tasks={int(r["task_id"]):r for r in task_rows}
    mapping=dict(identity)
    if len(tasks)!=WORKFLOWS[wf] or set(tasks)!=set(mapping) or set(tasks)!=set(reach):
        raise AssertionError("task ID or frozen mapping coverage")
    by_task=defaultdict(dict)
    if len(events)!=len(EVENTS)*len(tasks):
        raise AssertionError(("event count",wf,arm,speed,candidate,len(events)))
    for name,task,job,vm,time,stagein in events:
        if task not in tasks or name in by_task[task]:
            raise AssertionError(("unexpected or repeated event",name,task))
        if vm!=mapping[task] or not math.isfinite(time) or time<0:
            raise AssertionError(("unmatched event identity/timestamp",name,task))
        if name=="DATACENTER_SUBMIT" and (not math.isfinite(stagein) or stagein<0):
            raise AssertionError("missing actual file transfer duration")
        if name!="DATACENTER_SUBMIT" and stagein!=-1:
            raise AssertionError("stagein recorded outside datacenter")
        by_task[task][name]=(time,job,vm,stagein)
    prepared={}
    for task,row in tasks.items():
        ev=by_task[task]
        if set(ev)!=set(EVENTS):raise AssertionError(("missing event",task,ev.keys()))
        if len({ev[name][1] for name in EVENTS})!=1:
            raise AssertionError("Job ID changed within single-task chain")
        ts=[ev[name][0] for name in EVENTS]
        if any(ts[i+1]<ts[i]-1e-6 for i in range(len(ts)-1)):
            raise AssertionError(("nonmonotonic WorkflowSim event chain",wf,task,ts))
        start=float(row["actual_start"]);finish=float(row["actual_finish"])
        planned=float(row["planned_start"])
        if start+1e-6<ev["DATACENTER_SUBMIT"][0] or finish+1e-6<start:
            raise AssertionError(("actual job time inconsistent with datacenter event",task))
        if ev["ENGINE_COMPLETE"][0]+1e-6<finish:
            raise AssertionError(("job completion event precedes actual finish",task))
        if ev["DATACENTER_SUBMIT"][2]!=mapping[task]:
            raise AssertionError("VM mismatch in datacenter")
        prepared[task]={
            "planned_start":planned,"actual_start":start,
            **{name:ev[name][0] for name in EVENTS},
            "stagein":ev["DATACENTER_SUBMIT"][3],
            "original_actual_finish":finish,
        }
    if not math.isclose(max(v["original_actual_finish"] for v in prepared.values()),
                        float(summary["fixed_replay_actual_makespan"]),rel_tol=1e-7,abs_tol=1e-5):
        raise AssertionError("actual task finishes do not recover original simulator makespan")
    counts=defaultdict(lambda:dict(comparable=0,inverted=0,tied=0))
    first_mismatch=defaultdict(int)
    same_vm_independent_pairs=0
    for i,a in enumerate(sorted(tasks)):
        for b in sorted(tasks)[i+1:]:
            if mapping[a]!=mapping[b] or a in reach[b] or b in reach[a]:
                continue
            same_vm_independent_pairs+=1
            relation={stage:compare(prepared[a][stage],prepared[b][stage]) for stage in ORDER_STAGES}
            target=relation["actual_start"]
            for stage in ORDER_STAGES[:-1]:
                v=relation[stage]
                if not v or not target:
                    counts[stage]["tied"]+=1
                else:
                    counts[stage]["comparable"]+=1
                    counts[stage]["inverted"]+=int(v!=target)
            if relation["planned_start"] and target and relation["planned_start"]!=target:
                eligible=[stage for stage in ORDER_STAGES[1:-1] if relation[stage] and relation[stage]!=relation["planned_start"]]
                first_mismatch[eligible[0] if eligible else "UNRESOLVED_TIED_EVENTS"]+=1
    summary_row=dict(workflow=wf,arm=arm,speed=speed,candidate=candidate,
                     task_n=len(tasks),physical_mapping="|".join(f"{a}:{b}" for a,b in identity),
                     same_vm_independent_pairs=same_vm_independent_pairs,
                     total_stagein_seconds=sum(v["stagein"] for v in prepared.values()))
    for stage in ORDER_STAGES[:-1]:
        for key,value in counts[stage].items():summary_row[f"{stage}_{key}"]=value
    for stage in (*ORDER_STAGES[1:-1],"UNRESOLVED_TIED_EVENTS"):
        summary_row[f"first_divergence_{stage}"]=first_mismatch[stage]
    return summary_row,prepared

def run(root,daxroot,out):
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for wf in WORKFLOWS:
        folders=[p for p in root.iterdir() if p.is_dir() and wf in p.name]
        if len(folders)!=1:raise AssertionError(("expected one artifact folder",wf,folders))
        folder=folders[0];reach=ancestry(daxroot/(wf+".xml"))
        for tag,arm in ARMS.items():
            for speed in SPEEDS:
                replay=load(folder/f"{tag}_{speed}.csv")
                tasks=load(folder/f"{tag}_{speed}_tasks.csv")
                blocks=parse_event_blocks(folder/f"{tag}_{speed}.log")
                if len(replay)!=2 or len(tasks)!=2*WORKFLOWS[wf]:
                    raise AssertionError(("original replay incomplete",wf,tag,speed))
                for c in (1,2):
                    sr=next(r for r in replay if int(r["source_candidate_index"])==c)
                    tr=[r for r in tasks if int(r["candidate_index"])==c]
                    row,_=audit_case(wf,arm,speed,c,tr,blocks[c],sr,reach)
                    rows.append(row)
    if len(rows)!=16:raise AssertionError("expected 16 completed replay arms")
    # For physical duplicate assignments, all stage inversion/event results must agree.
    repeated=defaultdict(list)
    for row in rows:repeated[(row["workflow"],row["speed"],row["physical_mapping"])].append(row)
    conflicts=[]
    for key,x in repeated.items():
        for y in x[1:]:
            for metric in x[0]:
                if metric in ("arm","candidate"):continue
                if x[0][metric]!=y[metric]:
                    conflicts.append((key,metric))
    keys=list(rows[0])
    with (out/"fixed_event_chain_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    report=["# Fixed-VM mapping original Task-ID WorkflowSim event chain","",
      "Immutable simulator source: GitHub Actions 41664213940 (16 new real replays, 2 DAG families, 2 VM profiles).",
      f"Replays checked: **{len(rows)}**; unique physical profile-specific mappings: **{len(repeated)}**; cross-arm duplicate inconsistencies: **{len(conflicts)}**.",
      "Events: ENGINE_READY → SCHEDULER_ARRIVE → SCHEDULER_DISPATCH → DATACENTER_SUBMIT → ENGINE_COMPLETE; actual job start and finish verified separately.",
      "Only DAG-INDEPENDENT same-VM task pairs are analyzed. Each row aggregates original candidate 1+2; duplicated physical mappings must not be counted as independent experiments.",
      "",
      "| DAG | Assignment source | VM speed | Planned-vs-actual inversions | Engine-ready-vs-actual inversions | Dispatch-vs-actual inversions | Datacenter-submit-vs-actual inversions |",
      "|---|---|---|---:|---:|---:|---:|"]
    for wf in WORKFLOWS:
        for tag,arm in ARMS.items():
            for speed in SPEEDS:
                z=[r for r in rows if (r["workflow"],r["arm"],r["speed"])==(wf,arm,speed)]
                def f(s):
                    return f"{sum(x[s+'_inverted'] for x in z)}/{sum(x[s+'_comparable'] for x in z)}"
                report.append(f"| {wf} | {tag} | {speed} | {f('planned_start')} | {f('ENGINE_READY')} | {f('SCHEDULER_DISPATCH')} | {f('DATACENTER_SUBMIT')} |")
    report+=["","## Earliest recorded divergence for initially inverted planned-versus-actual task pairs"]
    for stage in (*ORDER_STAGES[1:-1],"UNRESOLVED_TIED_EVENTS"):
        total=sum(r[f"first_divergence_{stage}"] for r in rows)
        report.append(f"- {stage}: {total} pair-events (with cross-arm duplicates).")
    report+=["",
      "## Validity boundaries",
      "A job can be released on the same simulation tick as other jobs; tied timestamps are excluded from inversion denominators, not arbitrarily ordered by emitted-log row order.",
      "Engine-ready-versus-actual inversions show that planning's topological earliest-insertion rank already differs at parent-completion release for many pairs, but do not prove that the engine itself is faulty.",
      "DATACENTER_SUBMIT is a simulated CloudSim event, NOT the actual CPU start; stage-in recorded here is independently measured file-transfer delay, not the signed CPU accounting residual.",
      "Only original default K16 candidate prefixes and one optimizer seed on two known DAG instances were used. These results diagnose model fidelity, not an FLA improvement or publication-level validation."]
    if conflicts:report.append(f"WARNING: {len(conflicts)} cross-arm same-assignment inconsistencies; investigate before interpretation.")
    text="\n".join(report)+"\n"
    (out/"fixed_event_chain_report.md").write_text(text,encoding="utf-8")
    print(text)

if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("usage: script.py SOURCE_ARTIFACTS DAX_FOLDER OUTPUT_FOLDER")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),pathlib.Path(sys.argv[3]))
