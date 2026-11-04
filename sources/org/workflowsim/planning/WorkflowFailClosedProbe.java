package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import org.workflowsim.CondorVM;
import org.workflowsim.Task;

/**
 * Read-only bridge from real workflow TaskID->VMID assignments to the
 * fail-closed two-fidelity gate. This is a research probe, NOT an optimizer.
 * Until an external calibration protocol is validated, certification is
 * intentionally disabled; READY is still only a model, not simulation truth.
 */
public final class WorkflowFailClosedProbe {
    public static final class Result {
        public final String firstId, secondId;
        public final double[] oldFirst, oldSecond;
        public final FailClosedFidelityGate.Outcome decision;
        Result(String a,String b,double[] x,double[] y,FailClosedFidelityGate.Outcome d) {
            firstId=a;secondId=b;oldFirst=x.clone();oldSecond=y.clone();decision=d;
        }
    }
    private final StageInAwareScheduleEvaluator old;
    private final ReadyQueueScheduleEvaluator ready;
    private final FailClosedFidelityGate gate;
    private final Set<Integer> taskIds = new HashSet<>();
    private final Set<Integer> vmIds = new HashSet<>();
    private final Map<String,Map<Integer,Integer>> assignments = new HashMap<>();
    private final Map<String,double[]> oldCache = new HashMap<>();
    private int oldCalls,oldHits;
    private long oldNanos,readyNanos;

    public WorkflowFailClosedProbe(List<Task> tasks,List<CondorVM> vms,int maxReadyCalls) {
        if(tasks==null||tasks.isEmpty()||vms==null||vms.isEmpty())
            throw new IllegalArgumentException("Missing real Task/VM context");
        for(Task task:tasks)
            if(task==null||!taskIds.add(task.getCloudletId()))
                throw new IllegalArgumentException("Repeated/invalid task");
        for(CondorVM vm:vms)
            if(vm==null||!vmIds.add(vm.getId()))
                throw new IllegalArgumentException("Repeated/invalid VM");
        old=new StageInAwareScheduleEvaluator(tasks,vms);
        ready=new ReadyQueueScheduleEvaluator(tasks,vms);
        gate=new FailClosedFidelityGate(maxReadyCalls);
    }

    /**
     * Canonical assignment identity uses actual Task IDs and actual VM IDs,
     * never genotype indices. Invalid or incomplete maps fail before decoding.
     */
    public String register(Map<Integer,Integer> raw) {
        if(raw==null||raw.size()!=taskIds.size()||!raw.keySet().equals(taskIds))
            throw new IllegalArgumentException("Incomplete/unknown TaskIDs");
        TreeMap<Integer,Integer> ordered=new TreeMap<>();
        for(Map.Entry<Integer,Integer> entry:raw.entrySet()) {
            if(entry.getValue()==null||!vmIds.contains(entry.getValue()))
                throw new IllegalArgumentException("Unknown VM ID");
            ordered.put(entry.getKey(),entry.getValue());
        }
        StringBuilder id=new StringBuilder();
        for(Map.Entry<Integer,Integer> entry:ordered.entrySet()) {
            if(id.length()>0)id.append(';');
            id.append(entry.getKey()).append('=').append(entry.getValue());
        }
        String key=id.toString();
        Map<Integer,Integer> prev=assignments.putIfAbsent(
            key,Collections.unmodifiableMap(ordered));
        if(prev!=null&&!prev.equals(ordered))
            throw new IllegalStateException("Canonical Task/VM collision");
        return key;
    }

    private double[] oldScore(String id) {
        double[] cached=oldCache.get(id);
        if(cached!=null) {
            oldHits++;
            return cached.clone();
        }
        long started=System.nanoTime();
        StageInAwareScheduleEvaluator.Result prediction=old.evaluate(assignments.get(id));
        oldNanos+=System.nanoTime()-started;
        oldCalls++;
        double[] score={prediction.makespan,prediction.cost};
        if(!Double.isFinite(score[0])||score[0]<=0||
           !Double.isFinite(score[1])||score[1]<0)
            throw new IllegalStateException("Invalid OLD model prediction");
        oldCache.put(id,score.clone());
        return score;
    }

    /**
     * No certified elimination: coverage evidence is NOT available.
     * Two READY model forecasts are requested when possible; exhausted
     * budget and any model failure return KEEP_BOTH.
     */
    public Result assess(Map<Integer,Integer> first,Map<Integer,Integer> second) {
        String a=register(first),b=register(second);
        double[] x=oldScore(a),y=oldScore(b);
        FailClosedFidelityGate.Outcome result=gate.assess(
            a,b,x,y,null,null,false,id -> {
                long started=System.nanoTime();
                try {
                    ReadyQueueScheduleEvaluator.Result r=ready.evaluate(assignments.get(id));
                    return new double[]{r.makespan,r.cost};
                } finally {
                    readyNanos+=System.nanoTime()-started;
                }
            });
        if(result.kind==FailClosedFidelityGate.Kind.CONDITIONAL_FIRST_DOMINATES ||
           result.kind==FailClosedFidelityGate.Kind.CONDITIONAL_SECOND_DOMINATES)
            throw new IllegalStateException("Uncalibrated probe must never certify");
        return new Result(a,b,x,y,result);
    }
    public int oldCalls(){return oldCalls;}
    public int oldCacheHits(){return oldHits;}
    public int readyCalls(){return gate.readyCalls();}
    public int readyCacheHits(){return gate.cacheHits();}
    public int registeredAssignments(){return assignments.size();}
    public long oldNanos(){return oldNanos;}
    public long readyNanos(){return readyNanos;}
    public int readyBudget(){return gate.readyBudget();}
}
