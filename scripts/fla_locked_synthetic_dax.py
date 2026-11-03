#!/usr/bin/env python3
"""Generate two LOCKED synthetic DAX topology families for held-aside screening tests.

This generator is deterministic with fixed topology seed 20261103. No simulated
optimization outcomes or feedback are read. Its output is intentionally a new,
synthetic DAG shape (not a claim of an unseen real scientific workflow).
Writes into checkout config/dax/ for this CI job only; master is untouched.
"""
import argparse
import hashlib
import pathlib
import random
import xml.etree.ElementTree as ET

SEED=20261103
COUNT=40
NS="http://pegasus.isi.edu/schema/DAX"
XSI="http://www.w3.org/2001/XMLSchema-instance"
ET.register_namespace("",NS)
ET.register_namespace("xsi",XSI)

def graph(which):
    rng=random.Random(SEED+ (41 if which=="SynthWide_40" else 83))
    edges=set()
    if which=="SynthWide_40":
        for layer in range(1,5):
            for k in range(8):
                dest=layer*8+k
                picks=rng.sample(range((layer-1)*8,layer*8),rng.choice((2,3)))
                for parent in picks:edges.add((parent,dest))
    elif which=="SynthDeep_40":
        # Four mostly serial pipelines, interleaved into ten levels.
        for layer in range(1,10):
            for lane in range(4):
                dest=layer*4+lane
                edges.add(((layer-1)*4+lane,dest))
                if layer>=2 and rng.random()<0.75:
                    other=(lane+rng.randrange(1,4))%4
                    edges.add(((layer-2)*4+other,dest))
    else:
        raise ValueError("Unknown synthetic topology: "+which)
    assert all(0<=a<b<COUNT for a,b in edges)
    assert len(edges)>=35
    return rng,sorted(edges)

def generate(which,path):
    rng,edges=graph(which)
    outputs={i:[] for i in range(COUNT)}
    inputs={i:[] for i in range(COUNT)}
    for parent,child in edges:
        name=f"edge_{parent:05d}_{child:05d}.bin"
        size=rng.randint(4_000_000,120_000_000)
        outputs[parent].append((name,size))
        inputs[child].append((name,size))
    root=ET.Element(f"{{{NS}}}adag",{
        f"{{{XSI}}}schemaLocation":f"{NS} http://pegasus.isi.edu/schema/dax-2.1.xsd",
        "version":"2.1","count":"1","index":"0","name":which,
        "jobCount":str(COUNT),"fileCount":"0",
        "childCount":str(len({b for _,b in edges}))})
    for i in range(COUNT):
        job=ET.SubElement(root,f"{{{NS}}}job",{
            "id":f"ID{i:05d}","namespace":which,"name":"synth_task",
            "version":"1.0","runtime":f"{rng.uniform(15,135):.3f}"})
        for filename,size in sorted(inputs[i]):
            ET.SubElement(job,f"{{{NS}}}uses",{"file":filename,"link":"input",
                "register":"true","transfer":"true","optional":"false",
                "type":"data","size":str(size)})
        for filename,size in sorted(outputs[i]):
            ET.SubElement(job,f"{{{NS}}}uses",{"file":filename,"link":"output",
                "register":"true","transfer":"true","optional":"false",
                "type":"data","size":str(size)})
    for child in sorted({b for _,b in edges}):
        childel=ET.SubElement(root,f"{{{NS}}}child",{"ref":f"ID{child:05d}"})
        for parent in sorted(a for a,b in edges if b==child):
            ET.SubElement(childel,f"{{{NS}}}parent",{"ref":f"ID{parent:05d}"})
    path.parent.mkdir(parents=True,exist_ok=True)
    data=b'<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding="utf-8")
    path.write_bytes(data)
    parsed=ET.parse(path).getroot()
    assert len(parsed.findall(f"{{{NS}}}job"))==40
    assert sum(len(x.findall(f"{{{NS}}}parent")) for x in parsed.findall(f"{{{NS}}}child"))==len(edges)
    expected_edges={(a,b) for a,b in edges}
    observed_edges=set()
    for el in parsed.findall(f"{{{NS}}}child"):
        b=int(el.attrib["ref"][2:])
        for par in el.findall(f"{{{NS}}}parent"):
            observed_edges.add((int(par.attrib["ref"][2:]),b))
    assert observed_edges==expected_edges
    digest=hashlib.sha256(data).hexdigest()
    print(f"SYNTHETIC_DAX_OK {which} jobs={COUNT} edges={len(edges)} sha256={digest}")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=pathlib.Path,default=pathlib.Path("config/dax"))
    args=p.parse_args()
    for name in ("SynthWide_40","SynthDeep_40"):
        generate(name,args.output_dir/(name+".xml"))

if __name__=="__main__":
    main()
