#!/usr/bin/env python3
"""New precommitted SYNTHETIC 40-task fork/join bottleneck DAX, separate from prior wide/deep graphs."""
import argparse
import hashlib
import pathlib
import random
import xml.etree.ElementTree as ET

SEED=2026110317
NAME="SynthBottleneck_40"
N=40
NS="http://pegasus.isi.edu/schema/DAX"
XSI="http://www.w3.org/2001/XMLSchema-instance"
ET.register_namespace("",NS)
ET.register_namespace("xsi",XSI)

def build(path):
    rng=random.Random(SEED)
    edges=set()
    # Two concentrated all-to-one joins, alternate fan-out, and a serial tail.
    for i in range(8):
        edges.add((i,8+i))
    for i in range(8,16):
        edges.add((i,16))
    for i in range(17,25):
        edges.add((16,i))
        edges.add((8+(i-17),i))
    for i in range(17,25):
        edges.add((i,25))
    for i in range(26,34):
        edges.add((25,i))
    for i in range(34,40):
        edges.add((26+(i-34),i))
        edges.add((27+(i-34),i))
    for i in range(35,40):
        edges.add((i-1,i))
    assert all(0<=a<b<N for a,b in edges)
    inputs={i:[] for i in range(N)}
    outputs={i:[] for i in range(N)}
    for a,b in sorted(edges):
        filename=f"edge_{a:05d}_{b:05d}.bin"
        size=rng.randint(2_000_000,100_000_000)
        outputs[a].append((filename,size))
        inputs[b].append((filename,size))
    root=ET.Element(f"{{{NS}}}adag",{
        f"{{{XSI}}}schemaLocation":f"{NS} http://pegasus.isi.edu/schema/dax-2.1.xsd",
        "version":"2.1","count":"1","index":"0","name":NAME,
        "jobCount":str(N),"fileCount":"0",
        "childCount":str(len({b for a,b in edges}))})
    for i in range(N):
        duration=rng.uniform(20,120)
        if i in (16,25):duration=rng.uniform(160,280)
        j=ET.SubElement(root,f"{{{NS}}}job",{
            "id":f"ID{i:05d}","namespace":NAME,"name":"synth_task",
            "version":"1.0","runtime":f"{duration:.3f}"})
        for name,size in inputs[i]:
            ET.SubElement(j,f"{{{NS}}}uses",{"file":name,"link":"input",
                "register":"true","transfer":"true","optional":"false",
                "type":"data","size":str(size)})
        for name,size in outputs[i]:
            ET.SubElement(j,f"{{{NS}}}uses",{"file":name,"link":"output",
                "register":"true","transfer":"true","optional":"false",
                "type":"data","size":str(size)})
    for b in sorted({b for a,b in edges}):
        child=ET.SubElement(root,f"{{{NS}}}child",{"ref":f"ID{b:05d}"})
        for a in sorted(a for a,c in edges if c==b):
            ET.SubElement(child,f"{{{NS}}}parent",{"ref":f"ID{a:05d}"})
    data=b'<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding="utf-8")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data)
    check=ET.parse(path).getroot()
    assert len(check.findall(f"{{{NS}}}job"))==N
    assert sum(len(child.findall(f"{{{NS}}}parent")) for child in check.findall(f"{{{NS}}}child"))==len(edges)
    print(f"RELIABILITY_HOLDOUT_DAX_OK {NAME} jobs={N} edges={len(edges)} sha256={hashlib.sha256(data).hexdigest()}")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",type=pathlib.Path,default=pathlib.Path("config/dax"))
    args=parser.parse_args()
    build(args.output_dir/(NAME+".xml"))
