package org.workflowsim.planning;

import java.util.ArrayList;
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
 * Independent, simulator-informed planning ESTIMATOR for a fixed VM assignment.
 * It does not modify WorkflowSim, any optimizer, or the baseline decoder.
 *
 * Unlike the historical HEFT-style estimator, the CloudSim LOCAL simulator
 * places actual input stage-in in the job's occupied VM time and charges it as
 * CPU time. The simulator uses input-file bytes / 1e6 / VM bandwidth, not a
 * cross-edge 8*bytes/1e6/averageBandwidth predecessor offset.
 *
 * The estimator models source inputs and already-produced intermediate inputs;
 * VM caches are updated in topological planning order. The real simulator may
 * dispatch jobs in a different order and use other replica caches, so this is
 * a measurable approximation rather than an exact predictor.
 */
public final class StageInAwareScheduleEvaluator {
    public static final class Result {
        public final double makespan;
        public final double cost;
        public final double stageInSeconds;
        public final double externalStageInSeconds;
        public final double intermediateStageInSeconds;
        public final int chargedInputs;

        Result(double m,double c,double stage,double ext,double inter,int charged) {
            makespan=m;cost=c;stageInSeconds=stage;
            externalStageInSeconds=ext;intermediateStageInSeconds=inter;
            chargedInputs=charged;
        }
    }

    private final List<Task> order;
    private final List<CondorVM> vms;
    private final Map<Integer,Integer> vmIndexById;
    private final Map<Task,Integer> taskIndex;
    private static final double EPS=1e-9;

    /** The task list MUST already be topologically ordered, as in LIWSA. */
    public StageInAwareScheduleEvaluator(List<Task> topologicalTaskOrder,List<CondorVM> orderedVms) {
        if(topologicalTaskOrder==null||topologicalTaskOrder.isEmpty()||
           orderedVms==null||orderedVms.isEmpty())throw new IllegalArgumentException("Empty task/VM list");
        order=new ArrayList<>(topologicalTaskOrder);
        vms=new ArrayList<>(orderedVms);
        vmIndexById=new HashMap<>();
        taskIndex=new IdentityHashMap<>();
        for(int v=0;v<vms.size();v++) {
            CondorVM vm=vms.get(v);
            if(vm==null||vm.getBw()<=0||vm.getMips()<=0||!Double.isFinite(vm.getCost()) ||
               vmIndexById.put(vm.getId(),v)!=null)throw new IllegalArgumentException("Invalid VM pool");
        }
        for(int k=0;k<order.size();k++){
            Task t=order.get(k);
            if(t==null||taskIndex.put(t,k)!=null)throw new IllegalArgumentException("Repeated task");
        }
        for(int k=0;k<order.size();k++){
            for(Object po:order.get(k).getParentList()){
                Integer idx=taskIndex.get((Task)po);
                if(idx==null||idx>=k)throw new IllegalArgumentException("Not topologically ordered");
            }
        }
    }

    /** Assignment keys and VM values are Cloudlet IDs and actual VM IDs. */
    public Result evaluate(Map<Integer,Integer> assignment) {
        if(assignment==null||assignment.size()!=order.size())
            throw new IllegalArgumentException("Incomplete task-to-VM assignment");
        int n=order.size();
        int m=vms.size();
        int[] selected=new int[n];
        for(int k=0;k<n;k++){
            Integer vmId=assignment.get(order.get(k).getCloudletId());
            Integer index=vmId==null?null:vmIndexById.get(vmId);
            if(index==null)throw new IllegalArgumentException("Invalid assignment for task "+k);
            selected[k]=index;
        }
        List<List<double[]>> calendars=new ArrayList<>();
        List<Set<String>> cached=new ArrayList<>();
        for(int v=0;v<m;v++){calendars.add(new ArrayList<>());cached.add(new HashSet<>());}
        Map<String,Integer> outputVmByFile=new HashMap<>();
        double[] finish=new double[n];
        double makespan=0,cost=0,totalStage=0,external=0,intermediate=0;
        int charged=0;
        for(int k=0;k<n;k++){
            Task task=order.get(k);
            int vm=selected[k];
            CondorVM dest=vms.get(vm);
            double ready=0;
            for(Object parentObj:task.getParentList()){
                int parentIndex=taskIndex.get((Task)parentObj);
                ready=Math.max(ready,finish[parentIndex]);
            }
            double stage=0;
            List<FileItem> files=task.getFileList();
            for(FileItem file:files){
                if(file.getType()!=Parameters.FileType.INPUT||!file.isRealInputFile(files))
                    continue;
                String name=file.getName();
                if(cached.get(vm).contains(name))continue;
                Integer sourceVm=outputVmByFile.get(name);
                double bandwidth=dest.getBw();
                if(sourceVm!=null && sourceVm!=vm) {
                    bandwidth=Math.min(bandwidth,vms.get(sourceVm).getBw());
                }
                if(!(bandwidth>0)||!Double.isFinite(file.getSize())||file.getSize()<0)
                    throw new IllegalArgumentException("Invalid file size/bandwidth "+name);
                double delay=file.getSize()/(double)Consts.MILLION/bandwidth;
                stage+=delay;
                if(sourceVm==null)external+=delay;
                else if(sourceVm!=vm)intermediate+=delay;
                if(delay>EPS)charged++;
                cached.get(vm).add(name);
            }
            double compute=task.getCloudletTotalLength()/dest.getMips();
            double duration=compute+stage;
            if(!Double.isFinite(duration)||duration<0)throw new IllegalStateException("Invalid duration");
            List<double[]> slots=calendars.get(vm);
            double start=ready;
            int at=0;
            while(at<slots.size()) {
                double[] slot=slots.get(at);
                if(start+duration<=slot[0])break;
                start=Math.max(start,slot[1]);
                at++;
            }
            double end=start+duration;
            slots.add(at,new double[]{start,end});
            finish[k]=end;
            cost+=duration*dest.getCost();
            makespan=Math.max(makespan,end);
            totalStage+=stage;
            for(FileItem file:files) {
                if(file.getType()==Parameters.FileType.OUTPUT) {
                    outputVmByFile.put(file.getName(),vm);
                    cached.get(vm).add(file.getName());
                }
            }
        }
        if(!Double.isFinite(makespan)||!Double.isFinite(cost) || makespan<=0||cost<0)
            throw new IllegalStateException("Non-finite objectives");
        return new Result(makespan,cost,totalStage,external,intermediate,charged);
    }
}
