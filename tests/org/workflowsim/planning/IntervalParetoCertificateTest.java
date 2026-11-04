package org.workflowsim.planning;

import org.workflowsim.planning.IntervalParetoCertificate.Relation;

/** Hand-oracle checks: conservatism, abstain, dominance orientation, coverage. */
public final class IntervalParetoCertificateTest {
    private IntervalParetoCertificateTest() {}
    public static void main(String[] args) {
        double[] width={0.1,0.05};
        double[] small={10,20},large={20,40};
        if(IntervalParetoCertificate.compare(small,large,width,width)!=Relation.FIRST_DOMINATES)
            throw new AssertionError("Missed certain FIRST pair");
        if(IntervalParetoCertificate.compare(large,small,width,width)!=Relation.SECOND_DOMINATES)
            throw new AssertionError("Missed reversed certain SECOND pair");
        if(IntervalParetoCertificate.compare(new double[]{10,40},new double[]{20,20},
                width,width)!=Relation.ABSTAIN)
            throw new AssertionError("Trade-off wrongly certified");
        if(IntervalParetoCertificate.compare(new double[]{10,20},new double[]{10.1,20.1},
                width,width)!=Relation.ABSTAIN)
            throw new AssertionError("Overlapping uncertainty wrongly certified");
        if(!IntervalParetoCertificate.jointlyCovers(small,new double[]{11,19},width))
            throw new AssertionError("Wrong on-boundary coverage");
        if(IntervalParetoCertificate.jointlyCovers(small,new double[]{12,19},width))
            throw new AssertionError("Fails to catch out-of-bound real Makespan");
        for(int i=0;i<2;i++){
            boolean bad=false;
            try{
                IntervalParetoCertificate.compare(small,large,
                    i==0?new double[]{Double.NaN,0}:new double[]{1,0},width);
            }catch(IllegalArgumentException valid){bad=true;}
            if(!bad)throw new AssertionError("Invalid uncertainty accepted");
        }
        System.out.println("PASS IntervalParetoCertificateTest: strict two-objective separation, orientation, abstention and joint coverage");
    }
}
