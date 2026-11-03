package org.workflowsim.examples.planning;

import java.util.List;
import org.workflowsim.CondorVM;

/** Regression for explicitly opt-in within-tier heterogeneous VM speeds. */
public final class VMSpeedProfilesRegressionTest {
    private static void close(double actual,double expected) {
        if(Math.abs(actual-expected)>1e-10*Math.max(1.0,Math.abs(expected)))
            throw new AssertionError("VM speed mismatch "+actual+" != "+expected);
    }
    public static void main(String[] args) {
        String oldSpeed=System.getProperty("liwsa.vmSpeedProfile");
        String oldPrice=System.getProperty("liwsa.vmPriceProfile");
        try {
            double[] tiers={250,500,1000,2000};
            double[] prices={0.15,0.30,0.60,0.90};
            double[] factors={0.65,0.8,0.9,1.0};
            System.setProperty("liwsa.vmPriceProfile","default");
            System.setProperty("liwsa.vmSpeedProfile","default");
            List<CondorVM> baseline=LIWSABenchmarkExample.createVMs(1);
            if(baseline.size()!=16)throw new AssertionError("Expected 16 default VMs");
            for(int tier=0;tier<4;tier++)for(int k=0;k<4;k++){
                CondorVM vm=baseline.get(4*tier+k);
                close(vm.getMips(),tiers[tier]);
                close(vm.getCost(),prices[tier]);
                if(vm.getId()!=4*tier+k)throw new AssertionError("VM ID mismatch");
            }
            System.setProperty("liwsa.vmSpeedProfile","staggered");
            List<CondorVM> staggered=LIWSABenchmarkExample.createVMs(1);
            if(staggered.size()!=16)throw new AssertionError("Expected 16 staggered VMs");
            for(int tier=0;tier<4;tier++)for(int k=0;k<4;k++){
                CondorVM vm=staggered.get(4*tier+k);
                close(vm.getMips(),tiers[tier]*factors[k]);
                close(vm.getCost(),prices[tier]);
                if(vm.getId()!=4*tier+k)throw new AssertionError("VM ID mismatch");
            }
            System.setProperty("liwsa.vmPriceProfile","convex");
            List<CondorVM> convex=LIWSABenchmarkExample.createVMs(1);
            for(int tier=0;tier<4;tier++)for(int k=0;k<4;k++){
                CondorVM vm=convex.get(4*tier+k);
                close(vm.getCost(),0.15*Math.pow(vm.getMips()/250.,1.5));
            }
            System.setProperty("liwsa.vmSpeedProfile","invalid");
            boolean refused=false;
            try{LIWSABenchmarkExample.createVMs(1);}
            catch(IllegalArgumentException expected){refused=true;}
            if(!refused)throw new AssertionError("Invalid VM speed profile was accepted");
            System.out.println("PASS default and staggered MIPS, default/convex price matching, 16 IDs and invalid-profile fail-closed");
        }finally{
            if(oldSpeed==null)System.clearProperty("liwsa.vmSpeedProfile");
            else System.setProperty("liwsa.vmSpeedProfile",oldSpeed);
            if(oldPrice==null)System.clearProperty("liwsa.vmPriceProfile");
            else System.setProperty("liwsa.vmPriceProfile",oldPrice);
        }
    }
}
