#!/usr/bin/env python3
"""Read-only three-policy same-mapping Pareto decision audit, original 36 runs."""
import csv, itertools, math, pathlib, statistics, sys

DAGS=("CyberShake_100","Montage_100","Sipht_60")
MAPS=("all_vm0","all_vm12","round_robin","stride7")
POLICIES=("fifo","shortest","upward")

def read(p):
    with p.open(newline="",encoding="utf-8") as h:return list(csv.DictReader(h))
def write(p,values):
    if not values:raise AssertionError("No records")
    with p.open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(values[0]));w.writeheader();w.writerows(values)

def dominates(a,b):
    return all(x<=y for x,y in zip(a,b)) and any(x<y for x,y in zip(a,b))

def nd(data):
    return {a for a in data if not any(dominates(data[b],data[a]) for b in data if b!=a)}

def hv(data,reference):
    rx,ry=reference
    p=sorted(set(data.values()))
    p=[z for z in p if z[0]<rx and z[1]<ry]
    p=[x for x in p if not any(dominates(q,x) for q in p)]
    prev=ry;total=0.0
    for x,y in p:
        if y>=prev:continue
        total+=(rx-x)*(prev-y)
        prev=y
    return total/(rx*ry)

def main(root,out):
    out.mkdir(parents=True,exist_ok=True)
    groups=[];pairs=[];mistakes=[]
    for dag in DAGS:
        dirs=[p for p in root.iterdir() if p.is_dir() and p.name.startswith(f"fla-priority-forecast-{dag}-")]
        if len(dirs)!=1:raise AssertionError(("Need unique original artifact",dag))
        originals={mode:{x["policy"]:x for x in read(dirs[0]/(mode+".csv"))} for mode in POLICIES}
        for mode in POLICIES:
            if set(originals[mode])!=set(MAPS):raise AssertionError(("Source policies incomplete",dag,mode))
        for mapping in MAPS:
            predicted={};actual={}
            for mode in POLICIES:
                row=originals[mode][mapping]
                if (row["workflow"],row["speed"],row["runtime_priority"])!=(dag,"default",mode):
                    raise AssertionError(("Bad source labels",dag,mapping,mode))
                pr=(float(row["policy_model_makespan"]),float(row["policy_model_cost"]))
                ac=(float(row["actual_makespan"]),float(row["actual_cost"]))
                if not all(math.isfinite(x) and x>0 for x in pr+ac):
                    raise AssertionError(("Invalid original objective",dag,mapping,mode,pr,ac))
                predicted[mode]=pr;actual[mode]=ac
            predicted_nd=nd(predicted)
            actual_nd=nd(actual)
            both=predicted_nd & actual_nd
            union=predicted_nd | actual_nd
            fp=predicted_nd-actual_nd
            fn=actual_nd-predicted_nd
            jaccard=len(both)/len(union)
            for a,b in itertools.combinations(POLICIES,2):
                def classify(d):
                    if dominates(d[a],d[b]):return "a_dominates_b"
                    if dominates(d[b],d[a]):return "b_dominates_a"
                    return "incomparable"
                predicted_class=classify(predicted);actual_class=classify(actual)
                compare=dict(workflow=dag,mapping=mapping,policy_a=a,policy_b=b,
                    predicted_class=predicted_class,actual_class=actual_class,
                    misclassified=int(predicted_class!=actual_class),
                    true_abs_makespan_diff_pct=100*abs(actual[a][0]-actual[b][0])/min(actual[a][0],actual[b][0]),
                    true_abs_cost_diff_pct=100*abs(actual[a][1]-actual[b][1])/min(actual[a][1],actual[b][1]))
                pairs.append(compare)
                if predicted_class!=actual_class:mistakes.append(compare)
            refs={f:(f*max(x[0] for x in actual.values())+1e-6,
                     f*max(x[1] for x in actual.values())+1e-6) for f in (1.5,3.0)}
            case=dict(workflow=dag,mapping=mapping,
                predicted_nd="|".join(sorted(predicted_nd)),
                actual_nd="|".join(sorted(actual_nd)),
                false_selected="|".join(sorted(fp)),
                false_rejected="|".join(sorted(fn)),
                nd_jaccard=jaccard,precision=len(both)/len(predicted_nd),
                recall=len(both)/len(actual_nd),
                pairs_misclassified=sum(x["misclassified"] for x in pairs if x["workflow"]==dag and x["mapping"]==mapping))
            for factor,ref in refs.items():
                actual_oracle_hv=hv(actual,ref)
                selected_hv=hv({k:actual[k] for k in predicted_nd},ref)
                fifo_hv=hv({"fifo":actual["fifo"]},ref)
                if selected_hv>actual_oracle_hv+1e-10 or fifo_hv>actual_oracle_hv+1e-10:
                    raise AssertionError("Impossible HV coverage")
                case.update({f"all3_actual_hv_{factor}":actual_oracle_hv,
                             f"model_selected_actual_hv_{factor}":selected_hv,
                             f"fifo_actual_hv_{factor}":fifo_hv,
                             f"selected_coverage_{factor}":selected_hv/actual_oracle_hv,
                             f"fifo_coverage_{factor}":fifo_hv/actual_oracle_hv,
                             f"selected_minus_fifo_hv_{factor}":selected_hv-fifo_hv})
            groups.append(case)
    if (len(groups),len(pairs))!=(12,36):raise AssertionError("Missing source records")
    write(out/"all_12_same_mapping_pareto_groups.csv",groups)
    write(out/"all_36_true_vs_predicted_pairwise_dominance.csv",pairs)
    if mistakes:write(out/"all_pareto_class_errors.csv",mistakes)
    report=["# Actual simulator same-mapping three-policy Pareto rank and coverage",
        "", "Source immutable **36 true WorkflowSim results**: [Actions 41681448520](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41681448520). No new simulator or optimizer calls. Each exact Task→VM assignment held fixed across FIFO, SJF and UPWARD.",
        f"All 12 exact placement groups and 36 policy-pair comparisons checked. **Dominance class disagreements: {len(mistakes)}/36**, mean model-vs-actual ND Jaccard {statistics.mean(x['nd_jaccard'] for x in groups):.6f}.",
        "", "| DAG | Placement | Predicted ND policies | Real ND policies | Jaccard | Dominance errors | Predicted-front actual HV / all-three actual HV (1.5x) | FIFO actual HV / all-three (1.5x) |",
        "|---|---|---|---|---:|---:|---:|---:|"]
    for x in groups:
        report.append(f"| {x['workflow']} | {x['mapping']} | {x['predicted_nd']} | {x['actual_nd']} | "
           f"{x['nd_jaccard']:.3f} | {x['pairs_misclassified']} | "
           f"{x['selected_coverage_1.5']:.6f} | {x['fifo_coverage_1.5']:.6f} |")
    report+=["",
       "## Materiality of exact Pareto disagreements (absolute true objective separation)",
       "Note: this is a post-hoc descriptive stratification; the preregistration required reporting 0.01% and 0.1% epsilon context. Neither threshold magically resolves the full two-objective tradeoff.",
    ]
    for tolerance in (0.01,0.1):
        flagged=[p for p in pairs if max(p["true_abs_makespan_diff_pct"],p["true_abs_cost_diff_pct"])>tolerance]
        errors=[p for p in flagged if p["misclassified"]]
        report.append(f"- At least one actual objective differs by more than {tolerance}%: "
            f"{len(flagged)}/36 pairs; exact Pareto classification disagreement "
            f"{len(errors)}/{len(flagged) if flagged else 0} such material pairs.")
        for error in errors:
            report.append(f"  - {error['workflow']} {error['mapping']} "
               f"{error['policy_a']} vs {error['policy_b']}: "
               f"real M separation {error['true_abs_makespan_diff_pct']:.6f}%, "
               f"real Cost separation {error['true_abs_cost_diff_pct']:.6f}%, "
               f"predicted {error['predicted_class']} vs actual {error['actual_class']}.")
    report+=["",f"Mean actual HV coverage by model-selected nondominated policies {statistics.mean(x['selected_coverage_1.5'] for x in groups):.6f}, by unconditional FIFO {statistics.mean(x['fifo_coverage_1.5'] for x in groups):.6f}.",
       f"Cases model-selected actual HV higher than FIFO: {sum(x['selected_minus_fifo_hv_1.5']>1e-10 for x in groups)}/12; equal: {sum(abs(x['selected_minus_fifo_hv_1.5'])<=1e-10 for x in groups)}/12; lower: {sum(x['selected_minus_fifo_hv_1.5']< -1e-10 for x in groups)}/12.",
       "", "## Errors including known negative controls"]
    if not mistakes:report.append("No raw Pareto class mistakes observed in these fixed placements.")
    for x in mistakes:
        report.append(f"- {x['workflow']} {x['mapping']} {x['policy_a']} vs {x['policy_b']}: predicted {x['predicted_class']}, real {x['actual_class']}; real Makespan difference {x['true_abs_makespan_diff_pct']:.6f}% and Cost difference {x['true_abs_cost_diff_pct']:.6f}%.")
    report+=["",
      "## Scope and research decision",
      "This is a tiny three-policy Pareto universe for EACH fixed task-to-VM mapping, not real scheduling Pareto HV over varying VM assignments and certainly not a new FLA solver. The same group of DAXs was involved in estimator development and has a known CyberShake SJF sign failure.",
      "Very small cost differences can change exact Pareto classification even when practical cost impact is negligible; all raw signed changes and full 3.0× reference sensitivity are preserved.",
      "A real algorithm must use one identical compound priority+VM representation in both FLA and NSGA-II, work on unseen DAG families and be judged by full K16 actual HV and computation budgets; no default promotion is supported."
    ]
    (out/"three_policy_true_pareto_rank_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: script.py ORIGINAL_ARTIFACTS OUTPUT")
    main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
