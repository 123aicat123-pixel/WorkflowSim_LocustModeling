package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.cloudbus.cloudsim.CloudletSchedulerSpaceShared;
import org.workflowsim.CondorVM;
import org.workflowsim.Task;

/** No true simulator labels: verifies stable fitness, counting and token caps. */
public final class BudgetedEvolutionFidelityObjectiveTest {
    private BudgetedEvolutionFidelityObjectiveTest() {}
    private static CondorVM vm(int id) {
        return new CondorVM(id,0,id==0?100:200,1,512,100,10000,
                    "Xen",1,0,0,0,new CloudletSchedulerSpaceShared());
    }
    private static Map<Integer,Integer> assign(int a,int b,int c,int d) {
        Map<Integer,Integer> m=new HashMap<>();
        m.put(1,a);m.put(2,b);m.put(3,c);m.put(4,d);
        return m;
    }
    public static void main(String[] args) {
        Task a=new Task(1,1000),b=new Task(2,100),c=new Task(3,600),d=new Task(4,800);
        a.addChild(c);c.addParent(a);
        c.addChild(d);d.addParent(c);
        List<Task> tasks=Arrays.asList(a,c,d,b);
        List<CondorVM> vms=Arrays.asList(vm(0),vm(1));
        Map<Integer,Integer> p1=assign(0,1,0,1),p2=assign(1,0,1,0),
            p3=assign(0,0,0,0),p4=assign(1,1,1,1);
        BudgetedEvolutionFidelityObjective fixed=
            new BudgetedEvolutionFidelityObjective(tasks,vms,
                   BudgetedEvolutionFidelityObjective.Mode.PERIODIC,8,2);
        List<Map<Integer,Integer>> series=Arrays.asList(p1,p2,p3,p4,p1,p2,p3,p4);
        List<double[]> objectives=new ArrayList<>();
        for(int i=0;i<series.size();i++){
            objectives.add(fixed.evaluate(series.get(i)));
            BudgetedEvolutionFidelityObjective.Snapshot now=fixed.snapshot();
            if(now.readyCalls>(long)(i+1)*2/8 ||
               now.visits!=i+1||now.cheapCalls+now.cacheHits!=now.visits)
                throw new AssertionError("Violation of earned high-fidelity tokens");
        }
        for(int i=0;i<4;i++) {
            if(!Arrays.equals(objectives.get(i),objectives.get(i+4)))
                throw new AssertionError("Same placement changed Pareto objectives");
        }
        BudgetedEvolutionFidelityObjective.Snapshot first=fixed.snapshot();
        if(first.visits!=8||first.cheapCalls!=4||first.cacheHits!=4||
           first.distinct!=4||first.readyCalls>2)
            throw new AssertionError("Incorrect fixed-fitness cache/call bookkeeping");
        if(BudgetedEvolutionFidelityObjective.currentSnapshot()==null)
            throw new AssertionError("No context snapshot");
        BudgetedEvolutionFidelityObjective.clearCurrent();
        if(BudgetedEvolutionFidelityObjective.currentSnapshot()!=null)
            throw new AssertionError("Context leaked after explicit cleanup");
        boolean rejected=false;
        try{fixed.evaluate(p1);}catch(IllegalStateException correct){rejected=true;}
        if(!rejected)throw new AssertionError("Exceeded configured objective visit cap");
        BudgetedEvolutionFidelityObjective risk=
            new BudgetedEvolutionFidelityObjective(tasks,vms,
                BudgetedEvolutionFidelityObjective.Mode.RISK,8,2);
        for(Map<Integer,Integer> choice:series)risk.evaluate(choice);
        BudgetedEvolutionFidelityObjective.Snapshot second=risk.snapshot();
        if(second.readyCalls>2||second.visits!=8||second.cheapCalls!=4||
           second.distinct!=4)
            throw new AssertionError("Incorrect risk gate budget/caching");
        BudgetedEvolutionFidelityObjective.clearCurrent();
        System.out.println("PASS BudgetedEvolutionFidelityObjectiveTest: cached original genotype objective, token releases, both fidelity modes and no simulator oracle");
    }
}
