#!/usr/bin/env python3
"""Prospective algorithm-independent K4 decision-regret verification.

Original immutable WorkflowSim source run 42019263313: 4 DAX x 2 VM speed
regimes x 32 fixed genotypes. Neither OLD nor READY K4 gets simulator truth.
The actual K4 oracle is hindsight-only and exhaustively checks C(32,4).
"""
import csv
import hashlib
import random
import itertools
import math
import pathlib
import statistics
import sys

RUN="42019263313"
DAGS=("Inspiral_30","Sipht_30","Epigenomics_100","CyberShake_50")
PROFILES=("default","staggered")
POLICIES=(
    "all_vm0","all_vm12","round_robin","stride7",
    "evenodd_vm0_vm12","block4_vm0_vm12",
    "four_vm_round","four_vm_block5",
    "vm0_vm12_skew75","vm12_vm15_skew75",
    "prime_step5","prime_step11",
    "hash_seed17","hash_seed97",
    "monotonic_vm16","reverse_monotonic_vm16",
    "cyclic_step3","cyclic_step9","two_vm_alt_3_11","two_vm_block3_3_11",
    "four_vm_shift_round","four_vm_shift_block","eight_vm_odd_round","eight_vm_odd_block",
    "vm0_vm12_skew90","vm12_vm15_skew90","reverse_round_robin","reverse_stride7",
    "hash_seed211","hash_seed307","monotonic_vm8","reverse_monotonic_vm8")
METHODS=("old","ready","blind","first16_old","first16_ready")
TOL=1e-10

def read(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write(path, rows):
    assert rows
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def dominates(a,b):
    return a[0]<=b[0] and a[1]<=b[1] and (a[0]<b[0] or a[1]<b[1])

def rel(a,b):
    return 1 if dominates(a,b) else -1 if dominates(b,a) else 0

def front(points):
    return sorted(set(p for p in points if not any(dominates(q,p) for q in points)))

def hv(points,reference):
    ceiling=reference[1]
    val=0.
    for x,y in front(points):
        if x<reference[0] and y<ceiling:
            val+=(reference[0]-x)*(ceiling-y)
            ceiling=y
    answer=val/(reference[0]*reference[1])
    assert math.isfinite(answer) and -TOL<=answer<=1+TOL
    return answer

def k4_greedy(points, ref, labels):
    assert len(points)==len(labels) and len(points) in (16,32)
    # Tie break is predeclared: greater predicted marginal HV, then
    # lowest normalized sum M/Mmax+C/Cmax, then lexicographic policy name.
    maxima=(max(p[0] for p in points),max(p[1] for p in points))
    picks=[]
    for step in range(4):
        old=hv([points[i] for i in picks],ref)
        scored=[]
        for i in range(len(points)):
            if i in picks:continue
            gain=hv([points[j] for j in picks]+[points[i]],ref)-old
            scalar=points[i][0]/maxima[0]+points[i][1]/maxima[1]
            scored.append((-gain,scalar,labels[i],i))
        chosen=min(scored)[-1]
        picks.append(chosen)
    assert len(set(picks))==4
    return tuple(picks)

def source(root, dag, profile):
    folder=root/f"fla-independent32-{dag}-{profile}-{RUN}"
    assert folder.is_dir(),("Missing original physical source",str(folder))
    block=dict(s.split("=",1) for s in (folder/"block-id.txt").read_text().split())
    assert block==dict(DAG=dag,vm_speed=profile,seed="1501",
                       actual_priority="fifo",mappings="32",selection="none"),block
    sha=(folder/"source-sha.txt").read_text().strip()
    assert len(sha)==40 and all(c in "0123456789abcdef" for c in sha)
    records=read(folder/"same_mapping_true_replays.csv")
    assert len(records)==32 and {x["mapping_policy"] for x in records}==set(POLICIES)
    rows={x["mapping_policy"]:x for x in records}
    assert len({x["task_vm_mapping"] for x in records})==32
    for r in records:
        assert (r["workflow"],r["vm_profile"],r["seed"])==(dag,profile,"1501")
        n=int(r["task_count"])
        m=dict(tuple(map(int,v.split(":"))) for v in r["task_vm_mapping"].split("|"))
        assert set(m)==set(range(1,n+1)) and all(0<=v<16 for v in m.values())
        assert len(r["task_vm_mapping"].split("|"))==n
        for column in ("old_planned_makespan","old_planned_cost",
                       "ready_planned_makespan","ready_planned_cost",
                       "actual_makespan","actual_cost"):
            v=float(r[column])
            assert math.isfinite(v) and v>0,(dag,profile,column)
    return rows,sha

def audit(root,out):
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    pairs=[]
    chosen=[]
    shas=set()
    references=[]
    for dag in DAGS:
        for profile in PROFILES:
            src,sha=source(root,dag,profile)
            shas.add(sha)
            # Canonical 16 strategy positions, no selection from observed labels.
            x=[src[k] for k in POLICIES]
            truth=[(float(r["actual_makespan"]),float(r["actual_cost"])) for r in x]
            forecasts={model:[(float(r[model+"_planned_makespan"]),
                               float(r[model+"_planned_cost"])) for r in x]
                       for model in ("old","ready")}
            refs={factor:(factor*max(t[0] for t in truth)+1e-6,
                          factor*max(t[1] for t in truth)+1e-6)
                  for factor in (1.5,3.)}
            # Truth-label complete 1820-combination oracle, no approximation.
            best=-1.
            best_ids=None
            for combo in itertools.combinations(range(32),4):
                v=hv([truth[j] for j in combo],refs[1.5])
                if v>best+1e-12 or (abs(v-best)<=1e-12 and
                    (best_ids is None or tuple(POLICIES[k] for k in combo)<
                     tuple(POLICIES[k] for k in best_ids))):
                    best=v
                    best_ids=combo
            assert best_ids is not None
            ref30=refs[3.]
            oracle30=hv([truth[j] for j in best_ids],ref30)
            selected={}
            for model in METHODS:
                if model=="blind":
                    ids=(0,1,2,3)
                else:
                    predictor="old" if model=="first16_old" else "ready" if model=="first16_ready" else model
                    pred=forecasts[predictor]
                    if model.startswith("first16_"):
                        pred=pred[:16]
                        candidates=POLICIES[:16]
                    else:
                        candidates=POLICIES
                    predref=tuple(1.5*max(t[k] for t in pred)+1e-6 for k in (0,1))
                    ids=k4_greedy(pred,predref,candidates)
                realized=hv([truth[j] for j in ids],refs[1.5])
                realized3=hv([truth[j] for j in ids],refs[3.])
                assert realized<=best+1e-10
                selected[model]=dict(ids=ids,hv=realized,regret=best-realized)
                rows.append(dict(workflow=dag,vm_profile=profile,method=model,
                    original_source_sha=sha,seed=1501,
                    selected_policies="|".join(POLICIES[j] for j in ids),
                    true_hv_k4_15=realized,regret_vs_true_oracle_15=best-realized,
                    true_hv_k4_30=realized3,
                    regret_vs_15_optimal_set_under_3x=oracle30-realized3,
                    true_oracle_k4_15=best,oracle_policies="|".join(POLICIES[j] for j in best_ids),
                    reference_true_m=refs[1.5][0],reference_true_c=refs[1.5][1]))
            assert len(selected)==5
            selection_diff=int(set(selected["old"]["ids"])!=set(selected["ready"]["ids"]))
            for record in rows[-5:]:
                record["old_ready_K4_set_differs"]=selection_diff
                record["old_minus_ready_true_hv"]=selected["old"]["hv"]-selected["ready"]["hv"]
                record["old_minus_first16_old_true_hv"]=selected["old"]["hv"]-selected["first16_old"]["hv"]
                record["ready_minus_first16_ready_true_hv"]=selected["ready"]["hv"]-selected["first16_ready"]["hv"]
            salt=int(hashlib.sha256(
                f"frozen-independent32-k4-sham|{dag}|{profile}|1501".encode("utf-8")
                ).hexdigest()[:16],16)
            rng=random.Random(salt)
            sham_scores=[hv([truth[i] for i in rng.sample(range(32),4)],refs[1.5])
                         for _ in range(32)]
            for record in rows[-5:]:
                record["random32_sham_mean_hv"]=statistics.mean(sham_scores)
                record["random32_sham_max_hv"]=max(sham_scores)
            for model in ("old","ready"):
                pred=forecasts[model]
                wrong=0
                reversed_count=0
                comparable=0
                materially_wrong=0
                new_dominances=0
                for i,j in itertools.combinations(range(32),2):
                    a=rel(pred[i],pred[j])
                    b=rel(truth[i],truth[j])
                    if a!=0:
                        comparable+=1
                        if a!=b:
                            wrong+=1
                            if b==-a:reversed_count+=1
                            # A wrong planned dominance is material if actual
                            # objectives differ >0.1% on at least one coordinate.
                            gap=max(abs(truth[i][d]-truth[j][d])/
                                    max(truth[i][d],truth[j][d]) for d in (0,1))
                            materially_wrong+=gap>0.001
                    elif b!=0:
                        new_dominances+=1
                planned_nd={i for i in range(32) if not any(
                    dominates(pred[j],pred[i]) for j in range(32) if j!=i)}
                true_nd={i for i in range(32) if not any(
                    dominates(truth[j],truth[i]) for j in range(32) if j!=i)}
                pairs.append(dict(workflow=dag,vm_profile=profile,predictor=model,
                    comparable_planned_pairs=comparable,
                    false_planned_dominance_pairs=wrong,
                    directly_reversed_dominance_pairs=reversed_count,
                    material_false_dominance_pairs=materially_wrong,
                    planned_incomparable_true_dominance_pairs=new_dominances,
                    planned_vs_true_nd_jaccard=len(planned_nd&true_nd)/len(planned_nd|true_nd),
                    mean_absolute_makespan_relative_error=statistics.mean(
                        abs(pred[j][0]-truth[j][0])/truth[j][0] for j in range(32)),
                    true_k4_regret=selected[model]["regret"],
                    true_k4_gain_over_blind=selected[model]["hv"]-selected["blind"]["hv"],
                    true_k4_gain_over_other=
                      selected[model]["hv"]-selected["ready" if model=="old" else "old"]["hv"]))
            for i,pt in enumerate(truth):
                chosen.append(dict(workflow=dag,vm_profile=profile,
                    policy=POLICIES[i],actual_makespan=pt[0],actual_cost=pt[1],
                    old_pred_m=forecasts["old"][i][0],old_pred_cost=forecasts["old"][i][1],
                    ready_pred_m=forecasts["ready"][i][0],ready_pred_cost=forecasts["ready"][i][1],
                    old_selected=int(i in selected["old"]["ids"]),
                    ready_selected=int(i in selected["ready"]["ids"]),
                    blind_selected=int(i in selected["blind"]["ids"]),
                    oracle_selected=int(i in best_ids)))
    assert len(rows)==40 and len(pairs)==16 and len(chosen)==256
    assert len(shas)==1,("Mixed source revisions",shas)
    for dag in DAGS:
        a={r["policy"]:r for r in chosen if r["workflow"]==dag and r["vm_profile"]=="default"}
        b={r["policy"]:r for r in chosen if r["workflow"]==dag and r["vm_profile"]=="staggered"}
        assert set(a)==set(b)==set(POLICIES)
    write(out/"all_40_k4_oracle_regrets.csv",rows)
    write(out/"all_16_planner_true_dominance_pairs.csv",pairs)
    write(out/"all_256_original_same_mapping_truth.csv",chosen)
    report=["# Algorithm-independent fixed 16-VM mapping: prospective K4 decision regret",
       "","8 original DAG-size/VM-speed blocks, 256 physical WorkflowSim replay labels.",
       "OLD/READY forecast over the SAME original physical genotype; selections NEVER see true labels.",
       "Original first16 policies unchanged, plus 16 frozen new policies; no FLA/NSGA-II.",
       "True K4 oracle exhaustively checks C(32,4)=35960 subsets, retrospective ceiling only.",
       "Common actual reference per (DAG, VM profile) across all methods.","",
       "| DAG | Speed | OLD K4 real HV | READY K4 real HV | Blind K4 real HV | Oracle K4 real HV | OLD regret | READY regret |",
       "|---|---|---:|---:|---:|---:|---:|---:|"]
    for dag in DAGS:
        for speed in PROFILES:
            r={x["method"]:x for x in rows if x["workflow"]==dag and x["vm_profile"]==speed}
            report.append(f"| {dag} | {speed} | {r['old']['true_hv_k4_15']:.8f} | "
                 f"{r['ready']['true_hv_k4_15']:.8f} | {r['blind']['true_hv_k4_15']:.8f} | "
                 f"{r['old']['true_oracle_k4_15']:.8f} | "
                 f"{r['old']['regret_vs_true_oracle_15']:.8f} | "
                 f"{r['ready']['regret_vs_true_oracle_15']:.8f} |")
    for model in METHODS:
        rr=[r for r in rows if r["method"]==model]
        report.append(f"- {model}: mean true K4 regret={statistics.mean(r['regret_vs_true_oracle_15'] for r in rr):.9f}; "
            f"exact oracle matches={sum(abs(r['regret_vs_true_oracle_15'])<1e-10 for r in rr)}/8.")
    report.append(f"- OLD-vs-READY chosen K4 physical set differs in "
        f"{sum(r['old_ready_K4_set_differs'] for r in rows if r['method']=='old')}/8 DAG/profile blocks.")
    for model in ("old","ready"):
        pp=[r for r in pairs if r["predictor"]==model]
        report.append(f"- {model}: planned strict dominance pairs={sum(r['comparable_planned_pairs'] for r in pp)}, "
            f"false={sum(r['false_planned_dominance_pairs'] for r in pp)}, "
            f"direct reversed={sum(r['directly_reversed_dominance_pairs'] for r in pp)}, "
            f"material false={sum(r['material_false_dominance_pairs'] for r in pp)}; "
            f"mean true K4 HV gain over blind={statistics.mean(r['true_k4_gain_over_blind'] for r in pp):+.9f}.")
    report+=["","These results do not imply independent DAG-family holdout: all four families were studied",
       "historically, though these exact source instance sizes/VM combinations are newly measured.",
       "256 mappings and 3968 within-block pairs are NOT 128/960 statistically independent workflows.",
       "This evaluates planner decisions on a frozen small mapping universe, NOT the FLA search",
       "quality, and is NOT a publication-ready new scheduling method."]
    (out/"independent32_k4_decision_regret_findings.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    assert len(sys.argv)==3,"Usage: script.py ORIGINAL_SOURCE_ARTIFACTS REPORT_FOLDER"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
