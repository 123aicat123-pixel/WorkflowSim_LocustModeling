package org.workflowsim.planning;

import java.util.Arrays;
import java.util.List;
import java.util.Random;

/**
 * v20 opt-in proposal-only novelty control.
 * The score is the minimum normalized Hamming distance to the CURRENT
 * breeding population, not duplicate detection or objective-space diversity.
 * Produces exactly four non-fitness VM proposals when triggered.
 */
public final class FrontierNoveltyProposal {
    private FrontierNoveltyProposal() {}
    public enum Source { RANDOM, DAG_EDGE }
    public static final class Result {
        public final int[] genes;
        public final int proposalsChanged;
        public final double minHamming;
        Result(int[] genes,int changed,double distance) {
            this.genes=genes.clone();proposalsChanged=changed;minHamming=distance;
        }
    }
    private static void verify(int[] base,int[][] allowed,int[][] parents,
                               int[] edgeParent,int[] edgeChild,double[] costs) {
        if(base==null||base.length==0||allowed==null||allowed.length!=base.length||
           parents==null||parents.length==0||costs==null||costs.length==0||
           edgeParent==null||edgeChild==null||edgeParent.length!=edgeChild.length)
            throw new IllegalArgumentException("Invalid novelty context");
        for(int task=0;task<base.length;task++) {
            if(allowed[task]==null||allowed[task].length==0)
                throw new IllegalArgumentException("No allowed VM");
            boolean present=false;
            for(int vm:allowed[task]) {
                if(vm<0||vm>=costs.length)throw new IllegalArgumentException("Invalid VM option");
                if(vm==base[task])present=true;
            }
            if(!present)throw new IllegalArgumentException("Base genotype violates VM options");
        }
        for(int[] parent:parents)
            if(parent==null||parent.length!=base.length)
                throw new IllegalArgumentException("Bad parent dimensions");
        for(int j=0;j<edgeParent.length;j++)
            if(edgeParent[j]<0||edgeChild[j]<0||
               edgeParent[j]>=base.length||edgeChild[j]>=base.length)
                throw new IllegalArgumentException("Invalid DAG edge");
        for(double price:costs)
            if(!Double.isFinite(price)||price<0)
                throw new IllegalArgumentException("Invalid VM price");
    }
    private static int changedVm(int current,int[] options,Random random) {
        int size=0;
        for(int v:options)if(v!=current)size++;
        if(size==0)return current;
        int target=random.nextInt(size);
        for(int v:options)if(v!=current && target--==0)return v;
        throw new AssertionError("VM choice count mismatch");
    }
    private static boolean allows(int[] options,int vm) {
        for(int value:options)if(value==vm)return true;
        return false;
    }
    static double minHamming(int[] genes,int[][] population) {
        double distance=1;
        for(int[] parent:population) {
            int mismatch=0;
            for(int k=0;k<genes.length;k++)if(genes[k]!=parent[k])mismatch++;
            distance=Math.min(distance,(double)mismatch/genes.length);
        }
        return distance;
    }
    /**
     * Both arms use four independent proposals and exactly the same
     * distance comparator. Neither arm calls ANY fitness/simulator decoder.
     */
    public static Result propose(int[] base,int[][] allowed,int[][] population,
                                 int[] edgeParent,int[] edgeChild,double[] vmCosts,
                                 boolean makespanGroup,Source source,Random rng) {
        if(rng==null||source==null)throw new IllegalArgumentException("Missing proposal mode/RNG");
        verify(base,allowed,population,edgeParent,edgeChild,vmCosts);
        int[] best=base.clone();
        double bestScore=Double.NEGATIVE_INFINITY;
        int changed=0;
        for(int proposal=0;proposal<4;proposal++) {
            int[] candidate=base.clone();
            if(source==Source.DAG_EDGE && edgeParent.length>0) {
                int edge=rng.nextInt(edgeParent.length);
                int p=edgeParent[edge],task=edgeChild[edge];
                if(makespanGroup) {
                    int colocate=candidate[p];
                    if(colocate!=candidate[task]&&allows(allowed[task],colocate))
                        candidate[task]=colocate;
                } else {
                    int cheapest=candidate[task];
                    double cost=Double.POSITIVE_INFINITY;
                    for(int vm:allowed[task])
                        if(vmCosts[vm]<cost-1e-12 ||
                           (Math.abs(vmCosts[vm]-cost)<=1e-12 && vm<cheapest)) {
                            cheapest=vm;cost=vmCosts[vm];
                        }
                    candidate[task]=cheapest;
                }
                // Ensure the two arms test REAL alternative assignments.
                if(Arrays.equals(candidate,base)) {
                    int k=task;
                    candidate[k]=changedVm(candidate[k],allowed[k],rng);
                }
            } else {
                int k=rng.nextInt(base.length);
                candidate[k]=changedVm(candidate[k],allowed[k],rng);
            }
            if(!Arrays.equals(candidate,base))changed++;
            double score=minHamming(candidate,population);
            if(score>bestScore+1e-12) {
                bestScore=score;
                best=candidate;
            }
        }
        return new Result(best,changed,bestScore);
    }
}
