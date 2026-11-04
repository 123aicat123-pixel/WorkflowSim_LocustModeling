#!/usr/bin/env python3
"""Frozen, planned-only exact-K selection and after-choice true WorkflowSim HV.

Original real simulator source 41695356307; no simulation or optimizer.
Source grouping and identity verification reused from the completed 96-map audit.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import fla_algorithm_independent_same_mapping_rank_audit as base

KS=(1,2,4,8)
DAGS=base.DAGS
SPEEDS=base.SPEEDS
POLICIES=base.POLICIES
MODELS=base.MODELS
N=16
TIE_TOL=1e-12

def hv_subset(points,indices,reference):
    p=sorted(set(points[i] for i in indices))
    rx,ry=reference
    if not all(math.isfinite(x) and x>0 for x in reference):
        raise AssertionError("Invalid common reference")
    last=ry
    area=0.0
    for m,c in p:
        if m<rx and c<last:
            area+=(rx-m)*(last-c)
            last=c
    score=area/(rx*ry)
    if not (-1e-10<=score<=1+1e-10):
        raise AssertionError(("Impossible normalized HV",score))
    return score

def exact_max_subset(points,k,reference):
    # Both models and oracle use the exact SAME subset solver. Lexicographic
    # frozen policy ID order makes near-ties deterministic.
    winner=None
    best=-1.
    for indices in itertools.combinations(range(N),k):
        hv=hv_subset(points,indices,reference)
        if hv>best+TIE_TOL:
            best=hv;winner=indices
    if winner is None or len(winner)!=k:raise AssertionError("Subset search failed")
    return winner,best

def write(path,values):
    if not values:raise AssertionError(("Missing output rows",path))
    with path.open("w",newline="",encoding="utf-8") as out:
        writer=csv.DictWriter(out,fieldnames=list(values[0]))
        writer.writeheader();writer.writerows(values)

def run(source,out):
    groups,sha=base.load(source)
    out.mkdir(parents=True,exist_ok=True)
    details=[]
    pairs=[]
    for dag,speed in itertools.product(DAGS,SPEEDS):
        actual_rows=groups[(dag,speed)]
        ordered=[actual_rows[p] for p in POLICIES]
        real=[(float(r["actual_makespan"]),float(r["actual_cost"])) for r in ordered]
        predictions={
            model:[(float(r[f"{model}_planned_makespan"]),
                    float(r[f"{model}_planned_cost"])) for r in ordered]
            for model in MODELS
        }
        # Model-common reference can be built before any source simulation.
        predref=(
            1.5*max(m for group in predictions.values() for m,c in group)+1e-6,
            1.5*max(c for group in predictions.values() for m,c in group)+1e-6)
        realrefs={factor:(
            factor*max(m for m,c in real)+1e-6,
            factor*max(c for m,c in real)+1e-6)
            for factor in (1.5,3.0)}
        all_hv={factor:hv_subset(real,range(N),ref)
                for factor,ref in realrefs.items()}
        if any(val<=0 for val in all_hv.values()):
            raise AssertionError(("Zero true source candidate-universe HV",dag,speed))
        for k in KS:
            oracle={factor:exact_max_subset(real,k,ref)[1]
                    for factor,ref in realrefs.items()}
            selected={}
            for model in MODELS:
                choice,selected_planned_hv=exact_max_subset(predictions[model],k,predref)
                selected[model]=choice
                captured={factor:hv_subset(real,choice,ref)
                          for factor,ref in realrefs.items()}
                if any(captured[f]>oracle[f]+1e-9 for f in oracle):
                    raise AssertionError("Selected HV larger than hindsight optimum")
                details.append(dict(
                    workflow=dag,vm_speed=speed,source_sha=sha,
                    actual_universe=16,K=k,predictor=model,
                    predicted_hv=selected_planned_hv,
                    planned_choice_indices="|".join(str(i+1) for i in choice),
                    selected_mapping_policies="|".join(POLICIES[i] for i in choice),
                    actual_selected_hv15=captured[1.5],
                    actual_selected_hv30=captured[3.0],
                    actual_universe_hv15=all_hv[1.5],
                    actual_universe_hv30=all_hv[3.0],
                    actual_hv_recovery15_pct=100*captured[1.5]/all_hv[1.5],
                    actual_hv_recovery30_pct=100*captured[3.0]/all_hv[3.0],
                    hindsight_K_hv15=oracle[1.5],
                    hindsight_K_hv30=oracle[3.0],
                    hindsight_K_regret15_pct=100*(oracle[1.5]-captured[1.5])/all_hv[1.5],
                    hindsight_K_regret30_pct=100*(oracle[3.0]-captured[3.0])/all_hv[3.0]))
            old=next(x for x in details if x["workflow"]==dag and x["vm_speed"]==speed and x["K"]==k and x["predictor"]=="old")
            ready=next(x for x in details if x["workflow"]==dag and x["vm_speed"]==speed and x["K"]==k and x["predictor"]=="ready")
            common=set(selected["old"])&set(selected["ready"])
            union=set(selected["old"])|set(selected["ready"])
            pairs.append(dict(
                workflow=dag,vm_speed=speed,K=k,
                selected_same=int(selected["old"]==selected["ready"]),
                selected_overlap=len(common),selected_jaccard=len(common)/len(union),
                old_hv_recovery15_pct=old["actual_hv_recovery15_pct"],
                ready_hv_recovery15_pct=ready["actual_hv_recovery15_pct"],
                ready_minus_old_recovery15_pp=ready["actual_hv_recovery15_pct"]-old["actual_hv_recovery15_pct"],
                ready_minus_old_recovery30_pp=ready["actual_hv_recovery30_pct"]-old["actual_hv_recovery30_pct"],
                old_hindsight_regret15_pct=old["hindsight_K_regret15_pct"],
                ready_hindsight_regret15_pct=ready["hindsight_K_regret15_pct"]))
    if (len(details),len(pairs))!=(48,24):raise AssertionError("Incomplete original 96-point study")
    write(out/"all_48_frozen_planned_K_selections.csv",details)
    write(out/"all_24_paired_old_vs_ready_low_K_real_HV.csv",pairs)
    report=[
        "# Original same-genotype 96 WorkflowSim cases: planned-only exact low-K HV selection",
        "",
        "Frozen source actual WorkflowSim Actions **41695356307**; original Java SHA "+sha+
        ". Reused complete TaskID→VM original map identity from `fla_algorithm_independent_same_mapping_rank_audit.load`. Six source DAG/speed blocks, 16 fixed mappings/block; NO new optimizer or simulator calls.",
        "Selection uses ONLY predicted Makespan/Cost; one 1.5× common reference derived from the two MODELS' planned values per block. For K=1,2,4,8 the predicted-HV-maximizing subset is enumerated exactly with frozen lexicographic ties. Real 1.5×/3.0× HV is evaluated only AFTER selection and always normalized against the exact same 16-candidate real universe within block. Hindsight K optimum is a retrospective ceiling, NEVER a selector.",
        "",
        "| Replay budget K | Mean old true HV recovery of all16 | Mean ready true HV recovery of all16 | Mean Δ READY−OLD | Pair wins / ties / losses | Identical subsets / 6 |",
        "|---:|---:|---:|---:|---|---:|"
    ]
    for k in KS:
        pp=[p for p in pairs if p["K"]==k]
        gaps=[p["ready_minus_old_recovery15_pp"] for p in pp]
        report.append(f"| {k} | "
          f"{statistics.mean(x['old_hv_recovery15_pct'] for x in pp):.7f}% | "
          f"{statistics.mean(x['ready_hv_recovery15_pct'] for x in pp):.7f}% | "
          f"{statistics.mean(gaps):+.7f} pp | "
          f"{sum(x>1e-8 for x in gaps)}/{sum(abs(x)<=1e-8 for x in gaps)}/{sum(x<-1e-8 for x in gaps)} | "
          f"{sum(x['selected_same'] for x in pp)}/6 |")
    report+=["",
             "## All 24 blockwise actual results; report every gain, tie and loss",
             "| DAG | VM speed | K | OLD recovered real HV | READY recovered real HV | READY−OLD (pp) | Same policy subset? |",
             "|---|---|---:|---:|---:|---:|---|"]
    for x in pairs:
        report.append(f"| {x['workflow']} | {x['vm_speed']} | {x['K']} | "
          f"{x['old_hv_recovery15_pct']:.7f}% | {x['ready_hv_recovery15_pct']:.7f}% | "
          f"{x['ready_minus_old_recovery15_pp']:+.7f} | "
          f"{'yes' if x['selected_same'] else 'no'} |")
    report+=["",
      "## Important boundaries",
      "One source block has only 16 algorithm-independent placement patterns, including unrealistic all-on-one-VM patterns; any exact predicted or hindsight K subset enumeration over 16 does not model a realistic large FLA population. No information from actual outcomes entered the planned selectors.",
      "The hindsight optimum is shown only to measure screening regret, not to train, adjust K or choose a favorable threshold.",
      "All six blocks share only THREE previously researched DAG families, and two VM profiles; 24 paired cases are strongly correlated, so there is no statistical inferential/generalization claim.",
      "Improved prediction MAPE by itself is not a new FLA operator, not evidence of superior K16 true HV on real optimizer populations, and not sufficient for an SCI Q1 submission. FLA, NSGA-II, FIFO runtime and master remain unchanged."
    ]
    (out/"low_K_planned_selection_true_HV_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: low_K.py COMPLETE_ORIGINAL_SOURCE_ARTIFACTS OUTPUT_DIR")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
