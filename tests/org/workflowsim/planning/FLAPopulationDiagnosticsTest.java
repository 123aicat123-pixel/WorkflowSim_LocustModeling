package org.workflowsim.planning;

import java.util.Arrays;

/** Pure exact slot-count oracle, no optimizer, no RNG, no fitness calls. */
public final class FLAPopulationDiagnosticsTest {
    private FLAPopulationDiagnosticsTest() {}
    private static void eq(String msg,double a,double b){
        if(!Double.isFinite(a)||Math.abs(a-b)>1e-10)
            throw new AssertionError(msg+" expected "+b+" actual "+a);
    }
    public static void main(String[] args) {
        int[][] g1={{0,0},{0,0}};
        int[][] g2={{1,1},{1,0}};
        int[][] g1Copy={{0,0},{0,0}};
        double[] d=FLAPopulationDiagnostics.describe(g1,g2);
        eq("slots",d[0],4);eq("unique selected",d[1],3);
        eq("duplicates",d[2],1);eq("unique first",d[3],1);
        eq("unique second",d[4],2);eq("overlap",d[5],0);
        eq("pairwise disagreement",d[6],7./12.);
        eq("first group disagreement",d[7],0);
        eq("second group disagreement",d[8],0.5);
        if(!Arrays.deepEquals(g1,g1Copy))
            throw new AssertionError("Diagnostic must not mutate genotype");
        int[][] c={{0,1},{1,0}},e={{0,1},{1,0}};
        double[] o=FLAPopulationDiagnostics.describe(c,e);
        eq("cross group overlapping distinct",o[5],2);
        eq("overlap union",o[1],2);
        eq("overlap duplicates",o[2],2);
        boolean bad=false;
        try{FLAPopulationDiagnostics.describe(new int[][]{{0}},new int[][]{{1,2}});}
        catch(IllegalArgumentException expected){bad=true;}
        if(!bad)throw new AssertionError("Ragged genotype must fail closed");
        System.out.println("PASS exact selected population unique/duplicate/overlap/Hamming and read-only invariants");
    }
}
