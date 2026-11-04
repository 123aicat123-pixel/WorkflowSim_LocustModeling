package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.IntFunction;

/**
 * Pure, deterministic greedy 2-objective minimization HV screen/refine.
 * Research-only: no optimizer or simulator labels, no alteration of defaults.
 *
 * A caller MUST provide already-computed OLD scores and a truly lazy READY
 * callback, so exactly T expensive evaluations occur on selected candidates.
 */
public final class GreedyStagedParetoSelector {
    private GreedyStagedParetoSelector() {}
    private static final double TIE = 1e-12;

    public static final class Selection {
        public final int[] selected;
        public final double predictedHypervolume;
        Selection(int[] indices,double hv) {
            this.selected=indices.clone();this.predictedHypervolume=hv;
        }
    }
    public static final class Refined {
        public final int[] screened;
        public final int[] selected;
        public final int expensiveCalls;
        public final double predictedHypervolume;
        Refined(int[] first,int[] finalIndices,int calls,double hv) {
            screened=first.clone();selected=finalIndices.clone();
            expensiveCalls=calls;predictedHypervolume=hv;
        }
    }
    private static void check(double[][] scores,double[] reference) {
        if(scores==null||scores.length==0||reference==null||reference.length!=2||
                !Double.isFinite(reference[0])||!Double.isFinite(reference[1])||
                reference[0]<=0||reference[1]<=0)
            throw new IllegalArgumentException("Invalid two-objective reference or empty points");
        for(double[] v:scores)validate(v);
    }
    private static void validate(double[] value) {
        if(value==null||value.length!=2||!Double.isFinite(value[0])||
           !Double.isFinite(value[1])||value[0]<=0||value[1]<=0)
            throw new IllegalArgumentException("Only finite positive 2D predictions allowed");
    }

    public static double normalizedHV(double[][] scores,int[] indices,double[] reference) {
        check(scores,reference);
        if(indices==null)throw new IllegalArgumentException("Missing selected indices");
        List<double[]> points=new ArrayList<>();
        Set<Integer> used=new HashSet<>();
        for(int i:indices) {
            if(i<0||i>=scores.length||!used.add(i))
                throw new IllegalArgumentException("Invalid or duplicate candidate index");
            if(scores[i][0]<reference[0]&&scores[i][1]<reference[1])
                points.add(scores[i]);
        }
        points.sort((a,b)->{
            int c=Double.compare(a[0],b[0]);
            return c!=0?c:Double.compare(a[1],b[1]);
        });
        double last=reference[1],area=0.;
        for(double[] p:points) {
            if(p[1]>=last)continue;
            area+=(reference[0]-p[0])*(last-p[1]);
            last=p[1];
        }
        double result=area/(reference[0]*reference[1]);
        if(!Double.isFinite(result)||result<0||result>1+1e-8)
            throw new IllegalStateException("Invalid HV score");
        return result;
    }

    public static Selection select(double[][] scores,int quota,double[] reference) {
        check(scores,reference);
        if(quota<1||quota>scores.length)
            throw new IllegalArgumentException("Invalid K/T quota");
        int[] selected=new int[quota];
        boolean[] used=new boolean[scores.length];
        for(int position=0;position<quota;position++) {
            int best=-1;
            double bestValue=-1.0;
            for(int index=0;index<scores.length;index++) {
                if(used[index])continue;
                selected[position]=index;
                int[] current=Arrays.copyOf(selected,position+1);
                double value=normalizedHV(scores,current,reference);
                if(best<0||value>bestValue+TIE) {
                    best=index;bestValue=value;
                }
            }
            if(best<0)throw new IllegalStateException("No feasible greedy candidate");
            selected[position]=best;
            used[best]=true;
        }
        return new Selection(selected,normalizedHV(scores,selected,reference));
    }

    public static Refined refine(double[][] oldScores,IntFunction<double[]> readyEvaluator,
                                int screenQuota,int finalQuota,double[] reference) {
        check(oldScores,reference);
        if(readyEvaluator==null||finalQuota<1||screenQuota<finalQuota||
           screenQuota>oldScores.length)
            throw new IllegalArgumentException("Invalid staged budget/callback");
        Selection shortlist=select(oldScores,screenQuota,reference);
        double[][] hybrid=new double[oldScores.length][];
        for(int i=0;i<hybrid.length;i++)hybrid[i]=oldScores[i].clone();
        int count=0;
        for(int index:shortlist.selected) {
            double[] improved=readyEvaluator.apply(index);
            validate(improved);
            hybrid[index]=improved.clone();
            count++;
        }
        Selection finish=select(hybrid,finalQuota,reference);
        return new Refined(shortlist.selected,finish.selected,count,
                           finish.predictedHypervolume);
    }
}
