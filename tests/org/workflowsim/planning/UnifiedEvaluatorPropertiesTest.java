package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/** Deterministic shared-decoder property tests against an independent list calendar. */
public final class UnifiedEvaluatorPropertiesTest {
    private static final double EPS = 1e-8;
    private UnifiedEvaluatorPropertiesTest() {}

    public static void main(String[] args) {
        Random random = new Random(20261102L);
        int checked = 0;
        for (int trial = 0; trial < 150; trial++) {
            int n = 5 + random.nextInt(12);
            int m = 2 + random.nextInt(3);
            int[][] parents = new int[n][];
            double[][] delays = new double[n][];
            double[][] durations = new double[n][m];
            double[] prices = new double[m];
            for (int v = 0; v < m; v++) prices[v] = 0.1 + 0.1 * (v + 1);
            for (int k = 0; k < n; k++) {
                List<Integer> ps = new ArrayList<>();
                List<Double> ds = new ArrayList<>();
                for (int p = 0; p < k; p++) if (random.nextDouble() < 0.18) {
                    ps.add(p); ds.add((double) random.nextInt(16));
                }
                parents[k] = new int[ps.size()];
                delays[k] = new double[ds.size()];
                for (int j = 0; j < ps.size(); j++) {
                    parents[k][j] = ps.get(j);
                    delays[k][j] = ds.get(j);
                }
                for (int v = 0; v < m; v++) durations[k][v] = 1 + random.nextInt(40);
            }
            double[][] starts = new double[m][n], finishes = new double[m][n];
            int[] counts = new int[m], taskVMs = new int[n];
            double[] taskFinishes = new double[n];
            UnifiedScheduleEvaluator evaluator = new UnifiedScheduleEvaluator(
                parents, delays, durations, prices, starts, finishes, counts, taskFinishes, taskVMs);

            for (int attempt = 0; attempt < 12; attempt++) {
                int[] genes = new int[n];
                for (int k = 0; k < n; k++) genes[k] = random.nextInt(m);
                double[] actual = evaluator.evaluate(genes);
                double[] oracle = oracle(parents, delays, durations, prices, genes);
                near("makespan", actual[0], oracle[0]);
                near("cost", actual[1], oracle[1]);
                for (int v = 0; v < m; v++) for (int j = 1; j < counts[v]; j++) {
                    require(finishes[v][j - 1] <= starts[v][j] + EPS, "VM overlap/order error");
                }
                for (int k = 0; k < n; k++) {
                    double begin = taskFinishes[k] - durations[k][genes[k]];
                    for (int j = 0; j < parents[k].length; j++) {
                        int p = parents[k][j];
                        double ready = taskFinishes[p] + (genes[p] == genes[k] ? 0 : delays[k][j]);
                        require(begin + EPS >= ready, "DAG precedence error");
                    }
                }
                checked++;
            }
        }

        int[][] p = {{}, {0}};
        double[][] d = {{}, {2}};
        double[][] t = {{2, 3}, {4, 5}};
        double[][] s = new double[2][2], f = new double[2][2];
        UnifiedScheduleEvaluator evaluator = new UnifiedScheduleEvaluator(
            p, d, t, new double[] {1, 2}, s, f, new int[2], new double[2], new int[2]);
        rejects(() -> evaluator.evaluate(new int[] {0}));
        rejects(() -> evaluator.evaluate(new int[] {0, 2}));
        rejects(() -> new UnifiedScheduleEvaluator(
            new int[][] {{1}, {}}, d, t, new double[] {1, 2},
            s, f, new int[2], new double[2], new int[2]));
        System.out.println("PASS UnifiedEvaluatorPropertiesTest: " + checked
            + " fixed-seed schedules, independent oracle, precedence, VM calendars and invalid-input checks");
    }

    private static double[] oracle(int[][] parents, double[][] delays,
            double[][] durations, double[] prices, int[] genes) {
        int m = prices.length, n = genes.length;
        List<List<double[]>> calendars = new ArrayList<>();
        for (int v = 0; v < m; v++) calendars.add(new ArrayList<>());
        double[] finish = new double[n];
        double makespan = 0, cost = 0;
        for (int k = 0; k < n; k++) {
            int vm = genes[k];
            double ready = 0;
            for (int j = 0; j < parents[k].length; j++) {
                int p = parents[k][j];
                ready = Math.max(ready, finish[p] + (genes[p] == vm ? 0 : delays[k][j]));
            }
            double duration = durations[k][vm];
            List<double[]> slots = calendars.get(vm);
            double begin = ready;
            int at = 0;
            while (at < slots.size()) {
                double[] slot = slots.get(at);
                if (begin + duration <= slot[0]) break;
                begin = Math.max(begin, slot[1]);
                at++;
            }
            finish[k] = begin + duration;
            slots.add(at, new double[] {begin, finish[k]});
            makespan = Math.max(makespan, finish[k]);
            cost += duration * prices[vm];
        }
        return new double[] {makespan, cost};
    }

    private static void near(String what, double got, double expected) {
        require(!Double.isNaN(got) && Math.abs(got - expected) < EPS,
            what + " expected " + expected + ", got " + got);
    }
    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    private static void rejects(Runnable action) {
        try { action.run(); } catch (IllegalArgumentException expected) { return; }
        throw new AssertionError("Expected invalid input to be rejected");
    }
}
