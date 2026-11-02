package org.workflowsim.planning;

import java.util.Arrays;

/**
 * Shared planning-level decoder for VM-assignment chromosomes.
 * Tasks must be in topological order; each gene is a VM-list index.
 *
 * Model: earliest feasible non-preemptive VM gap; dependency finish plus
 * cross-VM transfer delay; execution cost = runtime * VM per-second price.
 * WorkflowSim execution can differ because of stage-in, dispatch and billing.
 *
 * Workspace arrays are owned by the caller. One evaluator instance is not
 * thread-safe; each planning algorithm/run must own its own instance.
 */
public final class UnifiedScheduleEvaluator {
    private final int[][] parentIndices;
    private final double[][] parentDelays;
    private final double[][] durations;
    private final double[] vmPrices;
    private final double[][] vmStarts;
    private final double[][] vmFinishes;
    private final int[] vmCounts;
    private final double[] taskFinishes;
    private final int[] taskVMs;
    private final int taskCount;
    private final int vmCount;

    public UnifiedScheduleEvaluator(
            int[][] parentIndices, double[][] parentDelays,
            double[][] durations, double[] vmPrices,
            double[][] vmStarts, double[][] vmFinishes,
            int[] vmCounts, double[] taskFinishes, int[] taskVMs) {
        if (durations == null || vmPrices == null || vmPrices.length == 0) {
            throw new IllegalArgumentException("Missing durations or VM prices");
        }
        taskCount = durations.length;
        vmCount = vmPrices.length;
        if (parentIndices == null || parentDelays == null ||
                parentIndices.length != taskCount || parentDelays.length != taskCount ||
                vmStarts == null || vmFinishes == null ||
                vmStarts.length != vmCount || vmFinishes.length != vmCount ||
                vmCounts == null || vmCounts.length != vmCount ||
                taskFinishes == null || taskFinishes.length != taskCount ||
                taskVMs == null || taskVMs.length != taskCount) {
            throw new IllegalArgumentException("Incorrect decoder workspace shape");
        }
        for (int v = 0; v < vmCount; v++) {
            if (!valid(vmPrices[v]) || vmStarts[v] == null || vmFinishes[v] == null ||
                    vmStarts[v].length < taskCount || vmFinishes[v].length < taskCount) {
                throw new IllegalArgumentException("Invalid VM workspace " + v);
            }
        }
        for (int k = 0; k < taskCount; k++) {
            if (durations[k] == null || durations[k].length != vmCount ||
                    parentIndices[k] == null || parentDelays[k] == null ||
                    parentIndices[k].length != parentDelays[k].length) {
                throw new IllegalArgumentException("Invalid task row " + k);
            }
            for (int v = 0; v < vmCount; v++) {
                if (!valid(durations[k][v])) {
                    throw new IllegalArgumentException("Invalid duration at task " + k + ", VM " + v);
                }
            }
            for (int j = 0; j < parentIndices[k].length; j++) {
                if (parentIndices[k][j] < 0 || parentIndices[k][j] >= k ||
                        !valid(parentDelays[k][j])) {
                    throw new IllegalArgumentException("Parent must precede task " + k);
                }
            }
        }
        this.parentIndices = parentIndices;
        this.parentDelays = parentDelays;
        this.durations = durations;
        this.vmPrices = vmPrices;
        this.vmStarts = vmStarts;
        this.vmFinishes = vmFinishes;
        this.vmCounts = vmCounts;
        this.taskFinishes = taskFinishes;
        this.taskVMs = taskVMs;
    }

    /** Returns [planning makespan, planning execution cost]. */
    public double[] evaluate(int[] assignment) {
        if (assignment == null || assignment.length != taskCount) {
            throw new IllegalArgumentException("Expected " + taskCount + " VM assignments");
        }
        Arrays.fill(vmCounts, 0);
        double makespan = 0.0;
        double cost = 0.0;
        for (int k = 0; k < taskCount; k++) {
            int vm = assignment[k];
            if (vm < 0 || vm >= vmCount) {
                throw new IllegalArgumentException("Invalid VM index at task " + k + ": " + vm);
            }
            double ready = 0.0;
            for (int j = 0; j < parentIndices[k].length; j++) {
                int parent = parentIndices[k][j];
                double available = taskFinishes[parent];
                if (taskVMs[parent] != vm) available += parentDelays[k][j];
                ready = Math.max(ready, available);
            }

            double duration = durations[k][vm];
            int used = vmCounts[vm];
            double start = ready;
            int insertAt = used;
            for (int i = 0; i < used; i++) {
                if (start + duration <= vmStarts[vm][i]) {
                    insertAt = i;
                    break;
                }
                start = Math.max(start, vmFinishes[vm][i]);
            }
            double finish = start + duration;
            if (insertAt < used) {
                System.arraycopy(vmStarts[vm], insertAt, vmStarts[vm], insertAt + 1, used - insertAt);
                System.arraycopy(vmFinishes[vm], insertAt, vmFinishes[vm], insertAt + 1, used - insertAt);
            }
            vmStarts[vm][insertAt] = start;
            vmFinishes[vm][insertAt] = finish;
            vmCounts[vm] = used + 1;
            taskFinishes[k] = finish;
            taskVMs[k] = vm;
            cost += duration * vmPrices[vm];
            makespan = Math.max(makespan, finish);
        }
        return new double[] {makespan, cost};
    }

    private static boolean valid(double value) {
        return !Double.isNaN(value) && !Double.isInfinite(value) && value >= 0.0;
    }
}
