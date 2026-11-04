package org.workflowsim.planning;

/**
 * Pure conservative 2D uncertainty-box Pareto comparator.
 *
 * A certificate is conditional: it is safe only if BOTH true objective pairs
 * actually fall within their declared predicted error boxes. Widths are
 * parameters supplied by the caller; there is NO automatic calibration,
 * no simulator peek and no default optimizer integration.
 */
public final class IntervalParetoCertificate {
    private IntervalParetoCertificate() {}

    public enum Relation { FIRST_DOMINATES, SECOND_DOMINATES, ABSTAIN }

    private static void requirePoint(double[] x) {
        if(x==null||x.length!=2||!Double.isFinite(x[0])||
           !Double.isFinite(x[1])||x[0]<=0||x[1]<=0)
            throw new IllegalArgumentException("Finite positive 2D objectives required");
    }
    private static void requireWidth(double[] x) {
        if(x==null||x.length!=2||!Double.isFinite(x[0])||
           !Double.isFinite(x[1])||x[0]<0||x[1]<0||x[0]>=1||x[1]>=1)
            throw new IllegalArgumentException("Finite two-coordinate widths in [0,1) required");
    }

    public static Relation compare(double[] first, double[] second,
                                   double[] firstWidth, double[] secondWidth) {
        requirePoint(first);requirePoint(second);
        requireWidth(firstWidth);requireWidth(secondWidth);
        boolean firstCertain=true,secondCertain=true;
        for(int i=0;i<2;i++) {
            firstCertain &= first[i]*(1+firstWidth[i]) <
                            second[i]*(1-secondWidth[i]);
            secondCertain &= second[i]*(1+secondWidth[i]) <
                             first[i]*(1-firstWidth[i]);
        }
        if(firstCertain&&secondCertain)
            throw new IllegalStateException("Numerically impossible bidirectional certificate");
        if(firstCertain)return Relation.FIRST_DOMINATES;
        if(secondCertain)return Relation.SECOND_DOMINATES;
        return Relation.ABSTAIN;
    }

    public static boolean jointlyCovers(double[] prediction,double[] actual,
                                        double[] widths) {
        requirePoint(prediction);requirePoint(actual);requireWidth(widths);
        return actual[0]>=prediction[0]*(1-widths[0]) &&
               actual[0]<=prediction[0]*(1+widths[0]) &&
               actual[1]>=prediction[1]*(1-widths[1]) &&
               actual[1]<=prediction[1]*(1+widths[1]);
    }
}
