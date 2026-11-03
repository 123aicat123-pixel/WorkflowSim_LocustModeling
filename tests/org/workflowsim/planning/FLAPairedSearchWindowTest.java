package org.workflowsim.planning;
public final class FLAPairedSearchWindowTest {
    private static void eq(int a,int b,String msg){
        if(a!=b)throw new AssertionError(msg+" expected "+b+" got "+a);
    }
    public static void main(String[] args){
        int early=0,late=0,full=0;
        eq(FLAPairedSearchWindow.diffusionGenerations(100),74,"DO total");
        for(int t=1;t<=100;t++){
            double tf=Math.sqrt(Math.sinh(t/100.0));
            int phase=tf<0.9?0:tf<=1.0?1:2;
            boolean a=FLAPairedSearchWindow.active(1,t,100,phase);
            boolean b=FLAPairedSearchWindow.active(2,t,100,phase);
            if(a!=(t<=74)||b!=(t>=27))
                throw new AssertionError("unexpected window membership at "+t);
            if(a)early++;
            if(b)late++;
            if(FLAPairedSearchWindow.active(0,t,100,phase))full++;
        }
        eq(early,74,"DO window");eq(late,74,"late window");eq(full,100,"full window");
        eq(14*early,1036,"counted local probes");
        eq(30*100-14*early,1964,"normal FLA child opportunities");
        eq(FLAPairedSearchWindow.activeGenerationCount(2,100),74,"count matching");
        try {
            FLAPairedSearchWindow.active(2,0,100,0);
            throw new AssertionError("bad generation accepted");
        }catch(IllegalArgumentException expected){}
        System.out.println("PASS 74 DO vs 74 shifted late generations, exactly 1036 charged local trials each");
    }
}
