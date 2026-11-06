#!/usr/bin/env python3
"""Fail-closed SHA256 parity of complete FLA histories and ORIGINAL 64 mappings.

Zero new simulator truth. Full history overlap is a sampled-source mechanism
diagnostic, not an improved algorithm result or fresh SCI confirmation.
"""
import csv
import hashlib
import itertools
import math
import pathlib
import statistics
import sys
from fla_montage_fullsearch_ready_transfer_audit import write

DAGS=("Montage_50","Montage_100")
SPEEDS=("default","staggered")
SEEDS=("1701","1702")
SOURCES=("old","ready")
KNOWN_SHA={
    "old":"7a0dba36a84e367be45c891eedd44dd629083455",
    "ready":"1209a4ba790ba4d9e81a15bd9edaef1a05688b49"
}
KEYS=set(itertools.product(DAGS,SPEEDS,SEEDS))
HEX=set("0123456789abcdef")

def read(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def meta(path):
    result={}
    for line in path.read_text().splitlines():
        key,value=line.split("=",1)
        assert key not in result
        result[key]=value
    return result

def sha_map(mapping):
    pairs={}
    for x in mapping.split("|"):
        task,vm=map(int,x.split(":"))
        assert task not in pairs
        pairs[task]=vm
    canonical="|".join(f"{k}:{pairs[k]}" for k in sorted(pairs))
    assert canonical==mapping
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def audit(history_root,original_root,out,current_source_sha,history_protocol_sha):
    out.mkdir(parents=True,exist_ok=True)
    history={}
    sample={}
    originals={}
    for source in SOURCES:
        for key in sorted(KEYS):
            dag,speed,seed=key
            h=history_root/f"history-{source}-{dag}-{speed}-s{seed}"
            o=original_root/source/f"visitedpool64-{dag}-{speed}-s{seed}"
            assert h.is_dir() and o.is_dir(),("Missing required original/history artifact",h,o)
            assert meta(h/"block-id.txt")==dict(source=source,workflow=dag,speed=speed,seed=seed)
            assert (h/"source-sha.txt").read_text().strip()==current_source_sha
            assert (h/"protocol-sha.txt").read_text().strip()==history_protocol_sha
            assert (o/"source-sha.txt").read_text().strip()==KNOWN_SHA[source]
            log=(h/"experiment.log").read_text(errors="replace")
            assert log.count("HISTORY_ONLY_PASS")==1
            assert "simulator_replays=0" in log and "evaluations=3030" in log
            assert not (h/"research_pool64_true_replays.csv").exists()
            unique=read(h/"research_pool64_entire_visit_hashes.csv")
            chosen=read(h/"research_pool64_original_sample_hashes.csv")
            old=read(o/"research_pool64_frozen_predictions.csv")
            true=read(o/"research_pool64_true_replays.csv")
            assert len(old)==len(true)==len(chosen)==64
            assert len(unique)>=64 and len(unique)<=3030
            assert len({r["mapping_sha256"] for r in unique})==len(unique)
            assert [int(r["unique_visit_index"]) for r in unique]==list(range(1,len(unique)+1))
            assert [int(r["pool_index"]) for r in chosen]==list(range(1,65))
            for i in range(64):
                r=old[i]
                assert (r["workflow"],r["seed"],r["pool_index"])==(dag,seed,str(i+1))
                assert (true[i]["workflow"],true[i]["seed"],true[i]["pool_index"],true[i]["mapping"])==(
                         dag,seed,str(i+1),r["mapping"])
                expected=sha_map(r["mapping"])
                assert chosen[i]["mapping_sha256"]==expected,(
                  "REEXECUTION DOES NOT REPRODUCE ORIGINAL CHOSEN PHYSICAL MAP",source,key,i+1)
                assert (chosen[i]["workflow"],chosen[i]["seed"])==(dag,seed)
                assert chosen[i]["mapping_sha256"] in {x["mapping_sha256"] for x in unique}
            assert len({r["mapping_sha256"] for r in chosen})==64
            assert all(r["workflow"]==dag and r["seed"]==seed for r in unique)
            assert all(len(r["mapping_sha256"])==64 and
                       set(r["mapping_sha256"])<=HEX for r in unique)
            history[source,key]={r["mapping_sha256"] for r in unique}
            sample[source,key]={r["mapping_sha256"] for r in chosen}
            originals[source,key]=dict(full_unique_count=len(unique),source_sha=KNOWN_SHA[source])
    assert len(history)==len(sample)==len(originals)==16
    data=[]
    for key in sorted(KEYS):
        fullold=history["old",key]
        fullready=history["ready",key]
        sampleold=sample["old",key]
        sampleready=sample["ready",key]
        common_full=len(fullold&fullready)
        common_sample=len(sampleold&sampleready)
        assert len(sampleold)==len(sampleready)==64
        assert common_sample<=common_full
        data.append(dict(workflow=key[0],speed=key[1],seed=key[2],
          old_full_visited=len(fullold),ready_full_visited=len(fullready),
          full_common=common_full,full_union=len(fullold|fullready),
          full_jaccard=common_full/len(fullold|fullready),
          old_sample=64,ready_sample=64,
          sample_common=common_sample,sample_union=len(sampleold|sampleready),
          sample_jaccard=common_sample/len(sampleold|sampleready),
          old_sample_pct=len(sampleold)/len(fullold),
          ready_sample_pct=len(sampleready)/len(fullready),
          source_history_sha=current_source_sha))
    assert len(data)==8
    write(out/"all_8_full_history_vs_original_pool64_fingerprint_overlap.csv",data)
    report=[
      "# Whole unique FLA-visited mapping histories: exact original 64-map parity",
      "",
      "**Sixteen real 3030-visit FLA-v12 search-history re-executions,",
      "ZERO additional physical WorkflowSim truth calls.**",
      "All sixteen original frozen sample sequences reproduced byte-exactly",
      "after SHA-256 canonical mapping hashing: source identity gate PASS.",
      "",
      "| DAG | Speed | Seed | OLD full unique visited | READY full unique visited | Entire-history common | Entire-history Jaccard | Sample-64 common |",
      "|---|---|---:|---:|---:|---:|---:|---:|"
    ]
    for r in data:
        report.append(f"| {r['workflow']} | {r['speed']} | {r['seed']} | "
                      f"{r['old_full_visited']} | {r['ready_full_visited']} | "
                      f"{r['full_common']} | {r['full_jaccard']:.6f} | "
                      f"{r['sample_common']} |")
    report+=["",f"- Mean entire-history Jaccard: **{statistics.mean(r['full_jaccard'] for r in data):.6f}**.",
        f"- Mean count of common unique genotypes: **{statistics.mean(r['full_common'] for r in data):.2f}**.",
        f"- Full-histories with 0 shared: **{sum(r['full_common']==0 for r in data)}/8**.",
        f"- Frozen sample-pool pairs with 0 shared: **{sum(r['sample_common']==0 for r in data)}/8**.",
        "",
        "The 64-sample overlap by itself cannot infer the full visited search",
        "distribution. This read-only re-execution reconstructs that denominator.",
        "Entire-history overlap reflects identical physical genotype encountered",
        "at any time; it does not imply equality of objective scores, rank or",
        "generation trajectory. Two sources use different objective decoders.",
        "All original 1024 real simulator outcomes remain unchanged; this new",
        "experiment introduces NO additional true performance labels.",
        "No statistical generalization, new FLA operator or SCI superiority claim."]
    (out/"full_history_fingerprint_findings.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    assert len(sys.argv)==6,"usage: script.py HISTORY_ROOT ORIGINAL_ROOT OUT HISTORY_SOURCE_SHA PROTOCOL_BLOB_SHA"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),
          pathlib.Path(sys.argv[3]),sys.argv[4],sys.argv[5])
