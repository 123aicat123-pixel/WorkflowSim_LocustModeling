package org.workflowsim.planning;

import java.util.Random;
import org.workflowsim.planning.IntervalParetoCertificate.Relation;

/**
 * Deterministic property oracle for the conditional Pareto certificate.
 * This test makes NO coverage/calibration claim for unseen workflows.
 */
public final class IntervalParetoCertificatePropertyTest {
    private IntervalParetoCertificatePropertyTest() {}

    private static void check(boolean valid, String reason) {
        if (!valid) throw new AssertionError(reason);
    }
    private static boolean dominates(double[] a, double[] b) {
        return a[0] <= b[0] && a[1] <= b[1] &&
               (a[0] < b[0] || a[1] < b[1]);
    }
    private static double[] drawInside(Random rng, double[] estimate, double[] width) {
        return new double[] {
            estimate[0] * (1.0 + width[0] * (2.0 * rng.nextDouble() - 1.0)),
            estimate[1] * (1.0 + width[1] * (2.0 * rng.nextDouble() - 1.0))
        };
    }
    public static void main(String[] args) {
        Random rng = new Random(20261104L);
        int certain = 0;
        int abstain = 0;
        for (int t = 0; t < 20000; t++) {
            double[] a = {1.0 + 1000 * rng.nextDouble(),
                          1.0 + 1000 * rng.nextDouble()};
            double[] b = {1.0 + 1000 * rng.nextDouble(),
                          1.0 + 1000 * rng.nextDouble()};
            double[] wa = {0.001 + 0.249 * rng.nextDouble(),
                           0.001 + 0.249 * rng.nextDouble()};
            double[] wb = {0.001 + 0.249 * rng.nextDouble(),
                           0.001 + 0.249 * rng.nextDouble()};
            Relation relation = IntervalParetoCertificate.compare(a, b, wa, wb);
            if (relation == Relation.ABSTAIN) {
                abstain++;
                continue;
            }
            certain++;
            // Inside every predicted box, a strict certificate must remain sound.
            // Multiple deterministic draws are a regression check, NOT a proof.
            for (int j = 0; j < 8; j++) {
                double[] actualA = drawInside(rng, a, wa);
                double[] actualB = drawInside(rng, b, wb);
                check(IntervalParetoCertificate.jointlyCovers(a, actualA, wa),
                      "Generated A is outside declared box");
                check(IntervalParetoCertificate.jointlyCovers(b, actualB, wb),
                      "Generated B is outside declared box");
                if (relation == Relation.FIRST_DOMINATES)
                    check(dominates(actualA, actualB), "Unsound FIRST certificate");
                else
                    check(dominates(actualB, actualA), "Unsound SECOND certificate");
            }
        }
        check(certain > 0 && abstain > 0, "Property oracle lacked both decision types");

        // Counterexample: a nominally certain prediction can be wrong when
        // the observed truth falls OUTSIDE its assumed intervals.
        double[] predictedA = {10, 10}, predictedB = {20, 20};
        double[] widths = {0.05, 0.05};
        check(IntervalParetoCertificate.compare(predictedA, predictedB, widths, widths)
              == Relation.FIRST_DOMINATES, "Expected nominal certificate");
        double[] actualA = {30, 10}, actualB = {20, 20};
        check(!IntervalParetoCertificate.jointlyCovers(predictedA, actualA, widths),
              "Coverage violation was missed");
        check(!dominates(actualA, actualB), "Counterexample must reverse certainty");

        System.out.println("PASS IntervalParetoCertificatePropertyTest: 20000 seeded boxes, "
                           + certain + " certifications, " + abstain
                           + " abstentions; outside-interval failure detected");
    }
}
