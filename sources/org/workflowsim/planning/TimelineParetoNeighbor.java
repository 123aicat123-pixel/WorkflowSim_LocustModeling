package org.workflowsim.planning;

import java.util.List;
import java.util.Random;
import org.workflowsim.CondorVM;
import org.workflowsim.Task;

/** Pure, never calls a fitness evaluator: chooses ONE local neighbor using
 * already-observed, stage-in-aware planned task timing and VM calendars. */
public final class TimelineParetoNeighbor {
    private TimelineParetoNeighbor() {}

    public static int chooseTask(FLAScheduleEvaluator.ScheduleTrace trace,int[][] allowed,
            boolean randomControl,Random rng) {
        if(trace==null||allowed==null||rng==null||trace.finishes.length!=allowed.length)
            throw new IllegalArgumentException("Invalid timeline task pool");
        int n=allowed.length;
        if(randomControl) {
            int eligible=0;
            for(int[] a:allowed)if(a.length>1)eligible++;
            if(eligible==0)return -1;
            int draw=rng.nextInt(eligible);
            for(int i=0;i<n;i++)if(allowed[i].length>1 && draw--==0)return i;
        }
        // Latest-finishing eligible task is the schedule's current trailing event.
         double[] finish=trace.finishes;
        int best=-1;double bestFinish=Double.NEGATIVE_INFINITY;
        for(int i=0;i<n;i++){
            if(allowed[i].length<2)continue;
            if(finish[i]>bestFinish){best=i;bestFinish=finish[i];}
        }
        return best;
    }

    public static int chooseVm(FLAScheduleEvaluator.ScheduleTrace trace,int[] genes,
            int task,int[] allowed,double[] service,List<CondorVM> vms,
            boolean latencyFocused,boolean randomControl,Random rng,List<Task> taskOrder) {
        if(trace==null||genes==null||allowed==null||service==null||vms==null||
           task<0||task>=genes.length||allowed.length<2||taskOrder==null||
           taskOrder.size()!=genes.length)
            throw new IllegalArgumentException("Invalid neighbor VM context");
        int current=genes[task];
        if(randomControl){
            int count=0;
            for(int v:allowed)if(v!=current)count++;
            if(count==0)throw new IllegalArgumentException("No alternate VM");
            int pick=rng.nextInt(count);
            for(int v:allowed)if(v!=current && pick--==0)return v;
        }
        // Existing true-planned stage-in-aware timeline supplies VM occupied
        // intervals, while the candidate's own service is an optimistic estimate.
        // Input-stage cache and any downstream rescheduling are NOT exact here.
        // Crucially, the proposed genotype is then evaluated EXACTLY ONCE.
        double ready=0.;
        for(Task parent:taskOrder.get(task).getParentList()){
            int parentIndex=-1;
            for(int i=0;i<taskOrder.size();i++)
                if(taskOrder.get(i)==parent){parentIndex=i;break;}
            if(parentIndex<0 || parentIndex>=task)
                throw new IllegalArgumentException("Parent outside preceding DAG order");
            ready=Math.max(ready,trace.finishes[parentIndex]);
        }
        int chosen=-1;double best=Double.POSITIVE_INFINITY;
        for(int v:allowed) {
            if(v==current)continue;
            double estimated=earliestGapFinish(trace,task,v,service[v],ready);
            double currentCost=Math.max(1e-9,service[current]*vms.get(current).getCost());
            double newCost=service[v]*vms.get(v).getCost();
            double extra=Math.max(0.,newCost-currentCost);
            double penalty=(latencyFocused?0.1:0.5)*(extra/currentCost)*
                    Math.max(1.,service[current]);
            double score=estimated+penalty;
            if(score<best){best=score;chosen=v;}
        }
        if(chosen<0)throw new IllegalStateException("No feasible different target VM");
        return chosen;
    }

    /** Earliest nonoverlapping insertion into the *previous* evaluated VM events. */
    public static double earliestGapFinish(FLAScheduleEvaluator.ScheduleTrace t,int moved,int vm,
            double duration,double ready) {
        if(!Double.isFinite(ready)||ready<0||!Double.isFinite(duration)||duration<0)
            throw new IllegalArgumentException("Invalid timing");
        double at=ready;
        int n=t.finishes.length;
        // Selection sort the matching VM calendar by start (n is DAG size).
        boolean[] used=new boolean[n];
        for(int count=0;count<n;count++){
            int first=-1;double firstStart=Double.POSITIVE_INFINITY;
            for(int k=0;k<n;k++){
                if(k==moved||used[k]||t.vmIndices[k]!=vm)continue;
                if(t.starts[k]<firstStart){firstStart=t.starts[k];first=k;}
            }
            if(first<0)break;
            used[first]=true;
            if(at+duration<=t.starts[first]+1e-9)return at+duration;
            at=Math.max(at,t.finishes[first]);
        }
        return at+duration;
    }
}
