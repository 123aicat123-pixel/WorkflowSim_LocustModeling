package org.workflowsim.planning;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;

public final class GreedyStagedParetoSelectorTest {
    private GreedyStagedParetoSelectorTest() {}
    private static void eq(String label,double got,double expected){
        if(!Double.isFinite(got)||Math.abs(got-expected)>1e-10)
            throw new AssertionError(label+" expected="+expected+" got="+got);
    }
    private static boolean unique(int[] arr) {
        Set<Integer> s=new HashSet<>();
        for(int i:arr)if(!s.add(i))return false;
        return true;
    }
    public static void main(String[] args) {
        double[] ref={10,10};
        double[][] points={{2,8},{8,2},{5,5},{9,9}};
        eq("exact geometry two points",
          GreedyStagedParetoSelector.normalizedHV(points,new int[]{0,1},ref),0.28);
        GreedyStagedParetoSelector.Selection chosen=
            GreedyStagedParetoSelector.select(points,2,ref);
        if(!Arrays.equals(chosen.selected,new int[]{2,0}))
            throw new AssertionError("Greedy geometry and tie index mismatch "+
                Arrays.toString(chosen.selected));
        eq("greedy second marginal",chosen.predictedHypervolume,0.31);
        AtomicInteger calls=new AtomicInteger(0);
        Set<Integer> evaluated=new HashSet<>();
        GreedyStagedParetoSelector.Refined result=
            GreedyStagedParetoSelector.refine(points,index->{
                calls.incrementAndGet();
                if(!evaluated.add(index))throw new AssertionError("Repeated expensive candidate");
                return new double[]{points[index][0]*0.9,points[index][1]*0.9};
            },2,1,ref);
        if(calls.get()!=2||result.expensiveCalls!=2||
           !Arrays.equals(result.screened,new int[]{2,0})||
           result.selected.length!=1||!unique(result.selected)||
           !evaluated.equals(new HashSet<>(Arrays.asList(0,2))))
            throw new AssertionError("Missed expensive budget or original shortlist");
        eq("original unchanged",points[0][0],2.);
        eq("original unchanged cost",points[2][1],5.);
        boolean rejected=false;
        try{GreedyStagedParetoSelector.refine(points,i->new double[]{Double.NaN,1},2,1,ref);}
        catch(IllegalArgumentException ok){rejected=true;}
        if(!rejected)throw new AssertionError("Nonfinite expensive label allowed");
        rejected=false;
        try{GreedyStagedParetoSelector.select(points,5,ref);}
        catch(IllegalArgumentException ok){rejected=true;}
        if(!rejected)throw new AssertionError("Out of range quota accepted");
        rejected=false;
        try{GreedyStagedParetoSelector.refine(points,i->new double[]{1,1},1,2,ref);}
        catch(IllegalArgumentException ok){rejected=true;}
        if(!rejected)throw new AssertionError("K greater than T accepted");
        System.out.println("PASS GreedyStagedParetoSelectorTest: 2D HV geometry, deterministic selection, exactly T lazy calls, no mutation, input validation");
    }
}
