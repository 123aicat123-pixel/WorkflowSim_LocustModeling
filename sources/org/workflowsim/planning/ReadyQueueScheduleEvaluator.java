package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.cloudbus.cloudsim.Consts;
import org.workflowsim.CondorVM;
import org.workflowsim.FileItem;
import org.workflowsim.Task;
import org.workflowsim.utils.Parameters;

/**
 * Read-only event-driven estimator for a FIXED task-to-VM assignment.
 *
 * An unmodified WorkflowSim STATIC scheduler dispatches at most one
 * ready job to each idle CondorVM, and its WorkflowEngine releases tasks
 * only after their parents complete. This alternative estimator models
 * that behavior with discrete finish events; when multiple independent
 * tasks are ready for an idle VM, it chooses the original DAX Task ID
 * (WorkflowParser's declaration order). It does NOT use future real
 * simulation outputs, and is NOT the actual CloudSim simulator.
 *
 * Differences still possible: original engine event batching, scheduler
 * overheads, exact file replica catalog state, datacenter processing
 * event latency, and CloudSim VM scheduling. This estimator is NEVER
 * installed into search unless a separate explicit scientific gate is met.
 */
public final class ReadyQueueScheduleEvaluator {
    private static final double EPS = 1e-9;

    /** Experimental fixed-ready-queue forecast policy, distinct from runtime labels. */
    public enum QueuePolicy { TASK_ID, SHORTEST, UPWARD }

    public static QueuePolicy fromRuntimeName(String name) {
        if("fifo".equals(name))return QueuePolicy.TASK_ID;
        if("shortest".equals(name))return QueuePolicy.SHORTEST;
        if("upward".equals(name))return QueuePolicy.UPWARD;
        throw new IllegalArgumentException("Unknown priority forecast policy "+name);
    }

    public static final class Result {
        public final double makespan;
        public final double cost;
        public final double totalStageInSeconds;
        public final double externalStageInSeconds;
        public final double intermediateStageInSeconds;
        public final double[] starts;
        public final double[] finishes;
        public final int[] scheduledTaskIds;

        private Result(double m,double c,double stage,double external,double intermediate,
                       double[] starts,double[] finishes,int[] sequence) {
            makespan=m; cost=c; totalStageInSeconds=stage;
            externalStageInSeconds=external;
            intermediateStageInSeconds=intermediate;
            this.starts=starts.clone(); this.finishes=finishes.clone();
            this.scheduledTaskIds=sequence.clone();
        }
    }

    private final List<Task> order;
    private final List<CondorVM> vms;
    private final IdentityHashMap<Task,Integer> indexes = new IdentityHashMap<>();
    private final Map<Integer,Integer> vmIndexById = new HashMap<>();
    private final int[][] parents;
    private final int[] declarationOrder;
    private final QueuePolicy queuePolicy;

    public ReadyQueueScheduleEvaluator(List<Task> topologicalTasks,List<CondorVM> orderedVms) {
        this(topologicalTasks,orderedVms,QueuePolicy.TASK_ID);
    }

    public ReadyQueueScheduleEvaluator(List<Task> topologicalTasks,List<CondorVM> orderedVms,
                                       QueuePolicy policy) {
        if(policy==null)throw new IllegalArgumentException("Missing queue forecast policy");
        this.queuePolicy=policy;
        if (topologicalTasks==null||topologicalTasks.isEmpty()||
                orderedVms==null||orderedVms.isEmpty())
            throw new IllegalArgumentException("Empty task/VM data");
        order=new ArrayList<>(topologicalTasks);
        vms=new ArrayList<>(orderedVms);
        int n=order.size();
        parents=new int[n][];
        for(int i=0;i<vms.size();i++) {
            CondorVM vm=vms.get(i);
            if(vm==null||!Double.isFinite(vm.getMips())||vm.getMips()<=0||
                    vm.getBw()<=0||!Double.isFinite(vm.getCost())||vm.getCost()<0||
                    vmIndexById.put(vm.getId(),i)!=null)
                throw new IllegalArgumentException("Invalid or repeated VM");
        }
        Set<Integer> uniqueTaskIds = new HashSet<>();
        for(int i=0;i<n;i++) {
            Task t=order.get(i);
            if(t==null||t.getCloudletId()<0||!uniqueTaskIds.add(t.getCloudletId())||
                    indexes.put(t,i)!=null)
                throw new IllegalArgumentException("Invalid or repeated task");
        }
        for(int i=0;i<n;i++) {
            List<Integer> p=new ArrayList<>();
            for(Object entry:order.get(i).getParentList()) {
                Integer index=indexes.get((Task)entry);
                if(index==null||index>=i)
                    throw new IllegalArgumentException("Input tasks must be in topological order");
                if(p.contains(index))
                    throw new IllegalArgumentException("Repeated parent dependency");
                p.add(index);
            }
            parents[i]=new int[p.size()];
            for(int j=0;j<p.size();j++)parents[i][j]=p.get(j);
        }
        List<Integer> ids=new ArrayList<>();
        for(int i=0;i<n;i++)ids.add(i);
        final double[] upwardRank=new double[n];
        if(queuePolicy==QueuePolicy.UPWARD) {
            for(int i=n-1;i>=0;i--) {
                double maximumChild=0.0;
                for(Task child:order.get(i).getChildList()) {
                    Integer childIndex=indexes.get(child);
                    if(childIndex==null||childIndex<=i)
                        throw new IllegalArgumentException("Invalid descendant relation for upward priority");
                    maximumChild=Math.max(maximumChild,upwardRank[childIndex]);
                }
                upwardRank[i]=order.get(i).getCloudletTotalLength()+maximumChild;
                if(!Double.isFinite(upwardRank[i])||upwardRank[i]<0)
                    throw new IllegalArgumentException("Invalid upward task priority");
            }
        }
        if(queuePolicy==QueuePolicy.SHORTEST) {
            Collections.sort(ids,(a,b)->{
                int cmp=Long.compare(order.get(a).getCloudletTotalLength(),
                                     order.get(b).getCloudletTotalLength());
                return cmp!=0?cmp:Integer.compare(order.get(a).getCloudletId(),
                                                  order.get(b).getCloudletId());
            });
        } else if(queuePolicy==QueuePolicy.UPWARD) {
            Collections.sort(ids,(a,b)->{
                int cmp=Double.compare(upwardRank[b],upwardRank[a]);
                return cmp!=0?cmp:Integer.compare(order.get(a).getCloudletId(),
                                                  order.get(b).getCloudletId());
            });
        } else {
            Collections.sort(ids,Comparator.comparingInt(i->order.get(i).getCloudletId()));
        }
        declarationOrder=new int[n];
        for(int i=0;i<n;i++)declarationOrder[i]=ids.get(i);
    }

    /** One-shot isolated evaluation; no cached state survives between assignments. */
    public Result evaluate(Map<Integer,Integer> mapping) {
        if(mapping==null||mapping.size()!=order.size())
            throw new IllegalArgumentException("Incomplete task-to-VM mapping");
        int n=order.size(),m=vms.size();
        int[] assigned=new int[n];
        for(int i=0;i<n;i++) {
            Integer vmId=mapping.get(order.get(i).getCloudletId());
            Integer vmIndex=vmId==null?null:vmIndexById.get(vmId);
            if(vmIndex==null)throw new IllegalArgumentException("Invalid VM for task "+order.get(i).getCloudletId());
            assigned[i]=vmIndex;
        }
        // 0=pending; 1=running; 2=completed. A VM runs at most one task.
        int[] status=new int[n];
        int[] running=new int[m];
        java.util.Arrays.fill(running,-1);
        double[] start=new double[n],finish=new double[n];
        List<Set<String>> cached=new ArrayList<>();
        for(int i=0;i<m;i++)cached.add(new HashSet<>());
        Map<String,Integer> completedOutputVm=new HashMap<>();
        double now=0,makespan=0,cost=0,totalStage=0,external=0,intermediate=0;
        int done=0,issued=0;
        int[] issueOrder=new int[n];
        while(done<n) {
            // Use the frozen experimental ready-task forecast order. Only
            // already completed-parent tasks can dispatch; VM mapping fixed.
            // TASK_ID retains the original diagnostic behavior exactly.
            for(int i:declarationOrder) {
                if(status[i]!=0||running[assigned[i]]>=0)continue;
                boolean ready=true;
                for(int p:parents[i]) {
                    if(status[p]!=2) {ready=false;break;}
                }
                if(!ready)continue;
                CondorVM vm=vms.get(assigned[i]);
                double delay=0;
                for(FileItem file:order.get(i).getFileList()) {
                    List<FileItem> taskFiles=order.get(i).getFileList();
                    if(file.getType()!=Parameters.FileType.INPUT||
                            !file.isRealInputFile(taskFiles))continue;
                    String name=file.getName();
                    if(cached.get(assigned[i]).contains(name))continue;
                    Integer source=completedOutputVm.get(name);
                    double bw=vm.getBw();
                    if(source!=null && source!=assigned[i])
                        bw=Math.min(bw,vms.get(source).getBw());
                    if(!Double.isFinite(file.getSize())||file.getSize()<0||
                            !Double.isFinite(bw)||bw<=0)
                        throw new IllegalArgumentException("Invalid file or bandwidth");
                    double stage=file.getSize()/(double)Consts.MILLION/bw;
                    delay+=stage;
                    if(source==null)external+=stage;
                    else if(source!=assigned[i])intermediate+=stage;
                    cached.get(assigned[i]).add(name);
                }
                double compute=order.get(i).getCloudletTotalLength()/vm.getMips();
                double duration=compute+delay;
                if(!Double.isFinite(duration)||duration<0)
                    throw new IllegalStateException("Invalid task duration");
                start[i]=now;
                finish[i]=now+duration;
                running[assigned[i]]=i;
                status[i]=1;
                issueOrder[issued++]=order.get(i).getCloudletId();
                cost+=duration*vm.getCost();
                totalStage+=delay;
            }
            double next=Double.POSITIVE_INFINITY;
            for(int task:running)if(task>=0)next=Math.min(next,finish[task]);
            if(!Double.isFinite(next)||next<now-EPS)
                throw new IllegalStateException("Deadlocked DAG / invalid time");
            // Zero-duration jobs are allowed; complete them at the current time.
            now=next;
            int finishedThisTick=0;
            for(int vm=0;vm<m;vm++) {
                int task=running[vm];
                if(task<0||finish[task]>now+EPS)continue;
                running[vm]=-1;
                status[task]=2;
                done++;finishedThisTick++;
                makespan=Math.max(makespan,finish[task]);
                for(FileItem f:order.get(task).getFileList()) {
                    if(f.getType()==Parameters.FileType.OUTPUT) {
                        completedOutputVm.put(f.getName(),vm);
                        cached.get(vm).add(f.getName());
                    }
                }
            }
            if(finishedThisTick==0)
                throw new IllegalStateException("Simulation made no progress");
        }
        if(issued!=n||!Double.isFinite(makespan)||makespan<=0||
                !Double.isFinite(cost)||cost<0)
            throw new IllegalStateException("Nonfinite/incomplete event-driven estimate");
        return new Result(makespan,cost,totalStage,external,intermediate,start,finish,issueOrder);
    }
}
