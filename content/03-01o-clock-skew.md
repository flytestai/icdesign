---
id: 03-01o-clock-skew
no: 31o
stage: 3
title: 时钟偏斜：从时钟树指标定位到具体路径
en: Clock Skew Debugging
hours: 0
tags: [Innovus, CTS, STA, 时钟偏斜]
summary: 用日志、时钟树报告和 STA 路径报告分别检查时钟目标、组内分布和具体收发端的到达差。
---

## 三份报告，各回答一个问题 {#report-entries}

:::fig innovus-practice-o.svg | 原创教学示意图 · 偏斜先判断看的是整组还是一条路径
:::

:::note 原创专题
本讲按钉钉目录第 19 项的主题编排。排查方法、算例和自检均为原创，不使用原文、原图或项目参数。
:::

**运行日志**回答「本次实现按什么目标工作」。先查 CTS 阶段、作用的时钟和偏斜组、约束是否加载，以及是否有未覆盖的 sink。目标偏斜（target skew）是优化目标，不是生成结果；日志里的数字先分清是目标、估计值还是最终统计。**时钟树报告**回答「组内哪些分支早或晚」。在同一口径下找最早和最晚的 sink，并查看插入延迟分布；组内极值不一定构成真实的时序路径。**STA 路径报告**回答「这条收发路径是否通过」。展开实际的 launch 和 capture 时钟段，核对参考边沿、早晚延迟、传播状态以及共同路径悲观量移除（CPPR）。三份报告不能互相替代，基础流程见 [CTS 基础课](/lesson/03-08-cts/)。

## 先统一口径，再解释正负号 {#skew-convention}

**Global skew** 是同组同口径内最晚与最早 sink 的到达差，为非负值；也可出现不同边沿或视图分别报告的结果，不能拿未对齐的极值直接相减。**Local skew** 则针对有时序关系的收发点，本讲约定 `local skew = capture 时钟网络延迟 − launch 时钟网络延迟`；正值表示接收时钟的网络延迟更大。比较两次运行要固定视图、时钟组、参考边沿和寄生阶段，再核对早晚延迟与 CPPR 是单独列出还是已经折入结果，避免重复加回。对于跨周期、分频或移相的生成时钟，参考边沿本来就可能相隔很远，要用边沿的相对关系构造检查，不能把时间差全解释为网络偏斜。

## 实验输入：组偏斜超目标，端点又有 hold 违例 {#practice-step-03}

固定布线后快照、提取寄生、库和时钟约束，选择 `CLK_A` 的上升沿路径 `FF_L -> FF_C`。时钟周期 400 ps，setup 使用下一上升沿，hold 使用同一参考上升沿。组统计用一个固定的分布视图；路径的 setup 和 hold 各自使用早晚组合，因此下面这三类数字不可混算。所有输出均为原创的合成摘录，不是 Innovus 或签核工具的真实格式，也不是可执行命令。实验保存原始检查点，修改不触碰周期、不改不确定性、不修改时序例外。

```text
CTS RUN LOG: clock=CLK_A  group=G_A  target_global_skew=50 ps
TREE BASELINE: view=tree_ref  edge=rise  propagated=yes
  min sink FF_E/CK = 80 ps; max sink FF_X/CK = 140 ps
  global skew = 60 ps; FF_C/CK = 132 ps on branch BR_C
STA BASELINE: path FF_L/Q -> FF_C/D, units=ps
  check   ref_delta  launch_net  capture_net  data   cons  unc  CPPR  slack
  setup         400          95          125   365     30   20     5    +20
  hold            0          90          140    65     15   12     4     -8
```

组统计的实测值超目标 10 ps；`FF_X` 最晚，并不意味着 `FF_X` 是这条 hold 路径的端点。再看 STA：本例 setup 使用迟到的 launch、早到的 capture，网络延迟差为 `125 − 95 = +30 ps`；hold 使用早到的 launch、迟到的 capture，差为 `140 − 90 = +50 ps`。同一个物理时钟树在两种检查下得到不同偏斜是正常的，既不能拿全局 60 ps 作路径偏斜，也不能把 setup 的 30 ps 照搬到 hold。

## 按参考边沿重算两类 slack {#practice-step-04}

本例的 `data` 从 launch 时钟引脚计到 capture 数据引脚，含对应的 clk-to-Q 和数据路径延迟；`cons` 是接收单元的 setup 或 hold 要求；`unc` 是扣除的不确定性；CPPR 在此表中单列为正的松弛修正，不假定所有报告都以同样方式显示。setup 的余量是「capture 要求时间减数据到达时间」，hold 则反过来，是「数据到达时间减最早允许时间」。两种检查必须分别代入自己的数据和时钟段。

```text
setup slack = ref_delta + (capture_net - launch_net) - data - cons - unc + CPPR
            = 400 + (125 - 95) - 365 - 30 - 20 + 5 = +20 ps
hold slack  = data - ref_delta - (capture_net - launch_net) - cons - unc + CPPR
            = 65 - 0 - (140 - 90) - 15 - 12 + 4 = -8 ps
```

因此，在其他项固定的这个模型里，接收边沿变晚会给 setup 增加余量，却让 hold 吃掉等量的余量。同理，提前接收分支时要预留 setup 退化空间。如果目标只剩「全局偏斜越小越好」，可能压缩了一些原来对 setup 有利的局部偏斜；全局指标适合给出定位入口，不足以替代对真实路径的裁决。

## 拆开两条时钟支路，验证根因 {#trace-branches}

先在 STA 展开的时钟段找到共同分叉点，从该点往下比较两侧缓冲级数、驱动边沿、负载、走线和寄生。再到版图检查 `BR_C` 是否与这组晚到 sink 一致。此例假定接收端 `FF_C` 与组内最晚 `FF_X` 共享 `BR_C`，而启动分支独立；寄生分段检查发现 `BR_C` 的共同段有一处绕宏的折返。把晚到归因于折返之前，还要确认多出来的延迟主要出现在该段，而不是来自分叉点上游或接收单元内部。

```text
                 +-- BR_L ------------------ FF_L/CK
CLK_A -- split --+
                 +-- BR_C -- detour --+----- FF_C/CK
                                     +----- FF_X/CK
```

若接收端在宏内，先确认报告到达点是宏时钟输入还是模型内部节点；库模型的时序弧或约束不能直接算成外部树延迟。类似地，版图上 data 与 clock 的投影交叉不是耦合证据：先核对层别、提取的耦合项和串扰分析差异，才能判断是否该动那段线。没有证据时不要为了让图看起来整齐而改数据网。

## 实施并对照：提前接收端，也会减少 setup 余量 {#practice-step-06}

在保留缓冲拓扑和负载组的前提下，实验只修改 `BR_C` 的折返走线，局部增量布线后重提取。通过同样的报告入口复跑组统计和路径分析。以下假设只有接收侧时钟延迟发生变化，数据、约束及 CPPR 数值不变；真实复跑中这些项也可能改变，不应手工沿用旧报告。

```text
TREE AFTER: view=tree_ref  edge=rise  propagated=yes
  min sink FF_E/CK = 80 ps; max sink FF_X/CK = 120 ps
  global skew = 40 ps; FF_C/CK = 114 ps
STA AFTER: path FF_L/Q -> FF_C/D, units=ps
  check   ref_delta  launch_net  capture_net  data   cons  unc  CPPR  slack
  setup         400          95          110   365     30   20     5     +5
  hold            0          90          118    65     15   12     4    +14
```

全局从 60 ps 降至 40 ps，达到 50 ps 的教学目标。setup 的局部偏斜从 +30 ps 降到 +15 ps，余量也从 +20 ps 降到 +5 ps；hold 的局部偏斜从 +50 ps 降到 +28 ps，余量增加 22 ps，变成 +14 ps。这条路径两项都非负，但如果项目要求 setup 至少保留 10 ps 的额外余量，这个改法仍不合格。改善了组指标和负 slack，不能代替检查实际交付门限。

复查时，把 `BR_C` 上所有受影响 sink 列出来，而不只抄录组报告的新极值。特别注意反向路径：当同一只 `FF_C` 改作启动端，提前启动时钟在其他项不变时会给 setup 增加余量，却可能让 hold 恶化。把进出该分支的端点对照登记，并标出修改前后是否由同一对端点取得最差值；否则即使组内最差数值相同，也可能掩盖一条原有路径的退化。若 CPPR 或数据段也变了，再逐项分解差值，不要把 slack 的全部变化归给时钟偏斜。

## 验收与回退：不要只复查被点名的路径 {#practice-step-07}

先以相同视图、边沿、寄生阶段复查组内分布和修改分支的时钟转换时间、负载。然后把受影响 sink 同时作为 capture 和 launch 搜索其他路径；局部提早对进来的路径和出去的路径未必同向，需要复查各签核视图的 setup、hold，以及时钟门控和脉宽检查。最后核对增量改线的连通性、几何 DRC 和邻近网耦合。若组指标达标却引入新的负 slack 或过阈值退化，保存分支和报告差异，恢复原布线及配对的寄生快照后复跑基线；可再比较温和的走线调整，或评估只在目标数据路径上修 hold。不能把缩小不确定性、增添时序例外或放宽时钟周期当成物理修复。

## 自检：算出偏斜，再判断影响 {#review}

:::quiz
树统计最早 80 ps、最晚 140 ps；路径 launch 95 ps、capture 125 ps。两个 skew 各多少？|Global skew 为 60 ps，按本讲约定该路径 local skew 为 +30 ps。若同口径的全局目标为 50 ps，实测超 10 ps。
为什么本例 setup 和 hold 不能共用 +30 ps 的 local skew？|两种检查选取不同的早晚时钟延迟；基线 hold 的网络差等于 140 减 90，即 +50 ps。
改线后目标已达且该路径非负，什么时候仍应回退？|例如签核门限要求至少 +10 ps 的 setup 余量而仅剩 +5 ps，或其他相关路径、时钟电气规则、连通性及几何 DRC 出现新问题。
:::
