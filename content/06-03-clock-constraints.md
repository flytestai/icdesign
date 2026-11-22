---
id: 06-03-clock-constraints
no: 38
stage: 6
title: 高级时钟约束：虚拟时钟、生成时钟、门控检查与最小脉宽
en: Advanced Clock Constraints
hours: 5
minutes: 50
tags: [SDC, virtual clock, generated clock, clock gating check, min pulse width]
summary: 课件里有四个 PDF 专门讲「高级时钟约束」，这些是新人最常漏写、也最常在签核时才被发现的一类约束。这一课把六条约束讲透：虚拟时钟、传播时钟、生成时钟、源延迟、门控检查、最小脉宽。
status: live
---

## 五条基础约束，覆盖不了真实的芯片 {#why}

:::goal 学完这一课，你能为一个带外部接口、分频时钟和门控单元的 SoC 写出一份完整的高级时钟约束，并用四条命令自己验收，说清每条违例是约束漏写还是设计真有问题。
:::

SDC 的五条基础约束——`create_clock`、`set_input_delay`、`set_output_delay`、`set_clock_uncertainty`、`set_false_path`——在 05-02 课里已经逐条拆过。这一课不重复它们，只讲**它们覆盖不到的场景**。

先看五个真实场景，每一个都对应一条高级约束：

| 场景 | 约束没写对的后果 | 对应约束 |
|---|---|---|
| 芯片外接 DDR 或 ADC，外部器件的时钟不在你的端口上 | 输入延迟没有参照，工具按 0 算，接口时序假乐观 | 虚拟时钟 |
| 一个时钟分频出 100MHz 给低速模块 | 分频后的触发器没有时钟，全部 unconstrained | 生成时钟 |
| 时钟经过 ICG 门控单元才到触发器 | enable 的 setup/hold 没人查，硅片上切出半截脉冲 | 门控检查 |
| 两个时钟经 MUX 二选一 | 工具同时按两个时钟分析，产生大量假违例 | 生成时钟 + 时钟组互斥 |
| 时钟从 PLL 出来，进芯片前已经走了一段 | 时钟延迟算少了，setup/hold 同时偏 | 源延迟 |

:::scene 周一早上，8 千条 clock gating 违例
你接手一个已经跑到 signoff 的 SoC：核心 500MHz、DDR 接口 800MHz、还有一个 100MHz 的低速域。PT 报出 12000 条违例，其中 8000 条是 ICG 的 enable 端 setup 违例，2000 条来自 DDR 输入接口，剩下的是分频时钟域的 hold。

leader 看了五分钟，说："这不是设计坏了，是约束漏了。你把时钟约束从 `create_clock` 开始重写一遍，写完自己先跑 `check_timing`，别再拿半份约束来签核。"

你打开 `sdc/soc_top.sdc`，只有 40 行：两个 `create_clock`、几条 `set_input_delay 0`、一条 `set_false_path`。分频器、MUX、ICG 一个都没提。这一刻你明白：**基础约束只能让设计"跑起来"，高级约束才能让它"算对"。**
:::

## 虚拟时钟：给芯片外的世界一个参照系 {#virtual}

`set_input_delay` 的含义是"数据相对于某个时钟，提前/延后多久到达端口"。问题来了：如果数据来自另一颗芯片，那颗芯片的时钟根本没有接到你的端口上，你拿什么当参照？

很多人图省事写 `set_input_delay 0 -clock clk_core`，意思是"数据与时钟同时到达"。这在物理上几乎不可能：外部器件有输出延迟（Tco），PCB 上有走线延迟，连接器还有延迟。写 0 等于告诉工具"数据来得刚刚好"，工具会把接口路径算得极其乐观，硅片上直接采错。

正确做法是造一个"只在约束文件里存在"的时钟——**虚拟时钟（virtual clock）**：

```tcl
# 作用：为片外器件建一个没有物理对象的参照时钟，并约束输入/输出延迟
# 用法：PT / Innovus 中 source 基础时钟之后执行；vclk 不驱动任何端口
create_clock -name vclk_ext -period 4.000          ;# 250MHz 外部时钟，无对象参数
set_input_delay  -clock vclk_ext -max 1.200 [get_ports data_in*]  ;# 外部 Tco + 板级延迟上限
set_input_delay  -clock vclk_ext -min 0.300 [get_ports data_in*]  ;# 最快到达，供 hold 检查
set_output_delay -clock vclk_ext -max 1.500 [get_ports data_out*] ;# 下游器件的 setup 要求
set_output_delay -clock vclk_ext -min 0.200 [get_ports data_out*] ;# 下游器件的 hold 要求
```

关键点：

1. `create_clock` 后面**没有对象**。这是虚拟时钟唯一的形式特征，工具不会把它当成某个端口的时钟。
2. `-max` 和 `-min` 必须都给。只给 max，hold 检查就没依据；只给 min，setup 检查会当作 0。
3. 虚拟时钟的周期要与外部器件一致。外部是 250MHz，就写 4ns；写成核心时钟的 2ns，接口会被要求跑双倍速度，全是假违例。
4. 输入延迟的数值来自**板级和外部器件的 datasheet**，不是拍脑袋。拿不到就找系统工程师要，或者按最坏情况估并标注假设。

:::fig sdc-virtual-clock | 这张图左边是外部芯片、中间是你的设计、右边是只存在于约束里的虚拟时钟。看中间那条虚线：虚拟时钟没有端口，但它给 input_delay 提供了"相对于谁"的参照。没有它，接口路径的时间起点是空的。
:::

:::term Virtual Clock | 虚拟时钟
用 `create_clock` 定义、但不绑定任何端口或引脚的时钟，只作为 `set_input_delay` / `set_output_delay` 的参照。它描述芯片外部器件的时钟，通常与某个真实端口同频但不同相。
:::

:::pitfall 输入延迟写 0，接口"完美"通过，硅片上全错
现象：DDR 输入接口在 PT 里 slack +0.8ns，流片后第一批芯片读写错误率 30%。

原因：`set_input_delay 0` 假设数据与时钟同时到达端口，实际外部器件 Tco 有 1~2ns、PCB 走线还有几百 ps，数据到得比工具以为的晚得多。工具算出的 +0.8ns 是"假余量"。

怎么查：`report_timing -from [get_ports data_in*]` 看路径起点的时间标注（input delay 那一段）。如果写着 `0.0000`，而接口手册要求 1.2ns，就是漏约束。修法不是改数字糊弄，而是按 datasheet 的 Tco + 板级延迟重新写 `-max/-min`，并让系统工程师签字确认。
:::

## 传播时钟：从"理想"切到"真实" {#propagated}

pre-layout 阶段（placement、CTS 之前），时钟树还不存在。工具默认用 **ideal clock（理想时钟）**：假设时钟从源瞬间到达所有触发器，延迟为 0、skew 为 0。

这个假设在早期是必要的——没有树，算了也是错的。但它不能带到签核：

- ideal clock 下，launch 和 capture 的时钟延迟完全相同，skew 被当成 0。
- 真实时钟树有 0.8~1.5ns 的 insertion delay，叶子之间还有几十到几百 ps 的 skew。
- 不切换，CTS 之后的所有时序报告都是"按零延迟时钟"算的，hold 尤其危险。

CTS 完成后，必须让工具走真实时钟树：

```tcl
# 作用：把指定时钟从理想模式切换为传播模式，让工具计算真实树延迟
# 用法：CTS 之后、post-CTS 优化之前；PT 签核时对所有时钟执行
set_propagated_clock [get_clocks clk_core]   ;# 核心时钟走真实树
set_propagated_clock [get_clocks clk_div2]   ;# 分频时钟也要切，别忘了
report_propagated_clock                      ;# 确认哪些时钟已是 propagated
```

切换时机会带来两个后果：

**切早了**：CTS 还没做，工具找不到时钟树，会报 "no clock tree" 或退回 ideal，等于没切。Innovus 里通常在 `ccopt_design` 之后切；PT 里没有"树"的概念，直接读 SPEF 后对所有时钟 `set_propagated_clock [all_clocks]`。

**切晚了**：CTS 之后还在用 ideal clock 修时序，工具以为 skew 是 0，会把 hold 修得不够，等到签核才发现一片负 slack。这类问题在 03-08 课里叫"hold 违例暴露"，本质就是切换时机不对。

:::term Propagated Clock | 传播时钟
时钟延迟由工具沿真实时钟树逐级计算（包括 buffer、线 RC、skew），而不是假设为 0。与 ideal clock 相对。签核必须用 propagated clock，否则 skew 和 insertion delay 都不进入时序方程。
:::

## 生成时钟：分频、倍频、MUX 之后 {#generated}

一个设计里往往不止一个时钟。分频器、PLL、时钟 MUX 的输出都是"从主时钟派生出来的时钟"，必须用 `create_generated_clock` 告诉工具它和主时钟的关系。不写，那片触发器就是 unconstrained。

### 分频

```tcl
# 作用：定义二分频时钟，源指向分频器的时钟输入引脚
# 用法：读到分频器单元之后执行；-source 必须是上游时钟的引脚，不是输出
create_generated_clock -name clk_div2 \
  -source [get_pins u_div/CP] \
  -divide_by 2 \
  [get_pins u_div/Q]        ;# 目标：分频器的输出引脚
```

`-source` 写错是最高频的错误。它要指向**主时钟经过的那个引脚**（分频器的 CP 端），而不是分频器的输出 Q。写在 Q 上，工具会认为"这个时钟的源就是它自己"，周期和相位都推不出来。

### 倍频

PLL 的输出用 `-multiply_by`：

```tcl
# 作用：定义 PLL 倍频后的时钟
# 用法：PLL 的参考时钟已定义；目标为 PLL 输出引脚
create_generated_clock -name clk_pll \
  -source [get_pins u_pll/REF] \
  -multiply_by 4 \
  [get_pins u_pll/OUT]      ;# 参考 125MHz → 输出 500MHz
```

### 用 -edges 描述非 50% 占空比

有些分频比无法用 `-divide_by` 表达占空比，比如三分频但高电平只占一个周期。这时用 `-edges` 指定"输出波形的第几个边沿对应源时钟的第几个边沿"：

```tcl
# 作用：用边沿列表定义三分频、占空比 1/3 的时钟
# 用法：源时钟边沿编号从 1 开始，1=第一个上升沿，2=第一个下降沿
create_generated_clock -name clk_div3 \
  -source [get_pins u_div3/CP] \
  -edges {1 3 7} \
  [get_pins u_div3/Q]       ;# 上升沿取源第1沿，下降沿取第3沿，下个上升沿取第7沿
```

`-edges {1 3 7}` 读法：输出上升沿对齐源的第 1 个边沿，下降沿对齐第 3 个，下一个上升沿对齐第 7 个（三个源周期后）。这样高电平占 1 个源周期、周期 3 个源周期，占空比 1/3。用之前先在纸上画三列波形，别在命令里试。

### MUX 后面：两个时钟，互斥

时钟 MUX 的输出可能来自 A 也可能来自 B。正确做法是**在输出引脚上定义两个生成时钟**，再用 `set_clock_groups -logically_exclusive` 声明二者不会同时有效：

```tcl
# 作用：为时钟 MUX 的输出定义两条来源，并声明逻辑互斥
# 用法：MUX 的 A/B 输入分别已有主时钟；Z 为输出
create_generated_clock -name clk_mux_a -source [get_pins u_mux/A] \
  -master_clock clk_core [get_pins u_mux/Z]   ;# 路径 A：核心时钟
create_generated_clock -name clk_mux_b -source [get_pins u_mux/B] \
  -master_clock clk_div2 [get_pins u_mux/Z]   ;# 路径 B：分频时钟
set_clock_groups -logically_exclusive \
  -group {clk_mux_a} -group {clk_mux_b}       ;# 同一时刻只有一个有效
```

不写互斥，工具会认为两个时钟同时存在，MUX 后面的路径要同时满足两条时钟的 setup/hold，违例数量翻倍且全是假的。

:::fig cts-multiclock | 这张图画的是主时钟 → 分频 → MUX → 叶子三层关系。重点看 MUX 那一层：它的输出同时挂着两条生成时钟，所以必须配一条 logically_exclusive；否则工具会把两条路径的约束叠加，报出根本不存在的违例。
:::

:::term Generated Clock | 生成时钟
由主时钟经过分频、倍频、门控或 MUX 派生出来的时钟。用 `create_generated_clock` 定义，必须写清 `-source`（从哪来）和变换关系（`-divide_by` / `-multiply_by` / `-edges`）。
:::

:::pitfall 分频时钟忘了定义，一半触发器没有时钟
现象：`check_timing` 报 `unconstrained_endpoints: 4218`，`report_clocks` 里只有 `clk_core` 和 `clk_ddr`，没有 100MHz 域。

原因：分频器输出没有 `create_generated_clock`，那片触发器在工具眼里"没有时钟驱动"，既不查 setup 也不查 hold，等于从时序分析里消失了。

怎么查：先 `report_clocks` 数时钟个数，再 `check_timing -include unconstrained` 找未约束端点，用 `get_cells -of [get_pins .../D]` 反查它们属于哪个时钟域。补生成时钟时确认 `-source` 指向上游引脚，且 `-divide_by` 与分频器实际比例一致。
:::

## 源延迟：时钟进芯片之前的那一段 {#latency}

时钟从哪来？板上晶振 → 芯片时钟 pad → PLL → 时钟树。工具默认认为"时钟在定义点（端口或 PLL 输出）的时刻就是 0"，但 PLL 到 pad、pad 到板上的那段延迟真实存在。

`set_clock_latency -source` 描述的就是**时钟源到时钟定义点**的延迟：

```tcl
# 作用：声明时钟从片外源到定义点的延迟（源延迟）
# 用法：post-layout 也要写；它和时钟树延迟是两段，不能混
set_clock_latency -source 0.800 [get_clocks clk_core]  ;# PLL 到 pad + 板级走线
set_clock_latency -source 0.300 [get_clocks vclk_ext]  ;# 虚拟时钟的源延迟
set_clock_latency 0.500 [get_clocks clk_core]          ;# 网络延迟（ideal clock 时手工给）
```

三件事要分清：

- **源延迟（source latency）**：时钟源 → 定义点，通常是片外 + PLL 内部，工具算不出来，必须手工给。
- **网络延迟（network latency）**：定义点 → 触发器时钟端，就是时钟树的 insertion delay。用 propagated clock 时由工具算；用 ideal clock 时才手工给。
- **不确定度（uncertainty）**：留给 jitter、OCV、时钟树差异的余量，用 `set_clock_uncertainty`，不是延迟。

源延迟给少了，launch 和 capture 的时钟都"到得比实际早"，setup 和 hold 会同时偏乐观；给多了则过度悲观，白留余量。数值来源是 PLL datasheet 和板级仿真，签字前要能说清出处。

:::term Source Latency | 源延迟
从时钟源（晶振、PLL、外部器件）到时钟定义点（端口或 PLL 输出引脚）的延迟。它发生在时钟树之前，工具无法从版图推出，必须由约束给出。
:::

## 时钟门控检查：别在水流着的时候关水龙头 {#cgc}

ICG（Integrated Clock Gating，集成时钟门控）单元长这样：一个锁存器 + 一个与门，用 enable 决定时钟要不要传下去。

```
# 门控单元结构：低电平锁存 enable，再与时钟相与
        ┌─────────┐
CLK ───►│  Latch  │──► EN_latched ──┐
        │ (低电平)│                 │
EN  ───►└─────────┘                 ▼
                                 ┌─────┐
CLK ────────────────────────────►│ AND │──► GCLK
                                 └─────┘
```

危险在于：如果 enable 在时钟高电平期间变化，与门会把一个完整脉冲切成半截。半截脉冲窄到触发器锁不住，下游就随机出错。所以 enable 相对于时钟有 setup/hold 要求，这就是 **clock gating check（时钟门控检查）**。

```tcl
# 作用：为门控单元的 enable 端设置 setup/hold 检查阈值
# 用法：ICG 单元已识别（库里有 clock_gating 属性）后执行
set_clock_gating_check -setup 0.080 -hold 0.040 [get_cells -hier *u_icg*]
set_clock_gating_check -setup 0.080 -hold 0.040   ;# 不带对象：全局默认
report_clock_gating_check                          ;# 列出所有门控检查与违例
```

:::fig sdc-cgc | 这张图把门控单元画成水龙头：enable 必须在"水关着"的时候去拧，流水时拧会切出半截脉冲。看最下面那条错误波形——高电平被切成一小段，这就是 enable 违反 setup 的后果。SDC 不写门控检查，工具不会主动替你查这一类。
:::

关于"不写会不会漏"要说准确：多数库里的 ICG 带 clock gating 属性，工具会**自动**做基本检查；但阈值往往取自库的默认值，或者根本没有覆盖你自定义的门控逻辑。显式写 `set_clock_gating_check` 的作用是：统一阈值、覆盖自定义单元、让检查结果可复现。签核时 `report_clock_gating_check` 必须是 0 违例，或者每条都有 waiver 理由。

修复方向只有两个：让 enable 更早到（把产生 enable 的逻辑提前一拍，或加一级寄存器），或者用 useful skew 把时钟沿挪后。前者是设计改动，后者是 CTS 手段，都不能靠"把阈值调小"解决。

:::term Clock Gating Check | 时钟门控检查
检查 ICG 的 enable 信号相对于时钟的 setup/hold 是否满足，保证 enable 只在时钟低电平期间变化，不会被切出窄脉冲。它是独立于普通 setup/hold 的一类检查。
:::

## 最小脉宽：时钟会被"削窄" {#mpw}

时钟经过一串 buffer，上升沿和下降沿的延迟并不完全相同。高电平持续时间可能从 50% 占空比变成 45%、40%，极端情况下窄到触发器锁存不住。

**最小脉宽检查（min pulse width check）** 就是量这个：时钟的高电平、低电平各自不能短于某个值。

```tcl
# 作用：给时钟设最小高/低电平宽度，并输出检查报告
# 用法：CTS 之后执行；阈值来自触发器库的最小脉宽参数
set_min_pulse_width -low 0.180 -high 0.180 [get_clocks clk_core]  ;# 180ps 下限
report_min_pulse_width -verbose                                     ;# 逐时钟列出最窄脉宽与 slack
```

:::fig wave-pulse | 这张图画的是时钟经过多级缓冲后高电平被削窄的过程。注意右边那个"窄到锁不住"的脉冲——它在 RTL 仿真里几乎看不出来，因为仿真用的是理想时钟；只有 STA 的脉宽检查能拦住。
:::

阈值从哪来？触发器库的 `minimum_pulse_width_high/low` 属性。写大了会过度悲观，写小了等于没查。CTS 阶段如果为了压 skew 插了太多反相器对，占空比失真会累积；这时要么减少级数，要么在树里做占空比修正（duty cycle correction）。

:::term Min Pulse Width | 最小脉宽
时钟高电平或低电平允许的最短持续时间。短于触发器要求时，触发器可能进入亚稳态。由工艺库给出阈值，由 STA 沿时钟树逐级检查。
:::

## 保持时钟干净：两条纪律 {#clean}

高级约束写得再全，两条纪律破了也白搭。

**第一，不要用时钟做数据逻辑。** 比如 `assign enable = clk & ready;` 或者把时钟接到触发器的 D 端。工具会把这条路径当时钟路径分析，插入巨大的 skew 预算，甚至把数据网络误认成时钟树。功能上也许能工作，但时序无法收敛，测试也测不了。

**第二，不要随意 `set_case_analysis` 时钟。** 为了让 MUX 选某一路而写 `set_case_analysis 1 [get_pins u_mux/S]`，等于告诉工具"另一条时钟永远不存在"。如果这个值是模式相关的（测试模式、低功耗模式），你会把另一种模式下的路径全部屏蔽掉，签核报告看起来干净，实际芯片在另一个模式下失效。

正确做法：用 `set_clock_groups -logically_exclusive` 或 `-physically_exclusive` 描述互斥关系，让工具知道"两种模式都存在，但不同时"；模式选择用 `set_case_analysis` 时，必须为每个模式单独出一份报告。

还有一条容易被忽略：**不要把 `set_false_path` 当成万能补丁**。跨时钟域路径如果真是异步，用 `set_clock_groups -asynchronous` 一次声明两个时钟组，比逐条写 `set_false_path` 更不容易漏；如果两个时钟其实同源、只是相位不同，写 false path 会把真实需要检查的路径也一起放过。判据是看两个时钟能不能追到同一个源：同源就不能随便 false。

## 一份完整的高级约束文件 {#full}

下面这份文件可以直接当模板。分七节，每节只干一件事；顺序不能乱——后面的约束依赖前面的时钟定义。

```tcl
# 作用：SoC 高级时钟约束模板（PT / Innovus 通用语法）
# 用法：在 05-02 的基础约束之后 source；本文件只补高级部分

# ---- 1. 基础时钟：周期与波形 ----
create_clock -name clk_core -period 2.000 [get_ports clk]      ;# 500MHz 核心
create_clock -name clk_ddr  -period 1.250 [get_ports clk_ddr]  ;# 800MHz DDR 参考

# ---- 2. 虚拟时钟：给片外接口做参照 ----
create_clock -name vclk_ext -period 4.000                       ;# 250MHz，无对象
set_input_delay  -clock vclk_ext -max 1.200 [get_ports data_in*]   ;# 外部 Tco + 板级
set_input_delay  -clock vclk_ext -min 0.300 [get_ports data_in*]
set_output_delay -clock vclk_ext -max 1.500 [get_ports data_out*]
set_output_delay -clock vclk_ext -min 0.200 [get_ports data_out*]

# ---- 3. 生成时钟：分频 / 倍频 / MUX ----
create_generated_clock -name clk_div2 -source [get_pins u_div/CP] \
  -divide_by 2 [get_pins u_div/Q]                               ;# 250MHz 低速域
create_generated_clock -name clk_pll -source [get_pins u_pll/REF] \
  -multiply_by 4 [get_pins u_pll/OUT]                           ;# PLL 倍频输出
create_generated_clock -name clk_mux_a -source [get_pins u_mux/A] \
  -master_clock clk_core [get_pins u_mux/Z]                     ;# MUX 路径 A
create_generated_clock -name clk_mux_b -source [get_pins u_mux/B] \
  -master_clock clk_div2 [get_pins u_mux/Z]                     ;# MUX 路径 B
set_clock_groups -logically_exclusive -group {clk_mux_a} -group {clk_mux_b}

# ---- 4. 传播时钟与源延迟 ----
set_propagated_clock [get_clocks clk_core]                      ;# CTS 后走真实树
set_propagated_clock [get_clocks clk_div2]
set_clock_latency -source 0.800 [get_clocks clk_core]           ;# PLL → pad → 板级
set_clock_uncertainty -setup 0.120 [get_clocks clk_core]        ;# OCV + jitter 余量
set_clock_uncertainty -hold  0.080 [get_clocks clk_core]

# ---- 5. 门控检查 ----
set_clock_gating_check -setup 0.080 -hold 0.040                 ;# 全局 ICG 阈值

# ---- 6. 最小脉宽 ----
set_min_pulse_width -low 0.180 -high 0.180 [get_clocks clk_core]

# ---- 7. 例外：每条都要写理由 ----
set_false_path -from [get_ports test_mode]                      ;# 测试引脚静态
set_clock_groups -asynchronous -group {clk_core clk_div2} -group {vclk_ext}
```

逐节解释几个容易写错的：

- 第 2 节：`vclk_ext` 的周期 4ns 与外部器件一致，和核心 2ns 无关。写成 2ns 会让接口被要求 500MHz。
- 第 3 节：`clk_mux_a/b` 都定义在 `u_mux/Z` 上，靠 `-master_clock` 区分来源；没有这两条，MUX 后面没有时钟。
- 第 4 节：`set_propagated_clock` 只对列出的时钟生效。只写 `clk_core`，`clk_div2` 还是 ideal，那片时序仍然是假的。
- 第 5 节：不带对象时是全局默认，适合统一阈值；有特殊 ICG 再单独覆盖。
- 第 6 节：`-low` 和 `-high` 要分别给。只给一个，另一个方向按 0 处理，等于放行了一半的窄脉冲。
- 第 7 节：例外放最后，因为 `set_false_path` 会覆盖前面的检查。先写例外再写时钟，容易被后面的约束"救回来"，顺序反了反而不易发现。

这份文件的长度是 40 行左右，但真正需要人判断的只有十几个数字：外部周期、Tco、分频比、源延迟、门控阈值、脉宽下限。**数字的出处比语法重要**——语法错了工具会报错，数字错了工具一声不吭。

## 写完的自检：四条命令，四个判据 {#selfcheck}

约束不是"写完就交"，要能自己证明它是对的。按顺序跑：

```tcl
# 作用：高级时钟约束的四步自检，全部通过才可交付
# 用法：source 完 SDC 后依次执行，输出重定向到 rpt/ 存证
report_clocks > rpt/clocks.rpt                    ;# ① 时钟清单与波形
check_timing -verbose > rpt/check_timing.rpt      ;# ② 未约束/无时钟/无延迟
report_clock_gating_check > rpt/cgc.rpt           ;# ③ 门控检查
report_min_pulse_width -verbose > rpt/mpw.rpt     ;# ④ 最小脉宽
```

| 命令 | 看什么 | 判据 |
|---|---|---|
| `report_clocks` | 每个时钟的周期、波形、源 | 时钟数与设计一致；生成时钟的 source 指向正确；没有重复定义 |
| `check_timing` | `unconstrained_endpoints`、`no_clock`、`no_input_delay` | 三个数都为 0；`no_input_delay` 非 0 说明有端口没约束 |
| `report_clock_gating_check` | 每条 ICG 的 setup/hold slack | 违例为 0，或有逐条 waiver 与设计确认 |
| `report_min_pulse_width` | 高/低脉宽最差值 | slack ≥ 0；负值要查时钟树级数与占空比 |

再加一条针对接口的抽查：`report_timing -from [get_ports data_in*] -max_paths 5`，看报告里 input delay 那一段是不是你写的 1.2ns，而不是 0。

四条命令里，`check_timing` 最容易"看漏"。它默认会列出一长串检查项，人眼很难逐条读；用 `-include` 只看你关心的几项（如 `unconstrained`、`no_clock`、`no_input_delay`），输出会短很多，也不容易漏。不同版本支持的检查项名略有差异，跑之前先 `check_timing -help` 看一眼。另一个常见误判是 `report_clock_gating_check` 显示 0 违例，其实是因为 ICG 没被识别成门控单元——这时报告里根本不会出现那些单元。判断方法是拿单元清单反查：`get_cells -hier *icg*` 的数量应与报告里的门控检查条数同量级，少了就是没识别。

## 工作中怎么用：约束是签核的合同 {#in-work}

**谁写**：SDC 通常由 STA 工程师主笔，PR 工程师提供时钟树信息（insertion delay、skew），系统工程师提供接口时序（Tco、板级延迟）。三方签字后冻结版本。

**什么时候写**：每个阶段都有一版——综合前是"预估版"，CTS 后加 propagated 和真实 latency，signoff 前冻结。**版本必须带日期和 commit**，PT 报告里要能追到用的是哪一版。

**交付什么**：一份 `soc_top.sdc`、一份 `clocks.rpt` 自检输出、一张"约束变更记录"（这次改了哪几条、为什么、谁确认）。变更记录比 SDC 本身更重要——三个月后出问题，靠它定位。

**评审会看什么**：`check_timing` 是否为 0、生成时钟是否覆盖所有派生时钟、门控检查违例是否有解释、接口延迟数值的出处。任何一条说不清出处，都要回去补依据。

**写错了会怎样**：漏一条生成时钟，那片逻辑等于没签核；虚拟时钟写错周期，接口假收敛；门控检查没写，硅片上随机切脉冲，这种故障在实验室复现极难，可能要几周。约束错误不会让工具报错，只会让报告"看起来很好"——这是它最危险的地方。

:::lab 动手：给一个漏约束的设计补三条时钟约束
**任务**：`~/backend_lab/soc/sdc/broken.sdc` 是一份只有基础约束的文件。设计里有：二分频器 `u_div`、时钟 MUX `u_mux`（A 接核心、B 接分频）、外部接口 `data_in[7:0]`（外部 250MHz）。补全后自检。

**步骤**：
1. `report_clocks` 记下当前只有哪些时钟，标出缺失的。
2. 补 `create_generated_clock` 两条（分频、MUX 两路）和虚拟时钟一条，`-source` 逐个确认指向上游引脚。
3. 写 `set_input_delay` 的 max/min（按 1.2ns / 0.3ns），并加 `set_clock_groups -logically_exclusive`。
4. 跑 `check_timing -verbose`，把 `unconstrained_endpoints`、`no_clock`、`no_input_delay` 三个数记下来。

**过关标准**：三个数全部为 0；`report_clocks` 里能看到 5 个以上时钟且每个都有周期；能指着 MUX 的两条生成时钟说清"为什么必须互斥"。
:::

:::quiz
虚拟时钟和普通时钟的区别是什么？|虚拟时钟用 create_clock 定义但不绑定任何端口/引脚，只作为 input/output delay 的参照；普通时钟必须定义在端口或引脚上。
为什么 input_delay 不能写 0？|写 0 等于假设外部数据与时钟同时到达，忽略了外部器件 Tco 和板级延迟，接口时序会被算得过于乐观。
ideal clock 和 propagated clock 的区别，什么时候切换？|ideal 假设时钟零延迟、零 skew，用于 pre-layout；propagated 沿真实时钟树计算延迟，CTS 之后（PT 签核时）必须切换。
create_generated_clock 的 -source 应该指向哪里？|指向上游主时钟经过的引脚（如分频器的 CP 端），不是生成时钟自己的输出引脚。
时钟 MUX 的输出为什么要定义两条生成时钟并声明互斥？|输出可能来自两个不同频率的时钟；不声明互斥，工具会同时按两条时钟检查，产生大量假违例。
set_clock_latency -source 描述的是哪一段延迟？|时钟源（PLL/晶振/片外）到时钟定义点之间的延迟；它发生在时钟树之前，工具无法从版图推出。
不写 set_clock_gating_check 会怎样？|ICG 的 enable 可能没有按项目阈值检查，或只用库默认值，导致切脉冲类违例被漏掉；显式写能统一阈值并覆盖自定义单元。
最小脉宽检查为什么要做？|时钟经过多级缓冲后高低电平会被削窄，窄到触发器锁不住时芯片随机出错，RTL 仿真看不出来，只能靠 STA 检查。
:::

:::check
- 能说出五个必须用高级约束的场景，并把它们和六条约束一一对应
- 能写对虚拟时钟的三要素：无对象、周期与外部一致、max/min 都给
- 能解释 ideal→propagated 的切换时机，以及切早/切晚各自的后果
- 能写分频、倍频、MUX 三种生成时钟，并说清 -source 指向哪里
- 能解释门控检查和最小脉宽各防的是什么故障
- 能用 report_clocks / check_timing / report_clock_gating_check / report_min_pulse_width 四条命令自检并给出判据
:::
