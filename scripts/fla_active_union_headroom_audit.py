#!/usr/bin/env python3
"""Post-hoc K8 headroom diagnostic using ONLY previously replayed actual truths.

WARNING: union-front and oracle-reselected K8 use AFTER-THE-FACT simulator
labels. They are retrospective diagnostics, never deployable selectors.
A union-front HV is an optimistic ceiling with no K restriction.
"""
import csv
import itertools
import math
import pathlib
import sys

RUN="41821482575"
DAGS=("CyberShake_50","Sipht_60","Epigenomics_100")
SEEDS=(903,904)
MODES=("old-greedy","ready-greedy","staged-greedy","active-uniform-greedy")
SOLVERS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")

def load(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def pareto(points):
    return sorted(set(p for p in points if not any(
        q[0]<=p[0] and q[1]<=p[1] and (q[0]<p[0] or q[1]<p[1])
        for q in points)))

def hv(points,reference):
    prev=reference[1]
    area=0.
    for x,y in pareto(points):
        if x<reference[0] and y<prev:
            area+=(reference[0]-x)*(prev-y)
            prev=y
    value=area/(reference[0]*reference[1])
    assert math.isfinite(value) and 0<=value<=1+1e-10
    return value

def write(path,rows):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)

def true_greedy_k8(observed,reference):
    # Greedy uses actual simulator labels; NOT a future policy or optimum proof.
    chosen=[]
    remaining=sorted(observed)
    while len(chosen)<8:
        best=None
        best_value=-1.
        for mapping in remaining:
            value=hv([observed[x] for x in chosen+[mapping]],reference)
            if best is None or value>best_value+1e-12:
                best=mapping
                best_value=value
        chosen.append(best)
        remaining.remove(best)
    return best_value

def main(root,out):
    out.mkdir(parents=True,exist_ok=True)
    source={}
    for dag,seed,mode in itertools.product(DAGS,SEEDS,MODES):
        folder=root/f"fla-active-uniform-k8-{dag}-s{seed}-{mode}-{RUN}"
        assert folder.is_dir(),("Missing frozen source",folder)
        replay=load(folder/"research_replays.csv")
        assert len(replay)==16
        for solver in SOLVERS:
            rows=[x for x in replay if x["algorithm"]==solver]
            assert len(rows)==8 and len({x["mapping"] for x in rows})==8
            mapping={}
            for r in rows:
                assert r["workflow"]==dag and r["seed"]==str(seed)
                value=(float(r["sim_makespan"]),float(r["sim_cost"]))
                assert all(math.isfinite(x) and x>0 for x in value)
                mapping[r["mapping"]]=value
            source[dag,seed,mode,solver]=mapping
    table=[]
    for dag,seed in itertools.product(DAGS,SEEDS):
        points=[v for mode,solver in itertools.product(MODES,SOLVERS)
                for v in source[dag,seed,mode,solver].values()]
        ref=tuple(1.5*max(p[i] for p in points)+1e-6 for i in range(2))
        for solver in SOLVERS:
            merged={}
            seen_by={}
            for mode in MODES:
                this=source[dag,seed,mode,solver]
                seen_by[mode]=set(this)
                for mapping,v in this.items():
                    if mapping in merged:
                        prev=merged[mapping]
                        assert all(abs(prev[i]-v[i])<=1e-7*max(1,abs(v[i]),abs(prev[i]))
                                   for i in range(2)),("Same mapping changes true objectives",dag,seed,solver,mapping)
                    else:
                        merged[mapping]=v
            union_hv=hv(merged.values(),ref)
            oracle_k8=true_greedy_k8(merged,ref)
            for mode in MODES:
                own=source[dag,seed,mode,solver]
                actual=hv(own.values(),ref)
                assert oracle_k8+1e-10>=actual-1e-10,(
                    "Greedy K8 oracle cannot be assumed to upper-bound every K8 selection",
                    dag,seed,solver,mode)
                active=seen_by["active-uniform-greedy"]
                overlap=len(seen_by[mode]&active)
                table.append(dict(workflow=dag,seed=seed,solver=solver,mode=mode,
                    own_true_hv15=actual,
                    union_all_replayed_true_hv15=union_hv,
                    true_greedy_union_k8_hv15=oracle_k8,
                    optimistic_union_gap=union_hv-actual,
                    retrospective_greedy_delta=oracle_k8-actual,
                    unique_union_mappings=len(merged),
                    overlap_with_active_k8=overlap,
                    reference_m=ref[0],reference_c=ref[1]))
    assert len(table)==48
    write(out/"all_48_posthoc_union_headroom.csv",table)
    findings=["# Retrospective union-headroom diagnostic","",
        "Original run 41821482575: ONLY previously replayed assignments, no extra WorkflowSim calls. Oracle greedy K8 uses TRUE simulator labels after the fact, and union HV uses more than K8; neither is an executable prospective algorithm.",
        "Shared reference within each original DAG/seed block. All 24 original replay artifacts must be present.","",
        "| DAG | Seed | Solver | Distinct union | Active K8 overlap OLD | ACTIVE HV | Union-all HV | Actual-label greedy K8 |",
        "|---|---:|---|---:|---:|---:|---:|---:|"]
    for dag,seed,solver in itertools.product(DAGS,SEEDS,SOLVERS):
        rows=[x for x in table if (x["workflow"],x["seed"],x["solver"])==(dag,seed,solver)]
        active=next(x for x in rows if x["mode"]=="active-uniform-greedy")
        old=next(x for x in rows if x["mode"]=="old-greedy")
        findings.append(f"| {dag} | {seed} | {solver} | {active['unique_union_mappings']} | "
                        f"{old['overlap_with_active_k8']}/8 | "
                        f"{active['own_true_hv15']:.8f} | {active['union_all_replayed_true_hv15']:.8f} | "
                        f"{active['true_greedy_union_k8_hv15']:.8f} |")
    findings+=["","The greedy K8 result is a post-hoc HEURISTIC, not a mathematical global best K8. It might be worse than an observed K8 subset and should not be assumed an upper bound. Union-all HV is a valid optimistic upper bound for ANY selected subset drawn from this observed union, but may require >8 assignments.",
        "This analysis cannot evaluate the unobserved N32 candidate assignments and cannot determine global feasible-workflow Pareto headroom."]
    (out/"posthoc_headroom_scope.md").write_text("\n".join(findings)+"\n",encoding="utf-8")
    print("\n".join(findings))
if __name__=="__main__":
    assert len(sys.argv)==3
    main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
