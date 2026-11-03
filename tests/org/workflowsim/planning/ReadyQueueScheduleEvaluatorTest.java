package org.workflowsim.planning;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import org.cloudbus.cloudsim.CloudletSchedulerSpaceShared;
import org.workflowsim.CondorVM;
import org.workflowsim.Task;

/**
 * Four-task hand oracle: A(10) and B(1) are roots on VM0, C(1) depends on A
 * on VM0, D(10) depends on C on VM1. Topological list deliberately puts
 * C,D before independent root B. A real ready queue must run B before C
 * after A finishes because B was ready earlier, whereas topological
 * insertion can book C before B.
 */
public final class ReadyQueueScheduleEvaluatorTest {
    private static void eq(String msg,double actual,double expected) {
        if(!Double.isFinite(actual)||Math.abs(actual-expected)>1e-8)
            throw new AssertionError(msg+" expected="+expected+" actual="+actual);
    }
    private static CondorVM vm(int id) {
        return new CondorVM(id,0,100,1,512,100,100000,
                "Xen",1,0,0,0,new CloudletSchedulerSpaceShared());
    }
    private static Map<Integer,Integer> assignment() {
        Map<Integer,Integer> map=new HashMap<>();
        map.put(1,0); map.put(2,0); map.put(3,0); map.put(4,1);
        return map;
    }
    public static void main(String[] args) {
        Task a=new Task(1,1000),b=new Task(2,100),c=new Task(3,100),d=new Task(4,1000);
        a.addChild(c);c.addParent(a);c.addChild(d);d.addParent(c);
        java.util.List<Task> topo=Arrays.asList(a,c,d,b);
        java.util.List<CondorVM> vms=Arrays.asList(vm(0),vm(1));
        ReadyQueueScheduleEvaluator reader=new ReadyQueueScheduleEvaluator(topo,vms);
        ReadyQueueScheduleEvaluator.Result q=reader.evaluate(assignment());
        eq("ready makespan",q.makespan,22);
        eq("ready cost",q.cost,22);
        eq("ready B start",q.starts[3],10);
        eq("ready C start",q.starts[1],11);
        eq("ready D start",q.starts[2],12);
        eq("ready no stagein",q.totalStageInSeconds,0);
        if(!Arrays.equals(q.scheduledTaskIds,new int[]{1,2,3,4}))
            throw new AssertionError("Wrong ready-queue dispatch order "+
                Arrays.toString(q.scheduledTaskIds));

        StageInAwareScheduleEvaluator.Result insertion=
                new StageInAwareScheduleEvaluator(topo,vms).evaluate(assignment());
        eq("topological insertion makespan",insertion.makespan,21);
        eq("topological insertion C start",insertion.starts[1],10);
        eq("topological insertion D start",insertion.starts[2],11);
        eq("topological insertion B start",insertion.starts[3],11);

        ReadyQueueScheduleEvaluator.Result repeated=reader.evaluate(assignment());
        eq("repeatable result",repeated.makespan,22);
        if(!Arrays.equals(repeated.scheduledTaskIds,q.scheduledTaskIds))
            throw new AssertionError("State leaked between evaluations");

        Map<Integer,Integer> missing=assignment();missing.remove(2);
        boolean rejected=false;
        try{reader.evaluate(missing);}catch(IllegalArgumentException ex){rejected=true;}
        if(!rejected)throw new AssertionError("Incomplete mapping must be rejected");
        System.out.println("PASS ReadyQueueScheduleEvaluatorTest: 4 tasks, causal ready priority, makespan 22 vs insertion 21, independent repeatability");
    }
}
