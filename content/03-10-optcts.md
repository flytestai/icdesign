---
id: 03-10-optcts
no: 23
stage: 3
title: OptCts：时钟树做完只是开始
en: Clock Tree Optimization (OptCts)
hours: 3
minutes: 40
tags: [CTS, OptCts, skew, useful skew, hold]
summary: CTS 把时钟送到每个触发器，但送得不一定齐、不一定快、波形也不一定干净。OptCts 是布线前的第二轮修补：压 skew、缩 insertion delay、修 DRV、用 useful skew 顺手救 setup、并把 hold 修掉大半。这一课讲清它改什么、不许改什么、三个数字怎么决定下一步。
---

## CTS 做完，为什么还要再优化一轮 {#why}

:::goal 学完这一课，你能读完一份时钟树汇总报告，用 skew、insertion delay、DRV 三个数判断下一步该修什么，并说清 useful skew 借多少、代价落在哪条路径上。
:::

装修有个分工：水电工负责把水管铺到每个房间（这是 CTS），但铺完不等于好用——有的房间水压大、有的水小，还得有人去调阀门（这是 OptCts）。

CTS 的目标函数很窄：**连通（每个触发器都收到时钟）、平衡（尽量同时到）、驱动够（波形不变形）**。它不负责"这条路径的 setup 差 60ps"，也不负责"这个端点 hold 只有 20ps 余量"——那些要动数据路径、换单元尺寸，风险和工作量都不同，所以分成两轮做。

分两轮还有一个工程上的好处：**能回退**。CTS 存一个点、优化完存一个点，发现优化把 skew 搞坏了，退回上一个点就行；如果合成一步，你只能从头再来。

CTS 结束时，树上一定还留着四类问题：

| 残留问题 | 表现 | 谁最在乎 |
|---|---|---|
| skew 偏大 | 同一时钟域内最晚与最早到达差 200ps 以上 | setup 和 hold 都吃这个亏 |
| insertion delay 太长 | 时钟从端口到触发器要走 1.5ns | 接口时序、功耗、OCV |
| DRV 违例 | 某段时钟线 transition 太慢，或一个 buffer 带太多负载 | 工艺厂规则，签核必挂 |
| hold 违例 | 同一路径上数据跑得比时钟还快 | 必须在布线前修掉大半 |

CTS 刚结束时树上留着的问题，在版图上是有形状的：

:::fig innovus-cts | 时钟树综合后的版图：绿色线条是从时钟源一路分叉到每个触发器的时钟网络，绿点是工具自动插入的缓冲器。重点看有没有分支特别长、分叉是否均匀——上面表格里的四类残留问题（skew、latency、DRV、hold），都能在这张图上找到对应的形状。
:::

从这张图里要看出什么：CTS 的目标函数只管"连通、平衡、驱动够"，图上那些长短不一的分支，就是这一课要收拾的四类问题的源头。

:::scene 早上来，hold 报了 800 条
CTS 跑完，`report_timing -delay_type min` 出来 800 条 hold 违例，最差 −0.31ns。你想着"布线完一起修"，直接进了 route。布线完再签：hold 变成 −0.52ns。

你可能会疑惑：布线让数据变慢，hold 不是应该变好吗？真实的机制不是这样。布线后有件事变了——**时钟线这时才真正布出来**。CTS 只建树、给了时钟网络的位置，route 阶段才按 NDR 把时钟线画成具体的线和 via，launch 端和 capture 端的实际到达时间差（也就是 skew）跟 CTS 报告里的数字不是一回事。再加上串扰、以及 route 期插入的 buffer 改变了最短路径，净效果就是一批 hold 余量被吃掉。

结论：**hold 必须在 CTS 后、布线前修掉大部分**。CTS 报告里的 hold 是"时钟已定、线未定"的结果，它已经比布线后乐观；带着一堆负值进 route，等于把问题交给一个更难回退的阶段。
:::

:::term CTS | Clock Tree Synthesis，时钟树综合
把时钟从根节点用缓冲器和连线一级一级送到每个触发器的时钟引脚。三个目标：连通、平衡、驱动够。它是布局之后、布线之前的一步。
:::

:::term OptCts | Post-CTS Optimization，时钟树后优化
在已经建好的时钟树上做第二轮优化：压 skew 和 insertion delay、修 DRV、用 useful skew 修 setup、插 delay cell 修 hold。

它**不重建树**（重建是 CTS 的事），只调整树的局部和数据的路径。
:::

## 时钟树的五个质量指标 {#metrics}

签核报告里查这五个数，它们决定这棵树能不能用。

| 指标 | 英文 | 好的标准（经验值，40nm 量级） | 太差的后果 |
|---|---|---|---|
| 偏斜 | skew | 全局 < 周期 3~5% | setup 和 hold 双向恶化 |
| 插入延迟 | insertion delay / latency | 越小越好，通常 < 1ns | 接口时序余量被吃掉、功耗高 |
| 转换时间 | transition / slew | 满足库的 max_transition（时钟常要求 < 100~150ps） | DRV 违例，签核不过 |
| 时钟功耗 | clock power | 占总功耗 20%~40% 属正常 | 太高压降、发热、电池寿命 |
| DRV 违例数 | DRV count（max_tran / max_cap / max_fanout） | 0 | 波形变形，触发器可能采样到中间电平 |

这五个数是**互相拉扯**的，不是五个独立指标：

- 想 skew 小 → 多插 buffer 把树做平衡 → buffer 变多 → 功耗上去、insertion delay 变长；
- 想 insertion delay 短 → 树做浅、级数少 → 单个 buffer 带更多负载 → transition 变差；
- 想 transition 好 → 用大驱动 buffer → 输入电容变大 → 上一级负载变重 → 那一级的 transition 又变差。

所以优化不是"把五个数都压到最小"，是**在满足 DRV 和 transition 的前提下，把 skew 和 latency 压到够用**。

:::term Skew | 偏斜
同一个时钟到达两个触发器时钟端的时间差。`skew = 最晚到达 − 最早到达`。

2ns 周期（500MHz）下 skew 有 200ps，等于**白白吃掉 10% 的时序预算**——这条路径上所有逻辑加起来只剩 1.8ns 可用。
:::

:::term Insertion Delay | 插入延迟
从时钟源（端口或根 buffer）到某个触发器时钟端的总延迟。

对芯片内部路径，它是"两边都有、可以抵消"的；对输入输出接口不能抵消——数据从片外来，时钟却在片内绕了 1.5ns，接口时序直接崩。所以顶层设计通常要求在芯片中间放时钟根、做对称的 H 树。
:::

:::note 为什么不能只看 skew
一个极端的例子：把整棵树做得很深，每级都插大 buffer，skew 可以压到 20ps，但 insertion delay 变成 2.5ns、功耗翻倍。这种树"看起来很平衡"，实际上接口时序崩了、芯片发烫。

评一棵树要同时看**平衡（skew）、快（latency）、干净（DRV/transition）、省（power）**，四个维度缺一个都不行。
:::

## useful skew：借时间，但有三条纪律 {#useful}

这是 CTS 阶段最值钱的技巧，也是最容易用错的。原理在第 18 课讲过，这里只讲在时钟树上怎么落地、借多少、代价落在哪。

一句话原理：**setup 违例的路径，让捕获端的时钟晚到一点，等于多给了它时间。**

```text
正常：launch 时钟 0ns ──数据 1.87ns──> 捕获时钟 2.00ns   余量 0.00ns（紧）
借用：launch 时钟 0ns ──数据 1.87ns──> 捕获时钟 2.08ns   余量 0.08ns  ← setup 过了
代价：捕获端这条路径的 hold 余量少 0.08ns；以它为起点的下游路径 setup 少 0.08ns
```

### 手算一次：借 80ps 到底救了谁、害了谁

条件：周期 2.0ns，触发器 clk-to-q 最大 0.15ns，逻辑最大延迟 1.72ns，setup 0.08ns，uncertainty 0.05ns，当前 skew ≈ 0。

**借之前（setup）**

`slack = 2.00 − 0.15 − 1.72 − 0.08 − 0.05 = 0.00ns`

刚好卡在零，一点波动就违例。

**借之后（把捕获端时钟推迟 80ps）**

`slack = 2.08 − 0.15 − 1.72 − 0.08 − 0.05 = 0.08ns`

setup 修好了。

**代价在这一条路径的 hold 上**（hold 的要求时间跟着捕获时钟一起往后移）：

- 借用前：数据最短到达 `0.10 + 0.15 = 0.25ns`，要求 `hold 0.06 + uncertainty 0.03 = 0.09ns`，余量 **+0.16ns**；
- 借用后：要求变成 `0.09 + 0.08 = 0.17ns`，余量只剩 **+0.08ns**。

还算安全。但如果这个端点原本 hold 余量只有 50ps——借用 80ps 之后就是 **−30ps**，你只是把 setup 违例换成了 hold 违例。

所以借之前必须做一次减法：**该端点的 hold 余量 ≥ 要借的量 + 20ps 安全余量**。不满足就别借，改用插 buffer 或换单元。

### 三条纪律

1. **只借给"下游还有余量"的触发器。** 借的是这个触发器的时钟，它会同时影响以它为起点的所有下游路径。先看它的 fanout 路径 slack，最差那条留够 50ps 再借。
2. **一次别超过周期的 10%。** 2ns 周期就是 200ps 上限；工程上单次常用 30~80ps，分几次借比一次借到底安全。
3. **借完必须重新跑 hold 检查，并把 skew 报告重出一份。** 这不是可选项——借 skew 改的就是时钟树，前面所有 skew 数字全部作废。

:::term Useful Skew | 有用偏斜
故意让某些触发器的时钟早到或晚到，把时序余量从"有余量的路径"挪给"差一点的路径"。

它不是"让时钟不齐"，而是**有意识地控制不齐**：知道哪条路径需要时间、哪条路径给得起。
:::

:::pitfall 全局加 latency，一次借出 200 条 hold 违例
现象：看到 setup 违例，直接 `set_clock_latency -0.2 [get_clocks clk]`，给整个时钟域加延迟。
结果：setup 数字好看了，hold 崩了 200 条，skew 报告也变得没法看。
原因：全局改 latency 等于同时动了所有端点，每个端点的 hold 余量都被吃掉 200ps。
处理：按端点借——只对具体引脚做 `set_clock_latency -late/-early`（或用工具的 useful skew 引擎指定路径），借完立刻查 hold。**用大锤修一颗螺丝，砸坏的是整面墙。**
:::

:::pitfall 时钟树还没定稿就开始借 skew
现象：place 阶段就手工调了一堆 latency，CTS 一跑完全被覆盖，白干。
原因：CTS 会重建整棵树，除非你把这些约束显式传给它（`set_ccopt_property` 的 skew 组），否则工具的平衡算法会把你调的延迟抹平。
处理：useful skew 放在 CTS 之后、OptCts 里做；CTS 阶段只给"哪些端点允许偏斜"的组约束。
:::

## Innovus 里的 OptCts 怎么做 {#innovus}

CTS 和优化是两轮，命令分开，中间存一个回退点。

```tcl
# 作用：Innovus 里完整的 CTS → OptCts 三段式
# 用法：placement 之后、route 之前；每段跑完都存盘，出问题能退回
# ---- 第一段：建树（只保证连通和基本平衡）----
set_ccopt_property target_skew       0.05                  ;# 目标 skew 50ps，约 2ns 周期的 2.5%
set_ccopt_property target_max_trans  0.10                  ;# 时钟线最大 transition 100ps
set_ccopt_property buffer_cells {CLKBUF_X2 CLKBUF_X4 CLKBUF_X8}   ;# 限定可用缓冲器，别让工具乱挑
ccopt_design -cts                                          ;# 只建树，不做时序优化
saveDesign db/06_cts.enc                                   ;# 回退点①：建树后的原始状态

# ---- 第二段：修 setup（含 useful skew）----
optDesign -postCTS                                         ;# 修 setup + DRV，允许工具借用 skew
saveDesign db/07_optcts_setup.enc                          ;# 回退点②：setup 修完

# ---- 第三段：修 hold ----
optDesign -postCTS -hold                                   ;# 插 delay cell / 调局部 skew 修 hold
saveDesign db/08_optcts.enc                                ;# 回退点③：可以交给 route 的状态

# ---- 出报告 ----
report_clock_tree -summary > rpt/optcts_tree.rpt           ;# skew / insertion / DRV 汇总
report_timing -delay_type max -max_paths 20 > rpt/optcts_setup.rpt   ;# setup 最差 20 条
report_timing -delay_type min -max_paths 20 > rpt/optcts_hold.rpt    ;# hold 最差 20 条
```

| 命令 | 做什么 | 什么时候用 |
|---|---|---|
| `ccopt_design -cts` | 只建树：连通 + 基本平衡 | CTS 第一步 |
| `optDesign -postCTS` | 修 setup 和 DRV，可用 useful skew | 建树之后立刻 |
| `optDesign -postCTS -hold` | 修 hold：插 delay cell、微调 skew | setup 修完之后 |
| `ccopt_design`（不带 `-cts`） | 建树 + 时序优化一起做 | 流程熟了以后常用，省一次迭代 |

顺序为什么不能反：**先 setup 后 hold**。因为修 setup 会插 buffer、换单元、动时钟，这些动作会改变 hold；反过来先修 hold，再修 setup 时又会把 hold 打回去。先做影响面大的那个，后做收尾的那个。

命令里的 `-postCTS` 不是"再来一遍 CTS"，它是告诉工具"当前数据库的时钟已经建好、请按传播时钟（propagated clock）算时序"。少了这个标记，工具可能还按理想时钟算，算出来的 slack 是假的。

存盘点也有讲究：三个 `.enc` 按 `06_/07_/08_` 递增命名，是为了让"哪一步出了问题"一眼可见。真实的项目里目录会被塞满几十个版本，命名混乱等于放弃回退能力。

## ICC2 里的对应做法 {#icc2}

同一件事，命令换一套，逻辑完全一样：

```tcl
# 作用：ICC2 里把"建树"和"树后优化"分成两条命令
# 用法：placement 之后执行；-no_clock_route 让时钟线先不布，省时间也少一轮 DRC
# ---- 建树 ----
clock_opt -only_cts -no_clock_route        ;# 只建树，不重建数据路径，不布时钟线
save_block -as cts_done                    ;# 回退点①

# ---- 树后优化（就是 OptCts）----
clock_opt -only_psyn -no_clock_route       ;# 只做 post-CTS 时序优化，不动树结构
save_block -as optcts_done                 ;# 回退点②

# ---- 想出报告 ----
report_clock_qor -type summary             ;# 树的五个指标：skew/insertion/DRV/power
report_qor                                 ;# setup/hold 的 WNS/TNS 汇总
```

| 动作 | Innovus | ICC2 |
|---|---|---|
| 只建树 | `ccopt_design -cts` | `clock_opt -only_cts` |
| 树后优化 | `optDesign -postCTS` | `clock_opt -only_psyn` |
| 一起做（CCD） | `ccopt_design` | `clock_opt` + 打开 CCD 选项 |
| 看树质量 | `report_clock_tree -summary` | `report_clock_qor -type summary` |
| 存盘 | `saveDesign x.enc` | `save_block -as x` |

`-only_psyn` 里的 psyn 是 physical synthesis（物理综合）的缩写，意思是"在物理信息已知的前提下做综合式优化"——换单元尺寸、插 buffer、重构逻辑，但不重建时钟树。

`-only_cts` 和 `-only_psyn` 这两个开关的存在，本身就说明 ICC2 默认把两件事合在一起做（`clock_opt` 不带开关就是全做）。拆开跑的好处只有一个，但很值钱：**出错时你知道是哪一半出的错**。合并跑省一小时，拆开跑省一天。

`report_clock_qor` 的输出字段和 Innovus 的 `report_clock_tree -summary` 一一对应：skew、insertion delay、DRV 分类计数、buffer 数、clock power。换工具不用换看报告的方法。

:::term CCD | Concurrent Clock and Data，时钟数据协同优化
传统流程是"先建树、再优化数据路径"，两步分开。CCD 让工具同时动时钟和数据，能一次兼顾 setup 和 hold。

代价：跑得慢、对约束质量敏感。前提是时钟树结构已经定下来，否则工具会在两件事之间反复横跳。
:::

## hold 修复：为什么必须现在修 {#hold}

hold 违例的物理含义：**数据跑得太快，把下一个时钟沿该采的值提前冲掉了**。

它有三个特点，决定了必须在 CTS 后、布线前修：

1. **跟频率无关。** 降频救不了 hold。hold 检查的公式里根本没有周期这一项，下面会写清。
2. **布线后会变差。** 数据路径的线延迟继续增加，时钟树的延迟已经固定，两者的差（也就是 hold 余量）会被吃掉。
3. **修法只有两种。** 给数据路径加延迟（插 buffer 或 delay cell），或者给捕获时钟加延迟（调 skew）。

```text
hold 检查（相邻两个触发器，同一个时钟沿）
  数据最短到达时间  >  捕获时钟到达时间 + hold 时间
                       ↑ 数据太早到 = 早于这个点 = 违例

修法 A：数据路径插 delay cell  → 让数据晚点到
修法 B：捕获时钟再晚一点      → 让要求的时间点后移
```

hold 违例在波形上的样子，复习一下第 17 课那张图：

:::fig wave-hold | hold 违例的波形：蓝线是"本来应该"的样子，红线是"实际发生"的样子，数据提前翻转冲掉了上一级要采的值。重点看违例发生在同一个时钟沿附近、与周期无关——这正是它必须在 OptCts 阶段、布线前修掉的原因。
:::

从这张图里要看出什么：hold 是"抢跑"问题，修法只有让数据晚到（修法 A）或让要求后移（修法 B）——和上面那两行一一对应。

**为什么"降频救不了 hold"，看公式就明白：**

`hold slack = (launch 时钟 + clk2q_min + 逻辑最短延迟) − (capture 时钟 + hold 时间)`

式子里只有时钟到达时间和延迟，**没有周期 T**。你把周期从 2ns 改成 4ns，这个式子的每一项都不变，hold slack 一丝不动。而 setup 的式子里有 T，所以降频只让 setup 变松。

:::pitfall 用降频来"修" hold
现象：hold 违例一堆，把周期从 2ns 改成 2.5ns，`report_timing -delay_type min` 还是那些负数。
原因：hold 与周期无关（看上面的公式）。
处理：要么插 delay cell，要么调 skew。降频只能当"确认诊断"的手段——如果降频后 setup 变好、hold 不变，正好证明你看到的是真 hold 违例，不是约束写错。
:::

修 hold 不是免费的，代价要提前知道：

| 修法 | 代价 | 副作用 |
|---|---|---|
| 插 delay cell | 面积 + 功耗，每条违例路径一个到几个 | 数据路径变长，可能把 setup 拖差 |
| 调捕获时钟（借 skew） | 零面积零功耗 | 该端点的下游 setup 少同样的时间 |
| 换更强驱动的单元 | 面积 + 功耗 | 数据更快，对 hold 是反效果（会更差） |

所以修 hold 之后**必须再查一次 setup**——这是 hold 修复最常见的翻车点：hold 全绿了，setup 冒出 30 条新的。

## 报告怎么读：三个数字决定下一步 {#report}

拿到 `report_clock_tree -summary`，别从头读到尾，只看三个数：**skew、insertion、DRV**。输出格式大致是这样（数值是示例，用来讲怎么读）：

```text
Clock      Skew(ns)   Insertion(ns)   DRVs   Buffers   Power(mW)
clk        0.048      0.612           0      184       12.4
```

| 数字 | 怎么判断 | 下一步 |
|---|---|---|
| skew 0.048，周期 2ns 的 2.4% | 合格 | 不用动 |
| insertion 0.612ns | 合格（< 1ns） | 接口紧的话可以再压 |
| DRVs 0 | 合格 | — |
| Buffers 184，叶子约 6400 | 比例 0.029，正常 | 不用管 |

再看一个不合格的：

```text
Clock      Skew(ns)   Insertion(ns)   DRVs   Buffers
clk        0.021      0.480           12     96
clk_div    0.290      1.340           0      412
```

判断顺序是固定的：

1. **DRV 12 是硬违例**，签核必挂 → 先修 transition / max_cap / max_fanout；
2. **`clk_div` skew 0.29（周期 2ns 的 14.5%）** → 先看是不是分频器后面负载不均，再看是不是某个触发器离得特别远（floorplan 问题）；
3. **`clk_div` insertion 1.34ns 偏大** → 根节点位置不对，或者树层级太深；
4. **`clk` 的 0.021 已经很好，别动它**——优化一个已经达标的时钟域，只会把它弄坏。

为什么 DRV 永远优先：它是**硬性工艺规则**，不是"预算够不够"的问题；skew 大只是吃掉时序余量，还能靠别的办法补。先修不可协商的，再修可协商的。

:::note 课程环境的一组数据
万门设计（ipa_top，12026 单元）在 ICC2 里跑 `clock_opt`，耗时约 9.5 分钟，插了 2636 个 buffer，最终 setup WNS +1.00ns、hold −0.07ns。

那个 −0.07ns 就是"没做第二轮 hold 优化"的典型残留：单 corner、单模式、时间预算紧，先保证 setup。真实项目里这一条会用 ECO 插 delay cell 修掉，不会带着负 hold 去布线。
:::

## 工作中怎么用：OptCts 在项目里的位置 {#in-work}

**谁做**：PR 工程师本人。CTS 和 OptCts 通常由同一个人连着做，因为调 skew 的决策依赖对树的直观了解。

**输入是什么**：placement 之后的数据库、SDC（含时钟定义与 uncertainty）、CTS 可用单元清单、NDR 规则。

**输出交给谁**：交给 Route（第 20 课）。同时给 STA 工程师一份时钟树汇总，因为签核用的时钟延迟和 skew 就是这一步定下的——后面布线只会让它变差一点，不会变好。

**评审看三个数**：skew 占周期比例、insertion delay 是否 < 1ns、DRV 是否为 0。三个都过才允许进 route，任一不过要说明理由并记录 waiver。

**做错会怎样**：这里借 skew 借过头，route 阶段会以 hold 违例的形式还回来；带着 −0.3ns 的 hold 进 route，布线后要花两三天做 ECO 补 delay cell，而且每补一个都可能把 setup 拖差。**OptCts 阶段多花两小时看报告，能省掉后面两天。**

:::lab 动手：从一份汇总报告里排出修复顺序
**任务**：给下面这份 `report_clock_qor` 的输出，排出前三步动作，并说明每一步的依据。

```text
Clock     Skew    Insertion   DRVs   Buffers
clk_core  0.155   1.820       0      521
clk_io    0.038   0.290       7      44
```

**步骤**：
1. 先算两个时钟的 skew 占周期比例（假设都是 2ns 周期）。
2. 判断哪个是硬违例、哪个是软问题。
3. 写出你的动作顺序，每一步注明"改哪个时钟、用什么命令"。
4. 在课程环境里跑 `report_clock_qor -type summary`，把你自己的数字填进同样的表，重复一遍判断。

**过关标准**：能说出"`clk_io` 的 7 个 DRV 先修（硬规则），`clk_core` 的 skew 7.75% 次之（软预算），`clk_core` 的 1.82ns insertion 最后（要先判断是不是根节点位置问题）"，并解释为什么不能反过来。
:::

:::quiz
CTS 和 OptCts 的分工是什么？|CTS 负责建树：连通、基本平衡、驱动够；OptCts 在已建好的树上压 skew 和 latency、修 DRV、用 useful skew 修 setup、插 delay cell 修 hold，不重建树。
时钟树的五个质量指标是哪五个？为什么要一起看？|skew、insertion delay、transition、clock power、DRV 违例数。它们互相拉扯：压 skew 要多插 buffer，buffer 多了 latency 和功耗就上去；树做浅 latency 短，但 transition 会变差。
useful skew 借 80ps 救 setup，代价具体落在哪？|捕获端时钟晚 80ps，这条路径的 hold 要求时间也后移 80ps，hold 余量少 80ps；如果这个触发器还是下游路径的起点，下游 setup 同样少 80ps。
useful skew 的三条纪律是什么？|只借给下游仍有余量的触发器；单次不超过周期的 10%（常用 30~80ps）；借完必须重跑 hold 检查并重出 skew 报告。
为什么降频救不了 hold？|hold slack 的公式里只有时钟到达时间、clk2q、最短逻辑延迟和 hold 时间，没有时钟周期这一项。改周期不影响任何一项。
报告里 DRV 和 skew 都超标，先修哪个？|先修 DRV。它是硬性工艺规则（max_transition/max_cap），签核一定报；skew 只是吃掉时序预算，属于可协商的软指标。
`clock_opt -only_cts` 和 `clock_opt -only_psyn` 有什么区别？|`-only_cts` 只建时钟树；`-only_psyn` 不重建树，只在已有树上做 post-CTS 的物理综合式优化（换尺寸、插 buffer、调 skew）。
为什么 OptCts 之后还要存盘再进 route？|因为 route 会改变线延迟，OptCts 的结果是 route 的输入基线；存盘保证 route 出问题时能退回"树已优化、线未布"的干净状态，不用从 CTS 重来。
:::

:::check
- 能说出 CTS 结束后残留的四类问题，以及为什么不能合成一步做完
- 能背出五个质量指标和大致合格范围，并解释它们为什么互相拉扯
- 能手算一次 useful skew：给定周期和各项延迟，算出借多少、setup 改善多少、hold 少多少
- 能背出三条纪律，尤其是"借完必须重查 hold"
- 能写出 Innovus 的 `ccopt_design -cts` → `optDesign -postCTS` → `-hold` 三段，以及每段的存盘点
- 能说出 ICC2 的 `clock_opt -only_cts` / `-only_psyn` 对应关系
- 能用公式解释"降频救不了 hold"
- 拿到汇总报告，能按"DRV → skew → insertion"的顺序排出动作
:::
