#!/usr/bin/env python3
"""Compare REAL equal-K WorkflowSim candidate replays after identical 3030 fitness-call searches.

Both policies are prospective: only their K selected assignments are actually simulated.
All comparisons use one common per-family HV reference across both policies, solvers,
and seeds, constructed post-hoc from ONLY the K replays, not from a full oracle.
"""
import csv
import math
import pathlib
import statistics
import sys
from collections import defaultdict

SOLVERS=('DAG-Pareto-FLA[v7-costseed]','DAG-Pareto-FLA[v12-hvbandit]','NSGA-II[costseed]')
FAMILIES=('CyberShake_100','Inspiral_50','Montage_25')
SEEDS=(53,54)
POLICIES=('pareto-cover','random')
K=16
EVALS=3030

def load(path):
    with path.open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

def front(raw):
    best=float('inf')
    result=[]
    for m,c in sorted(set(raw)):
        if c<best:
            result.append((m,c));best=c
    return result

def hv(points,ref):
    total,last=0.,ref[1]
    for m,c in front(points):
        if m<ref[0] and c<last:
            total+=(ref[0]-m)*(last-c)
            last=c
    return total

def run(root,out):
    outcomes=defaultdict(list)
    sources=defaultdict(dict)
    for policy,prefix in (('pareto-cover','cover3030_'),('random','random3030_')):
        replays=list(root.rglob(prefix+'*_replays.csv'))
        sums=list(root.rglob(prefix+'*_summary.csv'))
        assert len(replays)==len(sums)==len(FAMILIES)*len(SEEDS),(policy,len(replays),len(sums))
        for path in replays:
            for r in load(path):
                key=policy,r['workflow'],int(r['seed']),r['algorithm']
                assert key[1] in FAMILIES and key[2] in SEEDS and key[3] in SOLVERS,key
                point=float(r['sim_makespan']),float(r['sim_cost'])
                assert all(math.isfinite(v) and v>0 for v in point)
                outcomes[key].append(point)
        for path in sums:
            for r in load(path):
                key=policy,r['workflow'],int(r['seed']),r['algorithm']
                assert int(r['evaluations'])==int(r['captured_evaluations'])==EVALS,r
                assert int(r['replayed'])==K,r
                sources[key]=dict(source_archive=r['source_archive'],
                        distinct_observed=r['distinct_observed'],
                        planned_nd=r['distinct_planned_nondominated'])
    assert len(outcomes)==len(sources)==len(POLICIES)*len(FAMILIES)*len(SEEDS)*len(SOLVERS)
    assert all(len(v)==K for v in outcomes.values())
    for wf in FAMILIES:
        for seed in SEEDS:
            for alg in SOLVERS:
                assert sources['pareto-cover',wf,seed,alg]==sources['random',wf,seed,alg],(
                    'Search history changed between policies',wf,seed,alg)
    refs={}
    for wf in FAMILIES:
        all_points=[p for key,points in outcomes.items() if key[1]==wf for p in points]
        refs[wf]=(max(x[0] for x in all_points)*1.05+1,
                  max(x[1] for x in all_points)*1.05+1)
    rows=[]
    for (policy,wf,seed,alg),points in sorted(outcomes.items()):
        value=hv(points,refs[wf])
        rows.append(dict(workflow=wf,seed=seed,algorithm=alg,policy=policy,
                        planner_evaluations=EVALS,actual_simulator_calls=K,
                        simulator_hv=value,ref_m=refs[wf][0],ref_c=refs[wf][1]))
    scores={(r['policy'],r['workflow'],r['seed'],r['algorithm']):r['simulator_hv'] for r in rows}
    report=['# Real 3030 evaluation x K=16 prospective Pareto-cover versus random',
            '', 'Three workflow families, two paired seeds, three equal-costseed solver arms.',
            'BOTH policies run 3030 actual planning fitness calls per algorithm and K=16 actual WorkflowSim replay assignments.',
            'Each paired algorithm/seed has matching source archive, unique visited genotype counts and planned-ND archive size.',
            'Policies are applied after search and use ONLY planned objectives or genotype identity; no simulator labels select candidates.',
            'All solver/policy/seed scores within one DAG family use a shared post-hoc reference derived from the UNION of policy-selected simulator points.',
            'The random control is ONE predeclared deterministic random draw per case; no p-value or performance generalization is justified.',
            '', '| Workflow | Seed | Solver | Pareto-cover HV advantage vs random |',
            '|---|---:|---|---:|']
    diffs=defaultdict(list);wins=defaultdict(int)
    for wf in FAMILIES:
        for seed in SEEDS:
            for alg in SOLVERS:
                a=scores['pareto-cover',wf,seed,alg]
                b=scores['random',wf,seed,alg]
                delta=100*(a/max(1e-12,b)-1)
                diffs[alg].append(delta);wins[alg]+=a>b
                report.append(f'| {wf} | {seed} | {alg} | {delta:+.3f}% |')
    report+=['','## Within-solver paired descriptive summary',
        '', '| Solver | Mean relative K=16 HV improvement vs random | Cover wins / 6 |',
        '|---|---:|---:|']
    for alg in SOLVERS:
        report.append(f'| {alg} | {statistics.mean(diffs[alg]):+.3f}% | {wins[alg]}/6 |')
    report+=['','## Scientific limits',
       'These are 16-point selected simulator Pareto fronts, not all-history fronts or globally optimal fronts.',
       'The reference is shared across the two policies but not preregistered; it is post-hoc derived from selected K points.',
       'The random comparator has one draw per scenario; repeated seeds and further workload families are required.',
       'A larger or smaller K, workload/VM stress, total runtime and a robust statistical analysis are not established.',
       'An improvement in screening versus random does not prove that the underlying FLA optimizer is superior to NSGA-II.']
    out.mkdir(parents=True,exist_ok=True)
    with (out/'prospective_policy_scores.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (out/'prospective_policy_report.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print('\n'.join(report))

if __name__=='__main__':
    if len(sys.argv)!=3:
        raise SystemExit('Usage: prospective_policy_compare.py INPUT_DIR OUTPUT_DIR')
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
