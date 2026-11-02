# Unified planning evaluator contract

This is an engineering contract for the current planning model, not a claim of
exact WorkflowSim simulator parity and not a claim of faithful FLA reproduction.

## Shared objectives and chromosome
- Tasks are topologically ordered.
- A gene is a zero-based index into the experiment's ordered VM list, not a CloudSim VM ID.
- Runtime is the existing planner's task computation time on the selected VM.
- A child becomes ready after every parent finishes; a cross-VM transfer delay
  is added only when parent and child use different VMs.
- VM execution is non-preemptive and space-shared. The task is inserted into
  the earliest feasible gap in a chronological, non-overlapping VM calendar.
- Planning execution cost is sum(runtime * VM per-second price).
- The shared evaluator currently optimizes two minimization objectives:
  planning makespan and planning execution cost. It does not include rental
  period rounding, idle billing, energy, data-transfer price, or QoS penalties.

## Simulator parity
WorkflowSim can add stage-in time to job length, apply simulator dispatch
ordering and bill different CPU time. Therefore the planning decoder and
simulator measurements remain separate. The fidelity check measures their
difference; a zero exit code alone does not mean parity. Do not combine
planning estimates and simulator observations in one Pareto/HV calculation.

## Validation
- DecoderInsertionRegressionTest exercises the actual LIWSA, NSGA-II and
  MLEAO decode methods with the five-task/two-VM counterexample (95 seconds).
- UnifiedEvaluatorPropertiesTest compares the shared evaluator with a
  separate list-based calendar oracle over 1,800 fixed-seed random DAG schedules.
- DecoderFidelityCheck replays chosen assignments through WorkflowSim. It is
  a measurement, not a threshold assertion. Add per-workflow/per-seed
  thresholds only after defining the expected simulator model.

## FLA reproduction gate
Before labelling a Java implementation a faithful FLA baseline, pin the exact
paper and source-code versions, transcribe the DO/EO/SSO equations, all random
draws, phase boundaries, bound handling and update order, and separately
document the continuous-to-discrete VM assignment mapping. A MATLAB-derived
implementation is an adaptation unless this mapping and every update are
validated against the source.
