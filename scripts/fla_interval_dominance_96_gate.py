#!/usr/bin/env python3
"""Read-only uncertainty-interval dominance gate on frozen 96 WorkflowSim jobs.

All decisions are functions of planned objectives and fixed epsilon alone.
Real simulator labels are used only to score certification and retained fronts.
No fit, no learned bound, no simulator replay.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fla_algorithm_independent_same_mapping_rank_audit as source

EPSILONS=(0.001,0.01,0.05,0.10,0.25)
MODELS=("old","ready")
DAGS=source.DAGS
SPEEDS=source.SPEEDS
POLICIES=source.POLICIES

def write(path,records):
    if not records:
        raise AssertionError(("Missing original records",path))
    with path.open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)

def dominance(a,b):
    # 1 means A dominates B; -1 B dominates A; 0 neither.
    if all(x<=y for x,y in zip(a,b)) and any(x<y for x,y in zip(a,b)):
        return 1
    if all(y<=x for x,y in zip(a,b)) and any(y<x for x,y in zip(a,b)):
        return -1
    return 0

def certified(a,b,epsilon):
    # Strictly better on BOTH dimensions, a conservative sufficient condition.
    if all((1+epsilon)*x < (1-epsilon)*y for x,y in zip(a,b)):
        return 1
    if all((1+epsilon)*y < (1-epsilon)*x for x,y in zip(a,b)):
        return -1
    return 0

def main(original,out):
    groups,sha=source.load(original)
    out.mkdir(parents=True,exist_ok=True)
    per_point=[]
    per_group=[]
    errors=[]
    for dag,speed in itertools.product(DAGS,SPEEDS):
        original_rows=[groups[(dag,speed)][policy] for policy in POLICIES]
        actual=[(float(r["actual_makespan"]),float(r["actual_cost"])) for r in original_rows]
        ref15=(1.5*max(p[0] for p in actual)+1e-6,
               1.5*max(p[1] for p in actual)+1e-6)
        ref30=(3.0*max(p[0] for p in actual)+1e-6,
               3.0*max(p[1] for p in actual)+1e-6)
        full15=source.hv(actual,ref15)
        full30=source.hv(actual,ref30)
        if full15<=0 or full30<=0:
            raise AssertionError(("Nonpositive source full HV",dag,speed))
        actual_nd=source.ndidx(actual)
        for model,eps in itertools.product(MODELS,EPSILONS):
            planned=[(float(r[f"{model}_planned_makespan"]),
                      float(r[f"{model}_planned_cost"])) for r in original_rows]
            pair_total=0;cert_n=0;false_cert=0;actual_dom=0;recalled=0
            joint=0;mcover=0;ccover=0
            for i,(p,a) in enumerate(zip(planned,actual)):
                relative=(abs(p[0]-a[0])/p[0],abs(p[1]-a[1])/p[1])
                cm=relative[0]<=eps
                cc=relative[1]<=eps
                joint+=int(cm and cc);mcover+=int(cm);ccover+=int(cc)
                per_point.append(dict(workflow=dag,vm_speed=speed,
                    predictor=model,epsilon_fraction=eps,source_sha=sha,
                    policy=POLICIES[i],planned_m=p[0],planned_c=p[1],
                    actual_m=a[0],actual_c=a[1],
                    abs_relative_m_error=relative[0],
                    abs_relative_c_error=relative[1],
                    m_inside=int(cm),c_inside=int(cc),joint_inside=int(cm and cc)))
            retained=set(range(16))
            for i,j in itertools.combinations(range(16),2):
                pair_total+=1
                pred=certified(planned[i],planned[j],eps)
                truth=dominance(actual[i],actual[j])
                if truth:actual_dom+=1
                if pred:
                    cert_n+=1
                    if pred==truth:recalled+=1
                    else:
                        false_cert+=1
                        errors.append(dict(workflow=dag,vm_speed=speed,
                            predictor=model,epsilon_fraction=eps,
                            policy_a=POLICIES[i],policy_b=POLICIES[j],
                            certified_direction=pred,true_direction=truth,
                            a_m_error=abs(planned[i][0]-actual[i][0])/planned[i][0],
                            a_c_error=abs(planned[i][1]-actual[i][1])/planned[i][1],
                            b_m_error=abs(planned[j][0]-actual[j][0])/planned[j][0],
                            b_c_error=abs(planned[j][1]-actual[j][1])/planned[j][1]))
                    retained.discard(j if pred==1 else i)
            if pair_total!=120:raise AssertionError("Incomplete pair comparisons")
            kept_points=[actual[i] for i in sorted(retained)]
            recovery15=source.hv(kept_points,ref15)/full15
            recovery30=source.hv(kept_points,ref30)/full30
            if recovery15>1+1e-8 or recovery30>1+1e-8:
                raise AssertionError("Retained truth outperforms full truth")
            per_group.append(dict(workflow=dag,vm_speed=speed,
                predictor=model,epsilon_fraction=eps,source_sha=sha,
                total_pairs=120,certified_pairs=cert_n,abstained_pairs=120-cert_n,
                actual_dominance_pairs=actual_dom,
                correct_certified=cert_n-false_cert,
                false_certified=false_cert,
                certified_precision=(cert_n-false_cert)/cert_n if cert_n else "",
                true_dominance_recall=recalled/actual_dom if actual_dom else "",
                certified_fraction=cert_n/120,
                joint_point_coverage=joint/16,m_coverage=mcover/16,
                cost_coverage=ccover/16,
                kept=len(retained),discarded=16-len(retained),
                true_nd_lost=len(actual_nd-retained),
                real_hv15_coverage=recovery15,real_hv30_coverage=recovery30))
    if (len(per_point),len(per_group))!=(960,60):
        raise AssertionError(("Incomplete 96*2*5 points / six*2*5 groups",
                              len(per_point),len(per_group)))
    write(out/"all_960_interval_point_checks.csv",per_point)
    write(out/"all_60_group_interval_dominance_scores.csv",per_group)
    if errors:
        write(out/"all_false_confident_certifications.csv",errors)
    else:
        (out/"all_false_confident_certifications.txt").write_text(
            "Zero observed false confident decisions in this frozen cohort. This does NOT establish calibrated validity.\n",
            encoding="utf-8")
    report=[
        "# Frozen theoretical interval-dominance and real WorkflowSim coverage",
        "",
        "This is a read-only audit of 96 original true WorkflowSim results, immutable source Actions 41695356307, original source Java SHA "+sha+". There are six DAG/speed blocks and 16 fixed placement genotypes in each. No new optimizer, simulation, fitting, calibration or bound tuning.",
        "The intervals are symmetric around the MODEL prediction: each objective interval is [p(1-epsilon),p(1+epsilon)]. A certification A≺B requires BOTH upper_A < lower_B coordinates. Safety is provable only IF the real objectives are jointly covered by the declared intervals; this fixed epsilon is not a calibrated guarantee.",
        "",
        "| Predictor | Relative bound epsilon | Joint actual-point coverage | Certified source pairs / 720 | Wrong certified / certified | Correct-class precision | True dominance recall | Average kept /16 | Mean real HV15 coverage |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    ]
    for model,eps in itertools.product(MODELS,EPSILONS):
        z=[x for x in per_group if x["predictor"]==model and x["epsilon_fraction"]==eps]
        points=[p for p in per_point if p["predictor"]==model and p["epsilon_fraction"]==eps]
        cert=sum(x["certified_pairs"] for x in z)
        wrong=sum(x["false_certified"] for x in z)
        right=cert-wrong
        actual_dom=sum(x["actual_dominance_pairs"] for x in z)
        report.append(
            f"| {model} | {eps*100:.1f}% | "
            f"{sum(x['joint_inside'] for x in points)}/96 | "
            f"{cert}/720 | {wrong}/{cert} | "
            f"{right/cert:.4f}" if False else ""
        )
        # Construct row separately to avoid conditional operator precedence.
        report[-1]=(
            f"| {model} | {eps*100:.1f}% | "
            f"{sum(x['joint_inside'] for x in points)}/96 | {cert}/720 | "
            f"{wrong}/{cert} | {f'{right/cert:.4f}' if cert else 'n/a'} | "
            f"{f'{right/actual_dom:.4f}' if actual_dom else 'n/a'} | "
            f"{statistics.mean(x['kept'] for x in z):.2f} | "
            f"{100*statistics.mean(x['real_hv15_coverage'] for x in z):.6f}% |"
        )
    report.extend(["",
        "## Coverage failures and practical adverse cases"])
    for model in MODELS:
        pp=[p for p in per_point if p["predictor"]==model and p["epsilon_fraction"]==0.25]
        maxm=max(pp,key=lambda p:p["abs_relative_m_error"])
        maxc=max(pp,key=lambda p:p["abs_relative_c_error"])
        report.append(
            f"- {model}: worst Makespan error relative to planned = "
            f"{100*maxm['abs_relative_m_error']:.4f}% "
            f"({maxm['workflow']}, {maxm['vm_speed']}, {maxm['policy']}); "
            f"worst Cost error = {100*maxc['abs_relative_c_error']:.4f}% "
            f"({maxc['workflow']}, {maxc['vm_speed']}, {maxc['policy']}).")
    for p in errors[:30]:
        report.append(f"- False certainty: {p['workflow']}/{p['vm_speed']} "
            f"{p['predictor']} eps={p['epsilon_fraction']:.3f} "
            f"{p['policy_a']} vs {p['policy_b']}, "
            f"predicted orientation {p['certified_direction']}, real {p['true_direction']}.")
    if len(errors)>30:
        report.append(f"- Additional {len(errors)-30} false-certainty cases preserved in the full CSV.")
    report.extend(["",
        "## Interpretation and limitations",
        "The 720 pairs per predictor/epsilon share the same 96 observations and are NOT independent 720 test cases. All three DAG families are historically familiar and some placement policies are unrealistic extremes.",
        "A zero wrong-certification count may reflect near-total abstention, not a good Pareto selector. A 100% retained real HV fraction may be obtained by retaining all sixteen, so report both coverage AND kept count.",
        "The actual values enter ONLY scoring, never epsilon selection, interval construction, certification or shortlist decisions. None of these static epsilons was calibrated with an independent training split.",
        "This is a theoretical feasibility gate, not a validated uncertainty interval or adaptive high-fidelity evolutionary FLA. No READY budgets, search-wall-time or SCI Q1 performance improvement are established.",
        "All original FLA-v12, seeded NSGA-II and FIFO default paths are untouched; no changes to master."
    ])
    (out/"interval_dominance_read_only_report.md").write_text(
        "\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: interval_gate.py SIX_ORIGINAL_SOURCE_ARTIFACTS OUTPUT")
    main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
