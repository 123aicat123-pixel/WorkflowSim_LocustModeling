package org.workflowsim.planning;

import java.util.Arrays;
import java.util.List;
import org.cloudbus.cloudsim.CloudletSchedulerSpaceShared;
import org.workflowsim.CondorVM;
import org.workflowsim.Task;

/** Hand-oracle: gate operates on physical ready-queue contention, not labels. */
public final class QueueConflictRiskRelocationTest {
    private static CondorVM vm(int id) {
        return new CondorVM(id,0,100,1,512,100,100000,
                "Xen",1,0,0,0,new CloudletSchedulerSpaceShared());
    }
    private static java.util.Map<Integer,Integer> assignment(int[] genes,List<Task> tasks) {
        java.util.Map<Integer,Integer> result=new java.util.HashMap<>();
        for(int i=0;i<genes.length;i++)result.put(tasks.get(i).getCloudletId(),genes[i]);
        return result;
    }
    private static void eq(String label,double x,double expected) {
        if(!Double.isFinite(x)||Math.abs(x-expected)>1e-8)
            throw new AssertionError(label+": expected="+expected+" got="+x);
    }
    public static void main(String[] args) {
        Task a=new Task(1,1000),b=new Task(2,100),c=new Task(3,100),d=new Task(4,1000);
        a.addChild(c);c.addParent(a);
        c.addChild(d);d.addParent(c);
        List<Task> tasks=Arrays.asList(a,b,c,d);
        List<CondorVM> vms=Arrays.asList(vm(0),vm(1));
        int[][] allowed={{0,1},{0,1},{0,1},{0,1}};
        double[] importance={1.0,.04,.52,.48};
        double[][] service={{10,10},{1,1},{1,1},{10,10}};
        ReadyQueueScheduleEvaluator model=new ReadyQueueScheduleEvaluator(tasks,vms);
        int[] original={0,0,0,1};
        eq("original actual task queue estimate",model.evaluate(assignment(original,tasks)).makespan,22);
        int[] latency=original.clone();
        QueueConflictRiskRelocation.Result proposal=QueueConflictRiskRelocation.propose(
            latency,tasks,vms,allowed,importance,service,true,model);
        if(!proposal.moved||proposal.taskId!=3||!Arrays.equals(latency,new int[]{0,0,1,1}))
            throw new AssertionError("Queue conflict guided target should be Task C on VM1");
        eq("repaired predicted Makespan",model.evaluate(assignment(latency,tasks)).makespan,21);
        if(proposal.forecastCount!=2||proposal.candidateCount!=1||proposal.improvementRatio<=0)
            throw new AssertionError("Counterfactual probe accounting");
        int[] same=original.clone();
        QueueConflictRiskRelocation.Result repeat=QueueConflictRiskRelocation.propose(
            same,tasks,vms,allowed,importance,service,true,model);
        if(!Arrays.equals(latency,same)||repeat.forecastCount!=proposal.forecastCount)
            throw new AssertionError("Non-deterministic queue-risk repair");
        int[] cost=original.clone();
        QueueConflictRiskRelocation.Result noCost=QueueConflictRiskRelocation.propose(
            cost,tasks,vms,allowed,importance,service,false,model);
        if(noCost.moved||!Arrays.equals(cost,original))
            throw new AssertionError("Cost-focused group must reject non-cost-improving relocation");
        int[][] onlyOne={{0},{0},{0},{1}};
        int[] blocked=original.clone();
        QueueConflictRiskRelocation.Result invalid=QueueConflictRiskRelocation.propose(
            blocked,tasks,vms,onlyOne,importance,service,true,model);
        if(invalid.moved||invalid.forecastCount!=1||!Arrays.equals(blocked,original))
            throw new AssertionError("Do not invent alternative VMs");
        System.out.println("PASS QueueConflictRiskRelocationTest: exact physical 22->21 hand oracle, deterministic, bounded internal forecasts, cost safety and immutable failures");
    }
}
