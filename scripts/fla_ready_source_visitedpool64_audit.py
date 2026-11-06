#!/usr/bin/env python3
"""READY-fitness source-mode read-only companion for identical same64 auditor."""
import pathlib
import sys
from fla_visitedpool64_dual_k8_audit import audit
if __name__=="__main__":
    assert len(sys.argv)==5,"usage: script.py ORIGINAL_ARTIFACTS OUT SOURCE_SHA PROTOCOL_BLOB_SHA"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3],sys.argv[4],
          source_kind="READY")
