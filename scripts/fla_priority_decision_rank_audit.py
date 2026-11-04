#!/usr/bin/env python3
"""Read-only priority decision rank/regret from immutable actual WorkflowSim archives.

No planning, simulation or tuning. All source 8 blocks x 3 policies MUST exist.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

DAGS=("Inspiral_30","Epigenomics_100")
SPEEDS=("default","staggered")
MAPPINGS=("round_robin","stride7")
PRIORITIES=("fifo","shortest","upward")
THRESHOLD=0.001   # material absolute relative Makespan difference = 0.1%
TIE_TOL=1e-9

def load(file):
    with file.open(newline="",encoding="utf-8") as h:return list(csv.DictReader(h))
def put(file,rows):
    if not rows:raise AssertionError(("Empty derived results",file))
    with file.open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def number(row,key):
    value=float(row[key])
    if not math.isfinite(value) or value<0:raise AssertionError(("Invalid value",key,value))
    return value

def main(src,out):
    if not src.is_dir():raise AssertionError("No original artifacts")
    out.mkdir(parents=True,exist_ok=True)
    all_cases=[]
    pairwise=[]
    choices=[]
    for dag,speed,mapping in itertools.product(DAGS,SPEEDS,MAPPINGS):
        prefix=f"fla-new-instance-priority-{dag}-{speed}-{mapping}-"
        dirs=[p for p in src.iterdir() if p.is_dir() and p.name.startswith(prefix)]
        if len(dirs)!=1:raise AssertionError(("Missing or duplicate source",prefix,[str(x) for x in dirs]))
        original=load(dirs[0]/"three_actual_priority_forecasts.csv")
        if len(original)!=3 or {x["priority"] for x in original}!=set(PRIORITIES):
            raise AssertionError(("Expected EXACT three source policies",prefix))
        cases={}
        for row in original:
            policy=row["priority"]
            if (row["workflow"],row["vm_profile"],row["placement"])!=(dag,speed,mapping):
                raise AssertionError(("Provenance mismatch",prefix,row))
            actual=number(row,"actual_makespan")
            predicted=number(row,"actual_makespan")+0 # overwritten from archived original individual csv below
            if actual<=0:raise AssertionError("Zero observed Makespan")
            # The derived artifact has actual Makespan and actual/predicted changes
            # against FIFO, but not standalone predicted Makespan. Recover forecast
            # from RAW original policy CSV, which is also archived in the same artifact.
            raw=load(dirs[0]/(policy+".csv"))
            if len(raw)!=1 or raw[0]["runtime_priority"]!=policy or raw[0]["policy"]!=mapping:
                raise AssertionError(("Missing exact original forecast",prefix,policy))
            rawrow=raw[0]
            if rawrow["workflow"]!=dag or rawrow["speed"]!=speed:
                raise AssertionError(("Wrong raw source identifiers",prefix,policy))
            predicted=number(rawrow,"policy_model_makespan")
            actual_cost=number(rawrow,"actual_cost")
            pred_cost=number(rawrow,"policy_model_cost")
            if predicted<=0 or actual_cost<=0:raise AssertionError("Invalid source objective")
            if not math.isclose(float(rawrow["actual_makespan"]),actual,rel_tol=1e-10,abs_tol=1e-6):
                raise AssertionError(("Raw/derived actual disagreement",prefix,policy))
            cases[policy]=dict(policy=policy,real=actual,pred=predicted,
                               real_cost=actual_cost,pred_cost=pred_cost)
            all_cases.append(dict(workflow=dag,vm_profile=speed,mapping=mapping,
                                  priority=policy,actual_makespan=actual,
                                  predicted_makespan=predicted,actual_cost=actual_cost,
                                  predicted_cost=pred_cost))
        fifo=cases["fifo"]
        for policy,case in cases.items():
            real=100*(case["real"]/fifo["real"]-1)
            predicted=100*(case["pred"]/fifo["pred"]-1)
            if not math.isclose(real,float(next(x for x in original if x["priority"]==policy)["actual_effect_pct"]),abs_tol=1e-6,rel_tol=1e-7):
                raise AssertionError(("Original actual effect mismatch",prefix,policy))
            if not math.isclose(predicted,float(next(x for x in original if x["priority"]==policy)["predicted_effect_pct"]),abs_tol=1e-6,rel_tol=1e-7):
                raise AssertionError(("Original predicted effect mismatch",prefix,policy))
        for a,b in itertools.combinations(PRIORITIES,2):
            pa,pb=cases[a],cases[b]
            true_gap=100*(pb["real"]/pa["real"]-1)
            predicted_gap=100*(pb["pred"]/pa["pred"]-1)
            material=abs(pa["real"]-pb["real"])/min(pa["real"],pb["real"])>THRESHOLD
            true_dir= 1 if true_gap>0 else (-1 if true_gap<0 else 0)
            pred_dir= 1 if predicted_gap>0 else (-1 if predicted_gap<0 else 0)
            pairwise.append(dict(workflow=dag,vm_profile=speed,mapping=mapping,
                                 policy_a=a,policy_b=b,
                                 actual_b_minus_a_pct=true_gap,
                                 predicted_b_minus_a_pct=predicted_gap,
                                 material=int(material),
                                 direction_correct=int(material and true_dir==pred_dir),
                                 actual_cost_a=pa["real_cost"],actual_cost_b=pb["real_cost"],
                                 predicted_cost_a=pa["pred_cost"],predicted_cost_b=pb["pred_cost"]))
        min_model=min(x["pred"] for x in cases.values())
        selection=next(x for x in PRIORITIES if cases[x]["pred"]<=min_model*(1+TIE_TOL))
        actual_best=min(x["real"] for x in cases.values())
        predicted_choice_real=cases[selection]["real"]
        fifo_real=fifo["real"]
        regret=100*(predicted_choice_real/actual_best-1)
        fifo_regret=100*(fifo_real/actual_best-1)
        if regret< -1e-7 or fifo_regret< -1e-7:raise AssertionError("Negative actual regret")
        choices.append(dict(workflow=dag,vm_profile=speed,mapping=mapping,
                            model_selected_policy=selection,
                            selected_actual_makespan=predicted_choice_real,
                            oracle_best_actual_makespan=actual_best,
                            model_regret_pct=regret,
                            fifo_actual_makespan=fifo_real,
                            fifo_regret_pct=fifo_regret,
                            selected_actual_cost=cases[selection]["real_cost"],
                            fifo_actual_cost=fifo["real_cost"]))
    if (len(all_cases),len(pairwise),len(choices))!=(24,24,8):
        raise AssertionError(("Incomplete expected source",len(all_cases),len(pairwise),len(choices)))
    put(out/"all_24_verified_actual_and_predicted_policy_points.csv",all_cases)
    put(out/"all_24_policy_pairwise_rank_decisions.csv",pairwise)
    put(out/"all_8_before_truth_policy_decisions.csv",choices)
    material=[x for x in pairwise if x["material"]]
    right=[x for x in material if x["direction_correct"]]
    wrong=[x for x in material if not x["direction_correct"]]
    report=[
        "# Fixed-placement runtime-ready policy decision ranker and regret: read-only archive audit",
        "",
        "Original already-archived actual WorkflowSim source **41682109356**, 8 exact frozen DAX/speed/VM-allocation blocks × 3 policies = 24 source simulations. This audit has **no new simulator and no optimizer calls**.",
        "All original per-policy raw forecast CSV and derived true simulator outcomes were cross-checked before any ranking; those instances are not a research-wide untouched workflow-family holdout.",
        "",
        f"**Material (>0.1% relative true Makespan gap) priority comparisons:** {len(material)}/24. Predicted correct sign on **{len(right)}/{len(material) if material else 0}** such pairs. Remaining comparisons have insufficient actual effect to interpret direction accuracy.",
        "",
        "## Before-truth policy selection and regret (per exact Task→VM placement)",
        "| DAX | VM speed | Placement | Forecast-chosen policy | Actual selected Makespan (s) | Actual best policy Makespan (s) | Forecast decision regret | FIFO regret |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for c in choices:
        report.append(f"| {c['workflow']} | {c['vm_profile']} | {c['mapping']} | "
          f"{c['model_selected_policy']} | {c['selected_actual_makespan']:.6f} | "
          f"{c['oracle_best_actual_makespan']:.6f} | {c['model_regret_pct']:.6f}% | "
          f"{c['fifo_regret_pct']:.6f}% |")
    report+=["",
       f"Mean/median/worst prediction-only choice regret = "
       f"{statistics.mean(x['model_regret_pct'] for x in choices):.6f}% / "
       f"{statistics.median(x['model_regret_pct'] for x in choices):.6f}% / "
       f"{max(x['model_regret_pct'] for x in choices):.6f}%.",
       f"Mean FIFO regret = {statistics.mean(x['fifo_regret_pct'] for x in choices):.6f}%.",
       f"Number of policy decisions with >0.1% regret = {sum(x['model_regret_pct']>0.1 for x in choices)} of 8.",
       "",
       "## Material pairwise direction errors"]
    if not wrong:
        report.append("No wrong signs among the MATERIAL original pairs. This does not imply general ranking reliability.")
    for c in wrong:
        report.append(f"- {c['workflow']} {c['vm_profile']} {c['mapping']} {c['policy_a']}→{c['policy_b']}: "
          f"true signed difference={c['actual_b_minus_a_pct']:+.6f}%, "
          f"predicted={c['predicted_b_minus_a_pct']:+.6f}%.")
    report+=["",
      "## Decision and limits",
      "A lower forecast regret on these already known two DAG instances establishes a narrow fixed-mapping three-policy selection property, NOT a new Pareto-aware or joint FLA solver. Hypervolume requires simultaneous Makespan/Cost and full placement search.",
      "The ex-post best actual policy is used ONLY as the regret denominator, never as the selection input. Ranking ties are resolved in precommitted FIFO–SJF–UPWARD order.",
      "Pairwise decisions and eight placements share DAG structure and are statistically dependent. Report no significance test or generalization to an unseen DAG family.",
      "Earlier CyberShake_100 SJF had a known WRONG sign of material Makespan effect, a retained external negative counterexample. The model is not universally safe.",
      "Do not promote or modify any default FLA, seeded NSGA-II, or runtime FIFO policy. Any next algorithm must have its own frozen priority+mapping chromosome, fair NSGA-II encoding, real K16 Pareto-HV and compute-time parity."
    ]
    (out/"policy_decision_rank_and_regret_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: decision_rank.py ORIGINAL_EIGHT_ARTIFACTS OUTPUT")
    main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
