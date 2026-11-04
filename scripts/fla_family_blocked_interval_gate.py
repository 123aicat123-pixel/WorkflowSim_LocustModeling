#!/usr/bin/env python3
"""Strict leave-one-whole-DAX-family-out interval safety stress test, no simulation."""
import csv
import itertools
import math
import pathlib
import statistics
import sys

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import fla_algorithm_independent_same_mapping_rank_audit as baseline

MODELS=("old","ready")
BUFFER=1e-9
DAGS=baseline.DAGS
SPEEDS=baseline.SPEEDS
POLICIES=baseline.POLICIES

def write(path,rows):
    if not rows:raise AssertionError(("Missing output",path))
    with path.open("w",newline="",encoding="utf-8") as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)

def dom(a,b):
    if all(x<=y for x,y in zip(a,b)) and any(x<y for x,y in zip(a,b)):return 1
    if all(y<=x for x,y in zip(a,b)) and any(y<x for x,y in zip(a,b)):return -1
    return 0

def cert(a,b,epsilon):
    if all((1+e)*x<(1-e)*y for x,y,e in zip(a,b,epsilon)):return 1
    if all((1+e)*y<(1-e)*x for x,y,e in zip(a,b,epsilon)):return -1
    return 0

def evaluate(root,out):
    original,sha=baseline.load(root)
    out.mkdir(parents=True,exist_ok=True)
    folds=[];blocks=[];mistakes=[]
    for target,model in itertools.product(DAGS,MODELS):
        train=[original[(dag,profile)][policy] for dag in DAGS if dag!=target
               for profile in SPEEDS for policy in POLICIES]
        if len(train)!=64:raise AssertionError("Training family contamination")
        def pp(row):
            return (float(row[f"{model}_planned_makespan"]),float(row[f"{model}_planned_cost"]))
        def aa(row):
            return (float(row["actual_makespan"]),float(row["actual_cost"]))
        residuals=[tuple(abs(x/y-1) for x,y in zip(aa(r),pp(r))) for r in train]
        raw_eps=(max(v[0] for v in residuals),max(v[1] for v in residuals))
        epsilon=tuple(x+BUFFER for x in raw_eps)
        if not all(math.isfinite(x) and 0<=x<1 for x in epsilon):
            raise AssertionError(("Invalid error width; cannot safely certify",target,model,epsilon))
        folds.append(dict(held_out_family=target,predictor=model,
                          training_families="|".join(x for x in DAGS if x!=target),
                          train_points=len(train),training_max_m_error=raw_eps[0],
                          training_max_c_error=raw_eps[1],buffer=BUFFER,
                          test_m_width=epsilon[0],test_c_width=epsilon[1],
                          source_sha=sha))
        for profile in SPEEDS:
            source=[original[(target,profile)][policy] for policy in POLICIES]
            planned=[pp(r) for r in source]
            truth=[aa(r) for r in source]
            failures=[]
            for idx,(p,a) in enumerate(zip(planned,truth)):
                deviations=[abs(x/y-1) for x,y in zip(a,p)]
                if any(v>e for v,e in zip(deviations,epsilon)):
                    failures.append(dict(held_out_family=target,profile=profile,predictor=model,
                        mapping=POLICIES[idx],actual_m=a[0],planned_m=p[0],
                        actual_cost=a[1],planned_cost=p[1],
                        actual_m_deviation=deviations[0],actual_c_deviation=deviations[1],
                        trained_m_width=epsilon[0],trained_c_width=epsilon[1]))
            certified=0;incorrect=0;actual_dom=0;recall=0;retained=set(range(16))
            for i,j in itertools.combinations(range(16),2):
                predicted=cert(planned[i],planned[j],epsilon)
                observed=dom(truth[i],truth[j])
                if observed:actual_dom+=1
                if predicted:
                    certified+=1
                    retained.discard(j if predicted==1 else i)
                    if predicted==observed:recall+=1
                    else:
                        incorrect+=1
                        mistakes.append(dict(held_out_family=target,profile=profile,
                            predictor=model,policy_a=POLICIES[i],policy_b=POLICIES[j],
                            certificate=predicted,actual_relation=observed,
                            held_out_a_is_covered=int(all(abs(x/y-1)<=e for x,y,e in zip(truth[i],planned[i],epsilon))),
                            held_out_b_is_covered=int(all(abs(x/y-1)<=e for x,y,e in zip(truth[j],planned[j],epsilon)))))
            if certified>120 or len(retained)<1:raise AssertionError("Impossible certification")
            actual_nd=baseline.ndidx(truth)
            r15=(max(x[0] for x in truth)*1.5+1e-6,
                 max(x[1] for x in truth)*1.5+1e-6)
            r30=(max(x[0] for x in truth)*3.0+1e-6,
                 max(x[1] for x in truth)*3.0+1e-6)
            fraction15=baseline.hv([truth[i] for i in sorted(retained)],r15)/baseline.hv(truth,r15)
            fraction30=baseline.hv([truth[i] for i in sorted(retained)],r30)/baseline.hv(truth,r30)
            blocks.append(dict(held_out_family=target,profile=profile,predictor=model,
                trained_m_width=epsilon[0],trained_c_width=epsilon[1],
                training_points=64,test_points=16,point_failures=len(failures),
                test_joint_coverage=(16-len(failures))/16,
                certified_pairs=certified,abstained_pairs=120-certified,
                wrong_confident_certificates=incorrect,correct_certificates=certified-incorrect,
                actual_dominance_pairs=actual_dom,
                dominance_recall=recall/actual_dom if actual_dom else "",
                certification_precision=(certified-incorrect)/certified if certified else "",
                kept=len(retained),lost_true_nd=len(actual_nd-retained),
                true_HV15_retained_fraction=fraction15,true_HV30_retained_fraction=fraction30,
                failed_genotype_ids="|".join(f["mapping"] for f in failures)))
    if len(folds)!=6 or len(blocks)!=12:raise AssertionError("Incomplete whole-family-blocked evaluation")
    write(out/"all_6_training_family_widths.csv",folds)
    write(out/"all_12_held_out_speed_block_certifications.csv",blocks)
    if mistakes:
        write(out/"all_false_certifications.csv",mistakes)
    else:
        (out/"all_false_certifications.txt").write_text(
            "No false certification in this familiar three-family cohort; no distribution-free claim.\n",
            encoding="utf-8")
    report=[
        "# Three-family blocked error-envelopes for conservative Pareto pruning",
        "",
        "Only six original immutable DAX/profile artifacts from WorkflowSim run 41695356307. Training uses 64 points from two complete other DAG families, while evaluation uses the held-out family's 32 points (default+staggered). Error widths are TWO coordinate-specific maximum abs(actual/planned - 1) values plus 1e-9 numerical buffer. This is a leave-one-family-out STRESS TEST on KNOWN families, not a new prospective external holdout.",
        "",
        "| Held-out DAG | Model | Trained M bound | Trained C bound | Held-out joint covered / 32 | Confident certificates / 240 | False certificates | Kept mean / 16 | Mean true HV recovered |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for target,model in itertools.product(DAGS,MODELS):
        fold=next(x for x in folds if x["held_out_family"]==target and x["predictor"]==model)
        zz=[x for x in blocks if x["held_out_family"]==target and x["predictor"]==model]
        report.append(
            f"| {target} | {model} | {100*fold['test_m_width']:.3f}% | "
            f"{100*fold['test_c_width']:.4f}% | "
            f"{sum(16-x['point_failures'] for x in zz)}/32 | "
            f"{sum(x['certified_pairs'] for x in zz)}/240 | "
            f"{sum(x['wrong_confident_certificates'] for x in zz)} | "
            f"{statistics.mean(x['kept'] for x in zz):.2f} | "
            f"{100*statistics.mean(x['true_HV15_retained_fraction'] for x in zz):.6f}% |")
    report+=["","## Failure interpretation"]
    for model in MODELS:
        zz=[x for x in blocks if x["predictor"]==model]
        report.append(
            f"- {model}: held-out point coverage {sum(16-x['point_failures'] for x in zz)}/96, "
            f"certified {sum(x['certified_pairs'] for x in zz)}/720, "
            f"false confident {sum(x['wrong_confident_certificates'] for x in zz)}, "
            f"mean survivors {statistics.mean(x['kept'] for x in zz):.2f}/16.")
    for x in blocks:
        if x["point_failures"] or x["wrong_confident_certificates"] or x["lost_true_nd"]:
            report.append(f"- {x['held_out_family']}/{x['profile']}/{x['predictor']}: "
                f"point coverage failures={x['point_failures']} ({x['failed_genotype_ids']}), "
                f"false certified={x['wrong_confident_certificates']}, "
                f"true actual nondominated candidates discarded={x['lost_true_nd']}.")
    report+=["",
       "## Scientific decision",
       "Even a maximum-error envelope over two known families does not mathematically cover a third family. Any uncovered real point disproves deterministic transfer of that empirical maximum as a universal safety guarantee. A low false-certification count alone does not establish calibrated confidence.",
       "Real HV recovery only measures the 16 frozen physical VM assignments, not an algorithm-population true Pareto front. Some assignments are unrealistic; two speed profiles per DAG are correlated.",
       "All source real labels were available in the archive, but the frozen algorithm for each fold uses only the OTHER families' labels to construct its widths; held-out truth enters scoring only. No new WorkflowSim or optimizer experiment, no FLA search change, no default promotion, no SCI Q1 claim. master unchanged."
    ]
    (out/"family_blocked_error_interval_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: family_interval.py IMMUTABLE_96_SOURCE_ARTIFACTS OUTPUT")
    evaluate(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
