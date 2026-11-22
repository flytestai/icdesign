---
id: 03-07-fix-timing
no: 18
stage: 3
title: 修时序：六种手段和它们的代价
en: Timing Closure
hours: 6
minutes: 55
tags: [时序, 优化, ECO, hold]
summary: 违例不是"点一下优化就没了"。这一课讲六种修时序手段的适用场景与代价，以及一条最容易踩的坑：先修 hold 还是先修 setup。
---

## 六种手段一张表 {#table}

| 手段 | 怎么做 | 有效场景 | 代价 |
|---|---|---|---|
| 换大驱动单元（upsize） | `X1` → `X4` | 驱动能力不足、线长 | 面积↑、功耗↑ |
| 换低阈值单元（LVT） | `_HVT` → `_LVT` | 逻辑本身慢 | 漏电↑（静态功耗涨） |
| 插缓冲器（buffer） | 长线中间插 | 线延迟占主导 | 面积↑、拥塞↑ |
| 删缓冲器 | 去掉多余的 | hold 违例 | 可能影响驱动 |
| 挪位置（placement ECO） | 把单元靠近 | 线太长 | 可能造成新拥塞 |
| 调 skew（useful skew） | 时钟晚到/早到 | 局部紧张路径 | 会影响相邻路径 |

:::term ECO | 工程变更单
Engineering Change Order。指在不动整体流程的前提下，对设计做小范围修改（换一个单元、插一个 buffer、挪一个位置）。

后端 80% 的时序修复是靠 ECO 完成的，因为重跑全流程太慢。
:::

## 手段一：upsize 与换阈值电压 {#upsize}

```tcl
# 换单元尺寸（同一功能，驱动能力更强）
ecoChangeCell -inst u_core/u_alu/add_32/U12 -cell NAND2_X4

# 换阈值电压（同尺寸，更快但漏电更大）
ecoChangeCell -inst u_core/u_alu/U15 -cell NAND2_X1_LVT

# 批量：把所有驱动不足的单元换大一档（慎用，会连锁）
setOptMode -effort high
optDesign -preCTS -drv
```

:::term Vt | 阈值电压
晶体管的"开启门槛"。门槛低（LVT）→ 开得快 → 延迟小，但关不严 → 漏电大；门槛高（HVT）→ 慢但省电。

库里通常有 HVT / SVT / LVT 三档，后端按路径紧张程度混用，这叫 **multi-Vt 优化**。
:::

:::pitfall LVT 用太多，功耗爆炸
LVT 单元速度快，新手容易"全都换 LVT，时序立刻好了"。

结果：静态功耗（leakage）涨 3~5 倍，芯片发热超标，签核阶段被功耗报告打回来。

**正确做法：只有真正紧张的路径才用 LVT，其余保持 HVT/SVT。** 一般 LVT 占比控制在 10%~20%。
:::

## 手段二：插 buffer {#buffer}

长线（比如跨越大半个芯片的连线）延迟主要由线电阻电容决定，插 buffer 把长线切成几段，能显著降延迟。

```tcl
# 工具自动插（推荐）
optDesign -preCTS -buffering

# 手工插（精确控制时用）
insertBuffer -net u_core/net_1234 -location 120 340 -cell BUF_X2
```

:::scene 什么时候该怀疑"线太长"
看时序报告的路径延迟构成：

```
Data path:
  u_reg/Q -> u_alu/A     net delay 0.62ns  (78%)   ← 线延迟占大头
  u_alu/Z -> u_reg2/D    cell delay 0.18ns (22%)
```

线延迟占 70% 以上 → 说明问题在"距离"，不在"逻辑"。这时候 upsize 收效有限，应该挪位置或插 buffer。
:::

## 手段三：挪位置 {#move}

```tcl
# 把某个单元挪到指定坐标（placement ECO）
placeInstance u_core/u_alu/U20 180 260

# 或者让工具重新做局部布局
refinePlace
```

挪位置是**最有效但最危险**的手段：挪对了线长直线下降，挪错了会造成新拥塞，甚至把别的路径搞崩。

规矩：**一次只挪几个，挪完立刻看拥塞和时序报告。**

## 手段四：useful skew {#skew}

这是 CTS 阶段的"高级技巧"，但概念现在就要懂。

同一时钟沿，A→B 路径差 0.1ns。如果让 B 的时钟**晚到 0.1ns**，B 就多出 0.1ns 时间接收数据，路径就过了。

代价：B 发出的路径（B→C）少了 0.1ns，可能变违例。

```tcl
setUsefulSkewMode -maxSkew 0.15 -usefulSkewMode yes
optDesign -postCTS -hold
```

:::term Useful Skew | 有用偏斜
故意制造 skew，把时间从"有余量的路径"借给"紧张的路径"。

它不是免费的：借来的时间一定从别处扣。所以只在**局部**用，且要检查被扣的那条路径还够不够。
:::

## 最容易踩的坑：先修 hold 还是先修 setup {#order}

**正确顺序：先修 setup，再修 hold。**

原因：

1. 修 setup 常用 upsize / 挪位置 / 插 buffer，这些动作会**改变路径延迟**，可能让已经修好的 hold 又坏。
2. 修 hold 常用插延迟单元，这些单元**几乎不影响 setup**（只加在快路径上）。

所以先做"影响面大"的 setup，再做"影响面小"的 hold。

:::pitfall 顺序搞反，白干两轮
新手常做：先花两小时把 hold 修干净，再去修 setup。修 setup 时插了 buffer、换了单元，hold 又冒出 200 条违例。

回头再修 hold，又影响 setup……来回两三轮，一天没了。

**记住：setup → hold → 最后再整体验一遍。**
:::

## 时序修复的标准动作序列 {#flow}

```tcl
# 1. 先看全局：违例分布
reportTiming -max_paths 50 -slack_lesser_than 0 > rpt/viol_pre.rpt

# 2. 修 setup（preCTS 阶段）
setOptMode -effort high -fixFanoutLoad true
optDesign -preCTS

# 3. CTS 之后修 setup + drv
optDesign -postCTS

# 4. 修 hold（postCTS）
setOptMode -holdTargetSlack 0.05     # 留 50ps 余量，别卡在 0
optDesign -postCTS -hold

# 5. 布线后再来一轮（postRoute）
optDesign -postRoute
optDesign -postRoute -hold

# 6. 最终验证
timeDesign -postRoute -outDir rpt/final
```

:::tip 为什么要留余量（holdTargetSlack 0.05）
如果修到 slack = 0.000，任何一点工艺偏差（OCV、电压波动）都会让它变负。

**签核不是"刚好过"，是"留出安全边际"。** 一般 hold 留 30~50ps，setup 留 50~100ps。
:::

:::lab 动手：从报告判断该用哪种手段
给三条路径的延迟构成，判断修法：

| 路径 | 单元延迟 | 线延迟 | 判断 |
|---|---|---|---|
| A | 0.85ns | 0.10ns | ? |
| B | 0.30ns | 0.70ns | ? |
| C | 0.20ns | 0.05ns（但 fanout = 48） | ? |

参考答案：

- A：单元延迟占绝对主导 → 换 LVT 或 upsize 逻辑链上的关键单元。
- B：线延迟占主导 → 挪位置 / 插 buffer，upsize 效果有限。
- C：延迟不大但 fanout 极高 → 插 buffer 树（fanout 负载问题）。

过关标准：能说出每条路径"为什么选这个手段"，而不是笼统说"优化一下"。
:::

:::check
- 能列出六种修时序手段及各自代价
- 知道 LVT 用太多会导致漏电爆炸
- 会从延迟构成判断该用哪种手段
- 记得"先 setup 后 hold"的顺序和原因
- 知道签核要留余量而不是卡 0
:::

:::quiz
upsize 和换 LVT 的区别是什么？|upsize 是同功能换更大驱动（面积↑），换 LVT 是同尺寸换低阈值（速度快但漏电↑）。
线延迟占总延迟 70% 以上，应该优先做什么？|挪位置或插 buffer 把长线切开，upsize 效果有限。
为什么修时序要先 setup 后 hold？|修 setup 的动作（upsize/挪位置/插 buffer）会改变延迟、可能破坏 hold；修 hold 的延迟单元对 setup 影响小。
`optDesign -postCTS -hold` 里 `-hold` 的作用？|只做 hold 修复（插延迟单元），不动 setup。
为什么要设 holdTargetSlack 0.05 而不是 0？|留安全边际，防止工艺偏差/电压波动让 slack 变负。
:::
