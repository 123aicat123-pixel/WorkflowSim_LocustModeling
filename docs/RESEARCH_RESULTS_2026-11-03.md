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
