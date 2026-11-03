package org.workflowsim.planning;

import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * Adversarial no-lookahead contract for experimental causal replay selection.
 * Changing ANY unobserved simulator label must not affect the NEXT selected
 * mapping, predicted objectives, or marginal HV. Only previously observed
 * simulator outcomes are permitted into chooseOnlineFeedback.
 */
public final class OnlineFeedbackCausalityTest {
    private OnlineFeedbackCausalityTest() {}

    public static void main(String[] args) throws Exception {
        Class<?> experiment=Class.forName("org.workflowsim.examples.planning.FLAResearchExperiment");
        Class<?> candidate=Class.forName("org.workflowsim.examples.planning.FLAResearchExperiment$Candidate");
        Class<?> chosen=Class.forName("org.workflowsim.examples.planning.FLAResearchExperiment$FeedbackChoice");
        Constructor<?> constructor=candidate.getDeclaredConstructor(double[].class,Map.class);
        constructor.setAccessible(true);
        Field simulated=candidate.getDeclaredField("simulated");
        simulated.setAccessible(true);
        Field assignment=candidate.getDeclaredField("assignment");
        assignment.setAccessible(true);
        Method chooser=experiment.getDeclaredMethod("chooseOnlineFeedback",List.class,List.class);
        chooser.setAccessible(true);
        Field candidateChoice=chosen.getDeclaredField("candidate");
        candidateChoice.setAccessible(true);
        Field predictedMakespan=chosen.getDeclaredField("predictedMakespan");
        predictedMakespan.setAccessible(true);
        Field predictedCost=chosen.getDeclaredField("predictedCost");
        predictedCost.setAccessible(true);
        Field predictedGain=chosen.getDeclaredField("predictedHvGain");
        predictedGain.setAccessible(true);

        List<Object> pool=new ArrayList<>();
        double[][] points={
            {70,250},{75,226},{80,205},{86,190},
            {72,236},{76,218},{79,209},{84,197},{89,180},
            {95,165},{69,270},{87,184}
        };
        for(int i=0;i<points.length;i++) {
            Map<Integer,Integer> mapping=new TreeMap<>();
            mapping.put(1,i+1);
            pool.add(constructor.newInstance(points[i],mapping));
        }
        List<Object> observed=new ArrayList<>(pool.subList(0,4));
        for(int i=0;i<observed.size();i++)
            simulated.set(observed.get(i),new double[]{points[i][0]*(1.01+0.002*i),points[i][1]});

        Object first=chooser.invoke(null,pool,observed);
        Object choiceA=candidateChoice.get(first);
        String snapshot=signature(first,assignment,predictedMakespan,predictedCost,predictedGain);
        if(observed.contains(choiceA))throw new AssertionError("Next choice already replayed");

        for(int i=4;i<pool.size();i++)
            simulated.set(pool.get(i),new double[]{1.e8+i,0.00001+i});
        Object poisoned=chooser.invoke(null,pool,observed);
        String snapshot2=signature(poisoned,assignment,predictedMakespan,predictedCost,predictedGain);
        if(!snapshot.equals(snapshot2))throw new AssertionError(
                "CAUSALITY VIOLATION: unseen simulator labels changed decision: "+snapshot+" -> "+snapshot2);

        // The next choice must also work if unseen simulator labels are null.
        for(int i=4;i<pool.size();i++)simulated.set(pool.get(i),null);
        Object blank=chooser.invoke(null,pool,observed);
        String snapshot3=signature(blank,assignment,predictedMakespan,predictedCost,predictedGain);
        if(!snapshot.equals(snapshot3))throw new AssertionError("Unobserved null label changed selection");

        // Fail loudly if one of the supposedly observed replays has no true label.
        simulated.set(observed.get(0),null);
        try {
            chooser.invoke(null,pool,observed);
            throw new AssertionError("Missing earlier simulator label did not fail closed");
        } catch (java.lang.reflect.InvocationTargetException e) {
            if(!(e.getCause() instanceof IllegalStateException))throw e;
        }
        System.out.println("PASS causal feedback no-lookahead under adversarial unseen-label poisoning, missing-observation fails closed");
    }

    private static String signature(Object selected,Field assignment,Field makespan,
                                    Field cost,Field gain) throws Exception {
        Class<?> cls=selected.getClass();
        Field candidate=cls.getDeclaredField("candidate");
        candidate.setAccessible(true);
        Object item=candidate.get(selected);
        return assignment.get(item)+";"+Double.doubleToLongBits(makespan.getDouble(selected))+
                ";"+Double.doubleToLongBits(cost.getDouble(selected))+
                ";"+Double.doubleToLongBits(gain.getDouble(selected));
    }
}
