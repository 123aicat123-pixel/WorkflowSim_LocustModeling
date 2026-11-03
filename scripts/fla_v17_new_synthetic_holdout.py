#!/usr/bin/env python3
"""Frozen prospective synthetic structure-scale study, disconnected from observed v17 HV."""
import argparse
import hashlib
import pathlib
import random
import xml.etree.ElementTree as ET
from fla_dax_structure import inspect_dax

SEED=2026121501
SIZE=60
NS="http://pegasus.isi.edu/schema/DAX"
XSI="http://www.w3.org/2001/XMLSchema-instance"
NAMES=("SynthNewWide_60","SynthNewDeep_60")
ET.register_namespace("",NS)
ET.register_namespace("xsi",XSI)

def edges_for(name):
    if name not in NAMES:raise ValueError("Unsupported registered family")
    rng=random.Random(SEED+(317 if name==NAMES[0] else 719))
    graph=set()
    if name==NAMES[0]:
        # Six layers of ten tasks; fan-in 2..4 across adjacent levels.
        width,levels=10,6
        for level in range(1,levels):
            for k in range(width):
                b=level*width+k
                for a in rng.sample(range((level-1)*width,level*width),rng.randint(2,4)):
                    graph.add((a,b))
    else:
        # Twelve layers of five tasks, five long serial lanes with cross-lane edges.
        width,levels=5,12
        for level in range(1,levels):
            for k in range(width):
                b=level*width+k
                graph.add(((level-1)*width+k,b))
                if level>1 and rng.random()<.62:
                    other=(k+rng.randint(1,4))%width
                    graph.add(((level-2)*width+other,b))
    assert all(0<=a<b<SIZE for a,b in graph)
    return rng,sorted(graph)

def create(name,folder):
    rng,edges=edges_for(name)
    inputs={i:[] for i in range(SIZE)}
    outputs={i:[] for i in range(SIZE)}
    for a,b in edges:
        filename="dep_%05d_%05d.bin"%(a,b)
        size=rng.randint(2000000,40000000)
        outputs[a].append((filename,size))
        inputs[b].append((filename,size))
    ns=lambda key:"{%s}%s"%(NS,key)
    root=ET.Element(ns("adag"),{
        "{%s}schemaLocation"%XSI: NS+" http://pegasus.isi.edu/schema/dax-2.1.xsd",
        "version":"2.1","count":"1","index":"0","name":name,
        "jobCount":str(SIZE),"fileCount":"0",
        "childCount":str(len({b for a,b in edges}))})
    for i in range(SIZE):
        job=ET.SubElement(root,ns("job"),{
            "id":"ID%05d"%i,"namespace":name,"name":"synthetic_compute",
            "version":"1.0","runtime":"%.5f"%rng.uniform(20,130)})
        if not inputs[i]:
            inputs[i].append(("external_%05d.dat"%i,rng.randint(1000000,9000000)))
        for fn,sz in sorted(inputs[i]):
            ET.SubElement(job,ns("uses"),{
                "file":fn,"link":"input","register":"true","transfer":"true",
                "optional":"false","type":"data","size":str(sz)})
        for fn,sz in sorted(outputs[i]):
            ET.SubElement(job,ns("uses"),{
                "file":fn,"link":"output","register":"true","transfer":"true",
                "optional":"false","type":"data","size":str(sz)})
    for b in sorted({b for a,b in edges}):
        node=ET.SubElement(root,ns("child"),{"ref":"ID%05d"%b})
        for a in sorted(a for a,bb in edges if bb==b):
            ET.SubElement(node,ns("parent"),{"ref":"ID%05d"%a})
    xml=b'<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding="utf-8")
    path=folder/(name+".xml")
    folder.mkdir(parents=True,exist_ok=True)
    path.write_bytes(xml)
    details=inspect_dax(path)
    assert details["task_count"]==SIZE
    assert details["edge_count"]==len(edges)
    assert details["invalid_dax_runtime_jobs"]==0
    assert details["invalid_dax_file_size_references"]==0
    assert details["declared_job_count_mismatch"]==0
    assert details["declared_child_count_mismatch"]==0
    print("SYNTHETIC_HOLDOUT_OK %s n=%d edges=%d root=%d depth=%d sha256=%s"%(name,SIZE,len(edges),details["roots"],details["depth_levels"],hashlib.sha256(xml).hexdigest()))
    return details

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=pathlib.Path,default=pathlib.Path("config/dax"))
    a=p.parse_args()
    profiles=[create(name,a.output_dir) for name in NAMES]
    assert profiles[0]["depth_levels"]==6
    assert profiles[1]["depth_levels"]==12
    assert profiles[0]["roots"]==10
    assert profiles[1]["roots"]==5

if __name__=="__main__":main()
