package org.workflowsim.examples.planning;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.cloudbus.cloudsim.Log;
import org.workflowsim.planning.LIWSAPlanningAlgorithm;
import org.workflowsim.utils.Parameters;
import javax.xml.parsers.DocumentBuilderFactory;

/** Independent deterministic fixed-genotype prospective DAG-generalization audit. */
public final class FLAReadyQueueCrossDagAudit {
    private FLAReadyQueueCrossDagAudit(){}
    private static int countOriginalDaxTasks(String workflow) throws Exception {
        Path path=Paths.get("config/dax/"+workflow+".xml");
        if(!Files.isRegularFile(path))throw new IllegalArgumentException("Missing DAX "+path);
        DocumentBuilderFactory factory=DocumentBuilderFactory.newInstance();
        // No outside entities or DTD from untrusted DAX content.
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl",true);
        factory.setFeature("http://xml.org/sax/features/external-general-entities",false);
        factory.setFeature("http://xml.org/sax/features/external-parameter-entities",false);
        int n=factory.newDocumentBuilder().parse(path.toFile())
                .getElementsByTagName("job").getLength();
        if(n<2||n>500)throw new IllegalArgumentException("Unexpected DAX task count "+n);
        return n;
    }
    static Map<Integer,Integer> mapping(int n,String policy) {
        Map<Integer,Integer> out=new HashMap<>();
        for(int task=1;task<=n;task++) {
            int vm;
            switch(policy) {
                case "all_vm0":vm=0;break;
                case "all_vm12":vm=12;break;
                case "round_robin":vm=(task-1)%16;break;
                case "stride7":vm=(7*(task-1)+3)%16;break;
                default:throw new IllegalArgumentException("Unknown mapping policy "+policy);
            }
            out.put(task,vm);
        }
        return out;
    }
    public static void main(String[] args) throws Exception {
        if(args.length!=2 && args.length!=3)throw new IllegalArgumentException(
            "Usage: FLAReadyQueueCrossDagAudit WORKFLOW OUTPUT_CSV [ONE_FROZEN_MAPPING_POLICY]");
        String workflow=args[0];
        if(!workflow.matches("[A-Za-z0-9_]+"))
            throw new IllegalArgumentException("Untrusted DAX name");
        String speed=System.getProperty("liwsa.vmSpeedProfile","default");
        if(!"default".equals(speed)&&!"staggered".equals(speed))
            throw new IllegalArgumentException("Unsupported VM profile");
        int tasks=countOriginalDaxTasks(workflow);
        Path path=Paths.get(args[1]);
        if(path.getParent()!=null)Files.createDirectories(path.getParent());
        String[] policies=args.length==3?new String[]{args[2]}:
                new String[]{"all_vm0","all_vm12","round_robin","stride7"};
        // Validate BEFORE starting any simulation, including the optional
        // single-policy mechanism probe; original 2-argument behavior unchanged.
        for(String policy:policies) mapping(tasks,policy);
        Log.disable();
        try(BufferedWriter out=Files.newBufferedWriter(path,StandardCharsets.UTF_8)) {
            out.write("workflow,speed,seed,policy,task_count,"
                    +"old_plan_makespan,new_ready_makespan,actual_makespan,"
                    +"old_plan_cost,new_ready_cost,actual_cost,"
                    +"old_start_mae,new_start_mae,old_finish_mae,new_finish_mae,"
                    +"old_makespan_abs_pct,new_makespan_abs_pct,"
                    +"old_cost_abs_pct,new_cost_abs_pct\n");
            for(String policy:policies) {
                Map<Integer,Integer> genotype=mapping(tasks,policy);
                LIWSABenchmarkExample.RunResult real=
                    LIWSABenchmarkExample.runPlanning(
                        "config/dax/"+workflow+".xml",
                        Parameters.PlanningAlgorithm.LIWSA,
                        Parameters.SchedulingAlgorithm.STATIC,
                        "ready_dag_gate_"+speed+"_"+policy,
                        509L,1,0,Collections.singletonList(genotype));
                LIWSAPlanningAlgorithm.LastRunMetrics m=LIWSAPlanningAlgorithm.lastRun;
                if(real==null||m==null||real.assignment==null||
                        !real.assignment.equals(genotype))
                    throw new IllegalStateException("Actual VM map mismatch "+workflow+" "+policy);
                if(real.fixedTaskActualTimeline==null||
                        real.fixedTaskActualTimeline.size()!=tasks||
                        m.traceTaskIds==null||m.traceTaskIds.length!=tasks||
                        m.readyQueueStarts==null||m.readyQueueStarts.length!=tasks||
                        m.readyQueueFinishes==null||m.readyQueueFinishes.length!=tasks)
                    throw new IllegalStateException("Incomplete fixed Task-ID trace");
                double oldStart=0,newStart=0,oldFinish=0,newFinish=0;
                java.util.HashSet<Integer> seen=new java.util.HashSet<>();
                for(int k=0;k<tasks;k++) {
                    int tid=m.traceTaskIds[k];
                    double[] observed=real.fixedTaskActualTimeline.get(tid);
                    if(!seen.add(tid)||observed==null||
                            genotype.get(tid)==null||
                            genotype.get(tid)!=m.traceVmIds[k]||
                            m.traceVmIds[k]!=(int)observed[0])
                        throw new IllegalStateException("Original Task ID / VM mismatch "+tid);
                    oldStart+=Math.abs(m.tracePlannedStarts[k]-observed[1]);
                    newStart+=Math.abs(m.readyQueueStarts[k]-observed[1]);
                    oldFinish+=Math.abs(m.tracePlannedFinishes[k]-observed[2]);
                    newFinish+=Math.abs(m.readyQueueFinishes[k]-observed[2]);
                }
                double[] v={m.stageInAwareMakespan,m.readyQueueMakespan,real.makespan,
                    m.stageInAwareCost,m.readyQueueCost,real.cost,
                    oldStart,newStart,oldFinish,newFinish};
                for(double x:v)if(!Double.isFinite(x)||x<0)
                    throw new IllegalStateException("Invalid independent forecast or simulator truth");
                if(!(real.makespan>0)||!(real.cost>0))
                    throw new IllegalStateException("Invalid real simulator makespan or cost");
                out.write(String.format(Locale.ROOT,
                    "%s,%s,509,%s,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,"
                    +"%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g%n",
                    workflow,speed,policy,tasks,
                    m.stageInAwareMakespan,m.readyQueueMakespan,real.makespan,
                    m.stageInAwareCost,m.readyQueueCost,real.cost,
                    oldStart/tasks,newStart/tasks,oldFinish/tasks,newFinish/tasks,
                    100*Math.abs(m.stageInAwareMakespan-real.makespan)/real.makespan,
                    100*Math.abs(m.readyQueueMakespan-real.makespan)/real.makespan,
                    100*Math.abs(m.stageInAwareCost-real.cost)/real.cost,
                    100*Math.abs(m.readyQueueCost-real.cost)/real.cost));
                out.flush();
                System.out.printf(Locale.ROOT,
                    "CROSS_DAG_PASS workflow=%s speed=%s policy=%s old=%.7f%% new=%.7f%%%n",
                    workflow,speed,policy,
                    100*Math.abs(m.stageInAwareMakespan-real.makespan)/real.makespan,
                    100*Math.abs(m.readyQueueMakespan-real.makespan)/real.makespan);
            }
        }
        System.out.println("PASS "+policies.length+
            " independent original-DAX-identity VM allocations, real simulator truth and passive new decoder");
    }
}
