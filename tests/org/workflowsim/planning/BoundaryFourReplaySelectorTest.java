package org.workflowsim.planning;

import java.util.Arrays;
import java.util.Random;

/** Pure, no-simulator property regression of a frozen K12+4 replay policy. */
public final class BoundaryFourReplaySelectorTest {
    private BoundaryFourReplaySelectorTest() {}
    private static void ok(boolean value,String why) {
        if(!value)throw new AssertionError(why);
    }
    public static void main(String[] args) {
        double[][] p=new double[36][2];
        String[] ids=new String[36];
        int[] twelve=new int[12];
        for(int i=0;i<36;i++) {
            ids[i]=String.format("task=%02d",i);
            if(i<12) {
                p[i][0]=10+i;
                p[i][1]=50-i;
                twelve[i]=i;
            } else {
                p[i][0]=30+(i-12);
                p[i][1]=60+(i-12);
            }
        }
        for(BoundaryFourReplaySelector.Policy kind:
            BoundaryFourReplaySelector.Policy.values()) {
            BoundaryFourReplaySelector.Result a=
                BoundaryFourReplaySelector.select(p,ids,twelve,kind,new Random(971));
            BoundaryFourReplaySelector.Result b=
                BoundaryFourReplaySelector.select(p,ids,twelve,kind,new Random(971));
            ok(Arrays.equals(a.indices,b.indices),"Fixed seed was not reproducible");
            ok(a.indices.length==16 && a.dominatedEligible==24,"Wrong eligible pool");
            ok(Arrays.equals(a.stratumSizes,new int[]{6,6,6,6}),"Wrong quantile partition");
            for(int i=0;i<12;i++)ok(a.indices[i]==i,"Changed baseline K12");
            java.util.Set<Integer> uniq=new java.util.HashSet<>();
            for(int i:a.indices)ok(uniq.add(i),"Repeated assignment");
            for(int i=12;i<16;i++)
                ok(a.indices[i]>=12 && a.indices[i]<36,"Not a dominated candidate");
        }
        boolean rejected=false;
        try {
            double[][] q=new double[16][2];
            for(int i=0;i<16;i++)q[i]=new double[]{10+i,50-i};
            String[] id=new String[16];
            for(int i=0;i<16;i++)id[i]="task="+i;
            BoundaryFourReplaySelector.select(q,id,twelve,
                BoundaryFourReplaySelector.Policy.BOUNDARY,new Random(2));
        } catch(IllegalStateException expected) {rejected=true;}
        ok(rejected,"Must reject unfilled dominated strata instead of inventing fallback");
        rejected=false;
        try {
            String[] bad=ids.clone();bad[15]=bad[14];
            BoundaryFourReplaySelector.select(p,bad,twelve,
                BoundaryFourReplaySelector.Policy.BOUNDARY,new Random(2));
        } catch(IllegalArgumentException expected) {rejected=true;}
        ok(rejected,"Duplicate canonical maps should fail");
        rejected=false;
        try {
            double[][] q=p.clone();q[20]=new double[]{Double.NaN,10};
            BoundaryFourReplaySelector.select(q,ids,twelve,
                BoundaryFourReplaySelector.Policy.BOUNDARY,new Random(2));
        } catch(IllegalArgumentException expected) {rejected=true;}
        ok(rejected,"Invalid cheap objective must fail");
        System.out.println("PASS BoundaryFourReplaySelectorTest: fixed K12, disjoint K4 strata, reproducible selections, strict invalid-input and empty-eligibility fail-closed");
    }
}
