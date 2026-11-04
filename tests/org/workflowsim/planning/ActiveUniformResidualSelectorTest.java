package org.workflowsim.planning;

import java.util.Arrays;
import java.util.concurrent.atomic.AtomicInteger;

/** Mathematical test with synthetic READY labels; NOT true simulator evidence. */
public final class ActiveUniformResidualSelectorTest {
    private static void require(boolean ok,String message) {
        if(!ok)throw new AssertionError(message);
    }
    private static double[][] old() {
        return new double[][] {
            {10,50},{15,42},{20,35},{27,28},
            {33,23},{41,19},{48,15},{55,11}
        };
    }
    public static void main(String[] args) {
        double[] ref={100,100};
        double[][] initial=old();
        AtomicInteger calls=new AtomicInteger();
        java.util.Set<Integer> queried=new java.util.HashSet<>();
        ActiveUniformResidualSelector.Result result=
            ActiveUniformResidualSelector.select(initial,id->{
                require(queried.add(id),"Duplicate READY oracle access");
                calls.incrementAndGet();
                return new double[]{initial[id][0]*1.10,
                                    initial[id][1]*0.95};
            },4,3,ref);
        require(calls.get()==4&&queried.size()==4&&result.readyCalls==4,
                "READY physical budget incorrect");
        require(result.queried.length==4&&result.selected.length==3,
                "Wrong dimensions");
        for(int id:result.queried) {
            require(queried.contains(id),"Missing queried ID");
            require(Math.abs(result.commonPredictions[id][0]-initial[id][0]*1.10)<1e-9,
                    "Queried anchor not exactly preserved");
        }
        for(int i=0;i<initial.length;i++) {
            require(Math.abs(result.commonPredictions[i][0]-initial[i][0]*1.10)<1e-9 &&
                    Math.abs(result.commonPredictions[i][1]-initial[i][1]*0.95)<1e-9,
                    "Common-scale residual prediction is inconsistent");
        }
        ActiveUniformResidualSelector.Result again=
            ActiveUniformResidualSelector.select(initial,id->new double[]{
                initial[id][0]*1.10,initial[id][1]*0.95
            },4,3,ref);
        require(Arrays.equals(result.queried,again.queried) &&
                Arrays.equals(result.selected,again.selected),
                "Fixed active selector is not deterministic");
        require(result.predictedHypervolume>=0&&
                Double.isFinite(result.predictedHypervolume),"HV invalid");
        require(initial[0][0]==10&&initial[0][1]==50,
                "Input OLD scores changed");
        result.commonPredictions[0][0]=-1;
        require(initial[0][0]==10,"Result leaked to caller input");
        boolean rejected=false;
        try {ActiveUniformResidualSelector.select(old(),id->new double[]{
            Double.NaN,1},2,1,ref);}
        catch(IllegalArgumentException correct){rejected=true;}
        require(rejected,"Invalid READY score accepted");
        rejected=false;
        try {ActiveUniformResidualSelector.select(old(),id->new double[]{
            1,1},2,3,ref);}
        catch(IllegalArgumentException correct){rejected=true;}
        require(rejected,"T<K accepted");
        System.out.println("PASS ActiveUniformResidualSelectorTest: fixed T budget, uniform corrected scale, deterministic selection and invalid oracle rejection");
    }
}
