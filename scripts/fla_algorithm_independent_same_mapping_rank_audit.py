#!/usr/bin/env python3
"""Independent frozen same-genotype source-model rank fidelity, real WorkflowSim.

Only uses 96 actual original simulator replay data from Actions 41695356307.
No optimizer, candidate selection, stochastic training or simulator here.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

DAGS=("CyberShake_30","Epigenomics_46","Montage_50")
SPEEDS=("default","staggered")
POLICIES=(
"all_vm0","all_vm12","round_robin","stride7",
"evenodd_vm0_vm12","block4_vm0_vm12","four_vm_round","four_vm_block5",
"vm0_vm12_skew75","vm12_vm15_skew75","prime_step5","prime_step11",
"hash_seed17","hash_seed97","monotonic_vm16","reverse_monotonic_vm16")
MODELS=("old","ready")
TOL=1e-8

def read(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def dom(a,b):
    return a[0]<=b[0] and a[1]<=b[1] and (a[0]<b[0] or a[1]<b[1])

def dclass(a,b):
    return 1 if dom(a,b) else -1 if dom(b,a) else 0

def sign(a,b):
    d=a-b
    t=TOL*max(1.,abs(a),abs(b))
    return 1 if d>t else -1 if d< -t else 0

def ndidx(points):
    return {i for i,p in enumerate(points) if not any(dom(q,p) for j,q in enumerate(points) if i!=j)}

def hv(points,reference):
    rx,ry=reference
    front=sorted(set(points[i] for i in ndidx(points)))
    total=0
    prev=ry
    for m,c in front:
        if m>=rx or c>=ry or c>=prev:continue
        total+=(rx-m)*(prev-c)
        prev=c
    val=total/(rx*ry)
    if not math.isfinite(val) or not 0<=val<=1+1e-8:
        raise AssertionError(("Bad real normalized HV",val))
    return val

def load(source):
    assembled={}
    allsha=set()
    for dax,speed in itertools.product(DAGS,SPEEDS):
        folder=source/f"fla-algorithm-independent-{dax}-{speed}-41695356307"
        if not folder.is_dir():raise AssertionError(("Missing frozen source workflow artifact",folder))
        identity=dict(v.split("=",1) for v in (folder/"block-id.txt").read_text().split())
        if (identity.get("DAG"),identity.get("vm_speed"),identity.get("seed"),
            identity.get("actual_priority"),identity.get("mappings"),identity.get("selection"))!=(
                dax,speed,"1501","fifo","16","none"):
            raise AssertionError(("Original source metadata changed",identity))
        sha=(folder/"source-sha.txt").read_text().strip()
        if len(sha)!=40 or not all(c in "0123456789abcdef" for c in sha):
            raise AssertionError(("No original code provenance",sha))
        allsha.add(sha)
        cases=read(folder/"same_mapping_true_replays.csv")
        if len(cases)!=16 or {r["mapping_policy"] for r in cases}!=set(POLICIES):
            raise AssertionError(("Incomplete frozen original mapping universe",dax,speed,len(cases)))
        if len({r["task_vm_mapping"] for r in cases})!=16:
            raise AssertionError(("Original mappings repeated",dax,speed))
        for r in cases:
            if (r["workflow"],r["vm_profile"],r["seed"])!=(dax,speed,"1501"):
                raise AssertionError(("Original WorkflowSim job label mismatch",dax,speed))
            n=int(r["task_count"])
            assignments=r["task_vm_mapping"].split("|")
            if len(assignments)!=n:raise AssertionError("Missing original TaskID→VM map")
            mapping=dict(tuple(map(int,x.split(":"))) for x in assignments)
            if set(mapping)!=set(range(1,n+1)) or not all(0<=vm<16 for vm in mapping.values()):
                raise AssertionError(("Invalid physical genotype",dax,speed,r["mapping_policy"]))
            for k in ("old_planned_makespan","old_planned_cost",
                    "ready_planned_makespan","ready_planned_cost",
                    "actual_makespan","actual_cost",
                    "old_start_mae","ready_start_mae",
                    "old_finish_mae","ready_finish_mae"):
                val=float(r[k])
                if not math.isfinite(val) or val<0 or ("mae" not in k and val<=0):
                    raise AssertionError(("Invalid source objective",dax,speed,k,r[k]))
        assembled[(dax,speed)]={r["mapping_policy"]:r for r in cases}
    if len(allsha)!=1:raise AssertionError(("Nonidentical code across actual replay jobs",allsha))
    if len(assembled)!=6 or sum(len(q) for q in assembled.values())!=96:
        raise AssertionError("Wrong original source completeness")
    for dax in DAGS:
        a=assembled[(dax,"default")]
        b=assembled[(dax,"staggered")]
        if any(a[k]["task_vm_mapping"]!=b[k]["task_vm_mapping"] for k in POLICIES):
            raise AssertionError(("VM speed effect confounded with different task allocation",dax))
    return assembled,allsha.pop()

def write(path,records):
    if not records:raise AssertionError(("No original source values",path))
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]))
        w.writeheader();w.writerows(records)

def audit(source,out):
    cases,sha=load(source)
    out.mkdir(parents=True,exist_ok=True)
    scores=[]
    mistaken=[]
    raw=[]
    for (dag,speed),register in cases.items():
        ordered=[register[x] for x in POLICIES]
        true=[(float(r["actual_makespan"]),float(r["actual_cost"])) for r in ordered]
        reference15=(1.5*max(m for m,c in true)+1e-6,
                     1.5*max(c for m,c in true)+1e-6)
        reference30=(3*max(m for m,c in true)+1e-6,
                     3*max(c for m,c in true)+1e-6)
        ideal_hv15=hv(true,reference15)
        ideal_hv30=hv(true,reference30)
        true_nd=ndidx(true)
        for r in ordered:
            raw.append(dict(workflow=dag,vm_speed=speed,**r))
        for model in MODELS:
            planned=[(float(r[f"{model}_planned_makespan"]),
                      float(r[f"{model}_planned_cost"])) for r in ordered]
            plan_nd=ndidx(planned)
            shared_nd=len(plan_nd&true_nd)
            if len(plan_nd|true_nd)==0:raise AssertionError("Empty ND set")
            tally=dict(m_order_ok=0,m_order_bad=0,m_order_ties=0,m_material_bad=0,
                       c_order_ok=0,c_order_bad=0,c_order_ties=0,c_material_bad=0,
                       pareto_agree=0,pareto_lost=0,pareto_new=0,pareto_reversed=0)
            for i in range(16):
                for j in range(i+1,16):
                    pi,pj=planned[i],planned[j]
                    ai,aj=true[i],true[j]
                    for coord,prefix in ((0,"m"),(1,"c")):
                        a=sign(pi[coord],pj[coord])
                        b=sign(ai[coord],aj[coord])
                        if a==0 or b==0:tally[prefix+"_order_ties"]+=1
                        elif a==b:tally[prefix+"_order_ok"]+=1
                        else:
                            tally[prefix+"_order_bad"]+=1
                            physical_gap=abs(ai[coord]-aj[coord])/max(ai[coord],aj[coord])
                            if physical_gap>0.001:
                                tally[prefix+"_material_bad"]+=1
                    p=dclass(pi,pj);a=dclass(ai,aj)
                    if p==a:group="agree"
                    elif p!=0 and a==0:group="lost"
                    elif p==0 and a!=0:group="new"
                    else:group="reversed"
                    tally["pareto_"+group]+=1
                    if p!=a:
                        mistaken.append(dict(workflow=dag,vm_speed=speed,
                            predictor=model,policy_i=POLICIES[i],policy_j=POLICIES[j],
                            planned_relation=p,real_relation=a,kind=group,
                            planned_m_i=pi[0],planned_c_i=pi[1],
                            planned_m_j=pj[0],planned_c_j=pj[1],
                            actual_m_i=ai[0],actual_c_i=ai[1],
                            actual_m_j=aj[0],actual_c_j=aj[1]))
            if sum(tally["pareto_"+k] for k in ("agree","lost","new","reversed"))!=120:
                raise AssertionError("Missing physical same-map pair analysis")
            selected=[true[i] for i in sorted(plan_nd)]
            capture_hv15=hv(selected,reference15)
            capture_hv30=hv(selected,reference30)
            scores.append(dict(workflow=dag,vm_speed=speed,predictor=model,
                actual_replays=16,physical_candidate_pairs=120,
                mape_m_pct=statistics.mean(
                    100*abs(x[0]-y[0])/y[0] for x,y in zip(planned,true)),
                mape_cost_pct=statistics.mean(
                    100*abs(x[1]-y[1])/y[1] for x,y in zip(planned,true)),
                mean_start_mae_s=statistics.mean(
                    float(r[f"{model}_start_mae"]) for r in ordered),
                mean_finish_mae_s=statistics.mean(
                    float(r[f"{model}_finish_mae"]) for r in ordered),
                predicted_nd=len(plan_nd),actual_nd=len(true_nd),
                nd_overlap=shared_nd,nd_jaccard=shared_nd/len(plan_nd|true_nd),
                real_hv15_full_16=ideal_hv15,
                real_hv15_pred_nd=capture_hv15,
                nd_hv15_capture_fraction=capture_hv15/max(1e-12,ideal_hv15),
                real_hv30_full_16=ideal_hv30,
                real_hv30_pred_nd=capture_hv30,
                nd_hv30_capture_fraction=capture_hv30/max(1e-12,ideal_hv30),
                **tally))
    assert len(scores)==12 and len(raw)==96
    write(out/"all_96_original_fixed_genotype_truth_and_planning.csv",raw)
    write(out/"all_12_same_mapping_model_rank_scores.csv",scores)
    if mistaken:write(out/"all_misclassified_same_genotype_pairs.csv",mistaken)
    else:(out/"all_misclassified_same_genotype_pairs.csv").write_text("No Pareto mismatches\n")
    report=[
        "# Same-genotype source planner ranking vs actual WorkflowSim, independent 96-map universe",
        "",
        "Original immutable full static WorkflowSim source Actions 41695356307, SHA "+sha+". NO FLA/NSGA optimization or planned Pareto-based candidate selection, and NO optimization/simulator calls during this independent audit.",
        "3 historically studied DAX instances ×2 VM speed profiles ×16 EXACT same algorithm-independent deterministic source mappings = 96 actual simulator outputs, 6 independently recorded DAX/speed blocks. This is NOT 96 independent new workflow-family experiments.",
        "Each predictor forecasts the SAME 16 original mapping policies, compared to the SAME REAL Makespan/Cost labels, removing the model-specific candidate-set confound. All 120 unordered physical pairs per block are classified for Makespan order, Cost order, and Pareto dominance.",
        "",
        "| Workflow | VM speed | Model | Makespan MAPE | Cost MAPE | Makespan sign errors / comparable | Material Makespan sign errors (>0.1% true gap) | Pareto class mistakes /120 | ND set Jaccard | Real-HV coverage of all16 candidate universe |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in scores:
        compared=r["m_order_ok"]+r["m_order_bad"]
        report.append(f"| {r['workflow']} | {r['vm_speed']} | "
            f"{'StageIn insertion' if r['predictor']=='old' else 'Ready TaskID'} | "
            f"{r['mape_m_pct']:.5f}% | {r['mape_cost_pct']:.5f}% | "
            f"{r['m_order_bad']}/{compared} | {r['m_material_bad']} | "
            f"{r['pareto_lost']+r['pareto_new']+r['pareto_reversed']}/120 | "
            f"{r['nd_jaccard']:.3f} | {100*r['nd_hv15_capture_fraction']:.5f}% |")
    report+=["","## Paired same-map summary: 6 source DAG/speed blocks"]
    for model in MODELS:
        zz=[r for r in scores if r["predictor"]==model]
        report.append(f"- {model}: mean Makespan abs percent error "
            f"{statistics.mean(r['mape_m_pct'] for r in zz):.6f}%; "
            f"mean Cost abs percent error {statistics.mean(r['mape_cost_pct'] for r in zz):.6f}%; "
            f"total material Makespan sign reversals "
            f"{sum(r['m_material_bad'] for r in zz)} of {sum(r['physical_candidate_pairs'] for r in zz)} compared source pairs; "
            f"total Pareto class mismatches "
            f"{sum(r['pareto_lost']+r['pareto_new']+r['pareto_reversed'] for r in zz)} "
            f"of {sum(r['physical_candidate_pairs'] for r in zz)}; "
            f"mean actual K16 ND HV captured by predicted ND "
            f"{100*statistics.mean(r['nd_hv15_capture_fraction'] for r in zz):.5f}%.")
    better=0;ties=0;worse=0
    for dag,speed in itertools.product(DAGS,SPEEDS):
        old=next(r for r in scores if (r["workflow"],r["vm_speed"],r["predictor"])==(dag,speed,"old"))
        ready=next(r for r in scores if (r["workflow"],r["vm_speed"],r["predictor"])==(dag,speed,"ready"))
        diff=ready["mape_m_pct"]-old["mape_m_pct"]
        if diff< -1e-8:better+=1
        elif diff>1e-8:worse+=1
        else:ties+=1
    report+=["",f"Ready vs original insertion makespan MAPE per same-genotype DAG/speed block: **{better} improved, {ties} tied, {worse} worsened**.",
      "",
      "## Scientific caveats",
      "The 16 source mappings span some unrealistic extreme all-on-one VM cases; the mean MAPE and HV may be dominated by these task/VM patterns. Report individual mapping details, not just block averages.",
      "All DAG families were encountered earlier. There are only 6 independent DAX/speed blocks and 3 workflow instances; 720 within-block pairs are highly correlated and not independent experiments.",
      "The REAL HV reference is for the 16 frozen source mapping vectors, NOT the unknown complete scheduling Pareto set or full optimizer population. Models have not been trained on these new source labels, but the same workflow families previously informed engineering choices.",
      "An improved decoder shared by FLA and NSGA-II is a scheduling evaluation innovation, NOT proof of FLA search-operator superiority, novelty or SCI Q1 readiness.",
      "Original FLA, NSGA-II, FIFO runtime and master remain untouched. All changes are opt-in algorithm-independent science."
    ]
    (out/"same_genotype_actual_rank_fidelity_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py ORIGINAL_COMPLETED_96_SOURCE_ARTIFACTS OUTPUT_FOLDER")
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
