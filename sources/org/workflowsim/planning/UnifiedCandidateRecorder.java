package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import org.workflowsim.CondorVM;
import org.workflowsim.Task;

/**
 * Identical, passive observation of EVERY successful objective evaluation.
 * Does not affect fitness, mutation, selection, population, or final commitment.
 * A capture is scoped to the calling thread and must be opened by the driver.
 * Task identifiers and VM identifiers (NOT genotype indices) are serialized.
 */
public final class UnifiedCandidateRecorder {
    private static final ThreadLocal<Session> CURRENT = new ThreadLocal<>();
    private UnifiedCandidateRecorder() { }

    public static final class Event {
        public final long evaluation;
        public final String phase;
        public final double makespan, cost;
        public final Map<Integer, Integer> assignment;
        private Event(long evaluation, String phase, double m, double c,
                Map<Integer, Integer> assignment) {
            this.evaluation = evaluation;
            this.phase = phase;
            this.makespan = m;
            this.cost = c;
            this.assignment = Collections.unmodifiableMap(assignment);
        }
    }

    public static final class Capture {
        private final List<Event> events;
        private final List<Event> unique;
        private final List<Event> plannedFront;
        private Capture(List<Event> events, List<Event> unique, List<Event> front) {
            this.events = Collections.unmodifiableList(events);
            this.unique = Collections.unmodifiableList(unique);
            this.plannedFront = Collections.unmodifiableList(front);
        }
        public int evaluationCount() { return events.size(); }
        public int distinctAssignments() { return unique.size(); }
        public int plannedNondominatedAssignments() { return plannedFront.size(); }
        public List<Event> events() { return events; }
        /** All unique evaluated assignments, including planning-dominated ones. */
        public List<Event> uniqueEvents() { return unique; }
        public List<Event> plannedFront() { return plannedFront; }
        public List<double[]> frontPoints() {
            List<double[]> out = new ArrayList<>();
            for (Event e : plannedFront) out.add(new double[]{e.makespan, e.cost});
            return out;
        }
        public List<Map<Integer, Integer>> frontAssignments() {
            List<Map<Integer, Integer>> out = new ArrayList<>();
            for (Event e : plannedFront) out.add(e.assignment);
            return out;
        }
    }

    private static final class Session {
        final long budget;
        final List<Event> history = new ArrayList<>();
        final LinkedHashMap<Map<Integer, Integer>, Event> distinct = new LinkedHashMap<>();
        String phase = "default";
        Session(long budget) { this.budget = budget; }
    }

    public static void begin(long maxEvaluations) {
        if (maxEvaluations < 1) throw new IllegalArgumentException("Invalid evaluation cap");
        if (CURRENT.get() != null) throw new IllegalStateException("Nested capture not allowed");
        CURRENT.set(new Session(maxEvaluations));
    }

    public static void phase(String label) {
        Session session = CURRENT.get();
        if (session == null) throw new IllegalStateException("Capture not started");
        if (label == null || label.trim().isEmpty() || label.contains(","))
            throw new IllegalArgumentException("Invalid phase");
        session.phase = label;
    }

    public static void abort() { CURRENT.remove(); }

    public static void record(List<Task> tasks, List<CondorVM> vms,
            int[] genotype, double makespan, double cost) {
        Session s = CURRENT.get();
        if (s == null) return; // disabled by default, no effect on existing experiments
        if (tasks == null || vms == null || genotype == null || tasks.size() != genotype.length)
            throw new IllegalStateException("Invalid decoded genotype");
        if (!Double.isFinite(makespan) || !Double.isFinite(cost)
                || makespan < 0 || cost < 0)
            throw new IllegalStateException("Invalid evaluated objective pair");
        if (s.history.size() >= s.budget)
            throw new IllegalStateException("Objective evaluation cap exceeded: " + s.budget);
        Map<Integer, Integer> mapping = new TreeMap<>();
        for (int i = 0; i < genotype.length; i++) {
            int v = genotype[i];
            if (v < 0 || v >= vms.size()) throw new IllegalStateException("Invalid VM index");
            Integer previous = mapping.put(tasks.get(i).getCloudletId(), vms.get(v).getId());
            if (previous != null) throw new IllegalStateException("Duplicate task ID");
        }
        Event e = new Event(s.history.size() + 1L, s.phase, makespan, cost, mapping);
        Event prior = s.distinct.get(e.assignment);
        if (prior != null && (!near(prior.makespan, makespan) || !near(prior.cost, cost)))
            throw new IllegalStateException("Same assignment has inconsistent planned objectives."
                    + " Earlier=" + Arrays.toString(new double[]{prior.makespan, prior.cost})
                    + " now=" + Arrays.toString(new double[]{makespan, cost}));
        s.history.add(e);
        if (prior == null) s.distinct.put(e.assignment, e);
    }

    private static boolean near(double a, double b) {
        return Math.abs(a-b) <= 1e-8 * Math.max(1.0, Math.max(Math.abs(a), Math.abs(b)));
    }

    public static Capture end() {
        Session s = CURRENT.get();
        if (s == null) throw new IllegalStateException("No capture active");
        CURRENT.remove();
        if (s.history.isEmpty()) throw new IllegalStateException("No objective evaluations captured");
        List<Event> unique = new ArrayList<>(s.distinct.values());
        List<Event> front = new ArrayList<>();
        for (int i = 0; i < unique.size(); i++) {
            Event a = unique.get(i);
            boolean dominated = false;
            for (int j = 0; j < unique.size(); j++) {
                if (i == j) continue;
                Event b = unique.get(j);
                if (b.makespan <= a.makespan && b.cost <= a.cost
                    && (b.makespan < a.makespan || b.cost < a.cost)) {
                    dominated = true;
                    break;
                }
            }
            if (!dominated) front.add(a);
        }
        front.sort(Comparator.comparingDouble((Event e) -> e.makespan)
                .thenComparingDouble(e -> e.cost)
                .thenComparingLong(e -> e.evaluation));
        return new Capture(new ArrayList<>(s.history), unique, front);
    }
}