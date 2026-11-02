package org.workflowsim.examples.planning;

import java.util.Locale;
import org.workflowsim.planning.DAGParetoFLAPlanningAlgorithm;
import org.workflowsim.utils.Parameters;

/**
 * Entry point for the selected v6-pop DAG-Pareto-FLA algorithm.
 *
 * Separate from the exploratory runner, and NEVER silently alters the old
 * DAG_PARETO_FLA default. The configuration below is explicit to preserve
 * historical ablations and make the final candidate straightforward to run.
 *
 * From a freshly compiled checkout:
 *   java -cp 'build/classes:lib/*' \
 *     org.workflowsim.examples.planning.DAGParetoFLAV6Example Montage_25 1 30 100
 */
public final class DAGParetoFLAV6Example {
    private DAGParetoFLAV6Example() {}

    public static void main(String[] args) {
        if(args.length!=4)throw new IllegalArgumentException(
            "Usage: DAGParetoFLAV6Example WORKFLOW SEED POPULATION GENERATIONS");
        String workflow=args[0];
        if(!workflow.matches("[A-Za-z0-9_]+"))throw new IllegalArgumentException("Invalid workflow name");
        long seed=Long.parseLong(args[1]);
        int population=Integer.parseInt(args[2]);
        int generations=Integer.parseInt(args[3]);
        if(population<8||generations<1)throw new IllegalArgumentException("Population >= 8; generations >=1");

        // Enforces the simulator-informed objective model supported by the
        // paired fidelity experiments. No other global class is modified.
        System.setProperty("workflowsim.planningStageInAware","true");
        DAGParetoFLAPlanningAlgorithm.CONFIG_POPULATION_SIZE=population;
        DAGParetoFLAPlanningAlgorithm.CONFIG_GENERATION_COUNT=generations;
        DAGParetoFLAPlanningAlgorithm.CONFIG_RANDOM_SEED=seed;
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_CAPACITY=Math.max(population,32);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ENFORCE_PES=false;
        DAGParetoFLAPlanningAlgorithm.CONFIG_SEED_ASSIGNMENTS=null;
        DAGParetoFLAPlanningAlgorithm.CONFIG_DAG_GUIDANCE=true;
        DAGParetoFLAPlanningAlgorithm.CONFIG_CROSS_GROUP_DO=false;
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_SSO=true;
        DAGParetoFLAPlanningAlgorithm.CONFIG_ADAPTIVE_MUTATION=true;
        DAGParetoFLAPlanningAlgorithm.CONFIG_ADAPTIVE_PREFERENCE=true;
        DAGParetoFLAPlanningAlgorithm.CONFIG_GLOBAL_SURVIVOR_SELECTION=true;
        DAGParetoFLAPlanningAlgorithm.CONFIG_RANDOM_IMMIGRANTS=false;
        DAGParetoFLAPlanningAlgorithm.CONFIG_RESOURCE_AWARE_MUTATION=false;
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_RECOMBINATION=true;
        DAGParetoFLAPlanningAlgorithm.CONFIG_PARETO_CROWDING_SELECTION=false;
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_DAG_BLOCK=false;
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_PREFERENCE_DONOR=false;
        DAGParetoFLAPlanningAlgorithm.CONFIG_NOVELTY_REPAIR=true;
        DAGParetoFLAPlanningAlgorithm.CONFIG_NOVELTY_GLOBAL_HISTORY=false;
        DAGParetoFLAPlanningAlgorithm.CONFIG_NOVELTY_STRONG_REPAIR=false;

        LIWSABenchmarkExample.RunResult simulated=LIWSABenchmarkExample.runPlanning(
                "config/dax/"+workflow+".xml",
                Parameters.PlanningAlgorithm.DAG_PARETO_FLA,
                Parameters.SchedulingAlgorithm.STATIC,
                "DAG-Pareto-FLA-v6-pop",seed,population,generations,null);
        DAGParetoFLAPlanningAlgorithm.LastRunMetrics metrics=
                DAGParetoFLAPlanningAlgorithm.lastRun;
        if(simulated==null||metrics==null||simulated.assignment==null||
                simulated.assignment.isEmpty())
            throw new IllegalStateException("No simulated v6 result was produced");
        if(metrics.objectiveEvaluations!=(long)population*(generations+1))
            throw new IllegalStateException("Unexpected evaluation count: "+metrics.objectiveEvaluations);
        if(!(simulated.makespan>0&&simulated.cost>0))
            throw new IllegalStateException("Invalid simulation objectives");
        System.out.printf(Locale.ROOT,
                "V6_SUCCESS workflow=%s seed=%d population=%d generations=%d evaluations=%d "+
                "planning_makespan=%.9f planning_cost=%.9f simulator_makespan=%.9f simulator_cost=%.9f "+
                "planned_archive=%d assigned_tasks=%d%n",
                workflow,seed,population,generations,metrics.objectiveEvaluations,
                metrics.chosenMakespan,metrics.chosenCost,
                simulated.makespan,simulated.cost,metrics.paretoFrontSize,
                simulated.assignment.size());
    }
}
