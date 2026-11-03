package org.workflowsim.examples.planning;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import org.cloudbus.cloudsim.Log;
import org.workflowsim.planning.LIWSAPlanningAlgorithm;
import org.workflowsim.utils.Parameters;

/**
 * Research-only, fixed-genotype matched replay. Consumes ORIGINAL immutable
 * v17 cover-selected assignments from CSV and replays the SAME assignments
 * under the selected -Dliwsa.vmSpeedProfile. Does not run a new FLA/NSGA-II
 * optimization or pick assignments using simulator labels.
 *
 * CSV input is from FLAResearchExperiment and mapping values are VM IDs.
 */
public final class FLAFixedMappingReplay {
    private FLAFixedMappingReplay() {}

    static Map<Integer,Integer> parseMapping(String raw) {
        if (raw == null || raw.isEmpty()) throw new IllegalArgumentException("Empty mapping");
        Map<Integer,Integer> mapping=new TreeMap<>();
        for(String pair:raw.split("\\|",-1)) {
            String[] parts=pair.split(":",-1);
            if(parts.length!=2) throw new IllegalArgumentException("Malformed mapping pair");
            int task=Integer.parseInt(parts[0]);
            int vm=Integer.parseInt(parts[1]);
            if(task<0 || vm<0 || vm>=16 || mapping.put(task,vm)!=null)
                throw new IllegalArgumentException("Bad/duplicate mapping task or VM: "+pair);
        }
        return mapping;
    }

    private static int index(String[] columns,String wanted) {
        for(int i=0;i<columns.length;i++)
            if(wanted.equals(columns[i])) return i;
        throw new IllegalArgumentException("Missing original replay column: "+wanted);
    }

    private static double positive(String raw) {
        double value=Double.parseDouble(raw);
        if(!Double.isFinite(value) || value<=0)
            throw new IllegalArgumentException("Invalid simulator/planner numeric field");
        return value;
    }

    public static void main(String[] args) throws Exception {
        if(args.length!=6) throw new IllegalArgumentException(
            "Usage: FLAFixedMappingReplay WORKFLOW SEED ORIGINAL_REPLAYS_CSV ALGORITHM LIMIT OUTPUT_CSV");
        String workflow=args[0];
        long seed=Long.parseLong(args[1]);
        Path input=Paths.get(args[2]),output=Paths.get(args[5]);
        String algorithm=args[3],profile=System.getProperty("liwsa.vmSpeedProfile","default");
        if(!"default".equals(profile) && !"staggered".equals(profile))
            throw new IllegalArgumentException("Invalid VM speed profile: "+profile);
        int limit=Integer.parseInt(args[4]);
        if(limit<1 || limit>16)throw new IllegalArgumentException("Limit outside original K16");
        List<String> lines=Files.readAllLines(input,StandardCharsets.UTF_8);
        if(lines.size()<2)throw new IllegalArgumentException("Empty source replay CSV");
        String[] header=lines.get(0).split(",",-1);
        int wfIndex=index(header,"workflow"),algIndex=index(header,"algorithm");
        int seedIndex=index(header,"seed"),posIndex=index(header,"candidate_index");
        int mappingIndex=index(header,"mapping");
        int originalPlannedM=index(header,"planned_makespan");
        int originalPlannedC=index(header,"planned_cost");
        int originalRealM=index(header,"sim_makespan");
        int originalRealC=index(header,"sim_cost");
        Map<Integer,String[]> selected=new TreeMap<>();
        for(int i=1;i<lines.size();i++) {
            String[] fields=lines.get(i).split(",",-1);
            if(fields.length!=header.length)
                throw new IllegalArgumentException("Bad CSV field count line "+(i+1));
            if(!workflow.equals(fields[wfIndex]) || !algorithm.equals(fields[algIndex]) ||
                    seed!=Long.parseLong(fields[seedIndex])) continue;
            int k=Integer.parseInt(fields[posIndex]);
            if(k<1 || k>16 || selected.put(k,fields)!=null)
                throw new IllegalArgumentException("Bad original candidate index");
        }
        if(selected.size()!=16)throw new IllegalArgumentException("Original K16 arm incomplete");
        Set<String> keys=new HashSet<>();
        for(int i=1;i<=16;i++) {
            String[] fields=selected.get(i);
            if(fields==null || !keys.add(fields[mappingIndex]))
                throw new IllegalArgumentException("Original candidate index or mapping not unique");
        }
        if(output.getParent()!=null)Files.createDirectories(output.getParent());
        final boolean taskTrace=Boolean.getBoolean("dagfla.fixedTaskTrace");
        final boolean readyTrace=Boolean.getBoolean("dagfla.readyQueueDiagnostic");
        if(readyTrace&&!taskTrace)
            throw new IllegalArgumentException("readyQueueDiagnostic requires fixedTaskTrace for original Task-ID validation");
        final Path readyFile=Paths.get(output.toString().replaceFirst("\\.csv$","")+"_ready.csv");
        final Path taskTraceFile=Paths.get(output.toString().replaceFirst("\\.csv$","")+"_tasks.csv");
        Log.disable();
        try(BufferedWriter writer=Files.newBufferedWriter(output,StandardCharsets.UTF_8);
            BufferedWriter taskWriter=taskTrace
                ?Files.newBufferedWriter(taskTraceFile,StandardCharsets.UTF_8):null;
            BufferedWriter readyWriter=readyTrace
                ?Files.newBufferedWriter(readyFile,StandardCharsets.UTF_8):null) {
            if(readyTrace)readyWriter.write(
                "workflow,seed,algorithm,candidate_index,speed,mapping,"
                +"insertion_makespan,ready_queue_makespan,actual_makespan,"
                +"insertion_cost,ready_queue_cost,actual_cost,"
                +"insertion_task_mae_start,ready_task_mae_start,"
                +"insertion_task_mae_finish,ready_task_mae_finish,"
                +"insertion_makespan_abs_pct,ready_makespan_abs_pct,"
                +"insertion_cost_abs_pct,ready_cost_abs_pct\n");
            if(taskTrace)taskWriter.write("workflow,seed,algorithm,candidate_index,speed,task_id,vm_id,"
                +"planned_start,planned_finish,actual_start,actual_finish,actual_cpu_time,"
                +"nominal_compute_seconds,cpu_minus_nominal_compute_signed_seconds,start_error,finish_error\n");
            writer.write("workflow,seed,algorithm,source_candidate_index,speed,mapping,"
                +"original_default_planned_makespan,original_default_planned_cost,"
                +"original_default_actual_makespan,original_default_actual_cost,"
                +"fixed_replay_planned_makespan,fixed_replay_planned_cost,"
                +"fixed_replay_actual_makespan,fixed_replay_actual_cost\n");
            for(int k=1;k<=limit;k++) {
                String[] f=selected.get(k);
                String raw=f[mappingIndex];
                Map<Integer,Integer> mapping=parseMapping(raw);
                LIWSABenchmarkExample.RunResult result=LIWSABenchmarkExample.runPlanning(
                    "config/dax/"+workflow+".xml", Parameters.PlanningAlgorithm.LIWSA,
                    Parameters.SchedulingAlgorithm.STATIC,
                    "fixed_mapping_replay_"+profile+"_"+k,seed,
                    1,0,Collections.singletonList(mapping));
                if(result==null || !mapping.equals(new TreeMap<>(result.assignment)))
                    throw new IllegalStateException("Actual replay failed exact assignment identity");
                LIWSAPlanningAlgorithm.LastRunMetrics metrics=LIWSAPlanningAlgorithm.lastRun;
                if(metrics==null)throw new IllegalStateException("No independent planner metrics");
                if(taskTrace) {
                    if(metrics.traceTaskIds==null||metrics.traceVmIds==null||
                            metrics.tracePlannedStarts==null||metrics.tracePlannedFinishes==null||
                            result.fixedTaskActualTimeline==null||
                            metrics.traceTaskIds.length!=mapping.size()||
                            result.fixedTaskActualTimeline.size()!=mapping.size())
                        throw new IllegalStateException("Incomplete fixed task timeline");
                    java.util.Set<Integer> seen=new java.util.HashSet<>();
                    for(int taskIndex=0;taskIndex<metrics.traceTaskIds.length;taskIndex++) {
                        int taskId=metrics.traceTaskIds[taskIndex],vmId=metrics.traceVmIds[taskIndex];
                        double[] actual=result.fixedTaskActualTimeline.get(taskId);
                        if(actual==null||!seen.add(taskId)||mapping.get(taskId)==null||
                                mapping.get(taskId)!=vmId||(int)actual[0]!=vmId)
                            throw new IllegalStateException("Task trace identity/VM mismatch "+taskId);
                        double nominal=LIWSABenchmarkExample.VM_TYPES[vmId/4][0];
                        double speedMips=LIWSABenchmarkExample.vmMips(nominal,vmId%4);
                        double compute=actual[4]/speedMips;
                        double residual=actual[3]-compute;
                        // Signed accounting residual: CloudSim actual CPU duration may
                        // be smaller than taskLength/nominalVMmips. Do NOT interpret
                        // either sign as independently measured stage-in seconds.
                        if(!Double.isFinite(residual))
                            throw new IllegalStateException("Nonfinite actual CPU residual "+taskId);
                        double planStart=metrics.tracePlannedStarts[taskIndex];
                        double planFinish=metrics.tracePlannedFinishes[taskIndex];
                        if(!Double.isFinite(planStart)||!Double.isFinite(planFinish)||
                                planFinish<planStart)
                            throw new IllegalStateException("Invalid planned task timeline");
                        taskWriter.write(String.format(Locale.ROOT,
                           "%s,%d,%s,%d,%s,%d,%d,%.17g,%.17g,%.17g,%.17g,"
                           +"%.17g,%.17g,%.17g,%.17g,%.17g%n",
                           workflow,seed,algorithm,k,profile,taskId,vmId,planStart,planFinish,
                           actual[1],actual[2],actual[3],compute,residual,
                           actual[1]-planStart,actual[2]-planFinish));
                    }
                    taskWriter.flush();
                }
                if(readyTrace) {
                    int n=metrics.traceTaskIds.length;
                    if(metrics.readyQueueStarts==null||metrics.readyQueueFinishes==null||
                            metrics.readyQueueStarts.length!=n||metrics.readyQueueFinishes.length!=n||
                            !(metrics.readyQueueMakespan>0)||!(metrics.readyQueueCost>=0))
                        throw new IllegalStateException("Missing ready-queue diagnostic result");
                    double oldStart=0,newStart=0,oldFinish=0,newFinish=0;
                    for(int i=0;i<n;i++) {
                        int taskId=metrics.traceTaskIds[i];
                        double[] actual=result.fixedTaskActualTimeline.get(taskId);
                        if(actual==null)throw new IllegalStateException("Missing real task "+taskId);
                        if(metrics.readyQueueFinishes[i]<metrics.readyQueueStarts[i]||
                                !Double.isFinite(metrics.readyQueueStarts[i])||
                                !Double.isFinite(metrics.readyQueueFinishes[i]))
                            throw new IllegalStateException("Invalid alternative task time");
                        oldStart+=Math.abs(metrics.tracePlannedStarts[i]-actual[1]);
                        newStart+=Math.abs(metrics.readyQueueStarts[i]-actual[1]);
                        oldFinish+=Math.abs(metrics.tracePlannedFinishes[i]-actual[2]);
                        newFinish+=Math.abs(metrics.readyQueueFinishes[i]-actual[2]);
                    }
                    double baselineM=metrics.stageInAwareMakespan;
                    double newM=metrics.readyQueueMakespan;
                    double realM=result.makespan;
                    double baselineC=metrics.stageInAwareCost;
                    double newC=metrics.readyQueueCost;
                    double realC=result.cost;
                    readyWriter.write(String.format(Locale.ROOT,
                        "%s,%d,%s,%d,%s,%s,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,"
                        +"%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g%n",
                        workflow,seed,algorithm,k,profile,raw,
                        baselineM,newM,realM,baselineC,newC,realC,
                        oldStart/n,newStart/n,oldFinish/n,newFinish/n,
                        Math.abs(baselineM-realM)/realM*100,
                        Math.abs(newM-realM)/realM*100,
                        Math.abs(baselineC-realC)/realC*100,
                        Math.abs(newC-realC)/realC*100));
                    readyWriter.flush();
                }
                double[] measured={metrics.chosenMakespan,metrics.chosenCost,
                        result.makespan,result.cost};
                for(double x:measured)
                    if(!Double.isFinite(x)||x<=0)throw new IllegalStateException("Invalid replay outcome");
                double priorM=positive(f[originalPlannedM]),priorC=positive(f[originalPlannedC]);
                double oldRealM=positive(f[originalRealM]),oldRealC=positive(f[originalRealC]);
                if("default".equals(profile)) {
                    double[] original={priorM,priorC,oldRealM,oldRealC};
                    for(int j=0;j<4;j++) {
                        double tolerance=1e-6*Math.max(1.0,Math.abs(original[j]));
                        if(Math.abs(original[j]-measured[j])>tolerance)
                            throw new IllegalStateException("Default original replay mismatch"
                                +" candidate="+k+" field="+j+" expected="+original[j]+" got="+measured[j]);
                    }
                }
                writer.write(String.format(Locale.ROOT,
                    "%s,%d,%s,%d,%s,%s,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g%n",
                    workflow,seed,algorithm,k,profile,raw,
                    priorM,priorC,oldRealM,oldRealC,
                    measured[0],measured[1],measured[2],measured[3]));
                writer.flush();
                System.out.printf(Locale.ROOT,
                    "FIXED_MATCHED %s %s seed=%d k=%d speed=%s planned=%.9f real=%.9f%n",
                    workflow,algorithm,seed,k,profile,measured[0],measured[2]);
            }
        }
        System.out.println("PASS original source K16 mapping uniqueness, independent exact replay, fixed assignment");
    }
}
