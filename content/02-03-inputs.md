---
id: 02-03-inputs
no: 11
stage: 2
title: 开工前要拿到什么：设计数据准备与自检
en: Design Data Preparation & Sanity Checks
hours: 3
minutes: 38
tags: [输入数据, lib, lef, tluplus, sdc, 自检]
summary: 后端项目 80% 的"莫名报错"其实是输入数据不全或版本不对。这一课把 7 类输入文件讲清楚：各自是什么、少了会报什么错、怎么在开工前一次性查完。
---

## 一个项目开工，桌上应该有 7 样东西 {#seven}

综合和 PR 不是"给个网表就能跑"。工具要同时知道三件事：**逻辑长什么样、物理长什么样、时间要求是什么**。拆开就是下面这张表。

| # | 输入 | 常见后缀 | 谁给 | 少了会怎样（真实报错） |
|---|---|---|---|---|
| 1 | RTL 或综合后网表 | `.v` `.sv` | 前端 / 综合 | `Cannot find design 'xxx'` |
| 2 | 时序库 | `.lib` `.db` | 工艺厂 / 库团队 | `Unable to resolve reference 'INV_X1'`（单元全变黑盒） |
| 3 | 物理库 LEF | `.lef` | 工艺厂 | 单元没有尺寸，布局器无法摆放 |
| 4 | 工艺技术文件 | `.tf` `.techlef` | 工艺厂 | 建库失败，没有层定义 |
| 5 | 寄生参数模型 | `.tluplus` `.itf` `.qrc` | 工艺厂 | `NEX-018 no valid parasitic` → 优化器起不来 |
| 6 | 时序约束 | `.sdc` | 设计者 / 前端 | 时序全是 0，报告毫无意义 |
| 7 | 功耗意图（低功耗项目） | `.upf` `.cpf` | 架构 / 设计者 | 电源域不识别，隔离单元不插 |

:::scene 拿到一个"跑不起来"的工程
同事交接给你一个工程，说"脚本都在，直接跑就行"。你跑第一步就报：

```
Error: Unable to resolve reference 'DFF_X1' in design 'soc_top'. (LINK-5)
```

看着像脚本问题，其实是 **link_library 指错了目录，或者 .db 版本和网表不匹配**。会查输入数据的人 10 分钟解决；不会的人重装工具。
:::

## `.lib` 和 `.db`：一个是菜谱，一个是压缩包 {#libdb}

| | `.lib` | `.db` |
|---|---|---|
| 格式 | 纯文本，能打开看 | 二进制，打不开 |
| 内容 | 完全一样：每个单元的面积、引脚电容、延迟查找表 | 同左 |
| 谁生成 | 工艺厂 / 库团队 | 用 Library Compiler 从 `.lib` 转 |
| 工具读哪个 | 部分工具能直接读 | 综合与 PR 主要读这个（快很多） |

`.lib` 里能看到的东西（这是真正有用的部分）：

```tcl
cell (INV_X1) {
  area : 0.760;                       # 面积，算利用率要用
  pin (A)  { direction : input;  capacitance : 0.0021; }   # 输入电容，算驱动能力
  pin (ZN) { direction : output;
    timing () {
      related_pin : "A";
      cell_rise (delay_template_7x7) { ... }   # 输入转换时间 × 负载 -> 延迟，一张查找表
    }
  }
}
```

:::term 查找表（lookup table, LUT）| 延迟是怎么算出来的
标准单元的延迟不是一个固定数字，而是**输入信号变化快慢（transition）× 输出带多大负载（capacitance）** 的函数。工艺厂把它做成一张 7×7 的表存在 `.lib` 里，工具查表 + 插值得到延迟。

这就是为什么"换一个 corner、换一个负载"延迟就变了——不是工具在猜，是在查不同的表。
:::

:::pitfall 用了 `.lib` 但版本是 ss 的，时序全"过"
典型事故：综合用 `tt`（typical），PR 用了 `ss`（slow），PT 又用回 `tt`。三次报告的 WNS 各不相同，签字的人以为都过了。

**规矩：全流程记录 corner。** 每个阶段日志第一行打印用的是哪个库文件，归档时一起存。签核用的 corner 必须写在报告封面。
:::

## LEF：单元的"占地证" {#lef}

LEF 描述物理形状，分两种，都必须有：

| 类型 | 文件名常见 | 内容 |
|---|---|---|
| 技术 LEF（tech LEF） | `tech.lef` / `*.techlef` | 有哪些金属层、每层的最小线宽/间距、via 定义 |
| 宏 LEF（macro LEF） | `*_macro.lef` / `*.lef` | 每个标准单元的尺寸、引脚位置、阻挡层 |

一个单元在 LEF 里的样子：

```text
MACRO INV_X1
  CLASS CORE ;                 # 标准单元（CORE），不是 IO 也不是宏
  ORIGIN 0 0 ;
  SIZE 0.76 BY 1.4 ;           # 宽 0.76um、高 1.4um —— 行高由它决定
  PIN A
    DIRECTION INPUT ;
    PORT
      LAYER metal1 ;
      RECT 0.10 0.30 0.20 1.10 ;   # 引脚在 metal1 上的矩形位置
    END
  END A
END INV_X1
```

:::note 为什么行高是 1.4um
因为库里的标准单元都是 1.4um 高（`SIZE ... BY 1.4`）。**行高由库决定，不由你决定。** 你算"能放几行"时用的就是这个数：芯片高度 ÷ 1.4 = 行数。

我们实测的万门设计 222.2um 高，正好 153 行：222.2 ÷ 1.4 ≈ 158（去掉边距后 153）。
:::

## 寄生参数模型：为什么缺了优化器直接不干活 {#parasitic}

这一项最容易被漏，因为**缺了不一定马上报错，可能到优化阶段才炸**。

| 文件 | 工具 | 用途 |
|---|---|---|
| `.itf` / `.tluplus` | ICC2 / Innovus | 每层金属的电阻、电容、边缘电容参数 |
| `.qrc` / `.captable` | StarRC / QRC | 高精度提取用的电容表 |

我们踩过的真实案例（手册里有完整记录）：

```text
Error: Design has atleast one corner with no Parasitic information. (OPT-906)
```

原因不是"没做提取"，而是**建库时没把 TLU+ 绑进 corner**。修法两步：

```tcl
read_parasitic_tech -tlup ./tlup/NangateOpenCellLibrary.tlup \
                    -layermap ./tlup/NangateOpenCellLibrary.layermap -name nt
set_parasitic_parameters -early_spec nt -late_spec nt    # 必须绑到 corner 上
```

:::pitfall 只 `read_parasitic_tech` 不 `set_parasitic_parameters`
第一条命令只是"把文件读进内存"，第二条才是"告诉 corner 用它"。少了第二条，优化器依然认为没有寄生信息，照样报 `OPT-906`。

我们在这上面卡了一整轮，日志里 `NEX-018` 和 `OPT-906` 前后脚出现，真正的原因是后者。
:::

## SDC：最小可用的约束集 {#sdc}

一个能跑起来的 SDC 只需要五类语句。**先跑通这五条，再谈别的。**

```tcl
# 1) 时钟：周期 2ns = 500MHz。没有这一条，所有时序都是 0
create_clock -name clk -period 2.0 [get_ports clk]

# 2) 时钟不确定性：PLL 抖动 + 时钟树 skew 的预算，先给周期的 5%
set_clock_uncertainty 0.05 [get_clocks clk]

# 3) 输入延迟：外部器件把数据送进来要多久
set_input_delay 0.30 -clock clk [all_inputs]

# 4) 输出延迟：外部器件要求数据多快到位
set_output_delay 0.30 -clock clk [all_outputs]

# 5) 例外：复位是异步的，不该做时序检查
set_false_path -from [get_ports rst_n]
```

| 少了哪条 | 后果 |
|---|---|
| `create_clock` | 所有路径 unconstrained，报告显示"无违例"——**假的** |
| `set_input_delay` / `set_output_delay` | 输入输出路径按 0 延迟算，签核时全线违例 |
| `set_clock_uncertainty` | 时序过于乐观，实际芯片回来会 fail |
| `set_false_path` | 异步复位路径报一堆假违例，掩盖真问题 |

:::term SDC | Synopsys Design Constraints
时序约束文件，本质是一串 Tcl 命令。它不描述电路，只描述"这块电路要在多快下工作、哪些路径不用管"。

**SDC 写错比不写更危险**：不写，工具会说"没有约束"；写错，工具会一本正经地给你一份"全过"的报告。
:::

## 开工前的 5 项自检（10 分钟，省两天）{#check}

每次拿到新工程，按这个顺序查一遍：

```tcl
# 1) 库到底读了哪些？单元数对不对？
report_lib tt_1v0_25c
#    看 cell count，Nangate45 应该是 130 多个；如果是 0，库没读进来

# 2) 网表里有没有"找不到的单元"（黑盒）？
link_design
report_design -physical
#    有 unresolved reference 就是库不全，别往下跑

# 3) 时钟读到了吗？
report_clocks
#    必须能看到你 SDC 里定义的那个时钟名

# 4) 有没有完全没约束的路径？
report_timing -unconstrained
#    有输出就说明 SDC 漏了 input/output delay

# 5) 面积与利用率合理吗？
report_area
#    单元数为 0 或面积为 0，说明前面某步没生效
```

:::tip 把自检写成脚本
把这五条存成 `check_inputs.tcl`，每次新工程第一件事就是 `source check_inputs.tcl`。

老手和新手的差别不在会不会修 DRC，而在**新工程上手的前十分钟**：老手先查输入，新手直接跑流程，然后花两天查一个"库版本不对"的问题。
:::

:::lab 动手：算一次"这个库能放多少单元"
用 `.lib` 里的面积和 LEF 里的尺寸做一次手算，理解利用率的来源。

```bash
# 在模拟终端里跑（数据来自真实 Nangate45）
cd ~/pdk/nangate45/lib
grep -A2 "cell (INV_X1)" NangateOpenCellLibrary_typical.lib | head -3
# 看到 area : 0.760
```

然后手算：

- 芯片 222.5 × 222.2 um = 49440 um²
- 12026 个单元，平均面积按 2.0 um² 估 = 24052 um²
- 利用率 = 24052 / 49440 ≈ **48.6%**（和我们实测 49.8% 对得上）

过关标准：能说出"利用率 = 单元总面积 ÷ 芯片面积"，并解释为什么利用率不是越高越好（>85% 布不通）。
:::

:::check
- 能背出 7 类输入文件，以及每一类缺了会报什么错
- 知道 `.lib` 是文本、`.db` 是二进制、内容相同
- 知道 tech LEF 和 macro LEF 分别给什么
- 能写出 SDC 最小五条
- 遇到 `OPT-906` 知道先查寄生参数有没有绑到 corner
:::

:::quiz
`.lib` 和 `.db` 的内容有什么区别？|没有区别，都是同一个库；.lib 是文本可读，.db 是二进制，工具读 .db 更快。
只有 tech LEF 没有 macro LEF 会怎样？|工具知道有哪些层、线宽间距，但不知道每个标准单元多大、引脚在哪，无法布局布线。
`OPT-906` 报"没有寄生信息"，最常见的原因是什么？|寄生文件没读，或者读了没绑到 corner（缺 set_parasitic_parameters）。
SDC 里少了 create_clock 会怎样？|所有路径都 unconstrained，报告显示"无违例"，但这是假的，签核必挂。
为什么利用率不是越高越好？|超过 80~85% 后布线资源不够，拥塞和 DRC 会爆炸，反而要花更多时间收敛；经验值 50~70% 比较稳。
:::
