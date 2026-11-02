package org.workflowsim.examples.planning;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.cloudbus.cloudsim.Log;
import org.workflowsim.planning.LIWSAPlanningAlgorithm;
import org.workflowsim.utils.Parameters;

/**
 * Paired, fixed-assignment comparison of baseline planning, read-only
 * stage-in-aware planning estimate, and actual WorkflowSim observations.
 * No optimizer update is performed by the new estimator.
 *
 * Example: StageInAwareFidelityAudit
 *   "Montage_25,CyberShake_30" "1,2,3" "Output&Results/stagein_audit.csv"
 */
public final class StageInAwareFidelityAudit {
    private StageInAwareFidelityAudit(){}
    public static void main(String[] args) throws Exception {
        if(args.length!=3)throw new IllegalArgumentException(
            "Usage: StageInAwareFidelityAudit WORKFLOWS SEEDS OUTPUT_CSV");
        Path target=Paths.get(args[2]);
        if(target.getParent()!=null)Files.createDirectories(target.getParent());
        Log.disable();
        try(BufferedWriter out=Files.newBufferedWriter(target,StandardCharsets.UTF_8)){
            out.write("workflow,seed,baseline_plan_makespan,stagein_plan_makespan,sim_makespan,"
                +"baseline_plan_cost,stagein_plan_cost,sim_cost,estimated_stagein_seconds,"
                +"estimated_external_stagein_seconds,estimated_intermediate_stagein_seconds,"
                +"baseline_makespan_abs_pct,stagein_makespan_abs_pct,"
                +"baseline_cost_abs_pct,stagein_cost_abs_pct\n");
            for(String wf:args[0].split(",")){
                String dax="config/dax/"+wf.trim()+".xml";
                LIWSABenchmarkExample.RunResult heft=LIWSABenchmarkExample.runPlanning(
                    dax,Parameters.PlanningAlgorithm.HEFT,Parameters.SchedulingAlgorithm.STATIC,
                    "audit_HEFT",0L,30,100,null);
                LIWSABenchmarkExample.RunResult minmin=LIWSABenchmarkExample.runPlanning(
                    dax,Parameters.PlanningAlgorithm.INVALID,Parameters.SchedulingAlgorithm.MINMIN,
                    "audit_MinMin",0L,30,100,null);
                if(heft==null||minmin==null||heft.assignment==null||minmin.assignment==null)
                    throw new IllegalStateException("Failed reference runs for "+wf);
                List<Map<Integer,Integer>> warm=new ArrayList<>();
                warm.add(heft.assignment);warm.add(minmin.assignment);
                for(String ss:args[1].split(",")){
                    long seed=Long.parseLong(ss.trim());
                    LIWSABenchmarkExample.RunResult actual=LIWSABenchmarkExample.runPlanning(
                        dax,Parameters.PlanningAlgorithm.LIWSA,Parameters.SchedulingAlgorithm.STATIC,
                        "audit_LIWSA",seed,30,100,warm);
                    LIWSAPlanningAlgorithm.LastRunMetrics m=LIWSAPlanningAlgorithm.lastRun;
                    if(actual==null||m==null)throw new IllegalStateException("Failed LIWSA "+wf+" seed="+seed);
                    double baseM=error(m.chosenMakespan,actual.makespan);
                    double awareM=error(m.stageInAwareMakespan,actual.makespan);
                    double baseC=error(m.chosenCost,actual.cost);
                    double awareC=error(m.stageInAwareCost,actual.cost);
                    out.write(String.format(Locale.ROOT,
                        "%s,%d,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.6f,%.6f,%.6f,%.6f%n",
                        wf,seed,m.chosenMakespan,m.stageInAwareMakespan,actual.makespan,
                        m.chosenCost,m.stageInAwareCost,actual.cost,
                        m.stageInAwareTotalSeconds,m.stageInAwareExternalSeconds,
                        m.stageInAwareIntermediateSeconds,
                        baseM,awareM,baseC,awareC));
                    out.flush();
                    System.out.printf(Locale.ROOT,
                        "AUDIT %s seed=%d baseline_m_error=%.3f%% stagein_m_error=%.3f%% baseline_c_error=%.3f%% stagein_c_error=%.3f%% stagein=%.3fs%n",
                        wf,seed,baseM,awareM,baseC,awareC,m.stageInAwareTotalSeconds);
                }
            }
        }
    }
    private static double error(double plan,double sim){
        if(!Double.isFinite(plan)||!Double.isFinite(sim)||plan<=0||sim<=0)
            throw new IllegalArgumentException("Invalid objectives");
        return Math.abs(plan-sim)/sim*100.0;
    }
}
