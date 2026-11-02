package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.cloudbus.cloudsim.Consts;
import org.workflowsim.CondorVM;
import org.workflowsim.FileItem;
import org.workflowsim.Task;
import org.workflowsim.utils.Parameters;

/**
 * Planning-level makespan/cost evaluator for FLA scheduling algorithms.
 *
 * Based on the decoder in WorkflowSim_LocustModeling's
 * LIWSAPlanningAlgorithm.java (master branch). In REPOSITORY_COMPATIBLE mode,
 * reproduce its task order, parent/file transfer calculations, cost, and
 * insertion placement so algorithm comparisons remain diagnostic. The alternate
 * VERIFIED_EARLIEST_INSERTION mode is an independent, timeline-safe decoder
 * for detecting/safely avoiding historical insertion issues. DO NOT mix the
 * modes across competing algorithms in one comparison.
 *
 * Genotype[k] is a ZERO-BASED INDEX into the constructor's vm list, for
 * taskOrder[k]; do not confuse it with CondorVM.getId().
 *
 * This class is stateful (reuses scheduling arrays) and NOT thread-safe.
 * The example benchmark runs its CloudSim simulations sequentially.
 */
public final class FLAScheduleEvaluator {

    public enum InsertionMode {
        REPOSITORY_COMPATIBLE,
        VERIFIED_EARLIEST_INSERTION
    }

    /** Detached snapshot of one decoded schedule, in taskOrder order. */
    public static final class ScheduleTrace {
        public final double makespan;
        public final double cost;
        public final double[] starts;
        public final double[] finishes;
        public final int[] vmIndices;

        private ScheduleTrace(double makespan, double cost,
                double[] starts, double[] finishes, int[] vmIndices) {
            this.makespan = makespan;
            this.cost = cost;
            this.starts = starts.clone();
            this.finishes = finishes.clone();
            this.vmIndices = vmIndices.clone();
        }
    }

    private final List<Task> taskOrder;
    private final List<CondorVM> vmList;
    private final InsertionMode insertionMode;
    private final boolean enforcePes;

    private final int n;
    private final int m;
    private final int[][] parentIdx;
    private final double[][] parentTransfer;
    private final double[][] duration;
    private final double[] vmPrice;
    private final int[][] feasibleVmIndices;

    private final double[][] eventStart;
    private final double[][] eventFinish;
    private final int[] eventCount;
    private final double[] taskFinish;
    private final int[] taskAssignedVm;
    private final double[] currentStarts;

    private long objectiveEvaluations;
    private final StageInAwareScheduleEvaluator stageInAwareEvaluator;
    /** Optional model parity switch: -Dworkflowsim.planningStageInAware=true */

    /** Defaults to validated earliest insertion and no extra PE rejection.
     * Use REPOSITORY_COMPATIBLE explicitly for a controlled parity audit. */
    public FLAScheduleEvaluator(List<Task> tasks, List<CondorVM> vms) {
        this(tasks, vms, InsertionMode.VERIFIED_EARLIEST_INSERTION, false);
    }

    /**
     * @param enforcePes if true, reject assignments with VM PEs < task PEs.
     * This is stricter than the current LIWSA decoder; use the SAME policy
     * for all algorithms before making scientific performance comparisons.
     */
    public FLAScheduleEvaluator(List<Task> tasks, List<CondorVM> vms,
            InsertionMode mode, boolean enforcePes) {
        if (tasks == null || tasks.isEmpty() || vms == null || vms.isEmpty()) {
            throw new IllegalArgumentException("Task and VM lists must be non-empty");
        }
        if (mode == null) {
            throw new IllegalArgumentException("Insertion mode must not be null");
        }
        this.insertionMode = mode;
        this.enforcePes = enforcePes;
        this.vmList = Collections.unmodifiableList(new ArrayList<>(vms));
        for (CondorVM vm : this.vmList) {
            if (vm == null || !(vm.getMips() > 0.0) || !(vm.getBw() > 0)
                    || !Double.isFinite(vm.getMips()) || !Double.isFinite(vm.getCost())) {
                throw new IllegalArgumentException("Invalid VM parameters");
            }
        }
        this.taskOrder = Collections.unmodifiableList(topologicalOrder(tasks));
        this.n = taskOrder.size();
        this.m = vmList.size();
        this.parentIdx = new int[n][];
        this.parentTransfer = new double[n][];
        this.duration = new double[n][m];
        this.vmPrice = new double[m];
        this.feasibleVmIndices = new int[n][];
        this.eventStart = new double[m][n];
        this.eventFinish = new double[m][n];
        this.eventCount = new int[m];
        this.taskFinish = new double[n];
        this.taskAssignedVm = new int[n];
        this.currentStarts = new double[n];

        prepareDecoder();
        stageInAwareEvaluator = Boolean.getBoolean("workflowsim.planningStageInAware")
                ? new StageInAwareScheduleEvaluator(taskOrder,vmList) : null;
    }

    public List<Task> getTaskOrder() { return taskOrder; }
    public List<CondorVM> getVmList() { return vmList; }
    public long getObjectiveEvaluations() { return objectiveEvaluations; }

    /** Legal VM indices when PE constraints are enforced. */
    public int[] getFeasibleVmIndices(int taskIndex) {
        if (taskIndex < 0 || taskIndex >= n) {
            throw new IndexOutOfBoundsException("Invalid task index: " + taskIndex);
        }
        return feasibleVmIndices[taskIndex].clone();
    }

    private static int computeDepth(Task t, Map<Task,Integer> depth,
            Map<Task,Boolean> visiting) {
        Integer cached = depth.get(t);
        if (cached != null) { return cached; }
        if (visiting.put(t, Boolean.TRUE) != null) {
            throw new IllegalArgumentException("Cycle in task DAG");
        }
        int d = 0;
        for (Task parent : t.getParentList()) {
            d = Math.max(d, computeDepth(parent, depth, visiting) + 1);
        }
        visiting.remove(t);
        depth.put(t,d);
        return d;
    }

    private static List<Task> topologicalOrder(List<Task> tasks) {
        Map<Task,Integer> depth = new IdentityHashMap<>();
        Map<Task,Boolean> visiting = new IdentityHashMap<>();
        Map<Task,Boolean> contained = new IdentityHashMap<>();
        for (Task t:tasks) {
            if (t == null || contained.put(t, Boolean.TRUE) != null) {
                throw new IllegalArgumentException("Null or duplicate task object");
            }
        }
        for (Task t:tasks) {
            for (Task p:t.getParentList()) {
                if (!contained.containsKey(p)) {
                    throw new IllegalArgumentException("Task parent outside task list");
                }
            }
            computeDepth(t,depth,visiting);
        }
        List<Task> order = new ArrayList<>(tasks);
        Collections.sort(order, (a,b) -> {
            int da=depth.get(a), db=depth.get(b);
            if (da!=db) return Integer.compare(da,db);
            double la=a.getCloudletTotalLength(), lb=b.getCloudletTotalLength();
            if (la!=lb) return Double.compare(lb,la);
            return Integer.compare(a.getCloudletId(),b.getCloudletId());
        });
        return order;
    }

    private void prepareDecoder() {
        double averageBandwidth = 0.0;
        for (CondorVM vm : vmList) { averageBandwidth += vm.getBw(); }
        averageBandwidth /= m;
        Map<Task,Integer> taskIndex = new IdentityHashMap<>();
        for (int k=0; k<n; k++) { taskIndex.put(taskOrder.get(k),k); }
        for (int v=0;v<m;v++) { vmPrice[v]=vmList.get(v).getCost(); }
        for (int k=0; k<n; k++) {
            Task task=taskOrder.get(k);
            List<Task> ps=task.getParentList();
            parentIdx[k]=new int[ps.size()];
            parentTransfer[k]=new double[ps.size()];
            for (int q=0;q<ps.size();q++) {
                Task parent=ps.get(q);
                int p=taskIndex.get(parent);
                if (p>=k) throw new IllegalArgumentException("Non-topological task order");
                parentIdx[k][q]=p;
                parentTransfer[k][q]=transferTime(parent,task,averageBandwidth);
            }
            for(int v=0;v<m;v++) {
                duration[k][v]=task.getCloudletTotalLength()/vmList.get(v).getMips();
            }
            int count=0;
            for(int v=0;v<m;v++) {
                if(vmList.get(v).getNumberOfPes()>=task.getNumberOfPes()) count++;
            }
            int[] feasible=new int[count];
            int off=0;
            for(int v=0;v<m;v++) {
                if(vmList.get(v).getNumberOfPes()>=task.getNumberOfPes()) feasible[off++]=v;
            }
            feasibleVmIndices[k]=feasible;
            if(enforcePes && count==0) {
                throw new IllegalArgumentException("Task has no PE-feasible VM: " +task.getCloudletId());
            }
        }
    }

    /** Matches LIWSA's output-file / input-file name and byte-to-Mbit logic. */
    private static double transferTime(Task parent, Task child, double bandwidth) {
        double bytes=0.0;
        for (FileItem p:parent.getFileList()) {
            if(p.getType()!=Parameters.FileType.OUTPUT) continue;
            for(FileItem c:child.getFileList()) {
                if(c.getType()==Parameters.FileType.INPUT && c.getName().equals(p.getName())) {
                    bytes+=c.getSize();
                    break;
                }
            }
        }
        return (bytes/Consts.MILLION)*8/bandwidth;
    }

    private void validateGenotype(int[] g) {
        if (g==null || g.length!=n) throw new IllegalArgumentException("Invalid genotype length");
        for(int k=0;k<n;k++) {
            int v=g[k];
            if(v<0 || v>=m) throw new IllegalArgumentException("Invalid VM index at task "+k+": "+v);
            if(enforcePes && vmList.get(v).getNumberOfPes()<taskOrder.get(k).getNumberOfPes()) {
                throw new IllegalArgumentException("PE-infeasible mapping for task "+k);
            }
        }
    }

    private void insertEvent(int v,int pos,double start,double finish) {
        int size=eventCount[v];
        double[] st=eventStart[v], fi=eventFinish[v];
        if(pos<size) {
            System.arraycopy(st,pos,st,pos+1,size-pos);
            System.arraycopy(fi,pos,fi,pos+1,size-pos);
        }
        st[pos]=start;
        fi[pos]=finish;
        eventCount[v]=size+1;
    }

    /** Source-compatible insertion placement. Keep separate for auditing. */
    private double placeRepository(int v,double readyTime,double d) {
        double[] st=eventStart[v],fi=eventFinish[v];
        int size=eventCount[v];
        if(size==0) {
            insertEvent(v,0,readyTime,readyTime+d);
            return readyTime+d;
        }
        if(size==1) {
            double start;
            int pos;
            if(readyTime>=fi[0]) { pos=1; start=readyTime; }
            else if(readyTime+d<=st[0]) { pos=0; start=readyTime; }
            else { pos=1; start=fi[0]; }
            insertEvent(v,pos,start,start+d);
            return start+d;
        }
        double start=Math.max(readyTime,fi[size-1]);
        double finish=start+d;
        int pos=size;
        int i=size-1;
        int j=size-2;
        while(j>=0) {
            double currentStart=st[i];
            double previousFinish=fi[j];
            if(readyTime>previousFinish) {
                if(readyTime+d<=currentStart) {
                    start=readyTime;
                    finish=readyTime+d;
                }
                break;
            }
            if(previousFinish+d<=currentStart) {
                start=previousFinish;
                finish=previousFinish+d;
                pos=i;
            }
            i--;j--;
        }
        if(readyTime+d<=st[0]) {
            insertEvent(v,0,readyTime,readyTime+d);
            return readyTime+d;
        }
        insertEvent(v,pos,start,finish);
        return finish;
    }

    /** Independently implemented earliest feasible gap placement. */
    private double placeVerified(int v,double readyTime,double d) {
        double start=readyTime;
        int pos=0;
        while(pos<eventCount[v]) {
            if(start+d<=eventStart[v][pos]) break;
            start=Math.max(start,eventFinish[v][pos]);
            pos++;
        }
        double finish=start+d;
        insertEvent(v,pos,start,finish);
        return finish;
    }

    public double[] evaluate(int[] g) {
        return decode(g);
    }

    public ScheduleTrace evaluateWithTrace(int[] g) {
        if(stageInAwareEvaluator!=null)
            throw new IllegalStateException("Legacy interval trace is not valid for stage-in-aware objectives");
        double[] mc = decode(g);
        return new ScheduleTrace(mc[0],mc[1],currentStarts,taskFinish,g);
    }

    private double[] decode(int[] g) {
        validateGenotype(g);
        objectiveEvaluations++;
        Arrays.fill(eventCount,0);
        double cost=0.0, makespan=0.0;
        for (int k=0;k<n;k++) {
            int v=g[k];
            double ready=0.0;
            for(int q=0;q<parentIdx[k].length;q++) {
                int p=parentIdx[k][q];
                double pf=taskFinish[p];
                if(taskAssignedVm[p]!=v) pf+=parentTransfer[k][q];
                ready=Math.max(ready,pf);
            }
            double d=duration[k][v];
            double fin=(insertionMode==InsertionMode.REPOSITORY_COMPATIBLE)
                ?placeRepository(v,ready,d)
                :placeVerified(v,ready,d);
            taskFinish[k]=fin;
            taskAssignedVm[k]=v;
            currentStarts[k]=fin-d;
            cost+=d*vmPrice[v];
            makespan=Math.max(makespan,fin);
        }
        if(stageInAwareEvaluator!=null) {
            StageInAwareScheduleEvaluator.Result corrected =
                    stageInAwareEvaluator.evaluate(toAssignment(g));
            makespan=corrected.makespan;
            cost=corrected.cost;
        }
        UnifiedCandidateRecorder.record(taskOrder, vmList, g, makespan, cost);
        return new double[]{makespan,cost};
    }

    public Map<Integer,Integer> toAssignment(int[] genotype) {
        validateGenotype(genotype);
        Map<Integer,Integer> result=new LinkedHashMap<>();
        for(int k=0;k<n;k++) {
            result.put(taskOrder.get(k).getCloudletId(),vmList.get(genotype[k]).getId());
        }
        return result;
    }

    public int[] fromAssignment(Map<Integer,Integer> assignment) {
        if(assignment==null) throw new IllegalArgumentException("Null assignment");
        Map<Integer,Integer> vmIdToIdx=new HashMap<>();
        for(int v=0;v<m;v++) vmIdToIdx.put(vmList.get(v).getId(),v);
        int[] g=new int[n];
        for(int k=0;k<n;k++) {
            Integer vmId=assignment.get(taskOrder.get(k).getCloudletId());
            Integer idx=vmIdToIdx.get(vmId);
            if(idx==null) throw new IllegalArgumentException("Missing or invalid VM ID for cloudlet "+taskOrder.get(k).getCloudletId());
            g[k]=idx;
        }
        validateGenotype(g);
        return g;
    }

    public void commitAssignment(int[] genotype) {
        validateGenotype(genotype);
        for(int k=0;k<n;k++) {
            taskOrder.get(k).setVmId(vmList.get(genotype[k]).getId());
        }
    }
}