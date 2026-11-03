package org.workflowsim.planning;

import java.lang.reflect.*;
import java.util.*;

/** Verifies predeclared gate, conservative fallback and strict no-future-label usage. */
public final class ReplayReliabilityGateTest {
    private ReplayReliabilityGateTest() {}
    private static void check(boolean ok,String reason) {
        if(!ok)throw new AssertionError(reason);
    }
    private static List<double[]> list(double[][] rows) {
        return new ArrayList<>(Arrays.asList(rows));
    }
    public static void main(String[] args) throws Exception {
        double[][] p={{100,220},{105,210},{110,200},{115,190}};
        double[][] accurate={{100.5,220},{105.4,210},{110.3,200},{115.6,190}};
        check(ReplayReliabilityGate.trust(list(p),list(accurate)),"stable ranks should trust");
        check(!ReplayReliabilityGate.trust(list(p),list(new double[][]{
            {100.5,220},{105.4,210},{120,200},{115.6,190}})),"large error must fall back");
        check(!ReplayReliabilityGate.trust(list(new double[][]{
            {100,200},{100,201},{100,202},{100,203}}),list(new double[][]{
            {100,200},{100,201},{100,202},{100,203}})),"no planned rank evidence");
        check(!ReplayReliabilityGate.trust(list(new double[][]{p[0],p[1]}),
            list(new double[][]{accurate[0],accurate[1]})),"two replays cannot justify gate");
        try {
            ReplayReliabilityGate.trust(list(p),list(new double[][]{{100,220}}));
            throw new AssertionError("mismatch accepted");
        } catch(IllegalArgumentException expected) {}

        Class<?> exp=Class.forName("org.workflowsim.examples.planning.FLAResearchExperiment");
        Class<?> cand=Class.forName("org.workflowsim.examples.planning.FLAResearchExperiment$Candidate");
        Class<?> choice=Class.forName("org.workflowsim.examples.planning.FLAResearchExperiment$FeedbackChoice");
        Constructor<?> ctor=cand.getDeclaredConstructor(double[].class,Map.class);
        ctor.setAccessible(true);
        Field actual=cand.getDeclaredField("simulated");actual.setAccessible(true);
        Field decided=choice.getDeclaredField("candidate");decided.setAccessible(true);
        Field mode=choice.getDeclaredField("decisionMode");mode.setAccessible(true);
        Method select=exp.getDeclaredMethod("chooseReliabilityGatedFeedback",List.class,List.class);
        select.setAccessible(true);
        List<Object> pool=new ArrayList<>();
        double[][] planned={{100,220},{105,210},{110,200},{115,190},
             {102,215},{108,205},{112,195},{117,185}};
        for(int i=0;i<planned.length;i++) {
            Map<Integer,Integer> mapping=new TreeMap<>();mapping.put(7,i+1);
            pool.add(ctor.newInstance(planned[i],mapping));
        }
        List<Object> done=new ArrayList<>(pool.subList(0,4));
        for(int i=0;i<4;i++)actual.set(done.get(i),accurate[i]);
        Object a=select.invoke(null,pool,done);
        check("gated-observed".equals(mode.get(a)),"stable gate should choose observed front");
        Object picked=decided.get(a);
        check(!done.contains(picked),"duplicate selected candidate");
        for(int i=4;i<pool.size();i++)actual.set(pool.get(i),new double[]{1e9+i,1e-4+i});
        Object b=select.invoke(null,pool,done);
        check(decided.get(b)==picked && mode.get(a).equals(mode.get(b)),
            "future simulated labels leaked into decision");
        actual.set(done.get(0),new double[]{110,220});
        Object fallback=select.invoke(null,pool,done);
        check(decided.get(fallback)==pool.get(4),"fallback must use fixed cover order");
        check("gated-cover".equals(mode.get(fallback)),"fallback not audited");
        actual.set(done.get(0),null);
        try {
            select.invoke(null,pool,done);
            throw new AssertionError("missing prior label accepted");
        } catch(InvocationTargetException e) {
            check(e.getCause() instanceof IllegalStateException,"missing prior must fail closed");
        }
        System.out.println("PASS conservative trust gate, fixed cover fallback and adversarial no-lookahead");
    }
}
