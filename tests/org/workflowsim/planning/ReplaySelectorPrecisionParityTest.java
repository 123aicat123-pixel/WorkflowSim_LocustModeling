package org.workflowsim.planning;

import java.io.BufferedReader;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * Reflection-only contract test for the real (private) Java prospective selector.
 * No simulated objectives are supplied, and all data are deterministic.
 */
public final class ReplaySelectorPrecisionParityTest {
    private ReplaySelectorPrecisionParityTest() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("Usage: ReplaySelectorPrecisionParityTest FIXTURE.csv");
        }
        Class<?> experiment = Class.forName("org.workflowsim.examples.planning.FLAResearchExperiment");
        Class<?> candidate = Class.forName("org.workflowsim.examples.planning.FLAResearchExperiment$Candidate");
        Constructor<?> constructor = candidate.getDeclaredConstructor(double[].class, Map.class);
        constructor.setAccessible(true);
        Method selection = experiment.getDeclaredMethod("budgetedPlannedCoverage", List.class, int.class);
        selection.setAccessible(true);
        Method scalarSelection = experiment.getDeclaredMethod("budgetedScalarSweep", List.class, int.class);
        scalarSelection.setAccessible(true);
        Field assignment = candidate.getDeclaredField("assignment");
        assignment.setAccessible(true);

        Map<String,List<Object>> cases = new LinkedHashMap<>();
        try (BufferedReader reader = Files.newBufferedReader(Paths.get(args[0]), StandardCharsets.UTF_8)) {
            String header = reader.readLine();
            if (!"case,id,m,c".equals(header)) throw new IllegalArgumentException("Unexpected fixture schema " + header);
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.trim().isEmpty()) continue;
                String[] cols = line.split(",", -1);
                if (cols.length != 4) throw new IllegalArgumentException("Malformed row: " + line);
                int id = Integer.parseInt(cols[1]);
                Map<Integer,Integer> mapping = new TreeMap<>();
                mapping.put(1, id);
                Object item = constructor.newInstance(new double[]{
                    Double.parseDouble(cols[2]), Double.parseDouble(cols[3])
                }, mapping);
                cases.computeIfAbsent(cols[0], ignored -> new ArrayList<>()).add(item);
            }
        }
        if (cases.size() != 4) throw new IllegalStateException("Expected four stress fixtures, got " + cases.size());
        for (Map.Entry<String,List<Object>> group : cases.entrySet()) {
            for (int k : new int[]{8,16,24,32}) {
                @SuppressWarnings("unchecked")
                List<Object> chosen = (List<Object>) selection.invoke(null, group.getValue(), k);
                if (chosen.size() != k) throw new IllegalStateException("Wrong selected count " + k);
                StringBuilder ids = new StringBuilder();
                for (Object item : chosen) {
                    @SuppressWarnings("unchecked")
                    Map<Integer,Integer> mapping = (Map<Integer,Integer>) assignment.get(item);
                    if (ids.length() != 0) ids.append(",");
                    ids.append(mapping.get(1));
                }
                System.out.println("PARITY|" + group.getKey() + "|" + k + "|" + ids);
                @SuppressWarnings("unchecked")
                List<Object> swept = (List<Object>) scalarSelection.invoke(null, group.getValue(), k);
                if(swept.size()!=k)throw new IllegalStateException("Wrong scalar sweep size "+k);
                StringBuilder scalarIds=new StringBuilder();
                for(Object item:swept) {
                    @SuppressWarnings("unchecked")
                    Map<Integer,Integer> mapping = (Map<Integer,Integer>) assignment.get(item);
                    if(scalarIds.length()!=0)scalarIds.append(",");
                    scalarIds.append(mapping.get(1));
                }
                System.out.println("PARITYSWEEP|" + group.getKey() + "|" + k + "|" + scalarIds);
            }
        }
    }
}
