package org.workflowsim.examples.planning;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
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
import org.workflowsim.planning.ReplayReliabilityGate;
import org.workflowsim.planning.StagedScheduleBatchEvaluator;
import org.workflowsim.planning.BudgetedEvolutionFidelityObjective;
import org.workflowsim.planning.WorkflowFailClosedProbe;
import org.workflowsim.planning.BoundaryFourReplaySelector;
import org.workflowsim.Task;
import org.workflowsim.CondorVM;
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
    /** Search remains identical; extra post-search greedy replay policy. */
    private static final int STAGED_REPLAY_T=Integer.getInteger("dagfla.stagedReplayT",8);
    private static final int STAGED_REPLAY_POOL=Integer.getInteger("dagfla.stagedReplayPool",32);
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
        long policySelectionNanos;
        long simulatorReplayNanos;
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
        final List<Candidate> feedbackPool = new ArrayList<>();
        final List<String> feedbackTrace = new ArrayList<>();
        List<Task> stagedReplayTasks;
        List<CondorVM> stagedReplayVms;
        StagedScheduleBatchEvaluator.SelectionResult stagedSelection;
        BudgetedEvolutionFidelityObjective.Snapshot evolutionFidelity;
        final List<String> stagedPoolIds = new ArrayList<>();
        List<double[]> populationDiagnostics = Collections.emptyList();
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
        if(BUDGET_REPLAY_K>0 && BUDGET_REPLAY_POLICY.endsWith("-greedy")) {
            if(!Boolean.getBoolean("dagfla.stagedReplayContext")||
               BUDGET_REPLAY_K!=8 || STAGED_REPLAY_POOL!=32||
               STAGED_REPLAY_T!=8 ||
               !Arrays.asList("old-greedy","ready-greedy","staged-greedy","active-uniform-greedy","boundary-four","dominated-random-four").contains(BUDGET_REPLAY_POLICY))
                throw new IllegalArgumentException("Frozen staged K8/T8/32 context/policy required");
        }
        if (BUDGET_REPLAY_K > 0 && !Arrays.asList("pareto-cover","random","scalar-sweep","extreme-band3","online-nearest-hv","online-observed-hv","online-planned-hv","online-reliability-gated","old-greedy","ready-greedy","staged-greedy","active-uniform-greedy","boundary-four","dominated-random-four").contains(BUDGET_REPLAY_POLICY))
            throw new IllegalArgumentException("invalid prospective replay policy: "+BUDGET_REPLAY_POLICY);
        if(!"off".equals(System.getProperty("dagfla.evolutionFidelity","off"))) {
            // Explicit prospective K16 confirmation is isolated from all
            // historical K8 data and has no effect with opt-in disabled.
            final boolean confirmationK16 =
                    Boolean.getBoolean("dagfla.evolutionK16Confirmation");
            if(BUDGET_REPLAY_K!=(confirmationK16?16:8) ||
               !"pareto-cover".equals(BUDGET_REPLAY_POLICY) ||
               pop!=30||gens!=100||
               Integer.getInteger("dagfla.evolutionTotalVisits",3030)!=3030 ||
               Integer.getInteger("dagfla.evolutionReadyBudget",378)!=378)
                throw new IllegalArgumentException(
                    "Frozen evolutionary budget: pop30 gen100 K"+
                    (confirmationK16?16:8)+" quota378");
        }
        if (BUDGET_REPLAY_K < 0 || BUDGET_REPLAY_K > 10000)
            throw new IllegalArgumentException("invalid actual replay budget");
        if (BUDGET_REPLAY_REPLICATE < 0 || BUDGET_REPLAY_REPLICATE > 1024)
            throw new IllegalArgumentException("random replay replicate out of range");
        if (BUDGET_REPLAY_REPLICATE != 0 &&
                (BUDGET_REPLAY_K == 0 || !"random".equals(BUDGET_REPLAY_POLICY)))
            throw new IllegalArgumentException("random replicate only applies to prospective random policy");
        // An explicit research-only, two-phase diagnostic may replay a second
        // separate stratum of planning-dominated/tied genotypes AFTER K planned
        // candidates are frozen. This does NOT enter optimization or K16 HV.
        // Historical behavior remains an error unless this extra flag is set.
        if (BUDGET_REPLAY_K > 0 && SCREENING_AUDIT_N > 0 &&
                !Boolean.getBoolean("dagfla.allowSeparateKPlusScreeningDiagnostic"))
            throw new IllegalArgumentException(
                "K-limited replay plus screening requires explicit separate diagnostic opt-in");
        if (Boolean.getBoolean("dagfla.allowSeparateKPlusScreeningDiagnostic") &&
                (BUDGET_REPLAY_K<=0 || SCREENING_AUDIT_N<=0 ||
                 BUDGET_REPLAY_POLICY.startsWith("online-")))
            throw new IllegalArgumentException(
                "Separate K + screening diagnostic requires positive K, extra sample and nononline fixed replay policy");
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
            } else if ("v19-queue-risk-four-arm".equals(args[5])) {
                // New mechanistic FLA proposal: ORIGINAL same target fitness
                // for v12, v18, v19 and seeded NSGA-II; ONLY FLA proposal differs.
                // Extra v18/v19 internal predictor forecasts are UNCOUNTED target
                // objective operations and must be audited with source wall time.
                Run parent=runDag(dax,seed,pop,gens,"v12-hvbandit");
                Run disagreement=runDag(dax,seed,pop,gens,"v18-disagreement");
                Run queueRisk=runDag(dax,seed,pop,gens,"v19-queue-risk");
                Run nsga=runNsga(dax,seed,pop,gens,true);
                assertCostSeedIdentity(parent,nsga);
                assertCostSeedIdentity(disagreement,nsga);
                assertCostSeedIdentity(queueRisk,nsga);
                runs.add(parent);
                runs.add(disagreement);
                runs.add(queueRisk);
                runs.add(nsga);
            } else if ("v20-frontier-four-arm".equals(args[5])) {
                Run base=runDag(dax,seed,pop,gens,"v12-hvbandit");
                Run randomNovelty=runDag(dax,seed,pop,gens,"v20-frontier-random");
                Run dagNovelty=runDag(dax,seed,pop,gens,"v20-frontier-dag");
                Run nsga=runNsga(dax,seed,pop,gens,true);
                for(Run arm:Arrays.asList(base,randomNovelty,dagNovelty))
                    assertCostSeedIdentity(arm,nsga);
                runs.addAll(Arrays.asList(base,randomNovelty,dagNovelty,nsga));
            } else if ("v18-disagreement-three-arm".equals(args[5])) {
                // Same seeded NSGA-II control and original v12 parent policy.
                // v18 differs from v12 ONLY via its optional candidate proposal.
                Run original=runDag(dax,seed,pop,gens,"v12-hvbandit");
                Run experimental=runDag(dax,seed,pop,gens,"v18-disagreement");
                Run nsga=runNsga(dax,seed,pop,gens,true);
                assertCostSeedIdentity(original,nsga);
                assertCostSeedIdentity(experimental,nsga);
                runs.add(original);
                runs.add(experimental);
                runs.add(nsga);
            } else if ("v12-nsga-ready-pair".equals(args[5])) {
                // Research-only 2-arm parity: the same budget, deterministic
                // cost seeds, and active decoder selected by JVM property.
                // The existing behavior in every other mode is unchanged.
                Run fla=runDag(dax,seed,pop,gens,"v12-hvbandit");
                Run nsga=runNsga(dax,seed,pop,gens,true);
                assertCostSeedIdentity(fla,nsga);
                runs.add(fla);
                runs.add(nsga);
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
            } else if ("v13-search-pair".equals(args[5])) {
                // Predeclared search-operator comparison: all three optimizers
                // use identical two initial deterministic task->VM cost seeds.
                Run v12=runDag(dax,seed,pop,gens,"v12-hvbandit");
                Run v13=runDag(dax,seed,pop,gens,"v13-join");
                Run nsga=runNsga(dax,seed,pop,gens,true);
                assertCostSeedIdentity(v12,nsga);
                assertCostSeedIdentity(v13,nsga);
                runs.add(v12); runs.add(v13); runs.add(nsga);
            } else if ("v14-search-fourarm".equals(args[5])) {
                Run v12=runDag(dax,seed,pop,gens,"v12-hvbandit");
                Run random=runDag(dax,seed,pop,gens,"v14-randompair");
                Run timeline=runDag(dax,seed,pop,gens,"v14-timelinepair");
                Run nsga=runNsga(dax,seed,pop,gens,true);
                assertCostSeedIdentity(v12,nsga);
                assertCostSeedIdentity(random,nsga);
                assertCostSeedIdentity(timeline,nsga);
                runs.add(v12);runs.add(random);runs.add(timeline);runs.add(nsga);
            } else if ("v15-search-sixarm".equals(args[5])) {
                Run v12=runDag(dax,seed,pop,gens,"v12-hvbandit");
                Run v14random=runDag(dax,seed,pop,gens,"v14-randompair");
                Run v14timeline=runDag(dax,seed,pop,gens,"v14-timelinepair");
                Run v15random=runDag(dax,seed,pop,gens,"v15-randomgate");
                Run v15timeline=runDag(dax,seed,pop,gens,"v15-timelinegate");
                Run nsga=runNsga(dax,seed,pop,gens,true);
                for(Run arm:Arrays.asList(v12,v14random,v14timeline,v15random,v15timeline))
                    assertCostSeedIdentity(arm,nsga);
                runs.addAll(Arrays.asList(v12,v14random,v14timeline,v15random,v15timeline,nsga));
            } else if ("population-mechanism-fivearm".equals(args[5])) {
                if(!Boolean.getBoolean("dagfla.populationDiagnostics"))
                    throw new IllegalArgumentException("Population diagnostics required for mechanism comparison");
                Run v12=runDag(dax,seed,pop,gens,"v12-hvbandit");
                Run v14random=runDag(dax,seed,pop,gens,"v14-randompair");
                Run v14timeline=runDag(dax,seed,pop,gens,"v14-timelinepair");
                Run v15random=runDag(dax,seed,pop,gens,"v15-randomgate");
                Run v15timeline=runDag(dax,seed,pop,gens,"v15-timelinegate");
                Run nsga=runNsga(dax,seed,pop,gens,true);
                for(Run arm:Arrays.asList(v12,v14random,v14timeline,v15random,v15timeline))
                    assertCostSeedIdentity(arm,nsga);
                runs.addAll(Arrays.asList(v12,v14random,v14timeline,v15random,v15timeline,nsga));
            } else if ("bandit-opportunity-sixarm".equals(args[5])) {
                if(!Boolean.getBoolean("dagfla.populationDiagnostics"))
                    throw new IllegalArgumentException("Phase population diagnostics required for opportunity mechanism experiment");
                Run v12=runDag(dax,seed,pop,gens,"v12-hvbandit");
                Run shamRandom=runDag(dax,seed,pop,gens,"v16-shamrandom");
                Run activeRandom=runDag(dax,seed,pop,gens,"v14-randompair");
                Run shamTimeline=runDag(dax,seed,pop,gens,"v16-shamtimeline");
                Run activeTimeline=runDag(dax,seed,pop,gens,"v14-timelinepair");
                Run nsga=runNsga(dax,seed,pop,gens,true);
                for(Run arm:Arrays.asList(v12,shamRandom,activeRandom,shamTimeline,activeTimeline))
                    assertCostSeedIdentity(arm,nsga);
                runs.addAll(Arrays.asList(v12,shamRandom,activeRandom,shamTimeline,activeTimeline,nsga));
            } else if ("v17-phase-eightarm".equals(args[5])) {
                Run base=runDag(dax,seed,pop,gens,"v12-hvbandit");
                Run fullR=runDag(dax,seed,pop,gens,"v14-randompair");
                Run doR=runDag(dax,seed,pop,gens,"v17-do-random");
                Run lateR=runDag(dax,seed,pop,gens,"v17-late-random");
                Run fullT=runDag(dax,seed,pop,gens,"v14-timelinepair");
                Run doT=runDag(dax,seed,pop,gens,"v17-do-timeline");
                Run lateT=runDag(dax,seed,pop,gens,"v17-late-timeline");
                Run nsga=runNsga(dax,seed,pop,gens,true);
                for(Run x:Arrays.asList(base,fullR,doR,lateR,fullT,doT,lateT))
                    assertCostSeedIdentity(x,nsga);
                runs.addAll(Arrays.asList(base,fullR,doR,lateR,fullT,doT,lateT,nsga));
            } else if ("v17-confirm-fourarm".equals(args[5])) {
                Run baseline=runDag(dax,seed,pop,gens,"v12-hvbandit");
                Run doRandom=runDag(dax,seed,pop,gens,"v17-do-random");
                Run lateRandom=runDag(dax,seed,pop,gens,"v17-late-random");
                Run nsga=runNsga(dax,seed,pop,gens,true);
                for(Run arm:Arrays.asList(baseline,doRandom,lateRandom))
                    assertCostSeedIdentity(arm,nsga);
                runs.addAll(Arrays.asList(baseline,doRandom,lateRandom,nsga));
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

        // Freeze all paired Task/VM diagnostic evidence before ANY K replay:
        // no simulated label for a candidate is available to this probe.
        if(Integer.getInteger("dagfla.failClosedProbePairs",0)>0) {
            for(Run run:runs) {
                for(Candidate c:run.allVisited)
                    if(c.simulated!=null)
                        throw new IllegalStateException("Probe leaked future replay truth");
            }
            saveFailClosedProbe(prefix,runs);
            System.out.println("PASS pre-replay uncalibrated fail-closed mapping probe frozen");
        }
        // Passive model-space diagnostic is frozen BEFORE the first WorkflowSim
        // replay. It never changes fitness, search state, or the K selector.
        if(Boolean.getBoolean("dagfla.exportVisitedObjectiveSpace"))
            saveFullVisitedObjectiveSpace(prefix,runs,wf,seed);
        for (Run run : runs) {
            if (run.evals <= 0 || run.evals > cap || run.candidates.isEmpty()) {
                throw new IllegalStateException(run.algorithm + " invalid budget/front: " + run.evals);
            }
            // Only unique planned-nondominated schedules are replayed, equally.
            run.plannedNdCount = plannedNondominated(run.candidates).size();
            final boolean feedback = BUDGET_REPLAY_K > 0 && BUDGET_REPLAY_POLICY.startsWith("online-");
            if (feedback && BUDGET_REPLAY_K < 5)
                throw new IllegalArgumentException("online feedback requires K>=5");
            long initialSelectionStartNanos=System.nanoTime();
            if (feedback)
                run.feedbackPool.addAll(budgetedPlannedCoverage(run.allVisited,
                        Math.min(64,run.distinctObservedAssignments)));
            List<Candidate> front = feedback
                    ? new ArrayList<>(run.feedbackPool.subList(0,4))
                    : BUDGET_REPLAY_K > 0
                    ? (BUDGET_REPLAY_POLICY.endsWith("-greedy")
                        ? budgetedStagedReplay(run,BUDGET_REPLAY_POLICY,BUDGET_REPLAY_K)
                        : ("boundary-four".equals(BUDGET_REPLAY_POLICY) ||
                           "dominated-random-four".equals(BUDGET_REPLAY_POLICY))
                        ? budgetedBoundaryFour(run.allVisited,BUDGET_REPLAY_K,seed,run.algorithm,
                              "dominated-random-four".equals(BUDGET_REPLAY_POLICY))
                        : "random".equals(BUDGET_REPLAY_POLICY)
                        ? budgetedRandomVisited(run.allVisited,BUDGET_REPLAY_K,seed,run.algorithm)
                        : "scalar-sweep".equals(BUDGET_REPLAY_POLICY)
                            ? budgetedScalarSweep(run.allVisited,BUDGET_REPLAY_K)
                            : "extreme-band3".equals(BUDGET_REPLAY_POLICY)
                                ? budgetedExtremeBand3(run.allVisited,BUDGET_REPLAY_K)
                                : budgetedPlannedCoverage(run.allVisited,BUDGET_REPLAY_K))
                    : plannedNondominated(run.candidates);
            run.policySelectionNanos+=System.nanoTime()-initialSelectionStartNanos;
            if (BUDGET_REPLAY_K > 0 && !feedback && front.size() != BUDGET_REPLAY_K)
                throw new IllegalStateException("Wrong prospective simulator replay call budget");
            run.candidates.clear(); run.candidates.addAll(front);
            System.out.printf(Locale.ROOT,
                    "REPLAY %s %s seed=%d evaluations=%d archive=%d uniqueND=%d%n",
                    wf, run.algorithm, seed, run.evals, run.sourceFrontSize, front.size());
            final int replayGoal = feedback ? BUDGET_REPLAY_K : front.size();
            for (int index=0;index<replayGoal;index++) {
                if (feedback && index>=4) {
                    long selectStart=System.nanoTime();
                    FeedbackChoice selection = "online-reliability-gated".equals(BUDGET_REPLAY_POLICY)
                            ? chooseReliabilityGatedFeedback(run.feedbackPool,run.candidates)
                            : chooseFeedbackMode(run.feedbackPool,run.candidates,BUDGET_REPLAY_POLICY);
                    run.policySelectionNanos+=System.nanoTime()-selectStart;
                    if (selection==null || run.candidates.contains(selection.candidate))
                        throw new IllegalStateException("Nonunique online feedback candidate");
                    run.candidates.add(selection.candidate);
                    run.feedbackTrace.add(String.format(Locale.ROOT,
                            "%s,%d,%d,%s,%s,%s,%.17g,%.17g,%.17g",
                            run.algorithm,index+1,index,selection.decisionMode,canonicalMappingKey(selection.candidate),
                            selection.nearestMapping,selection.predictedMakespan,
                            selection.predictedCost,selection.predictedHvGain));
                } else if (feedback) {
                    Candidate warm=run.candidates.get(index);
                    run.feedbackTrace.add(String.format(Locale.ROOT,
                            "%s,%d,0,warm,%s,,%.17g,%.17g,0",
                            run.algorithm,index+1,canonicalMappingKey(warm),
                            warm.planned[0],warm.planned[1]));
                }
                Candidate c=run.candidates.get(index);
                long simulatorStart=System.nanoTime();
                LIWSABenchmarkExample.RunResult result = LIWSABenchmarkExample.runPlanning(
                        dax, Parameters.PlanningAlgorithm.LIWSA,
                        Parameters.SchedulingAlgorithm.STATIC,
                        "replay_" + run.algorithm.replace("-","_"), seed,
                        1, 0, Collections.singletonList(c.assignment));
                run.simulatorReplayNanos+=System.nanoTime()-simulatorStart;
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
            if(feedback && run.candidates.size()!=BUDGET_REPLAY_K)
                throw new IllegalStateException("Online K budget was not exhausted: "+run.candidates.size());
            List<double[]> actual = new ArrayList<>();
            for (Candidate c : run.candidates) actual.add(c.simulated);
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
        if(BUDGET_REPLAY_K>0 && BUDGET_REPLAY_POLICY.endsWith("-greedy"))
            saveStagedReplaySelection(prefix,runs);
        if(!"off".equals(System.getProperty("dagfla.evolutionFidelity","off")))
            saveEvolutionFidelity(prefix,runs);
        if(Boolean.getBoolean("dagfla.populationDiagnostics"))
            savePopulationDiagnostics(prefix,runs,gens,pop);
        if (SCREENING_AUDIT_N > 0) saveScreeningAudit(wf,seed,prefix,runs);
        if (BUDGET_REPLAY_K > 0) {
            saveVisitedFingerprints(wf,seed,prefix,runs);
            if(BUDGET_REPLAY_POLICY.startsWith("online-"))
                saveFeedbackTrace(prefix,runs);
            Path protocol = Paths.get(prefix + "_budget_protocol.txt");
            Files.write(protocol, Arrays.asList(
                    "PROSPECTIVE_REPLAY_BUDGET_K=" + BUDGET_REPLAY_K,
                    "PROSPECTIVE_REPLAY_POLICY=" + BUDGET_REPLAY_POLICY,
                    "VM_SPEED_PROFILE=" + System.getProperty("liwsa.vmSpeedProfile","default"),
                    "VM_PRICE_PROFILE=" + System.getProperty("liwsa.vmPriceProfile","default"),
                    "PROSPECTIVE_REPLAY_REPLICATE=" + BUDGET_REPLAY_REPLICATE,
                    "Actual WorkflowSim replays: exactly K distinct visited genotype assignments per solver",
                    "Replay selection: " + BUDGET_REPLAY_POLICY +
                    " (online variants may use previous real simulator outcomes only; other policies are pre-simulation)",
                    "Online mode starts with four fixed Pareto-cover schedules and uses past observations only for later choices",
                    "No replay policy may read labels of unobserved assignments; K is separate from optimizer evaluations",
                    "Simulator HV reference in summary is shared across solver arms within this run only",
                    "This is NOT the full visited simulator Pareto front and not a registered reference point",
                    "The archive size column denotes source archive size; planned nondominated count is separate from replay count"
                    ),StandardCharsets.UTF_8);
        }
    }


    /** Exact selected breeding-population measurement, no simulated labels. */
    private static void savePopulationDiagnostics(Path prefix,List<Run> runs,
            int generations,int pop) throws IOException {
        Path p=Paths.get(prefix+"_population_diagnostics.csv");
        try(BufferedWriter w=Files.newBufferedWriter(p,StandardCharsets.UTF_8)){
            w.write("algorithm,generation,phase,selected_slots,selected_unique,selected_duplicate_slots,group1_unique,group2_unique,cross_group_overlap,pairwise_hamming_all,pairwise_hamming_group1,pairwise_hamming_group2,generated_unique,archive_insert_events,local_gate_rejections,bandit_baseline_uses,bandit_colocate_uses,bandit_critical_uses,archive_size,min_archive_makespan,min_archive_cost,objective_evaluations\n");
            for(Run run:runs) {
                if(run.algorithm.startsWith("NSGA-II"))continue;
                if(run.populationDiagnostics.size()!=generations+1)
                    throw new IllegalStateException("Missing per-generation population snapshots: "+run.algorithm);
                int expectedEval=pop;
                for(int j=0;j<run.populationDiagnostics.size();j++) {
                    double[] row=run.populationDiagnostics.get(j);
                    if(row.length!=21 || (int)row[0]!=j ||
                       (int)row[2]!=pop || (int)row[20]!=expectedEval)
                        throw new IllegalStateException("Population trace corrupt: "+run.algorithm+" generation="+j);
                    w.write(run.algorithm);
                    for(double value:row)w.write(String.format(Locale.ROOT,",%.17g",value));
                    w.write("\n");
                    expectedEval+=pop;
                }
            }
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
                "v10-critical","v10-guarded","v11-bandit","v12-hvbandit","v13-join",
                "v14-randompair","v14-timelinepair",
                "v15-randomgate","v15-timelinegate",
                "v16-shamrandom","v16-shamtimeline",
                "v17-do-random","v17-late-random","v17-do-timeline","v17-late-timeline",
                "v18-disagreement","v19-queue-risk","v20-frontier-random","v20-frontier-dag");
        if (!supported.contains(variant)) throw new IllegalArgumentException("Unknown ablation: " + variant);
        final boolean minimal="minimal".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_DAG_GUIDANCE = !minimal && !"no-dag".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_CROSS_GROUP_DO = !minimal && !"no-cross".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_SSO = !minimal && !"no-archive-sso".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ADAPTIVE_MUTATION = !minimal && !"no-adaptive-mutation".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ADAPTIVE_PREFERENCE = !minimal && !"no-adaptive-preference".equals(variant);
        boolean isV2=variant.startsWith("v2") || variant.startsWith("v3") || variant.startsWith("v4") || variant.startsWith("v5") || variant.startsWith("v6") || variant.startsWith("v7") || variant.startsWith("v8") || variant.startsWith("v9") || variant.startsWith("v10") || variant.startsWith("v11") || (variant.startsWith("v12") || variant.startsWith("v13") || (variant.startsWith("v14") || variant.startsWith("v15") || variant.startsWith("v16") || (variant.startsWith("v17") || (variant.startsWith("v18") || (variant.startsWith("v19") || variant.startsWith("v20"))))));
        if(isV2) DAGParetoFLAPlanningAlgorithm.CONFIG_CROSS_GROUP_DO=false;
        DAGParetoFLAPlanningAlgorithm.CONFIG_RESOURCE_AWARE_MUTATION =
                "v3-resource".equals(variant) || "v3-both".equals(variant)
                || "v4-crowding-resource".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_RECOMBINATION =
                "v3-archive".equals(variant) || "v3-both".equals(variant) || variant.startsWith("v4")
                || variant.startsWith("v5") || variant.startsWith("v6") || variant.startsWith("v7") || variant.startsWith("v8") || variant.startsWith("v9") || variant.startsWith("v10") || variant.startsWith("v11") || (variant.startsWith("v12") || variant.startsWith("v13") || (variant.startsWith("v14") || variant.startsWith("v15") || variant.startsWith("v16") || (variant.startsWith("v17") || (variant.startsWith("v18") || (variant.startsWith("v19") || variant.startsWith("v20"))))));
        DAGParetoFLAPlanningAlgorithm.CONFIG_PARETO_CROWDING_SELECTION = variant.startsWith("v4");
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_DAG_BLOCK =
                "v5-dagblock".equals(variant) || "v5-both".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_PREFERENCE_DONOR =
                "v5-donor".equals(variant) || "v5-both".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_NOVELTY_REPAIR = variant.startsWith("v6") || variant.startsWith("v7") || variant.startsWith("v8") || variant.startsWith("v9") || variant.startsWith("v10") || variant.startsWith("v11") || (variant.startsWith("v12") || variant.startsWith("v13") || (variant.startsWith("v14") || variant.startsWith("v15") || variant.startsWith("v16") || (variant.startsWith("v17") || (variant.startsWith("v18") || (variant.startsWith("v19") || variant.startsWith("v20"))))));
        DAGParetoFLAPlanningAlgorithm.CONFIG_NOVELTY_GLOBAL_HISTORY =
                "v6-global".equals(variant) || "v6-strong".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_NOVELTY_STRONG_REPAIR =
                "v6-strong".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_COST_SEEDING =
                "v7-costseed".equals(variant) || "v7-both".equals(variant) || variant.startsWith("v8") || variant.startsWith("v9") || variant.startsWith("v10") || variant.startsWith("v11") || (variant.startsWith("v12") || variant.startsWith("v13") || (variant.startsWith("v14") || variant.startsWith("v15") || variant.startsWith("v16") || (variant.startsWith("v17") || (variant.startsWith("v18") || (variant.startsWith("v19") || variant.startsWith("v20"))))));
        DAGParetoFLAPlanningAlgorithm.CONFIG_COST_EXTREME_GUIDANCE =
                "v7-extreme".equals(variant) || "v7-both".equals(variant) || "v8-dual-guide".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_CRITICAL_LOCAL_AUDIT =
                Boolean.getBoolean("dagfla.criticalLocalAudit");
        DAGParetoFLAPlanningAlgorithm.CONFIG_PHASE_OPERATOR_BANDIT =
                "v11-bandit".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_PHASE_HV_BANDIT =
                "v12-hvbandit".equals(variant) || "v13-join".equals(variant)
                || (variant.startsWith("v14") || variant.startsWith("v15") || variant.startsWith("v16") || (variant.startsWith("v17") || (variant.startsWith("v18") || (variant.startsWith("v19") || variant.startsWith("v20")))));
        DAGParetoFLAPlanningAlgorithm.CONFIG_JOIN_AWARE_RELOCATION =
                "v13-join".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_PAIRED_LOCAL_SEARCH_MODE =
                ("v14-randompair".equals(variant) || "v15-randomgate".equals(variant))?1:
                ("v14-timelinepair".equals(variant) || "v15-timelinegate".equals(variant))?2:
                "v16-shamrandom".equals(variant)?3:
                "v16-shamtimeline".equals(variant)?4:
                ("v17-do-random".equals(variant) || "v17-late-random".equals(variant))?1:
                ("v17-do-timeline".equals(variant) || "v17-late-timeline".equals(variant))?2:0;
        DAGParetoFLAPlanningAlgorithm.CONFIG_PAIRED_ACTIVE_WINDOW=
                variant.startsWith("v17-do-")?1:
                variant.startsWith("v17-late-")?2:0;
        DAGParetoFLAPlanningAlgorithm.CONFIG_PARETO_GATED_LOCAL_SURVIVOR=
                variant.startsWith("v15");
        DAGParetoFLAPlanningAlgorithm.CONFIG_POPULATION_DIAGNOSTICS=
                Boolean.getBoolean("dagfla.populationDiagnostics");
        DAGParetoFLAPlanningAlgorithm.CONFIG_DISAGREEMENT_RELOCATION=
                "v18-disagreement".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_QUEUE_RISK_RELOCATION=
                "v19-queue-risk".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_FRONTIER_NOVELTY_MODE=
                "v20-frontier-random".equals(variant)?1:
                "v20-frontier-dag".equals(variant)?2:0;
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
                || variant.startsWith("v4") || variant.startsWith("v5") || variant.startsWith("v6") || variant.startsWith("v7") || variant.startsWith("v8") || variant.startsWith("v9") || variant.startsWith("v10") || variant.startsWith("v11") || (variant.startsWith("v12") || variant.startsWith("v13") || (variant.startsWith("v14") || variant.startsWith("v15") || variant.startsWith("v16") || (variant.startsWith("v17") || (variant.startsWith("v18") || (variant.startsWith("v19") || variant.startsWith("v20"))))));
        DAGParetoFLAPlanningAlgorithm.CONFIG_RANDOM_IMMIGRANTS =
                "v2-immigrants".equals(variant) || "v2".equals(variant);
        DAGParetoFLAPlanningAlgorithm.CONFIG_ARCHIVE_CAPACITY = Math.max(pop, 32);
        DAGParetoFLAPlanningAlgorithm.CONFIG_SEED_ASSIGNMENTS = null;
        BudgetedEvolutionFidelityObjective.clearCurrent();
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
        r.evolutionFidelity=BudgetedEvolutionFidelityObjective.currentSnapshot();
        BudgetedEvolutionFidelityObjective.clearCurrent();
        if(Boolean.getBoolean("dagfla.stagedReplayContext")){
            r.stagedReplayTasks=capture.replayTasks();
            r.stagedReplayVms=capture.replayVms();
        }
        saveFirstTwo(r,capture);
        append(r,capture.frontPoints(),capture.frontAssignments());
        appendAuditHistory(r,capture);
        if(Boolean.getBoolean("dagfla.populationDiagnostics")){
            if(m.populationDiagnostics==null || m.populationDiagnostics.size()!=gens+1)
                throw new IllegalStateException("Incomplete nonintrusive population trace");
            r.populationDiagnostics=new ArrayList<>();
            for(double[] row:m.populationDiagnostics)r.populationDiagnostics.add(row.clone());
        }
        return r;
    }
    private static Run runNsga(String dax,long seed,int pop,int gens,boolean costSeeded) {
        NSGAIIPlanningAlgorithm.CONFIG_OUTPUT_ARCHIVE=true;
        NSGAIIPlanningAlgorithm.CONFIG_SEED_ASSIGNMENTS=null;
        NSGAIIPlanningAlgorithm.CONFIG_COST_SEEDING=costSeeded;
        BudgetedEvolutionFidelityObjective.clearCurrent();
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
        r.searchMs=m.searchWallClockMillis;
        r.evolutionFidelity=BudgetedEvolutionFidelityObjective.currentSnapshot();
        BudgetedEvolutionFidelityObjective.clearCurrent();
        if(Boolean.getBoolean("dagfla.stagedReplayContext")){
            r.stagedReplayTasks=capture.replayTasks();
            r.stagedReplayVms=capture.replayVms();
        }
        saveFirstTwo(r,capture);append(r,capture.frontPoints(),capture.frontAssignments());
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


    /** Passive ordered source objective export. NEVER read actual simulator labels.
     * All rows reproduce the first-write distinct candidate-history commitment.
     */
    private static void saveFullVisitedObjectiveSpace(Path prefix,List<Run> runs,
            String workflow,long seed) throws IOException {
        Path output=Paths.get(prefix+"_full_visited_objectives.csv");
        try(BufferedWriter w=Files.newBufferedWriter(output,StandardCharsets.UTF_8)) {
            w.write("workflow,algorithm,seed,visited_index,planned_makespan,planned_cost,canonical_mapping\n");
            for(Run run:runs) {
                if(run.allVisited.isEmpty() ||
                   run.allVisited.size()!=run.distinctObservedAssignments)
                    throw new IllegalStateException(
                        "Incomplete distinct source history: "+run.algorithm);
                Set<String> mappingIds=new HashSet<>();
                for(int i=0;i<run.allVisited.size();i++) {
                    Candidate c=run.allVisited.get(i);
                    if(c.simulated!=null || c.independentPlanned!=null)
                        throw new IllegalStateException(
                            "Passive export attempted after simulator truth became available");
                    valid(c.planned);
                    String mappingId=canonicalMappingKey(c);
                    if(!mappingIds.add(mappingId))
                        throw new IllegalStateException("Repeated physical TaskID/VMID genotype");
                    w.write(String.format(Locale.ROOT,
                        "%s,%s,%d,%d,%.17g,%.17g,%s%n",
                        workflow,run.algorithm,seed,i+1,c.planned[0],c.planned[1],mappingId));
                }
                System.out.printf(Locale.ROOT,
                    "PASS PRE_REPLAY_VISITED_OBJECTIVES solver=%s rows=%d no_simulator_labels=1%n",
                    run.algorithm,run.allVisited.size());
            }
        }
    }

    /** Stable SHA-256 commitment to the complete ordered, DISTINCT planner-evaluated pool.
     *  Uses canonical task:VM mapping and exact double bits, not displayed rounded CSV numbers.
     *  Enables fairness auditors to prove that only the replay selector changed.
     */
    private static void saveVisitedFingerprints(String wf,long seed,Path prefix,List<Run> runs)
            throws Exception {
        try(BufferedWriter w=Files.newBufferedWriter(
                Paths.get(prefix+"_visited_fingerprints.csv"),StandardCharsets.UTF_8)) {
            w.write("workflow,algorithm,seed,distinct_visited,history_sha256\n");
            for(Run run:runs) {
                if(run.allVisited.isEmpty() || run.allVisited.size()!=run.distinctObservedAssignments)
                    throw new IllegalStateException("Incomplete ordered distinct visited history: "+run.algorithm);
                MessageDigest digest=MessageDigest.getInstance("SHA-256");
                for(Candidate c:run.allVisited) {
                    String entry=canonicalMappingKey(c)+"|"+
                            Long.toHexString(Double.doubleToLongBits(c.planned[0]))+"|"+
                            Long.toHexString(Double.doubleToLongBits(c.planned[1]))+"\n";
                    digest.update(entry.getBytes(StandardCharsets.UTF_8));
                }
                StringBuilder hex=new StringBuilder();
                for(byte value:digest.digest())
                    hex.append(String.format(Locale.ROOT,"%02x",value&255));
                w.write(wf+","+run.algorithm+","+seed+","+run.allVisited.size()+","+hex+"\n");
            }
        }
    }


    /** Audit decisions made BEFORE each real simulator replay, never future labels. */
    private static void saveFeedbackTrace(Path prefix,List<Run> runs) throws IOException {
        try(BufferedWriter w=Files.newBufferedWriter(
                Paths.get(prefix+"_online_trace.csv"),StandardCharsets.UTF_8)) {
            w.write("algorithm,step,observed_before,mode,mapping,nearest_observed_mapping,predicted_makespan,predicted_cost,predicted_hv_gain\n");
            for(Run r:runs) {
                if(r.feedbackTrace.size()!=BUDGET_REPLAY_K)
                    throw new IllegalStateException("Online trace and simulator budget mismatch: "+r.algorithm);
                for(String entry:r.feedbackTrace)w.write(entry+"\n");
            }
        }
    }

    private static final class FeedbackChoice {
        final Candidate candidate;
        final String nearestMapping;
        final double predictedMakespan;
        final double predictedCost;
        final double predictedHvGain;
        final String decisionMode;
        FeedbackChoice(Candidate c,String near,double m,double cost,double hv) {
            this(c,near,m,cost,hv,"online");
        }
        FeedbackChoice(Candidate c,String near,double m,double cost,double hv,String mode) {
            candidate=c;nearestMapping=near;predictedMakespan=m;
            predictedCost=cost;predictedHvGain=hv;decisionMode=mode;
        }
    }

    /**
     * Pure sequential choice: read ONLY observations from already replayed genotypes.
     * 1-nearest neighbor in normalized PLANNED makespan/cost provides a multiplicative
     * makespan residual, shrunk by half and capped at +/-10%; planned cost unchanged.
     * Among up to 64 planned-coverage candidates, maximize predicted marginal HV
     * against the ACTUALLY observed simulator front. Ties favor planned diversity.
     * All constants are fixed before the new holdout seed cohort.
     */
    private static FeedbackChoice chooseOnlineFeedback(List<Candidate> pool,List<Candidate> selected) {
        return chooseFeedbackMode(pool,selected,"online-nearest-hv");
    }

    /**
     * Experimental, predeclared reliability gate (not the production default).
     * All tests use only completed earlier replay labels. If there is insufficient
     * ordering evidence or a large/unstable makespan residual, fall back to the
     * next not-yet-replayed candidate in the fixed planned Pareto-cover order.
     * This policy is independent of the optimizer and cannot change its history.
     */
    private static FeedbackChoice chooseReliabilityGatedFeedback(
            List<Candidate> pool,List<Candidate> selected) {
        if(pool.size()<=selected.size() || selected.size()<4)
            throw new IllegalStateException("Invalid reliability-gated replay pool");
        List<double[]> predicted=new ArrayList<>();
        List<double[]> observed=new ArrayList<>();
        for(Candidate c:selected) {
            if(c.simulated==null)
                throw new IllegalStateException("Reliability gate requires all prior replay labels");
            predicted.add(c.planned);
            observed.add(c.simulated);
        }
        if(ReplayReliabilityGate.trust(predicted,observed)) {
            FeedbackChoice choice=chooseFeedbackMode(pool,selected,"online-observed-hv");
            return new FeedbackChoice(choice.candidate,choice.nearestMapping,
                    choice.predictedMakespan,choice.predictedCost,
                    choice.predictedHvGain,"gated-observed");
        }
        for(Candidate c:pool) {
            if(!selected.contains(c))
                return new FeedbackChoice(c,"",c.planned[0],c.planned[1],0.,"gated-cover");
        }
        throw new IllegalStateException("No unreplayed cover fallback candidate");
    }

    /** Exact factor ablation: planned-front greedy, observed-front greedy, observed+residual. */
    private static FeedbackChoice chooseFeedbackMode(List<Candidate> pool,List<Candidate> selected,String mode) {
        if(!Arrays.asList("online-planned-hv","online-observed-hv","online-nearest-hv").contains(mode))
            throw new IllegalArgumentException("Unsupported online feedback ablation: "+mode);
        final boolean useObservedFront=!"online-planned-hv".equals(mode);
        final boolean useResidual="online-nearest-hv".equals(mode);
        if(pool.size()<selected.size()+1 || selected.size()<4)
            throw new IllegalStateException("Invalid online feedback candidate pool");
        for(Candidate c:selected)
            if(useObservedFront && c.simulated==null)
                throw new IllegalStateException("Online feedback requires completed earlier replay");
        double minM=Double.POSITIVE_INFINITY,maxM=0.,minC=Double.POSITIVE_INFINITY,maxC=0.;
        for(Candidate c:pool) {
            minM=Math.min(minM,c.planned[0]);maxM=Math.max(maxM,c.planned[0]);
            minC=Math.min(minC,c.planned[1]);maxC=Math.max(maxC,c.planned[1]);
        }
        double spanM=Math.max(1e-12,maxM-minM),spanC=Math.max(1e-12,maxC-minC);
        final double refM=1.5*maxM+1.,refC=1.5*maxC+1.;
        List<double[]> observed=new ArrayList<>();
        for(Candidate c:selected)observed.add(
                useObservedFront ? c.simulated : c.planned);
        final double observedHv=ParetoMetrics.hypervolume2D(ndPoints(observed),refM,refC);
        FeedbackChoice best=null;
        double bestSpacing=Double.NEGATIVE_INFINITY;
        for(Candidate c:pool) {
            if(selected.contains(c))continue;
            Candidate nearest=null;
            double nearestDistance=Double.POSITIVE_INFINITY;
            double candidateSpacing=Double.POSITIVE_INFINITY;
            for(Candidate seen:selected) {
                double dM=(c.planned[0]-seen.planned[0])/spanM;
                double dC=(c.planned[1]-seen.planned[1])/spanC;
                double distance=dM*dM+dC*dC;
                candidateSpacing=Math.min(candidateSpacing,distance);
                if(nearest==null || Double.compare(distance,nearestDistance)<0 ||
                        (Double.compare(distance,nearestDistance)==0 &&
                         canonicalMappingKey(seen).compareTo(canonicalMappingKey(nearest))<0)) {
                    nearest=seen;nearestDistance=distance;
                }
            }
            double shrink=1.;
            if(useResidual) {
                double ratio=nearest.simulated[0]/nearest.planned[0];
                shrink=1.+0.5*(ratio-1.);
                shrink=Math.min(1.1,Math.max(0.9,shrink));
            }
            double predictedM=c.planned[0]*shrink;
            double predictedC=c.planned[1];
            List<double[]> proposed=new ArrayList<>(observed);
            proposed.add(new double[]{predictedM,predictedC});
            double gain=Math.max(0.,ParetoMetrics.hypervolume2D(ndPoints(proposed),refM,refC)-observedHv);
            if(best==null || Double.compare(gain,best.predictedHvGain)>0 ||
                    (Double.compare(gain,best.predictedHvGain)==0 &&
                     (Double.compare(candidateSpacing,bestSpacing)>0 ||
                      (Double.compare(candidateSpacing,bestSpacing)==0 &&
                       canonicalMappingKey(c).compareTo(canonicalMappingKey(best.candidate))<0)))) {
                best=new FeedbackChoice(c,canonicalMappingKey(nearest),predictedM,predictedC,gain);
                bestSpacing=candidateSpacing;
            }
        }
        if(best==null)throw new IllegalStateException("No next online candidate");
        return best;
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

    /** Prospective extreme-first low-discrepancy scalar sweep, using PLANNED objectives only.
     *  The first two weights protect minimum-cost and minimum-makespan extremes.
     *  Exactly matches scripts/fla_replay_budget_audit.py:sweep() for K<=32.
     */
    private static List<Candidate> budgetedScalarSweep(List<Candidate> history,int budget) {
        Map<Map<Integer,Integer>,Candidate> unique=new LinkedHashMap<>();
        for(Candidate c:history)unique.putIfAbsent(c.assignment,c);
        List<Candidate> remaining=new ArrayList<>(unique.values());
        if(remaining.size()<budget)
            throw new IllegalStateException("Insufficient distinct visited schedules for scalar sweep K="+budget);
        double mMin=Double.POSITIVE_INFINITY,mMax=Double.NEGATIVE_INFINITY;
        double cMin=Double.POSITIVE_INFINITY,cMax=Double.NEGATIVE_INFINITY;
        for(Candidate c:remaining) {
            valid(c.planned);
            mMin=Math.min(mMin,c.planned[0]);mMax=Math.max(mMax,c.planned[0]);
            cMin=Math.min(cMin,c.planned[1]);cMax=Math.max(cMax,c.planned[1]);
        }
        final double loM=mMin,loC=cMin;
        final double spanM=Math.max(1e-12,mMax-mMin);
        final double spanC=Math.max(1e-12,cMax-cMin);
        Comparator<Candidate> order=Comparator
                .comparingDouble((Candidate c)->c.planned[0])
                .thenComparingDouble(c->c.planned[1])
                .thenComparing(FLAResearchExperiment::canonicalMappingKey);
        List<Candidate> picked=new ArrayList<>();
        int maxWeightSteps=Math.min(101,budget);
        for(int step=0;step<maxWeightSteps;step++) {
            double w;
            if(step==0)w=0.;
            else if(step==1)w=1.;
            else {
                int value=step-1;
                double power=0.5,radical=0.;
                while(value!=0) {
                    radical+=(value&1)*power;
                    power*=0.5;
                    value>>>=1;
                }
                w=radical;
            }
            Candidate best=null;
            double bestScalar=Double.POSITIVE_INFINITY;
            for(Candidate c:remaining) {
                double scalar=w*(c.planned[0]-loM)/spanM+
                        (1.-w)*(c.planned[1]-loC)/spanC;
                int cmp=Double.compare(scalar,bestScalar);
                if(best==null || cmp<0 || (cmp==0 && order.compare(c,best)<0)) {
                    best=c;
                    bestScalar=scalar;
                }
            }
            picked.add(best);
            remaining.remove(best);
        }
        if(picked.size()<budget) {
            // Only used for K>101; fill with the same Pareto-coverage order.
            for(Candidate c:budgetedPlannedCoverage(history,unique.size())) {
                if(!picked.contains(c))picked.add(c);
                if(picked.size()==budget)break;
            }
        }
        if(picked.size()!=budget)throw new IllegalStateException("Wrong scalar sweep K="+budget);
        System.out.println("PASS prospective planned-only scalar-sweep replay selection K="+budget
                +" uniqueHistory="+unique.size());
        return picked;
    }

    /**
     * Conservative, fixed-before-validation ablation of coverage: reserve up to
     * three DISTINCT planned objective points at each extreme, then use the
     * unchanged Pareto/max-min coverage order to fill exactly K genotype slots.
     * This consumes NO true simulator objectives and never changes the optimizer.
     * Tied objective points are skipped in the reserved band to avoid consuming
     * all K with costseed duplicates. No parameters are tuned per DAG.
     */
    private static List<Candidate> budgetedExtremeBand3(List<Candidate> history,int budget) {
        Map<Map<Integer,Integer>,Candidate> unique=new LinkedHashMap<>();
        for(Candidate c:history)unique.putIfAbsent(c.assignment,c);
        List<Candidate> all=new ArrayList<>(unique.values());
        if(budget<=0 || all.size()<budget)
            throw new IllegalStateException("Invalid extreme-band3 K="+budget
                    +", unique schedules="+all.size());
        for(Candidate c:all)valid(c.planned);
        Comparator<Candidate> byMakespan=Comparator
                .comparingDouble((Candidate c)->c.planned[0])
                .thenComparingDouble(c->c.planned[1])
                .thenComparing(FLAResearchExperiment::canonicalMappingKey);
        Comparator<Candidate> byCost=Comparator
                .comparingDouble((Candidate c)->c.planned[1])
                .thenComparingDouble(c->c.planned[0])
                .thenComparing(FLAResearchExperiment::canonicalMappingKey);
        List<Candidate> selected=new ArrayList<>();
        int quota=Math.min(3,Math.max(1,budget/4));
        List<Candidate> mOrder=new ArrayList<>(all);
        List<Candidate> cOrder=new ArrayList<>(all);
        mOrder.sort(byMakespan);
        cOrder.sort(byCost);
        for(List<Candidate> pool:Arrays.asList(mOrder,cOrder)) {
            int reserved=0;
            for(Candidate c:pool) {
                if(reserved>=quota || selected.size()>=budget)break;
                boolean repeatedPoint=false;
                for(Candidate previous:selected) {
                    if(c.planned[0]==previous.planned[0] && c.planned[1]==previous.planned[1]) {
                        repeatedPoint=true;break;
                    }
                }
                if(!repeatedPoint && !selected.contains(c)) {
                    selected.add(c);reserved++;
                }
            }
        }
        for(Candidate c:budgetedPlannedCoverage(history,Math.min(all.size(),budget+2*quota))) {
            if(selected.size()==budget)break;
            if(!selected.contains(c))selected.add(c);
        }
        if(selected.size()!=budget)
            throw new IllegalStateException("Could not fill extreme-band3 K="+budget);
        System.out.println("PASS prospective planned-only extreme-band3 replay selection K="+budget
                +" quota="+quota+" uniqueHistory="+all.size());
        return selected;
    }

    /** Identical planned-only pool across control and staged selectors. */
    private static List<Candidate> budgetedStagedReplay(Run run,String mode,int budget) {
        if(run.stagedReplayTasks==null||run.stagedReplayVms==null)
            throw new IllegalStateException("No captured optimizer DAG/VM context for staged study");
        List<Candidate> pool=budgetedPlannedCoverage(run.allVisited,STAGED_REPLAY_POOL);
        if(pool.size()!=STAGED_REPLAY_POOL)throw new IllegalStateException("Wrong staged candidate pool");
        List<Map<Integer,Integer>> genotype=new ArrayList<>();
        for(Candidate c:pool){
            genotype.add(c.assignment);
            run.stagedPoolIds.add(canonicalMappingKey(c));
        }
        StagedScheduleBatchEvaluator eval=new StagedScheduleBatchEvaluator(
                    run.stagedReplayTasks,run.stagedReplayVms);
        StagedScheduleBatchEvaluator.SelectionResult selected=
                "staged-greedy".equals(mode)
                    ?eval.select(genotype,STAGED_REPLAY_T,budget)
                    :"active-uniform-greedy".equals(mode)
                    ?eval.selectActiveUniform(genotype,STAGED_REPLAY_T,budget)
                    :eval.selectControl(genotype,mode,budget);
        run.stagedSelection=selected;
        int highExpected=("staged-greedy".equals(mode)||
                          "active-uniform-greedy".equals(mode))?STAGED_REPLAY_T:
                          "ready-greedy".equals(mode)?STAGED_REPLAY_POOL:0;
        if(selected.oldCalls!=STAGED_REPLAY_POOL||
           selected.readyCalls!=highExpected||selected.selected.length!=budget)
            throw new IllegalStateException("Exceeded stage replay evaluation budget");
        Set<Integer> unique=new HashSet<>();
        List<Candidate> out=new ArrayList<>();
        for(int idx:selected.selected) {
            if(idx<0||idx>=pool.size()||!unique.add(idx))
                throw new IllegalStateException("Repeated physical staged replay map");
            out.add(pool.get(idx));
        }
        System.out.printf(Locale.ROOT,
            "STAGED_SELECTION,%s,%s,POOL=%d,K=%d,OLD=%d,READY=%d,BATCH_NS=%d%n",
            run.algorithm,mode,pool.size(),budget,selected.oldCalls,
            selected.readyCalls,selected.totalNanos);
        return out;
    }

    /**
     * BEFORE-replay, opt-in diagnostic of real optimizer-visited physical maps.
     * NOT evolutionary fitness, NOT a simulator outcome, NOT a calibrated gate.
     * Never changes the K replays, search trajectory or primary HV.
     * Requires -Ddagfla.stagedReplayContext=true, -Ddagfla.budgetReplayK>0
     * and -Ddagfla.failClosedProbePairs=N; records up to N disjoint pairs.
     */
    private static void saveFailClosedProbe(Path prefix,List<Run> runs)
            throws IOException {
        int pairs=Integer.getInteger("dagfla.failClosedProbePairs",0);
        if(pairs<1||pairs>64||BUDGET_REPLAY_K<=0||
           !Boolean.getBoolean("dagfla.stagedReplayContext"))
            throw new IllegalArgumentException("Probe requires N in 1..64, K replay and captured Task/VM context");
        int readyBudget=Integer.getInteger("dagfla.failClosedProbeReadyBudget",2*pairs);
        if(readyBudget<0||readyBudget>2*pairs)
            throw new IllegalArgumentException("Probe READY quota must be 0..2*N");
        try(BufferedWriter w=Files.newBufferedWriter(
                Paths.get(prefix+"_fail_closed_probe.csv"),StandardCharsets.UTF_8)) {
            w.write("algorithm,pair,first_assignment,second_assignment,decision,reason,"
                    +"old_first_m,old_first_c,old_second_m,old_second_c,"
                    +"ready_first_m,ready_first_c,ready_second_m,ready_second_c,"
                    +"old_calls,ready_calls,old_cache_hits,ready_cache_hits,ready_budget\n");
            for(Run run:runs) {
                if(run.stagedReplayTasks==null||run.stagedReplayVms==null)
                    throw new IllegalStateException("No original workflow decoder context: "+run.algorithm);
                WorkflowFailClosedProbe probe=new WorkflowFailClosedProbe(
                        run.stagedReplayTasks,run.stagedReplayVms,readyBudget);
                int count=Math.min(pairs,run.allVisited.size()/2);
                if(count<=0)throw new IllegalStateException("No distinct probe pairs: "+run.algorithm);
                for(int i=0;i<count;i++){
                    Candidate a=run.allVisited.get(2*i),b=run.allVisited.get(2*i+1);
                    WorkflowFailClosedProbe.Result result=probe.assess(a.assignment,b.assignment);
                    double[] ra=result.decision.readyFirst,rb=result.decision.readySecond;
                    String reason=result.decision.reason.replace(',',';').replace('\n',' ');
                    w.write(String.format(Locale.ROOT,
                        "%s,%d,%s,%s,%s,%s,%.17g,%.17g,%.17g,%.17g,%s,%s,%s,%s,%d,%d,%d,%d,%d%n",
                        run.algorithm,i+1,result.firstId,result.secondId,result.decision.kind,
                        reason,result.oldFirst[0],result.oldFirst[1],
                        result.oldSecond[0],result.oldSecond[1],
                        ra==null?"":String.format(Locale.ROOT,"%.17g",ra[0]),
                        ra==null?"":String.format(Locale.ROOT,"%.17g",ra[1]),
                        rb==null?"":String.format(Locale.ROOT,"%.17g",rb[0]),
                        rb==null?"":String.format(Locale.ROOT,"%.17g",rb[1]),
                        probe.oldCalls(),probe.readyCalls(),probe.oldCacheHits(),
                        probe.readyCacheHits(),probe.readyBudget()));
                    if(result.decision.kind==org.workflowsim.planning.FailClosedFidelityGate.Kind.CONDITIONAL_FIRST_DOMINATES ||
                       result.decision.kind==org.workflowsim.planning.FailClosedFidelityGate.Kind.CONDITIONAL_SECOND_DOMINATES)
                        throw new IllegalStateException("Uncalibrated probe certified a dominance");
                }
                if(probe.oldCalls()>2*count||probe.readyCalls()>readyBudget)
                    throw new IllegalStateException("Diagnostic violated decoder call budgets");
            }
        }
    }

    private static void saveEvolutionFidelity(Path prefix,List<Run> runs)
            throws IOException {
        try(BufferedWriter w=Files.newBufferedWriter(
                Paths.get(prefix+"_evolution_fidelity.csv"),StandardCharsets.UTF_8)) {
            w.write("algorithm,mode,visits,cheap_calls,ready_calls,cache_hits,distinct,"
                  +"ready_budget,near_gate_skips,cheap_ns,ready_ns\n");
            for(Run run:runs) {
                BudgetedEvolutionFidelityObjective.Snapshot x=run.evolutionFidelity;
                if(x==null||x.visits!=run.evals||
                   x.distinct+x.cacheHits!=x.visits||
                   x.readyCalls>x.maxReadyCalls)
                    throw new IllegalStateException("Invalid evolutionary fidelity trace "+run.algorithm);
                w.write(String.format(Locale.ROOT,
                    "%s,%s,%d,%d,%d,%d,%d,%d,%d,%d,%d%n",
                    run.algorithm,x.mode,x.visits,x.cheapCalls,x.readyCalls,
                    x.cacheHits,x.distinct,x.maxReadyCalls,x.nearGateSkips,
                    x.cheapNanos,x.readyNanos));
            }
        }
    }

    private static void saveStagedReplaySelection(Path prefix,List<Run> runs)
            throws IOException {
        try(BufferedWriter w=Files.newBufferedWriter(
                Paths.get(prefix+"_staged_selection.csv"),StandardCharsets.UTF_8)) {
            w.write("algorithm,selection_mode,pool_n,old_calls,ready_calls,"
                  +"old_ns,ready_ns,batch_total_ns,screened_indices,selected_indices,"
                  +"planned_hv,canonical_pool_fingerprint\n");
            for(Run run:runs) {
                StagedScheduleBatchEvaluator.SelectionResult r=run.stagedSelection;
                if(r==null||run.stagedPoolIds.size()!=STAGED_REPLAY_POOL)
                    throw new IllegalStateException("Uncaptured staged selector evidence");
                StringBuilder screen=new StringBuilder(),selected=new StringBuilder();
                for(int x:r.screened) {
                    if(screen.length()>0)screen.append('|');screen.append(x+1);
                }
                for(int x:r.selected) {
                    if(selected.length()>0)selected.append('|');selected.append(x+1);
                }
                MessageDigest digest;
                try{digest=MessageDigest.getInstance("SHA-256");}
                catch(Exception e){throw new IllegalStateException(e);}
                for(String key:run.stagedPoolIds)
                    digest.update((key+"\n").getBytes(StandardCharsets.UTF_8));
                StringBuilder hex=new StringBuilder();
                for(byte v:digest.digest())hex.append(String.format(Locale.ROOT,"%02x",v&0xff));
                w.write(String.format(Locale.ROOT,
                  "%s,%s,%d,%d,%d,%d,%d,%d,%s,%s,%.17g,%s%n",
                  run.algorithm,BUDGET_REPLAY_POLICY,STAGED_REPLAY_POOL,r.oldCalls,
                  r.readyCalls,r.oldNanos,r.readyNanos,r.totalNanos,
                  screen,selected,r.predictedHypervolume,hex.toString()));
            }
        }
    }

    /** Fixed K12+4 dominated-candidate rescue; no real simulator labels. */
    private static List<Candidate> budgetedBoundaryFour(List<Candidate> history,
            int budget,long seed,String algorithm,boolean stratifiedRandom) {
        if(budget!=16)throw new IllegalArgumentException("Frozen K16 required");
        Map<Map<Integer,Integer>,Candidate> unique=new LinkedHashMap<>();
        for(Candidate c:history)unique.putIfAbsent(c.assignment,c);
        List<Candidate> all=new ArrayList<>(unique.values());
        List<Candidate> baseline=budgetedPlannedCoverage(history,12);
        int[] anchors=new int[12];
        for(int i=0;i<12;i++){
            anchors[i]=all.indexOf(baseline.get(i));
            if(anchors[i]<0)throw new IllegalStateException("Lost baseline identity");
        }
        double[][] scores=new double[all.size()][];
        String[] ids=new String[all.size()];
        for(int i=0;i<all.size();i++) {
            scores[i]=all.get(i).planned;
            ids[i]=canonicalMappingKey(all.get(i));
        }
        long salt=seed^(((long)algorithm.hashCode())*0x9E3779B97F4A7C15L)
                ^0x41B0F9A4D3102A67L;
        BoundaryFourReplaySelector.Result result=
            BoundaryFourReplaySelector.select(scores,ids,anchors,
                stratifiedRandom?BoundaryFourReplaySelector.Policy.STRATIFIED_RANDOM
                                :BoundaryFourReplaySelector.Policy.BOUNDARY,
                new Random(salt));
        List<Candidate> resultCandidates=new ArrayList<>();
        for(int index:result.indices)resultCandidates.add(all.get(index));
        if(!resultCandidates.subList(0,12).equals(baseline))
            throw new IllegalStateException("K12 control no longer identical");
        System.out.printf(Locale.ROOT,
            "BOUNDARY_FOUR policy=%s eligible=%d strata=%s K=16%n",
            stratifiedRandom?"dominated-random-four":"boundary-four",
            result.dominatedEligible,Arrays.toString(result.stratumSizes));
        return resultCandidates;
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
            w.write("workflow,algorithm,seed,population,generations,budget_cap,evaluations,source_archive,distinct_planned_nondominated,replayed,sim_nondominated,captured_evaluations,distinct_observed,sim_hv,planned_hv,sim_ref_m,sim_ref_c,plan_ref_m,plan_ref_c,search_ms,actual_generations,selection_ms,replay_ms,search_selection_replay_ms\n");
            for(Run r:runs) {
                w.write(String.format(Locale.ROOT,"%s,%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%.10f,%.10f,%.10f,%.10f,%.10f,%.10f,%d,%s,%.6f,%.6f,%.6f%n",
                    wf,r.algorithm,seed,pop,gens,cap,r.evals,r.sourceFrontSize,r.plannedNdCount,
                    r.candidates.size(),r.simulatorFront.size(),r.capturedEvaluations,
                    r.distinctObservedAssignments,r.simHv,r.planHv,
                    simRef[0],simRef[1],planRef[0],planRef[1],r.searchMs,r.actualGenerations,
                    r.policySelectionNanos/1e6,r.simulatorReplayNanos/1e6,
                    r.searchMs+(r.policySelectionNanos+r.simulatorReplayNanos)/1e6));
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
