package org.workflowsim.planning;

/** Deterministic componentwise robust objective arithmetic and invalid-parameter checks. */
public final class DualModelScheduleObjectiveTest {
    private static void eq(String name,double actual,double expected) {
        if(!Double.isFinite(actual)||Math.abs(actual-expected)>1e-9)
            throw new AssertionError(name+" expected "+expected+" got "+actual);
    }
    public static void main(String[] args) {
        double[] mean=DualModelScheduleObjective.combine(DualModelScheduleObjective.Mode.MEAN,
                21,18,22,18);
        eq("mean makespan",mean[0],21.5);
        eq("mean cost",mean[1],18);
        double[] worst=DualModelScheduleObjective.combine(DualModelScheduleObjective.Mode.WORST,
                21,19,22,18);
        eq("worst makespan",worst[0],22);
        eq("worst cost",worst[1],19);
        if(DualModelScheduleObjective.parseMode("mean")!=DualModelScheduleObjective.Mode.MEAN)
            throw new AssertionError("Parse mean");
        if(DualModelScheduleObjective.parseMode("worst")!=DualModelScheduleObjective.Mode.WORST)
            throw new AssertionError("Parse worst");
        boolean rejected=false;
        try {DualModelScheduleObjective.combine(DualModelScheduleObjective.Mode.MEAN,
                21,18,Double.NaN,18);}
        catch(IllegalArgumentException expected){rejected=true;}
        if(!rejected)throw new AssertionError("Nonfinite models not rejected");
        rejected=false;
        try {DualModelScheduleObjective.parseMode("oracle");}
        catch(IllegalArgumentException expected){rejected=true;}
        if(!rejected)throw new AssertionError("Unregistered mode not rejected");
        System.out.println("PASS DualModelScheduleObjectiveTest: mean/worst, cost separation, reject invalid modes");
    }
}
