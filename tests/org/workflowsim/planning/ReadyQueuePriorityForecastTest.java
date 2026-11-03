package org.workflowsim.planning;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import org.cloudbus.cloudsim.CloudletSchedulerSpaceShared;
import org.workflowsim.CondorVM;
import org.workflowsim.Task;

/** Fixed assignment hand oracle to prove priority forecast actually changes task order. */
public final class ReadyQueuePriorityForecastTest {
    private static CondorVM vm(int id){
        return new CondorVM(id,0,100,1,512,100,100000,
                "Xen",1,0,0,0,new CloudletSchedulerSpaceShared());
    }
    private static void eq(String label,double value,double expected) {
        if(Math.abs(value-expected)>1e-8)
            throw new AssertionError(label+" expected="+expected+" observed="+value);
    }
    public static void main(String[] args) {
        Task a=new Task(1,1000),b=new Task(2,100),c=new Task(3,100),d=new Task(4,1000);
        a.addChild(c);c.addParent(a);c.addChild(d);d.addParent(c);
        java.util.List<Task> topo=Arrays.asList(a,c,d,b);
        java.util.List<CondorVM> vms=Arrays.asList(vm(0),vm(1));
        Map<Integer,Integer> map=new HashMap<>();
        map.put(1,0);map.put(2,0);map.put(3,0);map.put(4,1);

        ReadyQueueScheduleEvaluator.Result standard=
            new ReadyQueueScheduleEvaluator(topo,vms).evaluate(map);
        ReadyQueueScheduleEvaluator.Result explicit=
            new ReadyQueueScheduleEvaluator(topo,vms,
                ReadyQueueScheduleEvaluator.QueuePolicy.TASK_ID).evaluate(map);
        ReadyQueueScheduleEvaluator.Result shortest=
            new ReadyQueueScheduleEvaluator(topo,vms,
                ReadyQueueScheduleEvaluator.QueuePolicy.SHORTEST).evaluate(map);
        ReadyQueueScheduleEvaluator.Result upward=
            new ReadyQueueScheduleEvaluator(topo,vms,
                ReadyQueueScheduleEvaluator.QueuePolicy.UPWARD).evaluate(map);
        eq("old unchanged",standard.makespan,22);
        eq("explicit task id unchanged",explicit.makespan,22);
        eq("shortest",shortest.makespan,22);
        eq("upward",upward.makespan,21);
        eq("upward C before pending B",upward.starts[1],10);
        eq("upward D",upward.starts[2],11);
        eq("upward task B",upward.starts[3],11);
        if(!Arrays.equals(standard.scheduledTaskIds,explicit.scheduledTaskIds)||
            !Arrays.equals(upward.scheduledTaskIds,new int[]{1,3,4,2}))
            throw new AssertionError("Wrong forecast queue priority");
        boolean rejected=false;
        try{ReadyQueueScheduleEvaluator.fromRuntimeName("unknown");}
        catch(IllegalArgumentException expected){rejected=true;}
        if(!rejected)throw new AssertionError("Unregistered mode allowed");
        System.out.println("PASS ReadyQueuePriorityForecastTest: default semantic parity and 4-task upward-priority intervention");
    }
}
