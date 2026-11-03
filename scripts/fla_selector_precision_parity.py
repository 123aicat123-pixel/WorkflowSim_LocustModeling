#!/usr/bin/env python3
"""Cross-check exact K-replay selection between the Python research oracle and Java.
No WorkflowSim simulator outputs enter selection. Deterministic stress fixtures only.
"""
import csv
import importlib.util
import pathlib
import random
import sys

def import_oracle():
    path = pathlib.Path(__file__).with_name("fla_replay_budget_audit.py")
    spec = importlib.util.spec_from_file_location("fla_replay_budget_audit_parity", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def cases():
    rng = random.Random(20261103)
    out = []
    for i in range(1, 91):
        out.append(("smooth", i, 40 + i * 0.67 + rng.random() * 0.2,
                    160 - i * 0.83 + rng.random() * 0.2))
        out.append(("ties", i, 50 + (i % 9) * 2., 120 - (i % 9) * 3.))
        out.append(("near-ties", i, 70 + (i % 30) * 1.e-12,
                    120 - (i % 30) * 1.e-12))
        out.append(("skewed", i, 20 + i * 3. + rng.random() * 2.,
                    900 / (1 + i * 0.24) + rng.random() * 3.))
    return out

def generate(path):
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "id", "m", "c"])
        for case, ident, m, c in cases():
            w.writerow((case, ident, format(m, ".17g"), format(c, ".17g")))
    print("PASS fixture created:", path)

def verify(fixture, output):
    oracle = import_oracle()
    bycase = {}
    with fixture.open(newline="") as f:
        for row in csv.DictReader(f):
            bycase.setdefault(row["case"], []).append(
                oracle.Planned("1:" + row["id"], float(row["m"]), float(row["c"])))
    observed = {}
    for line in output.read_text().splitlines():
        if not (line.startswith("PARITY|") or line.startswith("PARITYSWEEP|") or line.startswith("PARITYBAND3|")):
            continue
        family, case, count, ordered = line.split("|", 3)
        policy = {"PARITY":"pareto-cover","PARITYSWEEP":"scalar-sweep","PARITYBAND3":"extreme-band3"}[family]
        key = (case, int(count), policy)
        assert key not in observed, key
        observed[key] = ordered.split(",")
    expected_keys = {(case, k, policy) for case in bycase
                     for k in (8, 16, 24, 32)
                     for policy in ("pareto-cover", "scalar-sweep", "extreme-band3")}
    assert set(observed) == expected_keys, (set(observed), expected_keys)
    diffs = []
    for (case, k, policy), actual in sorted(observed.items()):
        selected = oracle.choose(bycase[case], ("fixture", 1, case), policy, k, 0)
        expected = [str(int(x.mapping.split(":")[1])) for x in selected]
        if expected != actual:
            diffs.append((case, k, policy, expected, actual))
    if diffs:
        print("FAIL Python-Java selection order differs in", len(diffs), "case/budget configurations")
        for case, k, policy, expected, actual in diffs:
            print("MISMATCH", case, k, policy, "python=", expected, "java=", actual)
        raise SystemExit(1)
    print("PASS Python and Java exact selected-genotype ID/order parity:",
          len(observed), "policy/fixture/budget configurations across", len(bycase), "fixtures")

if __name__ == "__main__":
    assert len(sys.argv) >= 3 and sys.argv[1] in ("generate", "verify"), (
        "usage: fla_selector_precision_parity.py generate FILE | verify FIXTURE JAVA_OUTPUT")
    if sys.argv[1] == "generate":
        generate(pathlib.Path(sys.argv[2]))
    else:
        assert len(sys.argv) == 4
        verify(pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]))
