package org.workflowsim.planning;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Stream;

/**
 * Read-only Java greedy-source validation on original WorkflowSim records.
 * Real labels are read only AFTER all predicted candidate selections are fixed.
 * Not a new simulator, not FLA or NSGA-II integration.
 */
public final class GreedyStagedParetoSourceAudit {
    private GreedyStagedParetoSourceAudit(){}
    private static final String[] POLICIES={
        "all_vm0","all_vm12","round_robin","stride7",
        "evenodd_vm0_vm12","block4_vm0_vm12","four_vm_round","four_vm_block5",
        "vm0_vm12_skew75","vm12_vm15_skew75","prime_step5","prime_step11",
        "hash_seed17","hash_seed97","monotonic_vm16","reverse_monotonic_vm16"};

    private static Map<String,String> fields(String line,String[] header) {
        String[] parts=line.split(",",-1);
        if(parts.length!=header.length)
            throw new IllegalArgumentException("Unquoted input expected "+header.length+" fields got "+parts.length);
        Map<String,String> map=new HashMap<>();
        for(int i=0;i<header.length;i++)map.put(header[i],parts[i]);
        return map;
    }
    private static String fmt(int[] selected) {
        int[] sorted=selected.clone();
        Arrays.sort(sorted);
        StringBuilder b=new StringBuilder();
        for(int i:sorted) {
            if(b.length()>0)b.append('|');
            b.append(i+1);
        }
        return b.toString();
    }
    private static double number(Map<String,String> map,String key) {
        double x=Double.parseDouble(map.get(key));
        if(!Double.isFinite(x)||x<=0)throw new IllegalArgumentException("Invalid source "+key+" "+x);
        return x;
    }
    private static void one(Path file,BufferedWriter out) throws Exception {
        List<String> lines=Files.readAllLines(file,StandardCharsets.UTF_8);
        if(lines.size()!=17)throw new AssertionError("Must be exactly 16 original genotypes");
        String[] header=lines.get(0).split(",",-1);
        Map<String,Map<String,String>> byPolicy=new HashMap<>();
        for(int j=1;j<lines.size();j++) {
            Map<String,String> row=fields(lines.get(j),header);
            String policy=row.get("mapping_policy");
            if(byPolicy.put(policy,row)!=null)throw new AssertionError("Duplicate genotype");
        }
        if(byPolicy.size()!=16||!byPolicy.keySet().containsAll(Arrays.asList(POLICIES)))
            throw new AssertionError("Missing original placement genotypes");
        String dag=byPolicy.get(POLICIES[0]).get("workflow");
        String speed=byPolicy.get(POLICIES[0]).get("vm_profile");
        if(!Arrays.asList("CyberShake_30","Epigenomics_46","Montage_50").contains(dag)||
           !Arrays.asList("default","staggered").contains(speed))
            throw new AssertionError("Unregistered original source "+dag+" "+speed);
        double[][] old=new double[16][2],ready=new double[16][2];
        for(int i=0;i<16;i++) {
            Map<String,String> r=byPolicy.get(POLICIES[i]);
            if(!dag.equals(r.get("workflow"))||!speed.equals(r.get("vm_profile"))||
               !"1501".equals(r.get("seed")))
                throw new AssertionError("Original source provenance mismatch");
            old[i][0]=number(r,"old_planned_makespan");
            old[i][1]=number(r,"old_planned_cost");
            ready[i][0]=number(r,"ready_planned_makespan");
            ready[i][1]=number(r,"ready_planned_cost");
        }
        // Selection uses only modeled objectives and a common OLD-only reference.
        double maxM=0,maxC=0;
        for(double[] q:old) {
            maxM=Math.max(maxM,q[0]);
            maxC=Math.max(maxC,q[1]);
        }
        double[] reference={1.5*maxM+1e-6,1.5*maxC+1e-6};
        Map<String,int[]> fixed=new LinkedHashMap<>();
        for(int k:new int[]{2,4}) {
            fixed.put("old-"+k,GreedyStagedParetoSelector.select(old,k,reference).selected);
            fixed.put("ready-"+k,GreedyStagedParetoSelector.select(ready,k,reference).selected);
            for(int t:new int[]{4,8}) {
                final int[] calls={0};
                GreedyStagedParetoSelector.Refined x=
                    GreedyStagedParetoSelector.refine(old,i->{
                        calls[0]++;
                        return ready[i].clone();
                    },t,k,reference);
                if(x.expensiveCalls!=t||calls[0]!=t||
                        x.screened.length!=t||x.selected.length!=k)
                    throw new AssertionError("READY budget violation");
                fixed.put("stage-screen-"+k+"-"+t,x.screened);
                fixed.put("stage-final-"+k+"-"+t,x.selected);
            }
        }
        // Truth is used ONLY after all selectors have completed.
        double[][] truth=new double[16][2];
        double tm=0,tc=0;
        for(int i=0;i<16;i++) {
            Map<String,String> r=byPolicy.get(POLICIES[i]);
            truth[i][0]=number(r,"actual_makespan");
            truth[i][1]=number(r,"actual_cost");
            tm=Math.max(tm,truth[i][0]);
            tc=Math.max(tc,truth[i][1]);
        }
        double[] truthref={1.5*tm+1e-6,1.5*tc+1e-6};
        int[] all=new int[16];
        for(int i=0;i<16;i++)all[i]=i;
        double full=GreedyStagedParetoSelector.normalizedHV(truth,all,truthref);
        if(full<=0)throw new AssertionError("Zero real fixed-16 HV");
        for(int k:new int[]{2,4}){
            for(int t:new int[]{4,8}){
                int[] oi=fixed.get("old-"+k),ri=fixed.get("ready-"+k),
                      si=fixed.get("stage-final-"+k+"-"+t),
                      screen=fixed.get("stage-screen-"+k+"-"+t);
                double oldHv=100*GreedyStagedParetoSelector.normalizedHV(truth,oi,truthref)/full;
                double readyHv=100*GreedyStagedParetoSelector.normalizedHV(truth,ri,truthref)/full;
                double stageHv=100*GreedyStagedParetoSelector.normalizedHV(truth,si,truthref)/full;
                out.write(String.format(Locale.ROOT,
                    "%s,%s,%d,%d,%s,%s,%s,%s,%d,%.12f,%.12f,%.12f,%.12f,%.12f%n",
                    dag,speed,k,t,fmt(oi),fmt(ri),fmt(screen),fmt(si),t,
                    oldHv,readyHv,stageHv,stageHv-readyHv,stageHv-oldHv));
            }
        }
    }
    public static void main(String[] args) throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("Usage: SourceAudit ARTIFACT_ROOT OUT_CSV");
        List<Path> files=new ArrayList<>();
        try(Stream<Path> stream=Files.walk(Paths.get(args[0]))) {
            stream.filter(p->p.getFileName().toString().equals("same_mapping_true_replays.csv"))
                  .forEach(files::add);
        }
        files.sort(Path::compareTo);
        if(files.size()!=6)throw new AssertionError("Require six immutable original DAX/speed artifacts");
        Path out=Paths.get(args[1]);
        if(out.getParent()!=null)Files.createDirectories(out.getParent());
        try(BufferedWriter writer=Files.newBufferedWriter(out,StandardCharsets.UTF_8)){
            writer.write("workflow,vm_speed,K,T,old_indices,full_ready_indices,"
                +"screen_indices,staged_indices,ready_calls,"
                +"old_real_hv15_pct,full_ready_real_hv15_pct,"
                +"staged_real_hv15_pct,staged_minus_ready_pp,staged_minus_old_pp\n");
            for(Path p:files)one(p,writer);
        }
        System.out.println("PASS GreedyStagedParetoSourceAudit: 6 frozen real simulator blocks, 24 model-only greedy decision cells, exactly T READY calls per cell");
    }
}
