# WorkflowSim / FLA research audit and experimental results

**Research state:** validated engineering and simulator-informed objective modeling; algorithm superiority for DAG-Pareto-FLA **not demonstrated**.  
**Working branch:** `fla-baseline` only. **Original fork's `master` left untouched.**  
**Date recorded:** 2026-11-03.  
**Language:** Chinese research report with English reproducibility notes.

## 1. 执行摘要

实验已经在 GitHub Actions 的真实 Java 17 / WorkflowSim 环境完成，而不是只依据本地日志、仅编译成功或模拟测试。最可靠的工程进展是修复了任务插入解码器错误，将输入文件 stage-in 占用 VM 的执行时间和计费纳入新的可选规划目标估计，从而大幅缩小 CyberShake 家族的规划—仿真差异。在搜索方面，我们实现了连续 MATLAB FLA 的离散适配及独立多目标 DAG-Pareto-FLA，并统一记录实际目标函数评价次数、回放候选调度、用仿真而非规划估计计算 HV。

**目前不能声称 DAG-Pareto-FLA 优于 NSGA-II。** 相同 5 类 DAG × 5 个种子、约 3000 次评价的最终对照，NSGA-II 获得 20/25 次最高仿真 HV。改进版 v2-global 虽能改善旧版 DAG-FLA，但优势很有限，不宜凭现有实验向一区期刊宣称有显著算法突破。

## 2. 代码仓库与本地一致性

- GitHub: [123aicat123-pixel/WorkflowSim_LocustModeling](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling)
- 代码分支: [fla-baseline](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/tree/fla-baseline)
- 未对 `master` 提交代码。先前检查其 SHA 为 `c24d538300c6d3749f3149dd7495e7b3cdc3a4fa`。
- **未能证明 GitHub 分支与 Windows 本地完整项目逐文件一致**：会话无权直接读取用户电脑的本地目录，未做双端文件清单及 SHA-256 比对。远端包含本轮新增的算法/实验源码，不应称为原始本地副本。

## 3. 评价器科学性与回归测试

### 3.1 回归与源代码

- `DecoderInsertionRegressionTest`: 5 个任务/2 VM 反例，使 LIWSA、NSGA-II、MLEAO 返回可行 makespan=95s 而非历史上不可能的 65s。
- `UnifiedEvaluatorPropertiesTest`: 1,800 个固定随机种子 DAG 调度对独立列表式 oracle，比对任务先后约束、VM 无重叠区间及目标函数。
- `StageInAwareEvaluatorTest`: 手工检验外部输入加载、跨 VM 输入复制、已有数据副本缓存、任务 precedence、按时长计费、重复评价无状态污染。
- 新的可选 `StageInAwareScheduleEvaluator`：通过 `-Dworkflowsim.planningStageInAware=true` 启用；`false` 为默认值，使旧实验仍可复现。该新模型用于 **同一调度方案** 的预算相同优化，而非悄悄更改 WorkflowSim simulator 行为。
- 数据传输追踪证实 CyberShake 有单任务 stage-in 250.780678 秒；如果只按计算长度优化，Makespan 和 Cost 会出现很大系统性偏差。
- **限制：** Stage-in-aware 评价器依旧是对真实事件驱动调度、replica cache 和任务派发顺序的近似；不能笼统称为模拟器的数学等价实现。

### 3.2 7 个工作流 × 5 个种子：只改规划预测、执行结果不变

[实际 GitHub Actions 日志及 CSV](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41501564409)

绝对误差口径：`100 * abs(predicted - simulator) / simulator`，下表为 5 个种子的**中位数**。

| Workflow | Old Makespan error | Stage-in-aware Makespan error | Old Cost error | Stage-in-aware Cost error |
|---|---:|---:|---:|---:|
| CyberShake_30 | 66.144% | 0.108% | 57.293% | 0.011% |
| CyberShake_50 | 61.641% | 0.132% | 55.562% | 0.001% |
| CyberShake_100 | 51.414% | 0.093% | 48.565% | 0.000% |
| Epigenomics_24 | 0.581% | 0.017% | 0.540% | 0.000% |
| Inspiral_30 | 0.585% | 0.494% | 0.089% | 0.000% |
| Montage_25 | 1.150% | 1.511% | 0.927% | 0.152% |
| Sipht_30 | 0.115% | 0.024% | 0.087% | 0.007% |

**35 组配对比较：** Makespan 绝对误差降低于 30/35 组，Cost 降低于 35/35 组。Montage Makespan 误差轻微变差，必须如实保留。**评价模型的改进不是算法搜索效率或质量的提高。**

## 4. 完整公平比较：五类 DAG、五个种子、约 3000 次目标评价

[GitHub Actions 中的有效 30×100 对照](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41503062241)

- 种群大小 30；NSGA-II 与 DAG-FLA 各 100 generations；按实际函数调用数而非名义代数对齐预算。
- 实际调用：`FLA-3W = 3006`，`DAG-Pareto-FLA = 3030`，`NSGA-II = 3030`，`MLEAO = 3017`。MLEAO 使用 103 generations 匹配目标评价次数；FLA-3W 为三次独立、权重分别为 0.2/0.5/0.8 的标量搜索。
- 所有算法均关闭外部 warm start，统一 `-Dworkflowsim.planningStageInAware=true`，读取同一科学工作流 DAX 与 VM 池。
- `UnifiedCandidateRecorder` 对每次成功目标评价被动记录 cloudlet-ID → VM-ID、makespan/cost 和实际评价次数。将每个算法**实际访问过**的不同规划非支配任务分配，分别进行真实 WorkflowSim 仿真回放。
- HV 用**已回放候选的仿真** makespan 与 cost 计算，同一工作流跨全部种子和算法使用同一个固定参考点，不能跨不同工作流比较 HV 绝对值。
- **重要限制：** 被规划模型支配的候选没有全部仿真回放，因此仿真 Pareto 集可能不完整，这不是穷举的模拟器 Pareto front。

### 4.1 旧 DAG 改进版对照——平均 simulator HV

| Workflow | FLA-3W | DAG-FLA no-cross | NSGA-II | MLEAO |
|---|---:|---:|---:|---:|
| CyberShake_30 | 508749.33 | 488139.94 | **519323.38** | 486458.20 |
| Epigenomics_24 | 4741898.26 | 4432204.56 | **4835858.28** | 4803605.32 |
| Inspiral_30 | 943234.72 | 930617.54 | **996809.34** | 939347.28 |
| Montage_25 | 1281.25 | 1227.40 | **1380.83** | 1194.01 |
| Sipht_30 | **92201.08** | 91188.08 | 92044.53 | 91696.75 |

25 次种子级最高 HV：NSGA-II 20 次，FLA-3W 4 次，MLEAO 1 次，DAG-FLA 0 次。

## 5. DAG-FLA v2：消融选择与独立验证

### 5.1 提议的机制

在原 DAG-Pareto-FLA 的两组与 DO/EO/SSO 阶段更新外，加入**跨两组的全局 Pareto 精英环境选择**；此外独立测试 10% 随机移民，以避免无证据地叠加创新点。

- **开发集**：Montage_25、CyberShake_30、Sipht_30，各 3 个 paired seeds；`v2-global` 相对 `no-cross` 平均配对 HV **+3.185%**，改善 **7/9**。单独加入移民平均 **−4.879%**，故没有将移民作为最终默认推荐。
- **独立保留集**：Epigenomics_24 和 Inspiral_30，各 5 个 seeds。v2-global 平均配对改善 **+3.799%** 与 **+1.543%**，两者合计 **+2.671% / 10 组**，改善 6/10。
- [开发集逐算子试验](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41504028650) / [独立保留集验证](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41504496093)。

v2-global 的算子属于**新的混合多目标搜索策略**，不是原始连续 FLA 论文的忠实原式或实现证明。五个 seeds 的平均提升不能直接解释为统计显著。

### 5.2 v2-global 与标准算法的最终确认

[25 个成功的真实优化/仿真 job](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41504930248)。原汇总任务因为只匹配 `paper_*` 而实际 CSV 采用 `confirm_*` 失败；**该错误不在算法/回放实验**。使用原有 25 个 artifacts，独立修复汇总而不重新运行优化，获得[成功的冻结 HV 报告](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41505408839)。

| Workflow | FLA-3W | DAG-FLA v2-global | NSGA-II | MLEAO |
|---|---:|---:|---:|---:|
| CyberShake_30 | 508749.33 | 511435.47 | **519323.38** | 486458.20 |
| Epigenomics_24 | 4741898.26 | 4581556.30 | **4835858.28** | 4803605.32 |
| Inspiral_30 | 943234.72 | 937293.87 | **996809.34** | 939347.28 |
| Montage_25 | 1281.25 | 1296.49 | **1380.83** | 1194.01 |
| Sipht_30 | **90630.82** | 90333.07 | 90476.46 | 90128.13 |

25 组实验中，**DAG-FLA v2-global 相对 FLA-3W 的逐工作流、逐种子平均配对 HV 变化为 −0.507%**；NSGA-II 相对 FLA-3W 为 **+3.500%**，依然 20/25 次取得最高值。DAG-FLA v2-global 改善了自身原版，但没有证明超过 NSGA-II。

注意：在上述两个独立试验汇总中，Sipht 的单次均值略有差异。每份报告只可在自身冻结参考点和对应实验产物下解释，不把跨报告的绝对 HV 直接相减来声称改进。

## 6. 论文发表可行性的负责任结论

**工程验收：** 已能远端编译、真实运行优化、回放调度、保存日志与 raw CSV、执行解码器和 stage-in-aware 单元测试；科学性相比最初改善较大。

**算法创新论文：** 尚未充分验证。这些问题必须在正式投稿前处理：

1. 改进版 FLA 目前并未在主要 NSGA-II 对照下获得优势；若要做算法论文，需要有独立有效的新机制，而非事后只选表现较好的种子/工作流。
2. 五类各 1 个小规模工作流和 5 seeds 不足以论证普适性和统计显著性。至少扩展多种 workflow size、VM heterogeneity、价格场景、通信重负载、30+ seeds，并做配对效应量与统计检验。
3. 需进一步验证原始 MATLAB 源码及自定义离散转换边界；FLA-3W 是加权标量 portfolio，不是原生 MO 算法；MLEAO 是已声明的重构版，不应声称原作者开源原式完全复现。
4. 同时验证不同档期成本、按小时取整、数据传输费用、VM lease 生命周期和任务调度策略，否则成本目标只是当前 per-second 模型。
5. **规划非支配集回放不等于全仿真非支配集**；下一轮应对所有评价唯一 genotype 或经过精确不丢优的筛选做 simulator replay，明确仿真评价预算与搜索评价预算。
6. 工程代码仓库和 Windows 本地目录仍**未做文件级对账**；不做相同假定。

## 7. 复现路径与原始证据

原始日志及报告可从以上每个 GitHub Actions run 的 **Artifacts** 下载（Actions 产物有保留期，不是永久归档）。

CI 基本构建（Linux Java17）：

```bash
mkdir -p build/classes
find sources examples tests -type f -name '*.java' | sort > /tmp/sources-workflowsim.txt
javac -nowarn -encoding UTF-8 -cp 'lib/*' -d build/classes @/tmp/sources-workflowsim.txt
java -cp 'build/classes:lib/*' org.workflowsim.planning.DecoderInsertionRegressionTest
java -cp 'build/classes:lib/*' org.workflowsim.planning.UnifiedEvaluatorPropertiesTest
java -cp 'build/classes:lib/*' org.workflowsim.planning.StageInAwareEvaluatorTest
```

直接跑四算法调度并重放规划非支配解（单个 workflow / seed）：

```bash
java -Dworkflowsim.planningStageInAware=true \
  -Ddagfla.comparisonVariant=v2-global \
  -cp 'build/classes:lib/*' \
  org.workflowsim.examples.planning.FLAResearchExperiment \
  Montage_25 1 30 100 'Output&Results/demo_montage_s1'
```

以上命令生成 `_summary.csv`、`_replays.csv`、`_limitations.txt`。跨 5 种子 HV 汇总应使用同一工作流固定 reference point 的 Actions 汇总流程，而非直接比较单次默认 HV。建议提交论文时单独在仓库里发布不可变 Git tag、来源代码归档与完整外部实验数据，不仅依赖会过期的 Actions artifacts。

## 8. v3/v4 算子消融：保留有效机制，舍弃无效机制

### 8.1 v3 开发集（预先选择候选）

[GitHub v3 9 组开发集消融](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41506636358)。三类工作流各三个 paired seeds，种群 30 / 代数 100 / 每算法 3030 次目标函数评价，真实 WorkflowSim 回放后计算每个工作流的固定参考点 HV。

| Mechanism | Mean paired simulated HV change vs v2-global | Positive cases |
|---|---:|---:|
| Resource-aware VM mutation | +4.643% | 8/9 |
| Pareto-archive block recombination | **+5.661%** | 6/9 |
| Both combined | +3.965% | 7/9 |

根据事前记录的**开发集平均相对 HV 增益**选择 v3-archive 进入保留集。不能以同一组数据选择模型又声称独立验证。

### 8.2 预留两类工作流的独立验证

[Epigenomics + Inspiral 10 组成功的 v3 held-out run](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41507118883)。

- Epigenomics_24：相比 v2-global +0.903% 平均 paired HV，3/5 种子更好。
- Inspiral_30：相比 v2-global +4.142% 平均 paired HV，3/5 种子更好。
- 10 个保留集配对总体 +2.522%，6/10 更好，**不足以单独支持显著性声明**。

### 8.3 与现有算法的直接对照

[完整 5×5×4 种算法的 30×100 真实仿真对照](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41507243548)。

| v3-archive 对照对象 | 25 组 mean paired HV difference | v3 胜出 |
|---|---:|---:|
| NSGA-II | **−3.146%** | 3/25 |
| Scalar FLA-3W | +0.178% | 10/25 |
| MLEAO reconstructed | +2.813% | 14/25 |

**结论：v3 只证明相对自己的旧版有改进，仍未证明优于标准 NSGA-II。**

### 8.4 拒绝无效的 v4

[新增 NSGA-II 式 Pareto 拥挤距离环境选择的独立消融](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41508089777)：v4-crowding 相比 v3-archive 在 9 组开发集平均 paired HV **−3.803%**；与资源感知变异组合后 **−1.823%**。两种变体都未入选，保留在研究分支上供复现，不把失败结果隐藏。

## 9. 关键因果问题：改变评价模型是否真的改变优化质量？

[25 组真实仿真 NSGA-II 旧版 vs stage-in-aware 评价模型](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41509031050)。

**配对控制：** 两组均为同一份 NSGA-II 代码、30 population、100 generations、3030 次目标调用、相同 seed、DAX、VM 池、实际 WorkflowSim 引擎、最终候选模拟回放和同一工作流下冻结 HV reference；唯一实验开关是 `-Dworkflowsim.planningStageInAware=false/true`。算法搜索路径本身会因评价目标不同而变化，这是实验希望测量的因果效应。为公平，两种结果均仅回放所有独特的**规划非支配**候选；不能声称是完整 simulator Pareto front。

| DAG | Mean HV old model | Mean HV stage-in-aware | Mean paired % change | Positive seeds |
|---|---:|---:|---:|---:|
| CyberShake_30 | 40830.8492 | 203194.8401 | **+398.813%** | 5/5 |
| Epigenomics_24 | 1806620.2430 | 2554541.9364 | **+47.083%** | 4/5 |
| Inspiral_30 | 99435.2345 | 108974.2416 | +17.357% | 3/5 |
| Montage_25 | 363.6455 | 372.7709 | +2.510% | 5/5 |
| Sipht_30 | 16523.5311 | 16872.7746 | +2.132% | 4/5 |

**25 组配对中 21/25 真实仿真 HV 改善。** +398.813% 是该条件下的相对 HV 百分比，不代表 Makespan 降低 398% 或所有数据集都有该幅度。跨五种工作流的百分比均值受 CyberShake 异常大的比率强烈影响，**不能代替按工作流报告的效应**。

### 新的、更可靠的研究假设

1. **WorkflowSim stage-in 数据输入时间的错配**比简单的搜索算子微调更可能造成重大性能损失；原任务耗时与输入传输的系统性偏差可通过真实事件追踪、编译回归和固定分配重放验证。
2. 统一、成本一致且具有 replica-cache 意识的通信与执行评价模型，可以让**同一个优化器**获得更好的真正仿真解集，而不是仅改善估计数值。对 NSGA-II 现有数据支持此假设，需要跨另外的优化器和大规模 DAG 再验。
3. 若要发表多目标优化算法论文，仍应在公平、stage-in-aware 模型之上设计并严谨验证新的 FLA/DAG 机制；目前不能宣称 v2/v3/v4 性能超越 NSGA-II。

### 下一步科研验收门槛

- 至少另一类优化器复核评价模型开关的因果效应；模型误差与算法性能结论独立统计。
- 大规模 DAG、异构 VM / 通信瓶颈 / 不同价格环境与 20–30+ 随机种子；报告 HV/IGD、Makespan/Cost、运行时间、数据传输统计、置信区间。
- 清楚区分连续原始 FLA 与离散任务到 VM 的研究适配，记录真实 function evaluations 和模拟器回放预算；不能用一个成功 CI 代替科研结论。
- 对 GitHub fork 与 Windows 本地代码做文件级 SHA-256 对账才能说“两者完全一致”。

## 10. 本轮新增可复现实验入口

- [v3 archive 确认实验 CI](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/blob/fla-baseline/.github/workflows/fla-v3archive-confirm.yml)
- [NSGA-II 旧模型 vs Stage-in-aware 真实调度对照](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/blob/fla-baseline/.github/workflows/stagein-search-impact.yml)
- [v3 预留集评估](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/blob/fla-baseline/.github/workflows/dag-fla-v3-holdout.yml)
- [v4 负结果消融](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/blob/fla-baseline/.github/workflows/dag-fla-v4-pilot.yml)

本报告中的定量结果均来自明确列出的 GitHub Actions run；没有将相互不同的 reference point 下的 HV 绝对值混用。GitHub Actions artifacts 会过期，因此关键汇总及对应链接保存在此 Git 跟踪文档，原始候选与日志目前仍可在相应 Actions 产物下载。

## 11. 独立算法交叉验证：Stage-in 模型改善并非 NSGA-II 独有

为了排除“新评价函数只适用于 NSGA-II”的解释，额外以 **MATLAB FLA v1.0 连续版本的三权重离散改造 FLA-3W** 做相同的控制实验。

[FLA-3W 25 组配对真实 WorkflowSim 实验及 CSV](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41509595684)。

- 搜索算子、随机种子、任务 VM 资源池、工作流文件和真实 simulator 相同。
- 每个模型三个 scalar weights (`0.2 / 0.5 / 0.8`)、合计 3006 次目标评价；仅切换 `-Dworkflowsim.planningStageInAware`。
- 所有访问的**规划非支配**独特分配分别仿真，按每个工作流跨两个模型及全部种子冻结的 HV reference 评分。
- 不把 FLA-3W 当作原生多目标 FLA；不能把模型改善归于 FLA 的新搜索公式。

| Workflow | Old objective mean simulated HV | Stage-in-aware objective mean simulated HV | Mean paired % change | Positive seeds |
|---|---:|---:|---:|---:|
| CyberShake_30 | 113214.3883 | 508749.3282 | **+349.556%** | 5/5 |
| Epigenomics_24 | 4292978.7649 | 4741898.2636 | **+12.664%** | 5/5 |
| Inspiral_30 | 1016514.1552 | 1037270.3152 | +2.079% | 4/5 |
| Montage_25 | 1241.9521 | 1261.4550 | +1.608% | 3/5 |
| Sipht_30 | 208698.1212 | 210560.5836 | +0.894% | 5/5 |

**25 个 paired cases 中 22/25 提升。** 对照 NSGA-II 的相应结果为 21/25 种子提升；两个独立算法在方向上均支持更准确模型的重要性，效果大小差异很大，尤其 CyberShake 的文件读取使旧估计显著失真。

该结果属于 **evaluation-model ablation with two separate solvers**。研究论文应以“真实 WorkflowSim stage-in 约束与 cost 耦合的多目标调度评价/优化框架”为问题与贡献线索，而不是以“某种新的 FLA 在五类工作流上压倒 NSGA-II”为主张。进一步需要真实大规模 benchmark、更多随机种子和自适应仿真选择策略。

**最新可复现 CI：** [fla-stagein-causal-check.yml](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/blob/fla-baseline/.github/workflows/fla-stagein-causal-check.yml)。

**最终解释边界：** 上述 HV 都是各自 experiment run 内的冻参考点指标，不可把不同表格的绝对 HV 混算。通过计划层非支配筛选的仿真回放仍非全候选 simulator Pareto 集。尚未进行 GitHub vs Windows 本地项目的 SHA-256 文件级对比。
