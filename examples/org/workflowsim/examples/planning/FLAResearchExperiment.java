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
    /** Prospective, actual WorkflowSim replay budget; zero preserves historical replay behavior. */
    private static final int BUDGET_REPLAY_K = Integer.getInteger("dagfla.budgetReplayK", 0);
    /** Same real-K simulator-call budget for all solvers; policy chooses which planned candidates. */
    private static final String BUDGET_REPLAY_POLICY =
            System.getProperty("dagfla.budgetReplayPolicy", "pareto-cover");
    /** Independent RANDOM replay draw, fixed at zero for backward compatibility. */
    private static final int BUDGET_REPLAY_REPLICATE =
            Integer.getInteger("dagfla.budgetReplayReplicate", 0);
    /** Include equal planned objectives from distinct assignments in exhaustive audits. */
    private static final boolean SCREENING_INCLUDE_TIES =
            Boolean.getBoolean("dagfla.screeningAuditIncludeTies");
    /** Explicit diagnostic mode: replay every unique visited assignment, even if absent from final archive. */
    private static final boolean SCREENING_ALL_VISITED =
            Boolean.getBoolean("dagfla.screeningAuditAllVisited");

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
        int plannedNdCount;
        int capturedEvaluations;
        int distinctObservedAssignments;
        List<double[]> simulatorFront;
        final List<Candidate> allVisited = new ArrayList<>();
        final List<Map<Integer,Integer>> firstTwoEvaluated = new ArrayList<>();
        final List<Candidate> audited = new ArrayList<>();
        final List<String> auditStrata = new ArrayList<>();
        int dominatedPool;
        int tiedPool;
        int otherPlannedPool;
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
        if (SCREENING_AUDIT_N < 0 || SCREENING_AUDIT_N > 256) throw new IllegalArgumentException("invalid diagnostic sample count");
        if (BUDGET_REPLAY_K > 0 && !Arrays.asList("pareto-cover","random").contains(BUDGET_REPLAY_POLICY))
            throw new IllegalArgumentException("invalid prospective replay policy: "+BUDGET_REPLAY_POLICY);
        if (BUDGET_REPLAY_K < 0 || BUDGET_REPLAY_K > 10000)
            throw new IllegalArgumentException("invalid actual replay budget");
        if (BUDGET_REPLAY_REPLICATE < 0 || BUDGET_REPLAY_REPLICATE > 1024)
            throw new IllegalArgumentException("random replay replicate out of range");
        if (BUDGET_REPLAY_REPLICATE != 0 &&
                (BUDGET_REPLAY_K == 0 || !"random".equals(BUDGET_REPLAY_POLICY)))
            throw new IllegalArgumentException("random replicate only applies to prospective random policy");
        if (BUDGET_REPLAY_K > 0 && SCREENING_AUDIT_N > 0)
            throw new IllegalArgumentException("Prospective K-limited replay cannot be combined with the extra-replay audit");
        if (SCREENING_ALL_VISITED && (!SCREENING_INCLUDE_TIES || SCREENING_AUDIT_N == 0))
            throw new IllegalArgumentException("all-visited replay requires positive sample cap and including ties");
        Path prefix = Paths.get(args[4]);
        if (prefix.getParent() != null) Files.createDirectories(prefix.getParent());
        String dax = "config/dax/" + wf + ".xml";
        if (!Files.isRegularFile(Paths.get(dax))) throw new IllegalArgumentException("Missing " + dax);
        Log.disable();
        List<Run> runs = new ArrayList<>();
        final int cap = pop * (gens + 1) + 3 * pop + 6;
        if (args.length == 6) {
            if ("fair-pair".equals(args[5])) {
                // Predeclared fairness mode: identical low-cost initialization,
                // identical search budgets and simulator replay protocol.
                Run fla=runDag(dax, seed, pop, gens, "v7-costseed");
                Run nsga=runNsga(dax, seed, pop, gens, true);
                assertCostSeedIdentity(fla,nsga);
                runs.add(fla);
                runs.add(nsga);
            } else if ("costseed-factorial".equals(args[5])) {
                // Controlled 2x2 factorial: the same objective budget and
                // frozen simulator-HV reference, crossing solver and cost seeds.
                // No baseline optimizer is silently reconfigured.
                runs.add(runDag(dax,seed,pop,gens,"v6-pop"));
                Run seededFla=runDag(dax,seed,pop,gens,"v7-costseed");
                runs.add(seededFla);
                runs.add(runNsga(dax,seed,pop,gens,false));
                Run seededNsga=runNsga(dax,seed,pop,gens,true);
                assertCostSeedIdentity(seededFla,seededNsga);
                runs.add(seededNsga);
            } else if ("v12-fair-pair".equals(args[5])) {
                // Three-arm common-reference validation. The two seeded DAG
                // variants and NSGA-II share EXACTLY the same deterministic
                // low-cost first two assignments and evaluation budgets.
                Run v7=runDag(dax,seed,pop,gens,"v7-costseed");
                Run v12=runDag(dax,seed,pop,gens,"v12-hvbandit");
                Run nsga=runNsga(dax,seed,pop,gens,true);
                assertCostSeedIdentity(v7,nsga);
                assertCostSeedIdentity(v12,nsga);
                runs.add(v7);
                runs.add(v12);
                runs.add(nsga);
            } else if ("nsga-only".equals(args[5])) {
                runs.add(runNsga(dax, seed, pop, gens, false));
            } else if ("nsga-costseed".equals(args[5])) {
                runs.add(runNsga(dax, seed, pop, gens, true));
            } else if ("fla-only".equals(args[5])) {
                runs.add(runScalar(dax, seed, pop, gens));
            } else {
                runs.add(runDag(dax, seed, pop, gens, args[5]));
            }
        } else {
            runs.add(runScalar(dax, seed, pop, gens));
            runs.add(runDag(dax, seed, pop, gens,
                    System.getProperty("dagfla.comparisonVariant", "all")));
            runs.add(runNsga(dax, seed, pop, gens, false));
            if (Boolean.getBoolean("dagfla.includeCostSeededNsga"))
                runs.add(runNsga(dax, seed, pop, gens, true));
            runs.add(runMleao(dax, seed, pop, gens));
        }

        for (Run run : runs) {
            if (run.evals <= 0 || run.evals > cap || run.candidates.isEmpty()) {
                throw new IllegalStateException(run.algorithm + " invalid budget/front: " + run.evals);
            }
            // Only unique planned-nondominated schedules are replayed, equally.
            run.plannedNdCount = plannedNondominated(run.candidates).size();
            List<Candidate> front = BUDGET_REPLAY_K > 0
                    ? ("random".equals(BUDGET_REPLAY_POLICY)
                        ? budgetedRandomVisited(run.allVisited,BUDGET_REPLAY_K,seed,run.algorithm)
                        : budgetedPlannedCoverage(run.allVisited, BUDGET_REPLAY_K))
                    : plannedNondominated(run.candidates);
            if (BUDGET_REPLAY_K > 0 && front.size() != BUDGET_REPLAY_K)
                throw new IllegalStateException("Wrong prospective simulator replay call budget");
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
        if (BUDGET_REPLAY_K > 0) {
            Path protocol = Paths.get(prefix + "_budget_protocol.txt");
            Files.write(protocol, Arrays.asList(
                    "PROSPECTIVE_REPLAY_BUDGET_K=" + BUDGET_REPLAY_K,
                    "PROSPECTIVE_REPLAY_POLICY=" + BUDGET_REPLAY_POLICY,
                    "PROSPECTIVE_REPLAY_REPLICATE=" + BUDGET_REPLAY_REPLICATE,
                    "Actual WorkflowSim replays: exactly K distinct visited genotype assignments per solver",
                    "Pre-simulation selection: " + BUDGET_REPLAY_POLICY +
                    " (Pareto layer + max-min coverage, or deterministically seeded uniform random)",
                    "Selection never reads true simulator objective values; K is separate from optimizer evaluation counts",
                    "Simulator HV reference in summary is shared across solver arms within this run only",
                    "This is NOT the full visited simulator Pareto front and not a registered reference point",
                    "The archive size column denotes source archive size; planned nondominated count is separate from replay count"
                    ),StandardCharsets.UTF_8);
        }
    }

    private static void assertCostSeedIdentity(Run fla,Run nsga) {
        if(fla.firstTwoEvaluated.size()!=2 || nsga.firstTwoEvaluated.size()!=2)
            throw new IllegalStateException("Missing initial deterministic cost proposals");
        for(int i=0;i<2;i++) {
            if(!fla.firstTwoEvaluated.get(i).equals(nsga.firstTwoEvaluated.get(i)))
                throw new IllegalStateException(
                    "Cost-seed fairness violation for proposal "+i+": FLA="+
                    fla.firstTwoEvaluated.get(i)+" NSGA-II="+nsga.firstTwoEvaluated.get(i));
        }
        System.out.println("PASS identical first TWO task->VM deterministic cost seeds in FLA v7 and NSGA-II");
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
                "v7-costseed","v7-extreme","v7-both",
                "v8-cost","v8-dual","v8-dual-guide",
                "v9-colocate","v9-separate","v9-adaptive",
                "v10-critical","v10-guarded","v11-bandit","v12-hvbandit");
        if (!supported.contains(variant)) throw new IllegalArgumentException("Unknown ablation: " + variant);
        final boolean minimal="minimal".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_DAG_GUIDANCE = !minimal && !"no-dag".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_CROSS_GROUP_DO = !minimal && !"no-cross".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_SSO = !minimal && !"no-archive-sso".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ADAPTIVE_MUTATION = !minimal && !"no-adaptive-mutation".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ADAPTIVE_PREFERENCE = !minimal && !"no-adaptive-preference".equals(variant);
        boolean isV2=variant.startsWith("v2") || variant.startsWith("v3") || variant.startsWith("v4") || variant.startsWith("v5") || variant.startsWith("v6") || variant.startsWith("v7") || variant.startsWith("v8") || variant.startsWith("v9") || variant.startsWith("v10") || variant.startsWith("v11") || variant.startsWith("v12");
        if(isV2) DAGParetoFLAPlanningAlgorithm.CONFIG_CROSS_GROUP_DO=false;
        DAGParetoFLAPlanningAlgorithm.CONFIG_RESOURCE_AWARE_MUTATION =
                "v3-resource".equals(variant) || "v3-both".equals(variant)
                || "v4-crowding-resource".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_RECOMBINATION =
                "v3-archive".equals(variant) || "v3-both".equals(variant) || variant.startsWith("v4")
                || variant.startsWith("v5") || variant.startsWith("v6") || variant.startsWith("v7") || variant.startsWith("v8") || variant.startsWith("v9") || variant.startsWith("v10") || variant.startsWith("v11") || variant.startsWith("v12");
        DAGParetoFLAPlanningAlgorithm.CONFIG_PARETO_CROWDING_SELECTION = variant.startsWith("v4");
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_DAG_BLOCK =
                "v5-dagblock".equals(variant) || "v5-both".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_PREFERENCE_DONOR =
                "v5-donor".equals(variant) || "v5-both".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_NOVELTY_REPAIR = variant.startsWith("v6") || variant.startsWith("v7") || variant.startsWith("v8") || variant.startsWith("v9") || variant.startsWith("v10") || variant.startsWith("v11") || variant.startsWith("v12");
        DAGParetoFLAPlanningAlgorithm.CONFIG_NOVELTY_GLOBAL_HISTORY =
                "v6-global".equals(variant) || "v6-strong".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_NOVELTY_STRONG_REPAIR =
                "v6-strong".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_COST_SEEDING =
                "v7-costseed".equals(variant) || "v7-both".equals(variant) || variant.startsWith("v8") || variant.startsWith("v9") || variant.startsWith("v10") || variant.startsWith("v11") || variant.startsWith("v12");
        DAGParetoFLAPlanningAlgorithm.CONFIG_COST_EXTREME_GUIDANCE =
                "v7-extreme".equals(variant) || "v7-both".equals(variant) || "v8-dual-guide".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_CRITICAL_LOCAL_AUDIT =
                Boolean.getBoolean("dagfla.criticalLocalAudit");
        DAGParetoFLAPlanningAlgorithm.CONFIG_PHASE_OPERATOR_BANDIT =
                "v11-bandit".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_PHASE_HV_BANDIT =
                "v12-hvbandit".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_CRITICAL_RELOCATION_MODE =
                "v10-critical".equals(variant) ? 1 : "v10-guarded".equals(variant) ? 2 : 0;
        DAGParetoFLAPlanningAlgorithm.CONFIG_EDGE_RELOCATION_MODE =
                "v9-colocate".equals(variant) ? 1 : "v9-separate".equals(variant) ? 2
                : "v9-adaptive".equals(variant) ? 3 : 0;
        DAGParetoFLAPlanningAlgorithm.CONFIG_RESERVE_COST_EXTREME = variant.startsWith("v8");
        DAGParetoFLAPlanningAlgorithm.CONFIG_RESERVE_MAKESPAN_EXTREME =
                "v8-dual".equals(variant) || "v8-dual-guide".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_GLOBAL_SURVIVOR_SELECTION =
                "v2-global".equals(variant) || "v2".equals(variant) || variant.startsWith("v3")
                || variant.startsWith("v4") || variant.startsWith("v5") || variant.startsWith("v6") || variant.startsWith("v7") || variant.startsWith("v8") || variant.startsWith("v9") || variant.startsWith("v10") || variant.startsWith("v11") || variant.startsWith("v12");
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
        saveFirstTwo(r,capture);
        append(r,capture.frontPoints(),capture.frontAssignments());
        appendAuditHistory(r,capture);
        return r;
    }
    private static Run runNsga(String dax,long seed,int pop,int gens,boolean costSeeded) {
        NSGAIIPlanningAlgorithm.CONFIG_OUTPUT_ARCHIVE=true;
        NSGAIIPlanningAlgorithm.CONFIG_SEED_ASSIGNMENTS=null;
        NSGAIIPlanningAlgorithm.CONFIG_COST_SEEDING=costSeeded;
        UnifiedCandidateRecorder.begin((long)pop*(gens+2));
        UnifiedCandidateRecorder.phase(costSeeded ? "NSGA-II-costseed" : "NSGA-II");
        LIWSABenchmarkExample.RunResult result=LIWSABenchmarkExample.runPlanning(
                dax,Parameters.PlanningAlgorithm.NSGAII,Parameters.SchedulingAlgorithm.STATIC,
                "NSGA-II",seed,pop,gens,null);
        NSGAIIPlanningAlgorithm.LastRunMetrics m=NSGAIIPlanningAlgorithm.lastRun;
        if(result==null||m==null)throw new IllegalStateException("NSGA-II failed");
        UnifiedCandidateRecorder.Capture capture=UnifiedCandidateRecorder.end();
        if(capture.evaluationCount()!=m.objectiveEvaluations)
            throw new IllegalStateException("NSGA-II source-counter and recorder mismatch");
        Run r=new Run(costSeeded ? "NSGA-II[costseed]" : "NSGA-II");r.actualGenerations=String.valueOf(gens);r.evals=capture.evaluationCount();
        r.capturedEvaluations=capture.evaluationCount();
        r.distinctObservedAssignments=capture.distinctAssignments();
        r.searchMs=m.searchWallClockMillis;saveFirstTwo(r,capture);append(r,capture.frontPoints(),capture.frontAssignments());
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
    private static void saveFirstTwo(Run run,UnifiedCandidateRecorder.Capture cap) {
        int n=Math.min(2,cap.events().size());
        for(int i=0;i<n;i++)run.firstTwoEvaluated.add(cap.events().get(i).assignment);
    }

    private static void appendAuditHistory(Run run,UnifiedCandidateRecorder.Capture cap) {
        if (SCREENING_AUDIT_N == 0 && BUDGET_REPLAY_K == 0) return;
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
                } else if (SCREENING_ALL_VISITED) {
                    // A history member may be absent from the reported archive without
                    // being strictly planning-dominated; do not silently discard it.
                    dominated.add(c);
                    run.otherPlannedPool++;
                }
            }
        }
        dominated.sort(Comparator.comparingDouble(c->normalizedDistance(c,run.candidates)));
        if (SCREENING_ALL_VISITED && dominated.size() > SCREENING_AUDIT_N)
            throw new IllegalStateException("all-visited audit cap too small for " + run.algorithm
                    + ": need " + dominated.size() + ", cap " + SCREENING_AUDIT_N);
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
                "SCREENING_AUDIT %s %s seed=%d strictDominated=%d plannedTies=%d otherPlanned=%d sampled=%d nondominatedVsBase=%d hvBase=%.9f hvExtra=%.9f delta=%.9f%n",
                wf,run.algorithm,seed,run.dominatedPool,run.tiedPool,run.otherPlannedPool,run.audited.size(),
                run.newSimulatorNondominated,run.simHv,extraHv,run.auditHvGain);
    }

    private static void saveScreeningAudit(String wf,long seed,Path prefix,List<Run> runs)
            throws IOException {
        try(BufferedWriter w=Files.newBufferedWriter(
                Paths.get(prefix+"_screening_summary.csv"),StandardCharsets.UTF_8)) {
            w.write("workflow,algorithm,seed,unique_visited,strict_planned_dominated,planned_tie_pool,other_planned_pool,sampled,non_dominated_vs_base,baseline_sim_hv,extra_sim_hv,delta_hv,delta_hv_pct\n");
            for(Run r:runs) {
                double pct=100.0*r.auditHvGain/Math.max(1e-12,r.simHv);
                w.write(String.format(Locale.ROOT,
                     "%s,%s,%d,%d,%d,%d,%d,%d,%d,%.10f,%.10f,%.10f,%.8f%n",
                    wf,r.algorithm,seed,r.auditUniqueVisited,r.dominatedPool,r.tiedPool,
                     r.otherPlannedPool,r.audited.size(),r.newSimulatorNondominated,r.simHv,
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
                        "%s,%s,%d,%s,%.17g,%.17g,%.17g,%.17g,%s%n",
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

    /**
     * Budgeted, prospective replay selection from PLANNED objective history only.
     * Explicitly different from the default full planned-ND replay protocol.
     * No simulator labels are used before the K chosen schedules are simulated.
     * Pareto fronts are peeled in sorted makespan/cost order; distinct tied
     * genotypes remain in the same layer, rather than being discarded.
     */
    /** Same lexicographic task:vm mapping format as the independent Python selector. */
    private static String canonicalMappingKey(Candidate c) {
        StringBuilder key=new StringBuilder();
        for(Map.Entry<Integer,Integer> entry:c.assignment.entrySet()) {
            if(key.length()>0)key.append('|');
            key.append(entry.getKey()).append(':').append(entry.getValue());
        }
        return key.toString();
    }


    /** Exactly K deterministic genotype-uniform proposals, independent of simulator scores. */
    private static List<Candidate> budgetedRandomVisited(List<Candidate> history,int budget,
            long seed,String algorithm) {
        Map<Map<Integer,Integer>,Candidate> unique=new LinkedHashMap<>();
        for(Candidate c:history)unique.putIfAbsent(c.assignment,c);
        List<Candidate> list=new ArrayList<>(unique.values());
        if(list.size()<budget)throw new IllegalStateException("Insufficient distinct history for K");
        list.sort(Comparator.comparing(FLAResearchExperiment::canonicalMappingKey));
        long salt=(((long)algorithm.hashCode())*0x9E3779B97F4A7C15L)
                ^ 0xD1B54A32D192ED03L ^ seed
                ^ ((long)BUDGET_REPLAY_REPLICATE*0xBF58476D1CE4E5B9L);
        Collections.shuffle(list,new Random(salt));
        System.out.println("PASS prospective planned-only random replay selection K="+budget
                +" replicate="+BUDGET_REPLAY_REPLICATE
                +" uniqueHistory="+unique.size());
        return new ArrayList<>(list.subList(0,budget));
    }

    private static List<Candidate> budgetedPlannedCoverage(List<Candidate> history, int budget) {
        Map<Map<Integer,Integer>,Candidate> unique=new LinkedHashMap<>();
        for(Candidate c:history)unique.putIfAbsent(c.assignment,c);
        List<Candidate> remaining=new ArrayList<>(unique.values());
        if(remaining.size()<budget)
            throw new IllegalStateException("Insufficient unique visited schedules for K="+budget
                    +": have "+remaining.size());
        double mMin=Double.POSITIVE_INFINITY,cMin=Double.POSITIVE_INFINITY;
        double mMax=Double.NEGATIVE_INFINITY,cMax=Double.NEGATIVE_INFINITY;
        for(Candidate c:remaining) {
            valid(c.planned);
            mMin=Math.min(mMin,c.planned[0]);cMin=Math.min(cMin,c.planned[1]);
            mMax=Math.max(mMax,c.planned[0]);cMax=Math.max(cMax,c.planned[1]);
        }
        final double loM=mMin,loC=cMin;
        final double spanM=Math.max(1e-12,mMax-mMin);
        final double spanC=Math.max(1e-12,cMax-cMin);
        // Canonical mapping uses task:vm tokens, matching Python's persisted
        // genotype encoding exactly. Map.toString() is NOT the same ordering.
        Comparator<Candidate> order=Comparator
                .comparingDouble((Candidate c)->c.planned[0])
                .thenComparingDouble(c->c.planned[1])
                .thenComparing(FLAResearchExperiment::canonicalMappingKey);
        List<Candidate> selected=new ArrayList<>();
        while(selected.size()<budget && !remaining.isEmpty()) {
            remaining.sort(order);
            List<Candidate> layer=new ArrayList<>();
            double lowCost=Double.POSITIVE_INFINITY,lastM=Double.NaN,lastC=Double.NaN;
            for(Candidate c:remaining) {
                boolean equalPoint=c.planned[0]==lastM&&c.planned[1]==lastC;
                if(c.planned[1]<lowCost || equalPoint) {
                    layer.add(c);
                    lowCost=Math.min(lowCost,c.planned[1]);
                    lastM=c.planned[0];lastC=c.planned[1];
                }
            }
            if(layer.isEmpty())throw new IllegalStateException("Empty planned Pareto peel");
            remaining.removeAll(layer);
            while(!layer.isEmpty() && selected.size()<budget) {
                Candidate best=null;
                double bestSpacing=Double.NEGATIVE_INFINITY;
                for(Candidate c:layer) {
                    double spacing=Double.POSITIVE_INFINITY;
                    if(selected.isEmpty()) {
                        // First schedule is the minimum makespan extreme.
                        spacing=0;
                    } else {
                        double u=(c.planned[0]-loM)/spanM,v=(c.planned[1]-loC)/spanC;
                        for(Candidate s:selected) {
                            double du=u-(s.planned[0]-loM)/spanM;
                            double dv=v-(s.planned[1]-loC)/spanC;
                            spacing=Math.min(spacing,du*du+dv*dv);
                        }
                    }
                    if(best==null || Double.compare(spacing,bestSpacing)>0 ||
                            (Double.compare(spacing,bestSpacing)==0 && order.compare(c,best)<0)) {
                        best=c;bestSpacing=spacing;
                    }
                }
                selected.add(best);
                layer.remove(best);
            }
        }
        if(selected.size()!=budget)throw new IllegalStateException("Did not cover K="+budget);
        System.out.println("PASS prospective planned-only replay selection K="+budget
                +" uniqueHistory="+unique.size());
        return selected;
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
                    wf,r.algorithm,seed,pop,gens,cap,r.evals,r.sourceFrontSize,r.plannedNdCount,
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
                    w.write(String.format(Locale.ROOT,"%s,%s,%d,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%s%n",
                        wf,r.algorithm,seed,++i,c.planned[0],c.planned[1],
                        c.independentPlanned[0],c.independentPlanned[1],
                        c.simulated[0],c.simulated[1],sb.toString()));
                }
            }
        }
        try(BufferedWriter w=Files.newBufferedWriter(Paths.get(prefix+"_limitations.txt"),StandardCharsets.UTF_8)) {
            w.write("All algorithms use the same simulated Pareto/HV reference within this workflow/seed.\n");
            if (BUDGET_REPLAY_K > 0) {
                w.write("Prospective experiment: replay exactly K=" + BUDGET_REPLAY_K +
                        " distinct evaluated assignments per solver, selected using planned objectives only.\n");
                w.write("This selection policy is " + BUDGET_REPLAY_POLICY +
                        "; it is applied to unique visited genotypes before simulating.\n");
            } else {
                w.write("Historical experiment: replay selected planned-nondominated records, not every visited genotype.\n");
            }
            w.write("FLA-3W combines three independent scalar runs; native optimizers each use one population.\n");
            w.write("Total evaluations are reported and aligned as closely as possible; warm starts disabled.\n");
            w.write("FLA-3W has three runs and MLEAO receives extra generations to align actual evaluation counts.\n");
            w.write("UnifiedCandidateRecorder observes EVERY successful evaluation, including seeds and FLA normalization probes.\n");
            w.write("Search fitness evaluation count is separate from actual WorkflowSim assignment replay count.\n");
            w.write("This experiment does not establish algorithm fidelity or statistical superiority.\n");
            w.write("Independent planned objectives are re-evaluated with the unified LIWSA decoder for every replay.\n");
        }
    }
}
