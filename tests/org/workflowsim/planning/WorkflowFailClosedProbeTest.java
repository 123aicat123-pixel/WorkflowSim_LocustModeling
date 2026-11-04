package org.workflowsim.planning;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import org.cloudbus.cloudsim.CloudletSchedulerSpaceShared;
import org.workflowsim.CondorVM;
import org.workflowsim.Task;

/**
 * Actual Java Task / CondorVM decoder bridge smoke test.
 * Hand oracle from ReadyQueueScheduleEvaluatorTest; no true simulator
 * execution and no calibrated uncertainty claim.
 */
public final class WorkflowFailClosedProbeTest {
    private WorkflowFailClosedProbeTest() {}
    private static void check(boolean b,String msg) {
        if(!b)throw new AssertionError(msg);
    }
    private static CondorVM vm(int id) {
        return new CondorVM(id,0,100,1,512,100,100000,
                "Xen",1,0,0,0,new CloudletSchedulerSpaceShared());
    }
    private static Map<Integer,Integer> mapping(boolean swappedInsertion) {
        Map<Integer,Integer> m=new HashMap<>();
        m.put(4,1);m.put(3,0);m.put(2,swappedInsertion?1:0);m.put(1,0);
        return m;
    }
    public static void main(String[] args) {
        Task a=new Task(1,1000),b=new Task(2,100),
                c=new Task(3,100),d=new Task(4,1000);
        a.addChild(c);c.addParent(a);c.addChild(d);d.addParent(c);
        WorkflowFailClosedProbe probe=new WorkflowFailClosedProbe(
                Arrays.asList(a,c,d,b),Arrays.asList(vm(0),vm(1)),2);
        Map<Integer,Integer> p=mapping(false),q=mapping(true);
        String pId=probe.register(p);
        Map<Integer,Integer> reordered=new HashMap<>();
        reordered.put(1,0);reordered.put(2,0);reordered.put(3,0);reordered.put(4,1);
        check(pId.equals(probe.register(reordered)),
                "TaskID/VMID identity must be independent of HashMap ordering");
        WorkflowFailClosedProbe.Result first=probe.assess(p,q);
        check(first.decision.kind==FailClosedFidelityGate.Kind.READY_ESTIMATES_AVAILABLE,
                "Two available READY forecasts expected");
        check(Math.abs(first.oldFirst[0]-21)<1e-8,
                "OLD must use real StageInAwareScheduleEvaluator");
        check(Math.abs(first.decision.readyFirst[0]-22)<1e-8,
                "READY must use actual task-ID scheduling evaluator");
        check(probe.oldCalls()==2 && probe.readyCalls()==2,
                "Two distinct physical assignments should consume two model decodes");
        first.decision.readyFirst[0]=-1;
        WorkflowFailClosedProbe.Result cached=probe.assess(reordered,q);
        check(cached.decision.kind==FailClosedFidelityGate.Kind.READY_ESTIMATES_AVAILABLE,
                "Already cached READY predictions remain accessible");
        check(cached.decision.readyFirst[0]==22 && probe.oldCalls()==2 &&
                probe.readyCalls()==2 && probe.oldCacheHits()==2 &&
                probe.readyCacheHits()==2,
                "Repeated TaskID->VMID mappings must use defensive cache values");
        check(probe.assess(p,p).decision.kind==FailClosedFidelityGate.Kind.KEEP_BOTH,
                "Same physical assignment should never trigger Pareto pruning");
        check(probe.registeredAssignments()==2,"Canonical identity accidentally changed");
        Map<Integer,Integer> invalid=new HashMap<>(p);invalid.remove(1);
        boolean rejected=false;
        try {probe.assess(invalid,q);} catch(IllegalArgumentException good) {rejected=true;}
        check(rejected,"Incomplete Task map should fail before decoding");
        invalid=new HashMap<>(p);invalid.put(2,999);
        rejected=false;
        try {probe.assess(invalid,q);} catch(IllegalArgumentException good) {rejected=true;}
        check(rejected,"Unknown VM ID must be rejected");
        WorkflowFailClosedProbe zero=new WorkflowFailClosedProbe(
                Arrays.asList(a,c,d,b),Arrays.asList(vm(0),vm(1)),0);
        check(zero.assess(p,q).decision.kind==FailClosedFidelityGate.Kind.KEEP_BOTH &&
                zero.readyCalls()==0,
                "Uncalibrated zero-budget policy MUST keep both candidates");
        System.out.println("PASS WorkflowFailClosedProbeTest: real 4-task OLD=21 READY=22, "+
                "canonical Task/VM identity, duplicate cache, strict quota and abstention");
    }
}
