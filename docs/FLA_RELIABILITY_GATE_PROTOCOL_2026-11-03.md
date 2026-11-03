# Predeclared K16 causal reliability-gated replay pilot — 2026-11-03

Branch: `fla-baseline`. `master` must remain unchanged.

This is an **experimental post-search replay selector**, not a FLA operator improvement and not the default `pareto-cover` policy. Historical 20-case VM and 8-case synthetic experiments motivated a conservative trust gate, but their labels are NOT independent test data for this pilot.

Policy name: `online-reliability-gated`. Each optimizer executes the same 3030 planning evaluations as original and selects four identical planned-cover warmup assignments. Before each replay step 5–16, inspect **only simulator labels of previously replayed assignments**. Trust online observed-front marginal-HV greedy selection if ALL hold: (i) at least 4 labeled assignments; (ii) every prior relative planned-to-real makespan error <=2.5% in magnitude; (iii) maximum minus minimum makespan relative residual <=1.5 percentage points; (iv) at least two planned makespan pairs differ by >=0.5% of the larger predicted makespan; (v) none of those informative pairs has a real-order reversal or tie. Otherwise replay the next unvisited candidate in the original fixed planned-cover order. Reassess after each new replay.

All cutoffs are **design choices**, not learned confidence intervals or calibrated probability bounds. Cost is not used for the trust gate because previous cost prediction errors were tiny; this is a stated limitation. Record `gated-observed` / `gated-cover` in the causal trace. Continue to record equal planning budget, exact K16 true WorkflowSim replays, identical solver history SHA, two deterministic cost seeds and first four warmups. Do not use held-out labels to select a reference or tune the gate after evaluation.

NEXT TEST: new deterministic, previously untested synthetic bottleneck DAGs and fresh optimizer seeds, against `pareto-cover` and `online-observed-hv` in both baseline/staggered VM settings. Freeze a planned-only scoring reference (1.5x+1 primary, 3.0x+1 sensitivity) before reading real outcomes; report failures and unmeasured risks. Keep `pareto-cover` default regardless of pilot outcome until broader evidence.
