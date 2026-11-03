package org.workflowsim.planning;

import java.util.List;
import java.util.Map;
import org.workflowsim.Task;
import org.workflowsim.CondorVM;

/**
 * Experiment-only, fixed-genotype multi-model robust schedule estimate.
 *
 * Both predictors are deterministic, use ONLY the input DAG, VM pool and
 * assignment, and have no access to actual WorkflowSim replay labels.
 * `mean` limits the effect of either model's mistakes. `worst` is the
 * componentwise upper envelope over feasible scenario predictions.
 *
 * One invocation is ONE genotype objective evaluation even though the
 * internal effort includes two models. Search wall time is reported separately.
 * No model selection is learned from previously observed simulator outcomes.
 */
public final class DualModelScheduleObjective {
    public enum Mode { MEAN, WORST }

    private final StageInAwareScheduleEvaluator insertion;
    private final ReadyQueueScheduleEvaluator ready;
    private final Mode mode;

    public DualModelScheduleObjective(List<Task> tasks,List<CondorVM> vms,Mode mode) {
        if(mode==null)throw new IllegalArgumentException("Missing dual model mode");
        this.insertion=new StageInAwareScheduleEvaluator(tasks,vms);
        this.ready=new ReadyQueueScheduleEvaluator(tasks,vms);
        this.mode=mode;
    }

    public static Mode parseMode(String raw) {
        if("mean".equals(raw))return Mode.MEAN;
        if("worst".equals(raw))return Mode.WORST;
        throw new IllegalArgumentException("Unsupported dual decoder mode: "+raw);
    }

    public double[] evaluate(Map<Integer,Integer> genotype) {
        StageInAwareScheduleEvaluator.Result old=insertion.evaluate(genotype);
        ReadyQueueScheduleEvaluator.Result queue=ready.evaluate(genotype);
        return combine(mode,old.makespan,old.cost,queue.makespan,queue.cost);
    }

    public static double[] combine(Mode mode,double oldM,double oldC,double queueM,double queueC) {
        if(mode==null)throw new IllegalArgumentException("Missing mode");
        double[] inputs={oldM,oldC,queueM,queueC};
        for(int i=0;i<inputs.length;i++){
            if(!Double.isFinite(inputs[i]) || inputs[i]<(i%2==0?1e-15:0))
                throw new IllegalArgumentException("Invalid model prediction");
        }
        double m,c;
        if(mode==Mode.MEAN){
            m=oldM/2.0+queueM/2.0;
            c=oldC/2.0+queueC/2.0;
        } else {
            m=Math.max(oldM,queueM);
            c=Math.max(oldC,queueC);
        }
        if(!Double.isFinite(m)||!Double.isFinite(c)||m<=0||c<0)
            throw new IllegalStateException("Invalid combined objective");
        return new double[]{m,c};
    }
}
