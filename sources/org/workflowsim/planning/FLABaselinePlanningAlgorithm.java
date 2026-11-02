package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

import org.workflowsim.CondorVM;
import org.workflowsim.Task;

/**
 * A single-objective, continuous Fick's Law Algorithm (FLA) adapted to
 * WorkflowSim's categorical task-to-VM scheduling domain.
 *
 * SOURCE: FLA.m, "Fick's Law Algorithm (FLA) source codes version 1.0",
 * Hashim, Mostafa, Hussien, Mirjalili & Sallam (2023), KBS 260, 110146.
 * MATLAB source mirror: https://github.com/Hariom-01/Optimization-Using-Fick-s-Law-Algorithm/blob/main/FLA.m
 * Coauthor Julia port: https://github.com/AbdelazimHussien/MetaheuristicsAlgorithms.jl/blob/main/src/algo/FLA.jl
 *
 * Fidelity boundary: DO/EO/SSO formulas, the two molecular groups, TF and
 * strict greedy acceptance follow the MATLAB source, including its unusual
 * EO group-2 use of group-1 best and the SSO group-2 re-use of the final
 * group-1 random vector. Changes from continuous benchmark FLA:
 * (1) positions in [0,1]^n are mapped to feasible categorical VM indices;
 * (2) fixed-scale weighted makespan/cost is the scalar fitness;
 * (3) optional external archive is PASSIVE (reports visited non-dominated
 *     schedules, never changes the FLA search trajectory);
 * (4) numerical guards prevent Java NaNs/Inf from corrupting scheduling.
 * This is NOT a native multi-objective FLA and is NOT the proposed
 * DAG-Pareto-FLA algorithm.
 *
 * Thread safety: matching WorkflowSim's pattern, static configuration and
 * lastRun require sequential simulations in the same JVM.
 */
public class FLABaselinePlanningAlgorithm extends BasePlanningAlgorithm {
    public static int CONFIG_POPULATION_SIZE = 30;
    public static int CONFIG_GENERATION_COUNT = 100;
    public static Long CONFIG_RANDOM_SEED = null;
    public static double CONFIG_MAKESPAN_WEIGHT = 0.5;
    public static boolean CONFIG_ENFORCE_PES = false;
    public static boolean CONFIG_COLLECT_ARCHIVE = false;
    public static int CONFIG_ARCHIVE_CAPACITY = 100;
    public static List<Map<Integer, Integer>> CONFIG_SEED_ASSIGNMENTS = null;
    public static volatile LastRunMetrics lastRun;

    // MATLAB FLA.m version 1.0 constants.
    private static final double C1 = 0.5;
    private static final double C2 = 2.0;
    private static final double C3 = 0.1;
    private static final double C4 = 0.2;
    private static final double C5 = 2.0;
    private static final double D = 0.01;
    private static final double EPS = 1e-12;

    public static final class LastRunMetrics {
        public double chosenMakespan;
        public double chosenCost;
        public double chosenFitness;
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
        public double makespanScale;
        public double costScale;
        public double makespanWeight;
        public boolean passiveArchiveEnabled;
        public List<double[]> bestCurve; // {generation (starting 0), best scalar fitness}
    }

    private static final class Molecule {
        final double[] position;
        final int[] genotype;
        final double makespan;
        final double cost;
        final double fitness;
        Molecule(double[] position, int[] genotype, double makespan, double cost, double fitness) {
            this.position = position.clone();
            this.genotype = genotype.clone();
            this.makespan = makespan;
            this.cost = cost;
            this.fitness = fitness;
        }
    }

    private final int populationSize;
    private final int generations;
    private final double weight;
    private final boolean enforcePes;
    private final boolean collectArchive;
    private final int archiveCapacity;
    private final Long seed;

    private Random random;
    private FLAScheduleEvaluator evaluator;
    private int[][] allowedVms;
    private int dimensions;
    private int n1;
    private Molecule[] molecules;
    private Molecule bestEver;
    private double makeScale;
    private double costScale;
    private final List<Molecule> archive = new ArrayList<>();
    private final List<double[]> curve = new ArrayList<>();
    private int doCount, eoCount, ssoCount;

    public FLABaselinePlanningAlgorithm() {
        this.populationSize = CONFIG_POPULATION_SIZE;
        this.generations = CONFIG_GENERATION_COUNT;
        this.weight = CONFIG_MAKESPAN_WEIGHT;
        this.enforcePes = CONFIG_ENFORCE_PES;
        this.collectArchive = CONFIG_COLLECT_ARCHIVE;
        this.archiveCapacity = CONFIG_ARCHIVE_CAPACITY;
        this.seed = CONFIG_RANDOM_SEED;
    }

    /** No setters: WorkflowPlanner constructs the planner via its no-arg constructor. */
    @Override
    public void run() {
        lastRun = null;
        if (populationSize < 4 || generations < 1 || archiveCapacity < 2
                || !Double.isFinite(weight) || weight < 0 || weight > 1) {
            throw new IllegalArgumentException("Invalid FLA population/generations/archive/weight");
        }
        long started = System.nanoTime();
        List<CondorVM> vms = new ArrayList<>();
        for (Object vm : getVmList()) { vms.add((CondorVM) vm); }
        evaluator = new FLAScheduleEvaluator(getTaskList(), vms,
                FLAScheduleEvaluator.InsertionMode.VERIFIED_EARLIEST_INSERTION, enforcePes);
        dimensions = evaluator.getTaskOrder().size();
        allowedVms = new int[dimensions][];
        for (int j = 0; j < dimensions; j++) {
            if (enforcePes) {
                allowedVms[j] = evaluator.getFeasibleVmIndices(j);
            } else {
                allowedVms[j] = new int[vms.size()];
                for (int k = 0; k < vms.size(); k++) { allowedVms[j][k] = k; }
            }
        }
        random = (seed == null) ? new Random() : new Random(seed);
        n1 = (populationSize + 1) / 2;
        molecules = new Molecule[populationSize];
        archive.clear(); curve.clear();
        doCount = 0; eoCount = 0; ssoCount = 0;
        initializeFixedObjectiveScales();
        initializeMolecules();
        curve.add(new double[]{0, bestEver.fitness});

        for (int t = 1; t <= generations; t++) {
            double tf = Math.pow(Math.sinh((double) t / generations), C1);
            Molecule[] before = molecules.clone();
            Molecule best1 = groupBest(before, 0, n1);
            Molecule best2 = groupBest(before, n1, populationSize);
            double[] mean1 = groupMean(before, 0, n1);
            double[] mean2 = groupMean(before, n1, populationSize);
            double[] meanAll = groupMean(before, 0, populationSize);
            double[] global = bestEver.position;
            double groupBestFitness = Math.min(best1.fitness, best2.fitness);
            double[][] children = new double[populationSize][dimensions];
            if (tf < 0.9) {
                doCount++;
                diffusion(before, best1, best2, mean1, mean2, tf, children);
            } else if (tf <= 1.0) {
                eoCount++;
                equilibrium(before, best1, best2, mean1, mean2, tf, children);
            } else {
                ssoCount++;
                steadyState(before, mean1, meanAll, global,
                        groupBestFitness, tf, children);
            }
            for (int i = 0; i < populationSize; i++) {
                correct(children[i], before[i].position);
                Molecule candidate = evaluate(children[i]);
                if (collectArchive) { considerArchive(candidate); }
                if (candidate.fitness < before[i].fitness) {
                    molecules[i] = candidate;
                }
                if (molecules[i].fitness < bestEver.fitness) {
                    bestEver = molecules[i];
                }
            }
            curve.add(new double[]{t, bestEver.fitness});
        }
        evaluator.commitAssignment(bestEver.genotype);
        publishResult((System.nanoTime() - started) / 1_000_000L);
    }

    private void initializeFixedObjectiveScales() {
        int[] slow = new int[dimensions], fast = new int[dimensions];
        List<CondorVM> vms = evaluator.getVmList();
        for (int i = 0; i < dimensions; i++) {
            int min = allowedVms[i][0], max = allowedVms[i][0];
            for (int v : allowedVms[i]) {
                if (vms.get(v).getMips() < vms.get(min).getMips()) { min = v; }
                if (vms.get(v).getMips() > vms.get(max).getMips()) { max = v; }
            }
            slow[i] = min;
            fast[i] = max;
        }
        double[] s = evaluator.evaluate(slow);
        double[] f = evaluator.evaluate(fast);
        makeScale = Math.max(EPS, Math.max(s[0], f[0]));
        costScale = Math.max(EPS, Math.max(s[1], f[1]));
    }

    private void initializeMolecules() {
        int pos = 0;
        if (CONFIG_SEED_ASSIGNMENTS != null) {
            for (Map<Integer, Integer> assignment : CONFIG_SEED_ASSIGNMENTS) {
                if (pos >= populationSize) { break; }
                try {
                    int[] g = evaluator.fromAssignment(assignment);
                    double[] x = new double[dimensions];
                    for (int k = 0; k < dimensions; k++) {
                        int j = indexOf(allowedVms[k], g[k]);
                        if (j < 0) { throw new IllegalArgumentException("Infeasible warm-start"); }
                        x[k] = (j + 0.5) / allowedVms[k].length;
                    }
                    molecules[pos++] = evaluate(x);
                } catch (IllegalArgumentException ex) {
                    System.err.println("FLA: skipped invalid warm-start: " + ex.getMessage());
                }
            }
        }
        while (pos < populationSize) {
            double[] x = new double[dimensions];
            for (int k = 0; k < dimensions; k++) { x[k] = random.nextDouble(); }
            molecules[pos++] = evaluate(x);
        }
        bestEver = groupBest(molecules, 0, populationSize);
        if (collectArchive) {
            for (Molecule m : molecules) { considerArchive(m); }
        }
    }

    private static int indexOf(int[] values, int wanted) {
        for (int j = 0; j < values.length; j++) { if (values[j] == wanted) { return j; } }
        return -1;
    }

    /** Continuous [0,1] coordinate -> categorical task-specific VM index. */
    private int[] genotypeOf(double[] x) {
        int[] genotype = new int[dimensions];
        for (int k = 0; k < dimensions; k++) {
            int[] options = allowedVms[k];
            int j = Math.min(options.length - 1, (int) Math.floor(x[k] * options.length));
            genotype[k] = options[Math.max(0, j)];
        }
        return genotype;
    }

    private Molecule evaluate(double[] x) {
        int[] genotype = genotypeOf(x);
        double[] f = evaluator.evaluate(genotype);
        double scalar = weight * (f[0] / makeScale) + (1 - weight) * (f[1] / costScale);
        return new Molecule(x, genotype, f[0], f[1], scalar);
    }

    private Molecule groupBest(Molecule[] group, int lo, int hi) {
        Molecule best = group[lo];
        for (int i = lo + 1; i < hi; i++) {
            if (group[i].fitness < best.fitness) { best = group[i]; }
        }
        return best;
    }

    private double[] groupMean(Molecule[] group, int lo, int hi) {
        double[] avg = new double[dimensions];
        for (int i = lo; i < hi; i++) {
            for (int k = 0; k < dimensions; k++) { avg[k] += group[i].position[k]; }
        }
        for (int k = 0; k < dimensions; k++) { avg[k] /= (hi - lo); }
        return avg;
    }

    private static double norm(double[] a, double[] b) {
        double sum = 0;
        for (int i = 0; i < a.length; i++) {
            double d = a[i] - b[i];
            sum += d * d;
        }
        return Math.sqrt(sum);
    }

    private int direction() { return random.nextBoolean() ? 1 : -1; }

    /** Diffusion Operator (DO), matching source group-direction and NT12 logic. */
    private void diffusion(Molecule[] before, Molecule b1, Molecule b2,
            double[] mean1, double[] mean2, double tf, double[][] child) {
        double dof = Math.pow(Math.exp(-(C2 * tf - random.nextDouble())), C2);
        double tdo = C5 * tf - random.nextDouble();
        if (tdo < random.nextDouble()) {
            int nt = boundedTransferCount(n1);
            for (int i = 0; i < nt; i++) {
                double denominator = norm(b2.position, before[i].position) + EPS;
                int df = direction();
                for (int j = 0; j < dimensions; j++) {
                    double flux = -D * (mean2[j] - mean1[j]) / denominator;
                    child[i][j] = b2.position[j] + df * dof * random.nextDouble()
                            * (flux * b2.position[j] - before[i].position[j]);
                }
            }
            for (int i = nt; i < n1; i++) {
                intraGroupDO(child[i], before[i].position, b1.position, dof);
            }
            for (int i = n1; i < populationSize; i++) {
                double r = random.nextDouble();
                for (int j = 0; j < dimensions; j++) { child[i][j] = b2.position[j] + dof * r; }
            }
        } else {
            int nt = boundedTransferCount(populationSize - n1);
            for (int a = 0; a < nt; a++) {
                int i = n1 + a;
                double denominator = norm(b1.position, before[i].position) + EPS;
                int df = direction();
                for (int j = 0; j < dimensions; j++) {
                    double flux = -D * (mean1[j] - mean2[j]) / denominator;
                    child[i][j] = b1.position[j] + df * dof * random.nextDouble()
                            * (flux * b1.position[j] - before[i].position[j]);
                }
            }
            for (int i = n1 + nt; i < populationSize; i++) {
                intraGroupDO(child[i], before[i].position, b2.position, dof);
            }
            for (int i = 0; i < n1; i++) {
                double r = random.nextDouble();
                for (int j = 0; j < dimensions; j++) { child[i][j] = b1.position[j] + dof * r; }
            }
        }
    }

    private int boundedTransferCount(int size) {
        int nt = (int) Math.round(((C4 - C3) * size) * random.nextDouble() + C3 * size);
        return Math.max(0, Math.min(size, nt));
    }

    private void intraGroupDO(double[] out, double[] current, double[] leader, double dof) {
        for (int j = 0; j < dimensions; j++) {
            double p = random.nextDouble();
            if (p < 0.8) {
                out[j] = leader[j];
            } else if (p < 0.9) {
                out[j] = current[j] + dof * random.nextDouble();
            } else {
                out[j] = current[j];
            }
        }
    }

    /** Equilibrium Operator (EO): source MATLAB group-2 formula uses Xeo1. */
    private void equilibrium(Molecule[] before, Molecule b1, Molecule b2,
            double[] mean1, double[] mean2, double tf, double[][] child) {
        for (int i = 0; i < populationSize; i++) {
            boolean first = i < n1;
            Molecule lead = first ? b1 : b2;
            double[] avg = first ? mean1 : mean2;
            double denominator = norm(lead.position, before[i].position) + EPS;
            double ms = Math.exp(-lead.fitness / (before[i].fitness + EPS));
            int df = direction();
            for (int j = 0; j < dimensions; j++) {
                double flux = -D * (lead.position[j] - avg[j]) / denominator;
                double drf = safeExp(-flux / tf);
                double q = df * drf * random.nextDouble();
                double ref = b1.position[j]; // MATLAB FLA.m uses Xeo1 in both groups
                child[i][j] = lead.position[j]
                        + q * before[i].position[j] + q * (ms * ref - before[i].position[j]);
            }
        }
    }

    /** Steady State Operator (SSO): source MATLAB reuses last group-1 R1 in group 2. */
    private void steadyState(Molecule[] before,
            double[] mean1, double[] meanAll, double[] global,
            double fsss, double tf, double[][] child) {
        double[] lastGroup1R = new double[dimensions];
        for (int i = 0; i < populationSize; i++) {
            boolean first = i < n1;
            double denominator = norm(global, before[i].position) + EPS;
            double ms = Math.exp(-fsss / (before[i].fitness + EPS));
            int df = direction();
            for (int j = 0; j < dimensions; j++) {
                double flux = first
                        ? -D * (meanAll[j] - mean1[j]) / denominator
                        : -D * (mean1[j] - meanAll[j]) / denominator;
                double drf = safeExp(-flux / tf);
                double r;
                if (first) {
                    r = random.nextDouble();
                    lastGroup1R[j] = r;
                } else {
                    r = lastGroup1R[j];
                }
                double q = df * drf * r;
                child[i][j] = global[j]
                        + q * before[i].position[j] + q * (ms * global[j] - before[i].position[j]);
            }
        }
    }

    private static double safeExp(double arg) { return Math.exp(Math.max(-700, Math.min(700, arg))); }

    private static void correct(double[] candidate, double[] original) {
        for (int j = 0; j < candidate.length; j++) {
            if (!Double.isFinite(candidate[j])) { candidate[j] = original[j]; }
            candidate[j] = Math.max(0.0, Math.min(1.0, candidate[j]));
        }
    }

    private static boolean dominates(Molecule a, Molecule b) {
        return a.makespan <= b.makespan && a.cost <= b.cost
                && (a.makespan < b.makespan || a.cost < b.cost);
    }

    private void considerArchive(Molecule candidate) {
        for (Molecule old : archive) {
            if ((old.makespan <= candidate.makespan && old.cost <= candidate.cost)
                    || Arrays.equals(old.genotype, candidate.genotype)) {
                return;
            }
        }
        for (int i = archive.size() - 1; i >= 0; i--) {
            if (dominates(candidate, archive.get(i))) { archive.remove(i); }
        }
        archive.add(candidate);
        while (archive.size() > archiveCapacity) { dropMostCrowded(); }
    }

    private void dropMostCrowded() {
        final int size = archive.size();
        if (size < 3) { archive.remove(size - 1); return; }
        double minM = Double.POSITIVE_INFINITY, maxM = Double.NEGATIVE_INFINITY;
        double minC = Double.POSITIVE_INFINITY, maxC = Double.NEGATIVE_INFINITY;
        for (Molecule m : archive) {
            minM = Math.min(minM, m.makespan); maxM = Math.max(maxM, m.makespan);
            minC = Math.min(minC, m.cost); maxC = Math.max(maxC, m.cost);
        }
        double[] crowd = new double[size];
        for (int objective = 0; objective < 2; objective++) {
            final int which = objective;
            List<Integer> order = new ArrayList<>();
            for (int i = 0; i < size; i++) { order.add(i); }
            Collections.sort(order, (a, b) -> Double.compare(
                    which == 0 ? archive.get(a).makespan : archive.get(a).cost,
                    which == 0 ? archive.get(b).makespan : archive.get(b).cost));
            crowd[order.get(0)] = Double.POSITIVE_INFINITY;
            crowd[order.get(size - 1)] = Double.POSITIVE_INFINITY;
            double range = Math.max(EPS, objective == 0 ? maxM - minM : maxC - minC);
            for (int i = 1; i < size - 1; i++) {
                int k = order.get(i);
                if (Double.isInfinite(crowd[k])) { continue; }
                double prev = objective == 0 ? archive.get(order.get(i - 1)).makespan
                        : archive.get(order.get(i - 1)).cost;
                double next = objective == 0 ? archive.get(order.get(i + 1)).makespan
                        : archive.get(order.get(i + 1)).cost;
                crowd[k] += (next - prev) / range;
            }
        }
        int drop = -1;
        double min = Double.POSITIVE_INFINITY;
        for (int i = 0; i < size; i++) {
            if (crowd[i] < min) { min = crowd[i]; drop = i; }
        }
        if (drop < 0) { drop = size - 1; }
        archive.remove(drop);
    }

    private void publishResult(long elapsedMillis) {
        LastRunMetrics info = new LastRunMetrics();
        info.chosenMakespan = bestEver.makespan;
        info.chosenCost = bestEver.cost;
        info.chosenFitness = bestEver.fitness;
        info.populationSizeUsed = populationSize;
        info.generationCountUsed = generations;
        info.objectiveEvaluations = evaluator.getObjectiveEvaluations();
        info.searchWallClockMillis = elapsedMillis;
        info.diffusionIterations = doCount;
        info.equilibriumIterations = eoCount;
        info.steadyStateIterations = ssoCount;
        info.makespanScale = makeScale;
        info.costScale = costScale;
        info.makespanWeight = weight;
        info.passiveArchiveEnabled = collectArchive;
        info.bestCurve = new ArrayList<>();
        for (double[] x : curve) { info.bestCurve.add(x.clone()); }
        info.paretoFrontPoints = new ArrayList<>();
        info.paretoFrontAssignments = new ArrayList<>();
        List<Molecule> output = collectArchive ? archive : Collections.singletonList(bestEver);
        for (Molecule m : output) {
            info.paretoFrontPoints.add(new double[]{m.makespan, m.cost});
            info.paretoFrontAssignments.add(evaluator.toAssignment(m.genotype));
        }
        info.paretoFrontSize = output.size();
        lastRun = info;
        System.out.printf("FLA (MATLAB-v1.0 adapted): makespan=%.6f cost=%.6f scalar=%.6f, "
                + "evaluations=%d, DO=%d EO=%d SSO=%d%n",
                info.chosenMakespan, info.chosenCost, info.chosenFitness,
                info.objectiveEvaluations, doCount, eoCount, ssoCount);
    }
}