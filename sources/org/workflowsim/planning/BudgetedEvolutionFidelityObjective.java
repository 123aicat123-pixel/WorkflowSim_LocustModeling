package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import org.workflowsim.CondorVM;
import org.workflowsim.Task;

/**
 * Opt-in experimental DURING-EVOLUTION two-fidelity objective. One physical
 * task->VM map has exactly one fitness within this optimizer run (first-write).
 * Evaluation visits still count once each; expensive calls have an earned-token
 * cap released by counted visit index, independently of optimizer type.
 *
 * IMPORTANT: mixing old and ready scores is not a calibrated Pareto ranking;
 * all comparisons to original solvers and actual WorkflowSim remain mandatory.
 */
public final class BudgetedEvolutionFidelityObjective {
    public static final String PROPERTY="dagfla.evolutionFidelity";
    public enum Mode { OLD_CACHED, READY_CACHED, PERIODIC, RISK }

    public static final class Snapshot {
        public final String mode;
        public final int visits, cheapCalls, readyCalls, cacheHits, distinct;
        public final int maxReadyCalls, nearGateSkips;
        public final long cheapNanos, readyNanos;
        Snapshot(String mode,int v,int cheap,int ready,int hits,int distinct,
                 int quota,int skipped,long cn,long rn){
            this.mode=mode;visits=v;cheapCalls=cheap;readyCalls=ready;
            cacheHits=hits;this.distinct=distinct;maxReadyCalls=quota;
            nearGateSkips=skipped;cheapNanos=cn;readyNanos=rn;
        }
    }

    private static final ThreadLocal<BudgetedEvolutionFidelityObjective> CURRENT =
            new ThreadLocal<>();
    private final StageInAwareScheduleEvaluator insertion;
    private final ReadyQueueScheduleEvaluator queue;
    private final Mode mode;
    private final int maxVisits,quota;
    private int visits,cheapCalls,readyCalls,cacheHits,skipped;
    private long cheapNanos,readyNanos;
    private final Map<Map<Integer,Integer>,double[]> fixedFitness=new HashMap<>();
    private final List<double[]> cheapFront=new ArrayList<>();

    public BudgetedEvolutionFidelityObjective(List<Task> tasks,List<CondorVM> vms,
                        Mode mode,int maxVisits,int quota) {
        if(tasks==null||tasks.isEmpty()||vms==null||vms.isEmpty()||
           mode==null||maxVisits<1||quota<0||quota>maxVisits)
            throw new IllegalArgumentException("Invalid two-fidelity workload/budget");
        this.mode=mode;this.maxVisits=maxVisits;this.quota=quota;
        insertion=new StageInAwareScheduleEvaluator(tasks,vms);
        queue=new ReadyQueueScheduleEvaluator(tasks,vms);
        CURRENT.set(this);
    }
    public static BudgetedEvolutionFidelityObjective configured(
            List<Task> tasks,List<CondorVM> vms,int maxVisits) {
        String name=System.getProperty(PROPERTY,"off");
        if("off".equals(name))return null;
        if(!Boolean.getBoolean("workflowsim.planningStageInAware") ||
           Boolean.getBoolean("dagfla.useReadyQueueObjective") ||
           !"off".equals(System.getProperty("dagfla.dualModelMode","off")))
            throw new IllegalArgumentException("Evolution fidelity requires insertion baseline, no other objective mode");
        Mode mode;
        if("old-cached".equals(name))mode=Mode.OLD_CACHED;
        else if("ready-cached".equals(name))mode=Mode.READY_CACHED;
        else if("periodic".equals(name))mode=Mode.PERIODIC;
        else if("risk".equals(name))mode=Mode.RISK;
        else throw new IllegalArgumentException("Unknown evolution fidelity "+name);
        int quota=mode==Mode.OLD_CACHED?0:mode==Mode.READY_CACHED?maxVisits:
                  Integer.getInteger("dagfla.evolutionReadyBudget",378);
        return new BudgetedEvolutionFidelityObjective(tasks,vms,mode,maxVisits,quota);
    }
    public static Snapshot currentSnapshot() {
        BudgetedEvolutionFidelityObjective x=CURRENT.get();
        return x==null?null:x.snapshot();
    }
    public static void clearCurrent(){CURRENT.remove();}
    public Snapshot snapshot(){
        return new Snapshot(mode.toString().toLowerCase(),visits,cheapCalls,
                            readyCalls,cacheHits,fixedFitness.size(),quota,skipped,
                            cheapNanos,readyNanos);
    }
    private static boolean dominates(double[] a,double[] b) {
        return a[0]<=b[0]&&a[1]<=b[1]&&(a[0]<b[0]||a[1]<b[1]);
    }
    private boolean nearSkyline(double[] current) {
        if(cheapFront.isEmpty())return true;
        for(double[] point:cheapFront) {
            if(dominates(point,current) &&
               current[0]>point[0]*1.01 &&
               current[1]>point[1]*1.01)
                return false;
        }
        return true;
    }
    private void extendFront(double[] candidate) {
        for(double[] point:cheapFront)
            if(dominates(point,candidate))return;
        cheapFront.removeIf(point->dominates(candidate,point));
        cheapFront.add(candidate.clone());
    }

    public double[] evaluate(Map<Integer,Integer> assignment) {
        if(assignment==null||assignment.isEmpty())
            throw new IllegalArgumentException("Empty VM assignment");
        if(visits>=maxVisits)throw new IllegalStateException("Fitness evaluation cap exceeded");
        visits++;
        Map<Integer,Integer> key=Collections.unmodifiableMap(new TreeMap<>(assignment));
        double[] prior=fixedFitness.get(key);
        if(prior!=null) {
            cacheHits++;
            return prior.clone();
        }
        double[] objective;
        double[] cheapObjective=null;
        if(mode==Mode.READY_CACHED) {
            long begin=System.nanoTime();
            ReadyQueueScheduleEvaluator.Result high=queue.evaluate(key);
            readyNanos+=System.nanoTime()-begin;
            readyCalls++;
            objective=new double[]{high.makespan,high.cost};
        } else {
            long begin=System.nanoTime();
            StageInAwareScheduleEvaluator.Result cheap=insertion.evaluate(key);
            cheapNanos+=System.nanoTime()-begin;
            cheapCalls++;
            cheapObjective=new double[]{cheap.makespan,cheap.cost};
            objective=cheapObjective.clone();
            if(mode==Mode.PERIODIC||mode==Mode.RISK) {
                boolean near=nearSkyline(cheapObjective);
                int earned=(int)(((long)visits*quota)/maxVisits);
                if(earned>readyCalls && (mode==Mode.PERIODIC||near)) {
                    long highBegin=System.nanoTime();
                    ReadyQueueScheduleEvaluator.Result high=queue.evaluate(key);
                    readyNanos+=System.nanoTime()-highBegin;
                    readyCalls++;
                    objective=new double[]{high.makespan,high.cost};
                } else if(earned>readyCalls && !near) {
                    skipped++;
                }
                // Fixed policy consults cheap objectives only from previous
                // distinct genotypes; high-fidelity truth never enters gate.
                extendFront(cheapObjective);
            }
        }
        if(!Double.isFinite(objective[0])||objective[0]<=0||
           !Double.isFinite(objective[1])||objective[1]<=0)
            throw new IllegalStateException("Invalid cached evolutionary fitness");
        fixedFitness.put(key,objective.clone());
        int earned=(int)(((long)visits*quota)/maxVisits);
        if(readyCalls>earned||readyCalls>quota||fixedFitness.size()+cacheHits!=visits||
           (mode==Mode.OLD_CACHED && (readyCalls!=0||cheapCalls!=fixedFitness.size()))||
           (mode==Mode.READY_CACHED && (cheapCalls!=0||readyCalls!=fixedFitness.size())))
            throw new IllegalStateException("Inconsistent fidelity evaluation accounting");
        return objective.clone();
    }
}
