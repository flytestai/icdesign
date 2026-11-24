---
id: 02-03-pr-flow
no: 22
stage: 2
title: PR 全流程九步：从 init 到 chipfinish，以及一个项目怎么排期
en: The Place-and-Route Flow, Step by Step
hours: 3
minutes: 40
tags: [PR, 流程, floorplan, powerplan, cts, route, ECO, run]
summary: 把 init → floorplan → powerplan → place → cts → optcts → route → optroute → chipfinish 九个阶段逐个拆开，说清每步在干什么、产出什么、做完看哪个指标判断好坏；再讲清楚 run 是什么、PR → FINALPR → ECO → BTO/MTO 的项目时间线，以及 log 里 pre/post 命名的含义。
---

## 九步流程总表：先记住骨架 {#table}

:::goal 能按顺序背出 PR 九个阶段并说出每步的产出；能解释 run、ECO、BTO/MTO 是什么；看到 log 里的 PrePlace / PostCts 能判断它在流程哪个位置。
:::

下面这张表是整课的骨架，建议先扫一遍，再逐节看细节：

| # | 阶段 | 一句话在干什么 | 主要产出 | 做完先看什么 |
|---|---|---|---|---|
| 1 | init | 导入 netlist、lef、lib、sdc、MMMC | 一个"认得清设计"的数据库 | 有没有 error、单元数对不对 |
| 2 | floorplan | 定芯片面积，摆 mem/macro，加物理约束与物理单元 | die 尺寸、mem 位置、port 位置（def） | 利用率、通道够不够、mem 摆得顺不顺 |
| 3 | powerplan | 打供电网络 | 电源 mesh/strap、via 阵列 | IR drop、有没有断电的单元 |
| 4 | placement | 摆放所有 stdcell（并做一次 global route 试算） | 合法化的单元位置 | 拥塞（congestion）、时序初值 |
| 5 | cts | 时钟树综合，绕时钟线 | 时钟树、clock net | skew、insertion delay、时钟功耗 |
| 6 | optcts | 针对 cts 结果做优化 | 优化后的时序/面积 | setup/hold 违例数、DRV |
| 7 | route | 信号线正式绕线 | 完整布线（detail route） | DRC、绕通率、时序 |
| 8 | optroute | 针对 route 结果做优化（必要时 reroute） | 收敛后的布线与时序 | 违例是否清零、DRC 是否可签核 |
| 9 | chipfinish | 吐出所有交付文件 | GDSII、def、报告、数据库 | 文件齐不齐、版本对不对 |

:::note 别死记阶段名，记"顺序背后的因果"
先有地方（floorplan）→ 先有电（powerplan）→ 才能摆单元（place）→ 摆好了才能按时钟（cts）→ 时钟稳了才敢绕信号（route）→ 最后才是收尾（chipfinish）。**顺序错了物理上就不成立**：没打供电就绕信号，后面电源线和信号线抢资源，全得重来。
:::

:::fig pr-flow | PR 全流程与三次优化：布局优化（prects opt）、时钟树优化（postcts opt）、布线优化（postRoute opt）
:::

注意图里那三个"旁支"——**每走完一大步，都要回来优化一轮**：

| 优化 | 什么时候做 | 主要修什么 |
|---|---|---|
| **prects opt**（布局优化） | place 之后、cts 之前 | 用估算的时钟修 setup，顺便压面积、缓解拥塞 |
| **postcts opt**（时钟树优化） | cts 之后、route 之前 | 有了真实时钟树，setup/hold 都能真算，修得更准 |
| **postRoute opt**（布线优化） | route 之后 | 用真实 RC 修最后的 setup/hold + DRV/DRC |

所以 PR **不是"跑五步就完"，而是"跑一步、修一轮"的循环**。这也是为什么课表里 cts 给了 14 学时——时钟树出来之后那几轮优化，才是真正磨时序的地方（第 6 讲还会细讲）。

## 1. init：把数据喂进去 {#init}

init（初始化）要做的事只有一件：**让工具认识这个设计**。需要导入的东西就是下一课要细讲的那几样：

- `netlist`：门级网表（`.v.gz`），告诉工具有哪些单元、怎么连；
- `lef`：tech lef（工艺规则）+ cell lef（单元形状与引脚）；
- `lib`：单元的时序/功耗库，工具算延迟要用；
- `sdc`：时序约束，工具优化的目标；
- `MMMC`：多模式多端角环境（`viewDefinition.tcl`）。

init 做完的判断标准很朴素：**没有 error，单元数和网表对得上，工具能报出设计的面积估算**。这时候如果报 `Cannot find library` 或 `Cannot find cell`，八成是 lef/lib 路径或名字对不上，别急着往下走。

## 2. floorplan：定面积、摆 mem、加物理约束 {#floorplan}

floorplan（布局规划）是整个 PR 里**最像"设计"的一步**，因为它决定了后面所有阶段的天花板。

要做四件事：

1. **定芯片面积**（die size）：面积给大了浪费成本，给小了后面绕不开。核心指标是 **utilization（利用率）**＝单元总面积 ÷ 可用面积，通常从 60%~70% 起步，太高的留给布线的地方就不够了。
2. **摆 mem/macro**：上一课讲过，这些第三方 IP 必须人工确定位置与朝向，还要留 halo、加 routing blockage。
3. **定物理约束**：哪些区域禁止放单元、哪些层禁止走线、port（引脚）放在哪条边上。
4. **加物理单元**：tap cell、endcap 这些"没有逻辑但必须存在"的单元，floorplan 阶段就按规则铺好。

产出里最关键的是 **def**：它记录了 die 大小、每个 mem 的坐标与朝向、每个 port 的位置。**top 层就是靠这个 def 把"你的块多大、从哪进哪出"发给 block owner 的。**

:::term die / core | 芯片边界 / 可用摆放区
**die** 是芯片的物理边界（整块方形区域）；**core** 是 die 里真正用来摆单元的区域，四周留出的一圈是给电源环和 IO 的位置。**core 里还可能有中空区（hole），那是禁止摆任何单元的地方**（比如给别的模块或特殊结构预留）。
:::

:::tip 面积不是你随便定的：先看 top 给的 box
独立模块你自己定 die 尺寸；但在 SOC 项目里，**top 会给你一个 box（尺寸约束）**——你要做的是把 box 换算成 die/core 的具体数值（还要扣掉边界留白），而不是自己拍一个数。

**拿到 box 先算清楚三件事**：die 多宽多高、core 面积多少、据此估出的最大可用利用率是多少。算错这三样，后面全是返工。
:::

:::term partial density | 局部密度限制
不是全芯片一个密度目标，而是**对某个区域单独设上限**（如 30%、60%）。常用在 macro 周围：因为 macro 引脚多、走线密集，周围 cell 摆太满就必然拥塞。
:::

:::pitfall 面积一开始就给太小
**现象**：floorplan 时利用率定到 85%，place 阶段拥塞爆红，route 绕不通，只能回头重做 floorplan，前面几天全白干。
**原因**：stdcell 之间要留布线通道，mem 周围要留 halo，引脚密集区还要额外空间。利用率只是"单元占地"，不代表"线能走通"。
**怎么避免**：先用 60%~65% 起步跑一版 place，看拥塞图（congestion map）再决定要不要收紧；有大量 mem 的设计，利用率必须留更多余量，并对 macro 周围单独设 **partial density** 与 halo。
:::

:::term congestion | 拥塞
某个区域要走的线**超过了该区域能提供的布线资源**。表现是 place 之后拥塞图上出现大片红色，route 阶段绕不通或绕得特别长。

根因通常是三件事之一：密度太高、macro 周围没留通道、port 位置和内部单元位置"顶牛"。**拥塞是 floorplan 阶段的锅，不是 route 阶段能修的。**
:::

## 3. powerplan：先把电送到每个单元 {#powerplan}

powerplan（供电规划）主要工作是**打供电的绕线**：把电源/地从 pad 引进来，做成网格（mesh）或条带（strap），一层层用 via 往下打到每个 stdcell 的电源轨上。

它排在 place 前面的原因很实际：**电源线又宽又占层**，先把它们占好位置，后面的信号线才知道自己还剩多少资源。如果反过来先绕信号，电源线就没地方走了。

判断好坏看两个东西：**IR drop**（电压掉得太多，单元会变慢甚至不工作）和**电迁移**（电流密度太大，线会"烧断"）。这两项是阶段七功耗分析课的正题，这里先知道名字。

## 4. placement：自动摆 stdcell {#placement}

placement 把网表里成千上万个 stdcell 摆到 row 上，目标是**线短、拥塞低、时序好**。这一步工具会自动做，但同时会做一次 **global route（全局布线）试算**——不是真的绕线，而是估算"这些连接大概要走哪、会不会堵"。

:::term global route | 全局布线（试算）
不落到具体 track 上的粗粒度布线估算：把芯片划成网格，估每条连接大概经过哪些格子，用来提前发现拥塞（congestion）。真正的绕线在 route 阶段（detail route）才做。
:::

所以 place 结束后你要看的是**拥塞图**和**时序初值**，而不是"单元摆得整不整齐"。单元摆得再漂亮，绕不通就是废的。

## 5. cts：时钟树综合 {#cts}

cts（Clock Tree Synthesis，时钟树综合）专门解决一件事：**让时钟同时到达所有触发器**。

理想情况下，时钟到每个触发器的延迟应该完全一样；现实中不会，这个偏差叫 **skew（偏斜）**：

:::term skew | 偏斜
同一个时钟到达不同触发器的时间差。skew 越大，留给数据通路的余量就越少，越容易 setup/hold 违例。cts 的核心目标就是把 skew 压小。
:::

:::term insertion delay | 插入延迟
从时钟源（clock source）到某个触发器 clock 端的实际延迟。它决定了时钟要"提前"多久发出，也直接影响功耗（树越长越费电）。
:::

cts 阶段的产物是一棵真实的时钟树（一堆 buffer/inverter 加上连线）。它只绕**时钟线**，不碰信号线——这也是为什么 cts 能单独成为一个 14 学时的大章节：时钟树的结构、buffer 数量、层级、skew/latency 的取舍，全是经验活。

## 6. optcts：给时钟树擦屁股 {#optcts}

cts 做完，时序通常会更差（多了 buffer、多了延迟）。optcts 就是**针对 cts 的结果做优化**：修 setup/hold 违例、修 DRV（max transition / max capacitance / max fanout 这类电气规则违例），同时尽量不把时钟树搞乱。

## 7. route：信号线正式绕线 {#route}

route 阶段把剩下所有信号连接真正绕出来（detail route），落到具体的金属层和 track 上。这是计算量最大的一步，也是 DRC 的主要来源。

判断标准就三条：**绕通率**、**DRC 数量**、**时序是否还活着**。

绕线的两类硬错误，必须分清：

| 错误 | 英文 | 含义 |
|---|---|---|
| **断路** | **open** | 该连的没连上——线断了、via 漏打、pin 没接进来 |
| **短路** | **short** | 不该连的连上了——两条线碰到一起、线压到了别的网络上 |

**open 会让信号根本传不过去（功能直接错），short 会让两个网络短接（逻辑错乱 + 可能烧毁）**。这两类必须在 route 阶段清零，而绕不通的通常要回到 floorplan/placement 找原因（通道不够、mem 摆得太挤），不是在 route 里硬修。

## 8. optroute：收敛与 reroute {#optroute}

optroute 针对 route 的结果做优化：修时序、修 DRC、减少绕线长度。如果优化过程中把线拆了重绕，就叫 **reroute**。

:::note 这一步的另一个名字：OBT
有的公司/文档把"布线之后的这轮优化"叫 **OBT**（**O**ptimization **B**efore **T**apeout，流片前优化），有的叫 **postRoute opt**，说的都是同一件事：**在真实 RC 下把最后的时序和 DRC 修干净。**

听到 OBT 别以为是新阶段——它就是我们这张表里的第 8 步。
:::

到这一步，流程进入"反复迭代"模式：修一处时序可能带来新的 DRC，修 DRC 又可能破坏时序。真实的收敛过程就是在这种拉扯里一点点逼到"违例清零、DRC 可签核"。

:::term 收敛 / signoff | 收敛、签核
"收敛"指各项指标（时序、DRC、功耗、面积）都达到目标并且不再反弹；"签核"是最后用独立工具（PrimeTime、PV 工具）复核一遍并出正式结论。**PR 工具自己说没问题不算数，要签核工具也认。**
:::

## 9. chipfinish：把所有文件吐出来 {#chipfinish}

chipfinish 是收尾：导出 GDSII、def、各种报告（时序、面积、DRC、功耗），整理交付目录。这一步技术含量不高但最容易出事——**文件版本错、漏导一层、报告和数据库对不上**，都会让下游白跑一轮。

:::fig pr-chipfinish-netlist | chipfinish 阶段吐出的一版网表：ORCA_TOP_09_icc2_chipfinish.v.gz
:::

注意这个文件名，它把三件事写在了名字里，这也是工程上的通行做法：

| 片段 | 含义 |
|---|---|
| `ORCA_TOP` | 设计名（这颗芯片/这个 top 叫什么） |
| `09` | 版本号（第 9 版） |
| `icc2` | 用哪个工具跑的（ICC2，对应阶段四；Innovus 会写 innovus） |
| `chipfinish` | 跑到哪个阶段（收尾阶段导出的） |
| `.v.gz` | 压缩的 Verilog 网表 |

**看到这种命名就放心一大半**：谁的、第几版、哪个工具、哪个阶段，一目了然。反过来，如果你的目录里全是 `top.v`、`top_new.v`、`top_final.v`、`top_final2.v`——那就等着出事故。

## run 是什么：一句行话 {#run}

面试和日常沟通里高频出现的词：

:::term run | 一轮完整跑
针对某一版设计（某一版网表、某一组约束、某一套参数）**从头到尾跑一遍流程**，看新数据是不是变好了。改了东西就要重新 run 一次，所以"今天跑了三个 run"是很正常的说法。
:::

由此衍生出这些说法，听到别懵：

- **"跑一版 place 看看"**：只跑到 placement 就停下看结果，不跑完整流程；
- **"这个 run 挂了"**：这一轮跑到某步报错或结果崩了；
- **"对比一下两个 run"**：把两轮的时序/面积/DRC 报告拉出来比。

:::tip 一个 run 可能是几天
真实项目里，**一个五六百万门的大模块从 place 跑到 cts 出结果要 3~4 天**。所以 run 不是"敲个命令等十分钟"，而是提交到**集群 Queue** 排队跑。

于是工作方式变成：**手动做完 floorplan → 丢进 Queue → 等 → 看报告 → 改参数 → 再丢一版**。等待期不是空转，而是分析上一批结果、加新约束、再提交（这套流程在阶段三的「项目环境」那一课细讲）。
:::

## 一个真实项目的时间线 {#project}

:::term ECO | 工程变更单（改版）
Engineering Change Order。芯片流片前（甚至流片后）发现要改的地方，用最小的改动去打补丁：只动几个单元、几条线，而不是重跑全流程。
:::

完整链路长这样：

```
PR → FINALPR → ECO（PT / PV / PA）→ BTO → MTO
```

逐个解释：

| 环节 | 含义 | 大致在干什么 |
|---|---|---|
| PR | 布局布线主流程 | 第 1~4 版网表，一轮轮把设计做收敛 |
| FINALPR | 最终版 PR | 定版，所有指标达标，准备交付 |
| ECO | 工程变更 | 只改必要的地方：PT 修时序、PV 修物理规则、PA 修功耗 |
| BTO | Tape Out 前准备 | 数据整合、检查、生成送厂文件（GDSII 等） |
| MTO | Mask Tape Out | 掩膜版投产，之后就改不动了（改一次几百万起） |

时间尺度（一个典型项目）：**总周期约 9 个月**，其中 PR 占 **7 个月**（要吃 4 版网表：第一版到第四版），ECO 占 **2 个月**。

### 从 PR 到 Final PR：怎么挑出"最好的一版" {#finalpr}

绕线跑完不等于结束。你会**反复 run 出好几版结果**，然后从中挑一版定为 **Final PR**。挑选看的三个指标：

| 指标 | 看什么 | 为什么重要 |
|---|---|---|
| **Congestion**（拥塞） | 拥塞图/溢出量 | 拥塞大 → route 绕不通或绕得极长 → 时序崩 |
| **Density**（密度） | 利用率与局部密度 | 太挤没布线资源，太松浪费面积成本 |
| **Timing**（时序） | WNS/TNS、违例条数 | 最终决定能不能跑到目标频率 |

目标只有一个：**挑一版"没有明显短板"的结果**做 Final，然后进入 ECO。

### ECO 两个月：布局被锁死 {#eco-phase}

:::tip ECO 阶段的铁律：不能大改布局
Final PR 一定，**物理布局就基本锁死了**——memory 摆在左下角，就不能再挪到右上角。

所以 ECO 阶段干的不是"重新布局"，而是在**固定版图**上做：
- **PT** 修时序（只动关键路径上的单元/线）；
- **PV** 修物理验证问题（DRC/LVS/天线）；
- **PA** 修功耗（IR drop、电迁移）；
- 顺带跑 IR drop 分析确认供电没问题。

**两个月要跑完这一整套并修干净**——这就是为什么 ECO 阶段是全项目最忙的时候。
:::

### Tapeout：交出去就改不动了 {#tapeout}

所有检查修完、指标达标，就进入 **Tapeout（TO）**：

1. 数据整合 → 生成送厂文件（**GDSII** 为主）；
2. 交给 **Foundry** 做掩膜、流片；
3. 之后想改？**掩膜重做一次几百万起**，所以 TO 之前的每一轮检查都不能省。

:::note 为什么 PR 要吃四版网表？
因为前端也在改。第一版网表通常是"功能刚通"，面积和时序都很差；后面每一版修 bug、加功能、做低功耗，网表一直在变。**你这一版辛苦收敛的结果，下一版网表来了可能全崩**——所以流程必须脚本化、可复现，这也是为什么本站先讲 Linux 和 Tcl。
:::

## pre / post：log 和报告名里的位置标记 {#prepost}

看 log、看报告目录时，你会反复看到这两组词：

- `pre` = 在……之前；`post` = 在……之后；
- `PrePlace` / `PostPlace`：placement 之前 / 之后；
- `PreCts` / `PostCts`：cts 之前 / 之后；
- `PreRoute` / `PostRoute`：route 之前 / 之后。

所以 `postRoute_timing.rpt` 就是"绕完线之后的时序报告"，`preCts_area.rpt` 是"cts 之前的面积报告"。搞不清这个，就会拿 cts 之前的报告去解释 cts 之后的问题——这是新人最常犯的错之一。

## EDA 公司与其工具：一张对照表 {#eda}

| 公司 | 布局布线 | 综合 | 时序 | 寄生提取 | 功耗 |
|---|---|---|---|---|---|
| Cadence | **Encounter**（老）、**Innovus**（主流） | Genus | Tempus | QRC | Voltus |
| Synopsys | **ICC**（老）、**ICC2**（主流）、Fusion Compiler | Design Compiler（DC） | **PrimeTime** | **StarRC** | RedHawk（Ansyst 系） |

记两条就够用：

1. **90nm 以上工艺**常见 Encounter / ICC；**先进工艺**是 Innovus / ICC2 的天下——工艺越先进，老架构越跑不动（最直观的差别是运行时间）。
2. 本站阶段三用 **Innovus + 40nm**，阶段四用 **ICC2 + 32nm**：同一套方法论，换工具再走一遍，这是最快建立"工具只是壳、方法是内核"认知的方式。

:::term AE | 应用工程师（驻场支持）
Application Engineer，工具厂商派到客户现场的技术支持。**工具报了你根本看不懂的内部错误、或者怀疑是工具 bug 时，找 AE。**

大公司常有 AE 驻场（直接找人问）；小公司多靠线上提单/邮件。新人容易犯的错是：卡在工具问题上自己磨三天，其实问一句 AE 十分钟就解决了。
:::

另外，文档里提到的**内部库**要单独说一句：很多公司会在标准库之外再维护一套"内部库"（公司自己封装的单元/特殊 macro），**PR 读的库不止工艺厂那一套**。看到 lib 列表里出现你不认识的库名，先问清楚它是谁的、干什么用的，别默认删掉。

:::lab 把流程表和项目时间线对上
1. 不看资料，默写九个阶段的顺序，并给每个阶段写一个"产出物"。
2. 把 `powerplan / cts / route` 三步和上一课讲的"三种线"连线。
3. 算一道算术题：一个项目 9 个月，PR 占 7 个月、ECO 占 2 个月，PR 里 floorplan 通常占 25% 左右——floorplan 大概几周？如果 floorplan 做错重做一次，会吃掉多少余量？

验收标准：九步顺序不能错；能解释"为什么 powerplan 必须在 placement 之前"；能说出 pre/post 报告名的含义。
:::

:::quiz
PR 九个阶段按顺序是什么？| init → floorplan → powerplan → placement → cts → optcts → route → optroute → chipfinish。
为什么 powerplan 要排在 placement 前面？| 电源线又宽又占层，先把它们的位置占好，后面的信号线才知道还剩多少布线资源；反过来先绕信号，电源线就没地方走了。
floorplan 阶段最重要的产出是什么？为什么它对 block 级设计特别关键？| def 文件（die 大小、mem 坐标、port 位置）。block 的边界由 top 通过 def 下发，port 位置错了块内接口逻辑要重做。
global route 和 detail route 有什么区别？| global route 是网格级粗估，用来提前发现拥塞；detail route 才落到具体金属层和 track，是真正的绕线。
"run" 是什么？举两个日常说法。| 针对某一版设计从头跑一遍流程看数据是否变好。例如"跑一版 place 看看""这个 run 挂了"。
完整项目链路 PR → FINALPR → ECO → BTO → MTO 各是什么？| PR 是主流程（约 7 个月、4 版网表）；FINALPR 定版；ECO 做最小改动修补（PT/PV/PA，约 2 个月）；BTO 是流片前数据准备；MTO 是掩膜投产。
postRoute_timing.rpt 是什么报告？| route 结束之后的时序报告。pre 表示之前、post 表示之后。
place / cts / route 之后的三个优化分别叫什么？各修什么？| prects opt（布局优化，估算时钟下修 setup 并压面积/缓解拥塞）、postcts opt（时钟树优化，真实时钟下修 setup/hold）、postRoute opt（布线优化，真实 RC 下修最后违例与 DRC）。
从多版结果里挑 Final PR，看哪三个指标？| Congestion（拥塞）、Density（密度）、Timing（时序），目标是挑一版没有明显短板的。
ECO 阶段为什么"不能大改布局"？那它在干什么？| Final PR 一定，物理版图就锁死（memory 不能挪）；ECO 在固定版图上做最小改动：PT 修时序、PV 修物理验证、PA 修功耗，并跑 IR drop 检查。
die 和 core 有什么区别？core 里的中空区是什么？| die 是芯片物理边界，core 是其中真正摆单元的区域（四周留给电源环/IO）；core 里的中空区禁止摆放任何单元。
partial density 是什么？什么时候用？| 局部密度上限（如 30%/60%），常用在 macro 周围，因为那里引脚多走线密集，cell 摆太满必然拥塞。
:::

:::check
- 能不看书按顺序说出九个阶段，并给每个阶段配一个产出物
- 能解释 skew 与 insertion delay 的含义
- 能说清 run、ECO、BTO、MTO 分别指什么
- 看到 PrePlace / PostCts / PostRoute 能判断报告属于流程哪个位置
- 能说出 Cadence 与 Synopsys 各自的布局布线、时序、寄生提取工具名
:::
