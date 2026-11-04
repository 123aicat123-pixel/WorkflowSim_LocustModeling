package org.workflowsim.planning;

import java.util.HashMap;
import java.util.Map;

/**
 * Research-only, opt-in safe decision adapter for two-objective minimization.
 * The box certificates are CONDITIONAL on independently justified coverage;
 * a READY score remains a model estimate, never an actual simulator oracle.
 * No optimizer is changed by instantiating this class.
 */
public final class FailClosedFidelityGate {
    public enum Kind {
        CONDITIONAL_FIRST_DOMINATES, CONDITIONAL_SECOND_DOMINATES,
        READY_ESTIMATES_AVAILABLE, KEEP_BOTH
    }
    public interface ReadyDecoder {
        double[] evaluate(String canonicalAssignmentId);
    }
    public static final class Outcome {
        public final Kind kind;
        public final double[] readyFirst;
        public final double[] readySecond;
        public final String reason;
        private Outcome(Kind kind, double[] first, double[] second, String reason) {
            this.kind = kind;
            this.readyFirst = first == null ? null : first.clone();
            this.readySecond = second == null ? null : second.clone();
            this.reason = reason;
        }
    }
    private final int maxReadyCalls;
    private int readyCalls;
    private int cacheHits;
    private final Map<String,double[]> readyCache = new HashMap<>();

    public FailClosedFidelityGate(int maxReadyCalls) {
        if (maxReadyCalls < 0) throw new IllegalArgumentException("Negative READY budget");
        this.maxReadyCalls = maxReadyCalls;
    }
    private static boolean point(double[] x) {
        return x != null && x.length == 2 && Double.isFinite(x[0]) &&
                Double.isFinite(x[1]) && x[0] > 0 && x[1] > 0;
    }
    private static boolean width(double[] w) {
        return w != null && w.length == 2 && Double.isFinite(w[0]) &&
                Double.isFinite(w[1]) && w[0] >= 0 && w[1] >= 0 &&
                w[0] < 1 && w[1] < 1;
    }
    private static Outcome keep(String why) {
        return new Outcome(Kind.KEEP_BOTH, null, null, why);
    }
    public int readyCalls() { return readyCalls; }
    public int cacheHits() { return cacheHits; }
    public int cachedAssignments() { return readyCache.size(); }
    public int readyBudget() { return maxReadyCalls; }

    /**
     * A width without independent external evidence must NEVER certify a pair.
     * When comparison abstains, obtain both READY model estimates if budget
     * permits; if not, preserve both solutions (never silently prune).
     * Even READY_ESTIMATES_AVAILABLE is NOT a true Pareto certificate.
     * Canonical IDs must uniquely encode full TaskID->VM assignments.
     */
    public Outcome assess(String firstId, String secondId, double[] first,
                          double[] second, double[] firstWidth,
                          double[] secondWidth, boolean evidenceAccepted,
                          ReadyDecoder decoder) {
        if (firstId == null || firstId.isEmpty() ||
                secondId == null || secondId.isEmpty())
            throw new IllegalArgumentException("Canonical IDs required");
        if (firstId.equals(secondId)) return keep("identical assignment");
        if (!point(first) || !point(second)) return keep("invalid cheap objectives");
        if (evidenceAccepted && width(firstWidth) && width(secondWidth)) {
            IntervalParetoCertificate.Relation relation =
                IntervalParetoCertificate.compare(first, second, firstWidth, secondWidth);
            if (relation == IntervalParetoCertificate.Relation.FIRST_DOMINATES)
                return new Outcome(Kind.CONDITIONAL_FIRST_DOMINATES, null, null,
                        "conditional on both externally supported boxes covering truth");
            if (relation == IntervalParetoCertificate.Relation.SECOND_DOMINATES)
                return new Outcome(Kind.CONDITIONAL_SECOND_DOMINATES, null, null,
                        "conditional on both externally supported boxes covering truth");
        }
        if (decoder == null) return keep("READY callback unavailable");
        int needed = (readyCache.containsKey(firstId) ? 0 : 1) +
                     (readyCache.containsKey(secondId) ? 0 : 1);
        if (needed > maxReadyCalls - readyCalls)
            return keep("insufficient READY budget for complete pair");
        try {
            double[] highFirst = readyCache.get(firstId);
            if (highFirst != null) cacheHits++;
            else highFirst = computeReady(firstId, decoder);
            if (!point(highFirst)) return keep("READY model returned invalid objectives");
            double[] highSecond = readyCache.get(secondId);
            if (highSecond != null) cacheHits++;
            else highSecond = computeReady(secondId, decoder);
            if (!point(highSecond)) return keep("READY model returned invalid objectives");
            return new Outcome(Kind.READY_ESTIMATES_AVAILABLE, highFirst, highSecond,
                    "higher-fidelity MODEL estimates only; no true dominance certification");
        } catch (RuntimeException failed) {
            return keep("READY callback failed; preserve both candidates");
        }
    }
    private double[] computeReady(String id, ReadyDecoder decoder) {
        // Count attempted physical calls even if callback throws or returns garbage.
        readyCalls++;
        double[] result = decoder.evaluate(id);
        if (point(result)) {
            readyCache.put(id, result.clone());
            return result.clone();
        }
        return null;
    }
}
