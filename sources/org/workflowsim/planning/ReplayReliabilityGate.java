package org.workflowsim.planning;

import java.util.List;

/**
 * Conservative pilot gate for causal K-limited workflow replay selection.
 * Thresholds were predeclared for NEW topology/seed tests, NOT fitted on their
 * simulator labels. This is an experimental heuristic, not an accuracy guarantee.
 */
public final class ReplayReliabilityGate {
    private static final double MAX_ABS_MAKESPAN_REL_ERROR = 0.025;
    private static final double MAX_RESIDUAL_RANGE = 0.015;
    private static final double MIN_INFORMATIVE_PLANNED_GAP = 0.005;
    private ReplayReliabilityGate() {}

    public static boolean trust(List<double[]> planned,List<double[]> observed) {
        if(planned==null || observed==null || planned.size()!=observed.size())
            throw new IllegalArgumentException("Mismatched causal history");
        if(planned.size()<4)return false;
        double minResidual=Double.POSITIVE_INFINITY,maxResidual=Double.NEGATIVE_INFINITY;
        for(int i=0;i<planned.size();i++) {
            double[] p=planned.get(i),a=observed.get(i);
            if(p==null || a==null || p.length!=2 || a.length!=2 ||
                    !Double.isFinite(p[0]) || !Double.isFinite(p[1]) ||
                    !Double.isFinite(a[0]) || !Double.isFinite(a[1]) ||
                    p[0]<=0 || a[0]<=0 || p[1]<0 || a[1]<0)
                throw new IllegalArgumentException("Nonfinite/invalid observed objectives");
            double residual=a[0]/p[0]-1.;
            if(Math.abs(residual)>MAX_ABS_MAKESPAN_REL_ERROR)return false;
            minResidual=Math.min(minResidual,residual);
            maxResidual=Math.max(maxResidual,residual);
        }
        if(maxResidual-minResidual>MAX_RESIDUAL_RANGE)return false;
        int informative=0;
        for(int i=0;i<planned.size();i++)
            for(int j=i+1;j<planned.size();j++) {
                double pm=planned.get(i)[0]-planned.get(j)[0];
                double scale=Math.max(planned.get(i)[0],planned.get(j)[0]);
                if(Math.abs(pm)/scale<MIN_INFORMATIVE_PLANNED_GAP)continue;
                informative++;
                double am=observed.get(i)[0]-observed.get(j)[0];
                if((pm>0 && am<=0) || (pm<0 && am>=0))return false;
            }
        return informative>=2;
    }
}
