package org.workflowsim.scheduling;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.cloudbus.cloudsim.Cloudlet;
import org.workflowsim.Job;
import org.workflowsim.Task;
import org.workflowsim.utils.Parameters;

/**
 * EXPERIMENTAL runtime-ready-job priority: changes the order of candidate
 * COMPUTE jobs already released by WorkflowEngine, never their VM assignment
 * or the prerequisite constraints. It does NOT change the default FIFO policy.
 *
 * This is a feasibility pilot, not an optimizer or a claim of novelty:
 * shortest-job-first and upward critical path rank are existing heuristics.
 *
 * Only compute-job slots are reordered. Stage-in and clustered/non-compute
 * jobs remain at their original positions. The copy is mutated, not the
 * WorkflowScheduler's pending list.
 */
public final class FLAFixedVmReadyPriority {
    private FLAFixedVmReadyPriority() {}

    private static Task originalTask(Cloudlet cloudlet) {
        if (!(cloudlet instanceof Job))return null;
        Job job=(Job)cloudlet;
        if(job.getClassType()!=Parameters.ClassType.COMPUTE.value)return null;
        List<Task> tasks=job.getTaskList();
        return tasks!=null && tasks.size()==1 ?tasks.get(0):null;
    }

    private static double upward(Task task,IdentityHashMap<Task,Double> memo,
                                 Set<Task> stack) {
        Double known=memo.get(task);
        if(known!=null)return known;
        if(!stack.add(task))throw new IllegalArgumentException("Cycle in task graph");
        double maximumChild=0.0;
        for(Task child:task.getChildList())
            maximumChild=Math.max(maximumChild,upward(child,memo,stack));
        stack.remove(task);
        double score=(double)task.getCloudletTotalLength()+maximumChild;
        if(!Double.isFinite(score)||score<0)
            throw new IllegalArgumentException("Nonfinite task rank");
        memo.put(task,score);
        return score;
    }

    /**
     * Passive capture at the ONLY real dispatch decision point. Unlike raw
     * pending-list reorder counters, this counts competition between at least
     * two COMPUTE jobs assigned to a VM that is IDLE at this scheduling tick.
     * No scheduler state is mutated, no random draw consumed.
     */
    public static void traceIdleVmChoices(List<? extends Cloudlet> original,
            List<? extends Cloudlet> ranked,Map<Integer,CondorVM> vms) {
        if(!Boolean.getBoolean("dagfla.priorityOpportunityTrace"))return;
        java.util.TreeMap<Integer,CondorVM> orderedVms=new java.util.TreeMap<>(vms);
        for(Map.Entry<Integer,CondorVM> entry:orderedVms.entrySet()) {
            int vmId=entry.getKey();
            CondorVM vm=entry.getValue();
            if(vm.getState()!=org.workflowsim.WorkflowSimTags.VM_STATUS_IDLE)
                continue;
            int count=0;
            int fifo=-1;
            for(Cloudlet c:original) {
                Task task=originalTask(c);
                if(task==null||c.getVmId()!=vmId)continue;
                if(fifo<0)fifo=task.getCloudletId();
                count++;
            }
            if(count<2)continue;
            int chosen=-1;
            for(Cloudlet c:ranked) {
                Task t=originalTask(c);
                if(t!=null&&c.getVmId()==vmId) {
                    chosen=t.getCloudletId();
                    break;
                }
            }
            if(chosen<0)
                throw new IllegalStateException("Priority trace lost eligible task");
            System.out.printf(java.util.Locale.ROOT,
                "PRIORITY_OPPORTUNITY,%s,%.17g,%d,%d,%d,%d,%d%n",
                System.getProperty("dagfla.fixedVmReadyPriority","fifo"),
                org.cloudbus.cloudsim.core.CloudSim.clock(),vmId,count,fifo,chosen,
                fifo==chosen?0:1);
        }
    }

    public static List<Cloudlet> ordered(List<? extends Cloudlet> pending) {
        if(pending==null)throw new IllegalArgumentException("No scheduler list");
        List<Cloudlet> result=new ArrayList<>(pending);
        String policy=System.getProperty("dagfla.fixedVmReadyPriority","fifo");
        if("fifo".equals(policy))return result;
        if(!"shortest".equals(policy) && !"upward".equals(policy))
            throw new IllegalArgumentException("Unknown experimental ready priority "+policy);

        List<Integer> computeSlots=new ArrayList<>();
        List<Cloudlet> compute=new ArrayList<>();
        for(int i=0;i<result.size();i++) {
            Task task=originalTask(result.get(i));
            if(task!=null) {
                computeSlots.add(i);
                compute.add(result.get(i));
            }
        }
        IdentityHashMap<Task,Double> ranks=new IdentityHashMap<>();
        Set<Task> stack=java.util.Collections.newSetFromMap(new IdentityHashMap<Task,Boolean>());
        if("upward".equals(policy)) {
            for(Cloudlet job:compute)upward(originalTask(job),ranks,stack);
        }
        Comparator<Cloudlet> cmp=(left,right)-> {
            Task a=originalTask(left),b=originalTask(right);
            double pa="shortest".equals(policy) ?a.getCloudletTotalLength():ranks.get(a);
            double pb="shortest".equals(policy) ?b.getCloudletTotalLength():ranks.get(b);
            int c="shortest".equals(policy)?Double.compare(pa,pb):Double.compare(pb,pa);
            if(c!=0)return c;
            return Integer.compare(a.getCloudletId(),b.getCloudletId());
        };
        compute.sort(cmp);
        for(int k=0;k<compute.size();k++)result.set(computeSlots.get(k),compute.get(k));
        return result;
    }
}
