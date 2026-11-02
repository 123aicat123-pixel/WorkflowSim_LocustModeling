package org.workflowsim.planning;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Arrays;

/**
 * Self-contained regression: run the actual private/protected decode() method
 * of LIWSA, NSGA-II and MLEAO using five DAG tasks and two VM calendars.
 * No external JUnit dependency or CloudSim bootstrap is needed.
 *
 * Topological task order: A, B, C, D, E. VM assignments: 0, 1, 0, 0, 0.
 * Durations: A=10, B=12, C=20, D=8, E=45 seconds.
 * Edges: B->C with 18s cross-VM transfer; B->D with 0s transfer.
 * Correct VM0 intervals: A[0,10], D[12,20], C[30,50], E[50,95].
 * VM1: B[0,12]. Expected makespan and cost (prices=1): 95.
 *
 * Before the fix, D[12,20] was appended AFTER C[30,50], leaving the
 * calendar unsorted. E was then illegally placed at [20,65], overlapping C;
 * decode() returned an impossible makespan of 65 seconds.
 */
public final class DecoderInsertionRegressionTest {
    private static final double EPS = 1e-9;
    private static final int[] GENOTYPE = {0, 1, 0, 0, 0};
    private static final double[] DURATION = {10, 12, 20, 8, 45};
    private static final int[][] PARENTS = {{}, {}, {1}, {1}, {}};
    private static final double[][] TRANSFER = {{}, {}, {18}, {0}, {}};

    private DecoderInsertionRegressionTest() {}

    public static void main(String[] args) throws Exception {
        check(LIWSAPlanningAlgorithm.class);
        check(NSGAIIPlanningAlgorithm.class);
        check(MLEAOPlanningAlgorithm.class);
        System.out.println("PASS: all three decoders returned feasible makespan=95.0, cost=95.0");
    }

    private static void check(Class<?> cls) throws Exception {
        Object algorithm = cls.getDeclaredConstructor().newInstance();
        double[][] durations = new double[5][2];
        for (int i = 0; i < 5; i++) {
            durations[i][GENOTYPE[i]] = DURATION[i];
        }
        set(cls, algorithm, "decN", 5);
        set(cls, algorithm, "decParentIdx", PARENTS);
        set(cls, algorithm, "decParentTransfer", TRANSFER);
        set(cls, algorithm, "decDuration", durations);
        set(cls, algorithm, "decVmPrice", new double[] {1, 1});
        set(cls, algorithm, "decEvStart", new double[2][5]);
        set(cls, algorithm, "decEvFinish", new double[2][5]);
        set(cls, algorithm, "decEvCount", new int[2]);
        set(cls, algorithm, "decFinish", new double[5]);
        set(cls, algorithm, "decAssigned", new int[5]);

        Method decode = cls.getDeclaredMethod("decode", int[].class);
        decode.setAccessible(true);
        double[] objectives = (double[]) decode.invoke(algorithm, (Object) GENOTYPE.clone());
        close(cls, "makespan", objectives[0], 95);
        close(cls, "cost", objectives[1], 95);

        double[] finish = (double[]) get(cls, algorithm, "decFinish");
        double[] expectedFinishes = {10, 12, 50, 20, 95};
        for (int k = 0; k < finish.length; k++) {
            close(cls, "finish task " + k, finish[k], expectedFinishes[k]);
        }

        // Check precedence including cross-VM communication time.
        for (int k = 0; k < 5; k++) {
            double start = finish[k] - DURATION[k];
            for (int j = 0; j < PARENTS[k].length; j++) {
                int p = PARENTS[k][j];
                double ready = finish[p] + (GENOTYPE[p] == GENOTYPE[k] ? 0 : TRANSFER[k][j]);
                require(start + EPS >= ready, cls.getSimpleName() + ": precedence violation task " + k);
            }
        }

        // Verify the actual in-memory per-VM calendars remain sorted and non-overlapping.
        double[][] starts = (double[][]) get(cls, algorithm, "decEvStart");
        double[][] ends = (double[][]) get(cls, algorithm, "decEvFinish");
        int[] counts = (int[]) get(cls, algorithm, "decEvCount");
        require(Arrays.equals(counts, new int[] {4, 1}), cls.getSimpleName() + ": wrong VM task counts");
        double[] expectedStart0 = {0, 12, 30, 50};
        double[] expectedEnd0 = {10, 20, 50, 95};
        for (int v = 0; v < counts.length; v++) {
            for (int i = 0; i < counts[v]; i++) {
                require(starts[v][i] <= ends[v][i] + EPS, cls.getSimpleName() + ": negative interval");
                if (i > 0) {
                    require(ends[v][i-1] <= starts[v][i] + EPS,
                        cls.getSimpleName() + ": overlap / unsorted VM" + v + " at " + i);
                }
                if (v == 0) {
                    close(cls, "VM0 start " + i, starts[v][i], expectedStart0[i]);
                    close(cls, "VM0 end " + i, ends[v][i], expectedEnd0[i]);
                }
            }
        }
        close(cls, "VM1 start", starts[1][0], 0);
        close(cls, "VM1 end", ends[1][0], 12);
        System.out.println("PASS " + cls.getSimpleName()
            + ": makespan=" + objectives[0] + " cost=" + objectives[1]
            + " VM0=[0,10],[12,20],[30,50],[50,95]");
    }

    private static void set(Class<?> cls, Object target, String fieldName, Object value) throws Exception {
        Field field = cls.getDeclaredField(fieldName);
        field.setAccessible(true);
        field.set(target, value);
    }

    private static Object get(Class<?> cls, Object target, String fieldName) throws Exception {
        Field field = cls.getDeclaredField(fieldName);
        field.setAccessible(true);
        return field.get(target);
    }

    private static void close(Class<?> cls, String what, double actual, double expected) {
        require(Double.isFinite(actual) && Math.abs(actual - expected) < EPS,
            cls.getSimpleName() + ": " + what + " expected " + expected + " but got " + actual);
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
