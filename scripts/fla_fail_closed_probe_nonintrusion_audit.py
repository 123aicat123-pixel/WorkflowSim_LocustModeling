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

def audit(probed,control,k,pairs=2):
    assert pathlib.Path(str(probed)+"_fail_closed_probe.csv").is_file()
    assert not pathlib.Path(str(control)+"_fail_closed_probe.csv").exists()
    fa=keyed(load(probed,"_visited_fingerprints.csv"),["algorithm"])
    fb=keyed(load(control,"_visited_fingerprints.csv"),["algorithm"])
    assert len(fa)==2 and fa==fb, "Original ordered genotype histories diverged"
    # File existence alone was insufficient: an empty/truncated probe trace
    # must NEVER satisfy the noninterference gate.
    probe=load(probed,"_fail_closed_probe.csv")
    assert len(probe)==2*pairs, ("Wrong number of real optimizer probe rows",len(probe))
    assert set(row["algorithm"] for row in probe)==set(fa), "Missing/unknown probe solver"
    for alg in fa:
        records=[row for row in probe if row["algorithm"]==alg]
        assert len(records)==pairs, (alg,"Missing probe candidate pairs")
        assert [int(row["pair"]) for row in records]==list(range(1,pairs+1))
        physical=set()
        previous_old=previous_ready=-1
        for row in records:
            assert row["first_assignment"] and row["second_assignment"]
            assert row["first_assignment"]!=row["second_assignment"]
            physical.add(row["first_assignment"])
            physical.add(row["second_assignment"])
            assert row["decision"] in ("READY_ESTIMATES_AVAILABLE","KEEP_BOTH"), (
                "Uncalibrated diagnostic may not certify actual Pareto dominance",alg)
            assert all(near(row[c],row[c]) and float(row[c])>0 for c in
                ("old_first_m","old_first_c","old_second_m","old_second_c"))
            current_old=int(row["old_calls"])
            current_ready=int(row["ready_calls"])
            assert current_old>=previous_old and current_ready>=previous_ready
            assert current_old<=2*(int(row["pair"]))
            assert current_ready<=int(row["ready_budget"])
            previous_old,previous_ready=current_old,current_ready
        assert len(physical)==2*pairs, (alg,"Duplicate physical probe assignments")
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
    assert len(sys.argv) in (4,5), "USAGE: script.py PROBED_PREFIX CONTROL_PREFIX K [PAIRS]"
    audit(sys.argv[1],sys.argv[2],int(sys.argv[3]),
          int(sys.argv[4]) if len(sys.argv)==5 else 2)
