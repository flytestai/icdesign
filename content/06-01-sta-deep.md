---
id: 06-01-sta-deep
no: 31
stage: 6
title: STA 深水区：时钟组、跨时钟域与悲观度
en: Advanced STA
hours: 6
minutes: 50
tags: [STA, CDC, OCV, 约束]
summary: 会算 setup/hold 只是入门。真实项目里最难的是"哪些路径该查、该怎么查"——时钟组、跨时钟域、多周期、false path，以及签核时该有多悲观。
---

## 一、时钟组：异步时钟之间不该比 {#groups}

芯片里通常有多个时钟：core clk、ddr clk、apb clk。它们频率不同、相位无关（异步）。

如果工具把异步时钟之间的路径也按时序检查，会报出大量"永远修不好"的违例——因为它们本来就不该比。

```tcl
# 把两组时钟设为异步（互不检查）
set_clock_groups -asynchronous \
    -group {clk_core} \
    -group {clk_ddr}

# 或者按名字批量设
set_clock_groups -asynchronous \
    -group [get_clocks clk_core*] \
    -group [get_clocks clk_ddr*]
```

:::term Clock Group | 时钟组
告诉工具"这几组时钟之间是异步的，不要互相做时序检查"。

**这是 SDC 里最容易被漏掉、也最容易造成假违例的一条约束。**
:::

:::pitfall 忘了设 clock group，报告里一堆"不可能修好"的违例
现象：`report_timing` 里最差路径总是跨在 `clk_core` 和 `clk_ddr` 之间，slack −3ns，怎么优化都不动。

原因：两个异步时钟被当成同步检查了。

处理：先确认这两个时钟确实异步（看设计规格/前端确认），再设 `set_clock_groups -asynchronous`。

**注意：设成异步不等于"没问题"** —— 异步时钟域之间需要 CDC（跨时钟域）电路保证安全，这是设计问题，不是时序问题。
:::

:::term CDC | 跨时钟域
Clock Domain Crossing。信号从一个时钟域传到另一个时钟域。

后端不做 CDC 设计，但要看懂：单比特信号用两级同步器，多比特用异步 FIFO 或握手。**如果前端没做，后端怎么优化都没用。**
:::

## 二、false path 与 multicycle：该松的松，该紧的紧 {#exceptions}

| 约束 | 含义 | 典型场景 |
|---|---|---|
| `set_false_path` | 完全不检查 | 复位、测试逻辑、异步时钟域之间（配合 CDC 电路） |
| `set_multicycle_path` | 允许多个周期完成 | 慢速模块、使能信号控制的路径 |
| `set_max_delay` | 直接指定最大延迟 | 组合逻辑跨模块、异步接口 |

```tcl
# 多周期：2 个周期完成，hold 检查要退回到第 1 个周期
set_multicycle_path 2 -setup -from [get_cells u_slow/*] -to [get_cells u_slow/*]
set_multicycle_path 1 -hold  -from [get_cells u_slow/*] -to [get_cells u_slow/*]
# ↑ 只设 setup 不设 hold 是常见错误：hold 会检查错周期
```

:::pitfall multicycle 只设了 setup
`set_multicycle_path 2 -setup` 之后，hold 检查仍然按原周期算，但工具会以为 setup 检查点后移了一个周期，导致 **hold 检查点位置错了**。

正确做法：setup 设 N，hold 就设 N−1。
:::

## 三、悲观度：签核要多保守 {#pessimism}

| 层次 | 做法 | 什么时候用 |
|---|---|---|
| 无 OCV | 所有单元用标称延迟 | 早期探索，不能签核 |
| OCV（统一 derate） | 全部 ×1.05 / ×0.95 | 成熟工艺、快速评估 |
| AOCV | 按逻辑深度给不同 derate | 28nm~16nm 常用 |
| POCV / LVF | 按统计分布（均值+方差） | 16nm 以下必须 |

```tcl
# AOCV 示例
read_aocvm ./aocv/tsmc28.aocvm
set_timing_derate -early 0.97 -late 1.03
```

:::term AOCV | 先进 OCV
Advanced OCV。核心洞察：**路径越长，相对偏差越小**（统计平均效应）。

所以深逻辑路径的 derate 可以小一点，浅逻辑路径要大一点——比统一 derate 更准，也没那么悲观。
:::

:::scene 悲观度怎么影响项目
同一版设计，用三种模式跑 PT：

| 模式 | setup WNS | 结论 |
|---|---|---|
| 无 OCV | +0.35ns | 看起来很好 |
| OCV 5% | −0.12ns | 要修 |
| AOCV | +0.08ns | 可签核 |

**同一版设计，三种结论。** 所以签核前必须和团队确认"用哪种模式、derate 多少"，否则各说各话。
:::

## 四、时序预算：把周期分给谁 {#budget}

一个时钟周期里，时间要分给：

```
T_period = T_launch_clk + T_logic + T_setup + T_skew + margin
```

实际项目里常用"预算表"管理：

| 项目 | 预算 | 说明 |
|---|---|---|
| 组合逻辑 | 60% | 主要开销 |
| 时钟 skew | 8% | CTS 目标 |
| setup | 7% | 库参数 |
| 余量（margin） | 25% | 给布线绕线、OCV 留的缓冲 |

:::tip margin 为什么留 25%
因为**布线前是估算、布线后会变差**。我们实测中，理想互连 WNS +0.628ns，带真实 SPEF 后 +0.9955ns（这个案例里反而变好，因为线负载轻）。

但一般经验是：布线后比布线前差 10%~20%。所以前期必须留够余量。
:::

:::check
- 会用 `set_clock_groups -asynchronous` 处理异步时钟
- 知道 multicycle 要成对设 setup 和 hold
- 能说出 OCV / AOCV / POCV 的区别和适用节点
- 理解时序预算的构成，知道为什么要留 margin
- 明白"设成异步"不等于"CDC 安全"
:::

:::quiz
`set_clock_groups -asynchronous` 解决什么问题？|告诉工具两组时钟互不检查，避免异步时钟之间报出永远修不好的假违例。
`set_multicycle_path 2 -setup` 之后 hold 该怎么设？|`set_multicycle_path 1 -hold`（N−1），否则 hold 检查点会错位。
AOCV 相比 OCV 的核心改进是什么？|按逻辑深度分级 derate：路径越长相对偏差越小，比统一 derate 更准也更不悲观。
为什么时序预算要留 20%~25% 余量？|布线后真实线延迟通常比估算差 10%~20%，还要覆盖 OCV 和优化波动。
把异步时钟设成 false path 之后就安全了吗？|不是。异步域之间还需要 CDC 电路（同步器/异步 FIFO）保证功能正确，这是设计问题。
:::
