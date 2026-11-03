package org.workflowsim;

import java.util.Locale;
import org.workflowsim.utils.Parameters;

/**
 * Read-only, opt-in simulated event trace for *unclustered compute Jobs*.
 *
 * Enable only with -Ddagfla.fixedEventTrace=true. Records original Task ID
 * from job.getTaskList(), NEVER the unrelated clustered Job Cloudlet ID.
 * No mutation, no random draws, no extra simulator/evaluator calls.
 *
 * Columns: event,original_task_id,job_id,vm_id,clock,stagein_seconds.
 * stagein_seconds=-1 means "not measured at this event"; only the
 * DATACENTER_SUBMIT event carries a measured per-job file-transfer delay.
 */
public final class FLATaskEventTrace {
    private FLATaskEventTrace() {}

    public static void emit(String event, Job job, double timestamp, double stagein) {
        if (!Boolean.getBoolean("dagfla.fixedEventTrace")) return;
        if (job == null || job.getClassType() != Parameters.ClassType.COMPUTE.value) return;
        if (job.getTaskList() == null || job.getTaskList().size() != 1)
            throw new IllegalStateException("Event trace requires unclustered one-task compute Jobs");
        Task original = job.getTaskList().get(0);
        if (original == null || original.getCloudletId() < 0 ||
                !Double.isFinite(timestamp) || timestamp < 0 ||
                !Double.isFinite(stagein) || stagein < -1)
            throw new IllegalStateException("Invalid event trace source for Job " + job.getCloudletId());
        System.out.printf(Locale.ROOT, "FIXED_EVENT,%s,%d,%d,%d,%.17g,%.17g%n",
                event, original.getCloudletId(), job.getCloudletId(),
                job.getVmId(), timestamp, stagein);
    }
}
