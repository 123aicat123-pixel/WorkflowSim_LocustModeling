package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import org.cloudbus.cloudsim.Consts;
import org.workflowsim.CondorVM;
import org.workflowsim.FileItem;
import org.workflowsim.Task;
import org.workflowsim.utils.Parameters;

/**
 * DAG-Pareto-FLA (research candidate v0.1): MULTIOBJECTIVE DISCRETE ADAPTATION,
 * NOT an equation-faithful reimplementation of the continuous original FLA.
 *
 * Retains FLA's two groups and DO/EO/SSO time windows. Uses proposed VM-gene
 * update rules, a DAG upward-rank importance vector, and a nondominated archive.
 * All methods of this class are intentionally separate from LIWSA's operators.
 * This planner is single-threaded (so is the reusable decoder).
 */
public final class DAGParetoFLAPlanningAlgorithm extends BasePlanningAlgorithm {
    // WorkflowPlanner instantiates with a no-arg constructor. Set BEFORE startSimulation.
    public static int CONFIG_POPULATION_SIZE = 30;
    public static int CONFIG_GENERATION_COUNT = 100;
    public static Long CONFIG_RANDOM_SEED = null;
    public static int CONFIG_ARCHIVE_CAPACITY = 100;
    public static boolean CONFIG_ENFORCE_PES = false;
    public static List<Map<Integer, Integer>> CONFIG_SEED_ASSIGNMENTS = null;

    // Ablations (no other planner reads these).
    public static boolean CONFIG_DAG_GUIDANCE = true;
    public static boolean CONFIG_CROSS_GROUP_DO = true;
    public static boolean CONFIG_ARCHIVE_SSO = true;
    public static boolean CONFIG_ADAPTIVE_MUTATION = true;
    public static boolean CONFIG_ADAPTIVE_PREFERENCE = true;
    public static boolean CONFIG_GLOBAL_SURVIVOR_SELECTION = false;
    public static boolean CONFIG_RANDOM_IMMIGRANTS = false;
    // Experimental v3 operators: only affect the DAG-Pareto-FLA planner.
    public static boolean CONFIG_RESOURCE_AWARE_MUTATION = false;
    public static boolean CONFIG_ARCHIVE_RECOMBINATION = false;
    /** v4 alternative: strict non-dominated rank + crowding environmental selection. */
    public static boolean CONFIG_PARETO_CROWDING_SELECTION = false;
    /** v5 ablations; disabled unless the experiment selects them. */
    public static boolean CONFIG_ARCHIVE_DAG_BLOCK = false;
    public static boolean CONFIG_ARCHIVE_PREFERENCE_DONOR = false;
    /** v6: restore novelty BEFORE evaluating a proposed FLA offspring. */
    public static boolean CONFIG_NOVELTY_REPAIR = false;
    public static boolean CONFIG_NOVELTY_GLOBAL_HISTORY = false;
    public static boolean CONFIG_NOVELTY_STRONG_REPAIR = false;
    /** V7 controlled exploration: low-rental-price initialization and low-cost archive guidance. */
    public static boolean CONFIG_COST_SEEDING = false;
    public static boolean CONFIG_COST_EXTREME_GUIDANCE = false;
    /** v8: preserve genuine objective extremes from the evaluated parent/child pool. */
    public static boolean CONFIG_RESERVE_COST_EXTREME = false;
    public static boolean CONFIG_RESERVE_MAKESPAN_EXTREME = false;
    /** v9: DAG-edge relocation, 0=off, 1=co-location, 2=separation, 3=two-group-directed. */
    public static int CONFIG_EDGE_RELOCATION_MODE = 0;
    /** v10 makespan-critical single-gene relocation; 0=off,1=fast,2=cost-guarded. */
    public static int CONFIG_CRITICAL_RELOCATION_MODE = 0;
    /** Post-search, planning-only directional calibration; disabled by default. */
    public static boolean CONFIG_CRITICAL_LOCAL_AUDIT = false;

    public static volatile LastRunMetrics lastRun = null;

    private static final double EPS = 1e-12;
    private static final double MUT_MIN = 0.02;
    private static final double MUT_MAX = 0.20;
    private static final double DIVERSITY_REWARD = 0.15;
    private static final double LEADER_TEMPERATURE = 0.20;
    private static final double LEADER_CROWDING_REWARD = 0.50;

    public static final class LastRunMetrics {
        public double chosenMakespan;
        public double chosenCost;
        public int paretoFrontSize;
        public List<double[]> paretoFrontPoints;
        public List<Map<Integer, Integer>> paretoFrontAssignments;
        public long searchWallClockMillis;
        public int populationSizeUsed;
        public int generationCountUsed;
        public long objectiveEvaluations;
        public int diffusionIterations;
        public int equilibriumIterations;
        public int steadyStateIterations;
        public int group1Size;
        public int group2Size;
        public int edgeRelocationChanges;
        public int criticalRelocationChanges;
        public int criticalProxySamples;
        public double criticalProxyPearson;
        public double criticalProxyMedianAbsolutePctError;
        public double finalAlpha1;
        public double finalDiversity;
        public List<double[]> searchTrace; // {iteration, archiveSize, bestM, bestCost, diversity}
    }

    private static final class Solution {
        final int[] genes;
        final double makespan;
        final double cost;
        Solution(int[] x, double[] mc) {
            genes = x.clone();
            makespan = mc[0];
            cost = mc[1];
        }
    }
    private static final class Bounds {
        double minM = Double.POSITIVE_INFINITY, maxM = Double.NEGATIVE_INFINITY;
        double minC = Double.POSITIVE_INFINITY, maxC = Double.NEGATIVE_INFINITY;
        Bounds(List<Solution> xs) {
            for (Solution s : xs) {
                minM = Math.min(minM, s.makespan); maxM = Math.max(maxM, s.makespan);
                minC = Math.min(minC, s.cost); maxC = Math.max(maxC, s.cost);
            }
        }
        double m(double v) { return (v - minM) / Math.max(EPS, maxM - minM); }
        double c(double v) { return (v - minC) / Math.max(EPS, maxC - minC); }
    }

    private final int populationSize;
    private final int generations;
    private final int archiveCapacity;
    private final Long seed;
    private final boolean enforcePes;
    private final boolean useDag, useCross, useArchiveSso, useAdaptiveMutation, useAdaptivePreference;
    private final boolean useGlobalSelection, useImmigrants;
    private final boolean useResourceAwareMutation, useArchiveRecombination, useParetoCrowdingSelection;
    private final boolean useArchiveDagBlock, usePreferenceDonor;
    private final boolean useNoveltyRepair, useGlobalHistory, useStrongRepair;
    private final boolean useCostSeeding, useCostExtremeGuidance;
    private final boolean reserveCostExtreme, reserveMakespanExtreme;
    private final int edgeRelocationMode, criticalRelocationMode;
    private final List<Map<Integer,Integer>> seedMaps;
    private final List<Solution> archive = new ArrayList<>();
    private final List<double[]> searchTrace = new ArrayList<>();
    private final List<double[]> criticalProxyPairs = new ArrayList<>();

    private Random random;
    private FLAScheduleEvaluator evaluator;
    private List<Task> taskOrder;
    private List<CondorVM> vmList;
    private int[][] allowed;
    private double[] importance;
    private double[][] optimisticServiceSeconds;
    private int[] dagEdgeParent, dagEdgeChild;
    private double[] dagEdgeWeight;
    private int[][] criticalParentIndices;
    private double[][] criticalParentTransferMb;
    private int n, group1Size;
    private List<Solution> group1, group2;
    private double alpha1 = 0.85;
    private int doCount, eoCount, ssoCount, edgeChangeCount, criticalChangeCount;

    public DAGParetoFLAPlanningAlgorithm() {
        populationSize = CONFIG_POPULATION_SIZE;
        generations = CONFIG_GENERATION_COUNT;
        archiveCapacity = CONFIG_ARCHIVE_CAPACITY;
        seed = CONFIG_RANDOM_SEED;
        enforcePes = CONFIG_ENFORCE_PES;
        useDag = CONFIG_DAG_GUIDANCE;
        useCross = CONFIG_CROSS_GROUP_DO;
        useArchiveSso = CONFIG_ARCHIVE_SSO;
        useAdaptiveMutation = CONFIG_ADAPTIVE_MUTATION;
        useAdaptivePreference = CONFIG_ADAPTIVE_PREFERENCE;
        useGlobalSelection = CONFIG_GLOBAL_SURVIVOR_SELECTION;
        useImmigrants = CONFIG_RANDOM_IMMIGRANTS;
        useResourceAwareMutation = CONFIG_RESOURCE_AWARE_MUTATION;
        useArchiveRecombination = CONFIG_ARCHIVE_RECOMBINATION;
        useParetoCrowdingSelection = CONFIG_PARETO_CROWDING_SELECTION;
        useArchiveDagBlock = CONFIG_ARCHIVE_DAG_BLOCK;
        usePreferenceDonor = CONFIG_ARCHIVE_PREFERENCE_DONOR;
        useNoveltyRepair = CONFIG_NOVELTY_REPAIR;
        useGlobalHistory = CONFIG_NOVELTY_GLOBAL_HISTORY;
        useStrongRepair = CONFIG_NOVELTY_STRONG_REPAIR;
        useCostSeeding = CONFIG_COST_SEEDING;
        useCostExtremeGuidance = CONFIG_COST_EXTREME_GUIDANCE;
        reserveCostExtreme = CONFIG_RESERVE_COST_EXTREME;
        reserveMakespanExtreme = CONFIG_RESERVE_MAKESPAN_EXTREME;
        edgeRelocationMode = CONFIG_EDGE_RELOCATION_MODE;
        criticalRelocationMode = CONFIG_CRITICAL_RELOCATION_MODE;
        seedMaps = CONFIG_SEED_ASSIGNMENTS == null ? Collections.emptyList()
                : new ArrayList<>(CONFIG_SEED_ASSIGNMENTS);
    }

    @Override
    public void run() {
        lastRun = null;
        if (populationSize < 4 || generations < 1 || archiveCapacity < 2) {
            throw new IllegalArgumentException("Population >=4, generations >=1, archive capacity >=2 required");
        }
        long start = System.nanoTime();
        vmList = new ArrayList<>();
        for (Object obj : getVmList()) { vmList.add((CondorVM) obj); }
        evaluator = new FLAScheduleEvaluator(getTaskList(), vmList,
                FLAScheduleEvaluator.InsertionMode.VERIFIED_EARLIEST_INSERTION, enforcePes);
        taskOrder = evaluator.getTaskOrder();
        n = taskOrder.size();
        allowed = new int[n][];
        for (int k = 0; k < n; k++) {
            if (enforcePes) {
                allowed[k] = evaluator.getFeasibleVmIndices(k);
            } else {
                allowed[k] = new int[vmList.size()];
                for (int v = 0; v < vmList.size(); v++) { allowed[k][v] = v; }
            }
        }
        importance = calculateUpwardRankWeights();
        if (useResourceAwareMutation || useCostSeeding || edgeRelocationMode != 0 || criticalRelocationMode != 0) prepareResourceHeuristic();
        if (criticalRelocationMode != 0) prepareCriticalProxy();
        if (edgeRelocationMode != 0) prepareDagEdgeRelocation();
        if (!useDag) { Arrays.fill(importance, 1.0); }
        random = seed == null ? new Random() : new Random(seed);
        group1Size = (populationSize + 1) / 2;
        List<Solution> initial = initializePopulation();
        group1 = new ArrayList<>(initial.subList(0, group1Size));
        group2 = new ArrayList<>(initial.subList(group1Size, populationSize));
        archive.clear(); searchTrace.clear(); criticalProxyPairs.clear();
        doCount = 0; eoCount = 0; ssoCount = 0; edgeChangeCount = 0; criticalChangeCount = 0; alpha1 = 0.85;
        for (Solution s : initial) { archiveConsider(s); }
        final Set<String> globalVisited = useNoveltyRepair && useGlobalHistory
                ? new HashSet<String>() : null;
        if (globalVisited != null) {
            for (Solution s : initial) globalVisited.add(Arrays.toString(s.genes));
        }
        saveTrace(0);

        for (int t = 1; t <= generations; t++) {
            double tf = Math.sqrt(Math.sinh((double)t / generations));
            List<Solution> parents = population();
            int[] rank = nondominatedRank(parents);
            int maxRank = 0;
            for (int r : rank) { maxRank = Math.max(maxRank, r); }
            final Bounds snapshot = new Bounds(parents);
            Solution leader1 = chooseLeader(group1, alpha1, snapshot);
            Solution leader2 = chooseLeader(group2, 1.0 - alpha1, snapshot);
            double diversity = hammingDiversity(parents);
            double mutationProbability = useAdaptiveMutation
                    ? MUT_MIN + (MUT_MAX - MUT_MIN) * (1.0 - diversity)
                    : MUT_MIN;
            double dof = 0;
            int phase;
            if (tf < 0.9) {
                doCount++; phase = 0;
                // FLA MATLAB 1.0 diffusion factor; capped for a probability mapping.
                dof = clamp(Math.pow(Math.exp(-(2.0 * tf - random.nextDouble())), 2.0), 0, 1);
            } else if (tf <= 1.0) {
                eoCount++; phase = 1;
            } else {
                ssoCount++; phase = 2;
            }
            List<Solution> children1 = new ArrayList<>();
            List<Solution> children2 = new ArrayList<>();
            final Set<String> generationVisited;
            if (useNoveltyRepair) {
                generationVisited = useGlobalHistory ? globalVisited : new HashSet<String>();
                if (!useGlobalHistory) {
                    for (Solution p : parents) generationVisited.add(Arrays.toString(p.genes));
                }
            } else {
                generationVisited = null;
            }
            for (int i = 0; i < populationSize; i++) {
                Solution current = parents.get(i);
                boolean isG1 = i < group1Size;
                Solution ref;
                if (phase == 0) {
                    ref = useCross ? (isG1 ? leader2 : leader1)
                            : (isG1 ? leader1 : leader2);
                } else if (phase == 1) {
                    ref = isG1 ? leader1 : leader2;
                } else {
                    ref = useArchiveSso && !archive.isEmpty()
                            ? chooseArchiveLeader(isG1 ? alpha1 : 1.0 - alpha1)
                            : (isG1 ? leader1 : leader2);
                }
                if (useCostExtremeGuidance && !isG1 && !archive.isEmpty()
                        && random.nextDouble() < 0.35) {
                    // Controlled cost-tail pressure: sampling this elite does not
                    // itself evaluate a solution or change the search budget.
                    ref = minimumCostArchive();
                }
                int[] genes = current.genes.clone();
                if(useImmigrants && random.nextDouble()<0.10) {
                    // Budget unchanged: exactly one evaluation per child.
                    for(int k=0;k<n;k++) genes[k]=allowed[k][random.nextInt(allowed[k].length)];
                } else {
                    if (phase == 0) {
                        diffusionGenes(genes, ref.genes, dof);
                    } else {
                        double pressure = Math.exp(-(double) rank[i] / Math.max(1, maxRank));
                        guidedGenes(genes, ref.genes, pressure);
                    }
                    if (useArchiveRecombination && !archive.isEmpty()
                            && random.nextDouble() < 0.25) {
                        archiveRecombine(genes, isG1);
                    }
                    if (useResourceAwareMutation && random.nextDouble() < 0.45) {
                        resourceAwareMutation(genes, isG1);
                    } else {
                        mutate(genes, mutationProbability);
                    }
                    if (edgeRelocationMode != 0 && random.nextDouble() < 0.45) {
                        int[] beforeRelocation = genes.clone();
                        edgeRelocation(genes, isG1);
                        if (!Arrays.equals(beforeRelocation, genes)) edgeChangeCount++;
                    }
                    if (criticalRelocationMode != 0 && isG1 && random.nextDouble() < 0.45) {
                        int[] beforeCritical = genes.clone();
                        criticalRelocate(genes);
                        if (!Arrays.equals(beforeCritical, genes)) criticalChangeCount++;
                    }
                }
                if (useNoveltyRepair) repairNoveltyBeforeEvaluation(genes,generationVisited);
                // Passive fidelity audit: proxy uses NO target fitness calls;
                // compare to the ONE normal stage-in-aware evaluated result.
                final double predictedCriticalMakespan = criticalRelocationMode != 0
                        ? approximateMakespan(genes,null) : Double.NaN;
                Solution child = new Solution(genes, evaluator.evaluate(genes));
                if(criticalRelocationMode != 0)
                    criticalProxyPairs.add(new double[]{predictedCriticalMakespan, child.makespan});
                archiveConsider(child); // ALL visited children, even if not selected
                (isG1 ? children1 : children2).add(child);
            }
            // Global fronts are computed from all parents/children, but each group
            // retains its own size and objective preference.
            List<Solution> union1 = new ArrayList<>(group1);
            union1.addAll(children1);
            List<Solution> union2 = new ArrayList<>(group2);
            union2.addAll(children2);
            List<Solution> union = new ArrayList<>(union1);
            union.addAll(union2);
            int[] globalRank = nondominatedRank(union);
            double[] globalCrowd = crowdingDistance(union, globalRank);
            Bounds b = new Bounds(union);
            if(useGlobalSelection) {
                // Experimental NSGA-style global Pareto elitism before the next
                // two-group FLA phase; NOT an original MATLAB FLA equation.
                List<Solution> survivors=useParetoCrowdingSelection
                        ? selectGlobalCrowding(union,populationSize,globalRank,globalCrowd)
                        : selectGroup(union,0,populationSize,globalRank,globalCrowd,b,0.5);
                if (reserveCostExtreme || reserveMakespanExtreme)
                    reserveObjectiveExtremes(union,survivors,b);
                survivors.sort(Comparator.comparingDouble((Solution x)->preference(x,alpha1,b))
                        .thenComparingDouble(x->x.makespan)
                        .thenComparingDouble(x->x.cost));
                group1=new ArrayList<>(survivors.subList(0,group1Size));
                group2=new ArrayList<>(survivors.subList(group1Size,populationSize));
            } else {
                group1 = selectGroup(union1, 0, group1Size, globalRank, globalCrowd, b, alpha1);
                group2 = selectGroup(union2, union1.size(), populationSize-group1Size,
                        globalRank, globalCrowd, b, 1.0-alpha1);
            }
            if (useAdaptivePreference && t % 10 == 0 && !archive.isEmpty()) {
                adaptPreference();
            }
            saveTrace(t);
        }
        if (archive.isEmpty()) { throw new IllegalStateException("Empty Pareto archive"); }
        Solution chosen = archive.get(0);
        for (Solution s : archive) {
            if (s.makespan < chosen.makespan
                    || s.makespan == chosen.makespan && s.cost < chosen.cost) chosen = s;
        }
        evaluator.commitAssignment(chosen.genes);
        LastRunMetrics m = new LastRunMetrics();
        m.chosenMakespan = chosen.makespan;
        m.chosenCost = chosen.cost;
        m.paretoFrontSize = archive.size();
        m.paretoFrontPoints = new ArrayList<>();
        m.paretoFrontAssignments = new ArrayList<>();
        List<Solution> sorted = new ArrayList<>(archive);
        sorted.sort(Comparator.comparingDouble((Solution s)->s.makespan).thenComparingDouble(s->s.cost));
        for (Solution s : sorted) {
            m.paretoFrontPoints.add(new double[]{s.makespan,s.cost});
            m.paretoFrontAssignments.add(evaluator.toAssignment(s.genes));
        }
        m.populationSizeUsed = populationSize;
        m.generationCountUsed = generations;
        m.objectiveEvaluations = evaluator.getObjectiveEvaluations();
        m.searchWallClockMillis = (System.nanoTime() - start) / 1_000_000L;
        m.diffusionIterations = doCount;
        m.equilibriumIterations = eoCount;
        m.steadyStateIterations = ssoCount;
        m.group1Size = group1.size();
        m.group2Size = group2.size();
        m.edgeRelocationChanges = edgeChangeCount;
        m.criticalRelocationChanges = criticalChangeCount;
        if (!criticalProxyPairs.isEmpty()) {
            double sx=0,sy=0,sxx=0,syy=0,sxy=0;
            double[] errors=new double[criticalProxyPairs.size()];
            for(int i=0;i<criticalProxyPairs.size();i++) {
                double[] z=criticalProxyPairs.get(i);
                double x=z[0],y=z[1];
                sx+=x;sy+=y;sxx+=x*x;syy+=y*y;sxy+=x*y;
                errors[i]=100.0*Math.abs(x-y)/Math.max(EPS,y);
            }
            Arrays.sort(errors);
            int count=criticalProxyPairs.size();
            m.criticalProxySamples=count;
            m.criticalProxyMedianAbsolutePctError=
                    count%2==1 ? errors[count/2] : 0.5*(errors[count/2-1]+errors[count/2]);
            double corrDenom=(count*sxx-sx*sx)*(count*syy-sy*sy);
            m.criticalProxyPearson=corrDenom>EPS
                    ? (count*sxy-sx*sy)/Math.sqrt(corrDenom) : Double.NaN;
        }
        m.finalAlpha1 = alpha1;
        m.finalDiversity = hammingDiversity(population());
        m.searchTrace = new ArrayList<>();
        for (double[] a : searchTrace) { m.searchTrace.add(a.clone()); }
        lastRun = m;
        if(CONFIG_CRITICAL_LOCAL_AUDIT && criticalRelocationMode!=0)
            runCriticalLocalAudit();
        System.out.printf("DAG-Pareto-FLA: front=%d, chosenM=%.6f, chosenC=%.6f, eval=%d, DO=%d EO=%d SSO=%d edgeRelocationChanges=%d criticalRelocationChanges=%d%n",
                m.paretoFrontSize,m.chosenMakespan,m.chosenCost,m.objectiveEvaluations,
                m.diffusionIterations,m.equilibriumIterations,m.steadyStateIterations,m.edgeRelocationChanges,m.criticalRelocationChanges);
        if(m.criticalProxySamples>0)
            System.out.printf(java.util.Locale.ROOT,
                    "FLA_CRITICAL_PROXY_AUDIT samples=%d pearson=%.9f medianAbsolutePctError=%.9f%%%n",
                    m.criticalProxySamples,m.criticalProxyPearson,m.criticalProxyMedianAbsolutePctError);
    }

    private List<Solution> population() {
        List<Solution> all = new ArrayList<>(populationSize);
        all.addAll(group1); all.addAll(group2);
        return all;
    }

    private List<Solution> initializePopulation() {
        List<Solution> list = new ArrayList<>(populationSize);
        for (Map<Integer,Integer> map : seedMaps) {
            if (list.size() >= populationSize) break;
            try {
                int[] g = evaluator.fromAssignment(map);
                list.add(new Solution(g,evaluator.evaluate(g)));
            } catch (IllegalArgumentException ex) {
                System.err.println("DAG-Pareto-FLA skipped invalid warm-start: "+ex.getMessage());
            }
        }
        if (useCostSeeding && list.size() < populationSize) {
            // Replace random initialization, not add fitness calls: task-local
            // optimistic service time multiplied by the actual VM unit price.
            int[] priceEfficient = new int[n];
            for(int k=0;k<n;k++){
                int best=allowed[k][0];
                double lowest=Double.POSITIVE_INFINITY;
                for(int v:allowed[k]){
                    double score=optimisticServiceSeconds[k][v]*vmList.get(v).getCost();
                    if(score<lowest){lowest=score;best=v;}
                }
                priceEfficient[k]=best;
            }
            list.add(new Solution(priceEfficient,evaluator.evaluate(priceEfficient)));
        }
        if (useCostSeeding && list.size() < populationSize) {
            // Alternative very low-cost-rate policy: a VM may be slower and
            // thus costlier overall; this is a proposal, not a claimed optimum.
            int[] lowRate=new int[n];
            for(int k=0;k<n;k++){
                int best=allowed[k][0];
                for(int v:allowed[k])if(vmList.get(v).getCost()<vmList.get(best).getCost())best=v;
                lowRate[k]=best;
            }
            list.add(new Solution(lowRate,evaluator.evaluate(lowRate)));
        }
        while(list.size() < populationSize) {
            int[] g = new int[n];
            for(int k=0;k<n;k++) {
                g[k] = allowed[k][random.nextInt(allowed[k].length)];
            }
            list.add(new Solution(g,evaluator.evaluate(g)));
        }
        return list;
    }

    /** HEFT-style upward ranks; resource-aware but fixed for the run. */
    private double[] calculateUpwardRankWeights() {
        Map<Task,Integer> id = new IdentityHashMap<>();
        for (int k=0;k<n;k++) id.put(taskOrder.get(k),k);
        double[] rank = new double[n];
        double bandwidth = 0;
        for (CondorVM vm : vmList) bandwidth += vm.getBw();
        bandwidth /= vmList.size();
        for (int k=n-1;k>=0;k--) {
            Task task=taskOrder.get(k);
            double duration = 0;
            for (int vm : allowed[k]) duration += task.getCloudletTotalLength()/vmList.get(vm).getMips();
            duration /= allowed[k].length;
            double latest=0;
            for (Task child : task.getChildList()) {
                Integer index = id.get(child);
                if (index == null || index <= k) {
                    throw new IllegalArgumentException("Invalid task DAG or external child");
                }
                double comm = 0;
                for (FileItem f : task.getFileList()) {
                    if (f.getType()!=Parameters.FileType.OUTPUT) continue;
                    for(FileItem input:child.getFileList()) {
                        if (input.getType()==Parameters.FileType.INPUT && input.getName().equals(f.getName())) {
                            comm += input.getSize(); break;
                        }
                    }
                }
                comm = (comm / Consts.MILLION) * 8 / bandwidth;
                latest=Math.max(latest,comm+rank[index]);
            }
            rank[k]=duration+latest;
        }
        double max=0;
        for (double r : rank) max=Math.max(max,r);
        for (int k=0;k<n;k++) rank[k]=max>0?rank[k]/max:1;
        return rank;
    }

    private Solution chooseLeader(List<Solution> group,double a, Bounds bounds) {
        List<Solution> distinct = new ArrayList<>();
        for(Solution s:group) {
            boolean found=false;
            for (Solution d:distinct) {
                if(Arrays.equals(s.genes,d.genes)) {found=true;break;}
            }
            if(!found) distinct.add(s);
        }
        distinct.sort(Comparator.comparingDouble((Solution s)->preference(s,a,bounds))
                .thenComparingDouble(s->s.makespan).thenComparingDouble(s->s.cost));
        int k=Math.min(2,distinct.size());
        if(k==1)return distinct.get(0);
        // Stochastic top-2 selection avoids deterministic leader collapse.
        double w1=1.0/(preference(distinct.get(0),a,bounds)+0.1);
        double w2=1.0/(preference(distinct.get(1),a,bounds)+0.1);
        return random.nextDouble()*(w1+w2)<w1?distinct.get(0):distinct.get(1);
    }

    /** Lowest evaluated cost currently available in the nondominated archive. */
    private Solution minimumCostArchive() {
        Solution best=archive.get(0);
        for(Solution s:archive) {
            if(s.cost<best.cost || (s.cost==best.cost && s.makespan<best.makespan))
                best=s;
        }
        return best;
    }

    private Solution chooseArchiveLeader(double a) {
        Bounds bounds=new Bounds(archive);
        List<Solution> sorted=new ArrayList<>(archive);
        sorted.sort(Comparator.comparingDouble((Solution s)->preference(s,a,bounds))
                .thenComparingDouble(s->s.makespan).thenComparingDouble(s->s.cost));
        int k=Math.min(2,sorted.size());
        if(k==1)return sorted.get(0);
        int[] ranks=new int[sorted.size()];
        double[] cd=crowdingDistance(sorted,ranks);
        double maxFinite=0;
        for(double x:cd)if(Double.isFinite(x))maxFinite=Math.max(maxFinite,x);
        double[] probs=new double[k];double sum=0;
        for(int j=0;j<k;j++){
            double div=Double.isInfinite(cd[j])?1.0:cd[j]/Math.max(EPS,maxFinite);
            probs[j]=Math.exp(-preference(sorted.get(j),a,bounds)/LEADER_TEMPERATURE)
                    *(1.0+LEADER_CROWDING_REWARD*div);
            sum+=probs[j];
        }
        double sample=random.nextDouble()*sum;
        for(int j=0;j<k;j++) {
            sample-=probs[j];
            if(sample<=0)return sorted.get(j);
        }
        return sorted.get(k-1);
    }

    private static double preference(Solution s,double alpha,Bounds b) {
        return alpha*b.m(s.makespan)+(1-alpha)*b.c(s.cost);
    }

    /** DO: weighted distinct task draw followed by independent copy decisions. */
    private void diffusionGenes(int[] child, int[] guide, double dof) {
        int k=Math.min(n,Math.max(1,(int)Math.round(dof*n)));
        boolean[] selected=new boolean[n];
        for(int draw=0;draw<k;draw++) {
            double total=0;
            for(int j=0;j<n;j++) if(!selected[j]) total+=importance[j];
            double needle=random.nextDouble()*total;
            int picked=-1;
            for(int j=0;j<n;j++) {
                if(selected[j])continue;
                needle-=importance[j];
                if(needle<=0) {picked=j;break;}
            }
            if(picked<0)for(int j=n-1;j>=0;j--)if(!selected[j]){picked=j;break;}
            selected[picked]=true;
            if(random.nextDouble() < dof*(0.5+0.5*importance[picked])) child[picked]=guide[picked];
        }
    }

    /** EO / SSO: guide genes, using a rank-dependent per-task probability. */
    private void guidedGenes(int[] child,int[] guide,double pressure) {
        for(int k=0;k<n;k++) {
            double p=clamp(pressure*random.nextDouble()*(0.5+0.5*importance[k]),0,1);
            if(random.nextDouble()<p)child[k]=guide[k];
        }
    }

    /**
     * Conservative cost/latency proxy for a SINGLE gene proposal. The true
     * target is always evaluated by the shared stage-in-aware evaluator; this
     * precomputation is only a proposal heuristic, not a second objective.
     *
     * Source/intermediate input files use bytes / 1e6 / VM bandwidth, exactly
     * the unit convention in WorkflowDatacenter (but without replica caching).
     */
    private void prepareResourceHeuristic() {
        optimisticServiceSeconds = new double[n][vmList.size()];
        for (int k = 0; k < n; k++) {
            Task task = taskOrder.get(k);
            double inputMb = 0.0;
            List<FileItem> files = task.getFileList();
            for (FileItem f : files) {
                if (f.getType() == Parameters.FileType.INPUT && f.isRealInputFile(files)) {
                    inputMb += f.getSize() / Consts.MILLION;
                }
            }
            for (int v : allowed[k]) {
                CondorVM vm = vmList.get(v);
                optimisticServiceSeconds[k][v] =
                        task.getCloudletTotalLength() / vm.getMips() + inputMb / vm.getBw();
            }
        }
    }

    /**
     * A rank-weighted task is reassigned toward a resource-efficient VM.
     * Group 1 prioritizes low makespan (estimated current per-VM workload);
     * group 2 prioritizes low cost. This produces exactly ONE additional
     * child genotype and does NOT consume any extra objective evaluations.
     */
    private void resourceAwareMutation(int[] genes, boolean latencyFocused) {
        double total = 0;
        for (double v : importance) total += Math.max(EPS, v);
        double draw = random.nextDouble() * total;
        int k = n - 1;
        for (int t = 0; t < n; t++) {
            draw -= Math.max(EPS, importance[t]);
            if (draw <= 0) { k = t; break; }
        }
        if (allowed[k].length <= 1) return;
        double[] load = new double[vmList.size()];
        for (int t = 0; t < n; t++) {
            if (t != k) load[genes[t]] += optimisticServiceSeconds[t][genes[t]];
        }
        // Rank all ALTERNATIVE VMs; retain stochasticity to avoid collapse
        // into a single fastest/cheapest VM for every task.
        int best = -1, second = -1, third = -1;
        double bestScore = Double.POSITIVE_INFINITY;
        double secondScore = Double.POSITIVE_INFINITY;
        double thirdScore = Double.POSITIVE_INFINITY;
        for (int v : allowed[k]) {
            if (v == genes[k]) continue;
            double service = optimisticServiceSeconds[k][v];
            double score = latencyFocused
                    ? service + 0.35 * load[v] / Math.max(1.0, n / 4.0)
                    : service * vmList.get(v).getCost()
                        + 0.04 * load[v] * vmList.get(v).getCost() / Math.max(1.0, n / 4.0);
            if (score < bestScore) {
                third = second; thirdScore = secondScore;
                second = best; secondScore = bestScore;
                best = v; bestScore = score;
            } else if (score < secondScore) {
                third = second; thirdScore = secondScore;
                second = v; secondScore = score;
            } else if (score < thirdScore) {
                third = v; thirdScore = score;
            }
        }
        double r = random.nextDouble();
        genes[k] = (r < 0.75 || second < 0) ? best
                : (r < 0.95 || third < 0) ? second : third;
    }


    /**
     * Post-search counterfactual. Compare whether one v10 proposal truly
     * improves makespan under the independent stage-in-aware PLANNING model.
     *
     * This never calls the optimizer's target evaluator and therefore does
     * not consume/record fitness evaluations. Both direct planning estimates
     * are OUTSIDE optimization and no mutated genotype is reinserted into the
     * selected solution/archive. They are NOT independent WorkflowSim replay.
     */
    private void runCriticalLocalAudit() {
        StageInAwareScheduleEvaluator independent =
                new StageInAwareScheduleEvaluator(taskOrder,vmList);
        int proposed=0,proxyImproves=0,trueImproves=0,agreement=0;
        int paretoImproved=0,paretoWorsened=0,tradeoffs=0,costIncreased=0;
        double meanTrueDelta=0.0,meanProxyDelta=0.0,meanCostChange=0.0;
        for(Solution parent:population()) {
            int[] before=parent.genes.clone();
            int[] after=before.clone();
            double p0=approximateMakespan(before,null);
            criticalRelocate(after);
            if(Arrays.equals(before,after))continue;
            proposed++;
            double p1=approximateMakespan(after,null);
            StageInAwareScheduleEvaluator.Result base =
                    independent.evaluate(evaluator.toAssignment(before));
            StageInAwareScheduleEvaluator.Result changed =
                    independent.evaluate(evaluator.toAssignment(after));
            double t0=base.makespan,t1=changed.makespan;
            double c0=base.cost,c1=changed.cost;
            boolean predictedPositive=p0-p1>1e-9;
            boolean truePositive=t0-t1>1e-9;
            if(predictedPositive)proxyImproves++;
            if(truePositive)trueImproves++;
            if(predictedPositive==truePositive)agreement++;
            if(c1>c0+1e-9)costIncreased++;
            boolean moveDominates=t1<=t0+1e-9 && c1<=c0+1e-9 &&
                    (t1<t0-1e-9 || c1<c0-1e-9);
            boolean originalDominates=t0<=t1+1e-9 && c0<=c1+1e-9 &&
                    (t0<t1-1e-9 || c0<c1-1e-9);
            if(moveDominates)paretoImproved++;
            else if(originalDominates)paretoWorsened++;
            else tradeoffs++;
            meanProxyDelta+=100.0*(p0-p1)/Math.max(EPS,p0);
            meanTrueDelta+=100.0*(t0-t1)/Math.max(EPS,t0);
            meanCostChange+=100.0*(c1-c0)/Math.max(EPS,c0);
        }
        if(proposed>0){
            meanProxyDelta/=proposed;
            meanTrueDelta/=proposed;
            meanCostChange/=proposed;
        }
        System.out.printf(java.util.Locale.ROOT,
                "FLA_CRITICAL_LOCAL_AUDIT proposed=%d predictedPositive=%d stageInPositive=%d directionalAgreement=%d meanPredictedImprovementPct=%.9f meanStageInImprovementPct=%.9f costIncreased=%d paretoImproved=%d paretoWorsened=%d mixedOrTied=%d meanCostIncreasePct=%.9f%n",
                proposed,proxyImproves,trueImproves,agreement,meanProxyDelta,meanTrueDelta,
                costIncreased,paretoImproved,paretoWorsened,tradeoffs,meanCostChange);
    }

    /**
     * v10 surrogate for critical-path time only. This is NOT an extra
     * objective evaluation: no call to evaluator or candidate recorder.
     * Real objectives still use StageInAwareScheduleEvaluator exactly once
     * after the child genes are finalized. The proxy deliberately ignores
     * caching, insertion gaps and resource provisioning overhead, and is
     * useful only for ranking local assignment proposals.
     */
    private void prepareCriticalProxy() {
        IdentityHashMap<Task,Integer> idx = new IdentityHashMap<>();
        for(int k=0;k<n;k++)idx.put(taskOrder.get(k),k);
        criticalParentIndices=new int[n][];
        criticalParentTransferMb=new double[n][];
        for(int k=0;k<n;k++){
            Task child=taskOrder.get(k);
            List<Integer> parents=new ArrayList<>();
            List<Double> transfers=new ArrayList<>();
            for(Task parent:child.getParentList()){
                Integer pi=idx.get(parent);
                if(pi==null)continue;
                double bytes=0.0;
                for(FileItem out:parent.getFileList()){
                    if(out.getType()!=Parameters.FileType.OUTPUT)continue;
                    for(FileItem in:child.getFileList()){
                        if(in.getType()==Parameters.FileType.INPUT && in.getName().equals(out.getName())){
                            bytes+=in.getSize();
                            break;
                        }
                    }
                }
                parents.add(pi);
                transfers.add(Math.max(0.0,bytes/Consts.MILLION));
            }
            criticalParentIndices[k]=new int[parents.size()];
            criticalParentTransferMb[k]=new double[parents.size()];
            for(int j=0;j<parents.size();j++){
                criticalParentIndices[k][j]=parents.get(j);
                criticalParentTransferMb[k][j]=transfers.get(j);
            }
        }
    }

    private double approximateMakespan(int[] genes, double[] finishOut) {
        double[] avail=new double[vmList.size()];
        double[] finish=finishOut==null ? new double[n] : finishOut;
        double makespan=0.0;
        for(int k=0;k<n;k++){
            int v=genes[k];
            double ready=avail[v];
            for(int j=0;j<criticalParentIndices[k].length;j++){
                int p=criticalParentIndices[k][j];
                double transfer=0.0;
                if(genes[p]!=v){
                    double bandwidth=Math.min(vmList.get(genes[p]).getBw(),vmList.get(v).getBw());
                    transfer=criticalParentTransferMb[k][j]*8.0/Math.max(EPS,bandwidth);
                }
                ready=Math.max(ready,finish[p]+transfer);
            }
            finish[k]=ready+optimisticServiceSeconds[k][v];
            avail[v]=finish[k];
            makespan=Math.max(makespan,finish[k]);
        }
        return makespan;
    }

    private double approximateCost(int[] genes) {
        double result=0.0;
        for(int k=0;k<n;k++)
            result+=optimisticServiceSeconds[k][genes[k]]*vmList.get(genes[k]).getCost();
        return result;
    }

    /**
     * Try one high-criticality task reassignment among at most eight late
     * tasks. Evaluate all candidate alternatives with the CHEAP PROXY;
     * record only ONE true objective evaluation later in the normal FLA loop.
     * v10-guarded uses the same pure-time surrogate with a soft cost guard,
     * not a second search objective call.
     */
    private void criticalRelocate(int[] genes) {
        if(n==0)return;
        double[] finish=new double[n];
        double before=approximateMakespan(genes,finish);
        double costBefore=criticalRelocationMode==2 ? approximateCost(genes) : 0;
        Integer[] ordering=new Integer[n];
        for(int k=0;k<n;k++)ordering[k]=k;
        Arrays.sort(ordering,(a,b)->Double.compare(finish[b],finish[a]));
        int top=Math.min(8,n);
        int bestTask=-1,bestVm=-1;
        double best=before;
        // Tie-breaking and stochastic pressure preserve diversity but never
        // trigger more objective evaluations.
        for(int i=0;i<top;i++){
            int k=ordering[i];
            int original=genes[k];
            for(int v:allowed[k]){
                if(v==original)continue;
                genes[k]=v;
                double candidate=approximateMakespan(genes,null);
                double score=candidate;
                if(criticalRelocationMode==2){
                    double extra=Math.max(0.0,approximateCost(genes)-costBefore);
                    score+=0.25*before*extra/Math.max(EPS,costBefore);
                }
                score*=0.995+0.010*random.nextDouble();
                if(score<best-1e-9){
                    best=score;bestTask=k;bestVm=v;
                }
            }
            genes[k]=original;
        }
        if(bestTask>=0)genes[bestTask]=bestVm;
    }

    /**
     * v9 research operator, NOT a source-FLA mathematical step:
     *
     * Edge-sensitive VM assignment: copy parent/child to a shared VM in
     * the cost-oriented FLA group to reduce inter-VM dependency traffic;
     * split a co-located parent/child to a lightly loaded VM in the
     * makespan-oriented group. The proxy uses only task and VM metadata.
     * The child receives exactly ONE normal shared-objective evaluation.
     */
    private void prepareDagEdgeRelocation() {
        IdentityHashMap<Task,Integer> index = new IdentityHashMap<>();
        for (int k=0;k<n;k++) index.put(taskOrder.get(k),k);
        List<Integer> from = new ArrayList<>();
        List<Integer> to = new ArrayList<>();
        List<Double> weights = new ArrayList<>();
        for(int child=0;child<n;child++) {
            Task ct=taskOrder.get(child);
            for(Task pt:ct.getParentList()) {
                Integer parent=index.get(pt);
                if(parent==null) continue;
                double bytes=0.0;
                for(FileItem output:pt.getFileList()) {
                    if(output.getType()!=Parameters.FileType.OUTPUT)continue;
                    for(FileItem input:ct.getFileList()) {
                        if(input.getType()==Parameters.FileType.INPUT
                                && output.getName().equals(input.getName())) {
                            bytes+=input.getSize();
                            break;
                        }
                    }
                }
                from.add(parent);
                to.add(child);
                // Avoid one huge edge monopolizing exploration; zero-file DAG
                // edges still remain eligible.
                weights.add(1.0+Math.log1p(Math.max(0.0,bytes/Consts.MILLION)));
            }
        }
        dagEdgeParent=new int[from.size()];
        dagEdgeChild=new int[to.size()];
        dagEdgeWeight=new double[weights.size()];
        for(int i=0;i<from.size();i++){
            dagEdgeParent[i]=from.get(i);
            dagEdgeChild[i]=to.get(i);
            dagEdgeWeight[i]=weights.get(i);
        }
    }

    private boolean taskAllowsVm(int task,int vm) {
        for(int v:allowed[task])if(v==vm)return true;
        return false;
    }

    private void edgeRelocation(int[] genes, boolean makespanGroup) {
        if(dagEdgeWeight.length==0) return;
        final boolean coLocate = edgeRelocationMode==1 ||
                (edgeRelocationMode==3 && !makespanGroup);
        // Under edgeRelocationMode=2 all groups use separation.
        double total=0.0;
        for(double w:dagEdgeWeight)total+=w;
        for(int attempt=0;attempt<9;attempt++) {
            double draw=random.nextDouble()*total;
            int e=dagEdgeWeight.length-1;
            for(int i=0;i<dagEdgeWeight.length;i++){
                draw-=dagEdgeWeight[i];
                if(draw<=0.0){e=i;break;}
            }
            int parent=dagEdgeParent[e],child=dagEdgeChild[e];
            int parentVM=genes[parent],childVM=genes[child];
            if(coLocate) {
                if(parentVM==childVM)continue;
                boolean moveChild=taskAllowsVm(child,parentVM);
                boolean moveParent=taskAllowsVm(parent,childVM);
                if(!moveChild && !moveParent)continue;
                if(moveChild && moveParent){
                    double costA=optimisticServiceSeconds[child][parentVM]*vmList.get(parentVM).getCost();
                    double costB=optimisticServiceSeconds[parent][childVM]*vmList.get(childVM).getCost();
                    if(costA<=costB)genes[child]=parentVM;
                    else genes[parent]=childVM;
                } else if(moveChild)genes[child]=parentVM;
                else genes[parent]=childVM;
                return;
            }
            if(parentVM!=childVM)continue;
            double[] load=new double[vmList.size()];
            for(int k=0;k<n;k++){
                if(k!=child)load[genes[k]]+=optimisticServiceSeconds[k][genes[k]];
            }
            int best=-1;
            double bestScore=Double.POSITIVE_INFINITY;
            for(int alternative:allowed[child]){
                if(alternative==parentVM)continue;
                // Greedy scheduling proxy with modest randomized noise to
                // retain exploration; no expensive fitness calls here.
                double score=load[alternative]+optimisticServiceSeconds[child][alternative];
                score*=0.90+0.20*random.nextDouble();
                if(score<bestScore){bestScore=score;best=alternative;}
            }
            if(best>=0){genes[child]=best;return;}
        }
    }

    /**
     * v3: copy a random contiguous block from one archive member.
     * v5: copy a genuine dependency-connected neighborhood instead.
     * The offspring evaluation count is identical for all variants.
     */
    private void archiveRecombine(int[] genes, boolean groupOne) {
        Solution guide = usePreferenceDonor
                ? chooseArchiveLeader(groupOne ? alpha1 : 1.0 - alpha1)
                : archive.get(random.nextInt(archive.size()));
        if (!useArchiveDagBlock) {
            int length = Math.min(n, 1 + random.nextInt(Math.max(1, n / 5)));
            int start = random.nextInt(n - length + 1);
            for (int k = start; k < start + length; k++) genes[k] = guide.genes[k];
            return;
        }
        double total = 0.0;
        for (int k = 0; k < n; k++) total += Math.max(EPS, importance[k]);
        double target = random.nextDouble() * total;
        int focal = n - 1;
        for (int k = 0; k < n; k++) {
            target -= Math.max(EPS, importance[k]);
            if (target <= 0) { focal = k; break; }
        }
        Map<Task,Integer> indices = new IdentityHashMap<>();
        for (int k = 0; k < n; k++) indices.put(taskOrder.get(k),k);
        genes[focal] = guide.genes[focal];
        int copied = 1;
        for (Task parent : taskOrder.get(focal).getParentList()) {
            Integer i = indices.get(parent);
            if (i != null && random.nextDouble() < 0.70) {
                genes[i] = guide.genes[i];
                copied++;
            }
        }
        for (Task child : taskOrder.get(focal).getChildList()) {
            Integer i = indices.get(child);
            if (i != null && random.nextDouble() < 0.50) {
                genes[i] = guide.genes[i];
                copied++;
            }
        }
        if (copied == 1 && n > 1) {
            int other = random.nextInt(n - 1);
            if (other >= focal) other++;
            genes[other] = guide.genes[other];
        }
    }

    /**
     * v6 novelty restoration: avoid repeated genotypes without increasing the
     * number of objective evaluations. A repair is deliberately stochastic and
     * does not use any additional fitness computation or simulated outcome.
     * If every sampled alternative is seen, keep the original FLA child.
     */
    private void repairNoveltyBeforeEvaluation(int[] child, Set<String> visited) {
        if (visited.add(Arrays.toString(child))) return;
        int attempts = useStrongRepair ? 18 : 8;
        for (int tryIndex = 0; tryIndex < attempts; tryIndex++) {
            int[] candidate=child.clone();
            int changes=(useStrongRepair && tryIndex>=4) ? 2 + random.nextInt(2) : 1;
            for(int t=0;t<changes;t++) {
                int k=random.nextInt(n);
                int[] options=allowed[k];
                if(options.length<2)continue;
                int idx=random.nextInt(options.length-1);
                if(options[idx]==candidate[k]) idx=options.length-1;
                if(options[idx]!=candidate[k]) candidate[k]=options[idx];
            }
            String signature=Arrays.toString(candidate);
            if(visited.add(signature)) {
                System.arraycopy(candidate,0,child,0,n);
                return;
            }
        }
        // Search space may be exhausted; do not fabricate a novel evaluation.
    }

    /** One different feasible VM gene, with per-molecule adaptive probability. */
    private void mutate(int[] child,double probability) {
        if(random.nextDouble()>=probability) return;
        int k=random.nextInt(n);
        int[] choices=allowed[k];
        if(choices.length<=1) return;
        int idx=random.nextInt(choices.length-1);
        if(choices[idx]>=0 && choices[idx]==child[k]) idx=choices.length-1;
        // Alternative must actually differ from the current assignment.
        if(choices[idx]==child[k]) {
            for(int v:choices)if(v!=child[k]){child[k]=v;return;}
        } else child[k]=choices[idx];
    }

    private static boolean dominates(Solution a,Solution b) {
        return a.makespan<=b.makespan && a.cost<=b.cost
                && (a.makespan<b.makespan || a.cost<b.cost);
    }

    private void archiveConsider(Solution s) {
        for(Solution a:archive) {
            // Keep a single representative for an equal objective vector.
            if (a.makespan<=s.makespan && a.cost<=s.cost) return;
        }
        for (int i=archive.size()-1;i>=0;i--) if(dominates(s,archive.get(i)))archive.remove(i);
        archive.add(s);
        while(archive.size()>archiveCapacity) pruneArchive();
    }

    private void pruneArchive() {
        int[] rank=new int[archive.size()];
        double[] cd=crowdingDistance(archive,rank);
        int victim=-1;double smallest=Double.POSITIVE_INFINITY;
        for(int i=0;i<cd.length;i++) {
            if(cd[i]<smallest){smallest=cd[i];victim=i;}
        }
        if(victim<0)victim=archive.size()-1;
        archive.remove(victim);
    }

    private static int[] nondominatedRank(List<Solution> all) {
        int n=all.size();
        int[] count=new int[n];
        List<List<Integer>> dominated=new ArrayList<>();
        for(int i=0;i<n;i++)dominated.add(new ArrayList<Integer>());
        for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){
            if(dominates(all.get(i),all.get(j))){dominated.get(i).add(j);count[j]++;}
            else if(dominates(all.get(j),all.get(i))){dominated.get(j).add(i);count[i]++;}
        }
        int[] rank=new int[n];Arrays.fill(rank,-1);
        List<Integer> front=new ArrayList<>();
        for(int i=0;i<n;i++)if(count[i]==0)front.add(i);
        int level=0;
        while(!front.isEmpty()){
            List<Integer> next=new ArrayList<>();
            for(int idx:front){rank[idx]=level;
                for(int j:dominated.get(idx))if(--count[j]==0)next.add(j);
            }
            front=next;level++;
        }
        return rank;
    }

    private static double[] crowdingDistance(List<Solution> xs,int[] ranks) {
        int n=xs.size();double[] cd=new double[n];
        int max=0;for(int r:ranks)max=Math.max(max,r);
        for(int level=0;level<=max;level++){
            List<Integer> front=new ArrayList<>();
            for(int i=0;i<n;i++)if(ranks[i]==level)front.add(i);
            if(front.isEmpty())continue;
            if(front.size()<=2){for(int i:front)cd[i]=Double.POSITIVE_INFINITY;continue;}
            for(int objective=0;objective<2;objective++){
                final int obj=objective;
                front.sort(Comparator.comparingDouble(i->obj==0?xs.get(i).makespan:xs.get(i).cost));
                cd[front.get(0)]=Double.POSITIVE_INFINITY;
                cd[front.get(front.size()-1)]=Double.POSITIVE_INFINITY;
                double min=obj==0?xs.get(front.get(0)).makespan:xs.get(front.get(0)).cost;
                double maxV=obj==0?xs.get(front.get(front.size()-1)).makespan:xs.get(front.get(front.size()-1)).cost;
                double span=maxV-min;
                if(span<=EPS)continue;
                for(int j=1;j<front.size()-1;j++){
                    int id=front.get(j);
                    if(Double.isInfinite(cd[id]))continue;
                    double left=obj==0?xs.get(front.get(j-1)).makespan:xs.get(front.get(j-1)).cost;
                    double right=obj==0?xs.get(front.get(j+1)).makespan:xs.get(front.get(j+1)).cost;
                    cd[id]+=(right-left)/span;
                }
            }
        }
        return cd;
    }


    /**
     * Experimental v8: elite selection retains one best-cost and/or one
     * best-makespan member of the evaluated parent+offspring pool before the
     * two FLA subgroups are formed. This does not increase the number of
     * objective evaluations, use a simulator oracle, or modify old defaults.
     */
    private void reserveObjectiveExtremes(List<Solution> union,
            List<Solution> survivors,Bounds b) {
        if(union.isEmpty()||survivors.isEmpty())return;
        Solution costExtreme=union.get(0);
        Solution timeExtreme=union.get(0);
        for(Solution s:union) {
            if(s.cost<costExtreme.cost ||
                 (s.cost==costExtreme.cost && s.makespan<costExtreme.makespan))
                 costExtreme=s;
            if(s.makespan<timeExtreme.makespan ||
                 (s.makespan==timeExtreme.makespan && s.cost<timeExtreme.cost))
                 timeExtreme=s;
        }
        List<Solution> reserved=new ArrayList<>();
        if(reserveCostExtreme)reserved.add(costExtreme);
        if(reserveMakespanExtreme && !Arrays.equals(costExtreme.genes,timeExtreme.genes))
            reserved.add(timeExtreme);
        for(Solution wanted:reserved) {
            boolean present=false;
            for(Solution old:survivors)
                if(Arrays.equals(old.genes,wanted.genes)){present=true;break;}
            if(present)continue;
            int victim=-1;
            double worst=Double.NEGATIVE_INFINITY;
            for(int i=0;i<survivors.size();i++){
                Solution old=survivors.get(i);
                boolean protectedMember=false;
                for(Solution elite:reserved)
                    if(Arrays.equals(old.genes,elite.genes)){protectedMember=true;break;}
                if(protectedMember)continue;
                double score=preference(old,0.5,b);
                if(score>worst){worst=score;victim=i;}
            }
            if(victim<0)throw new IllegalStateException("No replaceable elite survivor");
            survivors.set(victim,wanted);
        }
    }

    /**
     * NSGA-II-style environmental selection over the full parent+child pool.
     * Non-dominated rank is primary; crowding distance preserves extremes and
     * front spread. Duplicate genotypes are rejected on the first pass.
     *
     * This is explicitly a proposed NSGA-II/FLA hybrid selection operator,
     * NOT an original FLA equation. The number of evaluated offspring is
     * unchanged. It only reorders/retains existing candidate solutions.
     */
    private List<Solution> selectGlobalCrowding(List<Solution> candidates,int size,
            int[] ranks,double[] crowd) {
        List<Integer> order=new ArrayList<>();
        for(int i=0;i<candidates.size();i++)order.add(i);
        order.sort((a,b)->{
            int c=Integer.compare(ranks[a],ranks[b]);
            if(c!=0)return c;
            c=Double.compare(crowd[b],crowd[a]);
            if(c!=0)return c;
            c=Double.compare(candidates.get(a).makespan,candidates.get(b).makespan);
            if(c!=0)return c;
            return Integer.compare(a,b);
        });
        List<Solution> chosen=new ArrayList<>(size);
        for(int i:order) {
            Solution next=candidates.get(i);
            boolean duplicate=false;
            for(Solution c:chosen)if(Arrays.equals(c.genes,next.genes)){duplicate=true;break;}
            if(!duplicate)chosen.add(next);
            if(chosen.size()==size)return chosen;
        }
        for(int i:order) {
            chosen.add(candidates.get(i));
            if(chosen.size()==size)break;
        }
        if(chosen.size()!=size)throw new IllegalStateException("Insufficient candidates");
        return chosen;
    }

    private List<Solution> selectGroup(List<Solution> candidates,int offset,int size,
            int[] globalRank,double[] crowd,Bounds b,double alpha) {
        List<Integer> order=new ArrayList<>();
        for(int i=0;i<candidates.size();i++) order.add(i);
        double maxFinite=0;
        for(int i:order){double x=crowd[offset+i];if(Double.isFinite(x))maxFinite=Math.max(maxFinite,x);}
        final double finiteMax=maxFinite;
        order.sort((i,j)->{
            int ri=globalRank[offset+i],rj=globalRank[offset+j];
            if(ri!=rj)return Integer.compare(ri,rj);
            double di=Double.isInfinite(crowd[offset+i])?1.0:crowd[offset+i]/Math.max(EPS,finiteMax);
            double dj=Double.isInfinite(crowd[offset+j])?1.0:crowd[offset+j]/Math.max(EPS,finiteMax);
            double si=preference(candidates.get(i),alpha,b)-DIVERSITY_REWARD*di;
            double sj=preference(candidates.get(j),alpha,b)-DIVERSITY_REWARD*dj;
            int diff=Double.compare(si,sj);
            return diff!=0?diff:Integer.compare(i,j);
        });
        List<Solution> picked=new ArrayList<>(size);
        for(int idx:order){
            if(picked.size()>=size)break;
            Solution s=candidates.get(idx);
            boolean dup=false;
            for(Solution p:picked)if(Arrays.equals(p.genes,s.genes)){dup=true;break;}
            if(!dup)picked.add(s);
        }
        // The search space may have fewer distinct assignments than group size.
        if(picked.size()<size)for(int idx:order){
            if(picked.size()>=size)break;
            picked.add(candidates.get(idx));
        }
        return picked;
    }

    private static double hammingDiversity(List<Solution> xs) {
        if(xs.size()<2 || xs.get(0).genes.length==0)return 0;
        long sum=0;
        for(int i=0;i<xs.size();i++)for(int j=i+1;j<xs.size();j++){
            int[] a=xs.get(i).genes,b=xs.get(j).genes;
            for(int k=0;k<a.length;k++)if(a[k]!=b[k])sum++;
        }
        return 2.0*sum/((double)xs.size()*(xs.size()-1)*xs.get(0).genes.length);
    }

    private void adaptPreference() {
        // Step-to-step progress over the last (up to) ten generations.
        if(searchTrace.size()<2)return;
        int from=Math.max(0,searchTrace.size()-10);
        double oldM=searchTrace.get(from)[2],oldC=searchTrace.get(from)[3];
        double newM=Double.POSITIVE_INFINITY,newC=Double.POSITIVE_INFINITY;
        for(Solution s:archive) {newM=Math.min(newM,s.makespan);newC=Math.min(newC,s.cost);}
        double gainM=Math.max(0,(oldM-newM)/Math.max(EPS,oldM));
        double gainC=Math.max(0,(oldC-newC)/Math.max(EPS,oldC));
        alpha1=clamp(alpha1+0.2*(gainC-gainM),0.7,0.9);
    }

    private void saveTrace(int t) {
        double bestM=Double.POSITIVE_INFINITY,bestC=Double.POSITIVE_INFINITY;
        for(Solution s:archive){bestM=Math.min(bestM,s.makespan);bestC=Math.min(bestC,s.cost);}
        searchTrace.add(new double[]{t,archive.size(),bestM,bestC,hammingDiversity(population())});
    }
    private static double clamp(double x,double lo,double hi){return Math.max(lo,Math.min(hi,x));}
}