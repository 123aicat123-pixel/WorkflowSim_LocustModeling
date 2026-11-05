package org.workflowsim.examples.planning;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import javax.xml.parsers.DocumentBuilderFactory;
import org.cloudbus.cloudsim.Log;
import org.workflowsim.planning.LIWSAPlanningAlgorithm;
import org.workflowsim.utils.Parameters;

/**
 * Expanded 32-item algorithm-independent, PREDECLARED mapping universe: both old and ready
 * planners forecast the SAME genotype, and original WorkflowSim produces
 * actual labels only AFTER these two planned predictions are frozen.
 * There is NO FLA/NSGA optimizer, learned source label or Pareto selection.
 */
public final class FLAFixedMappingUniverse32 {
    private FLAFixedMappingUniverse32(){}

    public static final String[] FROZEN_POLICIES={
        "all_vm0","all_vm12","round_robin","stride7",
        "evenodd_vm0_vm12","block4_vm0_vm12",
        "four_vm_round","four_vm_block5",
        "vm0_vm12_skew75","vm12_vm15_skew75",
        "prime_step5","prime_step11","hash_seed17","hash_seed97",
        "monotonic_vm16","reverse_monotonic_vm16",
        "cyclic_step3","cyclic_step9","two_vm_alt_3_11","two_vm_block3_3_11",
        "four_vm_shift_round","four_vm_shift_block","eight_vm_odd_round","eight_vm_odd_block",
        "vm0_vm12_skew90","vm12_vm15_skew90","reverse_round_robin","reverse_stride7",
        "hash_seed211","hash_seed307","monotonic_vm8","reverse_monotonic_vm8"
    };
    private static final int[] FOUR={0,4,8,12};
    private static final int[] FOUR_SHIFT={2,6,10,14};

    static int mixedHash(int taskId,int seed) {
        int x=taskId*0x9e3779b9 ^ seed;
        x^=x>>>16;
        x*=0x85ebca6b;
        x^=x>>>13;
        x*=0xc2b2ae35;
        x^=x>>>16;
        return (x&0x7fffffff)%16;
    }

    public static Map<Integer,Integer> mapping(int count,String policy) {
        if(count<2||count>500)throw new IllegalArgumentException("Invalid task count");
        Map<Integer,Integer> result=new java.util.TreeMap<>();
        for(int id=1;id<=count;id++) {
            int t=id-1,v;
            switch(policy) {
                case "all_vm0":v=0;break;
                case "all_vm12":v=12;break;
                case "round_robin":v=t%16;break;
                case "stride7":v=(7*t+3)%16;break;
                case "evenodd_vm0_vm12":v=t%2==0?0:12;break;
                case "block4_vm0_vm12":v=(t/4)%2==0?0:12;break;
                case "four_vm_round":v=FOUR[t%4];break;
                case "four_vm_block5":v=FOUR[(t/5)%4];break;
                case "vm0_vm12_skew75":v=t%4==0?12:0;break;
                case "vm12_vm15_skew75":v=t%4==0?15:12;break;
                case "prime_step5":v=(5*t+1)%16;break;
                case "prime_step11":v=(11*t+7)%16;break;
                case "hash_seed17":v=mixedHash(id,17);break;
                case "hash_seed97":v=mixedHash(id,97);break;
                case "monotonic_vm16":v=Math.min(15,16*t/count);break;
                case "reverse_monotonic_vm16":v=15-Math.min(15,16*t/count);break;
                case "cyclic_step3":v=(3*t+2)%16;break;
                case "cyclic_step9":v=(9*t+5)%16;break;
                case "two_vm_alt_3_11":v=t%2==0?3:11;break;
                case "two_vm_block3_3_11":v=(t/3)%2==0?3:11;break;
                case "four_vm_shift_round":v=FOUR_SHIFT[t%4];break;
                case "four_vm_shift_block":v=FOUR_SHIFT[(t/3)%4];break;
                case "eight_vm_odd_round":v=(2*t+1)%16;break;
                case "eight_vm_odd_block":v=(2*(t/3)+1)%16;break;
                case "vm0_vm12_skew90":v=t%10==0?12:0;break;
                case "vm12_vm15_skew90":v=t%10==0?15:12;break;
                case "reverse_round_robin":v=15-t%16;break;
                case "reverse_stride7":v=15-(7*t+3)%16;break;
                case "hash_seed211":v=mixedHash(id,211);break;
                case "hash_seed307":v=mixedHash(id,307);break;
                case "monotonic_vm8":v=2*Math.min(7,8*t/count);break;
                case "reverse_monotonic_vm8":v=15-2*Math.min(7,8*t/count);break;
                default:throw new IllegalArgumentException("Unsupported frozen VM mapping "+policy);
            }
            result.put(id,v);
        }
        return result;
    }

    private static String serialized(Map<Integer,Integer> m) {
        StringBuilder b=new StringBuilder();
        for(Map.Entry<Integer,Integer> e:new java.util.TreeMap<>(m).entrySet()){
            if(b.length()>0)b.append('|');
            b.append(e.getKey()).append(':').append(e.getValue());
        }
        return b.toString();
    }

    private static int daxCount(String workflow) throws Exception {
        Path dax=Paths.get("config/dax/"+workflow+".xml");
        if(!Files.isRegularFile(dax))throw new IllegalArgumentException("Missing DAX "+dax);
        DocumentBuilderFactory f=DocumentBuilderFactory.newInstance();
        f.setFeature("http://apache.org/xml/features/disallow-doctype-decl",true);
        f.setFeature("http://xml.org/sax/features/external-general-entities",false);
        f.setFeature("http://xml.org/sax/features/external-parameter-entities",false);
        int n=f.newDocumentBuilder().parse(dax.toFile()).getElementsByTagName("job").getLength();
        if(n<2||n>500)throw new IllegalArgumentException("Bad DAX task number "+n);
        return n;
    }

    private static void valid(String label,double value,boolean positive) {
        if(!Double.isFinite(value)||(positive?value<=0:value<0))
            throw new IllegalStateException("Invalid "+label+": "+value);
    }

    public static void main(String[] args) throws Exception {
        if(args.length!=2)throw new IllegalArgumentException(
                "Usage: FLAFixedMappingUniverse32 WORKFLOW OUTPUT_CSV");
        String workflow=args[0];
        if(!workflow.matches("[A-Za-z0-9_]+"))throw new IllegalArgumentException("Invalid DAX name");
        String profile=System.getProperty("liwsa.vmSpeedProfile","default");
        if(!profile.equals("default")&&!profile.equals("staggered"))
            throw new IllegalArgumentException("Unsupported VM speed profile "+profile);
        if(!Boolean.getBoolean("workflowsim.planningStageInAware")||
                !Boolean.getBoolean("dagfla.readyQueueDiagnostic")||
                !Boolean.getBoolean("dagfla.fixedTaskTrace")||
                !System.getProperty("dagfla.fixedVmReadyPriority","fifo").equals("fifo"))
            throw new IllegalArgumentException("This independent test needs stage-in, ready, full-task trace, actual FIFO runtime");
        int n=daxCount(workflow);
        Set<String> unique=new HashSet<>();
        for(String name:FROZEN_POLICIES) {
            String mapping=serialized(mapping(n,name));
            if(!unique.add(mapping))throw new IllegalStateException(
                "Duplicate frozen physical mapping; refuse to drop or replace "+name);
        }
        if(unique.size()!=32)throw new AssertionError("Not thirty-two algorithm-independent genotypes");
        Path output=Paths.get(args[1]);
        if(output.getParent()!=null)Files.createDirectories(output.getParent());
        Log.disable();
        try(BufferedWriter writer=Files.newBufferedWriter(output,StandardCharsets.UTF_8)){
            writer.write("workflow,vm_profile,seed,mapping_policy,task_count,"
                +"old_planned_makespan,old_planned_cost,"
                +"ready_planned_makespan,ready_planned_cost,"
                +"actual_makespan,actual_cost,"
                +"old_start_mae,ready_start_mae,old_finish_mae,ready_finish_mae,"
                +"task_vm_mapping");
            writer.newLine();
            for(String policy:FROZEN_POLICIES) {
                Map<Integer,Integer> assignment=mapping(n,policy);
                LIWSABenchmarkExample.RunResult truth=
                    LIWSABenchmarkExample.runPlanning(
                        "config/dax/"+workflow+".xml",
                        Parameters.PlanningAlgorithm.LIWSA,
                        Parameters.SchedulingAlgorithm.STATIC,
                        "independent_mapping_universe_"+profile+"_"+policy,
                        1501L,1,0,Collections.singletonList(assignment));
                LIWSAPlanningAlgorithm.LastRunMetrics plan=LIWSAPlanningAlgorithm.lastRun;
                if(truth==null||plan==null||truth.assignment==null||
                        !assignment.equals(truth.assignment))
                    throw new IllegalStateException("Original Task-to-VM mapping changed: "+policy);
                if(truth.fixedTaskActualTimeline==null||truth.fixedTaskActualTimeline.size()!=n||
                        plan.traceTaskIds==null||plan.traceTaskIds.length!=n||
                        plan.traceVmIds==null||plan.traceVmIds.length!=n||
                        plan.tracePlannedStarts==null||plan.tracePlannedStarts.length!=n||
                        plan.tracePlannedFinishes==null||plan.tracePlannedFinishes.length!=n||
                        plan.readyQueueStarts==null||plan.readyQueueStarts.length!=n||
                        plan.readyQueueFinishes==null||plan.readyQueueFinishes.length!=n)
                    throw new IllegalStateException("Missing original task-level simulator trace for "+policy);
                Set<Integer> seen=new HashSet<>();
                double oldStart=0,readyStart=0,oldFinish=0,readyFinish=0;
                for(int k=0;k<n;k++) {
                    int task=plan.traceTaskIds[k];
                    double[] real=truth.fixedTaskActualTimeline.get(task);
                    if(!seen.add(task)||real==null||assignment.get(task)==null||
                            plan.traceVmIds[k]!=assignment.get(task)||
                            (int)real[0]!=assignment.get(task))
                        throw new IllegalStateException("Wrong original task/VM identity: "+policy+" task "+task);
                    valid("task start",real[1],false);
                    valid("task finish",real[2],false);
                    if(real[2]<real[1])throw new IllegalStateException("Task finish earlier than start");
                    oldStart+=Math.abs(plan.tracePlannedStarts[k]-real[1]);
                    readyStart+=Math.abs(plan.readyQueueStarts[k]-real[1]);
                    oldFinish+=Math.abs(plan.tracePlannedFinishes[k]-real[2]);
                    readyFinish+=Math.abs(plan.readyQueueFinishes[k]-real[2]);
                }
                for(double v:new double[]{plan.stageInAwareMakespan,plan.stageInAwareCost,
                        plan.readyQueueMakespan,plan.readyQueueCost,
                        truth.makespan,truth.cost})
                    valid("planned or actual",v,true);
                writer.write(String.format(Locale.ROOT,
                    "%s,%s,1501,%s,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,"
                    +"%.17g,%.17g,%.17g,%.17g,%s",
                    workflow,profile,policy,n,
                    plan.stageInAwareMakespan,plan.stageInAwareCost,
                    plan.readyQueueMakespan,plan.readyQueueCost,
                    truth.makespan,truth.cost,
                    oldStart/n,readyStart/n,oldFinish/n,readyFinish/n,
                    serialized(assignment)));
                writer.newLine();writer.flush();
                System.out.printf(Locale.ROOT,
                    "FROZEN_MAP_UNIVERSE_PASS %s %s %s M_old=%.6f M_ready=%.6f M_sim=%.6f%n",
                    workflow,profile,policy,plan.stageInAwareMakespan,plan.readyQueueMakespan,truth.makespan);
            }
        }
        System.out.println("PASS thirty-two disjoint algorithm-independent source genotypes, per-task TaskID/VM identity and actual WorkflowSim traces");
    }
}
