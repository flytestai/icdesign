---
id: 02-06a-setup-hold
no: 28
stage: 2
title: Setup 与 Hold：两条红线与四种 Corner
en: Setup, Hold and Corners
hours: 2
minutes: 30
tags: [setup, hold, corner, FF, SS, TT, RC corner, PVT, WCS, BCF, OCV, POCV]
summary: 时序检查只有两件事：数据不能太晚（setup），也不能太早（hold）。这一课把这两条红线的判据写清楚，然后讲清它们各自该在什么条件下检查——corner 为什么分 FF/SS/TT、RC corner 的 Cmax/Cmin/RCmax/RCmin 由线宽 W、厚度 T、介质厚 H、间距 S 怎么决定、为什么 setup 看 SS+RCmax 而 hold 看 FF+RCmin，最后讲 OCV 与 POCV 这两种片上偏差建模。
---

## 时序检查只有两件事 {#why}

:::goal 能写出 setup 与 hold 的 slack 判据；能说出 setup 查最慢、hold 查最快的理由；能解释 FF/SS/TT 与 PVT 的对应关系；能说出 Cmax/Cmin/RCmax/RCmin 分别由 W/T/H/S 怎么组合出来；能说清 WCS 与 BCF 各是什么组合；知道 OCV 与 POCV 的区别。
:::

上一课（SDC）给的是"要求"：周期多长、外部给多少延迟。这一课讲的是**怎么判合格**——工具算出到达时间（arrival）和需求时间（required），两者一比，就是 slack。

```
setup:  slack = required(下一个时钟沿) - arrival(数据最晚到)     必须 ≥ 0
hold:   slack = arrival(数据最早到)   - required(当前时钟沿之后)  必须 ≥ 0
```

一句话记：**数据必须在 T1 到 T2 这个窗口里到，早了晚了都是错。**

## Setup：不能太晚 {#setup}

:::term setup | 建立时间
数据必须在**下一个时钟沿到来之前**稳定一段时间，这段提前量要求就是 setup 检查。**不满足 = 数据来不及被采到。**
:::

- 物理含义：这一拍的数据，要在下一拍的时钟沿"抓"之前就位；
- 检查的是**最慢**的情况——所以用**延迟最大**的库与 RC（慢 corner）；
- 表现：频率提不上去、WNS 为负、报告里一堆 `setup violation`；
- 修法（后端手段）：插 buffer 打拍不行（那是前端），能做的是换大驱动单元、缩短走线、调整位置、降密度。

## Hold：不能太早 {#hold}

:::term hold | 保持时间
数据在**当前时钟沿之后**还必须保持一段时间不变，否则会把该采的旧值冲掉。**不满足 = 数据跑太快，把上一拍冲了。**
:::

- 检查的是**最快**的情况——所以用**延迟最小**的库与 RC（快 corner）；
- **hold 是硬伤**：它和频率无关，你把时钟降到 1Hz 也修不好；一旦流片回来有 hold 问题，芯片基本就是废片；
- 修法：**插 delay（buffer）**把太快的数据拖慢——这是唯一常规手段。

:::pitfall 只看 setup，把 hold 留到最后
**现象**：setup 全收敛，报告一片绿，流片回来部分芯片上电即死。

**原因**：hold 违例不会因为降频而消失，而且 hold 的修法（插 delay）会**反过来让 setup 变差**。所以 hold 必须和 setup 一起收敛，通常做法是先修 hold（在 route 后），再回头确认 setup 没被破坏。

**记住**：**setup 决定"能跑多快"，hold 决定"能不能活"。**
:::

## Corner：为什么要分 FF / SS / TT {#corner}

:::term corner | 工艺角
制造偏差导致晶体管有快有慢。**FF / SS / TT** 是三种典型组合：取决于 NMOS 和 PMOS 各自偏快还是偏慢。
:::

:::fig pr-ff-ss-tt | FF / SS / TT 三种 process corner 的含义
:::

| Corner | 含义 | cell delay |
|---|---|---|
| **FF** | Fast-Fast：NMOS 快、PMOS 也快（fast process） | **最小** |
| **SS** | Slow-Slow：两个都慢（slow process） | **最大** |
| **TT** | Typical-Typical：都典型（standard process） | 中间 |

**为什么要两端都查？** 因为芯片造出来不可能是"恰好典型"：

- 偏快的那批（FF）→ 数据跑太早 → **hold 风险**；
- 偏慢的那批（SS）→ 数据跑太晚 → **setup 风险**。

只查 TT 等于假设"每颗芯片都完美"，这在量产里不成立。

## RC corner：线也有四种极端 {#rc}

线延迟不只看工艺，还要看**金属的几何偏差**。四个几何量决定一切：

```
        ← W（线宽）→  ← S（线间距）→
    ┌────────────────┐  ┌──────────┐
    │   metal  ▔▔▔▔  │  │  metal   │   ↕ T（金属厚度）
    └────────────────┘  └──────────┘
    ─────────────────────────────────  ↕ H（层间介质厚度）
```

:::fig pr-rc-corner | 各种不同的 RC 环境：Cmax / Cmin / RCmax / RCmin 由 W、T、H、S 决定
:::

| RC corner | 几何条件 | 结果 | 通常影响 |
|---|---|---|---|
| **Cmax（Cworst）** | W、T 大，H、S 小 | **电容最大** | setup 较差 |
| **Cmin（Cbest）** | W、T 小，H、S 大 | **电容最小** | hold 较差 |
| **RCmax（RCworst）** | W、T、H 小，S 大 | **电阻电容都最大** | setup 较差 |
| **RCmin（RCbest）** | W、T、H 大，S 小 | **电阻电容都最小** | hold 较差 |
| **typical（normal）** | 标准状态 | 中间值 | 参考 |

直观理解（不用背公式，记方向即可）：

- **电容**主要由"两块金属面对面"决定：**W、T 大（金属截面大）+ H、S 小（离得近）→ C 大**；
- **电阻**由"细、薄、长"决定：**W、T、H 小（截面小）→ R 大**。

## PVT：三个字母锁死一个 corner {#pvt}

| 字母 | 含义 | 极端取值 |
|---|---|---|
| **P** | Process 工艺 | FF（快）/ SS（慢）/ TT（典型） |
| **V** | Voltage 电压 | 高压（快）/ 低压（慢） |
| **T** | Temperature 温度 | 低温（快）/ 高温（慢，先进工艺可能反转） |

组合出来的两条"最坏线"：

:::term WCS | Worst Case Slow
**SS + 低压 + 高温 + RCmax** —— 器件最慢、线也最慢的组合，用来查 **setup**。
:::

:::term BCF | Best Case Fast
**FF + 高压 + 低温 + RCmin** —— 器件最快、线也最快的组合，用来查 **hold**。
:::

对照文档的描述：

- **FF corner 通常出现在高压 + 低温（如 -40℃）** → 器件延时最小、信号传输最快；
- **SS corner 通常出现在低压 + 高温（如 125℃）** → 器件延时最大、信号最慢。

:::tip 一条口诀收住这一节
**setup 查最慢（SS + 低压 + 高温 + RCmax = WCS）**
**hold 查最快（FF + 高压 + 低温 + RCmin = BCF）**

（先进工艺的低温反转会让"低温 setup"也变坏，所以低温 corner 也要单独跑——lib 课讲过。）
:::

## MMC：为什么还要乘上"模式" {#mmc}

:::term MMC / MMMC | Multi-Mode Multi-Corner
多模式多角。**光有工艺角还不够**——同一颗芯片在不同工作模式下（功能 / 扫描测试 / 超频），时钟结构与频率都不一样，所以 corner 还要再乘上 mode，得到一组 analysis view。
:::

- **Function 模式**：正常工作，主优化对象；
- **Scan 模式**：DFT 插入扫描链后的测试模式。**综合阶段先给纯功能网表，之后再合并 DFT 逻辑生成带 scan 的网表**——这就是上一课讲的 S1 / S2；
- 有的项目还有超频（performance）模式。

**MMC 的要求是：所有 corner × mode 的组合都收敛**，而不只是主 corner 好看。具体怎么配（library set / rc corner / view），下一课 MMMC 专讲。

## OCV 与 POCV：同一颗芯片内部也有快慢 {#ocv}

前面讲的 corner 是"**芯片之间**的偏差"（这颗快那颗慢）。但**同一颗芯片内部**，不同位置的器件也会有快慢差——比如靠近时钟源的和角落里的。

:::term OCV | On-Chip Variation 片上偏差
同一个芯片内部器件/连线的偏差。传统做法是给延迟加一个**固定百分比**（如 ±20%）作为悲观余量，保证"即使最坏也能工作"。
:::

:::term POCV | Parametric OCV
用**统计分布（正态分布）**代替固定百分比来建模偏差：按每个单元的实际敏感度累加偏差，而不是统一乘 1.2 或 0.8。
:::

两者差别一句话：**OCV 是"一刀切加余量"（简单但过悲观，白烧面积）；POCV 是"按统计规律累加"（更准，先进工艺基本都用它）。**

:::pitfall 把 corner 与 mode 弄混
**现象**：报告里明明按 SS 跑了，还是漏掉了问题；或者"我查了最快 corner 怎么还有 setup 违例"。

**原因**：corner（快慢）和 mode（功能/扫描/超频）是两个维度。**扫描模式下的时钟结构和功能模式完全不同**，只在 func 模式下查 SS，等于没查 scan 的时序。

**做法**：先确认"这个 view 是哪个 mode × 哪个 corner"，再看数字（下一课有专门讲 view 的命名与配置）。
:::

## 动手：算一次 slack {#lab}

把下面几个数改掉，体会"晚一点 / 早一点"对两条红线的影响。**注意这里全部用 ps 的整数**——真实签核数据也常以 ps 为单位，避免浮点误差（0.35 + 1.2 在浮点里会变成 1.5499999…）：

:::tclrun
# ---- setup 检查：数据最晚到达 vs 下一个时钟沿（单位：ps）----
set period 2000                               ;# 时钟周期 2000ps = 2ns
set t_launch 350                              ;# 起始触发器 clk→Q 的延迟
set t_logic 1200                              ;# 组合逻辑 + 线延迟（最慢）
set t_setup 100                               ;# 结束触发器的 setup 要求
set arrival [expr {$t_launch + $t_logic}]     ;# 数据实际最晚到达时刻
set required [expr {$period - $t_setup}]      ;# 必须在此时刻之前稳定
puts "setup: arrival=$arrival ps  required=$required ps  slack=[expr {$required - $arrival}] ps"

# ---- hold 检查：数据最早到达 vs 当前时钟沿之后 ----
set t_launch_fast 120                         ;# 起始触发器（最快 corner）
set t_logic_fast 50                           ;# 组合逻辑 + 线延迟（最快）
set t_hold 80                                 ;# 结束触发器的 hold 要求
set arrival_fast [expr {$t_launch_fast + $t_logic_fast}]
puts "hold : arrival=$arrival_fast ps       required=$t_hold ps   slack=[expr {$arrival_fast - $t_hold}] ps"

# ---- 把逻辑延迟调大 300ps，看 setup 怎么变 ----
set arrival2 [expr {$t_launch + $t_logic + 300}]
puts "逻辑慢 300ps 后 setup slack=[expr {$required - $arrival2}] ps"
:::

:::lab 三问
1. 把 `t_logic` 从 1200 加到 1500，setup slack 变多少？hold slack 变了吗？为什么？
2. 把 `period` 从 2000 降到 1000，setup slack 变成多少？（这就是提频的代价）
3. 若 hold slack 是负的，工程上怎么修？为什么"插 delay"会让 setup 变差？

验收标准：三问都能答，并能说出"setup 看最慢路径、hold 看最快路径"在这个算例里怎么体现。
:::

:::quiz
setup 与 hold 的 slack 公式分别是什么？| setup: required(下一时钟沿 - setup) − arrival(最晚到)；hold: arrival(最早到) − required(当前沿 + hold)。两者都必须 ≥ 0。
为什么 setup 查最慢、hold 查最快？| setup 是"来不及"，最坏发生在器件/线都最慢时；hold 是"太早"，最坏发生在器件/线都最快时。
FF / SS / TT 分别是什么意思？| Fast-Fast（NMOS、PMOS 都快，delay 最小）、Slow-Slow（都慢，delay 最大）、Typical-Typical（典型，中间）。
Cmax 与 Cmin 分别由什么几何条件造成？| Cmax：W、T 大且 H、S 小（金属截面大、离得近）→ 电容最大；Cmin：W、T 小且 H、S 大 → 电容最小。
WCS 和 BCF 各是什么组合？用来查什么？| WCS = SS + 低压 + 高温 + RCmax，查 setup；BCF = FF + 高压 + 低温 + RCmin，查 hold。
FF corner 一般在什么电压温度下出现？SS 呢？| FF 通常高压 + 低温（如 -40℃）延时最小；SS 通常低压 + 高温（如 125℃）延时最大。
为什么只查 TT 不够？| 制造有偏差，芯片会落在 FF~SS 之间；只查典型等于假设每颗都完美，量产必挂。
OCV 与 POCV 的区别是什么？| OCV 用固定百分比（如 20%）给延迟加悲观余量；POCV 用统计分布按单元敏感度累加，更精确、过悲观更少。
为什么 hold 违例比 setup 更致命？| hold 与频率无关，降频也修不好；一旦流片有 hold 问题基本是废片，只能在流片前靠插 delay 修掉。
:::

:::check
- 能写出 setup / hold 的 slack 判据，并说出"早了晚了都是错"
- 能解释 setup 查慢、hold 查快的物理原因
- 能说出 FF/SS/TT 与 delay 大小、PVT 极端条件的对应
- 能说出 Cmax/Cmin/RCmax/RCmin 由 W/T/H/S 的组合决定
- 能背出 WCS 与 BCF 的完整组合及各自用途
- 能说清 corner 与 mode 是两个维度，MMC 要求全组合收敛
- 能说出 OCV（固定百分比）与 POCV（统计分布）的区别
:::
