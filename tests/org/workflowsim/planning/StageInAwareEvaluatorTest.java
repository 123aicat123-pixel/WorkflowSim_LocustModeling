package org.workflowsim.planning;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import org.cloudbus.cloudsim.CloudletSchedulerSpaceShared;
import org.workflowsim.CondorVM;
import org.workflowsim.FileItem;
import org.workflowsim.Task;
import org.workflowsim.utils.Parameters;

/**
 * Hand-checked stage-in, VM-cache, DAG precedence and billing oracle.
 * A: 1s CPU, 20 MB external input / 10 MB/s = 2s stage-in.
 * A produces X (10MB). B consumes X, computes 1s.
 * C consumes the same original external input, computes 1s.
 * Two VMs: vm0 bandwidth 10 MB/s at $1/s; vm1 bandwidth 5 MB/s at $2/s.
 */
public final class StageInAwareEvaluatorTest {
    private static void eq(String what,double actual,double expected) {
        if(!Double.isFinite(actual)||Math.abs(actual-expected)>1e-8)
            throw new AssertionError(what+" expected "+expected+" but got "+actual);
    }
    private static FileItem file(String name,double bytes,Parameters.FileType t) {
        FileItem f=new FileItem(name,bytes);
        f.setType(t);
        return f;
    }
    private static CondorVM vm(int id,long bandwidth,double cost) {
        return new CondorVM(id,0,100,1,512,bandwidth,100000,
                "Xen",cost,0,0,0,new CloudletSchedulerSpaceShared());
    }
    private static Map<Integer,Integer> mapping(int a,int b,int c) {
        Map<Integer,Integer> map=new HashMap<>();
        map.put(0,a);map.put(1,b);map.put(2,c);return map;
    }
    public static void main(String[] args) {
        Task a=new Task(0,100), b=new Task(1,100), c=new Task(2,100);
        a.addChild(b);b.addParent(a);
        a.addFile(file("input",20000000,Parameters.FileType.INPUT));
        a.addFile(file("x",10000000,Parameters.FileType.OUTPUT));
        b.addFile(file("x",10000000,Parameters.FileType.INPUT));
        c.addFile(file("input",20000000,Parameters.FileType.INPUT));
        StageInAwareScheduleEvaluator e=new StageInAwareScheduleEvaluator(
            Arrays.asList(a,b,c),Arrays.asList(vm(0,10,1),vm(1,5,2)));
        StageInAwareScheduleEvaluator.Result cross=e.evaluate(mapping(0,1,0));
        eq("cross makespan",cross.makespan,6);
        eq("cross cost",cross.cost,10);
        eq("cross total stage",cross.stageInSeconds,4);
        eq("cross external stage",cross.externalStageInSeconds,2);
        eq("cross intermediate stage",cross.intermediateStageInSeconds,2);
        StageInAwareScheduleEvaluator.Result same=e.evaluate(mapping(0,0,0));
        eq("same-VM makespan",same.makespan,5);
        eq("same-VM cost",same.cost,5);
        eq("same-VM total stage",same.stageInSeconds,2);
        eq("same-VM external stage",same.externalStageInSeconds,2);
        eq("same-VM intermediate stage",same.intermediateStageInSeconds,0);
        // Evaluation must not retain replica caches across independent schedules.
        StageInAwareScheduleEvaluator.Result crossAgain=e.evaluate(mapping(0,1,0));
        eq("repeat cross makespan",crossAgain.makespan,6);
        eq("repeat cross cost",crossAgain.cost,10);
        boolean rejected=false;
        try {e.evaluate(mapping(0,1,999));} catch(IllegalArgumentException ex) {rejected=true;}
        if(!rejected)throw new AssertionError("Unknown VM id should be rejected");
        System.out.println("PASS StageInAwareEvaluatorTest: DAG, external stage-in, replica cache, cross-VM transfers, bill and repeatability");
    }
}
