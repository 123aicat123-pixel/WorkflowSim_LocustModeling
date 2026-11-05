package org.workflowsim.planning;
import java.util.Arrays;
import java.util.Random;

/** Pure non-simulator v20 controls: no extra objective calls are possible. */
public final class FrontierNoveltyProposalTest {
    private static void ok(boolean b,String msg){if(!b)throw new AssertionError(msg);}
    public static void main(String[] args) {
        int[] base={0,1,0,1};
        int[][] allowed={{0,1},{0,1},{0,1},{0,1}};
        int[][] parents={{0,1,0,1},{1,1,0,0},{0,0,1,1}};
        int[] ep={0,1,2},ec={1,2,3};
        double[] costs={1,2};
        for(FrontierNoveltyProposal.Source src:FrontierNoveltyProposal.Source.values()){
            FrontierNoveltyProposal.Result x=FrontierNoveltyProposal.propose(
                base,allowed,parents,ep,ec,costs,true,src,new Random(23));
            FrontierNoveltyProposal.Result y=FrontierNoveltyProposal.propose(
                base,allowed,parents,ep,ec,costs,true,src,new Random(23));
            ok(Arrays.equals(x.genes,y.genes),"Seeded proposer changed outcome");
            ok(x.proposalsChanged==4,"Four proposals must be distinct from base");
            ok(x.minHamming>=0&&x.minHamming<=1,"Invalid novelty range");
            ok(FrontierNoveltyProposal.minHamming(x.genes,parents)==x.minHamming,
                "Novelty metric differs from selected population");
            ok(Arrays.equals(base,new int[]{0,1,0,1}),
                "Caller genotype was modified");
            for(int vm:x.genes)ok(vm==0||vm==1,"Illegal VM chosen");
        }
        FrontierNoveltyProposal.Result cost=FrontierNoveltyProposal.propose(
            base,allowed,parents,ep,ec,costs,false,
            FrontierNoveltyProposal.Source.DAG_EDGE,new Random(20));
        ok(cost.proposalsChanged==4,"Cost group did not generate four candidates");
        int[][] single={{0},{1},{0},{1}};
        FrontierNoveltyProposal.Result constrained=FrontierNoveltyProposal.propose(
            base,single,parents,ep,ec,costs,false,
            FrontierNoveltyProposal.Source.DAG_EDGE,new Random(23));
        ok(Arrays.equals(constrained.genes,base) && constrained.proposalsChanged==0,
            "An infeasible genotype escaped PE constraints");
        boolean threw=false;
        try {
            FrontierNoveltyProposal.propose(base,allowed,parents,new int[]{99},
                new int[]{0},costs,true,FrontierNoveltyProposal.Source.DAG_EDGE,new Random(5));
        }catch(IllegalArgumentException expected){threw=true;}
        ok(threw,"Invalid DAG edge accepted");
        System.out.println("PASS FrontierNoveltyProposalTest: deterministic four-proposal random/DAG and VM feasibility oracles");
    }
}
