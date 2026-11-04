package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.cloudbus.cloudsim.CloudletSchedulerSpaceShared;
import org.workflowsim.CondorVM;
import org.workflowsim.Task;

/** Actual OLD/READY Java model batch integration regression, no simulator. */
public final class StagedScheduleBatchEvaluatorTest {
    private StagedScheduleBatchEvaluatorTest(){}
    private static CondorVM vm(int id){
        return new CondorVM(id,0,100,1,512,100,100000,
                "Xen",1,0,0,0,new CloudletSchedulerSpaceShared());
    }
    private static Map<Integer,Integer> mapping(int a,int b,int c,int d) {
        Map<Integer,Integer> m=new HashMap<>();
        m.put(1,a);m.put(2,b);m.put(3,c);m.put(4,d);
        return m;
    }
    private static void valid(StagedScheduleBatchEvaluator.SelectionResult x,int n,int t,int k) {
        if(x.oldCalls!=n||x.readyCalls!=t||x.screened.length!=t||
            x.selected.length!=k||x.chosenMappings.size()!=k||
            !(x.predictedHypervolume>=0)||!Double.isFinite(x.predictedHypervolume)||
            x.oldNanos<0||x.readyNanos<0||x.totalNanos<=0)
            throw new AssertionError("Incorrect two-layer evaluation bookkeeping");
        java.util.Set<Integer> used=new java.util.HashSet<>();
        for(int i:x.selected) {
            if(i<0||i>=n||!used.add(i))
                throw new AssertionError("Repeated or invalid output genotype");
        }
    }
    public static void main(String[] args) {
        Task a=new Task(1,1000),b=new Task(2,100),c=new Task(3,100),d=new Task(4,1000);
        a.addChild(c);c.addParent(a);c.addChild(d);d.addParent(c);
        List<Task> tasks=Arrays.asList(a,c,d,b);
        List<CondorVM> vm=Arrays.asList(vm(0),vm(1));
        List<Map<Integer,Integer>> candidates=new ArrayList<>();
        candidates.add(mapping(0,0,0,1));
        candidates.add(mapping(1,0,1,0));
        candidates.add(mapping(0,1,1,1));
        candidates.add(mapping(1,1,0,0));
        StagedScheduleBatchEvaluator stage=new StagedScheduleBatchEvaluator(tasks,vm);
        StagedScheduleBatchEvaluator.SelectionResult first=stage.select(candidates,2,1);
        valid(first,4,2,1);
        StagedScheduleBatchEvaluator.SelectionResult repeat=stage.select(candidates,2,1);
        valid(repeat,4,2,1);
        if(!Arrays.equals(first.selected,repeat.selected)||
            !Arrays.equals(first.screened,repeat.screened))
            throw new AssertionError("Repeated calls are not reproducible");
        StagedScheduleBatchEvaluator.SelectionResult active=
                stage.selectActiveUniform(candidates,2,1);
        valid(active,4,2,1);
        StagedScheduleBatchEvaluator.SelectionResult activeAgain=
                stage.selectActiveUniform(candidates,2,1);
        valid(activeAgain,4,2,1);
        if(!Arrays.equals(active.screened,activeAgain.screened)||
           !Arrays.equals(active.selected,activeAgain.selected))
            throw new AssertionError("Active model selector is nondeterministic");
        if(active.screened[0]==active.screened[1])
            throw new AssertionError("Repeated physical READY model query");
        StagedScheduleBatchEvaluator.SelectionResult another=stage.select(candidates,3,2);
        valid(another,4,3,2);
        valid(stage.select(candidates,4,4),4,4,4);
        Map<Integer,Integer> original=candidates.get(first.selected[0]);
        int before=original.get(1);
        first.chosenMappings.get(0).put(1,before==0?1:0);
        if(original.get(1)!=before)throw new AssertionError("Selected map leaked mutations");
        boolean rejected=false;
        try{stage.select(candidates,1,2);}
        catch(IllegalArgumentException e){rejected=true;}
        if(!rejected)throw new AssertionError("Invalid T<K budget not rejected");
        System.out.println("PASS StagedScheduleBatchEvaluatorTest: actual Java decoder wiring, 4 genotypes, strict T callbacks, deterministic original schedule mappings, detached outputs");
    }
}
