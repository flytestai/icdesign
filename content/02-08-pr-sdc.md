---
id: 02-08-pr-sdc
no: 24
stage: 2
title: SDC 时序约束：告诉工具"做到什么程度算合格"
en: SDC Timing Constraints
hours: 3
minutes: 0
tags: [SDC, create_clock, generated clock, 虚拟时钟, uncertainty, jitter, IO delay, false path, FCT]
summary: 前面几课给的是"事实"，这一课给的是"要求"。从 DFF→组合逻辑→DFF 的基本模型讲起，一条条写出时钟、分频、虚拟时钟、抖动、时钟分组、输入输出延迟、假路径、负载三件套，说清周期与频率、占空比与 waveform 的换算，最后讲约束力度为什么直接决定优化力度，以及 SDC 由 FCT 部门负责这件事对 PR 工程师意味着什么。
---

## SDC 是什么：设计的命脉 {#what}

:::goal 能画出 DFF → 组合逻辑 → DFF 的时序模型并指出起始点/结束点；能由周期算频率、由 waveform 算占空比；能写出 create_clock / create_generated_clock / 虚拟时钟 / uncertainty / clock group / io delay / false path / 负载三件套这几类约束，并说清每条在"要求"什么。
:::

:::term SDC | Synopsys Design Constraints
一套用 Tcl 写的约束文件，对设计的**时序、面积、功耗**提出要求。工具读进来后，就按这些要求去优化——它是"优化的目标函数"，也是判断合格与否的标准。
:::

文档对它的定位非常重：**"SDC 是一个设计中至关重要的文件……它是设计的命脉，决定了芯片是否满足设计要求的规范。"**

为什么说"命脉"？因为前面几课的文件都是"事实"：

| 文件 | 性质 | 回答的问题 |
|---|---|---|
| netlist / def | 事实 | 电路连成什么样 |
| lef | 事实 | 单元和工艺允许什么形状 |
| lib / rc tech | 事实 | 延迟实际是多少 |
| **sdc** | **要求** | **必须做到多少才算合格** |

事实错了工具会报错；**要求错了工具不会报错，它会安静地做出一颗废芯片**——这就是 SDC 危险的地方。

文档里还有一句必须画重点：

:::tip 约束力度 = 优化力度
**"对工具是否能够优化到期望的范围，设置的力度越大，优化的力度就越大。"**

周期写 15ns，工具就拼命插 buffer、换大驱动、拆逻辑去挤进 15ns；周期写 40ns，工具就躺平不管。**所以约束既不能虚松（松了不干活），也不能虚紧（紧了白烧面积和功耗，还可能根本收敛不了）。**
:::

## 先建立一个时序模型 {#model}

SDC 里所有命令，本质都在描述这张图：

```
             ┌───────┐    L1     L2     L3     L4    ┌───────┐
  clk ──┬───▷│ DFF1  │──▷[&]──▷[|]──▷[^]──▷[!]─────▷│ DFF2  │───▷
        │    └───────┘   （组合逻辑：与/或/异或/非）  └───────┘
        │         ↑                                      ↑
        │      起始点                                  结束点
        │     (launch)                                (capture)
        └──────────────────────────────────────────────────┘
                     同一个时钟，同一个周期
```

- **DFF**：触发器。时钟沿到来时把输入值搬到输出，其余时间保持不变。它是时序分析的分界线。
- **L1~L4**：中间的组合逻辑（与非门、缓冲器等），只有延迟、不存数据。
- **clk**：时钟输入端，同时驱动起始和结束两个触发器。

:::term 时序分析 | 检查数据能不能被正确接收
从起始触发器（launch）发出数据，经过组合逻辑，到结束触发器（capture）被采样。要求是：
**① 不能太晚**——必须在下个时钟沿到来之前到达并稳定（setup，建立时间）；
**② 不能太早**——不能在同一个时钟沿把上一拍的旧数据冲掉（hold，保持时间）。
:::

setup 差了表现为"跑不到这么高频率"；hold 差了表现为"芯片一上电就死，频率降到 1Hz 也没用"。**hold 是硬伤，必须修到零违规。**

## 一条一条写约束 {#write}

下面这份脚本是一份最小可用的 sdc 骨架，每一行都有注释，建议直接从它开始改。

### 1. create_clock：定义源头时钟 {#createclock}

```tcl
# 定义一个叫 CLK 的时钟：周期 20ns，上升沿在 0ns、下降沿在 10ns
create_clock -name CLK -period 20 -waveform {0 10} [get_ports clk]

# 端口本身也要有驱动和负载的描述，否则第一级 delay 算不准
set_driving_cell -lib_cell BUF_X4 [get_ports clk]
```

三个参数说清楚：

| 参数 | 含义 | 本例 |
|---|---|---|
| `-name` | 时钟名，后面所有命令都靠这个名字引用 | `CLK` |
| `-period` | **周期**，单位与 lib 的 time_unit 一致（通常 ns） | `20` → 频率 = 1/20ns = **50MHz** |
| `-waveform {0 10}` | 上升沿时刻、下降沿时刻 | 0ns 起高、10ns 落低 |

:::tip 频率与周期、占空比与 waveform 的换算
- **频率 = 1 / 周期**。周期 20ns → 50MHz；周期 1.25ns → 800MHz。
- **占空比 = 高电平持续时间 / 周期**。`-waveform {0 10}` 高电平持续 10ns，占空比 = 10/20 = **50%**。
- 文档里"周期是 20、占空比是 10"这句话，那个 **10 指的是波形里的第二个数（高电平持续 10ns）**，换算成占空比是 50%。写约束时永远写**时刻**，不写百分比——这是新人最容易搞混的一处。
- 想要 25% 占空比：`-waveform {0 5}`（高 5ns，低 15ns）。
:::

换算不熟就先在下面这台 Tcl 练习台上练两遍——**改数字，按运行，看结果**：

:::tclrun
# 800MHz 对应的周期是多少 ns：1 / 0.8GHz = 1.25ns
puts [expr {1.0 / 0.8}]

# 周期 2.5ns 对应多少 MHz：1000 / 2.5 = 400MHz
puts [expr {1000.0 / 2.5}]

# 分频：源周期 1.25ns，8 分频后周期变 10ns，频率 = 100MHz
set src 1.25                                  ;# 源时钟周期
set div 8                                     ;# 分频系数
set per [expr {$src * $div}]                  ;# 分频后周期
puts "分频后周期 $per ns，频率 [expr {1000.0 / $per}] MHz"

# 倍频：周期除以倍数
set mul 2                                     ;# 倍频系数
puts "倍频后周期 [expr {$src / $mul}] ns"      ;# 1.25/2 = 0.625ns → 1600MHz
:::

### 2. create_generated_clock：分频与倍频 {#genclock}

芯片内部几乎不可能所有模块都跑同一个频率。文档举的例子非常典型：

> 进入的时钟是 800M，模块内只能接受 100M 或者 200M，需要进行降频——分成 8 个，每个 100M；分成 4 个，就是每个 200M。

```tcl
# 8 分频：800MHz 进来，分出 100MHz，源是端口 clk，产生在分频器的 Q 端
create_generated_clock -name CLK_DIV8 \
    -source [get_ports clk] \
    -divide_by 8 \
    [get_pins u_div/Q]

# 倍频：100MHz 倍到 200MHz，源是 PLL 的参考输入，产生在 PLL 输出
create_generated_clock -name CLK_MUL2 \
    -source [get_pins u_pll/REFCLK] \
    -multiply_by 2 \
    [get_pins u_pll/CLKOUT]
```

**为什么必须显式声明？** 因为工具不知道分频器的 Q 端和输入时钟是什么关系。你不声明，它就认为那是一根普通的信号线——于是**整条时钟路径上的时序全都不分析**，报告一片绿。

文档里"倍频 = 加快时钟频率，例如 100MHz → 200MHz"就是这个意思。倍频通常来自 PLL，分频来自计数器/分频器。

### 3. Virtual Clock：虚拟时钟 {#virtual}

:::term 虚拟时钟 | virtual clock
一个**没有物理端口**的时钟。它只存在于约束里，用来描述"芯片外部那颗器件"的时钟。
:::

典型场景：芯片的数据从外面一颗 DDR 或另一个芯片送进来，那个器件有自己的时钟，你在芯片内部找不到它的端口。这时你要建一个虚拟时钟，作为 `set_input_delay` 的参考：

```tcl
# 建一个虚拟时钟：代表板上另一颗芯片的 100MHz 时钟（周期 10ns）
create_clock -name VCLK -period 10

# 用虚拟时钟约束输入延迟：外部器件在这个时钟下，已经用掉了 3ns
set_input_delay -clock VCLK -max 3.0 [get_ports din*]
```

**判断标准很简单**：如果参考时钟在芯片内部找不到对应的物理端口，就用虚拟时钟。

### 4. clock_uncertainty：抖动与余量 {#uncertainty}

:::term clock_uncertainty | 时钟不确定性
在时序分析里预扣的一笔"安全余量"，主要覆盖 **jitter（时钟抖动）** 和 skew 的建模误差。它不来自任何一根具体的线，而是人为设定的保险。
:::

```tcl
# setup 分析预扣 0.15ns：假设时钟沿可能提前/推迟这么多
set_clock_uncertainty -setup 0.15 [get_clocks CLK]

# hold 分析预扣 0.08ns：hold 通常留的余量小一些
set_clock_uncertainty -hold 0.08 [get_clocks CLK]
```

这笔余量怎么定？看时钟源的质量：

- 来自 PLL 且 PLL 抖动指标好 → 可以小（0.05~0.1ns）；
- 来自外部晶振、经过长走线 → 要大；
- **写 0 是绝对错误**——等于假设时钟沿完美无抖动，流片回来必然挂掉一批。

文档把它和"时钟抖动 jitter"并列，实际工作中你说的"uncertainty 给多少"就是问这个数。

### 5. Clock Group：时钟分组 {#group}

芯片里常有多组时钟（功能时钟、测试时钟、接口时钟）。**异步的时钟之间，路径根本不需要做时序分析**——它们的相位关系不确定，分析出来的数没有意义。

```tcl
# 声明 CLK 与 CLK_DIV8 是同步关系（有固定分频关系，需要分析）
# 而 CLK 与 TEST_CLK 是异步的，两者之间的路径不分析
set_clock_groups -asynchronous \
    -group {CLK CLK_DIV8} \
    -group {TEST_CLK}

# 完全互斥的时钟（用 MUX 二选一，不可能同时存在）
set_clock_groups -logically_exclusive \
    -group {CLK} -group {CLK_ALT}
```

`-asynchronous` 和 `-logically_exclusive` 的区别值得记一下：

- **asynchronous**：两个时钟都在跳，但没有固定相位关系（比如两个独立晶振）；
- **logically_exclusive**：物理上不可能同时有效（MUX 选了 A 就不会选 B）。

### 6. input_delay / output_delay：给外部留时间 {#iodelay}

这是新人最常写错的一类约束。它**不是**"我这根线有多长"，而是"**外部世界已经占用了多少时间**"。

```tcl
# 输入侧：外面那颗器件从时钟沿到数据稳定，用掉了 3.0ns
# 意思是：内部只剩 周期 - 3.0 - 触发器建立时间 可用
set_input_delay -clock VCLK -max 3.0 [get_ports din*]
set_input_delay -clock VCLK -min 0.5 [get_ports din*]

# 输出侧：芯片出去的数据，要在下个时钟沿前 2.5ns 就稳定，留给板级走线
set_output_delay -clock VCLK -max 2.5 [get_ports dout*]
set_output_delay -clock VCLK -min 0.3 [get_ports dout*]
```

`-max` 管 setup（最晚什么时候到），`-min` 管 hold（最早什么时候到）。**四个数一个都不能少**，少写一半，另一方向的检查就等于没做。

### 7. false_path：这些路径别修 {#falsepath}

:::term false path | 假路径
物理上存在，但**功能上永远不会在指定时序关系下工作**的路径。声明之后工具就不去优化它。
:::

```tcl
# 测试时钟到功能时钟：两者永不同时工作，跨域路径不分析
set_false_path -from [get_clocks TEST_CLK] -to [get_clocks CLK]

# 经过某个 MUX 选择端的配置路径：慢一点没关系，不占用时序预算
set_false_path -through [get_pins u_cfg_mux/SEL]

# 复位/配置寄存器这类静态信号，只需要约束"别太慢"，不需要按周期卡
set_false_path -from [get_ports rst_n]
```

**不写 false path 的后果很实在**：工具会拼尽全力去修一条根本不需要修的路径，插一堆 buffer、换超大驱动单元——**白烧面积、白烧功耗，还拖慢运行时间**，甚至把本来能收敛的地方挤到收敛不了。

反过来，**false path 写多了更危险**：把真路径标成假路径，等于关掉了检查，问题会一路瞒到流片。

### 8. 负载三件套：fanout / capacitance / transition {#load}

文档把"时序约束的分类"归到这三个量，它们是端口的**电气约束**：

| 约束对象 | 物理含义 | 命令 |
|---|---|---|
| **fanout** 负载个数 | 一个输出最多能带几个输入（带太多驱动不动） | `set_max_fanout 32 [current_design]` |
| **capacitance** 负载电容 | 一个输出最多能带多大电容 | `set_max_capacitance 0.15 [get_ports dout*]` |
| **transition** 翻转时间 | 信号从 0 到 1 最多允许多久（太"软"会被当成毛刺） | `set_max_transition 0.2 [current_design]` |

端口上还要给出**驱动能力与实际负载**，否则第一级和最后一级算不准：

```tcl
# 输入端口：用一个真实单元来代表外部驱动能力（比 set_input_transition 更准）
set_driving_cell -lib_cell BUF_X4 -pin Z [get_ports din*]

# 输入端口：直接给一个 transition 值（简单但粗糙）
set_input_transition 0.15 [get_ports din*]

# 输出端口：外部挂了多大电容（板级走线 + 接收端引脚）
set_load 0.05 [get_ports dout*]
```

回想上一课：**cell delay 由 input transition 和 output load 决定**。这三条命令就是在给这两端"喂数据"——喂错了，所有延迟数字都是编的。

## 谁写 SDC：FCT 部门 {#fct}

文档明确：**SDC 由 FCT（Full Chip Timing，全芯片时序）部门负责编写。**

这对 PR 工程师意味着什么，很值得说清楚：

1. **你不是 sdc 的作者，你是使用者和反馈者**。sdc 是"需求文档"，PR 是"施工方"。
2. **发现约束不合理（比如某条路径根本不可能在两周期内收敛），要提给 FCT 改**，不能自己偷偷在本地改一份跑——本地改完报告好看了，回到正式约束立刻崩，白干两周。
3. **debug 的第一件事往往是核对 sdc 版本**。项目里 sdc 会不断更新（v1.0 → v1.3），跑出来的结果和同事对不上，八成是拿了不同版本的 sdc。
4. **要能读懂每一条约束在要求什么**。哪怕不写，也要能判断"这条路径为什么要求这么紧"。

:::pitfall 抄别人的 sdc，只改周期
**现象**：约束能读进去，工具也跑了，但时序怎么都收敛不了，或者收敛了但报告里有一堆奇怪的违例。

**原因**：sdc 和设计是**一一对应**的。时钟名、端口名、层次名、生成时钟的 pin 位置，全都跟具体设计绑定。抄过来只改周期，等于给另一个人的设计下命令——工具找不到 `[get_ports clk]` 就静默忽略，找不到 `[get_pins u_div/Q]` 就报 warning。

**怎么查**：
1. 读 sdc 后先看 warning，`Can't find port/pin/clock` 这类一条都不能留；
2. `report_clocks` 确认时钟真的建上了（数量、周期对不对）；
3. `report_timing` 看路径的起点是不是你预期的触发器，不是就说明约束没生效。
:::

:::pitfall uncertainty 设成 0，或者 false path 满天飞
**现象 A**：为了让报告好看，把 `set_clock_uncertainty` 改成 0、把难修的路径全标 false path。报告全绿，流片回来一半芯片点不亮。
**现象 B**：反过来，uncertainty 给 0.5ns（周期才 2ns），工具怎么都收不敛，最后靠狂插 buffer 硬凑，面积功耗爆炸。

**正确做法**：uncertainty 按时钟源质量给（PLL 好就 0.05~0.1ns，外部时钟给大些）；false path 只用于**功能上真的不存在**的路径，且要有依据（跨异步时钟、配置寄存器、测试逻辑）。
:::

:::lab 审一份真 sdc
在练习终端里执行下面几条，边跑边记：

```bash
# 1. 看有几个时钟，名字和周期分别是什么
grep -n "create_clock" func.sdc

# 2. 看有没有生成时钟（分频/倍频）——没有的话多半是漏了
grep -n "create_generated_clock" func.sdc

# 3. 看不确定性给了多少（给 0 就是埋雷）
grep -n "set_clock_uncertainty" func.sdc

# 4. 统计假路径条数，太多要问清楚依据
grep -c "set_false_path" func.sdc

# 5. 检查输入输出延迟是否 max/min 都给了
grep -n "set_input_delay\|set_output_delay" func.sdc
```

验收标准：能报出这份 sdc 的主时钟周期与对应频率、有几个生成时钟、uncertainty 是 setup/hold 各多少、假路径几条，以及 input/output delay 有没有缺 `-min`。
:::

:::quiz
SDC 全称是什么？它对设计的哪三个方面做约束？| Synopsys Design Constraints；对时序、面积、功耗做约束。它是优化的目标，决定芯片是否满足规范。
`create_clock -period 20 -waveform {0 10}` 对应多少频率、多少占空比？| 周期 20ns → 频率 1/20ns = 50MHz；高电平持续 10ns，占空比 10/20 = 50%。
文档说"周期 20、占空比 10"，那个 10 到底指什么？| 指 waveform 里的第二个数，即下降沿时刻/高电平持续时间 10ns，换算成占空比是 50%。写约束永远写时刻，不写百分比。
为什么分频时钟必须用 create_generated_clock 声明？| 工具不知道分频器输出与输入时钟的关系，不声明就当成普通信号，整条时钟路径不做时序分析，报告全绿但全是漏检。
什么情况下用虚拟时钟？| 参考时钟在芯片内部找不到对应物理端口时（比如板上另一颗器件的时钟），用来做 set_input_delay 的参考。
set_input_delay 的含义是什么？| 不是线长，而是"外部世界已经占用了多少时间"；内部可用的时间 = 周期 - input_delay - 建立时间。max 管 setup、min 管 hold，四个数都不能少。
set_false_path 写多了会怎样？写少了会怎样？| 写多了等于关掉真路径的检查，问题瞒到流片；写少了工具会去修根本不需要修的路径，白烧面积功耗、拖慢收敛。
uncertainty 为什么不能设 0？| 它代表 jitter 与建模误差的安全余量，设 0 等于假设时钟沿完美无抖动，流片后必然因抖动挂掉一批芯片。
:::

:::check
- 能画出 DFF → 组合逻辑 → DFF 的模型，并指出起始点、结束点
- 能由周期算出频率、由 waveform 算出占空比，反过来也会
- 能写出 create_clock / create_generated_clock / create_clock 虚拟时钟三条命令并解释参数
- 能说清 set_input_delay / set_output_delay 的 -max 与 -min 各管什么
- 能举出两类该写 false path 的场景，并说出乱写的后果
- 能说出 fanout / capacitance / transition 三个电气约束各自限制什么
- 能说出"约束力度 = 优化力度"的含义，以及为什么 sdc 由 FCT 部门负责
:::
