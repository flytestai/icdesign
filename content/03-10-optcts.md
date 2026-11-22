---
id: 03-10-optcts
no: 21
stage: 3
title: OptCts：时钟树做完只是开始
en: Clock Tree Optimization (OptCts)
hours: 3
minutes: 40
tags: [CTS, OptCts, skew, useful skew, hold]
summary: CTS 把时钟送到每个触发器，但送得不齐、不快、不稳。OptCts 是布线前的第二轮修补：压 skew、压 insertion delay、修 DRV、顺手借用时间修 setup。这一课讲清楚它改什么、不许改什么。
---

## CTS 做完，为什么还要再优化一轮 {#why}

CTS（时钟树综合）的目标只有一个：**把时钟信号送到每一个触发器**。它插缓冲器、算平衡、尽量让各分支长度一致。但 CTS 结束时，树上一定还留着四类问题：

| 问题 | 表现 | 谁在乎 |
|---|---|---|
| skew 偏大 | 同一时钟域内，最晚和最早到达差 200ps 以上 | setup/hold 都吃这个亏 |
| insertion delay 太长 | 时钟从端口到触发器要走 1.5ns | 对外接口时序变差、功耗高 |
| DRV 违例 | 某段时钟线的 transition 太慢、或一个缓冲器带太多负载 | 工艺厂不允许，签核会报 |
| hold 违例 | 同一路径上数据跑得比时钟还快 | **必须在布线前修掉大半** |

:::scene 早上来，hold 报了 800 条
CTS 跑完，`report_timing -delay min` 出来 800 条 hold 违例，最差 -0.31ns。你没修，直接去布线。布线完再回签，hold 变成 -0.52ns——因为**线延迟也吃掉了余量**。

结论：hold 必须在 CTS 后、布线前修掉大部分，否则布线后要重来。
:::

:::term CTS | Clock Tree Synthesis，时钟树综合
把时钟从端口/根节点，用缓冲器和连线，一级一级送到每个触发器的时钟引脚。要做三件事：**连通**（都送到）、**平衡**（尽量同时到）、**驱动够**（信号不变形）。
:::

## 时钟树的五个质量指标 {#metrics}

这五个数字决定时钟树好坏。签核报告里都能查到。

| 指标 | 英文 | 好的标准（经验值） | 太差的后果 |
|---|---|---|---|
| 偏斜 | skew | < 周期的 3~5% | setup/hold 双向恶化 |
| 插入延迟 | insertion delay / latency | 越小越好，通常 < 1ns | 接口时序余量被吃掉、功耗高 |
| 转换时间 | transition / slew | 满足库的 max_transition | DRV 违例，签核不过 |
| 驱动能力 | DRV（max_cap / max_tran） | 无违例 | 时钟波形变形，触发器乱采样 |
| 时钟功耗 | clock power | 占总功耗 20~40% 属正常 | 太高压降、发热 |

:::term Skew | 偏斜
同一个时钟，到达两个触发器的时间差。`skew = 最晚到达 - 最早到达`。

2ns 周期（500MHz）下 skew 200ps，等于**白白吃掉 10% 的时序预算**。所以 CTS 的第一目标就是把 skew 压下来。
:::

:::note 为什么 insertion delay 也要管
时钟从端口进来到触发器的这段延迟，对**芯片内部**的路径是"两边都有、可以抵消"的；但对**输入输出接口**不能抵消——数据从外面来，时钟却在芯片里绕了 1.5ns 才到，接口时序直接崩。

所以顶层设计通常要求 insertion delay 控制在 0.5ns 以内，方法是在芯片中间放时钟根、做对称 H 树。
:::

## useful skew：借时间，但有三条纪律 {#useful}

这是 CTS 阶段最值钱的技巧，也是最容易用错的。

原理一句话：**setup 违例的路径，让捕获触发器（endpoint）的时钟晚一点到，就等于多给了它时间。**

```text
正常：launch 时钟 0ns ──数据 1.9ns──> 捕获时钟 2.0ns   余量 0.1ns
借用：launch 时钟 0ns ──数据 1.9ns──> 捕获时钟 2.2ns   余量 0.3ns  ← 多出 0.2ns
代价：这条路径的下游（从这个触发器出发的路径）少了 0.2ns
```

三条纪律，违反任何一条都会把 setup 违例换成 hold 违例：

1. **只借给"下游还有余量"的触发器**：借之前先看它的 fanout 路径 slack；
2. **一次别借超过周期的 10%**：借太多，hold 一定崩；
3. **借完必须重新跑 hold 检查**：这是硬性步骤，不是可选项。

:::pitfall 借 skew 借出 200 条 hold 违例
新人看到 setup 违例，直接 `set_clock_latency -0.2` 给所有 endpoint 加延迟。结果 setup 好了，hold 崩了 200 条。

正确做法是**按路径借**：只对具体 endpoint 的时钟引脚做 delay，并检查它的 fanout。全局加减延迟是"用一个大锤修一颗螺丝"。
:::

## Innovus 里的 OptCts 怎么做 {#innovus}

CTS 本身和优化是两轮，命令不同：

```tcl
# ---- 第一轮：建树 ----
set_ccopt_property target_max_trans 0.10         ;# 时钟线最大转换时间 100ps
set_ccopt_property target_skew       0.05        ;# 目标 skew 50ps
set_ccopt_property buffer_cells {CLKBUF_X1 CLKBUF_X2 CLKBUF_X4}
ccopt_design -cts                                ;# 只建树，不做时序优化

# ---- 存盘（重要：这一步之后要能回退）----
saveDesign db/06_cts.enc

# ---- 第二轮：优化（就是 OptCts）----
optDesign -postCTS                               ;# 修 setup（含 useful skew）
optDesign -postCTS -hold                         ;# 修 hold
saveDesign db/07_optcts.enc

# ---- 看结果 ----
report_clock_tree -summary                       ;# skew / insertion / DRV 汇总
report_timing -delay_type max -max_paths 20      ;# setup 最差 20 条
report_timing -delay_type min -max_paths 20      ;# hold 最差 20 条
```

| 命令 | 做什么 | 什么时候用 |
|---|---|---|
| `ccopt_design -cts` | 建树，只保证连通和基本平衡 | CTS 第一步 |
| `optDesign -postCTS` | 修 setup，可用 useful skew | 建树之后立刻 |
| `optDesign -postCTS -hold` | 修 hold（插 delay cell / 调 skew） | setup 修完再修 hold |
| `ccopt_design`（不带 -cts） | 建树 + 时序优化一起做 | 熟练后常用，一步到位 |

## ICC2 里的对应做法 {#icc2}

同一件事，命令换一套：

```tcl
# ---- 建树 ----
clock_opt -only_cts -no_clock_route
# 只做树，不布线；-no_clock_route 让时钟线先不布，省时间

save_block

# ---- 优化（OptCts 阶段）----
clock_opt -only_psyn -no_clock_route
# -only_psyn = 只做 post-CTS 的时序优化，不重建树

# ---- 开 CCD（concurrent clock & data），让时钟和数据一起优化 ----
set_app_options -name clock_opt.flow.enable_ccd -value true
clock_opt

save_block

# ---- 看 ----
report_clock_qor -type summary
report_qor
```

:::term CCD | Concurrent Clock and Data，时钟数据协同优化
传统流程是"先建树、再优化数据路径"，两步分开。CCD 让工具同时动时钟和数据，条件是**必须先把时钟树结构定下来**。

好处：能同时兼顾 setup 和 hold，减少反复。代价：跑得慢，且对约束质量敏感。
:::

| 动作 | Innovus | ICC2 |
|---|---|---|
| 只建树 | `ccopt_design -cts` | `clock_opt -only_cts` |
| 树后优化 | `optDesign -postCTS` | `clock_opt -only_psyn` |
| 一起做（CCD） | `ccopt_design` | `clock_opt` + `clock_opt.flow.enable_ccd` |
| 看树质量 | `report_clock_tree -summary` | `report_clock_qor` |
| 存盘 | `saveDesign x.enc` | `save_block` |

## hold 修复：为什么必须现在修 {#hold}

hold 违例的物理含义：**数据跑得太快，把下一个时钟周期该采的值提前冲掉了**。

它有三个特点，决定了必须在 CTS 后修：

1. **跟频率无关**。降频救不了 hold（降频只会让 setup 更松），这是很多人第一反应就错的地方；
2. **布线后会变差**。布线的线延迟会加在数据路径上而不是时钟上（时钟树已经布好了），所以余量会被吃掉；
3. **修法只有两种**：给数据路径加延迟（插 buffer/delay cell），或者给时钟加延迟（调 skew）。

```text
hold 检查：数据到达时间  >  捕获时钟到达时间 + hold 时间
                           ↑ 数据太快 = 早于这个点到达 = 违例
修法 A：数据路径插 delay cell  → 让数据晚点到
修法 B：捕获时钟提前到        → 让要求的时间点提前
```

:::pitfall 用降频来"修" hold
新人：hold 违例了，把周期从 2ns 改成 2.5ns。

结果：setup 更松了（看起来变好），**hold 一条没少**。因为 hold 检查的是同一时钟沿附近的竞争，跟周期无关。

记住这句话：**降频只救 setup，救不了 hold。**
:::

## 报告怎么读：三个数字决定下一步 {#report}

拿到 `report_clock_tree -summary`，只看三个数：

```text
Clock      Skew    Insertion   DRVs   Buffers   Power
clk        0.048   0.612       0      184       12.4mW
```

| 数字 | 判断 | 下一步 |
|---|---|---|
| skew 0.048（周期 2ns 的 2.4%） | 合格 | 不用动 |
| insertion 0.612ns | 合格 | 接口时序紧的话可以再压 |
| DRVs 0 | 合格 | — |
| Buffers 184 | 偏多 | 检查是不是某一支路负载太重 |

如果 skew 是 0.31（15%）：

1. 先看是不是有 **clock gating** 单元挂在不平衡的分支上；
2. 再看是不是某个触发器离得特别远（floorplan 问题）；
3. 最后才考虑加 `set_ccopt_property` 强行压。

:::note 我们实测的那组数据
万门设计（ipa_top，12026 单元）在 ICC2 里跑 `clock_opt`，耗时 9.5 分钟，插了 2636 个 buffer。最终 setup WNS +1.00ns，hold **-0.07ns**。

那个 -0.07ns 就是典型的"没做第二轮 hold 优化"的残留：单 corner、单模式、时间预算紧，先保证 setup 能过。真实项目里这一条会用 ECO 插 delay cell 修掉（见阶段五的 ECO 课）。
:::

:::lab 动手：从报告里判断该不该继续优化
假设你拿到这样一份 summary：

```text
Clock    Skew    Insertion   DRVs   Buffers
clk      0.021   0.480       12     96
clk_div  0.290   1.340       0      412
```

问题：先修哪个？

```text
判断顺序：
1) DRVs 12 是硬违例，签核必挂          -> 先修 transition / max_cap
2) clk_div skew 0.29 太大（周期 2ns 的 14.5%） -> 看是不是分频器后面负载不均
3) clk_div insertion 1.34ns 偏大        -> 根节点位置或树层级太深
4) clk 的 0.021 已经很好，别动它
```

过关标准：能说出"先修 DRV，再修 skew，最后才考虑 insertion"，并解释为什么 DRV 优先（它是硬性工艺规则，skew 只是时序预算问题）。
:::

:::check
- 能说出 CTS 结束后残留的四类问题
- 能背出时钟树五个指标和大致合格范围
- 知道 useful skew 的三条纪律，尤其是"借完必须重查 hold"
- 能写出 Innovus 的 `ccopt_design -cts` → `optDesign -postCTS` → `-hold` 三步
- 能说出 ICC2 里对应的 `clock_opt -only_cts` / `-only_psyn`
- 记住"降频救不了 hold"
:::

:::quiz
CTS 和 OptCts 的分工是什么？|CTS 负责建树（连通、基本平衡、驱动够）；OptCts 在建好的树上做时序优化：压 skew、修 DRV、用 useful skew 修 setup、修 hold。
useful skew 的原理是什么？代价是什么？|让捕获触发器的时钟晚到，等于给它更多时间；代价是这个触发器的下游路径少了同样的时间，可能变成新的 setup 违例。
为什么 hold 违例不能靠降频解决？|hold 检查的是同一时钟沿附近数据与时钟的竞争关系，与时钟周期长短无关；降频只会让 setup 更宽松。
时钟树报告里 DRV 违例和 skew 偏大，先修哪个？|先修 DRV，因为它是硬性工艺规则（max_transition/max_cap），签核一定报；skew 只是吃掉时序预算，可以后修。
`clock_opt -only_cts` 和 `clock_opt -only_psyn` 有什么区别？|-only_cts 只建时钟树；-only_psyn 不重建树，只在已有树上做 post-CTS 时序优化。
:::
