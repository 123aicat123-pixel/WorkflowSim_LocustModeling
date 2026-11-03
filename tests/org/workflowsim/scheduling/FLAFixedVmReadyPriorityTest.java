package org.workflowsim.scheduling;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.cloudbus.cloudsim.Cloudlet;
import org.workflowsim.Job;
import org.workflowsim.Task;
import org.workflowsim.utils.Parameters;

/** Checks optional ready-job ordering without mutating original queue or stage-in jobs. */
public final class FLAFixedVmReadyPriorityTest {
    private static Job singleJob(int jobId,Task task) {
        Job j=new Job(jobId,task.getCloudletTotalLength());
        j.setClassType(Parameters.ClassType.COMPUTE.value);
        j.addTaskList(java.util.Collections.singletonList(task));
        return j;
    }
    private static void check(List<Cloudlet> got,Cloudlet... expected){
        if(got.size()!=expected.length)throw new AssertionError("Wrong ordered queue length");
        for(int i=0;i<expected.length;i++)
            if(got.get(i)!=expected[i])
                throw new AssertionError("Unexpected result at position "+i);
    }
    public static void main(String[] args) {
        String before=System.getProperty("dagfla.fixedVmReadyPriority");
        try {
            Task a=new Task(1,10),b=new Task(2,50),c=new Task(3,100);
            a.addChild(c);c.addParent(a);
            Job ja=singleJob(101,a),jb=singleJob(102,b),jc=singleJob(103,c);
            Task untouched=new Task(300,1);
            List<Cloudlet> pending=new ArrayList<>(Arrays.asList(jb,untouched,jc,ja));
            System.setProperty("dagfla.fixedVmReadyPriority","fifo");
            check(FLAFixedVmReadyPriority.ordered(pending),jb,untouched,jc,ja);
            System.setProperty("dagfla.fixedVmReadyPriority","shortest");
            check(FLAFixedVmReadyPriority.ordered(pending),ja,untouched,jb,jc);
            System.setProperty("dagfla.fixedVmReadyPriority","upward");
            check(FLAFixedVmReadyPriority.ordered(pending),ja,untouched,jc,jb);
            check(pending,jb,untouched,jc,ja);
            boolean fail=false;
            System.setProperty("dagfla.fixedVmReadyPriority","invalid");
            try{FLAFixedVmReadyPriority.ordered(pending);}catch(IllegalArgumentException expected){fail=true;}
            if(!fail)throw new AssertionError("Unknown policy accepted");
            System.out.println("PASS FLAFixedVmReadyPriorityTest: FIFO parity, shortest, upward, queue immutability, stage-in slot, invalid policy");
        } finally {
            if(before==null)System.clearProperty("dagfla.fixedVmReadyPriority");
            else System.setProperty("dagfla.fixedVmReadyPriority",before);
        }
    }
}
