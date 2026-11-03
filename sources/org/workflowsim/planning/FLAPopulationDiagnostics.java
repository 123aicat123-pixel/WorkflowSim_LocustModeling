package org.workflowsim.planning;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/**
 * No simulator, evaluator or RNG. Exact genotype slot counts of a selected
 * breeding population (not the distinct history of evaluated candidates).
 */
public final class FLAPopulationDiagnostics {
    private FLAPopulationDiagnostics() {}

    /**
     * Return [population size, unique all, duplicate slots, unique group1,
     * unique group2, overlapping distinct genotypes across groups,
     * normalized mean pairwise Hamming all, group1, group2].
     */
    public static double[] describe(int[][] first,int[][] second) {
        if(first==null||second==null||first.length==0||second.length==0)
            throw new IllegalArgumentException("Both subgroups must be nonempty");
        int n=first[0].length;
        if(n==0)throw new IllegalArgumentException("Empty genotype");
        for(int[] g:first)
            if(g==null||g.length!=n)throw new IllegalArgumentException("Invalid first subgroup");
        for(int[] g:second)
            if(g==null||g.length!=n)throw new IllegalArgumentException("Invalid second subgroup");
        Set<String> u1=new HashSet<>(),u2=new HashSet<>();
        for(int[] g:first)u1.add(Arrays.toString(g));
        for(int[] g:second)u2.add(Arrays.toString(g));
        Set<String> combined=new HashSet<>(u1);combined.addAll(u2);
        int overlap=u1.size()+u2.size()-combined.size();
        int[][] all=new int[first.length+second.length][];
        System.arraycopy(first,0,all,0,first.length);
        System.arraycopy(second,0,all,first.length,second.length);
        return new double[]{
            all.length,combined.size(),all.length-combined.size(),u1.size(),
            u2.size(),overlap,pairHamming(all),pairHamming(first),pairHamming(second)};
    }

    public static double pairHamming(int[][] genes) {
        if(genes==null||genes.length==0)throw new IllegalArgumentException("Empty population");
        int n=genes[0].length;
        if(n==0)throw new IllegalArgumentException("Empty genotype");
        for(int[] g:genes)
            if(g==null||g.length!=n)throw new IllegalArgumentException("Ragged genotype");
        if(genes.length==1)return 0.;
        long disagree=0;
        for(int i=0;i<genes.length;i++)
            for(int j=i+1;j<genes.length;j++)
                for(int k=0;k<n;k++)
                    if(genes[i][k]!=genes[j][k])disagree++;
        return disagree/((double)n*genes.length*(genes.length-1)/2);
    }
}
