#!/usr/bin/env python3
"""Classify same-VM planned-vs-actual execution-order reversals by DAG ancestry.

Read-only: uses original per-task WorkflowSim artifacts, not future simulation
labels during optimization. Original task id assignment follows job element order,
starting at 1 in WorkflowParser.java.
"""
import csv
import pathlib
import sys
from collections import defaultdict
from xml.etree import ElementTree as ET

EPS=1e-8
WORKFLOWS=("Epigenomics_46","CyberShake_100")
ARMS=("v12","nsga")
SPEEDS=("default","staggered")

def local(tag):
    return tag.rsplit("}",1)[-1]

def ancestor_graph(dax_path):
    root=ET.parse(dax_path).getroot()
    jobs=[x for x in root if local(x.tag)=="job"]
    ids=[j.get("id") for j in jobs]
    if not ids or len(ids)!=len(set(ids)) or any(not v for v in ids):
        raise AssertionError("bad DAX job identifiers")
    task_id_by_job={v:i+1 for i,v in enumerate(ids)}
    parents={i+1:set() for i in range(len(ids))}
    for child in root:
        if local(child.tag)!="child":continue
        c=task_id_by_job[child.get("ref")]
        for item in child:
            if local(item.tag)=="parent":
                p=task_id_by_job[item.get("ref")]
                parents[c].add(p)
    memo={}
    visiting=set()
    def visit(t):
        if t in memo:return memo[t]
        if t in visiting:raise AssertionError("DAX contains cycle")
        visiting.add(t)
        reachable=set(parents[t])
        for p in parents[t]:reachable.update(visit(p))
        visiting.remove(t)
        memo[t]=reachable
        return reachable
    for i in parents:visit(i)
    return memo

def order_classes(rows,reach):
    groups=defaultdict(list)
    for r in rows:groups[int(r["vm_id"])].append(r)
    out=dict(dependent_inverted=0,independent_inverted=0,
             dependent_comparable=0,independent_comparable=0,
             dependent_ties=0,independent_ties=0)
    for tasks in groups.values():
        for i,a in enumerate(tasks):
            for b in tasks[i+1:]:
                ia=int(a["task_id"]);ib=int(b["task_id"])
                related=ia in reach[ib] or ib in reach[ia]
                prefix="dependent" if related else "independent"
                delta_p=float(a["planned_start"])-float(b["planned_start"])
                delta_a=float(a["actual_start"])-float(b["actual_start"])
                if abs(delta_p)<=EPS or abs(delta_a)<=EPS:
                    out[prefix+"_ties"]+=1
                else:
                    out[prefix+"_comparable"]+=1
                    out[prefix+"_inverted"]+=int((delta_p>0)!=(delta_a>0))
    return out

def read(path):
    with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def main(root,dax_dir,out):
    out.mkdir(parents=True,exist_ok=True)
    result=[]
    for wf in WORKFLOWS:
        reach=ancestor_graph(dax_dir/(wf+".xml"))
        folders=[p for p in root.iterdir() if p.is_dir() and wf in p.name]
        if len(folders)!=1:raise AssertionError(("missing archived original",wf))
        folder=folders[0]
        for alg in ARMS:
            for speed in SPEEDS:
                rows=read(folder/(alg+"_"+speed+"_tasks.csv"))
                summary=read(folder/(alg+"_"+speed+".csv"))
                if len(summary)!=2 or len(rows)!=2*len(reach):
                    raise AssertionError("incomplete original dataset")
                for candidate in ("1","2"):
                    z=[x for x in rows if x["candidate_index"]==candidate]
                    if len(z)!=len(reach) or {int(r["task_id"]) for r in z}!=set(reach):
                        raise AssertionError(("DAX/trace task ID mismatch",wf,candidate))
                    m=next(s["mapping"] for s in summary if s["source_candidate_index"]==candidate)
                    mapping=dict(tuple(map(int,p.split(":"))) for p in m.split("|"))
                    if any(mapping[int(r["task_id"])]!=int(r["vm_id"]) for r in z):
                        raise AssertionError("original assignment mismatch")
                    zstat=order_classes(z,reach)
                    result.append(dict(workflow=wf,arm=alg,speed=speed,candidate_index=candidate,**zstat))
    if len(result)!=16:raise AssertionError("must cover all 16 original replays")
    with (out/"dag_dependency_order_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]))
        w.writeheader();w.writerows(result)
    report=["# Fixed-mapping actual WorkflowSim ordering inversions, stratified by dependency", "",
        "Original simulator source: Actions 41660167042; 16 original replay traces, 1176 task-time rows. Read-only reanalysis.",
        "DAX ancestry is reconstructed from XML job order (original parser Task IDs start at 1 in job-element order) and the original DAX child/parent blocks; no inferred edges.",
        "",
        "| Workflow | Source | Speed | Ancestry-related inversions/comparable | Independent-task inversions/comparable | Total inverted |",
        "|---|---|---|---:|---:|---:|"]
    for wf in WORKFLOWS:
        for alg in ARMS:
            for speed in SPEEDS:
                z=[x for x in result if x["workflow"]==wf and x["arm"]==alg and x["speed"]==speed]
                if len(z)!=2:raise AssertionError("missing two candidates")
                sums=lambda k:sum(r[k] for r in z)
                d=sums("dependent_inverted");dc=sums("dependent_comparable")
                n=sums("independent_inverted");nc=sums("independent_comparable")
                report.append(f"| {wf} | {alg} | {speed} | {d}/{dc} | {n}/{nc} | {d+n} |")
    totaldep=sum(r["dependent_inverted"] for r in result)
    totalind=sum(r["independent_inverted"] for r in result)
    report+=["",f"Total inversion events across all original replay-arm rows: ancestry-related **{totaldep}**, independent-task **{totalind}**.",
        "Repeated physical genotype profiles across optimizer-source arms are not independent replicates. An inversion for an ancestor pair, if present, requires deeper source-ID or timeline validation before physical interpretation.",
        "Task-order reversals among DAX-independent pairs are compatible with different VM dispatch order, but do not isolate queueing as the causal mechanism. Stage-in, ready-time, scheduler event and caching effects remain possible.",
        "This is a post-hoc mechanism localization of 2 original DAX instances, not a novel algorithm, prospective holdout or significance claim."]
    (out/"dag_dependency_order_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("usage: script.py ORIGINAL_ARTIFACT_ROOT DAX_DIR OUT")
    main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),pathlib.Path(sys.argv[3]))
