#!/usr/bin/env python3
"""Pure unit tests for read-only matched VM-speed fidelity."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("matched", HERE/"fla_matched_speed_fidelity.py")
m=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

class MatchTest(unittest.TestCase):
    def row(self, speed, arm, mapping, mscale=1):
        return dict(cohort="real-sizes", dag="Epigenomics_46", seed=211,
                    speed=speed, arm=arm, mapping=mapping, candidate_index=1,
                    planned_makespan=100.*mscale, sim_makespan=110.*mscale,
                    planned_cost=12., sim_cost=12.)
    def test_speed_effect_no_error_when_predictions_scale_same(self):
        d=self.row("default","A","M")
        s=self.row("staggered","A","M",2)
        v=m.speed_effect(d,s)
        self.assertAlmostEqual(v["makespan_effect_gap_pp"],0)
        self.assertAlmostEqual(v["planned_makespan_change_pct"],100)
        self.assertAlmostEqual(v["actual_makespan_change_pct"],100)
    def test_speed_effect_residual_distinguishes_planned_true(self):
        d=self.row("default","A","M")
        s=self.row("staggered","A","M")
        s["sim_makespan"]=132.
        v=m.speed_effect(d,s)
        self.assertAlmostEqual(v["makespan_effect_gap_pp"],-20)
    def test_pairing_cross_arm_deduplicates_and_rejects_nonmatches(self):
        original={}
        for arm in m.ARMS:
            for speed in m.SPEEDS:
                for i in range(16):
                    mapping=f"m{i}"
                    r=self.row(speed,arm,mapping)
                    if speed=="staggered":
                        r["planned_makespan"]+=5
                    key=(r["cohort"],r["dag"],r["seed"],speed,arm,mapping)
                    original[key]=r
        # Compare-speed expects every declared case, so construct the same
        # complete matrix with unique maps outside one shared cohort.
        for cohort,names,seeds,_ in m.GROUPS:
            for dag in names:
                for seed in seeds:
                    for arm in m.ARMS:
                        for speed in m.SPEEDS:
                            for i in range(16):
                                mapping=f"m{i}" if (cohort,dag,seed)==("real-sizes","Epigenomics_46",211) else f"{speed}-m{i}"
                                r=self.row(speed,arm,mapping)
                                r.update(cohort=cohort,dag=dag,seed=seed)
                                if speed=="staggered":r["planned_makespan"]+=5
                                key=(cohort,dag,seed,speed,arm,mapping)
                                original[key]=r
        rows,cov,unique=m.compare_speed(original)
        self.assertEqual(len(rows),64)
        self.assertEqual(len(unique),16)
        self.assertEqual(sum(x["same_mapping_overlap_n"] for x in cov),64)
        self.assertTrue(all(x["repeated_arm_observations"]==4 for x in unique))
        self.assertTrue(all(x["cross_arm_consistent"]==1 for x in unique))
    def test_cross_arm_conflict_detected(self):
        original={}
        for cohort,names,seeds,_ in m.GROUPS:
            for dag in names:
                for seed in seeds:
                    for arm in m.ARMS:
                        for speed in m.SPEEDS:
                            for i in range(16):
                                mapping=f"{speed}-m{i}"
                                if (cohort,dag,seed)==("real-sizes","Epigenomics_46",211):
                                    mapping=f"m{i}"
                                r=self.row(speed,arm,mapping)
                                r.update(cohort=cohort,dag=dag,seed=seed)
                                if (cohort,dag,seed,arm,speed,i)==("real-sizes","Epigenomics_46",211,m.ARMS[-1],"default",0):
                                    r["sim_makespan"]+=100.
                                original[(cohort,dag,seed,speed,arm,mapping)]=r
        _,_,unique=m.compare_speed(original)
        self.assertEqual(len(unique),16)
        self.assertEqual(sum(not x["cross_arm_consistent"] for x in unique),1)

if __name__=="__main__":
    unittest.main()
