package org.workflowsim.examples.planning;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;
import org.cloudbus.cloudsim.Log;
import org.workflowsim.planning.DAGParetoFLAPlanningAlgorithm;
import org.workflowsim.planning.FLABaselinePlanningAlgorithm;
import org.workflowsim.planning.LIWSAPlanningAlgorithm;
import org.workflowsim.planning.MLEAOPlanningAlgorithm;
import org.workflowsim.planning.NSGAIIPlanningAlgorithm;
import org.workflowsim.utils.Parameters;

/**
 * Research-only experiment: replays the same planned-nondominated candidate
 * set selection rule for all four optimizers, then scores simulator outputs.
 * This is a pilot of archive consistency, not a publication-final comparison:
 * planning-dominated candidates are NOT replayed, and FLA-3W is scalarized.
 *
 * Example: FLAResearchExperiment Montage_25 1 12 12 Output&Results/fla_pilot
 * Budget: native optimizers have pop*(gens+1) evaluations; the three scalar
 * searches split the generation count and each has its own initialization.
 */
public final class FLAResearchExperiment {
    private FLAResearchExperiment() {}

    private static final class Candidate {
        final double[] planned;
        final Map<Integer,Integer> assignment;
        double[] simulated;
        Candidate(double[] point, Map<Integer,Integer> mapping) {
            planned = point.clone();
            assignment = Collections.unmodifiableMap(new TreeMap<>(mapping));
        }
    }
    private static final class Run {
        final String algorithm;
        final List<Candidate> candidates = new ArrayList<>();
        int evals;
        long searchMs;
        int sourceFrontSize;
        List<double[]> simulatorFront;
        double simHv;
        double planHv;
        Run(String name) { algorithm = name; }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 5) {
            throw new IllegalArgumentException("Usage: FLAResearchExperiment WORKFLOW SEED POP GENS OUT_PREFIX");
        }
        String wf = args[0];
        long seed = Long.parseLong(args[1]);
        int pop = Integer.parseInt(args[2]);
        int gens = Integer.parseInt(args[3]);
        if (pop < 8 || gens < 6) throw new IllegalArgumentException("pop>=8 gens>=6 needed");
        Path prefix = Paths.get(args[4]);
        if (prefix.getParent() != null) Files.createDirectories(prefix.getParent());
        String dax = "config/dax/" + wf + ".xml";
        if (!Files.isRegularFile(Paths.get(dax))) throw new IllegalArgumentException("Missing " + dax);
        Log.disable();
        List<Run> runs = new ArrayList<>();
        final int cap = pop * (gens + 1) + 3 * pop + 6;
        runs.add(runScalar(dax, seed, pop, gens));
        runs.add(runDag(dax, seed, pop, gens));
        runs.add(runNsga(dax, seed, pop, gens));
        runs.add(runMleao(dax, seed, pop, gens));

        for (Run run : runs) {
            if (run.evals <= 0 || run.evals > cap || run.candidates.isEmpty()) {
                throw new IllegalStateException(run.algorithm + " invalid budget/front: " + run.evals);
            }
            // Only unique planned-nondominated schedules are replayed, equally.
            List<Candidate> front = plannedNondominated(run.candidates);
            run.candidates.clear(); run.candidates.addAll(front);
            System.out.printf(Locale.ROOT,
                    "REPLAY %s %s seed=%d evaluations=%d archive=%d uniqueND=%d%n",
                    wf, run.algorithm, seed, run.evals, run.sourceFrontSize, front.size());
            for (Candidate c : front) {
                LIWSABenchmarkExample.RunResult result = LIWSABenchmarkExample.runPlanning(
                        dax, Parameters.PlanningAlgorithm.LIWSA,
                        Parameters.SchedulingAlgorithm.STATIC,
                        "replay_" + run.algorithm.replace("-","_"), seed,
                        1, 0, Collections.singletonList(c.assignment));
                if (result == null || !c.assignment.equals(new TreeMap<>(result.assignment))) {
                    throw new IllegalStateException("Invalid exact-assignment replay: " + run.algorithm);
                }
                c.simulated = new double[]{result.makespan, result.cost};
                valid(c.simulated);
            }
            List<double[]> actual = new ArrayList<>();
            for (Candidate c : front) actual.add(c.simulated);
            run.simulatorFront = ndPoints(actual);
        }
        List<List<double[]>> allSim = new ArrayList<>();
        List<List<double[]>> allPlan = new ArrayList<>();
        for (Run run : runs) {
            allSim.add(run.simulatorFront);
            List<double[]> x = new ArrayList<>();
            for (Candidate c : run.candidates) x.add(c.planned);
            allPlan.add(ndPoints(x));
        }
        double[] simRef = ParetoMetrics.sharedReferencePoint(allSim);
        double[] planRef = ParetoMetrics.sharedReferencePoint(allPlan);
        for (Run run : runs) {
            run.simHv = ParetoMetrics.hypervolume2D(run.simulatorFront,simRef[0],simRef[1]);
            List<double[]> x = new ArrayList<>();
            for (Candidate c:run.candidates) x.add(c.planned);
            run.planHv = ParetoMetrics.hypervolume2D(ndPoints(x),planRef[0],planRef[1]);
        }
        save(wf,seed,pop,gens,cap,prefix,runs,simRef,planRef);
    }

    private static Run runScalar(String dax, long seed, int pop, int gens) {
        Run run = new Run("FLA-3W");
        final double[] weights = {0.2,0.5,0.8};
        int[] distributed = {gens/3,gens/3,gens/3};
        for (int i = 0; i < gens % 3; i++) distributed[i]++;
        for (int i = 0; i < weights.length; i++) {
            FLABaselinePlanningAlgorithm.CONFIG_COLLECT_ARCHIVE = true;
            FLABaselinePlanningAlgorithm.CONFIG_ARCHIVE_CAPACITY = Math.max(pop, 32);
            FLABaselinePlanningAlgorithm.CONFIG_MAKESPAN_WEIGHT = weights[i];
            FLABaselinePlanningAlgorithm.CONFIG_SEED_ASSIGNMENTS = null;
            LIWSABenchmarkExample.RunResult result = LIWSABenchmarkExample.runPlanning(
                    dax, Parameters.PlanningAlgorithm.FLA_SCALAR,
                    Parameters.SchedulingAlgorithm.STATIC, "FLA-"+i,seed+10000*i,
                    pop,distributed[i],null);
            FLABaselinePlanningAlgorithm.LastRunMetrics m = FLABaselinePlanningAlgorithm.lastRun;
            if (result == null || m == null) throw new IllegalStateException("FLA scalar failed weight " + weights[i]);
            run.evals += Math.toIntExact(m.objectiveEvaluations);
            run.searchMs += m.searchWallClockMillis;
            append(run,m.paretoFrontPoints,m.paretoFrontAssignments);
        }
        return run;
    }
    private static Run runDag(String dax,long seed,int pop,int gens) {
        DAGParetoFLAPlanningAlgorithm.CONFIG_DAG_GUIDANCE = true;
        DAGParetoFLAPlanningAlgorithm.CONFIG_CROSS_GROUP_DO = true;
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_SSO = true;
        DAGParetoFLAPlanningAlgorithm.CONFIG_ADAPTIVE_MUTATION = true;
        DAGParetoFLAPlanningAlgorithm.CONFIG_ADAPTIVE_PREFERENCE = true;
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_CAPACITY = Math.max(pop, 32);
        DAGParetoFLAPlanningAlgorithm.CONFIG_SEED_ASSIGNMENTS = null;
        LIWSABenchmarkExample.RunResult result = LIWSABenchmarkExample.runPlanning(
                dax,Parameters.PlanningAlgorithm.DAG_PARETO_FLA,
                Parameters.SchedulingAlgorithm.STATIC,"DAG-Pareto-FLA",seed,pop,gens,null);
        DAGParetoFLAPlanningAlgorithm.LastRunMetrics m = DAGParetoFLAPlanningAlgorithm.lastRun;
        if(result==null||m==null) throw new IllegalStateException("DAG-FLA failed");
        Run r = new Run("DAG-Pareto-FLA");
        r.evals=Math.toIntExact(m.objectiveEvaluations);r.searchMs=m.searchWallClockMillis;
        append(r,m.paretoFrontPoints,m.paretoFrontAssignments);
        return r;
    }
    private static Run runNsga(String dax,long seed,int pop,int gens) {
        NSGAIIPlanningAlgorithm.CONFIG_OUTPUT_ARCHIVE=true;
        NSGAIIPlanningAlgorithm.CONFIG_SEED_ASSIGNMENTS=null;
        LIWSABenchmarkExample.RunResult result=LIWSABenchmarkExample.runPlanning(
                dax,Parameters.PlanningAlgorithm.NSGAII,Parameters.SchedulingAlgorithm.STATIC,
                "NSGA-II",seed,pop,gens,null);
        NSGAIIPlanningAlgorithm.LastRunMetrics m=NSGAIIPlanningAlgorithm.lastRun;
        if(result==null||m==null)throw new IllegalStateException("NSGA-II failed");
        Run r=new Run("NSGA-II");r.evals=Math.toIntExact(m.objectiveEvaluations);
        r.searchMs=m.searchWallClockMillis;append(r,m.paretoFrontPoints,m.paretoFrontAssignments);
        return r;
    }
    private static Run runMleao(String dax,long seed,int pop,int gens) {
        MLEAOPlanningAlgorithm.CONFIG_OUTPUT_ARCHIVE=true;
        MLEAOPlanningAlgorithm.CONFIG_SEED_ASSIGNMENTS=null;
        LIWSABenchmarkExample.RunResult result=LIWSABenchmarkExample.runPlanning(
                dax,Parameters.PlanningAlgorithm.MLEAO,Parameters.SchedulingAlgorithm.STATIC,
                "MLEAO",seed,pop,gens,null);
        MLEAOPlanningAlgorithm.LastRunMetrics m=MLEAOPlanningAlgorithm.lastRun;
        if(result==null||m==null)throw new IllegalStateException("MLEAO failed");
        Run r=new Run("MLEAO");r.evals=Math.toIntExact(m.objectiveEvaluations);
        r.searchMs=m.searchWallClockMillis;append(r,m.paretoFrontPoints,m.paretoFrontAssignments);
        return r;
    }

    private static void append(Run run,List<double[]> points,List<Map<Integer,Integer>> mappings) {
        if(points==null||mappings==null||points.isEmpty()||points.size()!=mappings.size())
            throw new IllegalStateException(run.algorithm + " missing archive assignments");
        run.sourceFrontSize+=points.size();
        for(int i=0;i<points.size();i++) {
            valid(points.get(i));
            if(mappings.get(i)==null||mappings.get(i).isEmpty())
                throw new IllegalStateException("Empty mapping");
            run.candidates.add(new Candidate(points.get(i),mappings.get(i)));
        }
    }
    private static void valid(double[] x) {
        if(x.length!=2 || !Double.isFinite(x[0])||!Double.isFinite(x[1])||x[0]<=0||x[1]<0)
            throw new IllegalStateException("Invalid objectives " + Arrays.toString(x));
    }
    private static List<Candidate> plannedNondominated(List<Candidate> raw) {
        Map<Map<Integer,Integer>,Candidate> unique=new LinkedHashMap<>();
        for(Candidate x:raw)unique.putIfAbsent(x.assignment,x);
        List<Candidate> values=new ArrayList<>(unique.values());
        List<Candidate> ans=new ArrayList<>();
        for(int i=0;i<values.size();i++){
            Candidate v=values.get(i);boolean defeated=false;
            for(int j=0;j<values.size();j++){
                if(i==j)continue;
                Candidate w=values.get(j);
                if(dominates(w.planned,v.planned) ||
                   (w.planned[0]==v.planned[0]&&w.planned[1]==v.planned[1]&&j<i)) {
                    defeated=true;break;
                }
            }
            if(!defeated)ans.add(v);
        }
        return ans;
    }
    private static boolean dominates(double[] a,double[] b) {
        return a[0]<=b[0]&&a[1]<=b[1]&&(a[0]<b[0]||a[1]<b[1]);
    }
    private static List<double[]> ndPoints(List<double[]> raw) {
        List<double[]> out=new ArrayList<>();
        for(int i=0;i<raw.size();i++){
            double[] x=raw.get(i);boolean defeated=false;
            for(int j=0;j<raw.size();j++){
                if(i==j)continue;
                double[] y=raw.get(j);
                if(dominates(y,x)||(y[0]==x[0]&&y[1]==x[1]&&j<i)){
                    defeated=true;break;
                }
            }
            if(!defeated)out.add(x);
        }
        return out;
    }
    private static void save(String wf,long seed,int pop,int gens,int cap,Path prefix,
            List<Run> runs,double[] simRef,double[] planRef) throws IOException {
        try(BufferedWriter w=Files.newBufferedWriter(Paths.get(prefix+"_summary.csv"),StandardCharsets.UTF_8)){
            w.write("workflow,algorithm,seed,population,generations,budget_cap,evaluations,source_archive,distinct_planned_nondominated,replayed,sim_nondominated,sim_hv,planned_hv,sim_ref_m,sim_ref_c,plan_ref_m,plan_ref_c,search_ms\n");
            for(Run r:runs) {
                w.write(String.format(Locale.ROOT,"%s,%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%.10f,%.10f,%.10f,%.10f,%.10f,%.10f,%d%n",
                    wf,r.algorithm,seed,pop,gens,cap,r.evals,r.sourceFrontSize,r.candidates.size(),
                    r.candidates.size(),r.simulatorFront.size(),r.simHv,r.planHv,
                    simRef[0],simRef[1],planRef[0],planRef[1],r.searchMs));
                System.out.printf(Locale.ROOT,"RESULT %s %s simHV=%.8f planningHV=%.8f simND=%d evals=%d%n",
                    wf,r.algorithm,r.simHv,r.planHv,r.simulatorFront.size(),r.evals);
            }
        }
        try(BufferedWriter w=Files.newBufferedWriter(Paths.get(prefix+"_replays.csv"),StandardCharsets.UTF_8)){
            w.write("workflow,algorithm,seed,candidate_index,planned_makespan,planned_cost,sim_makespan,sim_cost,mapping\n");
            for(Run r:runs){
                int i=0;
                for(Candidate c:r.candidates){
                    StringBuilder sb=new StringBuilder();
                    for(Map.Entry<Integer,Integer> p:c.assignment.entrySet()){
                        if(sb.length()>0)sb.append('|');
                        sb.append(p.getKey()).append(':').append(p.getValue());
                    }
                    w.write(String.format(Locale.ROOT,"%s,%s,%d,%d,%.10f,%.10f,%.10f,%.10f,%s%n",
                        wf,r.algorithm,seed,++i,c.planned[0],c.planned[1],
                        c.simulated[0],c.simulated[1],sb.toString()));
                }
            }
        }
        try(BufferedWriter w=Files.newBufferedWriter(Paths.get(prefix+"_limitations.txt"),StandardCharsets.UTF_8)) {
            w.write("All algorithms use the same simulated Pareto/HV reference within this workflow/seed.\n");
            w.write("Replayed sets are selected from each algorithm's PLANNED nondominated records, not every evaluation.\n");
            w.write("FLA-3W combines three independent scalar runs; native optimizers each use one population.\n");
            w.write("Total evaluations are reported, not assumed equal. Warm starts disabled in the pilot.\n");
            w.write("Archived candidates are not guaranteed to be full search histories for NSGA-II/MLEAO.\n");
            w.write("This experiment does not establish algorithm fidelity or statistical superiority.\n");
        }
    }
}
