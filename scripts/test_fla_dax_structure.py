#!/usr/bin/env python3
"""Exact DAX parser oracle independent of Java, no third-party dependencies."""
import tempfile
import unittest
from pathlib import Path
from fla_dax_structure import inspect_dax

FIXTURE="""<?xml version="1.0"?>
<adag xmlns="http://pegasus.isi.edu/schema/DAX" jobCount="3" childCount="2">
 <job id="A" runtime="2">
  <uses file="p.bin" link="output" size="100"/>
 </job>
 <job id="B" runtime="3">
  <uses file="p.bin" link="input" size="100"/>
 </job>
 <job id="C" runtime="4">
  <uses file="external.bin" link="input" size="10"/>
 </job>
 <child ref="B"><parent ref="A"/></child>
 <child ref="C"><parent ref="A"/></child>
</adag>
"""

class StructureTests(unittest.TestCase):
    def run_dax(self, xml, name="Synthetic_2.xml"):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / name
            p.write_text(xml, encoding="utf-8")
            return inspect_dax(p)

    def test_fork_and_metadata(self):
        x = self.run_dax(FIXTURE)
        self.assertEqual(x["workflow"], "Synthetic_2")
        self.assertEqual(x["task_count"], 3) # filename _2 MUST NOT determine actual count
        self.assertEqual(x["edge_count"], 2)
        self.assertEqual(x["roots"], 1)
        self.assertEqual(x["sinks"], 2)
        self.assertEqual(x["depth_levels"], 2)
        self.assertEqual(x["max_level_width"], 2)
        self.assertEqual(x["max_out_degree"], 2)
        self.assertEqual(x["fork_tasks"], 1)
        self.assertEqual(x["join_tasks"], 0)
        self.assertEqual(x["runtime_sum_dax"], 9)
        self.assertEqual(x["critical_path_runtime_dax"], 6)
        self.assertEqual(x["declared_intertask_file_bytes"], 100)
        self.assertEqual(x["edges_with_common_file"], 1)
        self.assertEqual(x["edges_without_common_file"], 1)
        self.assertEqual(x["parent_child_file_size_disagreements"], 0)

    def test_count_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, "jobCount"):
            self.run_dax(FIXTURE.replace('jobCount="3"', 'jobCount="2"'))

    def test_cycle_fails(self):
        x = FIXTURE.replace('childCount="2"', 'childCount="3"')
        x = x.replace("</adag>", '<child ref="A"><parent ref="B"/></child></adag>')
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            self.run_dax(x)

    def test_bad_edge_ref_fails(self):
        with self.assertRaisesRegex(ValueError, "Parent ref"):
            self.run_dax(FIXTURE.replace('ref="A"', 'ref="Z"', 1))

    def test_duplicate_edges_fail(self):
        x = FIXTURE.replace('<parent ref="A"/></child>', '<parent ref="A"/><parent ref="A"/></child>',1)
        with self.assertRaisesRegex(ValueError, "Duplicated"):
            self.run_dax(x)

    def test_negative_file_size_keeps_topology_but_excludes_invalid_bytes(self):
        xml = FIXTURE.replace('file="p.bin" link="output" size="100"',
                              'file="p.bin" link="output" size="-9"')
        result = self.run_dax(xml)
        self.assertEqual(result["task_count"], 3)
        self.assertEqual(result["edge_count"], 2)
        self.assertEqual(result["critical_path_runtime_dax"], 6)
        self.assertEqual(result["invalid_dax_file_size_references"], 1)
        self.assertEqual(result["skipped_invalid_edge_file_size_pairs"], 1)
        self.assertEqual(result["declared_intertask_file_bytes"], 0)

    def test_file_size_mismatch_is_diagnostic_not_communication_time(self):
        x = self.run_dax(FIXTURE.replace('file="p.bin" link="input" size="100"',
                                         'file="p.bin" link="input" size="99"'))
        self.assertEqual(x["parent_child_file_size_disagreements"], 1)
        self.assertEqual(x["declared_intertask_file_bytes"], 100)

if __name__ == "__main__":
    unittest.main(verbosity=2)
