package org.workflowsim.planning;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import org.cloudbus.cloudsim.CloudletSchedulerSpaceShared;
import org.workflowsim.CondorVM;
import org.workflowsim.FileItem;
import org.workflowsim.Task;
import org.workflowsim.utils.Parameters;

/** v14 requires a one-call stage-in-aware TRUE PLANNING timeline, not stale legacy intervals. */
public final class TimelineParetoNeighborTest {
    private TimelineParetoNeighborTest() {}
    private static void eq(double a,double b,String msg) {
        if(!Double.isFinite(a)||Math.abs(a-b)>1e-8)
            throw new AssertionError(msg+" expected "+b+" got "+a);
    }
    private static void check(boolean ok,String msg) {if(!ok)throw new AssertionError(msg);}
    private static CondorVM vm(int id,long bw,double cost) {
        return new CondorVM(id,0,100,1,512,bw,100000,
                "Xen",cost,0,0,0,new CloudletSchedulerSpaceShared());
    }
    private static FileItem file(String name,double size,Parameters.FileType type) {
        FileItem f=new FileItem(name,size);f.setType(type);return f;
    }
    public static void main(String[] args) {
        System.setProperty("workflowsim.planningStageInAware","true");
        Task a=new Task(0,100),b=new Task(1,100),c=new Task(2,100);
        a.addChild(b);b.addParent(a);
        a.addFile(file("source",20000000,Parameters.FileType.INPUT));
        a.addFile(file("transfer",10000000,Parameters.FileType.OUTPUT));
        b.addFile(file("transfer",10000000,Parameters.FileType.INPUT));
        c.addFile(file("source",20000000,Parameters.FileType.INPUT));
        List<CondorVM> vms=Arrays.asList(vm(0,10,1),vm(1,5,2));
        FLAScheduleEvaluator evaluator=new FLAScheduleEvaluator(Arrays.asList(a,b,c),vms);
        List<Task> order=evaluator.getTaskOrder();
        Map<Integer,Integer> mapping=new HashMap<>();mapping.put(0,0);mapping.put(1,1);mapping.put(2,0);
        int[] g=evaluator.fromAssignment(mapping);
        long n=evaluator.getObjectiveEvaluations();
        FLAScheduleEvaluator.ScheduleTrace t=evaluator.evaluateWithTrace(g);
        check(evaluator.getObjectiveEvaluations()==n+1,"trace used more than one objective call");
        eq(t.makespan,6,"true stage-in-aware makespan");
        eq(t.cost,10,"true stage-in-aware rental cost");
        int ia=order.indexOf(a),ib=order.indexOf(b),ic=order.indexOf(c);
        eq(t.starts[ia],0,"A starts");
        eq(t.finishes[ia],3,"A finish incl source stage");
        eq(t.starts[ib],3,"B parent readiness");
        eq(t.finishes[ib],6,"B finish incl intermediate stage");
        eq(t.starts[ic],3,"C queued on vm0");
        eq(t.finishes[ic],4,"C finish (replica cache)");
        int[][] allowed=new int[3][];
        for(int k=0;k<3;k++)allowed[k]=new int[]{0,1};
        int selected=TimelineParetoNeighbor.chooseTask(t,allowed,false,new Random(4));
        check(selected==ib,"trailing task should be B");
        int proposed=TimelineParetoNeighbor.chooseVm(t,g,ib,new int[]{0,1},
                new double[]{1,1},vms,true,false,new Random(4),order);
        check(proposed!=g[ib],"neighbor must change VM");
        check(evaluator.getObjectiveEvaluations()==n+1,
                "pure neighbor helper secretly evaluated schedule");
        // B must wait at least for A's completion (3s), even when VM has free
        // capacity from t=0. Old placeholder 0.0 readiness would violate this.
        double candidate=TimelineParetoNeighbor.earliestGapFinish(
                t,ib,0,1,t.finishes[ia]);
        check(candidate>=t.finishes[ia]+1-1e-8,
                "candidate violates causal predecessor-ready time");
        double[] detached=t.finishes.clone();
        Map<Integer,Integer> same=new HashMap<>();same.put(0,0);same.put(1,0);same.put(2,0);
        evaluator.evaluate(evaluator.fromAssignment(same));
        check(Arrays.equals(detached,t.finishes),"snapshot mutated by later evaluation");
        check(evaluator.getObjectiveEvaluations()==n+2,"second direct fitness call not counted");
        System.out.println("PASS v14 counted stage-in timeline, DAG parent readiness, deterministic eligible one-gene neighbor, immutable snapshot");
    }
}
