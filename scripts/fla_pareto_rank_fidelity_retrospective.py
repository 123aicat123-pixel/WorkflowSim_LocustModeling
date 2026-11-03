#!/usr/bin/env python3
"""Read-only 1024-simulator-row model-vs-reality decision-rank audit.

No optimization or simulator in this code. Unit of analysis is one original
optimizer arm's preselected K actual WorkflowSim replay candidates.
"""
import csv
import hashlib
import itertools
import math
import pathlib
import statistics
import sys

RESTART_DAGS=("Inspiral_50","Epigenomics_46")
RESTART_SEEDS=(821,822)
VARIANTS=("old_full","ready_full","shortest_full","upward_full",
          "split_fifo0","split_fifo1","split_fifo2",
          "split_priority_fifo","split_priority_shortest","split_priority_upward")
POLICIES={"old_full":"fifo","ready_full":"fifo",
          "shortest_full":"shortest","upward_full":"upward",
          "split_fifo0":"fifo","split_fifo1":"fifo","split_fifo2":"fifo",
          "split_priority_fifo":"fifo","split_priority_shortest":"shortest",
          "split_priority_upward":"upward"}
RESTART_ARMS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
V19_DAGS=("Inspiral_100","Sipht_100")
V19_SEEDS=(901,902)
V19_ARMS=("DAG-Pareto-FLA[v12-hvbandit]","DAG-Pareto-FLA[v18-disagreement]",
          "DAG-Pareto-FLA[v19-queue-risk]","NSGA-II[costseed]")
TOL=1e-8

def read(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def dominates(a,b):
    return a[0]<=b[0] and a[1]<=b[1] and (a[0]<b[0] or a[1]<b[1])

def sign(a,b):
    diff=a-b
    tol=TOL*max(1,abs(a),abs(b))
    return 1 if diff>tol else -1 if diff< -tol else 0

def dominance_label(a,b):
    return 1 if dominates(a,b) else -1 if dominates(b,a) else 0

def nondominated_indexes(points):
    return {i for i,p in enumerate(points) if not any(dominates(q,p)
                    for j,q in enumerate(points) if i!=j)}

def assert_number(x,key):
    value=float(x)
    if not math.isfinite(value) or value<=0:raise AssertionError(("Invalid source objective",key,x))
    return value

def sources(root_a,root_b):
    arms=[]
    source_calls=0
    source_sha={}
    seen_dirs=set()
    for origin,root in (("restart",root_a),("v19",root_b)):
        if not root.is_dir():raise AssertionError(("Missing source original artifacts",origin))
        loaded=set()
        for directory in root.iterdir():
            if not directory.is_dir():continue
            idfile=directory/"block-id.txt"
            if not idfile.exists():continue
            tags=dict(item.split("=",1) for item in idfile.read_text().split())
            if origin=="restart":
                wf=tags.get("DAG");base=int(tags.get("base_seed","-1"))
                variant=tags.get("variant");actual_seed=int(tags.get("source_seed","-1"))
                if wf not in RESTART_DAGS or base not in RESTART_SEEDS or variant not in VARIANTS:
                    raise AssertionError(("Unregistered original restart experiment",tags))
                key=(wf,base,variant)
                valid_arms=RESTART_ARMS
                expected_k=int(tags.get("K","-1"))
                expected_pop=int(tags.get("pop","-1"))
                assert tags.get("runtime_priority")==POLICIES[variant]
                assert expected_k in (5,6,16) and expected_pop in (10,30)
                policy=tags["runtime_priority"]
                session_seed=base
            else:
                wf=tags.get("DAG");actual_seed=int(tags.get("seed","-1"))
                if wf not in V19_DAGS or actual_seed not in V19_SEEDS:
                    raise AssertionError(("Unregistered original v19 data",tags))
                key=(wf,actual_seed)
                valid_arms=V19_ARMS
                expected_k=16
                expected_pop=30
                variant="four_algorithm_search"
                policy="fifo"
                session_seed=actual_seed
            if key in loaded:
                raise AssertionError(("Duplicated source original case",origin,key))
            loaded.add(key)
            sha=(directory/"source-sha.txt").read_text().strip()
            if len(sha)!=40 or not all(c in "0123456789abcdef" for c in sha):
                raise AssertionError(("Missing immutable source SHA",origin,key))
            source_sha.setdefault(origin,set()).add(sha)
            summary=read(directory/"research_summary.csv")
            replays=read(directory/"research_replays.csv")
            if len(summary)!=len(valid_arms) or set(s["algorithm"] for s in summary)!=set(valid_arms):
                raise AssertionError(("Wrong original source arms",origin,key))
            if len(replays)!=len(summary)*expected_k:
                raise AssertionError(("Missing original actual K-selected replays",origin,key,len(replays)))
            for s in summary:
                algo=s["algorithm"]
                if s["workflow"]!=wf or int(s["seed"])!=actual_seed:
                    raise AssertionError(("Wrong source arm identity",origin,key,algo))
                budget=tuple(int(s[col]) for col in
                    ("population","generations","evaluations","captured_evaluations","replayed"))
                if budget!=(expected_pop,100,expected_pop*101,expected_pop*101,expected_k):
                    raise AssertionError(("Broken source evaluation fairness",origin,key,algo,budget))
                candidate=sorted((r for r in replays if r["algorithm"]==algo),
                    key=lambda r:int(r["candidate_index"]))
                if len(candidate)!=expected_k or [int(r["candidate_index"]) for r in candidate]!=list(range(1,expected_k+1)):
                    raise AssertionError(("Selected K order missing",origin,key,algo))
                if len({r["mapping"] for r in candidate})!=expected_k:
                    raise AssertionError(("Duplicate original genotype within solver K",origin,key,algo))
                predictions=[]
                real=[]
                mapping=[]
                independent=[]
                for r in candidate:
                    if r["workflow"]!=wf or int(r["seed"])!=actual_seed:
                        raise AssertionError(("Original replay wrong seed",origin,key,algo))
                    predictions.append((assert_number(r["planned_makespan"],"planned_makespan"),
                                        assert_number(r["planned_cost"],"planned_cost")))
                    real.append((assert_number(r["sim_makespan"],"sim_makespan"),
                                 assert_number(r["sim_cost"],"sim_cost")))
                    independent.append((assert_number(r["independent_planned_makespan"],"independent_planned_makespan"),
                                        assert_number(r["independent_planned_cost"],"independent_planned_cost")))
                    mapping.append(r["mapping"])
                arms.append(dict(origin=origin,workflow=wf,session_seed=session_seed,
                    source_seed=actual_seed,variant=variant,algorithm=algo,
                    policy=policy,k=expected_k,pred=predictions,real=real,
                    independent=independent,mapping=mapping))
                source_calls+=len(real)
        expected=set(itertools.product(RESTART_DAGS,RESTART_SEEDS,VARIANTS)) if origin=="restart" \
                  else set(itertools.product(V19_DAGS,V19_SEEDS))
        if loaded!=expected:
            raise AssertionError(("Original source incomplete; REFUSE partial audit",origin,
                                  sorted(expected-loaded),sorted(loaded-expected)))
        if len(source_sha[origin])!=1:
            raise AssertionError(("Mixed original workflow job source SHA",origin,source_sha[origin]))
    if len(arms)!=96 or source_calls!=1024:
        raise AssertionError(("Expected EXACT 96 full source arms, 1024 actual replays",len(arms),source_calls))
    return arms,source_sha

def diagnostic(arm):
    p=arm["pred"];a=arm["real"];inde=arm["independent"]
    n=len(p)
    pnd=nondominated_indexes(p);andx=nondominated_indexes(a)
    intersect=len(pnd&andx)
    errors=[]
    ms_pairs=[0,0,0,0] # correct, discordant, tied by predicted, tied by actual
    cost_pairs=[0,0,0,0]
    d_pairs=[0,0,0,0] # agreement, lost, gained, reversed
    for i in range(n):
        for j in range(i+1,n):
            for ix,arr in enumerate((ms_pairs,cost_pairs)):
                pm=sign(p[i][ix],p[j][ix])
                am=sign(a[i][ix],a[j][ix])
                if pm==0:arr[2]+=1
                elif am==0:arr[3]+=1
                elif pm==am:arr[0]+=1
                else:arr[1]+=1
            predicted=dominance_label(p[i],p[j])
            actual=dominance_label(a[i],a[j])
            if predicted==actual:d_pairs[0]+=1
            elif predicted!=0 and actual==0:d_pairs[1]+=1
            elif predicted==0 and actual!=0:d_pairs[2]+=1
            else:d_pairs[3]+=1
            if predicted!=actual:
                errors.append(dict(origin=arm["origin"],workflow=arm["workflow"],
                    session_seed=arm["session_seed"],source_seed=arm["source_seed"],
                    variant=arm["variant"],algorithm=arm["algorithm"],policy=arm["policy"],
                    pair_i=i+1,pair_j=j+1,predicted_dominance=predicted,actual_dominance=actual,
                    mapping_i_sha256=hashlib.sha256(arm["mapping"][i].encode()).hexdigest()[:16],
                    mapping_j_sha256=hashlib.sha256(arm["mapping"][j].encode()).hexdigest()[:16],
                    planned_m_i=p[i][0],planned_c_i=p[i][1],
                    planned_m_j=p[j][0],planned_c_j=p[j][1],
                    real_m_i=a[i][0],real_c_i=a[i][1],
                    real_m_j=a[j][0],real_c_j=a[j][1]))
    best_pm=min(range(n),key=lambda j:(p[j][0],p[j][1],j))
    best_pc=min(range(n),key=lambda j:(p[j][1],p[j][0],j))
    min_real_m=min(x[0] for x in a)
    min_real_c=min(x[1] for x in a)
    meta={k:v for k,v in arm.items() if k not in
          ("pred","real","independent","mapping")}
    result=dict(**meta,
        candidate_pairs=n*(n-1)//2,
        makespan_mape_pct=statistics.mean(100*abs(y[0]-x[0])/x[0] for y,x in zip(p,a)),
        cost_mape_pct=statistics.mean(100*abs(y[1]-x[1])/x[1] for y,x in zip(p,a)),
        independent_planner_mape_delta_pct=statistics.mean(
            100*abs(q[0]-x[0])/x[0] for q,x in zip(inde,p)),
        predicted_nd=len(pnd),actual_nd=len(andx),overlap_nd=intersect,
        nd_jaccard=intersect/len(pnd|andx),
        predicted_nd_precision=intersect/len(pnd),
        predicted_nd_recall=intersect/len(andx),
        makespan_order_concordant=ms_pairs[0],makespan_order_discordant=ms_pairs[1],
        makespan_order_pred_tied=ms_pairs[2],makespan_order_actual_tied=ms_pairs[3],
        cost_order_concordant=cost_pairs[0],cost_order_discordant=cost_pairs[1],
        cost_order_pred_tied=cost_pairs[2],cost_order_actual_tied=cost_pairs[3],
        pareto_agree_pairs=d_pairs[0],pareto_lost_dominance=d_pairs[1],
        pareto_new_dominance=d_pairs[2],pareto_direction_reversed=d_pairs[3],
        pareto_mismatch_pairs=sum(d_pairs[1:]),
        pct_pareto_classification_error=100*sum(d_pairs[1:])/(n*(n-1)//2),
        selected_lowest_planned_m_real_regret_pct=100*(a[best_pm][0]/min_real_m-1),
        selected_lowest_planned_c_real_regret_pct=100*(a[best_pc][1]/min_real_c-1))
    if sum(d_pairs)!=n*(n-1)//2:
        raise AssertionError("Missing candidate pair")
    return result,errors

def write(path,records):
    if not records:raise AssertionError(("Empty result",path))
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]))
        writer.writeheader();writer.writerows(records)

def analyze(restarter,v19,out):
    original,shas=sources(restarter,v19)
    out.mkdir(parents=True,exist_ok=True)
    diagnostics=[]
    badpairs=[]
    physical=set()
    for arm in original:
        record,errors=diagnostic(arm)
        diagnostics.append(record)
        badpairs.extend(errors)
        for mapping in arm["mapping"]:
            physical.add((arm["workflow"],arm["source_seed"],arm["policy"],mapping))
    totalpairs=sum(r["candidate_pairs"] for r in diagnostics)
    assert totalpairs==6320,("All within-arm pair comparisons required",totalpairs)
    write(out/"all_96_optimizer_arm_rank_fidelity.csv",diagnostics)
    if badpairs:
        write(out/"all_pareto_misclassified_pairs.csv",badpairs)
    else:
        (out/"all_pareto_misclassified_pairs.csv").write_text("No predicted-vs-real Pareto classifications differed\n")
    groups={}
    for r in diagnostics:
        if r["origin"]=="v19":
            name=r["algorithm"]
        elif r["variant"] in ("old_full","ready_full","shortest_full","upward_full"):
            name=r["variant"]+"/"+("FLA" if r["algorithm"]==RESTART_ARMS[0] else "NSGA-II")
        else:
            name="split/"+("FLA" if r["algorithm"]==RESTART_ARMS[0] else "NSGA-II")
        groups.setdefault((r["origin"],name),[]).append(r)
    table=[
        "# Planner objective decision-ranking fidelity on 1024 true WorkflowSim K-selected replay points",
        "",
        "Read-only retrospective study, source Actions 41689142588 (40 jobs, 768 calls) and 41690669415 (4 jobs, 256 calls), **44 complete original jobs, 96 source optimizer arms, exactly 1024 recorded actual simulator replay calls and 6320 overlapping within-arm candidate pairs**. No new optimizer or simulator calls. Original program SHA by cohort: "+", ".join(
            f"{key}={list(val)[0]}" for key,val in shas.items())+".",
        "Deliberate repeated sources and repeated physical assignments are not counted as independent problems. "
        f"Observed {len(physical)} distinct (DAX, source-seed, runtime-priority, mapping) configurations across 1024 original replay rows. "
        "Reported percent-error and Pareto metrics are for preselected K candidates only; **not** the entire evaluated population or unknown simulator Pareto front.",
        "",
        "## Model rank fidelity: averaged over original SOURCE solver arms",
        "| Cohort / source treatment | Arms | Avg Makespan abs % error | Makespan directional reversals / comparable pairs | Pareto misclassified pair rate | Avg planned-vs-real K nondominated Jaccard |",
        "|---|---:|---:|---:|---:|---:|"
    ]
    for (origin,name),rr in sorted(groups.items()):
        reverse=sum(x["makespan_order_discordant"] for x in rr)
        comparable=sum(x["makespan_order_discordant"]+x["makespan_order_concordant"] for x in rr)
        table.append(f"| {origin}: {name} | {len(rr)} | "
           f"{statistics.mean(x['makespan_mape_pct'] for x in rr):.5f}% | "
           f"{reverse}/{comparable} | "
           f"{100*sum(x['pareto_mismatch_pairs'] for x in rr)/sum(x['candidate_pairs'] for x in rr):.3f}% | "
           f"{statistics.mean(x['nd_jaccard'] for x in rr):.3f} |")
    table+=["",
      "## Overall explanatory statistics",
      f"- Total original selected K replay candidates = {sum(x['k'] for x in diagnostics)}, "
      f"distinct physical candidates by DAG/seed/policy/mapping = {len(physical)}.",
      f"- Total Pareto pair classifications disagree = {sum(x['pareto_mismatch_pairs'] for x in diagnostics)} of {totalpairs} "
      f"({100*sum(x['pareto_mismatch_pairs'] for x in diagnostics)/totalpairs:.3f}%).",
      f"- Directly reversed planned-vs-real dominance pairs = {sum(x['pareto_direction_reversed'] for x in diagnostics)}; "
      f"lost planned dominances = {sum(x['pareto_lost_dominance'] for x in diagnostics)}; "
      f"new actual dominances absent from planner = {sum(x['pareto_new_dominance'] for x in diagnostics)}.",
      f"- Avg within-arm predicted-vs-real ND set Jaccard = "
      f"{statistics.mean(x['nd_jaccard'] for x in diagnostics):.3f}.",
      "",
      "## Highest per-arm Pareto ranking disagreement (descriptive, retrospective)"]
    for a in sorted(diagnostics,key=lambda r:-r["pct_pareto_classification_error"])[:10]:
        table.append(f"- {a['origin']} / {a['workflow']} / source seed {a['source_seed']} "
                     f"/ {a['variant']} / {a['algorithm']}: Makespan MAPE "
                     f"{a['makespan_mape_pct']:.4f}%, Pareto disagreement "
                     f"{a['pareto_mismatch_pairs']}/{a['candidate_pairs']} "
                     f"({a['pct_pareto_classification_error']:.2f}%), K-ND Jaccard {a['nd_jaccard']:.3f}.")
    table+=["",
      "## Limitations and next required falsification",
      "This audit is exploratory: previously observed WorkflowSim labels were available when it was designed. "
      "All simulator fronts are K-limited candidates selected using the planned fitness. "
      "The measured ranking error may differ sharply on rejected/unselected genotypes and should not be generalized.",
      "The 6320 task-pair comparisons are strongly correlated within 96 source optimizer arms and within only four DAG instances / seeds. "
      "Do not treat them as 6320 independent replicates or claim statistical significance.",
      "Even perfect candidate ranking on K-selected genotypes does not imply the optimizer generated diverse enough candidates or chose an efficient priority rule. "
      "A new algorithm should be tested separately with prospective new workflow families, full computation-time parity and never with retrospective best-policy labels.",
      "Original FLA, NSGA-II and FIFO defaults remain unchanged; this analysis produces CSV and explanation only."]
    (out/"pareto_rank_fidelity_retrospective_report.md").write_text("\n".join(table)+"\n",encoding="utf-8")
    print("\n".join(table))

if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: audit.py RESTART_SOURCE_ARTIFACTS V19_SOURCE_ARTIFACTS OUTPUT")
    analyze(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),pathlib.Path(sys.argv[3]))
