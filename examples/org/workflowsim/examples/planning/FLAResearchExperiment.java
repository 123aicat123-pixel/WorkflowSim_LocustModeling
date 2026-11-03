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
import java.util.Comparator;
import java.util.HashSet;
import java.util.Random;
import java.util.Set;
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
import org.workflowsim.planning.UnifiedCandidateRecorder;
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
    /** Read-only optional diagnostic, disabled by default. */
    private static final int SCREENING_AUDIT_N = Integer.getInteger("dagfla.screeningAuditPerAlgorithm", 0);
    /** Include equal planned objectives from distinct assignments in exhaustive audits. */
    private static final boolean SCREENING_INCLUDE_TIES =
            Boolean.getBoolean("dagfla.screeningAuditIncludeTies");

    private static final class Candidate {
        final double[] planned;
        final Map<Integer,Integer> assignment;
        double[] simulated;
        double[] independentPlanned;
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
        String actualGenerations;
        int sourceFrontSize;
        int capturedEvaluations;
        int distinctObservedAssignments;
        List<double[]> simulatorFront;
        final List<Candidate> allVisited = new ArrayList<>();
        final List<Candidate> audited = new ArrayList<>();
        final List<String> auditStrata = new ArrayList<>();
        int dominatedPool;
        int tiedPool;
        int auditUniqueVisited;
        int newSimulatorNondominated;
        double auditHvGain;
        double simHv;
        double planHv;
        Run(String name) { algorithm = name; }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 5 && args.length != 6) {
            throw new IllegalArgumentException("Usage: FLAResearchExperiment WORKFLOW SEED POP GENS OUT_PREFIX [DAG_ABLATION]");
        }
        String wf = args[0];
        long seed = Long.parseLong(args[1]);
        int pop = Integer.parseInt(args[2]);
        int gens = Integer.parseInt(args[3]);
        if (pop < 8 || gens < 6) throw new IllegalArgumentException("pop>=8 gens>=6 needed");
        if (SCREENING_AUDIT_N < 0 || SCREENING_AUDIT_N > 100) throw new IllegalArgumentException("invalid diagnostic sample count");
        Path prefix = Paths.get(args[4]);
        if (prefix.getParent() != null) Files.createDirectories(prefix.getParent());
        String dax = "config/dax/" + wf + ".xml";
        if (!Files.isRegularFile(Paths.get(dax))) throw new IllegalArgumentException("Missing " + dax);
        Log.disable();
        List<Run> runs = new ArrayList<>();
        final int cap = pop * (gens + 1) + 3 * pop + 6;
        if (args.length == 6) {
            if ("nsga-only".equals(args[5])) {
                runs.add(runNsga(dax, seed, pop, gens));
            } else if ("fla-only".equals(args[5])) {
                runs.add(runScalar(dax, seed, pop, gens));
            } else {
                runs.add(runDag(dax, seed, pop, gens, args[5]));
            }
        } else {
            runs.add(runScalar(dax, seed, pop, gens));
            runs.add(runDag(dax, seed, pop, gens,
                    System.getProperty("dagfla.comparisonVariant", "all")));
            runs.add(runNsga(dax, seed, pop, gens));
            runs.add(runMleao(dax, seed, pop, gens));
        }

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
                LIWSAPlanningAlgorithm.LastRunMetrics rmetrics = LIWSAPlanningAlgorithm.lastRun;
                if(rmetrics == null) throw new IllegalStateException("Replay planner did not publish objectives");
                c.independentPlanned = new double[]{rmetrics.chosenMakespan, rmetrics.chosenCost};
                valid(c.simulated);
                valid(c.independentPlanned);
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
        // Scientific sensitivity audit, not part of the optimization budget:
        // after freezing the normal simulator HV reference, replay a random/
        // near-front sample of PLANNING-DOMINATED evaluated assignments.
        if (SCREENING_AUDIT_N > 0) {
            for (Run run : runs) runScreeningAudit(dax, wf, seed, run, simRef);
        }
        save(wf,seed,pop,gens,cap,prefix,runs,simRef,planRef);
        if (SCREENING_AUDIT_N > 0) saveScreeningAudit(wf,seed,prefix,runs);
    }

    private static Run runScalar(String dax, long seed, int pop, int gens) {
        Run run = new Run("FLA-3W");
        final Set<Map<Integer,Integer>> globalUniqueAssignments = new HashSet<>();
        final double[] weights = {0.2,0.5,0.8};
        final int referenceBudget = pop * (gens + 1);
        // Includes three initial populations and six scale-normalization probes.
        final int scalarGenerations = Math.max(3, (referenceBudget - 6) / pop - 3);
        int[] distributed = {scalarGenerations/3,scalarGenerations/3,scalarGenerations/3};
        for (int i = 0; i < scalarGenerations % 3; i++) distributed[i]++;
        run.actualGenerations=distributed[0]+"+"+distributed[1]+"+"+distributed[2];
        for (int i = 0; i < weights.length; i++) {
            UnifiedCandidateRecorder.begin((long)pop*(distributed[i]+1)+2);
            UnifiedCandidateRecorder.phase("FLA-weight-"+weights[i]);
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
            UnifiedCandidateRecorder.Capture capture=UnifiedCandidateRecorder.end();
            if(capture.evaluationCount()!=m.objectiveEvaluations)
                throw new IllegalStateException("FLA source-counter and recorder mismatch");
            run.evals += capture.evaluationCount();
            run.capturedEvaluations += capture.evaluationCount();
            for (UnifiedCandidateRecorder.Event e:capture.uniqueEvents())
                globalUniqueAssignments.add(e.assignment);
            run.distinctObservedAssignments = globalUniqueAssignments.size();
            run.searchMs += m.searchWallClockMillis;
            append(run,capture.frontPoints(),capture.frontAssignments());
            appendAuditHistory(run,capture);
        }
        return run;
    }
    private static Run runDag(String dax,long seed,int pop,int gens,String variant) {
        final List<String> supported=Arrays.asList("all","no-dag","no-cross",
                "no-archive-sso","no-adaptive-mutation","no-adaptive-preference","minimal",
                "v2-global","v2-immigrants","v2",
                "v3-resource","v3-archive","v3-both","v4-crowding","v4-crowding-resource",
                "v5-dagblock","v5-donor","v5-both","v6-pop","v6-global","v6-strong",
                "v7-costseed","v7-extreme","v7-both");
        if (!supported.contains(variant)) throw new IllegalArgumentException("Unknown ablation: " + variant);
        final boolean minimal="minimal".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_DAG_GUIDANCE = !minimal && !"no-dag".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_CROSS_GROUP_DO = !minimal && !"no-cross".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_SSO = !minimal && !"no-archive-sso".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ADAPTIVE_MUTATION = !minimal && !"no-adaptive-mutation".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ADAPTIVE_PREFERENCE = !minimal && !"no-adaptive-preference".equals(variant);
        boolean isV2=variant.startsWith("v2") || variant.startsWith("v3") || variant.startsWith("v4") || variant.startsWith("v5") || variant.startsWith("v6") || variant.startsWith("v7");
        if(isV2) DAGParetoFLAPlanningAlgorithm.CONFIG_CROSS_GROUP_DO=false;
        DAGParetoFLAPlanningAlgorithm.CONFIG_RESOURCE_AWARE_MUTATION =
                "v3-resource".equals(variant) || "v3-both".equals(variant)
                || "v4-crowding-resource".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_RECOMBINATION =
                "v3-archive".equals(variant) || "v3-both".equals(variant) || variant.startsWith("v4")
                || variant.startsWith("v5") || variant.startsWith("v6") || variant.startsWith("v7");
        DAGParetoFLAPlanningAlgorithm.CONFIG_PARETO_CROWDING_SELECTION = variant.startsWith("v4");
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_DAG_BLOCK =
                "v5-dagblock".equals(variant) || "v5-both".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_PREFERENCE_DONOR =
                "v5-donor".equals(variant) || "v5-both".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_NOVELTY_REPAIR = variant.startsWith("v6") || variant.startsWith("v7");
        DAGParetoFLAPlanningAlgorithm.CONFIG_NOVELTY_GLOBAL_HISTORY =
                "v6-global".equals(variant) || "v6-strong".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_NOVELTY_STRONG_REPAIR =
                "v6-strong".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_COST_SEEDING =
                "v7-costseed".equals(variant) || "v7-both".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_COST_EXTREME_GUIDANCE =
                "v7-extreme".equals(variant) || "v7-both".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_GLOBAL_SURVIVOR_SELECTION =
                "v2-global".equals(variant) || "v2".equals(variant) || variant.startsWith("v3")
                || variant.startsWith("v4") || variant.startsWith("v5") || variant.startsWith("v6") || variant.startsWith("v7");
        DAGParetoFLAPlanningAlgorithm.CONFIG_RANDOM_IMMIGRANTS =
                "v2-immigrants".equals(variant) || "v2".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_CAPACITY = Math.max(pop, 32);
        DAGParetoFLAPlanningAlgorithm.CONFIG_SEED_ASSIGNMENTS = null;
        UnifiedCandidateRecorder.begin((long)pop*(gens+2));
        UnifiedCandidateRecorder.phase("DAG-FLA-"+variant);
        LIWSABenchmarkExample.RunResult result = LIWSABenchmarkExample.runPlanning(
                dax,Parameters.PlanningAlgorithm.DAG_PARETO_FLA,
                Parameters.SchedulingAlgorithm.STATIC,"DAG-Pareto-FLA",seed,pop,gens,null);
        DAGParetoFLAPlanningAlgorithm.LastRunMetrics m = DAGParetoFLAPlanningAlgorithm.lastRun;
        if(result==null||m==null) throw new IllegalStateException("DAG-FLA failed");
        UnifiedCandidateRecorder.Capture capture=UnifiedCandidateRecorder.end();
        if(capture.evaluationCount()!=m.objectiveEvaluations)
            throw new IllegalStateException("DAG-FLA source-counter and recorder mismatch");
        Run r = new Run("DAG-Pareto-FLA" + ("all".equals(variant) ? "" : "["+variant+"]"));
        r.actualGenerations=String.valueOf(gens);
        r.evals=capture.evaluationCount();r.searchMs=m.searchWallClockMillis;
        r.capturedEvaluations=capture.evaluationCount();
        r.distinctObservedAssignments=capture.distinctAssignments();
        append(r,capture.frontPoints(),capture.frontAssignments());
        appendAuditHistory(r,capture);
        return r;
    }
    private static Run runNsga(String dax,long seed,int pop,int gens) {
        NSGAIIPlanningAlgorithm.CONFIG_OUTPUT_ARCHIVE=true;
        NSGAIIPlanningAlgorithm.CONFIG_SEED_ASSIGNMENTS=null;
        UnifiedCandidateRecorder.begin((long)pop*(gens+2));
        UnifiedCandidateRecorder.phase("NSGA-II");
        LIWSABenchmarkExample.RunResult result=LIWSABenchmarkExample.runPlanning(
                dax,Parameters.PlanningAlgorithm.NSGAII,Parameters.SchedulingAlgorithm.STATIC,
                "NSGA-II",seed,pop,gens,null);
        NSGAIIPlanningAlgorithm.LastRunMetrics m=NSGAIIPlanningAlgorithm.lastRun;
        if(result==null||m==null)throw new IllegalStateException("NSGA-II failed");
        UnifiedCandidateRecorder.Capture capture=UnifiedCandidateRecorder.end();
        if(capture.evaluationCount()!=m.objectiveEvaluations)
            throw new IllegalStateException("NSGA-II source-counter and recorder mismatch");
        Run r=new Run("NSGA-II");r.actualGenerations=String.valueOf(gens);r.evals=capture.evaluationCount();
        r.capturedEvaluations=capture.evaluationCount();
        r.distinctObservedAssignments=capture.distinctAssignments();
        r.searchMs=m.searchWallClockMillis;append(r,capture.frontPoints(),capture.frontAssignments());
        appendAuditHistory(r,capture);
        return r;
    }
    private static Run runMleao(String dax,long seed,int pop,int gens) {
        // MLEAO skips one target evaluation per generation. Adjust generation
        // count to match, rather than falsely equate nominal generations with
        // objective evaluations. For pop=30/gen=100, use 103 -> 3017 evals.
        int matchedGenerations=gens+Math.max(0,(int)Math.round((double)gens/(pop-1)));
        MLEAOPlanningAlgorithm.CONFIG_OUTPUT_ARCHIVE=true;
        MLEAOPlanningAlgorithm.CONFIG_SEED_ASSIGNMENTS=null;
        UnifiedCandidateRecorder.begin((long)pop*(gens+2));
        UnifiedCandidateRecorder.phase("MLEAO");
        LIWSABenchmarkExample.RunResult result=LIWSABenchmarkExample.runPlanning(
                dax,Parameters.PlanningAlgorithm.MLEAO,Parameters.SchedulingAlgorithm.STATIC,
                "MLEAO",seed,pop,matchedGenerations,null);
        MLEAOPlanningAlgorithm.LastRunMetrics m=MLEAOPlanningAlgorithm.lastRun;
        if(result==null||m==null)throw new IllegalStateException("MLEAO failed");
        UnifiedCandidateRecorder.Capture capture=UnifiedCandidateRecorder.end();
        if(capture.evaluationCount()!=m.objectiveEvaluations)
            throw new IllegalStateException("MLEAO source-counter and recorder mismatch");
        Run r=new Run("MLEAO");r.actualGenerations=String.valueOf(matchedGenerations);r.evals=capture.evaluationCount();
        r.capturedEvaluations=capture.evaluationCount();
        r.distinctObservedAssignments=capture.distinctAssignments();
        r.searchMs=m.searchWallClockMillis;append(r,capture.frontPoints(),capture.frontAssignments());
        appendAuditHistory(r,capture);
        return r;
    }


    /** Keep every DISTINCT genotype to quantify planned-front screening bias. */
    private static void appendAuditHistory(Run run,UnifiedCandidateRecorder.Capture cap) {
        if (SCREENING_AUDIT_N == 0) return;
        for (UnifiedCandidateRecorder.Event e : cap.uniqueEvents()) {
            run.allVisited.add(new Candidate(new double[]{e.makespan,e.cost},e.assignment));
        }
    }

    private static double normalizedDistance(Candidate x,List<Candidate> front) {
        double best=Double.POSITIVE_INFINITY;
        for(Candidate f:front) {
            double dm=(x.planned[0]-f.planned[0])/Math.max(1.0,f.planned[0]);
            double dc=(x.planned[1]-f.planned[1])/Math.max(1.0,f.planned[1]);
            best=Math.min(best,Math.hypot(dm,dc));
        }
        return best;
    }

    /**
     * Equal diagnostic replay policy for EVERY algorithm:
     * half near the planned front, half uniformly shuffled among the
     * remaining strictly planning-dominated UNIQUE assignments.
     *
     * Additional replays NEVER enter the optimization archive and therefore
     * do not alter reported benchmark fitness calls or primary HV.
     */
    private static void runScreeningAudit(String dax,String wf,long seed,Run run,double[] frozenRef) {
        Map<Map<Integer,Integer>,Candidate> unique=new LinkedHashMap<>();
        for(Candidate c:run.allVisited) unique.putIfAbsent(c.assignment,c);
        run.auditUniqueVisited=unique.size();
        List<Candidate> dominated=new ArrayList<>();
        Set<Map<Integer,Integer>> frontAssignments=new HashSet<>();
        for(Candidate c:run.candidates)frontAssignments.add(c.assignment);
        for(Candidate c:unique.values()) {
            if(frontAssignments.contains(c.assignment))continue;
            boolean strict=false;
            for(Candidate f:run.candidates) {
                if(dominates(f.planned,c.planned)) { strict=true; break; }
            }
            if(strict) {
                dominated.add(c);
                run.dominatedPool++;
            } else if (SCREENING_INCLUDE_TIES) {
                boolean tied=false;
                for(Candidate f:run.candidates) {
                    if(f.planned[0]==c.planned[0] && f.planned[1]==c.planned[1]) {
                        tied=true;break;
                    }
                }
                if(tied) {
                    dominated.add(c);
                    run.tiedPool++;
                }
            }
        }
        dominated.sort(Comparator.comparingDouble(c->normalizedDistance(c,run.candidates)));
        int take=Math.min(SCREENING_AUDIT_N,dominated.size());
        int nearest=take/2;
        for(int i=0;i<nearest;i++){
            run.audited.add(dominated.get(i));
            run.auditStrata.add("near-planned-front");
        }
        List<Candidate> remaining=new ArrayList<>(dominated.subList(nearest,dominated.size()));
        Collections.shuffle(remaining,new Random(seed ^ ((long)run.algorithm.hashCode()*0x9E3779B97F4A7C15L)));
        for(int i=0;i<take-nearest;i++){
            run.audited.add(remaining.get(i));
            run.auditStrata.add("uniform-remainder");
        }
        List<double[]> all=new ArrayList<>(run.simulatorFront);
        for(Candidate c:run.audited) {
            LIWSABenchmarkExample.RunResult res=LIWSABenchmarkExample.runPlanning(
                    dax,Parameters.PlanningAlgorithm.LIWSA,
                    Parameters.SchedulingAlgorithm.STATIC,
                    "screening_audit_"+run.algorithm.replace("-","_"),seed,
                    1,0,Collections.singletonList(c.assignment));
            if(res==null || !c.assignment.equals(new TreeMap<>(res.assignment)))
                throw new IllegalStateException("Invalid dominated-sample assignment replay");
            c.simulated=new double[]{res.makespan,res.cost};
            valid(c.simulated);
            boolean improved=true;
            for(double[] q:run.simulatorFront) {
                if(dominates(q,c.simulated) ||
                    (q[0]==c.simulated[0]&&q[1]==c.simulated[1])) {
                    improved=false;break;
                }
            }
            if(improved)run.newSimulatorNondominated++;
            all.add(c.simulated);
        }
        List<double[]> newFront=ndPoints(all);
        double extraHv=ParetoMetrics.hypervolume2D(newFront,frozenRef[0],frozenRef[1]);
        run.auditHvGain=Math.max(0.0,extraHv-run.simHv);
        if(extraHv+1e-7*Math.max(1,Math.abs(run.simHv))<run.simHv)
            throw new IllegalStateException("Hypervolume lost after adding candidate points");
        System.out.printf(Locale.ROOT,
                "SCREENING_AUDIT %s %s seed=%d strictDominated=%d plannedTies=%d sampled=%d nondominatedVsBase=%d hvBase=%.9f hvExtra=%.9f delta=%.9f%n",
                wf,run.algorithm,seed,run.dominatedPool,run.tiedPool,run.audited.size(),
                run.newSimulatorNondominated,run.simHv,extraHv,run.auditHvGain);
    }

    private static void saveScreeningAudit(String wf,long seed,Path prefix,List<Run> runs)
            throws IOException {
        try(BufferedWriter w=Files.newBufferedWriter(
                Paths.get(prefix+"_screening_summary.csv"),StandardCharsets.UTF_8)) {
            w.write("workflow,algorithm,seed,unique_visited,strict_planned_dominated,planned_tie_pool,sampled,non_dominated_vs_base,baseline_sim_hv,extra_sim_hv,delta_hv,delta_hv_pct\n");
            for(Run r:runs) {
                double pct=100.0*r.auditHvGain/Math.max(1e-12,r.simHv);
                w.write(String.format(Locale.ROOT,
                     "%s,%s,%d,%d,%d,%d,%d,%d,%.10f,%.10f,%.10f,%.8f%n",
                    wf,r.algorithm,seed,r.auditUniqueVisited,r.dominatedPool,r.tiedPool,
                    r.audited.size(),r.newSimulatorNondominated,r.simHv,
                    r.simHv+r.auditHvGain,r.auditHvGain,pct));
            }
        }
        try(BufferedWriter w=Files.newBufferedWriter(
                Paths.get(prefix+"_screening_samples.csv"),StandardCharsets.UTF_8)) {
            w.write("workflow,algorithm,seed,stratum,planned_makespan,planned_cost,sim_makespan,sim_cost,mapping\n");
            for(Run r:runs) {
                for(int i=0;i<r.audited.size();i++) {
                    Candidate c=r.audited.get(i);
                    StringBuilder mapping=new StringBuilder();
                    for(Map.Entry<Integer,Integer> e:c.assignment.entrySet()){
                        if(mapping.length()>0)mapping.append('|');
                        mapping.append(e.getKey()).append(':').append(e.getValue());
                    }
                    w.write(String.format(Locale.ROOT,
                        "%s,%s,%d,%s,%.9f,%.9f,%.9f,%.9f,%s%n",
                        wf,r.algorithm,seed,r.auditStrata.get(i),
                        c.planned[0],c.planned[1],c.simulated[0],c.simulated[1],
                        mapping.toString()));
                }
            }
        }
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
            w.write("workflow,algorithm,seed,population,generations,budget_cap,evaluations,source_archive,distinct_planned_nondominated,replayed,sim_nondominated,captured_evaluations,distinct_observed,sim_hv,planned_hv,sim_ref_m,sim_ref_c,plan_ref_m,plan_ref_c,search_ms,actual_generations\n");
            for(Run r:runs) {
                w.write(String.format(Locale.ROOT,"%s,%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%.10f,%.10f,%.10f,%.10f,%.10f,%.10f,%d,%s%n",
                    wf,r.algorithm,seed,pop,gens,cap,r.evals,r.sourceFrontSize,r.candidates.size(),
                    r.candidates.size(),r.simulatorFront.size(),r.capturedEvaluations,
                    r.distinctObservedAssignments,r.simHv,r.planHv,
                    simRef[0],simRef[1],planRef[0],planRef[1],r.searchMs,r.actualGenerations));
                System.out.printf(Locale.ROOT,"RESULT %s %s simHV=%.8f planningHV=%.8f simND=%d evals=%d%n",
                    wf,r.algorithm,r.simHv,r.planHv,r.simulatorFront.size(),r.evals);
            }
        }
        try(BufferedWriter w=Files.newBufferedWriter(Paths.get(prefix+"_replays.csv"),StandardCharsets.UTF_8)){
            w.write("workflow,algorithm,seed,candidate_index,planned_makespan,planned_cost,independent_planned_makespan,independent_planned_cost,sim_makespan,sim_cost,mapping\n");
            for(Run r:runs){
                int i=0;
                for(Candidate c:r.candidates){
                    StringBuilder sb=new StringBuilder();
                    for(Map.Entry<Integer,Integer> p:c.assignment.entrySet()){
                        if(sb.length()>0)sb.append('|');
                        sb.append(p.getKey()).append(':').append(p.getValue());
                    }
                    w.write(String.format(Locale.ROOT,"%s,%s,%d,%d,%.10f,%.10f,%.10f,%.10f,%.10f,%.10f,%s%n",
                        wf,r.algorithm,seed,++i,c.planned[0],c.planned[1],
                        c.independentPlanned[0],c.independentPlanned[1],
                        c.simulated[0],c.simulated[1],sb.toString()));
                }
            }
        }
        try(BufferedWriter w=Files.newBufferedWriter(Paths.get(prefix+"_limitations.txt"),StandardCharsets.UTF_8)) {
            w.write("All algorithms use the same simulated Pareto/HV reference within this workflow/seed.\n");
            w.write("Replayed sets are selected from each algorithm's PLANNED nondominated records, not every evaluation.\n");
            w.write("FLA-3W combines three independent scalar runs; native optimizers each use one population.\n");
            w.write("Total evaluations are reported and aligned as closely as possible; warm starts disabled.\n");
            w.write("FLA-3W has three runs and MLEAO receives extra generations to align actual evaluation counts.\n");
            w.write("UnifiedCandidateRecorder observes EVERY successful evaluation, including seeds and FLA normalization probes.\n");
            w.write("Planning-nondominated assignments over ALL visited schedules are replayed.\n");
            w.write("This experiment does not establish algorithm fidelity or statistical superiority.\n");
            w.write("Independent planned objectives are re-evaluated with the unified LIWSA decoder for every replay.\n");
        }
    }
}
