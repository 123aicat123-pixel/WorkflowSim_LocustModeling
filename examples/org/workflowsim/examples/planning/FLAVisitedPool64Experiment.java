package org.workflowsim.examples.planning;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.TreeMap;
import org.cloudbus.cloudsim.Log;
import org.workflowsim.CondorVM;
import org.workflowsim.Task;
import org.workflowsim.planning.LIWSAPlanningAlgorithm;
import org.workflowsim.planning.ReadyQueueScheduleEvaluator;
import org.workflowsim.planning.StageInAwareScheduleEvaluator;
import org.workflowsim.utils.Parameters;

/**
 * FROZEN research-only: same 64 actually FLA-visited physical mappings get
 * BOTH old and ready read-only forecasts BEFORE any actual FIFO replay labels.
 * No changes to optimizer, search, queue policy, or objective budgets.
 */
public final class FLAVisitedPool64Experiment {
    private FLAVisitedPool64Experiment() { }

    private static String mappingKey(Map<Integer,Integer> x) {
        StringBuilder b=new StringBuilder();
        for(Map.Entry<Integer,Integer> e:new TreeMap<>(x).entrySet()) {
            if(b.length()>0)b.append('|');
            b.append(e.getKey()).append(':').append(e.getValue());
        }
        return b.toString();
    }
    private static void positive(double value,String field) {
        if(!Double.isFinite(value) || value<=0)
            throw new IllegalStateException("Invalid "+field+": "+value);
    }

    public static void run(String workflow,long seed,Path prefix,
            List<Map<Integer,Integer>> distinctVisited,
            List<Task> tasks,List<CondorVM> vms,int visits,long searchMillis)
            throws Exception {
        if(visits!=3030 || distinctVisited==null || distinctVisited.size()<64 ||
           tasks==null||tasks.size()<2||vms==null||vms.size()!=16)
            throw new IllegalStateException("Invalid full-search source / DAG/VM pool");
        Set<String> keys=new HashSet<>();
        for(Map<Integer,Integer> mapping:distinctVisited) {
            if(mapping==null || mapping.size()!=tasks.size() ||
               !keys.add(mappingKey(mapping)))
                throw new IllegalStateException("Not a complete distinct real FLA-visited pool");
        }
        List<Map<Integer,Integer>> samples=new ArrayList<>(distinctVisited);
        Collections.shuffle(samples,new Random(seed ^ 0x6A09E667F3BCC909L));
        samples=new ArrayList<>(samples.subList(0,64));
        StageInAwareScheduleEvaluator old=new StageInAwareScheduleEvaluator(tasks,vms);
        ReadyQueueScheduleEvaluator ready=new ReadyQueueScheduleEvaluator(tasks,vms,
                ReadyQueueScheduleEvaluator.QueuePolicy.TASK_ID);
        Path predictions=Paths.get(prefix.toString()+"_pool64_frozen_predictions.csv");
        Path replays=Paths.get(prefix.toString()+"_pool64_true_replays.csv");
        Path budget=Paths.get(prefix.toString()+"_pool64_budget.txt");
        double[][] oldValues=new double[64][2],readyValues=new double[64][2];
        Files.write(budget,java.util.Arrays.asList(
            "workflow="+workflow,"seed="+seed,"search_evaluations="+visits,
            "distinct_visited="+distinctVisited.size(),"pool_size=64",
            "old_forecasts=64","ready_forecasts=64",
            "sampling=java.util.Collections.shuffle encounter-order distinct visited; Random(seed ^ 0x6A09E667F3BCC909L)",
            "search_ms="+searchMillis),StandardCharsets.UTF_8);

        // Prediction write is fully closed before the first real simulator call.
        try(BufferedWriter w=Files.newBufferedWriter(predictions,StandardCharsets.UTF_8)) {
            w.write("workflow,seed,pool_index,mapping,old_planned_makespan,old_planned_cost,ready_planned_makespan,ready_planned_cost\n");
            for(int i=0;i<64;i++) {
                Map<Integer,Integer> map=samples.get(i);
                StageInAwareScheduleEvaluator.Result a=old.evaluate(map);
                ReadyQueueScheduleEvaluator.Result b=ready.evaluate(map);
                positive(a.makespan,"old makespan");
                positive(a.cost,"old cost");
                positive(b.makespan,"ready makespan");
                positive(b.cost,"ready cost");
                oldValues[i]=new double[]{a.makespan,a.cost};
                readyValues[i]=new double[]{b.makespan,b.cost};
                w.write(String.format(Locale.ROOT,"%s,%d,%d,%s,%.17g,%.17g,%.17g,%.17g%n",
                   workflow,seed,i+1,mappingKey(map),
                   a.makespan,a.cost,b.makespan,b.cost));
            }
        }
        System.out.printf(Locale.ROOT,
           "FROZEN_BEFORE_TRUTH workflow=%s seed=%d visited=%d pool=%d oldForecast=64 readyForecast=64%n",
           workflow,seed,distinctVisited.size(),samples.size());
        try(BufferedWriter w=Files.newBufferedWriter(replays,StandardCharsets.UTF_8)) {
            w.write("workflow,seed,pool_index,mapping,actual_makespan,actual_cost\n");
            for(int i=0;i<64;i++) {
                Map<Integer,Integer> map=samples.get(i);
                LIWSABenchmarkExample.RunResult result=LIWSABenchmarkExample.runPlanning(
                      "config/dax/"+workflow+".xml",Parameters.PlanningAlgorithm.LIWSA,
                      Parameters.SchedulingAlgorithm.STATIC,
                      "visited_pool64_physical_"+(i+1),seed,1,0,
                      Collections.singletonList(map));
                if(result==null || result.assignment==null ||
                   !new TreeMap<>(result.assignment).equals(new TreeMap<>(map)))
                    throw new IllegalStateException("Real FIFO simulator mapping identity mismatch "+i);
                positive(result.makespan,"actual makespan");
                positive(result.cost,"actual cost");
                LIWSAPlanningAlgorithm.LastRunMetrics trace=LIWSAPlanningAlgorithm.lastRun;
                if(trace==null||trace.traceTaskIds==null||trace.traceVmIds==null||
                   trace.traceTaskIds.length!=map.size()||
                   trace.traceVmIds.length!=map.size()||
                   result.fixedTaskActualTimeline==null||
                   result.fixedTaskActualTimeline.size()!=map.size())
                    throw new IllegalStateException("Incomplete original actual task trace "+i);
                Set<Integer> seen=new HashSet<>();
                for(int t=0;t<trace.traceTaskIds.length;t++) {
                    int id=trace.traceTaskIds[t],vm=trace.traceVmIds[t];
                    double[] a=result.fixedTaskActualTimeline.get(id);
                    if(!seen.add(id)||!map.containsKey(id)||map.get(id)!=vm||
                       a==null||(int)a[0]!=vm||!Double.isFinite(a[1])||
                       !Double.isFinite(a[2])||a[2]<a[1])
                        throw new IllegalStateException("Original physical task ID/timeline mismatch "+i+" task="+id);
                }
                w.write(String.format(Locale.ROOT,"%s,%d,%d,%s,%.17g,%.17g%n",
                   workflow,seed,i+1,mappingKey(map),result.makespan,result.cost));
                w.flush();
                System.out.printf(Locale.ROOT,"ORIGINAL_TRUE_POOL64_PASS source=%s seed=%d map=%d%n",
                  workflow,seed,i+1);
            }
        }
        System.out.printf(Locale.ROOT,
             "PASS OLD FLA 3030 real visits, 64 frozen same-genotype dual forecasts, 64 actual original WorkflowSim FIFO replays%n");
    }
}
