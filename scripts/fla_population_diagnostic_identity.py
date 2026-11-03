#!/usr/bin/env python3
"""Strict zero-effect verification for passive selected breeding-population traces."""
import csv, pathlib, sys, math, json

def rows(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))

def main(root):
    for variant in ("v12-hvbandit","v15-timelinegate"):
        off=root/("off-"+variant)
        on=root/("on-"+variant)
        for suffix in ("_visited_fingerprints.csv","_summary.csv","_replays.csv","_budget_protocol.txt"):
            assert pathlib.Path(str(off)+suffix).is_file(),(variant,suffix,"off missing")
            assert pathlib.Path(str(on)+suffix).is_file(),(variant,suffix,"on missing")
        foff=rows(pathlib.Path(str(off)+"_visited_fingerprints.csv"))
        fon=rows(pathlib.Path(str(on)+"_visited_fingerprints.csv"))
        assert len(foff)==len(fon)==1
        assert foff==fon,("EVALUATED SEARCH HISTORY CHANGED",variant,foff,fon)
        roff=rows(pathlib.Path(str(off)+"_replays.csv"))
        ron=rows(pathlib.Path(str(on)+"_replays.csv"))
        assert len(roff)==len(ron)==16 and roff==ron,("K16 SIMULATOR OUTCOME CHANGED",variant)
        soff=rows(pathlib.Path(str(off)+"_summary.csv"))[0]
        son=rows(pathlib.Path(str(on)+"_summary.csv"))[0]
        for k in ("workflow","algorithm","seed","population","generations","evaluations",
                  "source_archive","distinct_planned_nondominated","replayed",
                  "sim_nondominated","captured_evaluations","distinct_observed",
                  "sim_hv","planned_hv","sim_ref_m","sim_ref_c","plan_ref_m","plan_ref_c",
                  "actual_generations"):
            assert soff[k]==son[k],("SUMMARY DIFFERENCE",variant,k,soff[k],son[k])
        assert int(son["evaluations"])==3030 and int(son["replayed"])==16
        ontrace=rows(pathlib.Path(str(on)+"_population_diagnostics.csv"))
        assert len(ontrace)==101,(variant,len(ontrace))
        assert [int(float(x["generation"])) for x in ontrace]==list(range(101))
        assert [int(float(x["objective_evaluations"])) for x in ontrace]==[30*(i+1) for i in range(101)]
        assert all(int(float(x["selected_slots"]))==30 for x in ontrace)
        assert all(int(float(x["selected_unique"]))+int(float(x["selected_duplicate_slots"]))==30 for x in ontrace)
        assert all(0<=float(x["pairwise_hamming_all"])<=1 for x in ontrace)
        assert int(float(ontrace[0]["phase"]))==-1
        rejected=sum(int(float(x["local_gate_rejections"])) for x in ontrace[1:])
        if variant=="v12-hvbandit":assert rejected==0
        else:assert rejected>0
        assert not pathlib.Path(str(off)+"_population_diagnostics.csv").exists()
        print(f"PASS {variant}: full ordered history SHA and all 16 simulator rows identical ON/OFF, 3030 objective calls, 101 valid selected-generation snapshots, rejected={rejected}")
    (root/"identity_pass.txt").write_text("PASS exact passive population diagnostics identity across v12 and v15\n")

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: fla_population_diagnostic_identity.py directory")
    main(pathlib.Path(sys.argv[1]))
