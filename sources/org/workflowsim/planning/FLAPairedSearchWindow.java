package org.workflowsim.planning;

/** No RNG and no fitness access: exact DO and equal-count shifted late window. */
public final class FLAPairedSearchWindow {
    private FLAPairedSearchWindow(){}
    public static int diffusionGenerations(int generations){
        if(generations<1)throw new IllegalArgumentException("Positive generations required");
        int c=0;
        for(int t=1;t<=generations;t++)
            if(Math.sqrt(Math.sinh((double)t/generations))<0.9)c++;
        return c;
    }
    public static int activeGenerationCount(int window,int generations){
        if(window<0||window>2||generations<1)
            throw new IllegalArgumentException("Invalid window");
        return window==0?generations:diffusionGenerations(generations);
    }
    public static boolean active(int window,int t,int generations,int phase){
        if(window<0||window>2||generations<1||t<1||t>generations||phase<0||phase>2)
            throw new IllegalArgumentException("Invalid window/phase");
        return window==0 || (window==1 ? phase==0 :
                t>generations-diffusionGenerations(generations));
    }
}
