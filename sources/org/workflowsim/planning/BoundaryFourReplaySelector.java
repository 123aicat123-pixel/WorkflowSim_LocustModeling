package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Random;

/**
 * Opt-in planning-only K12+4 replay explorer.
 *
 * Does not call READY, the real simulator, or any fitness evaluator.
 * Scores are two strictly positive minimized objectives.
 * It requires at least four DISTINCT candidate identities that are
 * strictly dominated by one of the original K12 selected candidates.
 */
public final class BoundaryFourReplaySelector {
    private BoundaryFourReplaySelector() {}

    public enum Policy { BOUNDARY, STRATIFIED_RANDOM }

    public static final class Result {
        public final int[] indices;
        public final int[] stratumSizes;
        public final int dominatedEligible;
        Result(int[] picks, int[] sizes, int eligible) {
            indices = picks.clone();
            stratumSizes = sizes.clone();
            dominatedEligible = eligible;
        }
    }

    private static boolean dominates(double[] x, double[] y) {
        return x[0] <= y[0] && x[1] <= y[1] &&
               (x[0] < y[0] || x[1] < y[1]);
    }

    private static void check(double[][] scores, String[] ids, int[] first,
                              Policy policy, Random rng) {
        if (scores == null || ids == null || first == null ||
            scores.length != ids.length || scores.length < 16 ||
            first.length != 12 || policy == null || rng == null)
            throw new IllegalArgumentException("K12+4 dimensions or mode invalid");
        java.util.HashSet<String> seen = new java.util.HashSet<>();
        for (int i=0; i<scores.length; i++) {
            double[] x=scores[i];
            if (x==null || x.length!=2 ||
                !Double.isFinite(x[0]) || !Double.isFinite(x[1]) ||
                x[0]<=0 || x[1]<=0 ||
                ids[i]==null || !seen.add(ids[i]))
                throw new IllegalArgumentException("Invalid objective or duplicate mapping");
        }
        boolean[] selected=new boolean[scores.length];
        for (int i:first) {
            if (i<0 || i>=scores.length || selected[i])
                throw new IllegalArgumentException("Nonunique K12 baseline");
            selected[i]=true;
        }
    }

    /**
     * Quantile division by deterministic planned-makespan order.
     * Each eligible mapping appears in exactly one stratum, where the
     * first (eligibleCount % 4) strata receive one extra member.
     * Score = minimum normalized max-axis positive domination margin
     * relative to any of the twelve original planned cover anchors.
     */
    public static Result select(double[][] scores, String[] ids, int[] first,
                                Policy policy, Random rng) {
        check(scores,ids,first,policy,rng);
        boolean[] chosen=new boolean[scores.length];
        for (int index:first)chosen[index]=true;
        ArrayList<Integer> candidates=new ArrayList<>();
        double minM=Double.POSITIVE_INFINITY,maxM=Double.NEGATIVE_INFINITY;
        double minC=Double.POSITIVE_INFINITY,maxC=Double.NEGATIVE_INFINITY;
        for (double[] x:scores) {
            minM=Math.min(minM,x[0]); maxM=Math.max(maxM,x[0]);
            minC=Math.min(minC,x[1]); maxC=Math.max(maxC,x[1]);
        }
        final double dm=Math.max(1e-12,maxM-minM);
        final double dc=Math.max(1e-12,maxC-minC);
        for (int i=0;i<scores.length;i++) {
            if(chosen[i])continue;
            for(int original:first) {
                if(dominates(scores[original],scores[i])) {
                    candidates.add(i);
                    break;
                }
            }
        }
        if(candidates.size()<4)
            throw new IllegalStateException("Not enough original-K12-dominated assignments");
        candidates.sort(Comparator
            .comparingDouble((Integer i)->scores[i][0])
            .thenComparingDouble(i->scores[i][1])
            .thenComparing(i->ids[i]));
        int[] out=Arrays.copyOf(first,16);
        int[] sizes=new int[4];
        int start=0;
        for(int stratum=0;stratum<4;stratum++) {
            int size=candidates.size()/4 + (stratum < candidates.size()%4 ? 1:0);
            sizes[stratum]=size;
            int picked=-1;
            if(policy==Policy.STRATIFIED_RANDOM) {
                picked=candidates.get(start+rng.nextInt(size));
            } else {
                double nearest=Double.POSITIVE_INFINITY;
                for(int j=start;j<start+size;j++) {
                    int candidate=candidates.get(j);
                    double margin=Double.POSITIVE_INFINITY;
                    for(int original:first) {
                        if(!dominates(scores[original],scores[candidate]))continue;
                        double a=(scores[candidate][0]-scores[original][0])/dm;
                        double b=(scores[candidate][1]-scores[original][1])/dc;
                        margin=Math.min(margin,Math.max(a,b));
                    }
                    if(picked<0 || margin<nearest-1e-12 ||
                       (Math.abs(margin-nearest)<=1e-12 &&
                           ids[candidate].compareTo(ids[picked])<0)) {
                        picked=candidate;
                        nearest=margin;
                    }
                }
            }
            if(picked<0 || chosen[picked])
                throw new IllegalStateException("Invalid stratum selection");
            chosen[picked]=true;
            out[12+stratum]=picked;
            start+=size;
        }
        if(start!=candidates.size())
            throw new IllegalStateException("Uncovered eligible stratum");
        return new Result(out,sizes,candidates.size());
    }
}
