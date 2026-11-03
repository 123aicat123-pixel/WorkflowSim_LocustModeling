#!/usr/bin/env python3
"""Leave-one-DAG-family-out prediction generalization gate.

Uses only historical FULLY simulated visited genotypes from GitHub Actions
41582476054 (eight cases, four DAG families, two seeds); each heldout DAG
family is completely excluded from fitting. This is retrospective evidence,
not a prospective simulator-guided selector or an optimizer improvement.
"""
import csv
import math
import pathlib
import statistics
import sys
import collections
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from scipy.stats import kendalltau

FAMILIES=("CyberShake_100","Epigenomics_100","Montage_100","Sipht_100")
SOLVERS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")

def load(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))

def features(row):
    vm=np.array([int(item.split(":")[1]) for item in row["mapping"].split("|")],dtype=np.int32)
    counts=np.bincount(vm,minlength=16)/len(vm)
    loc=np.arange(16)
    center=float(np.dot(counts,loc))
    m=float(row["planned_makespan"]);c=float(row["planned_cost"])
    assert m>0 and c>0 and len(vm)>1 and max(vm)<16
    return [math.log(m),math.log(c),len(set(vm))/16,max(counts),float(sum(counts*counts)),
        center/15,float(np.dot(counts,(loc-center)**2))/225,
        float(np.mean(vm[1:]!=vm[:-1])),*counts]

def run(root,out):
    paths=sorted(root.rglob("budget_*_replays.csv"))
    assert len(paths)==8,("Expected exactly 8 independent full-history cases",len(paths))
    data=[]
    for p in paths:
        extra=pathlib.Path(str(p).replace("_replays.csv","_screening_samples.csv"))
        assert extra.exists(),p
        original=load(p);added=load(extra)
        by=collections.defaultdict(list)
        for row in original+added:
            assert row["workflow"] in FAMILIES and row["algorithm"] in SOLVERS
            by[row["algorithm"]].append(row)
        assert set(by)==set(SOLVERS)
        for alg,rows in by.items():
            assert len(rows)==len(set(r["mapping"] for r in rows))
            for row in rows:
                planned=float(row["planned_makespan"]);actual=float(row["sim_makespan"])
                assert math.isfinite(actual) and actual>0
                data.append(dict(family=row["workflow"],seed=int(row["seed"]),algorithm=alg,
                    mapping=row["mapping"],planned=planned,actual=actual,x=features(row)))
    assert sorted(set(r["family"] for r in data))==list(FAMILIES)
    assert set((r["family"],r["seed"],r["algorithm"]) for r in data)=={
        (wf,seed,alg) for wf in FAMILIES for seed in (46,47) for alg in SOLVERS}
    X=np.array([r["x"] for r in data],dtype=float)
    raw=np.array([r["planned"] for r in data])
    true=np.array([r["actual"] for r in data])
    y=np.log(true/raw)
    family=np.array([r["family"] for r in data])
    for wf in FAMILIES:
        mask=family==wf
        # Unsupervised, planner-only family scaling; never test simulator labels.
        X[mask,0]-=np.median(X[mask,0])
        X[mask,1]-=np.median(X[mask,1])
    models={
        "planner-only":None,
        "global-offset":None,
        "ridge-alpha100":lambda:make_pipeline(StandardScaler(),Ridge(alpha=100)),
        "random-forest-depth5":lambda:RandomForestRegressor(
            n_estimators=100,max_depth=5,min_samples_leaf=25,random_state=11,n_jobs=1)
    }
    scores=[]
    for name,factory in models.items():
        estimate=raw.copy()
        for wf in FAMILIES:
            test=family==wf
            if name=="planner-only":
                continue
            if name=="global-offset":
                adjustment=np.median(y[~test])*np.ones(sum(test))
            else:
                model=factory()
                model.fit(X[~test],y[~test])
                adjustment=model.predict(X[test])
            estimate[test]=raw[test]*np.exp(adjustment)
        for wf in FAMILIES:
            mask=family==wf
            groups=collections.defaultdict(list)
            for i,r in enumerate(data):
                if r["family"]==wf:groups[(r["seed"],r["algorithm"])].append(i)
            tau=[];overlap=[]
            for ids in groups.values():
                ids=np.array(ids,dtype=int)
                tau.append(float(kendalltau(estimate[ids],true[ids],variant="b").statistic))
                p=set(ids[np.argsort(estimate[ids],kind="stable")[:16]])
                a=set(ids[np.argsort(true[ids],kind="stable")[:16]])
                overlap.append(len(p&a)/16)
            scores.append(dict(model=name,heldout_family=wf,observations=int(sum(mask)),
                mean_ape_pct=float(100*np.mean(np.abs(estimate[mask]/true[mask]-1))),
                mean_kendall_tau_b=statistics.mean(tau),
                mean_top16_overlap_pct=100*statistics.mean(overlap)))
    out.mkdir(parents=True,exist_ok=True)
    with (out/"rank_generalization_folds.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(scores[0]));w.writeheader();w.writerows(scores)
    report=["# Held-out DAG makespan correction model: a negative research gate","",
        "Original complete 80-evaluation historical independent WorkflowSim replays: Actions 41582476054, four 100-task DAG families, two optimizer seeds and three solvers.",
        f"Total observed solver-case rows: {len(data)}. Duplicate genotypes from separate arms are NOT independent held-out DAGs.",
        "Leave-one-WHOLE-DAG-family-out training and testing; normalization uses only planned values from the held-out family (no true simulator labels).",
        "Preset models: original planned values, median residual global offset, standardized Ridge alpha=100, 100-tree RF with depth 5 and >=25 leaf samples.",
        "Features: planned makespan/cost logs, 16-way VM allocations, VM concentration, variance, count and adjacent assignment switches.",
        "",
        "| Method | Average absolute relative error across 4 held-out families (observation weighted) |",
        "|---|---:|"]
    weights=collections.Counter(r["family"] for r in data)
    for name in models:
        rs=[r for r in scores if r["model"]==name]
        value=sum(r["mean_ape_pct"]*weights[r["heldout_family"]] for r in rs)/len(data)
        report.append(f"| {name} | {value:.4f}% |")
    report+=["","## Per-family accuracy and ranking (all negative results retained)","",
        "| Model | Heldout family | MAPE | Kendall tau-b | Planned top16 overlap |",
        "|---|---|---:|---:|---:|"]
    for item in scores:
        report.append(f"| {item['model']} | {item['heldout_family']} | {item['mean_ape_pct']:.3f}% | "+
          f"{item['mean_kendall_tau_b']:.4f} | {item['mean_top16_overlap_pct']:.2f}% |")
    report+=["","## Decision and limitations",
        "A model cannot be promoted merely because it fits histories from previously seen workflows. The fully held-out family results here show simple mapping-feature correction often worsens objective ranking and actual error.",
        "The four families are too few to certify that ALL learning-based corrections fail, or to estimate statistical generalization with useful precision.",
        "No high-budget K16 prospective replay policy was changed; do not attribute any observed effects to FLA v12 search improvements.",
        "Further work needs additional diverse DAG families/VM and communication configurations and truly independent simulator-labeled training and evaluation sets."]
    (out/"rank_generalization_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_rank_generalization_gate.py ORIGINAL_ARCHIVE_ROOT OUTPUT")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
