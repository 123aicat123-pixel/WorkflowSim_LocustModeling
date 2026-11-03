package org.workflowsim.planning;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.workflowsim.CondorVM;
import org.workflowsim.Task;

/**
 * Experimental bounded queue-conflict Pareto-risk relocation (NOT yet a
 * validated FLA contribution). Pure genotype-to-genotype proposal.
 *
 * 1. Find a waiting task with the largest ready-queue wait multiplied by its
 *    upward DAG importance; only already-ready tasks can be dispatched.
 * 2. Choose at most TWO distinct alternatives: projected low load/latency
 *    and low workload-priced resource.
 * 3. Forecast the current mapping and at most two alternative mappings using
 *    the frozen event-driven ready-queue estimator, NOT actual CloudSim labels.
 * 4. In the latency group, accept improved predicted makespan only with <=1%
 *    cost risk; in the cost group, accept lower predicted cost only with <=1%
 *    makespan risk. No change if a guard fails.
 *
 * Each internal prediction is counted in Result; only the FINAL selected
 * genotype is evaluated by the FLA target objective. Evaluation-count parity
 * alone does not imply computational parity, so report wall time and probes.
 */
public final class QueueConflictRiskRelocation {
    private static final double EPS=1e-9;
    private static final double MAX_OTHER_OBJECTIVE_RELATIVE_RISK=0.01;
    private QueueConflictRiskRelocation(){}

    public static final class Result {
        public final int taskId;
        public final int forecastCount;
        public final int candidateCount;
        public final boolean moved;
        public final double improvementRatio;
        private Result(int id,int forecasts,int candidates,boolean moved,double improvement) {
            taskId=id;forecastCount=forecasts;candidateCount=candidates;
            this.moved=moved;improvementRatio=improvement;
        }
    }

    private static ReadyQueueScheduleEvaluator.Result forecast(
            int[] genes,List<Task> tasks,List<CondorVM> vms,
            ReadyQueueScheduleEvaluator model) {
        Map<Integer,Integer> mapping=new HashMap<>();
        for(int k=0;k<genes.length;k++) {
            if(genes[k]<0||genes[k]>=vms.size())
                throw new IllegalArgumentException("Unregistered VM gene");
            if(mapping.put(tasks.get(k).getCloudletId(),vms.get(genes[k]).getId())!=null)
                throw new IllegalArgumentException("Duplicate original task");
        }
        return model.evaluate(mapping);
    }

    public static Result propose(int[] genes,List<Task> tasks,List<CondorVM> vms,
            int[][] allowed,double[] importance,double[][] optimisticService,
            boolean latencyFocused,ReadyQueueScheduleEvaluator model) {
        int n=tasks.size();
        if(model==null||genes==null||genes.length!=n||vms==null||vms.isEmpty()||
                allowed==null||allowed.length!=n||
                importance==null||importance.length!=n||
                optimisticService==null||optimisticService.length!=n)
            throw new IllegalArgumentException("Inconsistent queue-risk proposal inputs");

        ReadyQueueScheduleEvaluator.Result base=forecast(genes,tasks,vms,model);
        Map<Integer,Integer> indexByTask=new HashMap<>();
        for(int k=0;k<n;k++)
            if(indexByTask.put(tasks.get(k).getCloudletId(),k)!=null)
                throw new IllegalArgumentException("Repeated original task ID");

        int chosenTask=-1;
        double maximumRiskScore=EPS;
        for(int k=0;k<n;k++) {
            if(allowed[k]==null||allowed[k].length<2)continue;
            double ready=0;
            for(Object object:tasks.get(k).getParentList()) {
                Task parent=(Task)object;
                Integer parentIndex=indexByTask.get(parent.getCloudletId());
                if(parentIndex==null)
                    throw new IllegalArgumentException("Unknown parent in forecast");
                ready=Math.max(ready,base.finishes[parentIndex]);
            }
            double waiting=Math.max(0,base.starts[k]-ready);
            double risk=waiting*Math.max(0,importance[k]);
            if(risk>maximumRiskScore+EPS ||
                    (Math.abs(risk-maximumRiskScore)<=EPS && chosenTask>=0 &&
                     tasks.get(k).getCloudletId()<tasks.get(chosenTask).getCloudletId())) {
                chosenTask=k;
                maximumRiskScore=risk;
            }
        }
        if(chosenTask<0)return new Result(-1,1,0,false,0);

        double[] vmWorkload=new double[vms.size()];
        for(int k=0;k<n;k++)if(k!=chosenTask) {
            if(optimisticService[k]==null||genes[k]>=optimisticService[k].length)
                throw new IllegalArgumentException("Missing VM resource service information");
            vmWorkload[genes[k]]+=optimisticService[k][genes[k]];
        }
        int fastest=-1,cheapest=-1;
        double fastestScore=Double.POSITIVE_INFINITY,cheapestScore=Double.POSITIVE_INFINITY;
        for(int vm:allowed[chosenTask]) {
            if(vm==genes[chosenTask])continue;
            if(vm<0||vm>=vms.size()||
                    optimisticService[chosenTask]==null||
                    vm>=optimisticService[chosenTask].length)
                throw new IllegalArgumentException("Invalid relocation alternative");
            double duration=optimisticService[chosenTask][vm];
            if(!Double.isFinite(duration)||duration<0)
                throw new IllegalArgumentException("Invalid optimistic duration");
            double load=vmWorkload[vm]/Math.max(1.0,n/4.0);
            double latency=duration+0.35*load;
            double cost=(duration+0.04*load)*vms.get(vm).getCost();
            if(latency<fastestScore-EPS || (Math.abs(latency-fastestScore)<=EPS && (fastest<0||vm<fastest))) {
                fastestScore=latency;fastest=vm;
            }
            if(cost<cheapestScore-EPS || (Math.abs(cost-cheapestScore)<=EPS && (cheapest<0||vm<cheapest))) {
                cheapestScore=cost;cheapest=vm;
            }
        }
        int oldVm=genes[chosenTask];
        int winningVm=-1;
        double winningScore=EPS;
        int evaluated=1,candidates=0;
        for(int vm:new int[]{fastest,cheapest}) {
            if(vm<0||vm==oldVm||vm==fastest&&candidates>0)continue;
            // Ensure only two distinct alternatives consume forecasts.
            if(vm==cheapest && vm==fastest && candidates>0)continue;
            genes[chosenTask]=vm;
            ReadyQueueScheduleEvaluator.Result candidate;
            try {
                candidate=forecast(genes,tasks,vms,model);
            } finally {
                genes[chosenTask]=oldVm;
            }
            evaluated++;candidates++;
            if(!Double.isFinite(candidate.makespan)||!Double.isFinite(candidate.cost))
                throw new IllegalStateException("Nonfinite internal candidate prediction");
            double improvement;
            double adverse;
            if(latencyFocused) {
                improvement=(base.makespan-candidate.makespan)/Math.max(EPS,base.makespan);
                adverse=Math.max(0,(candidate.cost-base.cost)/Math.max(EPS,base.cost));
            } else {
                improvement=(base.cost-candidate.cost)/Math.max(EPS,base.cost);
                adverse=Math.max(0,(candidate.makespan-base.makespan)/Math.max(EPS,base.makespan));
            }
            double score=improvement-0.25*adverse;
            if(improvement>EPS && adverse<=MAX_OTHER_OBJECTIVE_RELATIVE_RISK+EPS &&
                (score>winningScore+EPS || (Math.abs(score-winningScore)<=EPS &&
                                                (winningVm<0||vm<winningVm)))) {
                winningVm=vm;winningScore=score;
            }
        }
        if(winningVm>=0)genes[chosenTask]=winningVm;
        return new Result(tasks.get(chosenTask).getCloudletId(),
                evaluated,candidates,winningVm>=0,winningVm>=0?winningScore:0);
    }
}
