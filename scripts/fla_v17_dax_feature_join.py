#!/usr/bin/env python3
"""Read-only, leakage-aware descriptive join of source DAX features with v17 K16 outcomes.

NO model training, thresholds, causal effects or holdout claims.
"""
import csv
import pathlib
import statistics
import sys

DAGS = ("Epigenomics_46", "Inspiral_50", "CyberShake_100", "Sipht_100")
METRICS = ("do_vs_late_pct", "do_vs_v12_pct", "do_vs_nsga_pct")

def read(path):
    with pathlib.Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main(source_root, out_dir):
    root = pathlib.Path(source_root)
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True,exist_ok=True)
    structural = list(root.rglob("dax_structure.csv"))
    confirmation = list(root.rglob("v17_confirm_cases.csv"))
    if len(structural)!=1 or len(confirmation)!=1:
        raise AssertionError(("Missing or ambiguous original reports", structural, confirmation))
    dax_rows = read(structural[0])
    results = read(confirmation[0])
    assert len(dax_rows)==22 and len(results)==32,(len(dax_rows),len(results))
    lookup = {x["workflow"]:x for x in dax_rows}
    assert len(lookup)==22 and all(d in lookup for d in DAGS)
    primary = [x for x in results if float(x["ref_factor"])==1.5]
    secondary = [x for x in results if float(x["ref_factor"])==3.0]
    assert len(primary)==len(secondary)==16
    assert {r["workflow"] for r in primary}==set(DAGS)
    assert {int(r["seed"]) for r in primary}=={211,212}
    assert {r["speed"] for r in primary}=={"default","staggered"}
    joined = []
    for dag in DAGS:
        meta=lookup[dag]
        assert meta["declared_job_count_mismatch"]=="0"
        assert meta["declared_child_count_mismatch"]=="0"
        assert int(meta["invalid_dax_runtime_jobs"])==0
        assert int(meta["invalid_dax_file_size_references"])==0
        n=int(meta["task_count"])
        e=int(meta["edge_count"])
        roots=int(meta["roots"])
        indegree=int(meta["max_in_degree"])
        cp=float(meta["critical_path_runtime_dax"])
        total=float(meta["runtime_sum_dax"])
        parallelism=float(meta["work_span_parallelism_proxy"])
        fileMB=float(meta["declared_intertask_file_bytes"])/1e6
        assert n>0 and e>=0 and cp>0 and total>=cp and roots>0
        for speed in ("default","staggered"):
            p=[x for x in primary if x["workflow"]==dag and x["speed"]==speed]
            assert len(p)==2
            joined.append(dict(workflow=dag,speed=speed,actual_tasks=n,edges=e,roots=roots,
                root_fraction=roots/n,join_tasks=int(meta["join_tasks"]),
                max_in_degree=indegree,depth=int(meta["depth_levels"]),
                max_level_width=int(meta["max_level_width"]),
                critical_path_dax_runtime_proxy=cp,
                work_span_parallelism_proxy=parallelism,
                edge_file_volume_proxy_MiB=fileMB*1e6/(1024*1024),
                invalid_file_size_refs=0,invalid_runtime_jobs=0,
                do_vs_late_mean_pct=statistics.mean(float(x["do_vs_late_pct"]) for x in p),
                do_vs_v12_mean_pct=statistics.mean(float(x["do_vs_v12_pct"]) for x in p),
                do_vs_nsga_mean_pct=statistics.mean(float(x["do_vs_nsga_pct"]) for x in p),
                do_wins_late=sum(float(x["do_vs_late_pct"])>0 for x in p)))
    assert len(joined)==8
    with (out/"v17_dax_feature_join.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(joined[0]))
        writer.writeheader();writer.writerows(joined)
    lines=["# v17 K16 true simulator outcomes joined with independent DAX topology descriptors","",
        "Source artifacts: DAX structural audit run 41630971648 and frozen v17 new-size/seed confirmation run 41626382711. This file is a read-only descriptive join; NO additional fitness evaluations, simulations, feature fitting, tuning or thresholds.",
        "**Important:** Four DAX files in this confirmation, each with two VM speed regimes and two seeds. The eight table rows are NOT eight independent workflow families. All family/VM labels and outcomes were observed before this join. The join cannot validate a predictive policy.","",
        "| DAG (actual jobs) | VM | Edges | Depth | Root share | Max join fan-in | DAX work/span | DO random vs v12 | DO random vs late | DO random vs NSGA-II |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in joined:
        lines.append(f"| {x['workflow']} ({x['actual_tasks']}) | {x['speed']} | {x['edges']} | {x['depth']} | {x['root_fraction']:.3f} | {x['max_in_degree']} | {x['work_span_parallelism_proxy']:.3f} | {x['do_vs_v12_mean_pct']:+.4f}% | {x['do_vs_late_mean_pct']:+.4f}% | {x['do_vs_nsga_mean_pct']:+.4f}% |")
    lines+=["","## What this join does not establish",
       "DAX node runtimes are raw file metadata, not normalized by VM MIPS. The critical path and work/span ratio are structural/runtime proxies and exclude VM-dependent stage-in and cached file locality. Declared file-volume sums may count the same file on several DAG edges and are NOT observed inter-VM network consumption.",
       "There are four workflow families; DAG family, task scale, depth, root ratio and file characteristics are entangled. VM speed profiles add paired deployment conditions rather than independent structures. Cross-family feature correlations here would be exploratory and underpowered; no threshold, predictive accuracy or causal mechanism is claimed.",
       "The observed strong positive v17 results in staggered Sipht and losses on Epigenomics/Inspiral are inputs to this analysis, not a holdout for a newly chosen strategy. For publication, independently lock new DAG instances/generators and candidate policy BEFORE running true WorkflowSim evaluations and report all failure cases."]
    (out/"v17_dax_feature_join.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: script.py ORIGINAL_ACTION_ARTIFACT_ROOT OUTPUT_DIR")
    main(sys.argv[1],sys.argv[2])
