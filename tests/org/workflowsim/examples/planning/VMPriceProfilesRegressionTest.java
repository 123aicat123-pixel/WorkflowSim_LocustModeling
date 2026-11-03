package org.workflowsim.examples.planning;

/**
 * Validates opt-in synthetic pricing scenarios without modifying the original
 * WorkflowSim VM configuration or default rates.
 */
public final class VMPriceProfilesRegressionTest {
    private static void eq(double observed,double expected) {
        if(Math.abs(observed-expected)>1e-10*Math.max(1.0,expected))
            throw new AssertionError("price mismatch: "+observed+" vs "+expected);
    }
    public static void main(String[] args) {
        String before=System.getProperty("liwsa.vmPriceProfile");
        try {
            double[] mips={250,500,1000,2000};
            double[] defaults={0.15,0.30,0.60,0.90};
            for(int i=0;i<mips.length;i++) {
                System.setProperty("liwsa.vmPriceProfile","default");
                eq(LIWSABenchmarkExample.vmPrice(mips[i],defaults[i]),defaults[i]);
                System.setProperty("liwsa.vmPriceProfile","linear");
                eq(LIWSABenchmarkExample.vmPrice(mips[i],defaults[i]),0.15*mips[i]/250.0);
                System.setProperty("liwsa.vmPriceProfile","convex");
                eq(LIWSABenchmarkExample.vmPrice(mips[i],defaults[i]),
                    0.15*Math.pow(mips[i]/250.0,1.5));
            }
            System.setProperty("liwsa.vmPriceProfile","invalid");
            boolean rejected=false;
            try { LIWSABenchmarkExample.vmPrice(250,0.15); }
            catch(IllegalArgumentException expected) {rejected=true;}
            if(!rejected)throw new AssertionError("invalid VM profile accepted");
            System.out.println("PASS default, linear and convex synthetic VM price invariants");
        } finally {
            if(before==null)System.clearProperty("liwsa.vmPriceProfile");
            else System.setProperty("liwsa.vmPriceProfile",before);
        }
    }
}
