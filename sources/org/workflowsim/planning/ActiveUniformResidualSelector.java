package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.function.IntFunction;

/**
 * Prospective, research-only post-search selector for 2 minimized objectives.
 *
 * Always ranks EVERY candidate using the SAME nearest-observation residual
 * correction of an OLD score. Only T queried candidates are evaluated with
 * READY; unqueried READY targets and true WorkflowSim labels are NEVER read.
 * The correction is recalculated over the WHOLE pool after each observation:
 * no raw OLD vs READY pairwise fitness comparison (unlike staged-greedy).
 *
 * This does not edit the FLA/NSGA-II evolutionary population or assert true
 * calibration. Scores are estimates; original true K8 replays remain required.
 */
public final class ActiveUniformResidualSelector {
    private ActiveUniformResidualSelector() { }

    public static final class Result {
        public final int[] queried, selected;
        public final double[][] commonPredictions;
        public final int readyCalls;
        public final double predictedHypervolume;
        Result(int[] queried,int[] selected,double[][] predicted,double hv) {
            this.queried=queried.clone();
            this.selected=selected.clone();
            this.commonPredictions=new double[predicted.length][];
            for(int i=0;i<predicted.length;i++)this.commonPredictions[i]=predicted[i].clone();
            this.readyCalls=queried.length;
            this.predictedHypervolume=hv;
        }
    }

    static void point(double[] x) {
        if(x==null||x.length!=2||!Double.isFinite(x[0])||!Double.isFinite(x[1])||
           x[0]<=0||x[1]<=0)
            throw new IllegalArgumentException("Only finite positive two-objective scores");
    }
    private static void check(double[][] old,IntFunction<double[]> oracle,
                              int t,int k,double[] reference) {
        if(old==null||old.length==0||oracle==null||reference==null||
           t<1||t>old.length||k<1||k>t)
            throw new IllegalArgumentException("Bad fixed T/K/READY callback");
        point(reference);
        for(double[] score:old)point(score);
    }
    private static double[] spans(double[][] old) {
        double[] min={Double.POSITIVE_INFINITY,Double.POSITIVE_INFINITY};
        double[] max={0.,0.};
        for(double[] p:old)for(int j=0;j<2;j++) {
            min[j]=Math.min(min[j],p[j]);
            max[j]=Math.max(max[j],p[j]);
        }
        return new double[]{Math.max(1e-12,max[0]-min[0]),
                            Math.max(1e-12,max[1]-min[1])};
    }
    static double squaredDistance(double[] a,double[] b,double[] span) {
        double x=(a[0]-b[0])/span[0],y=(a[1]-b[1])/span[1];
        return x*x+y*y;
    }
    /**
     * Deterministic 1-nearest-neighbor multiplicative residual, measured
     * against OLD in the shared normalized OLD objective geometry. A sampled
     * solution predicts exactly its READY estimate (zero self-distance).
     */
    static double[][] uniformPrediction(double[][] old,int[] picked,
                                        double[][] observed,double[] span) {
        if(picked.length==0)throw new IllegalArgumentException("No READY anchors");
        double[][] out=new double[old.length][2];
        for(int i=0;i<old.length;i++) {
            int nearest=0;
            double best=Double.POSITIVE_INFINITY;
            for(int j=0;j<picked.length;j++) {
                double distance=squaredDistance(old[i],old[picked[j]],span);
                if(distance<best) {best=distance;nearest=j;}
            }
            int anchor=picked[nearest];
            for(int axis=0;axis<2;axis++)
                out[i][axis]=old[i][axis]*(observed[nearest][axis]/old[anchor][axis]);
            point(out[i]);
        }
        // Make the exact READY observations authoritative at their own IDs,
        // including objective ties where cheap-scores of different IDs match.
        for(int j=0;j<picked.length;j++)out[picked[j]]=observed[j].clone();
        return out;
    }

    /**
     * First query = maximum OLD singleton HV (tie first index). Next queries
     * maximize OLD-normalized distance to nearest queried mapping, multiplied
     * by (1 + its nonnegative predicted marginal HV / measured-anchor HV).
     * No fitted parameter, lookahead, true labels, or duplicate READY call.
     */
    public static Result select(double[][] old,IntFunction<double[]> callback,
                                int t,int k,double[] reference) {
        check(old,callback,t,k,reference);
        double[] span=spans(old);
        int[] queried=new int[t];
        double[][] observations=new double[t][];
        boolean[] used=new boolean[old.length];
        queried[0]=GreedyStagedParetoSelector.select(old,1,reference).selected[0];
        for(int round=0;round<t;round++) {
            int id=queried[round];
            if(id<0||id>=old.length||used[id])
                throw new IllegalStateException("Repeated READY query");
            used[id]=true;
            double[] ready=callback.apply(id);
            point(ready);
            observations[round]=ready.clone();
            if(round+1>=t)break;
            int[] selected=Arrays.copyOf(queried,round+1);
            double[][] measured=Arrays.copyOf(observations,round+1);
            double[][] estimated=uniformPrediction(old,selected,measured,span);
            double base=GreedyStagedParetoSelector.normalizedHV(estimated,selected,reference);
            double bestValue=Double.NEGATIVE_INFINITY;
            int best=-1;
            for(int candidate=0;candidate<old.length;candidate++) {
                if(used[candidate])continue;
                double nearest=Double.POSITIVE_INFINITY;
                for(int anchor:selected)
                    nearest=Math.min(nearest,squaredDistance(old[candidate],old[anchor],span));
                int[] trial=Arrays.copyOf(selected,selected.length+1);
                trial[selected.length]=candidate;
                double gain=Math.max(0.,GreedyStagedParetoSelector.normalizedHV(
                        estimated,trial,reference)-base);
                double value=Math.sqrt(nearest)*(1.+gain/Math.max(1e-12,base));
                if(!Double.isFinite(value))
                    throw new IllegalStateException("Nonfinite acquisition score");
                if(value>bestValue+1e-12) {
                    bestValue=value;best=candidate;
                }
            }
            if(best<0)throw new IllegalStateException("No remaining READY candidate");
            queried[round+1]=best;
        }
        double[][] estimated=uniformPrediction(old,queried,observations,span);
        GreedyStagedParetoSelector.Selection selection=
                GreedyStagedParetoSelector.select(estimated,k,reference);
        return new Result(queried,selection.selected,estimated,
                          selection.predictedHypervolume);
    }
}
