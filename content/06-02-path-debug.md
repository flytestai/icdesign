---
id: 06-02-path-debug
no: 32
stage: 6
title: 时序路径调试：从 WNS 数字走到那一个单元
en: Debugging a Timing Path
hours: 3
minutes: 38
tags: [STA, 路径分析, report_timing, 假违例, 时序预算]
summary: 报告上写着 WNS -0.35ns，然后呢？这一课把一条路径拆成五个时间点，给出五步定位法、四类"假违例"的识别方法，以及"该修还是该 waive"的判断标准。
---

## 为什么报告看不懂 {#why}

`report_timing` 的输出有几十行，新人往往从头读到尾，读完还是不知道问题在哪。

原因只有一个：**不知道工具在算什么式子。**

工具只算一个减法：

```text
slack = 要求时间（required） - 到达时间（arrival）
```

- **arrival**：数据从起点出发，经过一路上所有门和线，到达终点花了多久；
- **required**：数据最晚必须在什么时候到（由时钟周期减去捕获端的建立时间等推出来）；
- 两个一减，负的就是违例。

所以看报告只需要找两件事：**哪个环节吃掉了时间**、**能不能少花一点**。

:::term Slack | 余量
`slack = required - arrival`。正数表示还有富余，负数表示来不及。

WNS（Worst Negative Slack）= 所有违例里最差的那个负数，是"这个设计有多糟"的唯一指标。TNS（Total Negative Slack）= 所有负 slack 之和，是"总共欠多少"。
:::

## 一条路径的五个时间点 {#anatomy}

```text
launch 时钟沿                数据出发                 数据到达         捕获时钟沿
     |                          |                        |                 |
     t0 ──── 时钟树延迟 ──► t1 ── 组合逻辑 ──► t2 ── 建立时间 ──► t3 = t0+T-skew
                                    ↑
                              这一段的延迟就是你要抢的时间
```

| 时间点 | 名字 | 报告里的行 |
|---|---|---|
| t0 | 时钟源（clock source） | `clock clk (rise edge) 0.00` |
| t1 | launch 触发器时钟引脚 | `u_a/reg_a[3]/CK` |
| t2 | 数据到终点 D 引脚 | `u_b/reg_b[3]/D` |
| t3 | 要求到达时间 | `data required time` |
| — | 到达时间 | `data arrival time` |

报告里真正的信息量在**中间那几十行**：每一个门的延迟、每一段线的延迟。**找到最贵的那一行，就是找到修的方向。**

## 五步定位法 {#five}

不要一上来就改。按这五步走，10 分钟定位，比瞎试两小时强。

**第 1 步：确认这条违例是真的**

```tcl
report_timing -delay_type max -max_paths 1 -path_type full_clock_expanded
```

看三样东西：

- Startpoint / Endpoint 是不是**真的在同一个时钟域**；
- 时钟是不是**你定义的那个**（不是默认的虚拟时钟）；
- 路径上有没有 `false path` 标记（有标记的违例不计入 WNS）。

**第 2 步：找最贵的一段**

```tcl
report_timing -max_paths 1 -sort_by slack -fields {slack arrival required}
# 重点看哪一行 Incr 最大：一个门的延迟 0.3ns 就很可疑（一般是 0.03~0.1）
```

**第 3 步：判断是哪一类问题**

| 现象 | 判断 | 下一步 |
|---|---|---|
| 某一行 Incr 特别大（> 0.3ns） | 驱动不足 / 负载太大 | 看这一级的 fanout |
| 逻辑级数 > 30 | 结构问题（组合逻辑太深） | 找设计者改 RTL，或加 pipeline |
| 线延迟占比 > 50% | 布局太远 / 拥塞绕线 | 加约束把它拉近，或改 floorplan |
| 时钟树延迟差 > 0.3ns | skew 大 | 回 CTS 阶段（见 OptCts 课） |

**第 4 步：算一次"至少要多快"**

```text
假设周期 2.0ns，现在 slack -0.35ns
需要省出 0.35ns
可行手段：换驱动（省 0.10）+ 挪近（省 0.15）+ 减一级逻辑（省 0.12）= 0.37 ✅
不可能：只靠换驱动省 0.35（一个门最多省 0.1）
```

**第 5 步：改一处，重跑，只改一处**

改三个地方一起跑，你永远不知道哪个起了作用。**一次只改一处，记录数据**。

:::pitfall 一次改五个参数
新人看到违例，同时改利用率、max_density、buffer 列表、skew 目标、SDC 时钟不确定性，然后重跑。

结果：变好了，但不知道为什么好；下次换个设计，同样的参数组合失效了。

**一次只改一个变量**，是调试的唯一纪律。
:::

## 四类"假违例"：不是设计的问题，是约束的问题 {#fake}

签核时最常见的浪费：花两天修一堆根本不是问题的违例。

| 类型 | 症状 | 怎么确认 | 怎么处理 |
|---|---|---|---|
| 假路径 | 异步复位、跨时钟域、测试逻辑被报违例 | 路径起点终点时钟不同源 | `set_false_path` |
| 多周期 | 逻辑本身允许多个周期算完（如乘法器） | 设计者确认功能允许 | `set_multicycle_path` |
| 未约束 | 路径完全没出现在报告里（被忽略） | `report_timing -unconstrained` | 补 input/output delay |
| 时钟定义错 | 时钟周期写成实际的一半/两倍 | `report_clocks` 看周期 | 改 SDC |

:::term False Path | 假路径
物理上存在连接，但功能上永远不会有信号通过（或者不需要在这个时钟周期内通过）。告诉工具"别检查它"，可以省下大量无意义的违例。

**风险**：`set_false_path` 写错会把真违例藏起来。所以每一条 false path 都要有人签字确认，不能"先设上再说"。
:::

```tcl
# 典型的四类约束写法
set_false_path -from [get_ports rst_n]                      ;# 异步复位
set_false_path -from [get_clocks clk_a] -to [get_clocks clk_b]  ;# 跨时钟域（同步器已处理）
set_multicycle_path 2 -setup -from [get_cells u_mul/*] -to [get_cells u_acc/*]
set_clock_uncertainty 0.05 [get_clocks clk]                 ;# 抖动预算
```

## 六种过滤，把范围缩小到一条路径 {#filter}

```tcl
# 1) 只看最差的 10 条
report_timing -max_paths 10

# 2) 只看经过某个单元的路径
report_timing -through [get_pins u_core/u_alu/U2317/Z]

# 3) 只看从某个寄存器出发的
report_timing -from [get_cells u_core/reg_a_reg[3]]

# 4) 只看到达某个寄存器的
report_timing -to [get_cells u_core/reg_b_reg[3]]

# 5) 只看某个时钟域的
report_timing -group clk_500m

# 6) 按 slack 排序，只看负的
report_timing -slack_lesser_than 0 -max_paths 50
```

:::tip `-through` 是定位神器
当你怀疑"是不是某个单元特别慢"，用 `-through` 一查就知道它出现在多少条关键路径上。

出现在 200 条违例路径里的单元，换掉它比修 200 条路径划算得多。
:::

## 逻辑级数与时序预算：手算一次就懂 {#budget}

2ns 周期（500MHz）下，一个触发器到下一个触发器之间能放多少级逻辑？

```text
周期                    2.000 ns
- 时钟不确定性          -0.050
- 触发器 setup 时间      -0.080
- 触发器 clk->q 延迟     -0.110
- 时钟 skew             -0.100
- 布线余量（估）        -0.300
────────────────────────────────
= 留给组合逻辑          1.360 ns

如果一级 NAND2 平均 0.045ns：1.360 / 0.045 ≈ 30 级
实际留 20% 余量：约 24 级
```

这就是为什么"逻辑级数超过 30 基本必违例"。这个数不是玄学，是算出来的。

:::note 我们的实测：+1.00ns 是怎么来的
万门设计在 ICC2 里 `place_opt` 之后 setup WNS +1.00ns（周期 2ns，也就是用了 50% 的时间预算）。

这不是"工具很强"，而是**布局阶段插了 2636 个 buffer 换来的**：单元数从 9390 涨到 12026，面积从 270×270 缩到 222×222（因为时序驱动会把逻辑拉近）。

**代价要看清**：省下来的面积换成了 buffer 的面积和功耗；WNS 好看，但 dynamic power 上去了。真实项目里这两个要一起权衡。
:::

## 该修还是该 waive：一个判断表 {#decide}

不是所有违例都值得修。按这个顺序判断：

| 情况 | 处理 | 理由 |
|---|---|---|
| hold 违例 | **必须修** | 跟频率无关，降频也救不了，硅片上一定出错 |
| setup 违例且路径真实 | 修 | 影响良率与最高频率 |
| setup 违例在 false path 上 | waive（加约束） | 功能上不会发生 |
| 违例 < 周期的 1%（20ps 级） | 可 waive（记录在案） | 在工艺波动范围内，修的成本高于收益 |
| 测试/DFT 逻辑违例 | 通常 waive | 测试模式频率低 |
| 违例在 spare cell 上 | waive | 备用单元不参与功能 |

:::pitfall waive 不写记录
"这条我们 waive 了"——三个月后没人记得为什么 waive。签核报告里出现一条违例，审核的人会一路追到底。

**规矩**：每条 waive 都要写进签核报告的 waiver 表，包含路径名、slack、原因、批准人。
:::

:::lab 动手：读一份真实的 timing 报告并手算
模拟终端里有一份完整的路径报告：

```bash
cd ~/backend_lab/soc/pnr/reports
cat timing.rpt
```

报告里关键几行：

```text
  u_core/u_alu/reg_a[3]/Q              0.11       0.11
  u_core/u_alu/U12/ZN                  0.04       0.15
  u_core/u_alu/U57/ZN                  0.06       0.21
  u_core/u_alu/U88/Z                   0.09       0.30
  ...
  data arrival time                               0.32
  data required time                              1.90
  slack (MET)                                     1.58
```

手算验证：

```text
arrival  = 0.11 + 0.04 + 0.06 + 0.09 + 0.02 = 0.32   ✅ 与报告一致
required = 2.00（周期）- 0.05（uncertainty）- 0.05（setup）= 1.90  ✅
slack    = 1.90 - 0.32 = 1.58  ✅
```

再用命令抽数：

```bash
grep -E "slack|data (arrival|required)" timing.rpt
awk '/data arrival time/ {print "arrival =", $4}' timing.rpt
```

过关标准：能拿任意一份 report_timing，手算出 arrival / required / slack 三个数，并和报告对上。
:::

:::check
- 能说出 `slack = required - arrival`，并指出报告里哪两行是这两个数
- 能按五步定位法，从 WNS 走到"最贵的那一行"
- 能识别四类假违例，并写出对应的约束语句
- 能用手算得出"2ns 周期大概能放多少级逻辑"
- 知道 hold 必须修、setup 在 false path 上可以 waive，且 waive 必须留记录
:::

:::quiz
`slack = required - arrival` 里，required 由什么决定？|由捕获时钟到达时间减去触发器 setup 时间（以及不确定性、skew 等）决定，本质是"数据最晚必须什么时候到"。
一条路径上某一行 Incr 是 0.35ns，其他都是 0.05ns，说明什么？|这一级有问题：通常驱动不足、负载过大或线太长，是优先要修的点。
`report_timing -through` 用来干什么？|只看经过指定引脚/单元的路径，用来确认某个可疑单元出现在多少条关键路径上。
hold 违例为什么必须修，不能 waive？|它与时钟周期无关，硅片上一定会发生竞争，降频也救不了，属于功能性错误。
waive 一条违例时最低要求是什么？|写进签核报告的 waiver 表：路径、slack、原因、批准人，缺一不可。
:::
