#!/usr/bin/env python3
"""Fixed-WorkflowSim-call selection audit using already verified full-history replay.

Selection receives ONLY planned objectives/genotype; true simulation labels are
revealed solely after selection to score the budgeted replay. Retrospective
diagnostic, not an online simulator-in-the-loop optimizer.
"""
import argparse
import csv
import hashlib
import pathlib
import statistics
from collections import defaultdict
from dataclasses import dataclass

SOLVERS = ('DAG-Pareto-FLA[v7-costseed]', 'DAG-Pareto-FLA[v12-hvbandit]', 'NSGA-II[costseed]')
BUDGETS = (8, 16, 24, 32)
REPEATS = 16

@dataclass(frozen=True)
class Planned:
    mapping: str
    m: float
    c: float

def read(path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def front(points):
    out, low = [], float('inf')
    for m, c in sorted(set(points)):
        if c < low:
            out.append((m, c))
            low = c
    return out

def hv(points, ref):
    total, last = 0., ref[1]
    for m, c in front(points):
        if m < ref[0] and c < last:
            total += (ref[0] - m) * (last - c)
            last = c
    return total

def layers(items):
    left = sorted(items, key=lambda x: (x.m, x.c, x.mapping))
    while left:
        chosen = set(front((c.m, c.c) for c in left))
        layer = [c for c in left if (c.m, c.c) in chosen]
        assert layer
        used = {c.mapping for c in layer}
        yield layer
        left = [c for c in left if c.mapping not in used]

def cover(items):
    lo_m,lo_c = min(x.m for x in items),min(x.c for x in items)
    dm = max(1e-12,max(x.m for x in items)-lo_m)
    dc = max(1e-12,max(x.c for x in items)-lo_c)
    picked = []
    for group in layers(items):
        pending = list(group)
        while pending:
            if not picked:
                nxt = min(pending,key=lambda x:(x.m,x.c,x.mapping))
            else:
                points = [((x.m-lo_m)/dm,(x.c-lo_c)/dc) for x in picked]
                def rank(x):
                    a,b=(x.m-lo_m)/dm,(x.c-lo_c)/dc
                    d=min((a-u)**2+(b-v)**2 for u,v in points)
                    return (-d,x.m,x.c,x.mapping)
                nxt = min(pending,key=rank)
            picked.append(nxt)
            pending.remove(nxt)
    return picked

def shuffle(items, key):
    def digest(c):
        text='fla-replay-budget-v1|'+'|'.join(map(str,key))+'|'+c.mapping
        return hashlib.sha256(text.encode()).hexdigest()
    return sorted(items,key=lambda c:(digest(c),c.mapping))

def sweep(items):
    lo_m,lo_c=min(x.m for x in items),min(x.c for x in items)
    dm=max(1e-12,max(x.m for x in items)-lo_m)
    dc=max(1e-12,max(x.c for x in items)-lo_c)
    def radical(i):
        value,power=0.,0.5
        while i:
            value+=(i&1)*power
            power*=0.5
            i>>=1
        return value
    weights=[0.,1.]+[radical(i) for i in range(1,100)]
    remainder=list(items)
    ordered=[]
    for w in weights:
        if not remainder: break
        item=min(remainder,key=lambda x:(w*(x.m-lo_m)/dm+(1-w)*(x.c-lo_c)/dc,
                                         x.m,x.c,x.mapping))
        ordered.append(item)
        remainder.remove(item)
    ordered += [x for x in cover(items) if x in remainder]
    return ordered

def choose(items,key,policy,k,rep):
    if policy=='pareto-cover':
        result=cover(items)[:k]
    elif policy=='half-cover-half-random':
        start=cover(items)[:(k+1)//2]
        used={x.mapping for x in start}
        result=start+shuffle([x for x in items if x.mapping not in used],(*key,rep))[:k-len(start)]
    elif policy=='scalar-sweep':
        result=sweep(items)[:k]
    elif policy=='random':
        result=shuffle(items,(*key,rep))[:k]
    else:
        raise ValueError(policy)
    assert len(result)==k and len({c.mapping for c in result})==k
    return result

def load(root,workflows,seeds):
    history=defaultdict(dict)
    base=defaultdict(list)
    expected=len(workflows)*len(seeds)
    for suffix,is_base in (('_replays.csv',True),('_screening_samples.csv',False)):
        paths=list(root.rglob('*'+suffix))
        assert len(paths)==expected,(suffix,len(paths),expected)
        for path in paths:
            for r in read(path):
                key=(r['workflow'],int(r['seed']),r['algorithm'])
                assert key[0] in workflows and key[1] in seeds and key[2] in SOLVERS,key
                planned=Planned(r['mapping'],float(r['planned_makespan']),float(r['planned_cost']))
                sim=float(r['sim_makespan']),float(r['sim_cost'])
                assert min(planned.m,planned.c,sim[0],sim[1])>0
                assert planned.mapping not in history[key],key
                history[key][planned.mapping]=planned,sim
                if is_base:base[key].append(planned.mapping)
    assert len(history)==expected*3
    assert all(len(rows)>=max(BUDGETS) for rows in history.values())
    n=0
    for path in root.rglob('*_screening_summary.csv'):
        for r in read(path):
            key=(r['workflow'],int(r['seed']),r['algorithm'])
            assert int(r['unique_visited'])==len(history[key])
            assert int(r['sampled'])+len(base[key])==len(history[key])
            n+=1
    assert n==expected*3
    summaries=[p for p in root.rglob('*_summary.csv') if not p.name.endswith('_screening_summary.csv')]
    assert len(summaries)==expected
    for p in summaries:
        for r in read(p):
            key=r['workflow'],int(r['seed']),r['algorithm']
            assert int(r['captured_evaluations'])==int(r['evaluations'])==80
            assert int(r['replayed'])==len(base[key])
    return history,base

def write(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def analyze(root,dest,workflows,seeds,source_run,phase):
    history,base=load(root,workflows,seeds)
    refs={}
    for wf in workflows:
        raw=[history[key][mapping][1] for key in history if key[0]==wf for mapping in base[key]]
        refs[wf]=max(p[0] for p in raw)*1.05+1,max(p[1] for p in raw)*1.05+1
    policies=('pareto-cover','half-cover-half-random','scalar-sweep','random')
    full={}
    rows=[]
    for key,data in sorted(history.items()):
        wf,seed,alg=key
        options=sorted([x[0] for x in data.values()],key=lambda x:x.mapping)
        oracle=hv((x[1] for x in data.values()),refs[wf])
        assert oracle>0
        full[key]=oracle
        for k in BUDGETS:
            for policy in policies:
                repeats=REPEATS if policy in ('random','half-cover-half-random') else 1
                for rep in range(repeats):
                    selected=choose(options,key,policy,k,rep)
                    observed=hv([data[x.mapping][1] for x in selected],refs[wf])
                    assert -1e-8<=observed<=oracle+1e-8*max(1.,oracle)
                    rows.append(dict(workflow=wf,seed=seed,algorithm=alg,budget=k,policy=policy,
                        replicate=rep,selected=k,visited=len(options),original_replayed=len(base[key]),
                        ref_m=refs[wf][0],ref_c=refs[wf][1],selected_hv=observed,all_visited_hv=oracle,
                        recovery_pct=100*observed/oracle))
    ranking=[]
    for wf in workflows:
        for seed in seeds:
            full_winner=max(SOLVERS,key=lambda x:full[(wf,seed,x)])
            for k in BUDGETS:
                for policy in policies:
                    reps=REPEATS if policy in ('random','half-cover-half-random') else 1
                    for rep in range(reps):
                        chosen={r['algorithm']:r['selected_hv'] for r in rows
                                if r['workflow']==wf and r['seed']==seed
                                and r['budget']==k and r['policy']==policy and r['replicate']==rep}
                        assert len(chosen)==3
                        winner=max(SOLVERS,key=lambda x:chosen[x])
                        ranking.append(dict(workflow=wf,seed=seed,budget=k,policy=policy,replicate=rep,
                            full_winner=full_winner,budget_winner=winner,mismatch=int(full_winner!=winner),
                            v12_vs_nsga_pct=100*(chosen[SOLVERS[1]]/max(1e-12,chosen[SOLVERS[2]])-1)))
    report=['# Fixed simulator replay budget (retrospective WorkflowSim audit)','',
        f'Phase: {phase}. Original full-replay GitHub Actions source run: {source_run}.',
        f'{len(workflows)} workflow families x {len(seeds)} paired seeds x 3 algorithms, each with 80 genuine search fitness evaluations.',
        'All screening policies use planned makespan, planned cost and genotype identity ONLY.',
        'True WorkflowSim makespan/cost are looked up after selection for scoring, never for choosing.',
        'Every solver and selection policy consumes exactly K replay observations for the compared K.',
        'This is an offline full-history oracle audit and does NOT save the cost of generating its original full simulator labels.',
        f'Random/hybrid policies have {REPEATS} reproducible deterministic hash-seeded draws per case, which are NOT independent workflows.',
        'Reference point is frozen separately per workflow family using ONLY original planned-front replays across all solvers and seeds.',
        'Front recovery is relative to the FULL VISITED genotype history, not a global search-space Pareto optimum.','',
        '| Replay budget | Planned-only screening policy | Mean recovery | Median recovery | Wrong winner vs full visited front |',
        '|---:|---|---:|---:|---:|']
    for k in BUDGETS:
        for policy in policies:
            g=[r['recovery_pct'] for r in rows if r['budget']==k and r['policy']==policy]
            errs=[r['mismatch'] for r in ranking if r['budget']==k and r['policy']==policy]
            expected=len(workflows)*len(seeds)*(REPEATS if policy in ('random','half-cover-half-random') else 1)
            assert len(g)==expected*3 and len(errs)==expected
            report.append(f'| {k} | {policy} | {statistics.mean(g):.3f}% | {statistics.median(g):.3f}% | {sum(errs)}/{expected} |')
    report+=['','## Per-family/per-algorithm mean recovery at K=16','','| Workflow | Algorithm | Pareto cover | Hybrid | Scalar sweep | Random |',
             '|---|---|---:|---:|---:|---:|']
    for wf in workflows:
        for alg in SOLVERS:
            vals={policy:statistics.mean(r['recovery_pct'] for r in rows if r['workflow']==wf
                and r['algorithm']==alg and r['policy']==policy and r['budget']==16)
                for policy in policies}
            report.append(f'| {wf} | {alg} | {vals["pareto-cover"]:.2f}% | {vals["half-cover-half-random"]:.2f}% | {vals["scalar-sweep"]:.2f}% | {vals["random"]:.2f}% |')
    report+=['','## Scientific limits',
        'Search evaluations (80) and simulator replay observations (K) are different budgets.',
        'The tested algorithm versions had undergone previous development; family/seed variation is limited.',
        'A prospective simulator-in-the-loop implementation with a fixed total simulator budget is not yet tested.',
        'No statistical significance or general superiority over NSGA-II is claimed.']
    dest.mkdir(parents=True,exist_ok=True)
    write(dest/'replay_budget_scores.csv',rows)
    write(dest/'replay_budget_winners.csv',ranking)
    (dest/'replay_budget_report.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print('\n'.join(report))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('input',type=pathlib.Path)
    parser.add_argument('output',type=pathlib.Path)
    parser.add_argument('--phase',choices=['development','validation','scale50'],default='development')
    parser.add_argument('--source-run',type=int,default=41580592118)
    args=parser.parse_args()
    if args.phase=='development':
        workflows,seeds=('CyberShake_30','Montage_25','Sipht_30'),(1,2)
    elif args.phase=='validation':
        workflows,seeds=('Epigenomics_24','Inspiral_30'),(41,42,43)
    else:
        workflows,seeds=('CyberShake_50','Inspiral_50','Montage_50'),(44,45)
    analyze(args.input,args.output,workflows,seeds,args.source_run,args.phase)
