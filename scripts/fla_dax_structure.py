#!/usr/bin/env python3
"""Deterministic, simulator-free structural audit of existing Pegasus DAX XML.

These are DAX *metadata* proxies, not measured WorkflowSim communications,
processor-weighted critical paths, or learned performance predictors.
"""
import argparse
import csv
import hashlib
import heapq
import math
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

def local(tag):
    return tag.rsplit("}", 1)[-1]

def children(element, tag):
    return [x for x in element if local(x.tag) == tag]

def nonnegative_number(value, label):
    try:
        n = float(value)
    except (ValueError, TypeError):
        raise ValueError("Invalid numeric " + label + ": " + str(value)) from None
    if not math.isfinite(n) or n < 0:
        raise ValueError("Nonfinite/negative " + label)
    return n

def inspect_dax(path):
    path = Path(path)
    blob = path.read_bytes()
    root = ET.fromstring(blob)
    if local(root.tag) != "adag":
        raise ValueError("Not a Pegasus DAX adag: " + str(path))
    nodes = children(root, "job")
    n = len(nodes)
    if n == 0:
        raise ValueError("No jobs in " + str(path))
    durations = {}
    invalid_runtimes = 0
    producers, consumers = {}, {}
    bad_links = 0
    invalid_file_sizes = 0
    for node in nodes:
        identifier = node.get("id")
        if not identifier or identifier in durations:
            raise ValueError("Missing or duplicate job id: " + str(identifier))
        try:
            durations[identifier] = nonnegative_number(node.get("runtime"), "job runtime")
        except ValueError:
            # Preserve topology; suppress EVERY derived runtime/critical-path
            # statistic for the entire DAX when any runtime is invalid.
            durations[identifier] = 0.
            invalid_runtimes += 1
        inputs, outputs = {}, {}
        for f in children(node, "uses"):
            name, link = f.get("file"), f.get("link")
            if not name:
                raise ValueError("Missing filename in job " + identifier)
            # Some Pegasus DAX sets (e.g. Epigenomics_997) contain
            # negative file sizes. They are invalid bytes, NOT negative
            # communication. Preserve DAG topology; exclude invalid sizes
            # explicitly from any logical-byte aggregation.
            try:
                size = nonnegative_number(f.get("size"), "file bytes")
            except ValueError:
                size = None
                invalid_file_sizes += 1
            if link == "input":
                if name in inputs and inputs[name] != size:
                    raise ValueError("Conflicting input sizes")
                inputs[name] = size
            elif link == "output":
                if name in outputs and outputs[name] != size:
                    raise ValueError("Conflicting output sizes")
                outputs[name] = size
            else:
                bad_links += 1
        producers[identifier] = outputs
        consumers[identifier] = inputs
    if bad_links:
        raise ValueError("Unsupported DAX file-link types: " + str(bad_links))

    edge_set = set()
    child_blocks = children(root, "child")
    for item in child_blocks:
        target = item.get("ref")
        if target not in durations:
            raise ValueError("Child ref missing from DAG jobs: " + str(target))
        for parent in children(item, "parent"):
            source = parent.get("ref")
            if source not in durations:
                raise ValueError("Parent ref missing from DAG jobs: " + str(source))
            if source == target:
                raise ValueError("Self-dependency")
            edge = (source, target)
            if edge in edge_set:
                raise ValueError("Duplicated dependency edge: " + str(edge))
            edge_set.add(edge)
    nxt = {i: [] for i in durations}
    indegree = {i: 0 for i in durations}
    for a, b in sorted(edge_set):
        nxt[a].append(b)
        indegree[b] += 1
    roots = sum(v == 0 for v in indegree.values())
    sinks = sum(len(v) == 0 for v in nxt.values())

    queue = [i for i, d in indegree.items() if d == 0]
    heapq.heapify(queue)
    pending = dict(indegree)
    depth = {i: 0 for i in durations}
    weighted_end = {i: durations[i] for i in durations}
    order = []
    while queue:
        a = heapq.heappop(queue)
        order.append(a)
        for b in nxt[a]:
            depth[b] = max(depth[b], depth[a] + 1)
            weighted_end[b] = max(weighted_end[b], weighted_end[a] + durations[b])
            pending[b] -= 1
            if pending[b] == 0:
                heapq.heappush(queue, b)
    if len(order) != n:
        raise ValueError("Cyclic DAX dependency graph")
    layer_width = max(Counter(depth.values()).values())
    runtime_sum = sum(durations.values())
    critical_runtime = max(weighted_end.values())
    if critical_runtime < 0 or critical_runtime > runtime_sum + 1e-8 * max(1, runtime_sum):
        raise AssertionError("Invalid weighted critical path")
    runtime_valid = invalid_runtimes == 0

    matched_edges = 0
    logical_bytes = 0.
    mismatched_bytes = 0
    invalid_edge_file_sizes = 0
    for a, b in edge_set:
        common = producers[a].keys() & consumers[b].keys()
        if common:
            matched_edges += 1
            for file in common:
                producer_size=producers[a][file]
                consumer_size=consumers[b][file]
                if producer_size is None or consumer_size is None:
                    invalid_edge_file_sizes += 1
                    continue
                logical_bytes += producer_size
                if producer_size != consumer_size:
                    mismatched_bytes += 1

    declared_jobs = root.get("jobCount")
    declared_children = root.get("childCount")
    # Historical DAX files can carry stale metadata (notably HEFT_paper.xml).
    # Record the disagreement explicitly, rather than assuming the header is
    # authoritative or fabricating missing jobs.
    job_count_mismatch=int(declared_jobs is not None and (
        not declared_jobs.isdigit() or int(declared_jobs)!=n))
    child_count_mismatch=int(declared_children is not None and (
        not declared_children.isdigit() or int(declared_children)!=len(child_blocks)))
    return dict(
        workflow=path.stem, family=path.stem.split("_")[0],
        dax_sha256=hashlib.sha256(blob).hexdigest(),
        declared_job_count=declared_jobs or "", task_count=n,
        declared_job_count_mismatch=job_count_mismatch,
        declared_child_blocks=declared_children or "", child_block_count=len(child_blocks),
        declared_child_count_mismatch=child_count_mismatch,
        edge_count=len(edge_set), roots=roots, sinks=sinks,
        edge_density=len(edge_set) / (n * (n - 1) / 2) if n > 1 else 0.,
        max_in_degree=max(indegree.values()), max_out_degree=max(map(len, nxt.values())),
        join_tasks=sum(d > 1 for d in indegree.values()),
        fork_tasks=sum(len(xs) > 1 for xs in nxt.values()),
        max_level_width=layer_width, depth_levels=max(depth.values())+1,
        invalid_dax_runtime_jobs=invalid_runtimes,
        runtime_sum_dax=runtime_sum if runtime_valid else "",
        runtime_mean_dax=runtime_sum/n if runtime_valid else "",
        critical_path_runtime_dax=critical_runtime if runtime_valid else "",
        critical_runtime_share=critical_runtime/runtime_sum if runtime_valid and runtime_sum > 0 else "",
        work_span_parallelism_proxy=runtime_sum/critical_runtime if runtime_valid and critical_runtime > 0 else "",
        edges_with_common_file=matched_edges,
        edges_without_common_file=len(edge_set)-matched_edges,
        declared_intertask_file_bytes=logical_bytes,
        invalid_dax_file_size_references=invalid_file_sizes,
        skipped_invalid_edge_file_size_pairs=invalid_edge_file_sizes,
        parent_child_file_size_disagreements=mismatched_bytes,
        input_file_references=sum(map(len, consumers.values())),
        output_file_references=sum(map(len, producers.values()))
    )

def inspect_paths(paths):
    records = [inspect_dax(p) for p in sorted(paths, key=lambda p: Path(p).name)]
    if not records:
        raise ValueError("No DAX paths provided")
    if len({r["workflow"] for r in records}) != len(records):
        raise ValueError("Ambiguous duplicate workflow names")
    return records

def save_csv(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dax-dir", default="config/dax")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workflows", nargs="*", default=None,
                    help="Without this argument audit all *.xml DAX files.")
    args = ap.parse_args()
    base = Path(args.dax_dir)
    if args.workflows:
        paths = [base / (name if name.endswith(".xml") else name+".xml") for name in args.workflows]
    else:
        paths = list(base.glob("*.xml"))
    records = inspect_paths(paths)
    save_csv(args.out, records)
    for r in records:
        cp=r["critical_path_runtime_dax"]
        print("%s parsed_jobs=%d declared_jobs=%s jobcount_mismatch=%d edges=%d depth=%d roots=%d CP_DAX=%s bad_runtimes=%d bad_file_sizes=%d"
              % (r["workflow"],r["task_count"],r["declared_job_count"],
                 r["declared_job_count_mismatch"],r["edge_count"],r["depth_levels"],r["roots"],
                 ("%.4f" % cp) if cp != "" else "UNAVAILABLE",
                 r["invalid_dax_runtime_jobs"],r["invalid_dax_file_size_references"]))
    print("PASS DAX structural audit: %d workflows, acyclic, validated job and child counts" % len(records))

if __name__ == "__main__":
    main()
