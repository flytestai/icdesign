---
id: 03-01-innovus
no: 12
stage: 3
title: Innovus 起步：一个后端工具到底在管什么
en: Getting Started with Innovus
hours: 2
minutes: 35
tags: [Innovus, 工具, 数据库]
summary: 后端工具不是"画图软件"，它管的是一个巨大的数据库和一套优化引擎。这一课讲清 GUI 与命令行的关系、设计数据库里存了什么、以及第一个能跑通的命令序列。
---

## 工具在管什么 {#what}

一个布局布线工具（Innovus / ICC2）本质是三样东西：

1. **一个数据库**：几万个单元、几十万条连线、几百层几何图形，全在里面。
2. **一个优化引擎**：决定"放哪、怎么连、插不插缓冲器"。
3. **一堆报告**：时序、拥塞、DRC、面积、功耗。

你敲的每条命令，都是在**改数据库**或者**让引擎干活**，然后**读报告**判断下一步。

:::term Innovus | Cadence 的布局布线工具
数字后端两大主流 PR 工具之一（另一个是 Synopsys 的 ICC2）。命令语言是 Tcl，所有操作都能写成脚本。

课程阶段三用 40nm 工艺走 Innovus；阶段四用 32nm 走 ICC2。**两套工具，一套方法论。**
:::

## GUI 和命令行：到底用哪个 {#gui}

新手最容易犯的错：以为要用鼠标拖。

真实情况：

- **GUI 用来"看"**：看布局、看拥塞热图、看某条路径的走向。
- **命令行/脚本用来"做"**：所有设置、所有流程，都写成 `.tcl` 脚本跑。

原因很实际：一次 PR 要跑几小时，中间要改几十个参数。用鼠标点，你没法复现、没法对比、没法交接。**脚本是唯一可复现的方式。**

```tcl
# 启动 Innovus（GUI + 命令行都在）
innovus -no_gui -files run.tcl     # 纯命令行，服务器上跑批用这个
innovus                            # 带界面，调试时用
```

## 数据库里有什么 {#db}

打开一个设计后，数据库里至少存了这些：

| 内容 | 说明 | 对应报告 |
|---|---|---|
| 单元实例 | 每个标准单元的类型、坐标、朝向 | `report_area` |
| 连线（net） | 谁连谁、走哪层、多长 | `report_congestion` |
| 引脚（pin） | IO 位置、方向 | `report_pin` |
| 电源网络 | ring / stripe / rail | `verifyPowerVia` |
| 时序图 | 每条路径的门延迟、线延迟 | `report_timing` |
| 约束 | 时钟、IO 延迟、false path | `report_clocks` |

:::scene 为什么"重跑一遍"要几小时
因为数据库巨大。每次优化引擎动一下，都要重算几万个单元的时序和拥塞。

所以老手的习惯是：**小步试，快速验**。先用 `-incremental` 跑局部，看报告有没有改善，再决定要不要全量重跑。全量重跑一次 3 小时，你一天只能试 2 次。
:::

## 第一个能跑通的序列 {#first}

```tcl
# ---- 1. 读入设计 ----
# 读网表（综合出来的 .v）
read_netlist ../syn/netlist/ipa_top.v

# 读物理库（标准单元和宏单元的 .lef）
read_lef ../lib/lef/tsmc40_stdcell.lef
read_lef ../lib/lef/sram_2048x64.lef

# 读时序库（.lib，工具内部转成 .db）
read_libs ../lib/lib/tsmc40_tt.lib

# 读约束
read_sdc ../constraints/ipa.sdc

# 指定顶层模块名，并把网表和库"绑"起来
set top_design ipa_top
init_design

# ---- 2. 看一眼是否读对了 ----
report_area                    # 总面积、单元数
report_clocks                  # 时钟有没有读到
checkDesign -all               # 一致性检查，有 unconnected 会报出来

# ---- 3. 存盘（重要：每步都存） ----
saveDesign db/01_init.enc
```

:::pitfall 忘了 saveDesign，几小时白干
Innovus 不会自动存。跑到一半崩溃、或者你自己想回退，没有存盘就只能从零开始。

**规矩：每完成一个阶段就 `saveDesign db/NN_阶段名.enc`。** 这样出问题可以 `restoreDesign db/05_cts.enc` 回到上一个可用状态。

`NN` 用序号，方便排序和回退。
:::

:::term .enc | Innovus 设计数据库
Innovus 自己的二进制存盘格式（enc.dat 目录）。存了设计的完整状态：布局、布线、约束、设置。

和它对应的是 ICC2 的 `.ndm`（库）+ block 数据库。格式不同，作用相同。
:::

## 与 ICC2 的对应关系 {#icc2}

工具不同，动作一样。这张表建议存下来：

| 动作 | Innovus | ICC2 |
|---|---|---|
| 读网表 | `read_netlist` | `read_verilog` |
| 读物理库 | `read_lef` | 建库时已包含 |
| 读时序库 | `read_libs` | 建库时已包含 |
| 初始化 | `init_design` | `link_design` |
| 存盘 | `saveDesign x.enc` | `save_block` |
| 布局规划 | `floorPlan` | `initialize_floorplan` |
| 布局 | `place_opt_design` | `place_opt` |
| 时钟树 | `ccopt_design` | `clock_opt` |
| 布线 | `routeDesign` | `route_auto` |
| 时序报告 | `report_timing` | `report_timing` |

:::tip 学一套，通两套
面试常问"你会 Innovus 还是 ICC2"。正确答法是："我熟悉 PR 流程本身，两个工具的命令能对应上。"——因为公司换工具是常事，方法论才是你的资产。
:::

:::lab 动手：用 ICC2 走一遍同样的动作（本课程实测环境）
如果你的环境是 ICC2（我们验证过的机器），对应命令：

```tcl
# 打开库和 block
open_lib ./work_dir
open_block ipa_top

# 看状态
report_design -physical
report_timing -max_paths 1

# 存盘
save_block
```

过关标准：能说出你敲的每条命令，在另一套工具里叫什么。
:::

:::check
- 能说出后端工具管的三样东西（数据库、引擎、报告）
- 知道 GUI 用来看、脚本用来做
- 记得每个阶段结束必须 `saveDesign`
- 能背出至少 6 组 Innovus / ICC2 命令对应
:::

:::quiz
为什么后端流程强调"写脚本"而不是用 GUI 点？|因为要可复现、可对比、可交接；一次运行几小时、参数几十个，脚本是唯一能重跑和版本管理的方式。
`saveDesign` 为什么每个阶段都要做？|工具不会自动存盘，崩溃或需要回退时没有存档就得从头再来。
Innovus 的 `.enc` 和 ICC2 的数据库有什么区别？|格式不同（Cadence 私有 vs Synopsys NDM），作用相同：保存设计的完整状态。
`init_design` 做了什么？|把网表、物理库、时序库、约束绑定在一起，建立可操作的内部数据库。
:::
