#!/usr/bin/env python3
"""Retrospective decision-identifiability check on already-audited 32-map truth.

Source = untouched original true source 42019263313, faithfully exported by
independent strict audit 42019608367 (attempt 2 success). This is NOT a
new experiment or a prospective test of OLD/READY forecasting.
"""
import csv
import itertools
import math
import pathlib
import sys

DAGS=("Inspiral_30","Sipht_30","Epigenomics_100","CyberShake_50")
PROFILES=("default","staggered")
N=32
TOL=1e-10

def read(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def save(path,rows):
    assert rows
    with path.open("w",newline="",encoding="utf-8") as f:
        wr=csv.DictWriter(f,fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)

def hv(points,ref):
    best_cost=float("inf")
    top=ref[1]
    area=0.
    for m,c in sorted(set(points)):
        if c<best_cost:
            best_cost=c
            if m<ref[0] and c<top:
                area+=(ref[0]-m)*(top-c)
                top=c
    out=area/(ref[0]*ref[1])
    assert math.isfinite(out) and 0<=out<=1+TOL
    return out

def dominates(a,b):
    return a[0]<=b[0] and a[1]<=b[1] and (a[0]<b[0] or a[1]<b[1])

def planned_greedy(points,names,k=4):
    # Match the original independent forecast-only scorer and its immutable
    # predicted HV reference, normalized scalar and lexicographic tie break.
    ref=(1.5*max(x[0] for x in points)+1e-6,
         1.5*max(x[1] for x in points)+1e-6)
    maxes=(max(x[0] for x in points),max(x[1] for x in points))
    selected=[]
    for _ in range(k):
        prior=hv([points[j] for j in selected],ref)
        ranked=[]
        for j in range(len(points)):
            if j in selected:continue
            delta=hv([points[q] for q in selected]+[points[j]],ref)-prior
            scalar=points[j][0]/maxes[0]+points[j][1]/maxes[1]
            ranked.append((-delta,scalar,names[j],j))
        selected.append(min(ranked)[3])
    return [names[j] for j in selected]

def audit(root,out):
    out.mkdir(parents=True,exist_ok=True)
    source=root/"fla-independent32-true-k4-audit-42019608367"
    assert source.is_dir(),("Original verified audit artifact absent",str(source))
    original=read(source/"all_256_original_same_mapping_truth.csv")
    decision=read(source/"all_40_k4_oracle_regrets.csv")
    assert len(original)==256 and len(decision)==40
    assert {r["method"] for r in decision}=={
        "old","ready","blind","first16_old","first16_ready"}
    shas={r["original_source_sha"] for r in decision}
    assert len(shas)==1 and len(next(iter(shas)))==40
    data=[]
    for dag,profile in itertools.product(DAGS,PROFILES):
        case=[r for r in original if (r["workflow"],r["vm_profile"])==(dag,profile)]
        assert len(case)==32 and len({r["policy"] for r in case})==32
        actual={r["policy"]:(float(r["actual_makespan"]),float(r["actual_cost"]))
                for r in case}
        assert all(math.isfinite(v) and v>0 for t in actual.values() for v in t)
        points=list(actual.values())
        reference=(1.5*max(p[0] for p in points)+1e-6,
                   1.5*max(p[1] for p in points)+1e-6)
        all_hv=hv(points,reference)
        nd={key for key,pt in actual.items() if not any(
            dominates(q,pt) for other,q in actual.items() if key!=other)}
        block={r["method"]:r for r in decision if
               (r["workflow"],r["vm_profile"])==(dag,profile)}
        assert set(block)=={"old","ready","blind","first16_old","first16_ready"}
        maxima={}
        optimal_count={}
        for k in range(1,5):
            best=-1.
            nbest=0
            for choice in itertools.combinations(points,k):
                result=hv(choice,reference)
                if result>best+TOL:
                    best=result
                    nbest=1
                elif abs(result-best)<=TOL:
                    nbest+=1
            maxima[k]=best
            optimal_count[k]=nbest
        assert math.isclose(maxima[4],float(block["old"]["true_oracle_k4_15"]),
                            rel_tol=0,abs_tol=TOL),(dag,profile,"Oracle mismatch")
        selected={}
        for predictor in ("old","ready"):
            labels=block[predictor]["selected_policies"].split("|")
            assert len(labels)==4 and len(set(labels))==4 and set(labels)<=set(actual)
            actualhv=hv([actual[x] for x in labels],reference)
            assert math.isclose(actualhv,float(block[predictor]["true_hv_k4_15"]),
                                rel_tol=0,abs_tol=TOL)
            selected[predictor]=labels
        assert bool(set(selected["old"])!=set(selected["ready"]))==bool(
            int(block["old"]["old_ready_K4_set_differs"]))
        policies=[r["policy"] for r in case]
        forecast_orders={}
        for predictor in ("old","ready"):
            pred=[(float(r[predictor+"_pred_m"]),float(r[predictor+"_pred_cost"]))
                  for r in case]
            forecast_orders[predictor]=planned_greedy(pred,policies)
            assert forecast_orders[predictor]==selected[predictor],(
                "Forecast-only greedy decision changed",dag,profile,predictor)
        prefix_differences={
            k:int(set(forecast_orders["old"][:k])!=set(forecast_orders["ready"][:k]))
            for k in (1,2,3,4)}
        # Each observed prefix is evaluated solely against independently computed
        # true-label hindsight oracle at the SAME K. These are retrospective
        # diagnostic regrets, never used to choose forecasts or mappings.
        prefix_regret={}
        prefix_actual_hv={}
        for predictor in ("old","ready"):
            for k in (1,2,3,4):
                chosen=forecast_orders[predictor][:k]
                value=hv([actual[x] for x in chosen],reference)
                regret=maxima[k]-value
                assert regret>=-TOL,(dag,profile,predictor,k,regret)
                prefix_actual_hv[predictor,k]=value
                prefix_regret[predictor,k]=max(0.,regret)
        assert math.isclose(prefix_regret["old",4],
                            maxima[4]-hv([actual[x] for x in selected["old"]],reference),
                            rel_tol=0,abs_tol=TOL)
        data.append(dict(workflow=dag,vm_profile=profile,
            old_ready_k1_set_differs=prefix_differences[1],
            old_ready_k2_set_differs=prefix_differences[2],
            old_ready_k3_set_differs=prefix_differences[3],
            old_ready_k4_prefix_set_differs=prefix_differences[4],
            old_ready_full_K4_order_differs=int(forecast_orders["old"]!=forecast_orders["ready"]),
            actual_true_pareto_policies=len(nd),
            selected_old_true_nd_members=sum(x in nd for x in selected["old"]),
            old_ready_k4_set_differs=int(set(selected["old"])!=set(selected["ready"])),
            best_k1_true_hv=maxima[1],
            best_k2_true_hv=maxima[2],
            best_k3_true_hv=maxima[3],
            best_k4_true_hv=maxima[4],
            complete_32_true_hv=all_hv,
            full_minus_k4_true_hv=all_hv-maxima[4],
            k4_minus_k3_true_hv=maxima[4]-maxima[3],
            equivalent_best_k4_combinations=optimal_count[4],
            total_four_subsets=math.comb(32,4),
            fraction_optimal_four_subsets=optimal_count[4]/math.comb(32,4),
            **{f"{model}_k{k}_true_hv":prefix_actual_hv[model,k]
               for model in ("old","ready") for k in (1,2,3,4)},
            **{f"{model}_k{k}_true_regret":prefix_regret[model,k]
               for model in ("old","ready") for k in (1,2,3,4)},
            old_regret=prefix_regret["old",4],
            ready_regret=prefix_regret["ready",4],
            original_source_sha=next(iter(shas))))
    assert len(data)==8
    save(out/"all_8_fixed32_decision_identifiability.csv",data)
    assert all(r["old_ready_k4_set_differs"] == 0 for r in data)
    assert all(r["old_k4_true_regret"] <= TOL and
               r["ready_k4_true_regret"] <= TOL for r in data)
    lines=[
      "# Original 32-genotype K4 experiment: decision identifiability",
      "",
      "**Retrospective source-verified diagnostic, NOT a new prospective forecasting trial.**",
      "Original real simulator run 42019263313 (8/8 PASS); strict audit 42019608367",
      "(attempt 2 PASS). The present read-only audit consumes the already-verified",
      "256 true mapping observations and 40 prior decision outputs, checks original",
      "single source SHA and actual HV oracle consistency.",
      "",
      "| Workflow | VM profile | True nondominated maps | K4 − K3 true HV | Full 32 − K4 true HV | Equivalent optimal K4 subsets |",
      "|---|---|---:|---:|---:|---:|",
    ]
    for r in data:
        lines.append(f"| {r['workflow']} | {r['vm_profile']} | "
          f"{r['actual_true_pareto_policies']} | {r['k4_minus_k3_true_hv']:+.9f} | "
          f"{r['full_minus_k4_true_hv']:+.9f} | "
          f"{r['equivalent_best_k4_combinations']} / 35960 |")
    easy=sum(r["actual_true_pareto_policies"]<=4 for r in data)
    saturated=sum(abs(r["k4_minus_k3_true_hv"])<=TOL for r in data)
    tied=sum(r["equivalent_best_k4_combinations"]>1 for r in data)
    lines+=["",f"- True Pareto front cardinality <= K4 in **{easy}/8** cases.",
           f"- Adding the fourth mapping after the true K3 optimum changes HV by ~0 in **{saturated}/8** cases.",
           f"- More than one true-HV-optimal K4 subset exists in **{tied}/8** cases.",
           f"- OLD and READY select different physical K4 sets in "
           f"**{sum(r['old_ready_k4_set_differs'] for r in data)}/8** cases.",
           f"- OLD/READY physical prefix-set disagreements at K=1,2,3,4: "
           + ", ".join(str(sum(r[f'old_ready_k{k}_set_differs'] for r in data))+"/8"
                       for k in (1,2,3,4))+".",
           f"- OLD/READY entire ordered greedy K4 sequences disagree in "
           f"**{sum(r['old_ready_full_K4_order_differs'] for r in data)}/8** cases.",
           "",
           "| K | OLD/READY physical prefix disagreements (of 8) | "
           "OLD mean true regret | READY mean true regret | "
           "Blocks where both regrets are zero |",
           "|---:|---:|---:|---:|---:|",
           *[
             f"| {k} | {sum(r[f'old_ready_k{k}_set_differs'] for r in data)}/8 | "
             f"{sum(r[f'old_k{k}_true_regret'] for r in data)/8:.9f} | "
             f"{sum(r[f'ready_k{k}_true_regret'] for r in data)/8:.9f} | "
             f"{sum(r[f'old_k{k}_true_regret']<=TOL and r[f'ready_k{k}_true_regret']<=TOL for r in data)}/8 |"
             for k in (1,2,3,4)
           ],
           "",
           "These K-specific regrets use the same 32 existing physical true labels and",
           "an exact hindsight oracle of size K. No new trials or algorithm improvement",
           "are implied by additional retrospective outcome columns.",
           "",
           "The result diagnoses a partially *under-informative evaluation universe*: ",
           "in some blocks K4 can cover the entire finite actual nondominated front.",
           "The exactly optimal 8/8 OLD and READY result is not evidence of a",
           "perfect planner or an unseen-family superior FLA algorithm.",
           "The remaining 3030-source search and any untested VM/DAG regimes are",
           "not implied by these 32 fixed physical genotypes.",
           "No risk feature, OLD/READY tuning, or promotion is authorized by this already-seen cohort."]
    (out/"decision_identifiability_findings.md").write_text(
        "\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))

if __name__=="__main__":
    assert len(sys.argv)==3,"Usage: script.py ORIGINAL_AUDIT_ARTIFACT_ROOT OUTPUT"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
