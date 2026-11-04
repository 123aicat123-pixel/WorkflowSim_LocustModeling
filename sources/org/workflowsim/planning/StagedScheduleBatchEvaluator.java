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
            this(selection.screened,selection.selected,selection.predictedHypervolume,
                 choices,oldCalls,readyCalls,oldNanos,readyNanos,totalNanos);
        }
        SelectionResult(int[] screen,int[] selected,double predictedHV,
                        List<Map<Integer,Integer>> choices,
                        int oldCalls,int readyCalls,long oldNanos,long readyNanos,long totalNanos) {
            this.screened=screen.clone();
            this.selected=selected.clone();
            this.chosenMappings=new ArrayList<>();
            for(int id:this.selected)
                this.chosenMappings.add(new HashMap<>(choices.get(id)));
            this.predictedHypervolume=predictedHV;
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
     * Paired model-only controls, applied AFTER search on the EXACT SAME
     * genotype list as staged. Both use OLD-only reference; the full-ready
     * control spends N READY calls, while OLD-only spends zero.
     */
    public SelectionResult selectControl(List<Map<Integer,Integer>> genotypes,
                                         String mode,int finalK) {
        if(genotypes==null||genotypes.isEmpty()||finalK<1||
            finalK>genotypes.size()||
            !("old-greedy".equals(mode)||"ready-greedy".equals(mode)))
            throw new IllegalArgumentException("Invalid control mode or K");
        long start=System.nanoTime();
        double[][] cheap=new double[genotypes.size()][2];
        double mMax=0,cMax=0;
        for(int i=0;i<cheap.length;i++){
            StageInAwareScheduleEvaluator.Result p=old.evaluate(genotypes.get(i));
            cheap[i][0]=p.makespan;cheap[i][1]=p.cost;
            mMax=Math.max(mMax,p.makespan);
            cMax=Math.max(cMax,p.cost);
        }
        long afterOld=System.nanoTime();
        double[] reference={1.5*mMax+1e-6,1.5*cMax+1e-6};
        double[][] ranking=cheap;
        int calls=0;
        long readyNs=0;
        if("ready-greedy".equals(mode)) {
            ranking=new double[cheap.length][2];
            for(int i=0;i<ranking.length;i++){
                long begin=System.nanoTime();
                ReadyQueueScheduleEvaluator.Result p=ready.evaluate(genotypes.get(i));
                readyNs+=System.nanoTime()-begin;
                ranking[i][0]=p.makespan;ranking[i][1]=p.cost;
                calls++;
            }
        }
        GreedyStagedParetoSelector.Selection selected=
            GreedyStagedParetoSelector.select(ranking,finalK,reference);
        long end=System.nanoTime();
        return new SelectionResult(new int[0],selected.selected,
            selected.predictedHypervolume,genotypes,cheap.length,calls,
            afterOld-start,readyNs,end-start);
    }

    /**
     * Prospective alternative to staged-greedy. Spend T READY calls using
     * active OLD-space acquisition, then rank ALL N physical candidates on
     * one uniformly residual-corrected OLD scale. No mixed raw objectives.
     * The estimates are not certified and no simulator outcomes are read.
     */
    public SelectionResult selectActiveUniform(List<Map<Integer,Integer>> genotypes,
                                                int queryT,int outputK) {
        if(genotypes==null||genotypes.isEmpty()||queryT<outputK||
           outputK<1||queryT>genotypes.size())
            throw new IllegalArgumentException("Invalid active batch parameters");
        long begin=System.nanoTime();
        double[][] scores=new double[genotypes.size()][2];
        double maxM=0.,maxC=0.;
        for(int i=0;i<genotypes.size();i++) {
            StageInAwareScheduleEvaluator.Result p=old.evaluate(genotypes.get(i));
            scores[i][0]=p.makespan;scores[i][1]=p.cost;
            maxM=Math.max(maxM,p.makespan);
            maxC=Math.max(maxC,p.cost);
        }
        long afterOld=System.nanoTime();
        double[] reference={1.5*maxM+1e-6,1.5*maxC+1e-6};
        final int[] used={0};
        final long[] readyNanos={0L};
        ActiveUniformResidualSelector.Result output=
            ActiveUniformResidualSelector.select(scores,index->{
                long b=System.nanoTime();
                try {
                    ReadyQueueScheduleEvaluator.Result r=ready.evaluate(genotypes.get(index));
                    used[0]++;
                    return new double[]{r.makespan,r.cost};
                } finally {
                    readyNanos[0]+=System.nanoTime()-b;
                }
            },queryT,outputK,reference);
        long end=System.nanoTime();
        if(used[0]!=queryT||output.readyCalls!=queryT||
           output.queried.length!=queryT||output.selected.length!=outputK)
            throw new IllegalStateException("Unmatched active READY query budget");
        return new SelectionResult(output.queried,output.selected,
            output.predictedHypervolume,genotypes,genotypes.size(),used[0],
            afterOld-begin,readyNanos[0],end-begin);
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
