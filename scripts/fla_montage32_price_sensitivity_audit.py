#!/usr/bin/env python3
"""Precommitted independent original-WorkflowSim Montage32 price sensitivity audit.
Real truth labels are for post-selection scoring only; all 32 maps are frozen.
"""
import csv
import itertools
import math
import pathlib
import sys
from fla_montage32_transfer_audit import (
    DAGS, PROFILES, POLICIES, SOURCE_COLUMNS, hv, dominates, planned_greedy, write, TOL
)

PRICES=("linear","convex")
BLOCKS=set(itertools.product(DAGS,PROFILES,PRICES))

def audit(root,out,expected_sha,protocol_sha):
    out.mkdir(parents=True,exist_ok=True)
    paths=sorted(root.glob("fla-price32-*/same_mapping_true_replays.csv"))
    assert len(paths)==8,("Expected 8 original physical source artifacts",len(paths))
    by_case={}
    for path in paths:
        folder=path.parent
        metadata={}
        for line in (folder/"block-id.txt").read_text().splitlines():
            k,v=line.split("=",1)
            assert k not in metadata
            metadata[k]=v
        case=(metadata["workflow"],metadata["vm_speed"],metadata["vm_price"])
        assert case in BLOCKS and case not in by_case
        assert folder.name==f"fla-price32-{case[0]}-{case[1]}-{case[2]}"
        assert metadata["seed"]=="1501" and metadata["policies"]=="32"
        assert (folder/"source-sha.txt").read_text().strip()==expected_sha
        assert (folder/"protocol-sha.txt").read_text().strip()==protocol_sha
        with path.open(newline="",encoding="utf-8") as f:
            reader=csv.DictReader(f)
            assert reader.fieldnames==list(SOURCE_COLUMNS),reader.fieldnames
            rows=list(reader)
        assert len(rows)==32
        assert {r["mapping_policy"] for r in rows}==set(POLICIES)
        assert len({r["task_vm_mapping"] for r in rows})==32
        assert all((r["workflow"],r["vm_profile"],r["seed"])==
                   (case[0],case[1],"1501") for r in rows)
        count=int(case[0].split("_")[-1])
        for r in rows:
            assert int(r["task_count"])==count
            mapping={}
            for entry in r["task_vm_mapping"].split("|"):
                task,vm=map(int,entry.split(":"))
                assert task not in mapping
                mapping[task]=vm
            assert set(mapping)==set(range(1,count+1))
            assert all(0<=vm<16 for vm in mapping.values())
            for key in SOURCE_COLUMNS[5:15]:
                val=float(r[key])
                assert math.isfinite(val) and (val>=0 if key.endswith("_mae") else val>0)
        log=(folder/"source.log").read_text(errors="replace")
        assert log.count("FROZEN_MAP_UNIVERSE_PASS")==32
        assert "PASS thirty-two disjoint algorithm-independent source genotypes" in log
        by_case[case]=rows
    assert set(by_case)==BLOCKS
    outputs=[]
    for case in sorted(BLOCKS):
        rows=by_case[case]
        names=[r["mapping_policy"] for r in rows]
        truth={r["mapping_policy"]:(float(r["actual_makespan"]),float(r["actual_cost"])) for r in rows}
        reference=tuple(1.5*max(p[i] for p in truth.values())+1e-6 for i in range(2))
        nd=sum(not any(dominates(other,pt) for other in truth.values() if other!=pt)
               for pt in truth.values())
        oracles={}
        optimal_counts={}
        for k in range(1,5):
            best=-1.
            tied=0
            for combo in itertools.combinations(truth.values(),k):
                score=hv(combo,reference)
                if score>best+TOL:
                    best=score
                    tied=1
                elif abs(score-best)<=TOL:
                    tied+=1
            oracles[k]=best
            optimal_counts[k]=tied
        selected={}
        for model in ("old","ready"):
            forecasts=[(float(r[f"{model}_planned_makespan"]),float(r[f"{model}_planned_cost"])) for r in rows]
            selected[model]=planned_greedy(forecasts,names,4)
        record=dict(workflow=case[0],vm_speed=case[1],vm_price=case[2],
                    source_sha=expected_sha,source_count=32,
                    true_nd_maps=nd,true_full_32_hv=hv(truth.values(),reference),
                    exact_k4_optimal_sets=optimal_counts[4],
                    old_order="|".join(selected["old"]),ready_order="|".join(selected["ready"]))
        for k in range(1,5):
            record[f"k{k}_oracle_hv"]=oracles[k]
            for model in ("old","ready"):
                val=hv([truth[x] for x in selected[model][:k]],reference)
                assert val<=oracles[k]+TOL
                record[f"{model}_k{k}_actual_hv"]=val
                record[f"{model}_k{k}_regret"]=max(0.,oracles[k]-val)
            record[f"k{k}_physical_sets_differ"]=int(
                set(selected["old"][:k])!=set(selected["ready"][:k]))
            record[f"k{k}_ready_minus_old_actual_hv"]=(
                record[f"ready_k{k}_actual_hv"]-record[f"old_k{k}_actual_hv"])
        outputs.append(record)
    write(out/"all_8_price_sensitivity_actual_decisions.csv",outputs)
    lines=[
        "# Precommitted Montage32 original-WorkflowSim price sensitivity",
        "",
        "**Exploratory deterministic physics sensitivity, NOT random-seed replication.**",
        "256 actual original WorkflowSim mappings; 8 blocks; 32 unique identical physical",
        "genotypes/block. Four fixed-source outcomes per model; exhaustive actual K1-K4",
        "oracles, predictions frozen independently of actual labels.",
        "",
        "| DAG | VM speed | Price | True ND | Different K4 | OLD K4 regret | READY K4 regret | READY − OLD true HV |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in outputs:
        lines.append(f"| {r['workflow']} | {r['vm_speed']} | {r['vm_price']} | "
          f"{r['true_nd_maps']} | {r['k4_physical_sets_differ']} | "
          f"{r['old_k4_regret']:.9f} | {r['ready_k4_regret']:.9f} | "
          f"{r['k4_ready_minus_old_actual_hv']:+.9f} |")
    lines+=["", "| K | Physical decision disagreements | Mean OLD regret | Mean READY regret | Mean READY − OLD true HV |",
            "|---:|---:|---:|---:|---:|"]
    for k in range(1,5):
        lines.append(f"| {k} | {sum(r[f'k{k}_physical_sets_differ'] for r in outputs)}/8 | "
           f"{sum(r[f'old_k{k}_regret'] for r in outputs)/8:.9f} | "
           f"{sum(r[f'ready_k{k}_regret'] for r in outputs)/8:.9f} | "
           f"{sum(r[f'k{k}_ready_minus_old_actual_hv'] for r in outputs)/8:+.9f} |")
    lines+=["","**No statistical significance or new optimizer benefit can be inferred.**",
            "Each block is a deterministic DAG/VM price/speed treatment, not a fresh random draw.",
            "Montage was previously investigated; count negative and tied outcomes openly.",
            "Actual oracle uses true labels only for retrospective diagnosis."]
    (out/"price_sensitivity_findings.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))

if __name__=="__main__":
    assert len(sys.argv)==5,"Usage: script.py source_root output_dir source_sha protocol_blob_sha"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3],sys.argv[4])
