package org.workflowsim.planning;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import org.cloudbus.cloudsim.Consts;
import org.workflowsim.CondorVM;
import org.workflowsim.FileItem;
import org.workflowsim.Task;
import org.workflowsim.utils.Parameters;

/**
 * DAG-Pareto-FLA (research candidate v0.1): MULTIOBJECTIVE DISCRETE ADAPTATION,
 * NOT an equation-faithful reimplementation of the continuous original FLA.
 *
 * Retains FLA's two groups and DO/EO/SSO time windows. Uses proposed VM-gene
 * update rules, a DAG upward-rank importance vector, and a nondominated archive.
 * All methods of this class are intentionally separate from LIWSA's operators.
 * This planner is single-threaded (so is the reusable decoder).
 */
public final class DAGParetoFLAPlanningAlgorithm extends BasePlanningAlgorithm {
    // WorkflowPlanner instantiates with a no-arg constructor. Set BEFORE startSimulation.
    public static int CONFIG_POPULATION_SIZE = 30;
    public static int CONFIG_GENERATION_COUNT = 100;
    public static Long CONFIG_RANDOM_SEED = null;
    public static int CONFIG_ARCHIVE_CAPACITY = 100;
    public static boolean CONFIG_ENFORCE_PES = false;
    public static List<Map<Integer, Integer>> CONFIG_SEED_ASSIGNMENTS = null;

    // Ablations (no other planner reads these).
    public static boolean CONFIG_DAG_GUIDANCE = true;
    public static boolean CONFIG_CROSS_GROUP_DO = true;
    public static boolean CONFIG_ARCHIVE_SSO = true;
    public static boolean CONFIG_ADAPTIVE_MUTATION = true;
    public static boolean CONFIG_ADAPTIVE_PREFERENCE = true;
    public static boolean CONFIG_GLOBAL_SURVIVOR_SELECTION = false;
    public static boolean CONFIG_RANDOM_IMMIGRANTS = false;

    public static volatile LastRunMetrics lastRun = null;

    private static final double EPS = 1e-12;
    private static final double MUT_MIN = 0.02;
    private static final double MUT_MAX = 0.20;
    private static final double DIVERSITY_REWARD = 0.15;
    private static final double LEADER_TEMPERATURE = 0.20;
    private static final double LEADER_CROWDING_REWARD = 0.50;

    public static final class LastRunMetrics {
        public double chosenMakespan;
        public double chosenCost;
        public int paretoFrontSize;
        public List<double[]> paretoFrontPoints;
        public List<Map<Integer, Integer>> paretoFrontAssignments;
        public long searchWallClockMillis;
        public int populationSizeUsed;
        public int generationCountUsed;
        public long objectiveEvaluations;
        public int diffusionIterations;
        public int equilibriumIterations;
        public int steadyStateIterations;
        public int group1Size;
        public int group2Size;
        public double finalAlpha1;
        public double finalDiversity;
        public List<double[]> searchTrace; // {iteration, archiveSize, bestM, bestCost, diversity}
    }

    private static final class Solution {
        final int[] genes;
        final double makespan;
        final double cost;
        Solution(int[] x, double[] mc) {
            genes = x.clone();
            makespan = mc[0];
            cost = mc[1];
        }
    }
    private static final class Bounds {
        double minM = Double.POSITIVE_INFINITY, maxM = Double.NEGATIVE_INFINITY;
        double minC = Double.POSITIVE_INFINITY, maxC = Double.NEGATIVE_INFINITY;
        Bounds(List<Solution> xs) {
            for (Solution s : xs) {
                minM = Math.min(minM, s.makespan); maxM = Math.max(maxM, s.makespan);
                minC = Math.min(minC, s.cost); maxC = Math.max(maxC, s.cost);
            }
        }
        double m(double v) { return (v - minM) / Math.max(EPS, maxM - minM); }
        double c(double v) { return (v - minC) / Math.max(EPS, maxC - minC); }
    }

    private final int populationSize;
    private final int generations;
    private final int archiveCapacity;
    private final Long seed;
    private final boolean enforcePes;
    private final boolean useDag, useCross, useArchiveSso, useAdaptiveMutation, useAdaptivePreference;
    private final boolean useGlobalSelection, useImmigrants;
    private final List<Map<Integer,Integer>> seedMaps;
    private final List<Solution> archive = new ArrayList<>();
    private final List<double[]> searchTrace = new ArrayList<>();

    private Random random;
    private FLAScheduleEvaluator evaluator;
    private List<Task> taskOrder;
    private List<CondorVM> vmList;
    private int[][] allowed;
    private double[] importance;
    private int n, group1Size;
    private List<Solution> group1, group2;
    private double alpha1 = 0.85;
    private int doCount, eoCount, ssoCount;

    public DAGParetoFLAPlanningAlgorithm() {
        populationSize = CONFIG_POPULATION_SIZE;
        generations = CONFIG_GENERATION_COUNT;
        archiveCapacity = CONFIG_ARCHIVE_CAPACITY;
        seed = CONFIG_RANDOM_SEED;
        enforcePes = CONFIG_ENFORCE_PES;
        useDag = CONFIG_DAG_GUIDANCE;
        useCross = CONFIG_CROSS_GROUP_DO;
        useArchiveSso = CONFIG_ARCHIVE_SSO;
        useAdaptiveMutation = CONFIG_ADAPTIVE_MUTATION;
        useAdaptivePreference = CONFIG_ADAPTIVE_PREFERENCE;
        useGlobalSelection = CONFIG_GLOBAL_SURVIVOR_SELECTION;
        useImmigrants = CONFIG_RANDOM_IMMIGRANTS;
        seedMaps = CONFIG_SEED_ASSIGNMENTS == null ? Collections.emptyList()
                : new ArrayList<>(CONFIG_SEED_ASSIGNMENTS);
    }

    @Override
    public void run() {
        lastRun = null;
        if (populationSize < 4 || generations < 1 || archiveCapacity < 2) {
            throw new IllegalArgumentException("Population >=4, generations >=1, archive capacity >=2 required");
        }
        long start = System.nanoTime();
        vmList = new ArrayList<>();
        for (Object obj : getVmList()) { vmList.add((CondorVM) obj); }
        evaluator = new FLAScheduleEvaluator(getTaskList(), vmList,
                FLAScheduleEvaluator.InsertionMode.VERIFIED_EARLIEST_INSERTION, enforcePes);
        taskOrder = evaluator.getTaskOrder();
        n = taskOrder.size();
        allowed = new int[n][];
        for (int k = 0; k < n; k++) {
            if (enforcePes) {
                allowed[k] = evaluator.getFeasibleVmIndices(k);
            } else {
                allowed[k] = new int[vmList.size()];
                for (int v = 0; v < vmList.size(); v++) { allowed[k][v] = v; }
            }
        }
        importance = calculateUpwardRankWeights();
        if (!useDag) { Arrays.fill(importance, 1.0); }
        random = seed == null ? new Random() : new Random(seed);
        group1Size = (populationSize + 1) / 2;
        List<Solution> initial = initializePopulation();
        group1 = new ArrayList<>(initial.subList(0, group1Size));
        group2 = new ArrayList<>(initial.subList(group1Size, populationSize));
        archive.clear(); searchTrace.clear();
        doCount = 0; eoCount = 0; ssoCount = 0; alpha1 = 0.85;
        for (Solution s : initial) { archiveConsider(s); }
        saveTrace(0);

        for (int t = 1; t <= generations; t++) {
            double tf = Math.sqrt(Math.sinh((double)t / generations));
            List<Solution> parents = population();
            int[] rank = nondominatedRank(parents);
            int maxRank = 0;
            for (int r : rank) { maxRank = Math.max(maxRank, r); }
            final Bounds snapshot = new Bounds(parents);
            Solution leader1 = chooseLeader(group1, alpha1, snapshot);
            Solution leader2 = chooseLeader(group2, 1.0 - alpha1, snapshot);
            double diversity = hammingDiversity(parents);
            double mutationProbability = useAdaptiveMutation
                    ? MUT_MIN + (MUT_MAX - MUT_MIN) * (1.0 - diversity)
                    : MUT_MIN;
            double dof = 0;
            int phase;
            if (tf < 0.9) {
                doCount++; phase = 0;
                // FLA MATLAB 1.0 diffusion factor; capped for a probability mapping.
                dof = clamp(Math.pow(Math.exp(-(2.0 * tf - random.nextDouble())), 2.0), 0, 1);
            } else if (tf <= 1.0) {
                eoCount++; phase = 1;
            } else {
                ssoCount++; phase = 2;
            }
            List<Solution> children1 = new ArrayList<>();
            List<Solution> children2 = new ArrayList<>();
            for (int i = 0; i < populationSize; i++) {
                Solution current = parents.get(i);
                boolean isG1 = i < group1Size;
                Solution ref;
                if (phase == 0) {
                    ref = useCross ? (isG1 ? leader2 : leader1)
                            : (isG1 ? leader1 : leader2);
                } else if (phase == 1) {
                    ref = isG1 ? leader1 : leader2;
                } else {
                    ref = useArchiveSso && !archive.isEmpty()
                            ? chooseArchiveLeader(isG1 ? alpha1 : 1.0 - alpha1)
                            : (isG1 ? leader1 : leader2);
                }
                int[] genes = current.genes.clone();
                if(useImmigrants && random.nextDouble()<0.10) {
                    // Budget unchanged: exactly one evaluation per child.
                    for(int k=0;k<n;k++) genes[k]=allowed[k][random.nextInt(allowed[k].length)];
                } else {
                    if (phase == 0) {
                        diffusionGenes(genes, ref.genes, dof);
                    } else {
                        double pressure = Math.exp(-(double) rank[i] / Math.max(1, maxRank));
                        guidedGenes(genes, ref.genes, pressure);
                    }
                    mutate(genes, mutationProbability);
                }
                Solution child = new Solution(genes, evaluator.evaluate(genes));
                archiveConsider(child); // ALL visited children, even if not selected
                (isG1 ? children1 : children2).add(child);
            }
            // Global fronts are computed from all parents/children, but each group
            // retains its own size and objective preference.
            List<Solution> union1 = new ArrayList<>(group1);
            union1.addAll(children1);
            List<Solution> union2 = new ArrayList<>(group2);
            union2.addAll(children2);
            List<Solution> union = new ArrayList<>(union1);
            union.addAll(union2);
            int[] globalRank = nondominatedRank(union);
            double[] globalCrowd = crowdingDistance(union, globalRank);
            Bounds b = new Bounds(union);
            if(useGlobalSelection) {
                // Experimental NSGA-style global Pareto elitism before the next
                // two-group FLA phase; NOT an original MATLAB FLA equation.
                List<Solution> survivors=selectGroup(union,0,populationSize,
                        globalRank,globalCrowd,b,0.5);
                survivors.sort(Comparator.comparingDouble((Solution x)->preference(x,alpha1,b))
                        .thenComparingDouble(x->x.makespan)
                        .thenComparingDouble(x->x.cost));
                group1=new ArrayList<>(survivors.subList(0,group1Size));
                group2=new ArrayList<>(survivors.subList(group1Size,populationSize));
            } else {
                group1 = selectGroup(union1, 0, group1Size, globalRank, globalCrowd, b, alpha1);
                group2 = selectGroup(union2, union1.size(), populationSize-group1Size,
                        globalRank, globalCrowd, b, 1.0-alpha1);
            }
            if (useAdaptivePreference && t % 10 == 0 && !archive.isEmpty()) {
                adaptPreference();
            }
            saveTrace(t);
        }
        if (archive.isEmpty()) { throw new IllegalStateException("Empty Pareto archive"); }
        Solution chosen = archive.get(0);
        for (Solution s : archive) {
            if (s.makespan < chosen.makespan
                    || s.makespan == chosen.makespan && s.cost < chosen.cost) chosen = s;
        }
        evaluator.commitAssignment(chosen.genes);
        LastRunMetrics m = new LastRunMetrics();
        m.chosenMakespan = chosen.makespan;
        m.chosenCost = chosen.cost;
        m.paretoFrontSize = archive.size();
        m.paretoFrontPoints = new ArrayList<>();
        m.paretoFrontAssignments = new ArrayList<>();
        List<Solution> sorted = new ArrayList<>(archive);
        sorted.sort(Comparator.comparingDouble((Solution s)->s.makespan).thenComparingDouble(s->s.cost));
        for (Solution s : sorted) {
            m.paretoFrontPoints.add(new double[]{s.makespan,s.cost});
            m.paretoFrontAssignments.add(evaluator.toAssignment(s.genes));
        }
        m.populationSizeUsed = populationSize;
        m.generationCountUsed = generations;
        m.objectiveEvaluations = evaluator.getObjectiveEvaluations();
        m.searchWallClockMillis = (System.nanoTime() - start) / 1_000_000L;
        m.diffusionIterations = doCount;
        m.equilibriumIterations = eoCount;
        m.steadyStateIterations = ssoCount;
        m.group1Size = group1.size();
        m.group2Size = group2.size();
        m.finalAlpha1 = alpha1;
        m.finalDiversity = hammingDiversity(population());
        m.searchTrace = new ArrayList<>();
        for (double[] a : searchTrace) { m.searchTrace.add(a.clone()); }
        lastRun = m;
        System.out.printf("DAG-Pareto-FLA: front=%d, chosenM=%.6f, chosenC=%.6f, eval=%d, DO=%d EO=%d SSO=%d%n",
                m.paretoFrontSize,m.chosenMakespan,m.chosenCost,m.objectiveEvaluations,
                m.diffusionIterations,m.equilibriumIterations,m.steadyStateIterations);
    }

    private List<Solution> population() {
        List<Solution> all = new ArrayList<>(populationSize);
        all.addAll(group1); all.addAll(group2);
        return all;
    }

    private List<Solution> initializePopulation() {
        List<Solution> list = new ArrayList<>(populationSize);
        for (Map<Integer,Integer> map : seedMaps) {
            if (list.size() >= populationSize) break;
            try {
                int[] g = evaluator.fromAssignment(map);
                list.add(new Solution(g,evaluator.evaluate(g)));
            } catch (IllegalArgumentException ex) {
                System.err.println("DAG-Pareto-FLA skipped invalid warm-start: "+ex.getMessage());
            }
        }
        while(list.size() < populationSize) {
            int[] g = new int[n];
            for(int k=0;k<n;k++) {
                g[k] = allowed[k][random.nextInt(allowed[k].length)];
            }
            list.add(new Solution(g,evaluator.evaluate(g)));
        }
        return list;
    }

    /** HEFT-style upward ranks; resource-aware but fixed for the run. */
    private double[] calculateUpwardRankWeights() {
        Map<Task,Integer> id = new IdentityHashMap<>();
        for (int k=0;k<n;k++) id.put(taskOrder.get(k),k);
        double[] rank = new double[n];
        double bandwidth = 0;
        for (CondorVM vm : vmList) bandwidth += vm.getBw();
        bandwidth /= vmList.size();
        for (int k=n-1;k>=0;k--) {
            Task task=taskOrder.get(k);
            double duration = 0;
            for (int vm : allowed[k]) duration += task.getCloudletTotalLength()/vmList.get(vm).getMips();
            duration /= allowed[k].length;
            double latest=0;
            for (Task child : task.getChildList()) {
                Integer index = id.get(child);
                if (index == null || index <= k) {
                    throw new IllegalArgumentException("Invalid task DAG or external child");
                }
                double comm = 0;
                for (FileItem f : task.getFileList()) {
                    if (f.getType()!=Parameters.FileType.OUTPUT) continue;
                    for(FileItem input:child.getFileList()) {
                        if (input.getType()==Parameters.FileType.INPUT && input.getName().equals(f.getName())) {
                            comm += input.getSize(); break;
                        }
                    }
                }
                comm = (comm / Consts.MILLION) * 8 / bandwidth;
                latest=Math.max(latest,comm+rank[index]);
            }
            rank[k]=duration+latest;
        }
        double max=0;
        for (double r : rank) max=Math.max(max,r);
        for (int k=0;k<n;k++) rank[k]=max>0?rank[k]/max:1;
        return rank;
    }

    private Solution chooseLeader(List<Solution> group,double a, Bounds bounds) {
        List<Solution> distinct = new ArrayList<>();
        for(Solution s:group) {
            boolean found=false;
            for (Solution d:distinct) {
                if(Arrays.equals(s.genes,d.genes)) {found=true;break;}
            }
            if(!found) distinct.add(s);
        }
        distinct.sort(Comparator.comparingDouble((Solution s)->preference(s,a,bounds))
                .thenComparingDouble(s->s.makespan).thenComparingDouble(s->s.cost));
        int k=Math.min(2,distinct.size());
        if(k==1)return distinct.get(0);
        // Stochastic top-2 selection avoids deterministic leader collapse.
        double w1=1.0/(preference(distinct.get(0),a,bounds)+0.1);
        double w2=1.0/(preference(distinct.get(1),a,bounds)+0.1);
        return random.nextDouble()*(w1+w2)<w1?distinct.get(0):distinct.get(1);
    }

    private Solution chooseArchiveLeader(double a) {
        Bounds bounds=new Bounds(archive);
        List<Solution> sorted=new ArrayList<>(archive);
        sorted.sort(Comparator.comparingDouble((Solution s)->preference(s,a,bounds))
                .thenComparingDouble(s->s.makespan).thenComparingDouble(s->s.cost));
        int k=Math.min(2,sorted.size());
        if(k==1)return sorted.get(0);
        int[] ranks=new int[sorted.size()];
        double[] cd=crowdingDistance(sorted,ranks);
        double maxFinite=0;
        for(double x:cd)if(Double.isFinite(x))maxFinite=Math.max(maxFinite,x);
        double[] probs=new double[k];double sum=0;
        for(int j=0;j<k;j++){
            double div=Double.isInfinite(cd[j])?1.0:cd[j]/Math.max(EPS,maxFinite);
            probs[j]=Math.exp(-preference(sorted.get(j),a,bounds)/LEADER_TEMPERATURE)
                    *(1.0+LEADER_CROWDING_REWARD*div);
            sum+=probs[j];
        }
        double sample=random.nextDouble()*sum;
        for(int j=0;j<k;j++) {
            sample-=probs[j];
            if(sample<=0)return sorted.get(j);
        }
        return sorted.get(k-1);
    }

    private static double preference(Solution s,double alpha,Bounds b) {
        return alpha*b.m(s.makespan)+(1-alpha)*b.c(s.cost);
    }

    /** DO: weighted distinct task draw followed by independent copy decisions. */
    private void diffusionGenes(int[] child, int[] guide, double dof) {
        int k=Math.min(n,Math.max(1,(int)Math.round(dof*n)));
        boolean[] selected=new boolean[n];
        for(int draw=0;draw<k;draw++) {
            double total=0;
            for(int j=0;j<n;j++) if(!selected[j]) total+=importance[j];
            double needle=random.nextDouble()*total;
            int picked=-1;
            for(int j=0;j<n;j++) {
                if(selected[j])continue;
                needle-=importance[j];
                if(needle<=0) {picked=j;break;}
            }
            if(picked<0)for(int j=n-1;j>=0;j--)if(!selected[j]){picked=j;break;}
            selected[picked]=true;
            if(random.nextDouble() < dof*(0.5+0.5*importance[picked])) child[picked]=guide[picked];
        }
    }

    /** EO / SSO: guide genes, using a rank-dependent per-task probability. */
    private void guidedGenes(int[] child,int[] guide,double pressure) {
        for(int k=0;k<n;k++) {
            double p=clamp(pressure*random.nextDouble()*(0.5+0.5*importance[k]),0,1);
            if(random.nextDouble()<p)child[k]=guide[k];
        }
    }

    /** One different feasible VM gene, with per-molecule adaptive probability. */
    private void mutate(int[] child,double probability) {
        if(random.nextDouble()>=probability) return;
        int k=random.nextInt(n);
        int[] choices=allowed[k];
        if(choices.length<=1) return;
        int idx=random.nextInt(choices.length-1);
        if(choices[idx]>=0 && choices[idx]==child[k]) idx=choices.length-1;
        // Alternative must actually differ from the current assignment.
        if(choices[idx]==child[k]) {
            for(int v:choices)if(v!=child[k]){child[k]=v;return;}
        } else child[k]=choices[idx];
    }

    private static boolean dominates(Solution a,Solution b) {
        return a.makespan<=b.makespan && a.cost<=b.cost
                && (a.makespan<b.makespan || a.cost<b.cost);
    }

    private void archiveConsider(Solution s) {
        for(Solution a:archive) {
            // Keep a single representative for an equal objective vector.
            if (a.makespan<=s.makespan && a.cost<=s.cost) return;
        }
        for (int i=archive.size()-1;i>=0;i--) if(dominates(s,archive.get(i)))archive.remove(i);
        archive.add(s);
        while(archive.size()>archiveCapacity) pruneArchive();
    }

    private void pruneArchive() {
        int[] rank=new int[archive.size()];
        double[] cd=crowdingDistance(archive,rank);
        int victim=-1;double smallest=Double.POSITIVE_INFINITY;
        for(int i=0;i<cd.length;i++) {
            if(cd[i]<smallest){smallest=cd[i];victim=i;}
        }
        if(victim<0)victim=archive.size()-1;
        archive.remove(victim);
    }

    private static int[] nondominatedRank(List<Solution> all) {
        int n=all.size();
        int[] count=new int[n];
        List<List<Integer>> dominated=new ArrayList<>();
        for(int i=0;i<n;i++)dominated.add(new ArrayList<Integer>());
        for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){
            if(dominates(all.get(i),all.get(j))){dominated.get(i).add(j);count[j]++;}
            else if(dominates(all.get(j),all.get(i))){dominated.get(j).add(i);count[i]++;}
        }
        int[] rank=new int[n];Arrays.fill(rank,-1);
        List<Integer> front=new ArrayList<>();
        for(int i=0;i<n;i++)if(count[i]==0)front.add(i);
        int level=0;
        while(!front.isEmpty()){
            List<Integer> next=new ArrayList<>();
            for(int idx:front){rank[idx]=level;
                for(int j:dominated.get(idx))if(--count[j]==0)next.add(j);
            }
            front=next;level++;
        }
        return rank;
    }

    private static double[] crowdingDistance(List<Solution> xs,int[] ranks) {
        int n=xs.size();double[] cd=new double[n];
        int max=0;for(int r:ranks)max=Math.max(max,r);
        for(int level=0;level<=max;level++){
            List<Integer> front=new ArrayList<>();
            for(int i=0;i<n;i++)if(ranks[i]==level)front.add(i);
            if(front.isEmpty())continue;
            if(front.size()<=2){for(int i:front)cd[i]=Double.POSITIVE_INFINITY;continue;}
            for(int objective=0;objective<2;objective++){
                final int obj=objective;
                front.sort(Comparator.comparingDouble(i->obj==0?xs.get(i).makespan:xs.get(i).cost));
                cd[front.get(0)]=Double.POSITIVE_INFINITY;
                cd[front.get(front.size()-1)]=Double.POSITIVE_INFINITY;
                double min=obj==0?xs.get(front.get(0)).makespan:xs.get(front.get(0)).cost;
                double maxV=obj==0?xs.get(front.get(front.size()-1)).makespan:xs.get(front.get(front.size()-1)).cost;
                double span=maxV-min;
                if(span<=EPS)continue;
                for(int j=1;j<front.size()-1;j++){
                    int id=front.get(j);
                    if(Double.isInfinite(cd[id]))continue;
                    double left=obj==0?xs.get(front.get(j-1)).makespan:xs.get(front.get(j-1)).cost;
                    double right=obj==0?xs.get(front.get(j+1)).makespan:xs.get(front.get(j+1)).cost;
                    cd[id]+=(right-left)/span;
                }
            }
        }
        return cd;
    }

    private List<Solution> selectGroup(List<Solution> candidates,int offset,int size,
            int[] globalRank,double[] crowd,Bounds b,double alpha) {
        List<Integer> order=new ArrayList<>();
        for(int i=0;i<candidates.size();i++) order.add(i);
        double maxFinite=0;
        for(int i:order){double x=crowd[offset+i];if(Double.isFinite(x))maxFinite=Math.max(maxFinite,x);}
        final double finiteMax=maxFinite;
        order.sort((i,j)->{
            int ri=globalRank[offset+i],rj=globalRank[offset+j];
            if(ri!=rj)return Integer.compare(ri,rj);
            double di=Double.isInfinite(crowd[offset+i])?1.0:crowd[offset+i]/Math.max(EPS,finiteMax);
            double dj=Double.isInfinite(crowd[offset+j])?1.0:crowd[offset+j]/Math.max(EPS,finiteMax);
            double si=preference(candidates.get(i),alpha,b)-DIVERSITY_REWARD*di;
            double sj=preference(candidates.get(j),alpha,b)-DIVERSITY_REWARD*dj;
            int diff=Double.compare(si,sj);
            return diff!=0?diff:Integer.compare(i,j);
        });
        List<Solution> picked=new ArrayList<>(size);
        for(int idx:order){
            if(picked.size()>=size)break;
            Solution s=candidates.get(idx);
            boolean dup=false;
            for(Solution p:picked)if(Arrays.equals(p.genes,s.genes)){dup=true;break;}
            if(!dup)picked.add(s);
        }
        // The search space may have fewer distinct assignments than group size.
        if(picked.size()<size)for(int idx:order){
            if(picked.size()>=size)break;
            picked.add(candidates.get(idx));
        }
        return picked;
    }

    private static double hammingDiversity(List<Solution> xs) {
        if(xs.size()<2 || xs.get(0).genes.length==0)return 0;
        long sum=0;
        for(int i=0;i<xs.size();i++)for(int j=i+1;j<xs.size();j++){
            int[] a=xs.get(i).genes,b=xs.get(j).genes;
            for(int k=0;k<a.length;k++)if(a[k]!=b[k])sum++;
        }
        return 2.0*sum/((double)xs.size()*(xs.size()-1)*xs.get(0).genes.length);
    }

    private void adaptPreference() {
        // Step-to-step progress over the last (up to) ten generations.
        if(searchTrace.size()<2)return;
        int from=Math.max(0,searchTrace.size()-10);
        double oldM=searchTrace.get(from)[2],oldC=searchTrace.get(from)[3];
        double newM=Double.POSITIVE_INFINITY,newC=Double.POSITIVE_INFINITY;
        for(Solution s:archive) {newM=Math.min(newM,s.makespan);newC=Math.min(newC,s.cost);}
        double gainM=Math.max(0,(oldM-newM)/Math.max(EPS,oldM));
        double gainC=Math.max(0,(oldC-newC)/Math.max(EPS,oldC));
        alpha1=clamp(alpha1+0.2*(gainC-gainM),0.7,0.9);
    }

    private void saveTrace(int t) {
        double bestM=Double.POSITIVE_INFINITY,bestC=Double.POSITIVE_INFINITY;
        for(Solution s:archive){bestM=Math.min(bestM,s.makespan);bestC=Math.min(bestC,s.cost);}
        searchTrace.add(new double[]{t,archive.size(),bestM,bestC,hammingDiversity(population())});
    }
    private static double clamp(double x,double lo,double hi){return Math.max(lo,Math.min(hi,x));}
}