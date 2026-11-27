---
id: 03-07-place
no: 37
stage: 3
title: Place：布局三阶段、OCV 谱系与时序判据
en: Placement
hours: 4
tags: [Innovus, 40nm, 项目实操, Place]
summary: 布局的四个目标；global/scan reorder/detail 三阶段各做什么；OCV→AOCV→SOCV 的演进与 CPPR 为什么能救回来；path group 怎么用；Setup/Hold 公式怎么推；四类 DRV；面积计算脚本与成败判据。附原始资料对照。
---

## 布局要同时满足四个目标 {#goals}

Place 是把标准单元放到合法位置上的过程。听起来简单——位置而已。但要同时满足四个互相冲突的目标：

| 目标 | 含义 | 冲突对象 |
|---|---|---|
| **合法** | 在行上、不重叠、朝向正确、不违反 floorplan 约束 | 想挤在一起省面积 |
| **线短** | 相关单元靠近，减少线长和延迟 | 挤在一起反而绕线 |
| **密度合理** | 局部不过密，给布线留资源 | 面积越小成本越低 |
| **时序好** | 关键路径的单元靠近 | 全局最优不等于时序最优 |

这四个目标不可能同时最优，所以 Place 的本质是**找平衡点**。工具做加权优化，你要判断「这次结果是不是可接受」。

:::term Place | 布局
把网表中的标准单元分配到版图上的合法位置，在满足合法性、密度、时序、线长等多重约束下寻求最优解。
:::

## 布局目标与三阶段流程 {#source-01}

原文把目标和流程放在一起讲。

:::source
"五、Place"
"1）主要的目标"
"合理规范摆放标准单元："
"stdcell的方向正确"
"stdcell不能出现overlap(单元重叠的情况)"
"stdcell必须在row上，基于site进行摆放"
"没有违反fp的constrain(布局约束 region partial 等)"
"2）place的流程"
"2.1 global place"
"全局性摆放单元，确定大致的位置,比较粗糙的走线，主要目的为了评估congestion是否有问题，以及density是否合理"
"2.2 Scan Reorder 扫描链重组"
"扫描链Scan Chain  DFT(design for test)部门设计专门网表"
"一种测试的手段，验证芯片功能是否满足要求"
"认识cell的常见pin"
"D pin"
"Q pin"
"SI pin  scan input"
"SO pin scan output"
"SE pin scan exable"
"CK pin"
:::

### 四个合法性要求，缺一不可

这是「合法布局」的定义，逐条说清为什么：

**方向正确**：标准单元朝向有 R0/MX/MY/R180 几种。方向错了不会立刻报错，但**电源轨接反**——VDD 接到 VSS 的轨上——会导致整行短路。

**不能重叠**：两个单元占同一块面积，物理上做不出来。工具通常自动避免，但 ECO 手改坐标时容易造出来。

**必须在 row 上、基于 site**：这就是 Floorplan 那课讲的 base DRC 来源——不在 row 上，底层 color 映射错乱。

**不违反 floorplan 约束**：region/fence/blockage 必须遵守。注意前面提到的两个开关，不开的话工具可能「不完全遵守」。

:::pitfall 四个合法性要分别验
工具报「placement legal」通常只覆盖重叠和行对齐。方向错误和约束越界要自己查，`checkPlace` 检查整体布局（含 overlap 和 VT 不匹配）。
:::

### 三阶段：global → scan reorder → detail

**① Global Placement（全局布局）**：原文说「确定大致的位置，比较粗糙的走线，主要目的为了评估 congestion 和 density 是否合理」。

关键理解：这一步**不做精确定位**，做的是「资源分配」——把单元分到各区域，让密度和布线需求大致均衡。产物是一个粗略布局，单元可能重叠、不在格点上，这是正常的。

**为什么这一步就能评估拥塞**？因为全局布局同时会做 trial route，估算每个区域的轨道需求，所以跑完就能看 congestion map。

**② Scan Reorder（扫描链重组）**：原文解释扫描链是 DFT 部门设计的专门网表，一种测试手段。

**什么是扫描链**？把成百上千个触发器串成移位寄存器链，测试时从外部把测试向量移进去、结果移出来，从而检查每个触发器是否正常。

**为什么布局后要重组**？因为链的连接顺序在综合时是**逻辑上**定的，没考虑物理位置。布局后链上相邻两个触发器可能一个在左上角一个在右下角，连线长得离谱。Scan Reorder 就是在允许范围内重排，让物理相邻的在链上也相邻。

原文列的引脚：**D 数据输入、Q 数据输出、SI 扫描输入、SO 扫描输出、SE 扫描使能、CK 时钟**。一个触发器扫描模式下数据从 SI 进、SO 出，所以扫描链是「D→Q→SI→SO」串起来的。

:::pitfall scan reorder 不是随便重排
链段内顺序可调，链段之间不能乱；有些触发器被标记为不可重排（如跨时钟域边界）；重排后要同步更新扫描链描述文件，否则测试向量对不上。

所以原文说链的定义权在 DFT，布局只能在其允许范围内调整。
:::

**③ Detail Placement（详细布局）**：把全局结果**合法化并细调**——消除重叠、对齐 site 和 row、在合法位置附近微调优化线长时序。

:::fig innovus-doc-31.png | 原文图 31 · 布局目标与摆放流程
:::

:::note 这张图该看什么
布局阶段的操作界面与流程入口。注意版图区此时单元还是粗略分布的状态，尚未完全合法化。

这一步的产物不是交付件，而是「可供下一步计算的粗略解」。不要把全局布局的中间状态当成最终布局来验收。
:::

:::source
"DFF = D Flip-Flop，D 触发器（后端最核心时序单元，也常叫寄存器 reg）"
"MUX选择器  "
"2.3 detail place"
"globalroute 全局布线  "
"MultuiBit  Banking   "
"将多个完全相同的cell进行合并，"
:::

:::note 这张图该看什么
布局相关的工具入口或结果视图。原文在这里引出了 detail place、globalroute 和 MultiBit Banking 三个概念。
:::

原文还提了两个概念：**globalroute（全局布线）** 和 **MultiBit Banking（多比特合并）**。

**Multi-Bit Banking**：把多个单比特触发器合并成一个多比特触发器（4 个 DFF 合成 1 个 4-bit DFF）。三个好处：省面积（共享时钟和扫描逻辑）、省功耗（时钟负载减少）、改善时序（共享时钟路径更短）。

**代价**：合并后的触发器必须放在一起，丧失独立摆放灵活性。原本分散的几个被强行合并，输入输出连线可能变长。

:::fig innovus-doc-32.png | 原文图 32 · 布局目标与摆放流程
:::

**runtime 与资源**：原文说「inst 数量越多 runtime 越长，也看服务器配置，256G 内存，核心 16」。

经验上：10 万实例几十分钟，100 万实例几小时，千万级要分块做。**内存是更硬的瓶颈**——实例数超过内存装得下的量，工具开始 swap，速度骤降几十倍。所以原文特别提内存配置。

:::source
"inst的数量越多，runtime就越长"
"runtime也看服务器的配置，256G内存，核心16 "
:::

## 分析模式：OCV 谱系与 CPPR {#source-02}

这一段是整门课理论密度最高的部分。原文把 OCV → AOCV → SOCV → CPPR 的演进全列出来了，但没解释「为什么」。

### 问题的起点：每个单元的延迟都不一样

理想情况下同批单元在同工艺角下延迟相同。现实是：**工艺偏差**（光刻、掺杂、氧化层厚度的微小差异让每个晶体管阈值电压不同）、**电压偏差**（芯片上不同位置供电电压有差异）、**温度偏差**（不同位置温度不同，迁移率不同）。三者合称 **PVT**。

所以**同一批单元实际延迟有分布**，不是一个确定值。

### OCV：用一个统一系数兜住所有偏差

:::source
"关于analysis mode"
"onChipVariation  简称OCV 偏上芯片误差"
"不同区域的单元的PVT环境不一样"
"OCV会引入derate（一个系数）的设置"
"OCV的弊端：设置统一的dreate,会导致，path越长，时序越悲观"
"为了解决OCV，设置CPPR（共同路径悲观去除）"
"AOCV 自动的OCV"
"更加智能，根据cell的级数，电路结构(距离) 设置不同derate"
"和电路级数成反比，级数越多，derate就越小"
"和距离distance 成正比, 距离越远，dreate越大"
"SOCV/POCV   "
"相比较AOCV更乐观"
"引入正态分布的思想，计算不同cell的延迟落在不同区间的概率，设置derate，尽量覆盖大部分场景"
"CPPR： 公共路径悲观去除"
"修复时序方法--设置group组"
"create path groups (reg2reg, in2reg, reg2out, in2out  reg2mem  mem2mem  mem2reg  reg2cg  )"
"group_path -name reg2reg -from [all_registers] -to [all_registers]"
"group_path -name in2reg -from [all_inputs] -to [all_registers]"
"group_path -name reg2out -from [all_registers] -to [all_outputs]"
"group_path -name in2out -from [all_inputs] -to [all_outputs]"
"setPathGroupOptions reg2reg -effortLevel high"
"setPathGroupOptions in2reg -effortLevel low"
"setPathGroupOptions reg2out -effortLevel low"
"setPathGroupOptions in2out -effortLevel low"
"group_path -name CLKM -from   [get_ports UFF0/CK ]  -to  [get_ports UFF1/D]"
"setPathGroupOptions CLKM -effortLevel high"
"set_interactive_constraint_modes [all_constraint_modes -active]    开启约束的修改"
"set_max_transition -clock_path 200 [all_clocks ] -override"
"set_max_transition -data_path 400 [all_clocks ] -override"
"set_interactive_constraint_modes {}   结束约束的修改"
:::

**做法**：给所有单元延迟乘一个系数。derate = 1.05 表示「实际延迟可能是标称值的 1.05 倍」。算 setup（要保守）用 late derate（延迟取大）；算 hold 用 early derate（取小）。

**OCV 的弊端**，原文一句话点中要害：**设置统一的 derate 会导致 path 越长时序越悲观**。

**为什么**？derate 是**逐级累乘**的。路径有 20 级单元，每级乘 1.05，总延迟变成 1.05²⁰ ≈ 2.65 倍——显然不合理，因为实际偏差是随机的、会互相抵消一部分。路径越长累积悲观量越大，这就是 OCV 的根本缺陷。

### CPPR：把「共同路径」的悲观量去掉

原文：**为了解决 OCV，设置 CPPR（共同路径悲观去除）**。CPPR = Clock Path Pessimism Removal。

**要解决的问题**：时序路径分两段——发射时钟路径和捕获时钟路径。这两条**从时钟源到分叉点之前是同一段物理路径**：

```
        时钟源
          │
      ┌───┴───┐        ← 这一段是「共同路径」
      │       │
   发射侧   捕获侧
      │       │
     FF1     FF2
```

用 OCV 算时这段共同路径被算了两遍：发射侧用 late derate（取大），捕获侧用 early derate（取小）。**但物理上它是同一段线，不可能同时既慢又快！** 这个差值就是纯粹的悲观量，CPPR 把它加回去。

**CPPR 能救回多少**？通常几十到几百 ps，取决于共同路径长度。对接近违例的路径，CPPR 经常就是「过与不过」的分界线。

:::note 为什么 CPPR 是「必须」而不是「可选」
不开 CPPR 等于所有路径被多算悲观量，会逼工具过度优化——插一堆 buffer、加宽线、挪单元，面积和功耗白涨，实际时序并没问题。

反过来，开了 CPPR 之后还违例，那违例是「真的」，必须修。
:::

### AOCV：按级数和距离给不同 derate

原文：**AOCV 自动的 OCV，更智能，根据 cell 级数、电路结构（距离）设置不同 derate。和级数成反比，级数越多 derate 越小；和距离成正比，距离越远 derate 越大。**

**为什么级数越多 derate 越小**？随机偏差会**统计平均**。一级的偏差是随机的，20 级串联后正负部分互相抵消，总偏差的相对量变小——这就是中心极限定理的直观体现。

**为什么距离越远 derate 越大**？距离远意味着两个单元位置差得远，PVT 环境差异大（工艺、电压、温度都随位置变化）。距离近的单元环境相似，偏差相关性高。

**数据从哪来**？foundry 提供的 AOCV 表（按级数和距离查表），需要额外库文件支持。

### SOCV / POCV：用概率分布代替固定系数

原文：**SOCV/POCV 比 AOCV 更乐观，引入正态分布思想，计算不同 cell 延迟落在不同区间的概率**。

**核心变化**：从「延迟是确定值 × 系数」改成「延迟是一个**分布**（均值 + 标准差）」。时序计算变成统计计算——每条路径的延迟是多个随机变量之和，多个正态分布相加仍是正态分布（均值相加、方差相加），最终算出违例概率。

**为什么更乐观**？统计方法能正确处理偏差抵消——长路径的偏差不简单累加，而按方差的平方根增长（√n 而不是 n），比 AOCV 的经验公式更精确。

**代价**：计算量大得多，需要 foundry 提供每颗单元的 σ 数据。

### 四种模式对比

| 模式 | 数据来源 | 精度 | 计算量 | 何时用 |
|---|---|---|---|---|
| **OCV** | 一个全局 derate | 最悲观 | 最小 | 早期评估、快速迭代 |
| **OCV + CPPR** | 同上 + 共同路径 | 明显改善 | 小 | 多数项目的基线 |
| **AOCV** | foundry 的 AOCV 表 | 较好 | 中 | 主流项目 |
| **SOCV/POCV** | foundry 的 σ 数据 | 最好 | 大 | 先进工艺、签核 |

:::tip 判断一份时序报告可不可信，先问用的哪种模式
同一设计，OCV 和 SOCV 算出的 WNS 可能差几百 ps。

所以看到「WNS = -0.15 ns」，必须同时知道：用的哪种 OCV 模式、有没有开 CPPR、derate 设多少。**缺了这三项，这个数字没有意义**——这也是跨项目比较时序数字没意义的原因。
:::

### Path Group：把路径分组分别用力

原文给了完整的 path group 命令集，这是实操性最强的部分。

| 组名 | 起点 | 终点 | 典型特征 |
|---|---|---|---|
| **reg2reg** | 寄存器 | 寄存器 | 数量最多，优化重点 |
| **in2reg** | 输入端口 | 寄存器 | 受外部延迟约束影响 |
| **reg2out** | 寄存器 | 输出端口 | 同上 |
| **in2out** | 输入端口 | 输出端口 | 纯组合，通常很少 |
| **reg2mem** | 寄存器 | 存储器 | 到宏的路径 |
| **mem2reg** | 存储器 | 寄存器 | 从宏出来 |
| **mem2mem** | 存储器 | 存储器 | 宏到宏 |
| **reg2cg** | 寄存器 | 时钟门控 | 到 ICG 的使能路径 |

**为什么分组**？不同组优化难度和重要性不同：reg2reg 是主力要投入最多资源；in2out 通常很少且容易过，不值得花力气；reg2cg 影响时钟门控时序，错了会功能错误。

**实用价值**：可以给不同组设不同优化力度（`-effortLevel high/low`），把计算资源花在重要的组上。命令：

```tcl
group_path -name reg2reg -from [all_registers] -to [all_registers]
group_path -name in2reg  -from [all_inputs]    -to [all_registers]
group_path -name reg2out -from [all_registers] -to [all_outputs]
group_path -name in2out  -from [all_inputs]    -to [all_outputs]

setPathGroupOptions reg2reg -effortLevel high
setPathGroupOptions in2reg  -effortLevel low
setPathGroupOptions reg2out -effortLevel low
setPathGroupOptions in2out  -effortLevel low
```

**注意 `-effortLevel`**：优化力度。high 表示花更多时间，low 表示「能过就行」。默认策略是主要组 high、边角组 low，避免计算资源浪费。

原文还给了一个自定义组的例子：

```tcl
group_path -name CLKM -from [get_ports UFF0/CK] -to [get_ports UFF1/D]
setPathGroupOptions CLKM -effortLevel high
```

把某一条**具体路径**单独成组给最高优先级。用于特别关键的路径（如跨时钟域关键接口）。

### 修改约束的正确姿势

原文这两行很多人不知道为什么要写：

```tcl
set_interactive_constraint_modes [all_constraint_modes -active]   ;# 开启约束修改
set_max_transition -clock_path 200 [all_clocks] -override
set_max_transition -data_path 400 [all_clocks] -override
set_interactive_constraint_modes {}    ;# 结束约束修改
```

**为什么要「开启/结束」**？因为 SDC 约束默认**只读**——工具不希望你在流程中途偷改约束（会导致结果不可复现）。`set_interactive_constraint_modes` 临时打开写权限，**改完必须关掉**。

:::pitfall 忘了关 interactive 模式
只开不关，后面所有 `set_*` 命令都被当成「临时修改」，不会写进最终 SDC。

结果是实现时用的约束和签核时的不一样，时序数字对不上。**养成习惯**：成对写这两行，就像括号一样。
:::

**`-override`** 是覆盖之前的值；不加的话已经设过 `max_transition` 时新值可能不生效。

**为什么分开设 clock_path 和 data_path**？时钟路径要求更严（200 ps）——时钟边沿必须陡，否则触发器采样点漂移；数据路径可以松一些（400 ps）——数据晚一点到没关系，只要在时钟沿前稳定。

## 布局命令与静态时序分析 {#source-03}

### 一条命令跑完布局

原文：**跑 place 的超级指令 `place_opt_design`**。

这一条命令包含：全局布局 → 合法化 → 详细布局 → 时序优化 → DRV 修复。叫「超级指令」是因为内部调用了十几个子步骤。方便，但**出问题时不好定位**——不知道是哪一步出的问题。

:::source
"跑place的超级指令"
"place_opt_design"
"STA静态时序分析"
:::

### Setup 与 Hold：公式怎么来的

原文给了完整推导，这是理解时序的基础。

:::fig innovus-doc-33.png | 原文图 33 · 布局命令及静态时序分析
:::

**Setup（建立时间）**：数据必须在时钟沿**之前**稳定，提前量至少等于 setup 时间。

```
Tarrive（数据什么时候到） < Trequire（最晚可以什么时候到）

Tarrive  = Tlunch + Tck2q + Tdatapath
Trequire = Tcapture + Tcycle − Tsetup − uncertainty
```

**Trequire 里为什么有「一个时钟周期」**？数据在第 N 个时钟沿发射，要在第 N+1 个沿被捕获，中间隔一个周期。

:::source
"建立时间检查 setup检查"
"第一次数据到达时间要比第一次检查时间要快"
"Trequire - Tarrive > 0"
"Trequire > Tarrive"
"Tarrive 数据到达时间"
"= Tlunch +Tck2q+Tdatapath "
"Trequire第一次检查时间"
"= Tcapture+Tck时钟周期-Tsetup(uncertainty)"
"保持时间检查 hold检查"
"第二次数据到达时间要比第一次检查时间要慢"
"Tarrive2 - Trequire > 0 "
"Tarrive2 > Trequire"
"第二次数据到达时间应该比第一次到达时间多一个周期"
"Tarrive2 = Tlunch +Tck2q+Tdatapath + Tcycle"
"Trequire = Tcapture+Tcycle +Thold(uncertainty)"
"Tlunch +Tck2q+Tdatapath - (Tcapture+Thold(uncertainty)) > 0"
"Tlunch +Tck2q+Tdatapath > Tcaputure + Tuncertainty"
"注意：place阶段不看hold，因为clock的idea的，此时hld天生就满足"
"延伸："
"addInstancePrefix"
"添加的实例的名字前缀"
"作用： debug一些单元在什么时候插入的"
"为了修复什么问题才添加的这个缓冲器"
"Instance  实例化的对象"
"fanout   扇出"
:::

:::note 这张图该看什么
STA 分析的操作界面或结果视图，对应原文的「STA 静态时序分析」小节。重点看报告里的路径分解——每条路径都分成 launch clock、data path、capture clock 三段，正好对应公式里的三项。
:::

:::fig innovus-doc-34.png | 原文图 34 · 布局命令及静态时序分析
:::

:::note 这张图该看什么
时序报告的详细展开，能看到 Tarrive 和 Trequire 的具体构成。**读报告的方法**：先看 slack 正负，再看是哪一段（launch / data / capture）贡献了最大延迟——那一段才是要优化的对象。
:::

**Hold（保持时间）**：数据在时钟沿之后还必须**保持**一段时间。原文的推导：

```
Tarrive2  = Tlunch + Tck2q + Tdatapath + Tcycle
Trequire  = Tcapture + Tcycle + Thold + uncertainty

化简（两边 Tcycle 约掉）：
Hold 余量 = (Tlunch + Tck2q + Tdatapath) − (Tcapture + Thold)
```

**关键结论：Hold 和时钟周期无关！** 周期被约掉了。这是很多人没意识到的——**降频救不了 hold 违例**。

**原文最重要的提醒**：`place 阶段不看 hold，因为 clock 是 ideal 的，此时 hold 天生就满足`。

**为什么天生满足**？理想时钟下所有触发器时钟同时到达（`Tlunch = Tcapture`），代入得 `Hold 余量 = Tck2q + Tdatapath − Thold`。只要数据路径不是极短，对绝大多数单元这个式子成立。

**CTS 之后就不一样**：时钟有了真实延迟差，`Tlunch ≠ Tcapture`，hold 违例冒出来。

:::note 这个知识点解释了流程顺序
为什么流程是 Place → CTS → 再看 hold？因为 place 阶段看 hold 没意义（恒满足），而 setup 在 place 阶段就有意义。

这也解释了为什么 CTS 之后时序会「变差」——不是设计变差了，而是之前被理想时钟掩盖的问题暴露了。
:::

### addInstancePrefix：给实例加前缀

原文延伸提到的工程习惯，很实用：`addInstancePrefix` 添加实例名字前缀，用于 debug 单元在什么时候插入、为了修什么问题。

流程会插入大量 buffer（修 DRV、修时序、做时钟树），如果名字都是工具自动生成的（`FE_OFC1234`），出问题根本不知道哪个是干什么的。**做法**：

```
fix_drv_0308_01     3月8日修DRV插的第1个
fix_hold_0308_01    修hold插的
cts_clock_buf_01    时钟树缓冲
eco_timing_01       ECO修时序
```

**价值**：出问题时能快速定位「这个 buffer 是哪一轮加的、为什么加的」。项目后期改动频繁时尤其重要。原文还提了两个术语：**Instance**（实例化对象，网表里的具体单元）、**fanout**（扇出，一个输出驱动多少输入）。

原文还给了一个最小的 path group 示例，作为前面那段完整命令集的补充：

:::source
"设置grouppath"
"对时序路径进行分组"
"group_path -name in2out -from [all_inputs] -to [all_outputs]"
"setPathGroupOptions in2out -effortLevel low"
:::

这个例子用最简单的一条命令演示了「分组 + 设力度」两步。实战中会按 reg2reg / in2reg / reg2out / in2out 分成四组，各自设不同 effort。分组的意义在于**把优化资源集中在真正重要的路径上**——in2out 这种纯组合路径通常很少且容易过，设 low 就够了。

## 布局摘要与 DRV {#source-04}

### 四类基本 DRV

:::source
"placement summary"
:::

:::fig innovus-doc-35.png | 原文图 35 · 布局摘要与设计规则违例
:::

:::note 这张图该看什么
placement summary 报告。这是判断「这次布局能不能过」的核心依据，重点看三块：时序（WNS/TNS 分组建看）、DRV 计数（四类基本 DRV）、利用率。

**读法**：先看 WNS 是否超过 -100 ps，再看 DRV 是否为 0，最后确认利用率在 45–50%。三项都过才算可接受。
:::

**DRV = design rule violation**，四类基本型：

| DRV | 含义 | 
|---|---|
| **max_transition** | 边沿太缓（上升/下降太慢） |
| **max_fanout** | 一个输出驱动的负载太多 |
| **max_length** | 走线太长 |
| **max_cap** | 总电容太大 |

**为什么四项要限制**：transition 太缓会让单元延迟变大（输入缓输出更缓），还可能引起短路功耗（PMOS 和 NMOS 同时导通）；fanout 太多驱动能力不够；length 太长 RC 延迟大且易受串扰；cap 太大充电慢同样导致边沿变缓。

**注意四者互相连锁**：fanout 多 → cap 大 → transition 缓 → 延迟大。修一个往往连带修好其他。

原文还列了其他 DRV：`setup、hold、dontuse、clock transition、min_pluse`。**min_pulse（最小脉宽）**是时钟树特有的——高或低电平持续时间不能太短，否则触发器采样不到。**dontuse** 是流程违例（用了被禁用的单元），不是制造规则。

:::source
"DRV  "
"design rule vertation"
"设计规则违反"
"基本四种drv"
"max_transtion   最大转换时间"
"分为data transtion  和clock transtion"
"max_fanout    最大扇出"
"max_length   最大长度"
"max_cap     最大负载电容"
"其他的drv："
"setup、hold、dontuse、clock transtion"
"min_pluse"
"设置约束"
"set_interactive_constraint_modes [all_constraint_modes -active]  开始设置约束"
"set_max_transition -clock_path 200 [all_clocks ] -override"
"set_max_transition -data_path 400 [all_clocks ] -override"
"set_interactive_constraint_modes {}  结束设置约束"
"place的summary"
"WNS 表示最差的结果    一般place阶段不要超过 -100ps  /   -0.1ns"
"TNS  所有违例的总和"
:::

原文这里又给了一遍那三行约束命令——和前面 path group 那节是同一对，**再出现说明它是常用操作**，值得记住。

:::fig innovus-doc-36.png | 原文图 36 · 布局摘要与设计规则违例
:::

**Summary 的判据**：原文给了具体数字——**WNS 一般 place 阶段不要超过 -100ps / -0.1ns**；TNS 是所有违例的总和。

**WNS（Worst Negative Slack）**：最差那条路径差多少，负数表示违例。**TNS（Total Negative Slack）**：所有违例路径余量绝对值之和，反映整体有多差。

**为什么 place 阶段允许 -100 ps**？因为后面还有 CTS 和 OptRoute 两轮优化。place 阶段就修到 0 会导致插过多 buffer（浪费面积功耗）、走线过度优化（抢后面资源），而且 CTS 后时钟变真实了现在的优化可能白做。

**所以 -100 ps 是「留有余地」的判据，修到 0 反而不正常。**

:::note 判据要分路径组看
原文特别提到**需要关注 reg2reg、reg2cg、reg2mem（除了 in/out 那些）**。

为什么排除 in2out？它是纯组合路径、数量少、延迟主要由外部环境决定（input/output delay）、内部优化空间有限、约束通常设得比较松。

所以全局 WNS 可能被 in2out 的个别路径拉低，但那不是真正的问题。
:::

## 利用率与面积计算 {#source-05}

### 利用率的经验值

:::source
"3）利用率"
"一般Place的利用率在45%-50% "
"postroute不超过60%"
:::

原文给了三个阶段参考：**place 45%–50%，postroute 不超过 60%**。

**为什么 place 阶段只有 45–50%**？因为后面还要插东西：CTS 插时钟缓冲器、时序优化插 buffer、修 DRV 插 buffer。从 45% 涨到 60%，中间的 15% 就是这些后加的单元。

:::pitfall 一开始就把利用率压到 60%
新手常想「面积越小成本越低」，一开始就设 60%。

结果 CTS 插完时钟树利用率变 75%，密度过高 → 布线拥塞 → 大量 short → 只能回退重来。

**正确做法**：place 阶段 45–50%，给后续留空间。
:::

### 面积计算脚本

原文给了一段很实用的 Tcl 脚本，用来算「这个设计该设多大」。

:::fig innovus-doc-37.png | 原文图 37 · 利用率与面积计算脚本
:::

:::source
"根据利用率调整die的面积"
"innovus计算面积的脚本"
"计算整个模块中std+mem的总面积"
"set all_cells [dbGet top.insts.name * -p]   #抓到所有的单元，包括mem和stdcell"
"set all_cells_area 0   #定义所有单元面积之和为0"
"foreach cell $all_cells {"
"set cell_area [dbGet ${cell}.area]   #获取单个遍历取到的单元的面积"
"set all_cells_area [expr $all_cells_area+$cell_area]"
"}"
"echo \"The total area of all cells is $all_cells_area um^2.\""
"计算所有的mem的总面积"
"set all_macros [dbGet top.insts.cell.subClass block -p2]"
"set all_macros_area 0"
"foreach macrocell $all_macros {"
"set macro_area [dbGet ${macrocell}.area]"
"set all_macros_area [expr $all_macros_area+$macro_area]"
"}"
"echo \"The total area of all macro cells is $all_macros_area um^2.\""
"计算所有的stdcell的总面积"
"set all_stdcells_area [expr $all_cells_area - $all_macros_area]"
"echo \"The total area of all std cells is $all_stdcells_area um^2.\""
"计算出当前模块应该设置的大小"
"set total_estimate_area [expr $all_stdcells_area / 0.6 + $all_macros_area / 0.7]"
"echo \"The estimated area is $total_estimate_area um^2.\""
"icc版本计算面积的脚本"
"ICC2 :"
"area"
"set stdcell_areas 0"
"set cells [get_cells -q -hier -filter \"@is_hierarchical == false \"]"
"set stdcells [get_cells -q -hier -filter \"@is_hierarchical == false && @is_hard_macro == false \"]"
"foreach_in_coll cell $stdcells {"
"set stdcell_area [get_attr $cell area]"
"set stdcell_areas [expr $stdcell_areas +$stdcell_area]"
"}"
"puts \"area of standard cell is $stdcell_areas\""
"##macro cell"
"set macro_areas 0"
"set macro_cells [filter_coll $cells \"@design_type =~ macro\"]"
"foreach_in_coll cell $macro_cells {"
"set macro_area [get_attr $cell area]"
"set macro_name [get_object_name $cell]"
"set macro_areas [expr $macro_areas +$macro_area]"
"puts \"area of $macro_name is $macro_area\""
"}"
"puts \"area of macro is $macro_areas\""
"set total_estimate_area [expr $stdcell_areas / 0.65 + $macro_areas / 0.82]"
"puts \"The estimated area is $total_estimate_area um^2."
"设置display能显示的最大行数量"
"set enc_tcl_return_display_limit 99999"
:::

:::note 这张图该看什么
利用率与面积计算相关的报告/脚本视图。重点看利用率数字与面积统计，对照脚本算出来的估算面积。
:::

脚本四步，逐段解释。**第一步算所有单元总面积**：

```tcl
set all_cells [dbGet top.insts.name * -p]     ;# 抓所有单元，含 mem 和 stdcell
set all_cells_area 0
foreach cell $all_cells {
    set cell_area [dbGet ${cell}.area]
    set all_cells_area [expr $all_cells_area + $cell_area]
}
```

**第二步算宏总面积**，关键在 `subClass block`：

```tcl
set all_macros [dbGet top.insts.cell.subClass block -p2]   ;# 按分类属性筛宏，不靠名字匹配
set all_macros_area 0
foreach macrocell $all_macros {
    set macro_area [dbGet ${macrocell}.area]
    set all_macros_area [expr $all_macros_area + $macro_area]
}
```

用**单元的分类属性**筛宏，不是靠名字匹配（`*RAM*`）。前者可靠，后者依赖命名规范。

**第三步**：`set all_stdcells_area [expr $all_cells_area - $all_macros_area]`。

**第四步估算目标面积**，这是整段脚本的核心：

```tcl
set total_estimate_area [expr $all_stdcells_area / 0.6 + $all_macros_area / 0.7]
```

**为什么要分开算再相加**？因为标准单元和宏的「可填充程度」不同：标准单元区可填到 60%（留布线空间），宏区可填到 70%（宏周围要留 channel，但宏本身是实心块）。

**如果笼统地 `总面积 / 0.6`，会低估宏占的地方**——宏之间要留通道，不能按 60% 填。注意分子分母关系：`面积 / 利用率 = 需要的总空间`，算出的是「core 应该多大」。

**ICC2 版本**用不同命令体系（`get_cells` / `-filter` / `foreach_in_coll` / `get_attr`），系数是 0.65 / 0.82。**系数不同是因为工具和工艺不同，不是谁对谁错**，抄脚本要改系数。

原文还给了一行很实用的小命令：`set enc_tcl_return_display_limit 99999`，把 Tcl 输出显示上限调大。默认 `dbGet` 返回大量结果时只显示前几个，加这行才能看全。

## 跑完 place 查什么 {#source-06}

原文给了五项检查，是最实用的验收清单。

:::source
"跑完place需要check什么"
"1）检查setup的时序是否符合预期，一般在-100ps左右都是合理的，需要关注reg2reg  reg2cg  reg2mem(除了In\\out那些)"
"2）检查是否有congestion的问题，先看congestion map,其次看overflow的值是否符合要求，一般在1.5%"
"3）cell 的density (单元摆放密度)不要超过80%"
"4）检查设计的ut利用率（随着步骤往后，利用率是不断上升的，place阶段利用率大概在45%左右）"
"5）检查DRV是否有违例(四种基本DRV)"
"修复setup"
"设置group单独对有违例的path进行优化"
"group_path -name  gp1  -from  [get_cells {cell1 cell2 cell3}]"
"group_path -name gp2  -to [get_cells {cell1 cell2 cell3}]"
"setPathGroupOptions gp1 -effortLevel high"
"setPathGroupOptions gp2 -effortLevel high"
"设置pathmargin/input_delay "
"例如：  原本违例  -20ps, 设置pathmargin, 会变成-120或者-220ps，工具修复到-80ps"
"等工具修完之后，在拿掉这个margin，违例可能就修复掉了"
:::

**① Setup 时序**：原文说「一般在 -100ps 左右都是合理的，需要关注 reg2reg、reg2cg、reg2mem（除了 in/out 那些）」。判据前面讲过——-100 ps 是留余地的标准，修到 0 反而说明过度优化。

**② 拥塞**：先看 congestion map，再看 overflow，**一般在 1.5%**。

注意这个数字和 Floorplan 那课的 1% 不同：Floorplan < 1%，**Place < 1.5%**。为什么放宽？因为 place 阶段还没真正布线、估算误差大，留余量给 route 优化是合理的。但太大会导致 route 修不回来。

**③ Cell density**：不要超过 80%。超过这个值剩余空间不足以走线——布线需要穿过单元区的空隙。

**④ UT 利用率**：place 阶段大概 45% 左右。**「随着步骤往后不断上升」这句话是关键认知**——利用率是动态的，每次插 buffer 都会涨。所以看到利用率要问「这是哪个阶段的」，place 的 50% 和 route 的 50% 是两个概念。

**⑤ DRV**：四种基本 DRV 都要查。

### 修复 setup 的两个技巧

**技巧一：给违例路径单独建组**

```tcl
group_path -name gp1 -from [get_cells {cell1 cell2 cell3}]
group_path -name gp2 -to   [get_cells {cell1 cell2 cell3}]
setPathGroupOptions gp1 -effortLevel high
setPathGroupOptions gp2 -effortLevel high
```

把有违例的路径单独成组给 high effort，让工具优先修。

**技巧二：临时加 margin 逼工具多修一点**。原文的解释很精彩：原本违例 -20 ps，设置 pathmargin 后变成 -120 或 -220 ps，工具修复到 -80 ps，等修完拿掉 margin，违例可能就修掉了。

**算一遍就清楚了**：

```
原始约束：要求 0，实际到达 -20        → 违例 20 ps
加 margin 100：要求变 100，实际还是那个延迟 → 违例 120 ps
工具优化，把延迟改善 40 ps           → 违例 80 ps（相对收紧后的 100）
拿掉 margin：要求回到 0，延迟改善了 40 ps → 余量 +20 ps ✓
```

**本质是「给工具一个更严格的目标，逼它多用力」**。但 margin 不能加太大，否则工具会插过多 buffer 反而恶化。

:::pitfall margin 忘了拿掉
加 margin 是为了逼工具优化，但**最后必须拿掉**。

忘了拿掉会让最终 SDC 带着虚假 margin，签核时按过严约束检查报一堆假违例；或者实现按过严约束做，面积功耗白涨。

用 margin 时一定要记录「在哪一步加了、什么时候拿掉」。
:::

## 检查清单 {#checklist}

:::check
- 布局合法性四项都验过：方向、无重叠、在 row 上、不违反 floorplan 约束
- `checkPlace` 无 overlap、无 VT 不匹配
- scan reorder 在 DFT 允许范围内，链描述已同步更新
- OCV 模式明确（OCV/AOCV/SOCV），CPPR 已开启
- path group 按 reg2reg/in2reg/reg2out/in2out 等正确划分
- 主要组 effortLevel 设 high，边角组设 low
- 约束修改用 `set_interactive_constraint_modes` 成对开关，没有只开不关
- `place_opt_design` 跑完后 setup 时序在 -100 ps 以内
- 分组建看 WNS，排除 in2out 的干扰
- overflow < 1.5%，congestion map 无大面积红色
- cell density < 80%
- 利用率在 45–50% 区间（为后续插入留余量）
- 四类基本 DRV（transition/fanout/length/cap）无违例
- 插入的 buffer 都加了有意义的前缀（fix_drv_xxx / fix_hold_xxx）
- 临时加的 path margin 已拿掉
- 面积计算脚本跑过，core 尺寸与估算值核对
:::

## 自测 {#quiz}

:::quiz
全局布局、扫描链重组、详细布局三阶段各做什么？| 全局布局确定大致位置并评估拥塞和密度；扫描链重组在允许范围内缩短测试链走线；详细布局做合法化并细调线长与时序。
为什么 place 阶段不用查 hold？| 此时时钟是理想网络，所有触发器时钟同时到达（Tlunch=Tcapture），代入 hold 公式后天然满足。要等 CTS 后有真实延迟差才暴露。
OCV 的根本缺陷是什么？为什么路径越长越悲观？| 用统一 derate 逐级累乘，长路径累积悲观量按级数指数增长，而实际随机偏差会互相抵消。
CPPR 解决什么问题？| 发射和捕获时钟路径在分叉点之前是同一段物理线，OCV 却按 late 和 early 各算一次，产生虚假悲观量。CPPR 把这段重复计算加回去。
AOCV 为什么「级数越多 derate 越小、距离越远 derate 越大」？| 随机偏差在多级串联时统计平均互相抵消（中心极限定理）；距离远则两单元 PVT 环境差异大，偏差相关性低。
SOCV/POCV 比 AOCV 更乐观的原因？| 用概率分布代替固定系数，多级串联时方差按平方根增长而非线性累加，更准确反映偏差抵消。
Setup 和 Hold 公式分别是什么？Hold 为什么和时钟周期无关？| Setup: Tarrive < Trequire，其中 Trequire 含一个 Tcycle。Hold: 两边都含 Tcycle 被约掉，所以降频救不了 hold。
四类基本 DRV 是什么？为什么互相连锁？| max_transition、max_fanout、max_length、max_cap。fanout 多导致 cap 大，cap 大导致 transition 缓，transition 缓导致延迟大。
place 阶段 WNS 判据为什么是 -100 ps 而不是 0？| 后面还有 CTS 和 OptRoute 两轮优化；修到 0 说明过度优化，会插过多 buffer、浪费面积功耗，且 CTS 后时钟变真实可能白做。
place 阶段利用率为什么只要 45–50%？| 后面 CTS 插时钟树、时序优化和修 DRV 再插 buffer，利用率会涨到 60% 左右。一开始压太满会导致密度过高、布线拥塞。
面积估算公式为什么把标准单元和宏分开算？| 标准单元区可填到 60%（留布线空间），宏区可填到 70%（宏间要留 channel）。笼统按 60% 会低估宏占的空间。
set_interactive_constraint_modes 为什么要成对开关？| 只开不关会让后续约束修改不被写入最终 SDC，导致实现和签核用的约束不一致。
临时加 path margin 的原理？为什么必须拿掉？| 收紧约束逼工具多用力优化，实际改善后再放开。忘了拿掉会让最终 SDC 带虚假约束，报假违例或过度优化。
addInstancePrefix 这类前缀的工程价值？| 出问题时能快速定位这个 buffer 是哪一轮、为修什么问题加的。项目后期改动频繁时尤其重要。
place 阶段 overflow 阈值和 floorplan 为什么不同？| floorplan <1%，place <1.5%。place 阶段还没真正布线、估算误差大，留余量给 route 优化是合理的。
:::

## 延伸阅读 {#next}

下一课是 [CTS：时钟树综合](/lesson/03-08-cts/)。

| 主题 | 参考 |
|---|---|
| 布局密度与拥塞诊断 | [Place 诊断](/lesson/03-01e-placement-diagnostics/) |
| GCell 溢出计算 | [Overflow](/lesson/03-01l-overflow/) |
| 按阶段读 Setup 和 Hold | [时序与噪声诊断](/lesson/03-01h-timing-noise/) |
