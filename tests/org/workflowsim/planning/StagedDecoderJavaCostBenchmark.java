package org.workflowsim.planning;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.cloudbus.cloudsim.CloudletSchedulerSpaceShared;
import org.workflowsim.CondorVM;
import org.workflowsim.Task;

/**
 * Deterministic synthetic Java **actual evaluator** microbenchmark, no CloudSim.
 * Outputs all rounds to CSV for independent median and compute-cost audit.
 */
public final class StagedDecoderJavaCostBenchmark {
    private StagedDecoderJavaCostBenchmark() {}
    private static volatile double checksum = 0;

    private static CondorVM vm(int id) {
        double mips=100.0+25*(id%4);
        return new CondorVM(id,0,mips,1,512,1000,100000,
                "Xen",1,0,0,0,new CloudletSchedulerSpaceShared());
    }
    private static List<Task> tasks(int n,String graph) {
        List<Task> jobs=new ArrayList<>();
        for(int i=0;i<n;i++)jobs.add(new Task(i+1,100L*(1+i%17)));
        for(int i=0;i<n;i++) {
            List<Integer> parents=new ArrayList<>();
            if("chain".equals(graph)&&i>0)parents.add(i-1);
            if("forked".equals(graph)) {
                if(i>0&&i%3==0)parents.add(i-1);
                if(i>=4)parents.add(i-4);
            }
            if(!"chain".equals(graph)&&!"forked".equals(graph)&&!"independent".equals(graph))
                throw new IllegalArgumentException("Unknown DAG structure");
            for(int parent:parents){
                Task before=jobs.get(parent),child=jobs.get(i);
                before.addChild(child);
                child.addParent(before);
            }
        }
        return jobs;
    }
    private static List<Map<Integer,Integer>> assignments(int n) {
        List<Map<Integer,Integer>> all=new ArrayList<>();
        for(int k=0;k<16;k++) {
            Map<Integer,Integer> m=new HashMap<>();
            for(int i=0;i<n;i++){
                int target;
                switch(k%4){
                    case 0:target=(i+k)%16;break;
                    case 1:target=(7*i+3*k)%16;break;
                    case 2:target=((i/4)+k)%16;break;
                    default:target=((i*11+k*3)%16);break;
                }
                m.put(i+1,target);
            }
            all.add(m);
        }
        return all;
    }
    private static long timed(String model,StageInAwareScheduleEvaluator old,
                ReadyQueueScheduleEvaluator ready,
                List<Map<Integer,Integer>> mappings,int repetitions) {
        long start=System.nanoTime();
        double accum=0;
        for(int j=0;j<repetitions;j++) {
            for(Map<Integer,Integer> m:mappings) {
                double span,cost;
                if("old".equals(model)) {
                    StageInAwareScheduleEvaluator.Result r=old.evaluate(m);
                    span=r.makespan;cost=r.cost;
                } else {
                    ReadyQueueScheduleEvaluator.Result r=ready.evaluate(m);
                    span=r.makespan;cost=r.cost;
                }
                if(!Double.isFinite(span)||span<=0||
                        !Double.isFinite(cost)||cost<0)
                    throw new AssertionError("Invalid Java decoder objectives");
                accum+=span+cost*1e-5;
            }
        }
        long elapsed=System.nanoTime()-start;
        if(elapsed<=0)throw new AssertionError("Nonpositive wall time");
        checksum=accum;
        return elapsed;
    }
    public static void main(String[] args) throws Exception {
        if(args.length!=1)
            throw new IllegalArgumentException("Usage: JavaCostBenchmark OUTPUT_CSV");
        Path file=Paths.get(args[0]);
        if(file.getParent()!=null)Files.createDirectories(file.getParent());
        int count=0;
        try(BufferedWriter out=Files.newBufferedWriter(file,StandardCharsets.UTF_8)) {
            out.write("task_count,graph,vm_count,model,round,calls,total_ns,ns_per_candidate\n");
            for(int n:new int[]{30,100,200}) {
                for(String graph:new String[]{"chain","forked","independent"}) {
                    List<Task> order=tasks(n,graph);
                    List<CondorVM> pool=new ArrayList<>();
                    for(int v=0;v<16;v++)pool.add(vm(v));
                    List<Map<Integer,Integer>> mappings=assignments(n);
                    StageInAwareScheduleEvaluator old=
                            new StageInAwareScheduleEvaluator(order,pool);
                    ReadyQueueScheduleEvaluator ready=
                            new ReadyQueueScheduleEvaluator(order,pool);

                    for(Map<Integer,Integer> m:mappings) {
                        StageInAwareScheduleEvaluator.Result a=old.evaluate(m);
                        ReadyQueueScheduleEvaluator.Result b=ready.evaluate(m);
                        StageInAwareScheduleEvaluator.Result aa=old.evaluate(m);
                        ReadyQueueScheduleEvaluator.Result bb=ready.evaluate(m);
                        if(a.makespan!=aa.makespan||a.cost!=aa.cost||
                           b.makespan!=bb.makespan||b.cost!=bb.cost)
                            throw new AssertionError("Model state leakage on "+graph+" "+n);
                    }
                    // Exactly four complete 16-candidate warm-up passes per model.
                    timed("old",old,ready,mappings,4);
                    timed("ready",old,ready,mappings,4);
                    for(int round=0;round<6;round++) {
                        String first=round%2==0?"old":"ready";
                        String second=round%2==0?"ready":"old";
                        for(String model:new String[]{first,second}) {
                            long elapsed=timed(model,old,ready,mappings,8);
                            int calls=8*mappings.size();
                            out.write(String.format(Locale.ROOT,
                                "%d,%s,16,%s,%d,%d,%d,%.10f%n",
                                n,graph,model,round,calls,elapsed,
                                (double)elapsed/calls));
                            count++;
                        }
                        out.flush();
                    }
                }
            }
        }
        if(count!=108||!Double.isFinite(checksum)||checksum<=0)
            throw new AssertionError("Incomplete 108 original timing rounds");
        System.out.printf(Locale.ROOT,
            "PASS StagedDecoderJavaCostBenchmark: %d rounds, two actual Java evaluators, synthetic DAGs; checksum=%.6f%n",
            count,checksum);
    }
}
