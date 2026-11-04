#!/usr/bin/env python3
"""Independent read-only A/B audit: diagnostic enabled vs disabled."""
import csv
import math
import pathlib
import sys

def load(prefix, suffix):
    with open(str(prefix)+suffix, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def keyed(rows, keys):
    result = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        assert key not in result, ("Duplicate key", key)
        result[key] = row
    return result

def near(a,b):
    x,y=float(a),float(b)
    return math.isfinite(x) and math.isfinite(y) and abs(x-y)<=1e-9*max(1,abs(x),abs(y))

def audit(probed,control,k):
    assert pathlib.Path(str(probed)+"_fail_closed_probe.csv").is_file()
    assert not pathlib.Path(str(control)+"_fail_closed_probe.csv").exists()
    fa=keyed(load(probed,"_visited_fingerprints.csv"),["algorithm"])
    fb=keyed(load(control,"_visited_fingerprints.csv"),["algorithm"])
    assert len(fa)==2 and fa==fb, "Original ordered genotype histories diverged"
    sa=keyed(load(probed,"_summary.csv"),["algorithm"])
    sb=keyed(load(control,"_summary.csv"),["algorithm"])
    assert sa.keys()==sb.keys()==fa.keys()
    ignore={"search_ms","selection_ms","replay_ms","search_selection_replay_ms"}
    for alg in sa:
        for field in sa[alg]:
            if field in ignore:
                continue
            x,y=sa[alg][field],sb[alg][field]
            if field in ("sim_hv","planned_hv"):
                assert near(x,y),(alg,field,x,y)
            else:
                assert x==y,(alg,field,x,y)
        assert int(sa[alg]["replayed"])==k
    ra=keyed(load(probed,"_replays.csv"),["algorithm","candidate_index"])
    rb=keyed(load(control,"_replays.csv"),["algorithm","candidate_index"])
    assert len(ra)==2*k and ra.keys()==rb.keys()
    for key in ra:
        for field in ra[key]:
            x,y=ra[key][field],rb[key][field]
            if field in ("planned_makespan","planned_cost",
                         "independent_planned_makespan","independent_planned_cost",
                         "sim_makespan","sim_cost"):
                assert near(x,y),(key,field,x,y)
            else:
                assert x==y,(key,field,x,y)
    assert pathlib.Path(str(probed)+"_budget_protocol.txt").read_text()==pathlib.Path(str(control)+"_budget_protocol.txt").read_text()
    print("PASS paired FLA/NSGA nonintrusion: identical histories, exact physical replay maps and true K objectives")

if __name__=="__main__":
    assert len(sys.argv)==4, "USAGE: script.py PROBED_PREFIX CONTROL_PREFIX K"
    audit(sys.argv[1],sys.argv[2],int(sys.argv[3]))
