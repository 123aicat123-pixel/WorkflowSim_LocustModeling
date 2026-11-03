#!/usr/bin/env python3
"""Registered, PASSIVE selected breeding population mechanism analysis by DO/EO/SSO."""
import collections,csv,math,pathlib,statistics,sys

DAGS=("Montage_25","CyberShake_30")
SEEDS=(173,174)
PROFILES=("default","staggered")
ALGS=("DAG-Pareto-FLA[v12-hvbandit]",
      "DAG-Pareto-FLA[v14-randompair]",
      "DAG-Pareto-FLA[v14-timelinepair]",
      "DAG-Pareto-FLA[v15-randomgate]",
      "DAG-Pareto-FLA[v15-timelinegate]")
ALL=ALGS+("NSGA-II[costseed]",)
PHASE={0:"DO",1:"EO",2:"SSO"}
def load(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))
def get(row,key):return float(row[key])
def hv(points,ref):
    total,last=0.,ref[1]
    for m,c in sorted(set(points)):
        if m<ref[0] and c<last:
            total+=(ref[0]-m)*(last-c);last=c
    return total
def analyze(root,out):
    data={}; cases=[]
    for dag in DAGS:
        for speed in PROFILES:
            for seed in SEEDS:
                prefix=f"phase-pop-{speed}-{dag}-s{seed}"
                files={s:list(root.rglob(prefix+s)) for s in (
                    "_population_diagnostics.csv","_summary.csv",
                    "_replays.csv","_budget_protocol.txt")}
                assert all(len(p)==1 for p in files.values()),(prefix,files)
                traces=load(files["_population_diagnostics.csv"][0])
                summaries=load(files["_summary.csv"][0])
                replays=load(files["_replays.csv"][0])
                assert len(traces)==5*101 and len(summaries)==6 and len(replays)==6*16,(prefix,len(traces))
                assert {r["algorithm"] for r in summaries}==set(ALL)
                protocol=files["_budget_protocol.txt"][0].read_text()
                assert "PROSPECTIVE_REPLAY_BUDGET_K=16" in protocol
                assert "PROSPECTIVE_REPLAY_POLICY=pareto-cover" in protocol
                assert "VM_SPEED_PROFILE="+speed in protocol
                for r in summaries:
                    assert int(r["evaluations"])==int(r["captured_evaluations"])==3030
                    assert int(r["replayed"])==16
                expectedPhases=None
                for alg in ALGS:
                    rows=sorted([x for x in traces if x["algorithm"]==alg],
                                key=lambda x:int(get(x,"generation")))
                    assert len(rows)==101
                    assert [int(get(x,"generation")) for x in rows]==list(range(101))
                    assert [int(get(x,"objective_evaluations")) for x in rows]==[30*(i+1) for i in range(101)]
                    assert all(get(x,"selected_unique")+get(x,"selected_duplicate_slots")==30 for x in rows)
                    assert all(0<=get(x,"pairwise_hamming_all")<=1 for x in rows)
                    phases=[int(get(x,"phase")) for x in rows[1:]]
                    assert set(phases)==set(PHASE)
                    if expectedPhases is None:expectedPhases=phases
                    else:assert expectedPhases==phases,("different phase pattern",dag,speed,seed,alg)
                    assert int(get(rows[0],"phase"))==-1
                    data[dag,speed,seed,alg]=rows
                    if alg.startswith("DAG-Pareto-FLA[v15"):
                        assert sum(int(get(x,"local_gate_rejections")) for x in rows[1:])>0
                    else:
                        assert sum(int(get(x,"local_gate_rejections")) for x in rows[1:])==0
                    for phase in PHASE:
                        z=[x for x in rows[1:] if int(get(x,"phase"))==phase]
                        assert z
                        cases.append(dict(workflow=dag,vm_speed=speed,seed=seed,algorithm=alg,phase=PHASE[phase],
                          generations=len(z),
                          mean_unique=statistics.mean(get(x,"selected_unique") for x in z),
                          mean_duplicate_slots=statistics.mean(get(x,"selected_duplicate_slots") for x in z),
                          mean_hamming=statistics.mean(get(x,"pairwise_hamming_all") for x in z),
                          mean_group_overlap=statistics.mean(get(x,"cross_group_overlap") for x in z),
                          mean_generated_unique=statistics.mean(get(x,"generated_unique") for x in z),
                          archive_insertions=sum(int(get(x,"archive_insert_events")) for x in z),
                          local_gate_rejections=sum(int(get(x,"local_gate_rejections")) for x in z),
                          bandit_normal_uses=sum(int(get(x,"bandit_baseline_uses")+get(x,"bandit_colocate_uses")+get(x,"bandit_critical_uses")) for x in z)))
                data[dag,speed,seed,"_replays"]=replays
    assert len(cases)==len(DAGS)*len(PROFILES)*len(SEEDS)*len(ALGS)*3
    out.mkdir(parents=True,exist_ok=True)
    with (out/"phase_population_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
    paired=[]
    for dag in DAGS:
        for speed in PROFILES:
            for seed in SEEDS:
                def z(alg,phase):
                    return next(x for x in cases if x["workflow"]==dag and x["vm_speed"]==speed and x["seed"]==seed and x["algorithm"]==alg and x["phase"]==phase)
                for phase in PHASE.values():
                    v12,rt,tt,rg,tg=[z(alg,phase) for alg in ALGS]
                    paired.append(dict(workflow=dag,vm_speed=speed,seed=seed,phase=phase,
                       generations=tg["generations"],
                       timeline_gate_vs_ungated_selected_unique=tg["mean_unique"]-tt["mean_unique"],
                       random_gate_vs_ungated_selected_unique=rg["mean_unique"]-rt["mean_unique"],
                       timeline_gate_vs_v12_selected_unique=tg["mean_unique"]-v12["mean_unique"],
                       timeline_gate_vs_ungated_hamming=tg["mean_hamming"]-tt["mean_hamming"],
                       timeline_gate_vs_ungated_generated_unique=tg["mean_generated_unique"]-tt["mean_generated_unique"],
                       timeline_gate_rejections=tg["local_gate_rejections"],
                       random_gate_rejections=rg["local_gate_rejections"],
                       timeline_gate_archive_add=tg["archive_insertions"],
                       timeline_ungated_archive_add=tt["archive_insertions"]))
    assert len(paired)==len(DAGS)*len(PROFILES)*len(SEEDS)*3
    with (out/"phase_population_paired.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(paired[0]));w.writeheader();w.writerows(paired)
    hvCases=[]
    for dag in DAGS:
        for speed in PROFILES:
            planned=[(float(x["planned_makespan"]),float(x["planned_cost"]))
                for seed in SEEDS for x in data[dag,speed,seed,"_replays"]]
            reference=(1.5*max(x[0] for x in planned)+1,1.5*max(x[1] for x in planned)+1)
            for seed in SEEDS:
                replay=data[dag,speed,seed,"_replays"]
                val={}
                for alg in ALL:
                    rr=[x for x in replay if x["algorithm"]==alg]
                    assert len(rr)==16
                    pts=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in rr]
                    assert all(a<reference[0] and b<reference[1] for a,b in pts),("invalid reference",dag,speed,seed)
                    val[alg]=hv(pts,reference)
                    assert val[alg]>0
                hvCases.append(dict(workflow=dag,vm_speed=speed,seed=seed,
                     v15_timeline_vs_v14_timeline_pct=100*(val[ALGS[4]]/val[ALGS[2]]-1),
                     v15_timeline_vs_v12_pct=100*(val[ALGS[4]]/val[ALGS[0]]-1),
                     v15_timeline_vs_nsga_pct=100*(val[ALGS[4]]/val[ALL[5]]-1)))
    with (out/"phase_population_hv_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(hvCases[0]));w.writeheader();w.writerows(hvCases)
    lines=["# Passive FLA DO/EO/SSO breeding-population mechanism study","",
      "All values below come from ACTUAL POST-SELECTION breeding groups, not from cumulative evaluated genotype history. Same 3030 counted objective evaluations and K16 actual WorkflowSim replays per solver; instrumentation already passed strict ON/OFF SHA+simulator identity gate 41621195545.",
      "This is a small development study on previously explored DAG families, two seeds per speed. A phase correlation does not identify a causal influence: FLA stage also covaries with iteration count and changing population state.","",
      "| Phase | Mean v15 timeline gate minus v14 timeline unique selected slots | Mean v15 random gate minus v14 random unique slots | Mean v15 timeline gate minus v14 timeline pairwise Hamming | Total v15 timeline rejected trial slots |",
      "|---|---:|---:|---:|---:|"]
    for phase in PHASE.values():
        xs=[x for x in paired if x["phase"]==phase]
        lines.append(f"| {phase} | {statistics.mean(x['timeline_gate_vs_ungated_selected_unique'] for x in xs):+.4f} | {statistics.mean(x['random_gate_vs_ungated_selected_unique'] for x in xs):+.4f} | {statistics.mean(x['timeline_gate_vs_ungated_hamming'] for x in xs):+.6f} | {sum(x['timeline_gate_rejections'] for x in xs)} |")
    lines+=["","## Case-level v15 timeline-gate effect by actual selected breeding population",
      "| DAG | Speed | Seed | Phase | Gate−ungated unique slots | Gate−ungated Hamming | Gate rejected trials |",
      "|---|---|---:|---|---:|---:|---:|"]
    for x in paired:
        lines.append(f"| {x['workflow']} | {x['vm_speed']} | {x['seed']} | {x['phase']} | {x['timeline_gate_vs_ungated_selected_unique']:+.4f} | {x['timeline_gate_vs_ungated_hamming']:+.6f} | {x['timeline_gate_rejections']} |")
    lines+=["","## Actual WorkflowSim K16 HV context, primary planned-only reference",
      "Reference is 1.5× max PLANNED selected K16 objectives across ALL six arms and two seeds within each DAG/speed, +1. The reference must contain every actual simulator result; it never uses actual outcomes to change bounds.",
      "| DAG | Speed | Seed | v15 timeline vs v14 timeline | v15 timeline vs v12 | v15 timeline vs seeded NSGA-II |",
      "|---|---|---:|---:|---:|---:|"]
    for x in hvCases:
        lines.append(f"| {x['workflow']} | {x['vm_speed']} | {x['seed']} | {x['v15_timeline_vs_v14_timeline_pct']:+.4f}% | {x['v15_timeline_vs_v12_pct']:+.4f}% | {x['v15_timeline_vs_nsga_pct']:+.4f}% |")
    lines+=["","## Boundaries",
       "Selected-genotype uniqueness, Hamming, and group overlap are descriptive counts. Source phase-bandit per generation is only charged to normal children; paired local probes have a separate gate-rejection count. Archive insertion events are admissions, not final archive survivors or HV deltas.",
       "A post-selection duplicate can arise from ordinary survivor selection too: only the paired v14 vs v15 comparison can describe incremental gate-associated changes. Association is not causation, and phase timing cannot be separated from generation progression without additional randomized interventions.",
       "These used already-studied families; do not claim new holdout validity. No algorithm defaults were changed, and this passive instrumentation must never be used to feed the optimizer selection logic."]
    (out/"phase_population_report.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_phase_population_report.py INPUT_ARTIFACTS OUTPUT_DIRECTORY")
    analyze(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
