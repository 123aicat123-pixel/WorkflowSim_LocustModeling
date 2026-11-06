package org.workflowsim.examples.planning;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.TreeMap;

/**
 * Research-only passive read-out of ENTIRE unique FLA visited mapping history.
 * No decoder, simulator, actual label, or objective evaluation is called here.
 * A deterministic 64-sample fingerprint is required to match the PRIOR original
 * original true-replay frozen pool, otherwise all history contrasts fail closed.
 */
public final class FLAVisitedFullHistorySnapshot {
    private FLAVisitedFullHistorySnapshot() { }
    private static String canonical(Map<Integer,Integer> mapping) {
        StringBuilder b=new StringBuilder();
        for(Map.Entry<Integer,Integer> e:new TreeMap<>(mapping).entrySet()) {
            if(b.length()>0)b.append('|');
            b.append(e.getKey()).append(':').append(e.getValue());
        }
        return b.toString();
    }
    private static String sha(String text) throws Exception {
        byte[] sum=MessageDigest.getInstance("SHA-256").digest(
                text.getBytes(StandardCharsets.UTF_8));
        StringBuilder b=new StringBuilder();
        for(byte v:sum)b.append(String.format(Locale.ROOT,"%02x",v&0xff));
        return b.toString();
    }
    public static void run(String workflow,long seed,Path prefix,
            List<Map<Integer,Integer>> visited,int evaluations) throws Exception {
        if(evaluations!=3030 || visited==null||visited.size()<64)
            throw new IllegalStateException("Incomplete real full FLA candidate history");
        Set<String> seen=new HashSet<>();
        for(Map<Integer,Integer> map:visited) {
            if(map==null||map.isEmpty()||!seen.add(canonical(map)))
                throw new IllegalStateException("Duplicate/missing original search mapping");
        }
        Path all=Paths.get(prefix+"_pool64_entire_visit_hashes.csv");
        Path sample=Paths.get(prefix+"_pool64_original_sample_hashes.csv");
        try(BufferedWriter w=Files.newBufferedWriter(all,StandardCharsets.UTF_8)) {
            w.write("workflow,seed,unique_visit_index,mapping_sha256\n");
            for(int i=0;i<visited.size();i++) {
                w.write(String.format(Locale.ROOT,"%s,%d,%d,%s%n",workflow,
                    seed,i+1,sha(canonical(visited.get(i)))));
            }
        }
        List<Map<Integer,Integer>> perm=new ArrayList<>(visited);
        Collections.shuffle(perm,new Random(seed ^ 0x6A09E667F3BCC909L));
        try(BufferedWriter w=Files.newBufferedWriter(sample,StandardCharsets.UTF_8)) {
            w.write("workflow,seed,pool_index,mapping_sha256\n");
            for(int i=0;i<64;i++) {
                w.write(String.format(Locale.ROOT,"%s,%d,%d,%s%n",workflow,
                    seed,i+1,sha(canonical(perm.get(i)))));
            }
        }
        System.out.printf(Locale.ROOT,
             "HISTORY_ONLY_PASS workflow=%s seed=%d evaluations=%d unique=%d sample=64 simulator_replays=0%n",
             workflow,seed,evaluations,visited.size());
    }
}
