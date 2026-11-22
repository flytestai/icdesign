---
id: 03-06-setup-hold
no: 17
stage: 3
title: setup 与 hold：用"拍照"讲明白时序
en: Setup & Hold
hours: 6
minutes: 55
tags: [时序, setup, hold, skew]
summary: 这是后端最核心的两个概念，也是最容易被讲糊涂的。这一课用拍照、接力赛两个比喻，配合公式和手算例子，让你第一次真正搞懂 setup/hold 在算什么。
---

## 触发器就是一台照相机 {#camera}

数字电路里，绝大多数数据都在**触发器（Flip-Flop）**之间传递。触发器的工作方式像一台定时拍照的相机：

```
        ┌─────────┐
数据 D ─▶│         │
        │  触发器  │──▶ 输出 Q
时钟 ──▶│         │
        └─────────┘
        ↑
     时钟上升沿 = 按下快门
```

**快门按下的那一瞬间，D 端的数据必须已经稳定，并且之后还要保持一小会儿稳定**，拍出来的照片才不是糊的。

这两个"稳定窗口"就是 setup 和 hold：

| 名称 | 中文 | 要求 | 物理含义 |
|---|---|---|---|
| Setup | 建立时间 | 数据必须在时钟沿**之前** T_setup 就稳定 | 相机需要预热对焦 |
| Hold | 保持时间 | 数据必须在时钟沿**之后** T_hold 内保持稳定 | 快门关闭前别动 |

:::term Setup Time | 建立时间
时钟沿到来之前，数据必须已经稳定的最短时间。不满足叫 **setup violation**，俗称"setup 违例"。

后果：数据没来得及传到，触发器抓到了旧值 → 功能错。
:::

:::term Hold Time | 保持时间
时钟沿到来之后，数据必须继续保持稳定的最短时间。不满足叫 **hold violation**。

后果：新数据来得太早，把本该抓的旧值冲掉了 → 功能错。
:::

## setup 在算什么 {#setup}

一条路径从"发射触发器"到"接收触发器"，中间要经过组合逻辑（与门、加法器……）。

```
      ┌────┐        ┌──────────┐        ┌────┐
CLK ─▶│ FF │──Q────▶│ 组合逻辑  │───────▶│ FF │◀─ CLK
      │ A  │        │  (延迟 T) │        │ B  │
      └────┘        └──────────┘        └────┘
```

数据从 A 出发，要在**下一个时钟沿之前**赶到 B，并且提前 T_setup 站稳。

```
要求：T_clk_period ≥ T_launch_clk + T_logic + T_setup - T_capture_clk
整理：T_clk_period ≥ T_logic + T_setup + (T_launch_clk - T_capture_clk)
                                    └────── skew ──────┘
```

用大白话：**一个时钟周期里，数据要跑完组合逻辑、还要提前站稳。**

所以：

- 逻辑越复杂（T_logic 大）→ 越容易 setup 违例 → 需要降频或拆分逻辑。
- 频率越高（周期越短）→ 越容易 setup 违例。

:::term Slack | 裕量
实际时间 − 需要时间。正数表示有余量，负数表示违例。

`slack = T_period − (T_logic + T_setup + skew)`

- slack = +0.2ns：还有 0.2ns 余量，安全。
- slack = −0.15ns：差 0.15ns，必须修。

**报时序报告时，大家看的就是这个数。**
:::

## hold 在算什么 {#hold}

同一个时钟沿，数据从 A 出发，**不能太快**到达 B——因为 B 还在抓上一个值，新数据太早到会把它冲掉。

```
要求：T_launch_clk + T_logic ≥ T_capture_clk + T_hold
整理：T_logic ≥ T_hold + (T_capture_clk - T_launch_clk)
```

用大白话：**数据不能跑太快，得等接收端把当前值抓稳。**

:::pitfall 为什么 hold 违例和频率无关
这是新手最容易搞混的一点。

看公式：`T_logic ≥ T_hold + skew`。里面**没有 T_clk_period**。

所以：

- 降频能救 setup（周期变长），**救不了 hold**。
- hold 违例只能靠加延迟（插 buffer）或调 skew 来修。

面试高频题："hold 违例能靠降频解决吗？" 答案：不能。
:::

## 手算一个例子 {#example}

条件：

- 时钟周期 2.0ns（500MHz）
- 组合逻辑延迟 1.6ns
- 触发器 T_setup = 0.15ns，T_hold = 0.08ns
- 时钟 skew = 0.10ns（接收端晚到 0.10ns，对 setup 不利）
- 线延迟忽略

setup 检查：

```
slack = 2.0 − (1.6 + 0.15 + 0.10) = 2.0 − 1.85 = +0.15ns  ✅ 通过
```

hold 检查（假设最短路径延迟 0.20ns）：

```
slack = 0.20 − (0.08 + 0.10) = 0.20 − 0.18 = +0.02ns  ✅ 勉强通过
```

如果把频率提到 800MHz（周期 1.25ns）：

```
setup slack = 1.25 − 1.85 = −0.60ns  ❌ 严重违例
hold slack  = +0.02ns                ✅ 不变
```

**这就是"降频救 setup、救不了 hold"的数值证明。**

:::term Skew | 时钟偏斜（重要）
同一个时钟到达两个触发器的时间差。

- **正 skew**（接收端晚到）：对 setup 有利（多给时间），对 hold 不利。
- **负 skew**（接收端早到）：对 setup 不利，对 hold 有利。

CTS 的目标不是"skew = 0"，而是"把 skew 控制在可控范围内，并留给紧张的路径一点余地"。
:::

:::scene 为什么后端工程师天天盯着 slack
流片前 review，投影上就是一页 slack 表：

```
Path Group   WNS      TNS    Violating Paths
clk_core     -0.02    0.00   1
clk_ddr      +0.31    0.00   0
```

WNS（Worst Negative Slack）= 最差那条的 slack。只要 WNS 是负的，就不能签核。

组长只问一句："WNS 为什么是负的？哪条路径？" 你要能立刻答出来。
:::

:::lab 动手：自己写一个时序计算器
```bash
python3 - <<'EOF'
def check(period, t_logic, t_setup, t_hold, skew, t_logic_min):
    setup = period - (t_logic + t_setup + skew)
    hold  = t_logic_min - (t_hold + skew)
    print(f"周期 {period}ns  逻辑 {t_logic}ns  skew {skew}ns")
    print(f"  setup slack = {setup:+.3f}ns  {'PASS' if setup>=0 else 'FAIL'}")
    print(f"  hold  slack = {hold:+.3f}ns  {'PASS' if hold>=0 else 'FAIL'}")

check(2.0, 1.6, 0.15, 0.08, 0.10, 0.20)   # 500MHz
check(1.25, 1.6, 0.15, 0.08, 0.10, 0.20)  # 800MHz
check(2.0, 1.6, 0.15, 0.08, -0.10, 0.20)  # skew 改成负的
EOF
```

预期：第一组两个都 PASS；第二组 setup FAIL、hold 仍 PASS；第三组 setup 更容易过、hold 变差。

过关标准：能解释第三组为什么 setup 变好、hold 变差（提示：负 skew 让接收端早到）。
:::

:::check
- 能用拍照比喻讲清 setup 和 hold
- 记得两条公式，并且知道 skew 符号怎么影响
- 能证明"降频救不了 hold"
- 知道 slack 的含义和 WNS 是什么
- 能手算一条路径的 slack
:::

:::quiz
setup 和 hold 分别检查什么？|setup 检查数据是否在时钟沿前足够早稳定；hold 检查数据在时钟沿后是否保持足够久。
为什么降频不能修 hold？|hold 公式里没有时钟周期，只和逻辑延迟、T_hold、skew 有关。
正 skew 对 setup 和 hold 分别有什么影响？|对 setup 有利（接收端晚到，等于多给时间），对 hold 不利（数据更容易冲掉旧值）。
WNS 是什么？|Worst Negative Slack，所有违例路径中最差的那个 slack 值，是签核的关键指标。
一条路径 setup slack = −0.08ns，有哪几种修法？|减小逻辑延迟（拆逻辑/换快单元）、增大驱动（upsize）、缩短线长（挪位置）、调 skew（useful skew）、降频（最后手段）。
:::
