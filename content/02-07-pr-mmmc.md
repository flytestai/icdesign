---
id: 02-07-pr-mmmc
no: 23
stage: 2
title: MMMC：多模式多端角，工具到底在几种世界里跑时序
en: MMMC: Multi-Mode Multi-Corner Analysis
hours: 2
minutes: 20
tags: [MMMC, viewDefinition, corner, PVT, RC corner, DFT, 超频, analysis view]
summary: 一颗芯片不能只按"正常工作、典型电压、室温"来验。这一课讲清多模式（func / 超频 / DFT）与多端角（工艺、电压、温度、RC）为什么要组合，把 viewDefinition.tcl 里的 library set、rc corner、delay corner、constraint mode、analysis view 五层结构拆开，最后说清 setup 和 hold 各看哪个 view、配错了会出什么事故。
---

## 一个设计，很多种"世界" {#why}

:::goal 能说出模式（func / 超频 / DFT）与端角（PVT / RC）两个维度各描述什么；能画出 viewDefinition.tcl 里 library set → rc corner → delay corner → constraint mode → analysis view 的五层引用关系；能立刻回答 setup 用哪个 view、hold 用哪个 view，并解释原因。
:::

假设你只按一种条件验芯片：正常工作模式、0.81V、125°C、慢速工艺库。会发生什么？

- 换到**超频模式**（电压拉高、频率拉高），时序全崩；
- 进了**DFT 测试模式**（扫描链串起来），工具从没优化过这条路，测试跑不通；
- 到了**低温环境**（先进工艺的温度反转效应），setup 反而不够了；
- **hold** 检查完全没做快 corner，芯片一上电就锁死。

所以签核不能只看一个"世界"，必须**把所有关键条件排列组合，每一种都跑一遍**。这就是 MMMC：

:::term MMMC | 多模式多端角
**M**ulti-**M**ode（多模式）× Multi-**C**orner（多端角）。Mode 描述"芯片在干什么"（功能/超频/测试），Corner 描述"芯片在什么物理条件下工作"（工艺快慢、电压、温度、RC）。两者的组合叫一个 **analysis view**，每个 view 都要单独跑时序。
:::

MMMC 的全部配置信息集中在一个文件里——文档说的 **`viewDefinition.tcl`**（也常写作 `view_definition.tcl`，放在 `scripts/` 下）。**这是 init 阶段除了 sdc 之外最容易被漏掉的文件**，漏了工具就只按默认的一套环境跑，报告好看但全是假的。

## 多模式 Mode：芯片在干什么 {#mode}

:::term mode | 工作模式
芯片的一种工作状态。不同模式下电路的结构、时钟、频率、约束都不一样，所以必须各有一套 sdc。
:::

文档列了三类，加一类工程上常见的：

### 1. func 模式：功能模式 {#func}

芯片**正常工作**时的模式，也是最主要、优化力度最大的模式。你平时看到的时序报告，绝大部分来自 func 模式。

### 2. 超频模式（Performance） {#turbo}

:::term 超频模式 | performance mode
性能最强的工作模式：**增强电压 + 提升时钟频率**，把芯片压到极限跑。频率上去了，周期变短，时序最紧，所以这一套 sdc 里的 clock period 要按超频后的频率写。
:::

注意这里有个容易忽略的细节：超频往往伴随**电压升高**，而电压升高会让延迟变小（上一课讲过）。所以超频模式不是简单"把周期改小"就完事，**它的 lib 也要跟着换成高压的那一份**——这就是为什么 view 是"模式 × 端角"的组合，而不是单一维度。

### 3. DFT 模式：测试模式 {#dft}

:::term DFT | Design for Test 可测性设计
为了让芯片出厂后能被测试而加入的设计。**DFT 部门会针对网表插入 scan chain（扫描链）**，把大量触发器串成移位寄存器，用少量引脚把内部状态扫进扫出，从而用自动测试机（ATE）覆盖到几乎每个门。
:::

文档对 DFT 的价值说得很到位：**"可以更早发现问题所在，减少损失和成本。"** 一颗芯片流片回来，如果没有 DFT，内部某个门坏了你根本定位不到；有了扫描链，测试向量能直接指到具体位置。

对 PR 的影响：

- scan chain 是一条**全新的、很长的路径**（几千个触发器串起来），PR 必须专门为它做优化和绕线；
- DFT 模式下时钟结构不同（常常是"扫描时钟"直通），所以**必须单独一套 sdc**；
- 有些设计还会做 scan chain reordering（重排扫描链顺序），让物理上相邻的触发器串在一起，减少绕线长度。

### 4. 模式怎么切换：预留引脚 {#pin}

文档提到"**一般预留引脚来触发不同的模式**"。这在工程上非常常见：

- 芯片留几个**测试模式选择脚**（test mode pin），上电时拉高就进 DFT 模式；
- 有的用 efuse / 寄存器配置位来切模式；
- 超频模式可能靠一个"性能使能"脚配合外部供电。

对 PR 的意义：这些模式选择脚是**真实的物理端口**，floorplan 时要给它们留位置，而且它们的输入延迟/驱动要按最严的模式约束。

## 多端角 Corner：芯片在什么条件下工作 {#corner}

:::term corner | 端角
一组极端工艺/电压/温度条件的组合。芯片制造有偏差、供电有波动、环境温度有范围，签核必须在这些范围的**边界**上做——边界就是"端角"。
:::

### P / V / T 三个维度 {#pvt}

| 维度 | 含义 | 典型取值 |
|---|---|---|
| **P** 工艺 | 制造偏差导致的晶体管快慢 | `ss`（慢）、`tt`（典型）、`ff`（快） |
| **V** 电压 | 供电电压的允许范围 | 标称 0.81V，低到 0.74V、高到 0.88V |
| **T** 温度 | 工作环境温度范围 | `125c`（高温）、`m40c`（-40°C 低温） |

组合起来就是库文件名里的那串：`ssg0p81v125c` = 慢工艺 + 0.81V + 125°C。

### RC corner：线也有快慢 {#rc}

上一课讲过，线延迟取决于寄生 R 和 C。工艺偏差让 R、C 各有偏差，于是要单独定义一组 RC corner：

:::term RC corner
一组寄生参数抽取的系数（res 系数、cap 系数）与温度设定。**同一个版图，用不同 RC corner 抽出来的 R、C 不同，算出的 net delay 就不同。**
:::

文档把因果链讲得很清楚：

- **"由于工艺生产过程有误差，所以要考虑各种情况"** —— R、C 都有 ±x% 的偏差；
- **"信号通过导线越快，可能导致 hold 问题"** —— 线太快，新数据冲到下一级太早；
- **"信号通过导线越慢，可能导致 setup 问题"** —— 线太慢，数据来不及在时钟沿前到达。

所以 RC corner 至少要有两端：**最快的（cbest / rcbest）给 hold 用，最慢的（cworst / rcworst）给 setup 用**。

## viewDefinition.tcl：五层结构一张图 {#viewdef}

这份文件不是随便写的配置，它有严格的**层层引用**关系。看清这个结构，你就再也不会写错：

```
[1] create_library_set        ──┐  用哪些 lib（决定 cell 快慢）
     (名字, lib 文件列表)        │
                                ↓
[2] create_rc_corner          ──┐  用哪些 RC 系数（决定线快慢）
     (名字, QX 技术文件, 温度)   │
                                ↓
[3] create_delay_corner       ──┐  把 [1] + [2] 绑在一起 = 一个物理条件
     (名字, library_set, rc_corner) │
                                ↓
[4] create_constraint_mode    ──┐  用哪套 sdc（决定"要求"）
     (名字, sdc 文件列表)        │
                                ↓
[5] create_analysis_view      ──┐  [3] + [4] 组合 = 一个 view
     (名字, delay_corner, constraint_mode) │
                                ↓
[6] set_analysis_view         ──┘  指定哪些 view 做 setup、哪些做 hold
```

对应文档说的"由图上几部分组成"，我们逐个看代码。

### ① library set：慢组 / 快组 {#libset}

```tcl
# 慢速低压高温组：setup 分析用这一套（延迟最大）
create_library_set -name slh \
    -timing { /libs/tsc28_lvtssg0p74v125c.lib \
              /libs/tsc28_lvtssg0p74vm40c.lib }

# 慢速低压低温组：先进工艺温度反转，"慢 + 冷"可能是最坏，单独成组
create_library_set -name sll \
    -timing { /libs/tsc28_lvtssg0p74vm40c.lib }

# 快速高压高温组：hold 分析用这一套（延迟最小）
create_library_set -name fhh \
    -timing { /libs/tsc28_lvtffg0p88v125c.lib }
```

命名规律（文档给的写法）：**`slh` = slow-low-hot（慢速低压高温）、`sll` = slow-low-low（慢速低压低温）、`fhh` = fast-high-hot（高速高压高温）**。

三个字母分别是 速度 / 电压 / 温度。**这套缩写看着土，但它是行业通用口语**——同事说"跑一下 slh"，指的就是这一组库。

:::tip 在 vim 里顺着路径看 lib 文件
viewDefinition.tcl 里的 lib 路径很长，手抄容易错。把光标停在路径上，按 **`gf`**（go to file）直接跳进那个 lib 文件；看完按 **`Ctrl+O`** 跳回来。

（文档写作"命令模式 g+f"，指的是先按 `g` 再按 `f`；`Ctrl+O` 是 vim 的"回到上一个位置"，可以连按。）
:::


### ② rc corner：系数 + 温度 {#rccorner}

```tcl
# 最坏电容 corner：C 取最大，net delay 偏大 → setup 用
create_rc_corner -name rc_cworst \
    -qx_tech_file /tech/qrcTechFile_cworst \
    -temperature 125

# 最好电容 corner：C 取最小，net delay 偏小 → hold 用
create_rc_corner -name rc_cbest \
    -qx_tech_file /tech/qrcTechFile_cbest \
    -temperature -40
```

注意 `-temperature`：**RC corner 自带温度**，因为金属电阻随温度变化（温度越高电阻越大）。这跟 lib 的温度是两件事——lib 管晶体管，rc corner 管导线。

### ③ delay corner：把物理条件锁死 {#delaycorner}

```tcl
# 慢条件：慢库 + 最坏 RC，cell 慢、线也慢
create_delay_corner -name dc_slow \
    -library_set slh \
    -rc_corner rc_cworst

# 快条件：快库 + 最好 RC，cell 快、线也快
create_delay_corner -name dc_fast \
    -library_set fhh \
    -rc_corner rc_cbest
```

**delay corner 是"物理世界"的完整定义**：这里不再有"模式"的概念，纯粹是快慢。所以 delay corner 的数量通常远少于 view——因为多个模式可以共用同一个 delay corner。

### ④ constraint mode：模式 = 一套 sdc {#conmode}

```tcl
# 功能模式：正常工作的一套约束
create_constraint_mode -name cm_func \
    -sdc_files { /scripts/func.sdc }

# 超频模式：周期更短、电压更高的约束
create_constraint_mode -name cm_turbo \
    -sdc_files { /scripts/turbo.sdc }

# DFT 测试模式：扫描链相关约束
create_constraint_mode -name cm_dft \
    -sdc_files { /scripts/dft.sdc }
```

**这就是"多模式"在文件里的落地方式：一个模式 = 一套 sdc。** 所以模式不是靠一个开关变量实现的，而是靠不同的约束文件。

### ⑤ analysis view：组合出最终环境 {#view}

```tcl
# 功能模式 × 慢条件：检查 setup 的主力 view
create_analysis_view -name func_slow \
    -delay_corner dc_slow -constraint_mode cm_func

# 功能模式 × 快条件：检查 hold 的主力 view
create_analysis_view -name func_fast \
    -delay_corner dc_fast -constraint_mode cm_func

# 超频模式 × 慢条件：性能极限下的 setup
create_analysis_view -name turbo_slow \
    -delay_corner dc_slow -constraint_mode cm_turbo

# DFT 模式 × 快条件：扫描链的 hold（测试时最容易挂的一项）
create_analysis_view -name dft_fast \
    -delay_corner dc_fast -constraint_mode cm_dft
```

:::tip view 数量的算法
view 数 = 模式数 × 需要的端角数。3 个模式 × 2 个端角 = 6 个 view。但实际没人全线组合——**超频模式只看慢条件，DFT 模式重点看快条件**，按需挑，通常 4~8 个 view 就够。

**view 越多，每轮优化越慢**（工具要在每个 view 上分别算时序再取最坏）。所以工程上要克制，别把 20 个 view 全打开。
:::

### ⑥ set_analysis_view：谁查 setup，谁查 hold {#setview}

```tcl
# setup 分析：慢条件的所有模式都要查（来不及到就是错）
set_analysis_view \
    -setup { func_slow turbo_slow } \
    -hold  { func_fast dft_fast }

# 查看当前配置了哪些 view、哪个是激活的
report_analysis_view
```

**setup 用慢的 view、hold 用快的 view** —— 这是 MMMC 唯一必须背下来的一句话。搞反了，报告全绿但芯片是废的。

## 配错 MMMC 会长什么样 {#pitfall}

:::pitfall 只配了一个 view
**现象**：时序报告非常漂亮，WNS 为正，看起来能流片；流片回来大批芯片在低温或测试模式下失效。

**原因**：默认只跑了一个典型条件（tt + 常温），既没有低温 corner，也没有 DFT 模式。**工具不会提醒你"你漏了一个世界"**，它只老老实实报告你让它算的那个。

**怎么查**：
1. `report_analysis_view` 看一共几个 view、覆盖了哪些模式；
2. 检查 setup 的 view 列表里是否包含慢库 + 最坏 RC，hold 的列表里是否包含快库 + 最好 RC；
3. 检查 sdc 列表里有没有 dft/超频模式的文件——**如果只有一套 sdc，几乎可以肯定漏了模式**。
:::

:::pitfall lib 与 rc corner 的温度打架
**现象**：某个 view 的时序结果明显异常（好得离谱或差得离谱）。

**原因**：lib 用的是 125°C，rc corner 的 `-temperature` 却写了 -40，两个温度混在一个 view 里。

**原则**：**lib 的温度和 rc corner 的温度要匹配**。先进工艺做低温 setup 检查时，要专门建一组"低温 lib + 低温 rc"的 delay corner，而不是随便拼。
:::

:::lab 读一份 viewDefinition.tcl，把五层结构标出来
在练习终端里执行下面几条，边跑边在纸上画结构图：

```bash
# 1. 数一数这份配置里各层各有几个对象
grep -c "create_library_set" scripts/viewDefinition.tcl    # 几个库组
grep -c "create_rc_corner" scripts/viewDefinition.tcl      # 几个 RC corner
grep -c "create_delay_corner" scripts/viewDefinition.tcl   # 几个物理条件
grep -c "create_constraint_mode" scripts/viewDefinition.tcl # 几个模式
grep -c "create_analysis_view" scripts/viewDefinition.tcl  # 几个 view

# 2. 看 setup 和 hold 分别用哪些 view（关键的一行）
grep -n -A4 "set_analysis_view" scripts/viewDefinition.tcl

# 3. 看模式名，判断覆盖了哪几种工作状态
grep -n "create_constraint_mode" scripts/viewDefinition.tcl
```

验收标准：能报出这份配置有几种模式、几个 view，setup 用了哪几个、hold 用了哪几个，以及有没有 DFT 模式。
:::

:::quiz
MMMC 两个 M 一个 C 分别是什么？| Multi-Mode（多模式）、Multi-Corner（多端角）。模式=芯片在干什么，端角=芯片在什么物理条件下工作。
func / 超频 / DFT 三种模式有什么区别？| func 是正常工作；超频是提高电压和频率的性能极限模式；DFT 是测试模式，DFT 部门插入 scan chain，用扫描链把内部状态扫进扫出。
为什么 DFT 模式需要单独一套 sdc？| 因为扫描链是一条全新的长路径，时钟结构和频率都不同，约束要求完全不一样。
setup 和 hold 各用哪种 corner？为什么？| setup 用慢 corner（慢库 + 最坏 RC），因为要检查信号最晚到达；hold 用快 corner（快库 + 最好 RC），因为要检查信号最早到达。
viewDefinition.tcl 里五层结构是什么引用关系？| library_set + rc_corner → delay_corner；sdc → constraint_mode；delay_corner + constraint_mode → analysis_view；最后 set_analysis_view 指定 setup/hold 各用哪些 view。
为什么 view 不是越多越好？| 每个 view 都要单独算时序并取最坏，view 越多每轮优化越慢；实际按需挑选 4~8 个即可。
只配一套环境会有什么后果？| 报告只在一种条件下好看，漏掉低温 corner、DFT 模式等场景，流片后在这些条件下失效，且工具不会提醒你。
:::

:::check
- 能说出模式与端角两个维度各描述什么，并给出 3 种模式、2 种端角的例子
- 能读懂 slh / sll / fhh 这组缩写（速度-电压-温度）
- 能画出 viewDefinition.tcl 的五层引用关系
- 能说出"一个模式 = 一套 sdc"这句话的含义
- 能立刻回答 setup 用慢 view、hold 用快 view，并解释原因
- 能列出配错 MMMC 的两个典型现象：只配一个 view、lib 与 rc 温度不匹配
:::
