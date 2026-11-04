package org.workflowsim.planning;

import java.util.concurrent.atomic.AtomicInteger;
import org.workflowsim.planning.FailClosedFidelityGate.Kind;
import org.workflowsim.planning.FailClosedFidelityGate.Outcome;

/** Deterministic research component checks, NOT a cross-family coverage claim. */
public final class FailClosedFidelityGateTest {
    private FailClosedFidelityGateTest() {}
    private static void eq(boolean ok, String reason) {
        if (!ok) throw new AssertionError(reason);
    }
    private static final double[] A = {10,20};
    private static final double[] B = {30,40};
    private static final double[] W = {0.05,0.05};
    public static void main(String[] args) {
        AtomicInteger calls = new AtomicInteger();
        FailClosedFidelityGate.ReadyDecoder decoder = id -> {
            calls.incrementAndGet();
            return "a".equals(id) ? new double[]{11,22} :
                   "b".equals(id) ? new double[]{29,42} : new double[]{50,60};
        };
        FailClosedFidelityGate noBudget = new FailClosedFidelityGate(0);
        eq(noBudget.assess("a","b",A,B,W,W,false,decoder).kind == Kind.KEEP_BOTH,
           "Unverified boxes without budget must abstain");
        eq(calls.get()==0, "No model should run when budget is exhausted");
        eq(noBudget.assess("a","b",A,B,W,W,true,decoder).kind ==
           Kind.CONDITIONAL_FIRST_DOMINATES, "Separated supported boxes should certify conditionally");
        eq(noBudget.readyCalls()==0, "Pure interval decision must not spend READY");
        eq(noBudget.assess("a","b",new double[]{30,40},A,W,W,true,decoder).kind ==
           Kind.CONDITIONAL_SECOND_DOMINATES, "Reverse box order should certify second");
        FailClosedFidelityGate budget1 = new FailClosedFidelityGate(1);
        eq(budget1.assess("a","b",A,B,W,W,false,decoder).kind == Kind.KEEP_BOTH,
           "Insufficient pair budget must fail closed before partial evaluation");
        eq(budget1.readyCalls()==0, "No partial pair expenditure");
        FailClosedFidelityGate budget2 = new FailClosedFidelityGate(2);
        Outcome first = budget2.assess("a","b",A,B,W,W,false,decoder);
        eq(first.kind==Kind.READY_ESTIMATES_AVAILABLE,"READY is model evidence, not a certificate");
        eq(first.readyFirst[0]==11 && first.readySecond[0]==29,"Wrong READY returned values");
        first.readyFirst[0] = 999;
        eq(budget2.readyCalls()==2 && calls.get()==2,"Each distinct READY assignment counted");
        Outcome repeat = budget2.assess("a","b",A,B,null,W,false,decoder);
        eq(repeat.kind==Kind.READY_ESTIMATES_AVAILABLE && repeat.readyFirst[0]==11,
           "Cache / defensive output copies failed");
        eq(budget2.readyCalls()==2 && budget2.cacheHits()==2,
           "Repeated pair must not issue new READY calls");
        eq(budget2.assess("a","c",A,B,W,W,false,decoder).kind==Kind.KEEP_BOTH,
           "Exhausted READY budget must preserve both");
        eq(budget2.readyCalls()==2,"Budget was exceeded");
        FailClosedFidelityGate close = new FailClosedFidelityGate(2);
        eq(close.assess("a","b",A,new double[]{10.1,20.1},W,W,true,decoder).kind==
           Kind.READY_ESTIMATES_AVAILABLE,"Overlapping boxes must request READY if possible");
        FailClosedFidelityGate invalid = new FailClosedFidelityGate(0);
        eq(invalid.assess("a","b",A,B,new double[]{Double.NaN,0},W,true,decoder).kind==
           Kind.KEEP_BOTH,"Invalid calibration geometry must never certify");
        eq(invalid.assess("a","b",new double[]{Double.NaN,1},B,W,W,true,decoder).kind==
           Kind.KEEP_BOTH,"Invalid predictions must never certify");
        FailClosedFidelityGate broken = new FailClosedFidelityGate(2);
        eq(broken.assess("a","b",A,B,W,W,false,id -> {
            throw new IllegalStateException("backend error");
        }).kind==Kind.KEEP_BOTH,"Decoder failure must preserve both");
        eq(broken.readyCalls()==1,"Failed physical READY attempt must be counted");
        eq(broken.assess("a","b",A,B,W,W,false,id -> new double[]{Double.NaN,2}).kind==
           Kind.KEEP_BOTH,"Invalid READY observations must not be accepted");
        eq(broken.readyCalls()==1,"Insufficient remaining quota must avoid partial pair calls");
        FailClosedFidelityGate invalidReady = new FailClosedFidelityGate(2);
        eq(invalidReady.assess("a","b",A,B,W,W,false,id -> new double[]{Double.NaN,2}).kind==
           Kind.KEEP_BOTH,"Invalid READY score must fail closed");
        eq(invalidReady.readyCalls()==1, "Invalid attempted READY score must consume one call");
        eq(noBudget.assess("a","a",A,A,W,W,true,decoder).kind==Kind.KEEP_BOTH,
           "Identical canonical assignments must not be double-pruned");
        System.out.println("PASS FailClosedFidelityGateTest: conditional geometry, READY fallback, " +
                           "cache, insufficient budgets, invalid widths and decoder failure");
    }
}
