package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.workflowsim.CondorVM;
import org.workflowsim.Task;

/**
 * Batch adapter connecting the staged greedy callback to the actual cloud
 * workflow Java OLD and READY decoder classes (not a synthetic model).
 *
 * Research only: chooses K already-existing candidate Task->VM maps. It does
 * not replace an optimizer's per-genotype target fitness, mutate a schedule,
 * or alter WorkflowSim runtime. The reported time is Java batch time only.
 */
public final class StagedScheduleBatchEvaluator {
    private final StageInAwareScheduleEvaluator old;
    private final ReadyQueueScheduleEvaluator ready;

    public static final class SelectionResult {
        public final int[] screened;
        public final int[] selected;
        public final List<Map<Integer,Integer>> chosenMappings;
        public final double predictedHypervolume;
        public final int oldCalls,readyCalls;
        public final long oldNanos,readyNanos,totalNanos;
        SelectionResult(GreedyStagedParetoSelector.Refined selection,
                        List<Map<Integer,Integer>> choices,
                        int oldCalls,int readyCalls,long oldNanos,long readyNanos,long totalNanos) {
            this.screened=selection.screened.clone();
            this.selected=selection.selected.clone();
            this.chosenMappings=new ArrayList<>();
            for(int id:this.selected)
                this.chosenMappings.add(new HashMap<>(choices.get(id)));
            this.predictedHypervolume=selection.predictedHypervolume;
            this.oldCalls=oldCalls;
            this.readyCalls=readyCalls;
            this.oldNanos=oldNanos;
            this.readyNanos=readyNanos;
            this.totalNanos=totalNanos;
        }
    }

    public StagedScheduleBatchEvaluator(List<Task> tasks,List<CondorVM> vmPool) {
        this.old=new StageInAwareScheduleEvaluator(tasks,vmPool);
        this.ready=new ReadyQueueScheduleEvaluator(tasks,vmPool);
    }

    /**
     * Evaluate all candidates once with OLD, select an OLD-HV shortlist
     * of T, evaluate READY exactly T times and pick K from mixed predictions.
     * A single cheap-only reference for both selection stages is frozen as
     * 1.5 x OLD objective maxima, plus tiny positivity margin.
     */
    public SelectionResult select(List<Map<Integer,Integer>> genotypes,
                                  int screenT,int outputK) {
        if(genotypes==null||genotypes.isEmpty()||outputK<1||
                screenT<outputK||screenT>genotypes.size())
            throw new IllegalArgumentException("Invalid staged candidate budget");
        long begin=System.nanoTime();
        double[][] scores=new double[genotypes.size()][2];
        for(int i=0;i<genotypes.size();i++) {
            StageInAwareScheduleEvaluator.Result x=old.evaluate(genotypes.get(i));
            scores[i][0]=x.makespan;
            scores[i][1]=x.cost;
        }
        long afterOld=System.nanoTime();
        double maxM=0,maxC=0;
        for(double[] r:scores) {
            maxM=Math.max(maxM,r[0]);
            maxC=Math.max(maxC,r[1]);
        }
        final double[] reference={1.5*maxM+1e-6,1.5*maxC+1e-6};
        final int[] readyCalls={0};
        final long[] readyNanos={0};
        GreedyStagedParetoSelector.Refined result=
            GreedyStagedParetoSelector.refine(scores,i-> {
                long b=System.nanoTime();
                ReadyQueueScheduleEvaluator.Result value=ready.evaluate(genotypes.get(i));
                long cost=System.nanoTime()-b;
                readyNanos[0]+=cost;
                readyCalls[0]++;
                return new double[]{value.makespan,value.cost};
            },screenT,outputK,reference);
        long finish=System.nanoTime();
        if(readyCalls[0]!=screenT||result.expensiveCalls!=screenT)
            throw new IllegalStateException("Violated high-accuracy budget");
        if(finish<begin||afterOld<begin||readyNanos[0]<0)
            throw new IllegalStateException("Invalid Java monotonic measurements");
        return new SelectionResult(result,genotypes,genotypes.size(),readyCalls[0],
                                   afterOld-begin,readyNanos[0],finish-begin);
    }
}
