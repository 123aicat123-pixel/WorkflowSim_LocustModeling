# Montage32 independent physical decision transfer: actual verified results (2026-11-06)

**STATUS: Original physical replay PASS (4/4 blocks; 128/128 rows), independently audited exact K1–K4 actual-HV selection PASS. One positive matched decision effect, three ties. Exploratory pilot, NOT an SCI algorithm-improvement demonstration.**

## Frozen prospective record and verified source
- Pre-outcome protocol: `docs/FLA_MONTAGE32_TRANSFER_PROTOCOL_FROZEN_2026-11-06.md`, commit `b015ddc11ea55d09df032c350b488360701c369c`.
- New frozen audit script commit `3b4be0f28f4cd7160d1f8e08fc073e0a11cb87e9`.
- Original real source + audit workflow commit `97e1ced0f0fea1b1f2e771a11fbfdea6d3f2db5b`.
- **All five jobs SUCCESS:** [GitHub Actions run 42188466329](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/42188466329), source artifacts for four workflow×VM configurations and one independent audit artifact. Source checks enforced the same 32 distinct physical TaskID-to-VMID maps in all conditions, true per-task FIFO WorkflowSim tracing, exact 32-row case count, matched labels, identical source SHA, four distinct cases, independent actual-normalized-HV scoring, K1–K4 exact hindsight oracle.
- **128 original true mappings**: Montage_50 and Montage_100 × default and staggered VM speeds × 32 exact immutable policies × simulator seed 1501. Montage is a previously studied workflow family, not a genuinely untouched-family holdout, and this experiment does not execute the FLA optimizer itself.

## Primary realized K4 outcome

| Original DAG | VM profile | True nondominated physical maps /32 | Number of optimal true K4 subsets | OLD actual K4 regret | READY actual K4 regret | Physically distinct K4 selections? |
|---|---|---:|---:|---:|---:|---:|
| Montage_50 | default | 4 | 1 | 0 | 0 | No |
| Montage_50 | staggered | 4 | 1 | **0.000867221** | **0** | **Yes** |
| Montage_100 | default | 4 | 1 | 0 | 0 | No |
| Montage_100 | staggered | 6 | 1 | 0 | 0 | No |

The normalized true HV difference at K4 in Montage_50/staggered is **READY minus OLD = +0.000867221**. This is a true-WorkflowSim, matched-fixed-mapping choice improvement relative to OLD for **one of four** exploratory blocks; READY captured the *restricted 32-map hindsight* optimum there. It is **not** a globally optimal workflow schedule or an improved full FLA search result.

## Exact prefix budget outcomes

| K | OLD and READY different physical prefix sets | Mean OLD true regret over four blocks | Mean READY true regret | Mean READY minus OLD actual normalized HV |
|---:|---:|---:|---:|---:|
| 1 | 0/4 | 0 | 0 | 0 |
| 2 | 0/4 | 0.001055500 | 0.001055500 | 0 |
| 3 | **1/4** | 0.000216805 | 0 | **+0.000216805** |
| 4 | **1/4** | 0.000216805 | 0 | **+0.000216805** |

One original source seed (1501) and four blocks are insufficient for causal performance robustness, independent replication or statistical significance. Three of four true 32-map fronts contain exactly four nondominated maps and can be covered by K4; the fourth has six. All blocks have one exact true-HV optimal K4 combination, so no exact K4 optimal-set ties obscure the positive finding, but evaluation is still small.

## Next falsification gate
Before claiming superior optimization, freeze a **new seed × queue/VM regime matrix**, preserving identical physical maps, common actual reference and balanced source evaluations. The present single-seed source method hardcodes seed 1501; extending seeds requires a separately reviewed change to the runner, and a new prospective protocol must precede any new true labels. Report paired positive and negative READY−OLD normalized HV, actual regret, proportion of divergent selected physical mappings, bootstrap/blocked uncertainty and total simulator overhead; include truly untouched DAX structures or synthetic DAG regimes and full optimizer-vs-optimizer baselines if preparing an SCI algorithm paper. Do not tune the existing 32 mappings or discard unfavorable seeds based on observed actual outcomes.

**All code and results on `fla-baseline`. `master` not changed.**
