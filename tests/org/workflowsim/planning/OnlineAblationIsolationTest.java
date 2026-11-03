package org.workflowsim.planning;

import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/** Mechanism isolation contract: future labels have no influence in ANY mode.
 * Pure planned greedy must also be invariant to changed labels of earlier
 * real replays (the labels exist but are never used in candidate choice).
 */
public final class OnlineAblationIsolationTest {
    private OnlineAblationIsolationTest() {}

    public static void main(String[] args) throws Exception {
        Class<?> experiment=Class.forName("org.workflowsim.examples.planning.FLAResearchExperiment");
        Class<?> candidate=Class.forName("org.workflowsim.examples.planning.FLAResearchExperiment$Candidate");
        Class<?> result=Class.forName("org.workflowsim.examples.planning.FLAResearchExperiment$FeedbackChoice");
        Constructor<?> factory=candidate.getDeclaredConstructor(double[].class,Map.class);
        factory.setAccessible(true);
        Field simulated=candidate.getDeclaredField("simulated");simulated.setAccessible(true);
        Field map=candidate.getDeclaredField("assignment");map.setAccessible(true);
        Method select=experiment.getDeclaredMethod("chooseFeedbackMode",List.class,List.class,String.class);
        select.setAccessible(true);
        Field chosen=result.getDeclaredField("candidate");chosen.setAccessible(true);
        Field pM=result.getDeclaredField("predictedMakespan");pM.setAccessible(true);
        Field pC=result.getDeclaredField("predictedCost");pC.setAccessible(true);
        Field gain=result.getDeclaredField("predictedHvGain");gain.setAccessible(true);

        List<Object> pool=new ArrayList<>();
        double[][] data={{50,400},{55,350},{60,300},{65,250},
            {52,395},{53,365},{58,330},{62,287},{67,240},
            {70,220},{49,420},{64,255}};
        for(int i=0;i<data.length;i++){
            Map<Integer,Integer> assignment=new TreeMap<>();
            assignment.put(1,i+1);
            pool.add(factory.newInstance(data[i],assignment));
        }
        List<Object> prior=new ArrayList<>(pool.subList(0,4));
        for(int i=0;i<4;i++)simulated.set(prior.get(i),new double[]{data[i][0]*(1.02+i*.01),data[i][1]});
        for(String mode:new String[]{"online-planned-hv","online-observed-hv","online-nearest-hv"}) {
            Object baseline=select.invoke(null,pool,prior,mode);
            String expected=signature(baseline,chosen,map,pM,pC,gain);
            Object picked=chosen.get(baseline);
            if(prior.contains(picked))throw new AssertionError(mode+" selected already observed item");
            for(int i=4;i<pool.size();i++)
                simulated.set(pool.get(i),new double[]{1.e10+i,1.e-6+i});
            Object poisoned=select.invoke(null,pool,prior,mode);
            if(!expected.equals(signature(poisoned,chosen,map,pM,pC,gain)))
                throw new AssertionError(mode+" accessed future simulator labels");
            for(int i=4;i<pool.size();i++)simulated.set(pool.get(i),null);
            if(!expected.equals(signature(select.invoke(null,pool,prior,mode),chosen,map,pM,pC,gain)))
                throw new AssertionError(mode+" changed with missing future labels");
        }

        String planned=signature(select.invoke(null,pool,prior,"online-planned-hv"),
            chosen,map,pM,pC,gain);
        for(int i=0;i<4;i++)
            simulated.set(prior.get(i),new double[]{10000.+i,0.001+i});
        String changed=signature(select.invoke(null,pool,prior,"online-planned-hv"),
            chosen,map,pM,pC,gain);
        if(!planned.equals(changed))
            throw new AssertionError("Planned-only greedy depends on observed real simulator labels");
        for(Object p:prior)simulated.set(p,null);
        String absent=signature(select.invoke(null,pool,prior,"online-planned-hv"),
            chosen,map,pM,pC,gain);
        if(!planned.equals(absent))
            throw new AssertionError("Planned-only greedy requires simulator labels");
        for(String mode:new String[]{"online-observed-hv","online-nearest-hv"}) {
            try {
                select.invoke(null,pool,prior,mode);
                throw new AssertionError("Observed mode "+mode+" accepted missing earlier labels");
            } catch(InvocationTargetException e) {
                if(!(e.getCause() instanceof IllegalStateException))throw e;
            }
        }
        System.out.println("PASS three-way online mechanism isolation: no unobserved label lookahead, planned-only invariant to all simulator labels, observed modes fail closed");
    }

    private static String signature(Object decision,Field chosen,Field mapping,Field m,
                                    Field c,Field gain) throws Exception {
        return mapping.get(chosen.get(decision))+"|"+Double.doubleToLongBits(m.getDouble(decision))+
            "|"+Double.doubleToLongBits(c.getDouble(decision))+
            "|"+Double.doubleToLongBits(gain.getDouble(decision));
    }
}
