#!/usr/bin/env python3
"""Read-only revalidation of the four original completed simulator-source artifacts.

IMPORTANT provenance: GitHub source run 41693332570 is UI-RED/failed ONLY
because a 1-character Python validation syntax error occurred AFTER Java had
already saved every actual WorkflowSim result. Reuse source CSVs; NEVER rerun
the simulator just to make the UI green. Frozen original source commit:
f963e95c952a0d3dd67a26cdefa2b5eb221d8d61.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

DAGS=("Montage_100","CyberShake_50")
SEEDS=(951,952)
ARMS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
ORIGINAL_RUN=41693332570
SOURCE_SHA="f963e95c952a0d3dd67a26cdefa2b5eb221d8d61"

def rows(p):
    with p.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def dominated(a,b):
    return a[0]<=b[0] and a[1]<=b[1] and (a[0]<b[0] or a[1]<b[1])

def classification(a,b):
    return 1 if dominated(a,b) else -1 if dominated(b,a) else 0

def nd_indices(points):
    return {i for i,p in enumerate(points) if not any(dominated(q,p)
        for j,q in enumerate(points) if i!=j)}

def hv(points,reference):
    rx,ry=reference
    if not all(math.isfinite(v) and v>0 for v in reference):
        raise AssertionError("Invalid shared real reference")
    nd=sorted(set(points[i] for i in nd_indices(points)))
    prev=ry
    area=0.
    for x,y in nd:
        if x>=rx or y>=ry:continue
        if y>=prev:continue
        area+=(rx-x)*(prev-y)
        prev=y
    result=area/(rx*ry)
    if not math.isfinite(result) or not (0<=result<=1+1e-8):
        raise AssertionError(("Bad normalized real HV",result))
    return result

def metrics(sample):
    for k in ("planned_makespan","planned_cost","sim_makespan","sim_cost"):
        if k not in sample:raise AssertionError(("Missing actual/planned column",k))
        val=float(sample[k])
        if not math.isfinite(val) or val<=0:raise AssertionError(("Invalid source label",k,sample))
    return ((float(sample["planned_makespan"]),float(sample["planned_cost"])),
            (float(sample["sim_makespan"]),float(sample["sim_cost"])))

def load(original):
    source={}
    for dag,seed in itertools.product(DAGS,SEEDS):
        folder=original/f"fla-dom-k16plus12-{dag}-s{seed}-{ORIGINAL_RUN}"
        if not folder.is_dir():raise AssertionError(("Missing immutable source artifact",folder))
        ss=rows(folder/"research_summary.csv")
        rr=rows(folder/"research_replays.csv")
        es=rows(folder/"research_screening_summary.csv")
        ee=rows(folder/"research_screening_samples.csv")
        if (len(ss),len(rr),len(es),len(ee))!=(2,32,2,24):
            raise AssertionError(("Java output incomplete despite failed postcheck",
                                  dag,seed,len(ss),len(rr),len(es),len(ee)))
        if {s["algorithm"] for s in ss}!={s["algorithm"] for s in es}!={*ARMS}:
            raise AssertionError(("Unexpected source solver identity",dag,seed))
        for alg in ARMS:
            s=next(q for q in ss if q["algorithm"]==alg)
            e=next(q for q in es if q["algorithm"]==alg)
            orig=sorted((x for x in rr if x["algorithm"]==alg),
                key=lambda x:int(x["candidate_index"]))
            extra=[x for x in ee if x["algorithm"]==alg]
            if (s["workflow"],int(s["seed"]))!=(dag,seed):
                raise AssertionError(("Wrong original source task identity",dag,seed,alg))
            if tuple(int(s[k]) for k in ("population","generations",
                "evaluations","captured_evaluations","replayed"))!=(30,100,3030,3030,16):
                raise AssertionError(("Wrong original objective/replay budget",dag,seed,alg))
            if e["workflow"]!=dag or int(e["seed"])!=seed or int(e["sampled"])!=12:
                raise AssertionError(("No 12 true secondary simulator outcomes",dag,seed,alg))
            if len(orig)!=16 or len(extra)!=12 or [int(x["candidate_index"]) for x in orig]!=list(range(1,17)):
                raise AssertionError(("Bad K16/K12 source ordering",dag,seed,alg))
            if {x["stratum"] for x in extra}!={"near-planned-front","uniform-remainder"}:
                raise AssertionError(("Unexpected source sampling stratum",dag,seed,alg))
            if sum(x["stratum"]=="near-planned-front" for x in extra)!=6 or sum(
                x["stratum"]=="uniform-remainder" for x in extra)!=6:
                raise AssertionError(("Sampled stratum sizes do not match frozen 6/6",dag,seed,alg))
            if len({r["mapping"] for r in orig+extra})!=28:
                raise AssertionError(("Repeated same task-VM mapping across K16 and K12",dag,seed,alg))
            if any(x["workflow"]!=dag or int(x["seed"])!=seed for x in orig+extra):
                raise AssertionError(("Source replay metadata mismatch",dag,seed,alg))
            for x in orig+extra:metrics(x)
            original_planned=[metrics(x)[0] for x in orig]
            for x in extra:
                z=metrics(x)[0]
                if not (any(dominated(y,z) or y==z for y in original_planned)):
                    raise AssertionError(("Extra candidate not dominated/tied by selected K16",
                        dag,seed,alg,x["stratum"],z))
            source[(dag,seed,alg)]={"original":orig,"extra":extra,"summary":s,"extra_summary":e}
    if len(source)!=8:raise AssertionError(("Expected exact 8 original solver strata",len(source)))
    return source

def arm_audit(dag,seed,alg,source,reference):
    before=source["original"]
    after=source["extra"]
    joined=before+after
    planned=[metrics(r)[0] for r in joined]
    real=[metrics(r)[1] for r in joined]
    nd_original=nd_indices(real[:16])
    nd_union=nd_indices(real)
    new_against_old=[]
    for ix in range(16,28):
        if not any(dominated(real[j],real[ix]) or real[j]==real[ix] for j in range(16)):
            new_against_old.append(ix)
    return_strata={}
    for key in ("near-planned-front","uniform-remainder"):
        ids=[i for i in range(16,28) if joined[i]["stratum"]==key]
        return_strata[key]=sum(i in new_against_old for i in ids)
    all_pairs=[]
    count_types={"cross":dict(agree=0,lost=0,new=0,reversed=0),
                 "within_k16":dict(agree=0,lost=0,new=0,reversed=0),
                 "within_extra":dict(agree=0,lost=0,new=0,reversed=0)}
    for i in range(28):
        for j in range(i+1,28):
            tag="within_k16" if j<16 else "within_extra" if i>=16 else "cross"
            p=classification(planned[i],planned[j])
            t=classification(real[i],real[j])
            kind="agree" if p==t else "lost" if p!=0 and t==0 else (
                "new" if p==0 and t!=0 else "reversed")
            count_types[tag][kind]+=1
            if p!=t:
                all_pairs.append(dict(workflow=dag,seed=seed,solver=alg,
                    pair_type=tag,original_candidate_i=i+1,original_candidate_j=j+1,
                    sampled_stratum_j=joined[j].get("stratum","primary-K16"),
                    planned_dominance=p,real_dominance=t,mismatch=kind,
                    planned_makespan_i=planned[i][0],planned_cost_i=planned[i][1],
                    planned_makespan_j=planned[j][0],planned_cost_j=planned[j][1],
                    actual_makespan_i=real[i][0],actual_cost_i=real[i][1],
                    actual_makespan_j=real[j][0],actual_cost_j=real[j][1]))
    if sum(count_types["within_k16"].values())!=120 or sum(count_types["cross"].values())!=192 or sum(count_types["within_extra"].values())!=66:
        raise AssertionError(("Missing pairwise comparisons",dag,seed,alg,count_types))
    initial_hv=hv(real[:16],reference)
    after_hv=hv(real,reference)
    if after_hv+1e-10<initial_hv:raise AssertionError(("Adding dominated real points decreased HV",dag,seed,alg))
    pct=100*(after_hv-initial_hv)/max(1e-12,initial_hv)
    top={k:v for k,d in count_types.items() for k2,v in d.items()}
    # Expand each pair type in stable fields to avoid flatten collision.
    aggregate=dict(workflow=dag,seed=seed,solver=alg,
        target_evaluations=3030,original_k16=16,additional_dominated_samples=12,
        original_actual_nd=len(nd_original),union_actual_nd=len(nd_union),
        extra_nondominated_against_original_k16=len(new_against_old),
        extra_nd_near=return_strata["near-planned-front"],
        extra_nd_uniform=return_strata["uniform-remainder"],
        extra_surviving_union_nd=sum(i in nd_union for i in range(16,28)),
        common_hv15_original=initial_hv,common_hv15_union=after_hv,
        delta_hv15=after_hv-initial_hv,relative_hv_increase_pct=pct)
    for name,d in count_types.items():
        for key,num in d.items():
            aggregate[name+"_"+key]=num
    return aggregate,all_pairs,real

def write(path,things):
    if not things:raise AssertionError(("No rows",path))
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(things[0]));w.writeheader();w.writerows(things)

def audit(original,output):
    s=load(original)
    output.mkdir(parents=True,exist_ok=True)
    summaries=[]
    mistakes=[]
    full_source=[]
    for dag,seed in itertools.product(DAGS,SEEDS):
        union=[metrics(r)[1] for alg in ARMS for r in
            s[(dag,seed,alg)]["original"]+s[(dag,seed,alg)]["extra"]]
        if len(union)!=56:raise AssertionError("Expected 56 same-reference simulator outputs per block")
        ref15=(1.5*max(m for m,c in union)+1e-6,1.5*max(c for m,c in union)+1e-6)
        ref30=(3*max(m for m,c in union)+1e-6,3*max(c for m,c in union)+1e-6)
        for alg in ARMS:
            source=s[(dag,seed,alg)]
            d,wrong,real=arm_audit(dag,seed,alg,source,ref15)
            d30,_,_=arm_audit(dag,seed,alg,source,ref30)
            d["common_hv30_original"]=d30["common_hv15_original"]
            d["common_hv30_union"]=d30["common_hv15_union"]
            d["delta_hv30"]=d30["delta_hv15"]
            d["shared_ref_m15"]=ref15[0];d["shared_ref_c15"]=ref15[1]
            d["shared_ref_m30"]=ref30[0];d["shared_ref_c30"]=ref30[1]
            summaries.append(d)
            mistakes+=wrong
            for order,x in enumerate(source["original"]+source["extra"]):
                point_real=metrics(x)[1]
                point_plan=metrics(x)[0]
                full_source.append(dict(workflow=dag,seed=seed,solver=alg,
                    candidate_index=order+1,selection="primary-k16" if order<16 else "secondary-k12",
                    stratum=x.get("stratum","primary"),
                    planned_makespan=point_plan[0],planned_cost=point_plan[1],
                    actual_makespan=point_real[0],actual_cost=point_real[1],
                    task_vm_mapping=x["mapping"]))
    if len(full_source)!=224 or len(summaries)!=8:
        raise AssertionError(("Incomplete original simulator actual outcomes",len(full_source),len(summaries)))
    write(output/"all_224_true_replay_candidates.csv",full_source)
    write(output/"all_8_solver_original_vs_extra_rank_and_hv.csv",summaries)
    if mistakes:write(output/"all_pareto_misclassified_pair_details.csv",mistakes)
    else:(output/"all_pareto_misclassified_pair_details.csv").write_text("No planned/real Pareto misclassifications found\n",encoding="utf-8")
    loss=sum(x["cross_lost"] for x in summaries)
    reversal=sum(x["cross_reversed"] for x in summaries)
    fresh=sum(x["cross_new"] for x in summaries)
    report=[
        "# Independent completed source K16+K12 actual simulator Pareto rank audit",
        "",
        "**Original GitHub Actions run 41693332570 FAILED in a subsequent Python validation step due to a stray quote, AFTER Java had written all 224 WorkflowSim results.** Its original four artifacts were retained. This independent analysis uses THOSE IMMUTABLE SOURCE files, does not rerun the actual simulator, and records the original CI failure rather than calling it green.",
        "Original 4 source cases Montage_100, CyberShake_50, seeds951,952; two identical seeded FLA-v12 and NSGA-II benchmark arms, fixed stage-in-aware FIFO objective, 3030 evaluations each; **8 ×(K16 primary +K12 frozen planned-dominated/tied) =224 original complete actual simulator replay outcomes**. Every K28 mapping distinct within original solver arm, 6/6 fixed secondary sampling strata.",
        "Within each workflow/seed block, the union of both solvers' 56 REAL results establishes ONE common normalized 1.5× or 3.0× HV reference. All gains are EXPLORATORY OFFLINE second-stratum gains, not improvements achieved by original K16 optimizer.",
        "",
        "| DAG | Seed | Solver | Additional true ND vs K16 | True ND in final K28 | Original real HV | Real K28 HV | Δ HV (additional samples) | Planned→real cross K16×K12 lost / reversed / new dominance |",
        "|---|---:|---|---:|---:|---:|---:|---:|---|"]
    for r in summaries:
        report.append(f"| {r['workflow']} | {r['seed']} | "
           f"{'FLA-v12' if r['solver']==ARMS[0] else 'NSGA-II'} | "
           f"{r['extra_nondominated_against_original_k16']}/12 | "
           f"{r['extra_surviving_union_nd']}/12 | "
           f"{r['common_hv15_original']:.8f} | {r['common_hv15_union']:.8f} | "
           f"{r['delta_hv15']:+.8f} | "
           f"{r['cross_lost']}/{r['cross_reversed']}/{r['cross_new']} |")
    report+=["",
        "## Prespecified Pareto decision-rank misclassifications",
        f"- Among **{8*192} original planner-selected K16 versus planned-dominated K12 pairs**, "
        f"planned-dominance lost after simulation: **{loss}**; directly reversed: **{reversal}**; new actual dominance not predicted: **{fresh}**.",
        f"- Additional real nondominated candidates against the *original K16* total "
        f"**{sum(r['extra_nondominated_against_original_k16'] for r in summaries)} of 96** separately selected dominated/tied source candidates.",
        f"- Strictly additive real Pareto HV improvement in **{sum(r['delta_hv15']>1e-10 for r in summaries)} of 8** original solver cases; mean absolute normalized HV increment "
        f"{statistics.mean(r['delta_hv15'] for r in summaries):+.8f}.",
        "",
        "## Interpretation and limitations",
        "All secondary candidates were chosen using their PLANNED labels before their ACTUAL WorkflowSim labels were observed. This is a proper evaluation-selection bias diagnostic, not proof the optimizer would have selected the useful secondary points.",
        "K16 selection deliberately favors planned Pareto-cover. This causes much of the earlier selected-K 'new actual dominance only' asymmetry; the added dominated/tied pool makes predicted dominances actually observable and falsifiable.",
        "The source workflow failing post-validation while retaining immutable source artifacts is an ENGINEERING failure, not a failed Java scheduling/CloudSim run. No simulator rerun or cherry-picking; original failed logs remain linked and reported.",
        "Only two familiar DAX families and two seeds, strong candidate-pair dependence, 96 extras from two strata selected by one existing heuristic; no 1536 pairs can be interpreted as independent randomized scientific tests, no formal significance or SCI publication readiness.",
        "No master/default FLA/runtime priority changes. Before claiming a new Pareto-ranked scheduler, design a fixed, algorithm-independent candidate universe with unbiased ranks and more truly unseen DAX families, then separate ranking quality from FLA proposal quality."
    ]
    (output/"complete_k16_plus12_actual_rank_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py ORIGINAL_FAILED_BUT_COMPLETE_ARTIFACTS REPORT_DIR")
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
