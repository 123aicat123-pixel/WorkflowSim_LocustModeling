package org.workflowsim.examples.planning;

import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/** Source-only identity checks on all 16 frozen algorithm-independent mappings. */
public final class FLAAlgorithmIndependentMappingUniverseTest {
    public static void main(String[] args) {
        for(int n:new int[]{24,30,46,50,60,100}) {
            Set<String> fingerprints=new HashSet<>();
            for(String policy:FLAAlgorithmIndependentMappingUniverse.FROZEN_POLICIES) {
                Map<Integer,Integer> m=FLAAlgorithmIndependentMappingUniverse.mapping(n,policy);
                if(m.size()!=n)throw new AssertionError("Missing task assignment");
                StringBuilder fingerprint=new StringBuilder();
                for(int task=1;task<=n;task++){
                    Integer vm=m.get(task);
                    if(vm==null||vm<0||vm>=16)throw new AssertionError("Out-of-range VM mapping");
                    fingerprint.append(task).append(':').append(vm).append('|');
                }
                if(!fingerprints.add(fingerprint.toString()))
                    throw new AssertionError("Repeated policy fingerprint for n="+n+": "+policy);
            }
            if(fingerprints.size()!=16)throw new AssertionError("Not 16 unique frozen maps");
            if(FLAAlgorithmIndependentMappingUniverse.mapping(n,"all_vm0").get(1)!=0||
               FLAAlgorithmIndependentMappingUniverse.mapping(n,"all_vm12").get(n)!=12||
               FLAAlgorithmIndependentMappingUniverse.mapping(n,"stride7").get(1)!=3||
               FLAAlgorithmIndependentMappingUniverse.mapping(n,"round_robin").get(16)!=15)
                throw new AssertionError("Changed historical four mapping sources");
        }
        boolean rejected=false;
        try{FLAAlgorithmIndependentMappingUniverse.mapping(30,"best-from-real-HV");}
        catch(IllegalArgumentException expected){rejected=true;}
        if(!rejected)throw new AssertionError("Accepted unregistered post-outcome mapping policy");
        System.out.println("PASS 16 unique deterministic VM mappings, six independent task sizes, historical parity and reject unregistered policy");
    }
}
