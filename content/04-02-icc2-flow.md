---
id: 04-02-icc2-flow
no: 30
stage: 4
title: ICC2 全流程实战：从空目录到导出版图
en: ICC2 Full Flow
hours: 10
minutes: 60
tags: [ICC2, 全流程, place_opt, clock_opt, route_opt]
summary: 一个 9390 单元的设计，从空目录跑到导出版图。八步各成一章：准备、建 block、floorplan、电源、place_opt、clock_opt、route、收尾导出。每步给命令、报告、常见报错，最后给一份分六节注释的完整 run 脚本和课程环境实测数据。
---

## 这一课怎么用：先把整条流水线看一遍 {#overview}

:::goal 学完这一课，你能从零独立跑完一个万门级设计的 ICC2 全流程：知道每一步在做什么、该看哪份报告、报告上什么算通过、失败了先查哪里。
:::

装修一套房子，顺序是有讲究的：量房 → 改水电 → 砌墙 → 摆家具 → 装灯 → 走线 → 保洁 → 交钥匙。你不能先装灯再砌墙，也不能保洁完再开槽。

后端全流程一模一样。**每一步都在给下一步准备条件**，顺序错了不是"效果差一点"，而是根本跑不下去：

- 没建库就读网表，单元全是空壳，时序一条都算不出来。
- 没做 floorplan 就布局，工具不知道该往多大的地方摆。
- 没布电源就布线，最后所有标准单元没电，ERC 全红。
- 没建时钟树就布线，时钟网络会被当普通信号线随便走，skew 大得没法看。

这一课把八步拆成八章，每章回答四个问题：**做什么、敲什么命令、看什么报告、常见什么错**。最后给一份可以直接改路径就跑的 run 脚本。

整条流水线长什么样，先看一眼全景再进章节。

:::fig flow-overview | 全流程图：左边灰色虚线框是前端做完交给你的东西（网表、约束、库），右边蓝色框是后端各阶段。本课要跑的是其中 ICC2 这一段：建库建 block → floorplan → 电源 → place_opt → clock_opt → route → 收尾 → 导出，正好对应下面表里的 0~8 步。
:::

从图里要看出什么：**每一步的产物都是下一步的原料**。后面八章会反复回到这句话——哪一步失败，先看它的上游喂了什么。

| 阶段 | 一句话目的 | 主命令 | 产物 |
|---|---|---|---|
| 0 准备 | 确认库、约束、网表三样齐 | `report_lib` / `check_timing` | 一份检查记录 |
| 1 建 block | 把网表装进库，单元对上号 | `create_lib` / `link_block` | 可操作的 block |
| 2 floorplan | 定芯片多大、宏放哪 | `initialize_floorplan` | 边界 + 宏位置 |
| 3 电源 | 把电送到每个单元头上 | `compile_pg` | PG 网络 |
| 4 place_opt | 摆标准单元并做预 CTS 优化 | `place_opt` | 布局 + 初步时序 |
| 5 clock_opt | 建时钟树、修 hold | `clock_opt` | 时钟树 |
| 6 route | 把逻辑连接变成金属线 | `route_auto` / `route_opt` | 无 DRC 的版图 |
| 7 收尾 | 填 filler、全面自检 | `insert_stdcell_filler` | 可签核数据 |
| 8 导出 | 交给 STA / PV / 工厂 | `write_def` 等 | def/v/spef/sdc |

**每一步结束问三个问题**：数量对不对（单元数、pin 数）、报告红不红（WNS、DRC、违例数）、存盘了没有。三个都答"是"，才允许进下一步。

前面 03 章学的是"单点技术"——floorplan 怎么规划、CTS 指标怎么读。这一课学的是"串联"：同样的知识，放进一条有先后依赖的流水线里，什么时候用、用哪个数、用完交给谁。

:::scene 周三下午，一条跑到一半的流程
你接手一个离职同事的 ICC2 项目。目录里只有一个 `run.tcl`，没有任何注释；`work/` 下有个半成品 block，不知道跑到哪一步了。

leader 说："这周五要交一版给 STA 签核，你先把它跑通。"

你打开 `run.tcl`，第一行是 `open_lib ./work/ipa.lib`，第二行 `open_block ipa.lib:ipa_top`。跑到 `place_opt` 时报 `OPT-041`。你不知道这个 block 里电源布了没有、时序约束 source 了没有、上一次存盘是布局前还是布局后。

这一课的目标，就是让你不再造出这样的目录：**每一步都有固定命名、固定报告、固定检查点，任何人接手都能从任意一步续跑。**
:::

:::term Floorplan | 布局规划
决定芯片/模块的物理边界（die/core 多大、什么形状）、宏单元（SRAM、PLL、IP）摆在哪、电源怎么走。它不摆标准单元，但决定了标准单元以后能有多舒服。
:::

:::term Core Utilization | 核心利用率
标准单元总面积 ÷ core 面积。0.65 表示 core 里 65% 的面积被单元占掉，剩下 35% 留给布线通道和空白。利用率越高，布线越挤。
:::

:::term Congestion | 拥塞
某个区域内"需要的连线数"超过"能提供的布线轨道数"。表现是全局布线后一片红色热点，详细布线时绕不出去，最后变成大量 DRC。
:::

:::term Pre-CTS Optimization | 预时钟树优化
`place_opt` 的后半段：在时钟还是"理想时钟"的阶段，插 buffer、换驱动、换阈值电压，把 setup 违例压下去。它算的线延迟是估算值，不是最终值。
:::

:::term Global Route | 全局布线
把每条连接分配到大致走哪几个布线通道（哪一层、哪个区域），不决定具体坐标。它负责"分车道"，详细布线才负责"画车道线"。
:::

:::term Filler Cell | 填充单元
没有逻辑功能、只有版图图形的单元，用来填满标准单元行里的空隙，保证阱和电源轨连续、CMP 抛光均匀。它不参与逻辑，但少了它 ERC/LVS 会出问题。
:::

:::term SPEF (Standard Parasitic Exchange Format) | 标准寄生交换格式
描述每根线电阻、电容的文本文件。STA 工具读它，才能用"真实线延迟"而不是"估算线延迟"算时序。
:::

:::term Signoff | 签核
设计交付前的最终确认：时序、DRC、LVS、IR drop、EM 全部达标。PR 工具内部的报告只是"自检"，签核要用专门工具（PrimeTime、Calibre 等）再跑一遍。
:::

## 跑之前先确认三件事 {#prep}

很多人跳过这一步，直接 `place_opt`，然后在两小时后收到一个看不懂的报错。**准备阶段花二十分钟，能省掉半天。**

### 第一件：库对不对

```tcl
# 作用：确认 NDM 里有物理视图、时序视图，且 corner 齐全
# 用法：open_lib 之后、create_block 之前执行；输出贴进 run.log 头部
report_lib tsmc32_tt                          ;# 打印库内容：单元数、各 corner 的 timing view、面积单位
report_parasitic_tech                          ;# 列出已加载的寄生模型（有的版本叫 get_parasitic_techs）
get_attribute [current_lib] name               ;# 确认当前挂的是哪个库，避免拿错版本
```

`report_lib` 里要看到 `Timing Data`，且 corner 数量和你预期一致（典型是 ss/tt/ff 三档，每档可能还有不同电压温度）。只有物理没有时序，`place_opt` 一定失败，报 `OPT-041`——这条在 04-01 课已经拆过。

### 第二件：约束对不对

```tcl
# 作用：source 约束后，检查时钟定义和未约束端点
# 用法：link_block 之后执行；必须全部通过才进 floorplan
source ../constraints/ipa.sdc                  ;# 读 SDC：时钟、input/output delay、false path 等
report_clocks                                  ;# 列出工具认到的时钟：名字、周期、源端口
check_timing -verbose                          ;# 检查未约束端点、缺 input delay、组合环等
```

三个数必须记住：**时钟个数**、**最小时钟周期**、**unconstrained endpoints 是否为 0**。时钟个数不对，说明 SDC 里有 `create_clock` 写错端口名；有未约束端点，说明那部分逻辑根本没进时序分析，后面优化会"看不见"它们。

### 第三件：网表对不对

```bash
# 作用：在跑 ICC2 之前，先用文本工具做三个廉价检查
# 用法：在 netlist/ 目录下执行；比开工具快得多
grep -c "^module" ipa_top.v                    # 数模块个数：正常只有顶层 + 少量黑盒
grep -n "assign.*x" ipa_top.v | head            # 找三态/不定态赋值，综合后不该出现
grep -c "SRAM" ipa_top.v                        # 数 SRAM 实例，和 floorplan 方案里的数量对一下
```

网表最常见的两个问题是：**黑盒没替换**（某个 IP 还是空 module）和**电源引脚没接**（UPF 流程里常见）。黑盒在 `link_block` 时会变成 unresolved，工具不一定报错，但那个模块的所有路径都不参与优化。

顺带看一眼这份网表是哪来的：它是上游综合工具 Design Compiler 用几行脚本把 RTL 变成门级的产物。

:::fig term-dc | Design Compiler 综合的最小脚本：读 RTL、设约束、`compile`、写出 `.v`。重点看它输出的网表文件——就是本课 `netlist/` 里那份 `ipa_top.v` 的来源。后端是这份网表的"下家"，网表有问题，先回这几行脚本附近查。
:::

从图里要看出什么：**后端拿到的是"原料"不是"成品"**。黑盒、电源引脚没接这类问题，根源多半在综合侧，定位时别只在 PR 里打转。

:::pitfall SDC 端口名和网表对不上，工具不报错
现象：`report_clocks` 只有一个时钟，但设计明明有三个；`check_timing` 里 `unconstrained_endpoints` 是几百。

原因：综合后顶层端口被改过名（比如 `clk_axi` 变成了 `CLK_AXI`），SDC 里还是老名字。`create_clock` 找不到端口时**只报 warning，不报 error**，时钟就静默地没建。

怎么查：`get_ports *clk*` 看实际端口名，和 SDC 里的名字逐个对。大小写敏感，这是最常见的差异。

怎么避免：SDC 不要手写端口名，从综合的同一份约束导出；或者在 `source` 之后加一条断言：`if {[llength [all_clocks]] != 3} { error "clock count mismatch" }`。
:::

### 手算一次：core 要多大

课程环境这个设计有 9390 个单元，课程库的平均单元面积约 2.6 µm²（由最终面积反推，典型值）：

- 单元总面积 ≈ 9390 × 2.6 = 24,414 µm²
- 目标利用率 0.65 → core 面积 = 24,414 ÷ 0.65 ≈ 37,560 µm²
- core 边长 = √37,560 ≈ 194 µm

所以 `initialize_floorplan -core_utilization 0.65` 会给出接近 194×194 µm 的 core。最终 die 是 222.5×222.2 µm，比 core 每边多出约 14 µm，这部分留给电源环、边界和 IO。

**利用率不是拍脑袋**：0.65 意味着 35% 的空地。万门级设计布线需求不大，0.65 很宽松；十万门以上通常给 0.75~0.85，再高就会拥塞。

## 第 1 步：建库、建 block、读网表 {#step1}

库（library）和 block 的关系，像"文件夹"和"里面的一份文档"。库是容器，block 是具体设计。一个库里可以放多个 block（比如不同版本、不同模块）。

打开 block 之后，你在 ICC2 里看到的界面是这样：

:::fig icc2-gui | ICC2 主窗口：左侧设计浏览器、中间版图视图、底部 Tcl 命令窗。本课八步的所有操作都在这个窗口里发生——第 1 步之后中间应能看到读进来的网表单元，底部命令窗则是逐节跑脚本、看报错的地方。
:::

从图里要看出什么：**记住"左边看层次、中间看版图、底部看命令"的分工**。后面每一步的检查点，要么是左边数个数，要么是中间看一眼图形，要么是底部那条命令的返回值。

```tcl
# ---- 第 1 步：建库、建 block、读网表 ----
set PDK /pdk/tsmc32                                              ;# PDK 根目录，所有路径从这里拼，避免到处写绝对路径
set DESIGN ipa_top                                               ;# 设计名，后面 block 名、报告名都用它
create_lib ./work/${DESIGN}.lib -ref_libs [list $PDK/ndm/tsmc32_tt.ndm]  ;# 建设计库，挂只读参考库（标准单元）
create_block $DESIGN -lib ./work/${DESIGN}.lib                   ;# 在库里建一个空 block，名字就是设计名
open_block ./work/${DESIGN}.lib:$DESIGN                          ;# 打开 block；ICC2 用"库:block"的写法定位
read_verilog ./netlist/${DESIGN}.v                               ;# 读综合后的门级网表（不是 RTL）
link_block                                                       ;# 把网表单元和参考库对上号（旧脚本写作 link_design）
report_design_mismatch                                           ;# 列出没对上的引用：缺库、缺 cell、缺 pin
```

逐条说清三个关键点：

- **`create_lib -ref_libs` 只是"引用"标准单元库，不复制**。所以 NDM 更新后，所有引用它的 block 都会受影响。项目里要记录"这次跑用的是哪一版 NDM"。
- **`read_verilog` 只把网表读进内存**，还没和库建立联系。`link_block` 才做匹配：按单元名去参考库里找定义。
- **`report_design_mismatch` 必须是空的**。不为空时，先别往下跑——哪怕只缺一个 cell，那个 cell 的所有引脚都会变成"没有负载/没有驱动"，时序结果整体失真。

`link_block` 失败的三种典型原因：

| 现象 | 原因 | 处理 |
|---|---|---|
| 大量单元 unresolved | 参考库没挂上，或挂错库 | `report_ref_libs` 看引用列表 |
| 只缺几个单元 | 库里确实没有（如自定义 IP） | 补一个 NDM，或确认它是黑盒 |
| 缺 pin | 网表的 pin 名和库不一致（多见于电源 pin） | 检查 UPF 和库的 PG pin 定义 |

:::pitfall link 之后不检查，直接 floorplan
现象：`place_opt` 报大量 "unlinked" 或者时序里某些单元延迟为 0。

原因：`link_block` 有 unresolved 但不 fatal，工具允许你继续。你以为成功了，其实带着一堆空壳在跑。

规矩：**`report_design_mismatch` 输出为空，才允许 `initialize_floorplan`。** 把它写进脚本断言，比人眼可靠。
:::

## 第 2 步：floorplan：定边界、摆宏 {#step2}

Floorplan 是"量房 + 定承重墙"。它决定三件事：芯片多大、core 在哪、宏单元（SRAM/PLL/IP）摆哪。

```tcl
# ---- 第 2 步：floorplan ----
initialize_floorplan -core_utilization 0.65 -core_offset {10 10 10 10}  ;# 按 65% 利用率推 core 大小，四周各留 10µm
# 另一种写法：边界和封装已经定了，直接给四个角点（单位 µm）
# initialize_floorplan -boundary {{0 0} {222.5 0} {222.5 222.2} {0 222.2}}  ;# 顺序必须是左下→右下→右上→左上
set_cell_location -coordinates {40 60} -orientation MY [get_cells u_sram0]  ;# 把 0 号 SRAM 摆到 (40,60)，MY 表示沿 Y 轴镜像
set_attribute [get_cells u_sram0] is_fixed true                   ;# 锁定位置，后续 place_opt 不许移动它
set_cell_location -coordinates {40 140} -orientation R0 [get_cells u_sram1]  ;# 第二个 SRAM 摆到上方，R0 表示不旋转
set_attribute [get_cells u_sram1] is_fixed true                    ;# 同样锁定
```

`initialize_floorplan` 是 ICC2 的命令；ICC1 里叫 `create_floorplan`。看到老教程写 `create_floorplan`，先确认它讲的是哪一代工具。

宏摆放的三条经验：

1. **沿边界摆，不要摆在中间**。宏放中间会把布线通道切成两半，标准单元绕不过去。
2. **出 pin 的一侧朝 core 内部**。SRAM 的数据/地址 pin 朝向标准单元区，线最短。
3. **宏之间留通道**。通道宽度 ≈ 穿过它的引脚数 × 布线间距 ÷ 可用层数。比如 200 根线、每根占 0.1 µm、可用 4 层，通道至少 5 µm，实际给 10~15 µm 更稳（详细算法见 03-03 课）。

摆完要做三件检查：

```tcl
# 作用：floorplan 后的三项体检
# 用法：摆完宏立刻执行，不要等 place_opt
report_qor                                      ;# 看利用率、单元数、是否有重叠
check_floorplan                                 ;# 检查边界、row、宏是否越界或重叠（命令名以版本为准）
report_congestion -hotspot                      ;# 看宏周围有没有明显的拥塞热点
```

利用率这一栏如果显著高于 `-core_utilization` 的设定（比如设 0.65、报 0.78），说明宏占的面积没算进去，core 给小了。硬撑下去的后果是 `place_opt` 把单元塞得满满当当，布线阶段无路可走。

:::pitfall 宏重叠，place_opt 直接合法化失败
现象：`place_opt` 刚开始就报 legalization failed，或者日志里说某些单元无法摆放。

原因：两个 SRAM 的边界框重叠了。工具不会自动帮你挪宏（宏是 fixed 的），只能报错。

怎么查：`report_qor` 看不出来时，用 `get_cells -filter "is_macro==true"` 列出所有宏，打印各自 `boundary`，两两比对。或者打开 GUI 看。

怎么避免：宏坐标不要手算。用脚本从 floorplan 方案表（Excel/CSV）读，摆完统一做一次重叠检查。
:::

## 第 3 步：电源网络：先把电送到每个单元 {#step3}

电源像小区的供水管网：先有一圈主管（ring），再有支管（strap），最后每栋楼接一根入户管（via + rail）。标准单元行里已经自带 horizontal rail（在 M1/M2），你要做的是把电从顶层金属送到这些 rail 上。

不同的 ICC2 版本，电源命令差别很大。老版本用 `create_pg_ring` / `create_power_straps`，2016 之后的版本主流是"pattern + strategy + compile"三件套。有的教学环境会把这一组封装成一个叫 `create_pg_network` 的脚本，**Synopsys 原生命令是下面这一组，以你版本的 `man` 为准**。

```tcl
# ---- 第 3 步：电源网络 ----
create_pg_ring_pattern ring_m5m6 -horizontal_layer M6 -horizontal_width 3 -horizontal_spacing 2 -vertical_layer M5 -vertical_width 3 -vertical_spacing 2  ;# 定义电源环模板：线宽 3µm、间距 2µm
set_pg_strategy core_ring -core -pattern {{name: ring_m5m6} {nets: {VDD VSS}}}  ;# 把模板套到 core 四边，VDD/VSS 各一圈
compile_pg -strategies core_ring                                  ;# 按策略真正生成几何图形（多边形和 via）
create_power_straps -direction vertical -layer M5 -width 1.5 -spacing 2 -pitch 25 -nets {VDD VSS}  ;# 竖向支管：每 25µm 一根（老版本写法）
connect_pg_net -net VDD [get_pins -hier -filter "name==VDD"]       ;# 把所有单元的 VDD 引脚接到 VDD 网络
connect_pg_net -net VSS [get_pins -hier -filter "name==VSS"]       ;# 同理接 VSS
check_pg_connectivity                                              ;# 检查有没有"悬空"的电源引脚
check_pg_drc                                                       ;# 检查电源网络自身的 DRC（宽度、间距、via 阵列）
```

四个检查点：

- `check_pg_connectivity` 必须报 **0 unconnected**。有一个没接，将来 IR drop 分析会漏掉它，硅片上就是局部不工作。
- `check_pg_drc` 看 via 阵列够不够。一根 3 µm 宽的 M6 接到 M5，只打一个 via 会有很大的接触电阻，通常要打一排。
- 电源环要**闭合**。四边缺一边，电流绕远路，IR drop 会明显变差。
- 支管方向要和单元 row 方向匹配。row 是横向的，rail 在 M1 横向走，所以竖向支管（M5）负责"分配到每一行"。

### 手算一次：一根电源条能扛多少电流

假设 M5 的方块电阻 0.05 Ω/sq（课程库典型值），一根电源条长 200 µm、宽 4 µm：

- 方块数 = 200 ÷ 4 = 50 个方块
- 电阻 = 50 × 0.05 = 2.5 Ω
- 如果这根条要送 20 mA：压降 = 0.02 A × 2.5 Ω = **50 mV**

电源 1.0 V，IR drop 预算通常给 5%（50 mV）。这根条刚好用满预算，所以宽度不能再减。如果把它改成 2 µm 宽，电阻翻倍到 5 Ω，压降 100 mV，直接超标。

这就是"电源规划靠算，不靠感觉"的意思：**宽度、间距、pitch 三个数，每一个都能折算成 mV。**

常见报错与现象：`check_pg_connectivity` 报成片的 unconnected，先看电源环有没有闭合、标准单元的 rail 有没有和 stripe 交上；`check_pg_drc` 报 min width / min spacing，通常是 stripe 宽度低于工艺最小值，或者两条 VDD/VSS 挨得太近。这两类都不是"多跑一遍"能修的，必须改图形。

## 第 4 步：place_opt：摆单元 + 预 CTS 优化 {#step4}

`place_opt` 一个命令干了四件事，顺序是内部的：

1. **全局布局（global placement）**：先把单元"撒"开，允许重叠，目标是线长最短、拥塞最小。
2. **合法化（legalization）**：把每个单元对齐到标准单元行的格点上，消除重叠。
3. **高扇出与 DRV 修复**：插 buffer、加大驱动，修 max fanout / max transition。
4. **预 CTS 时序优化**：在理想时钟下修 setup，插 buffer、换 LVT、调整尺寸。

```tcl
# ---- 第 4 步：布局 + 预 CTS 优化 ----
set_app_options -name place.coarse.continue_on_missing_scandef -value true  ;# 没有 scan def 时不要静默跳过布局（关键！）
set_host_options -max_cores 8                                              ;# 允许用 8 核并行；按机器实际核数改
place_opt                                                                   ;# 全局布局 → 合法化 → 插 buffer → 预 CTS 时序优化
report_qor > rpt/04_qor_place.rpt                                          ;# QoR：WNS/TNS/面积/利用率/违例数
report_timing -max_paths 20 > rpt/04_timing_place.rpt                      ;# 最差 20 条路径，看瓶颈在逻辑级数还是线延迟
report_congestion -hotspot > rpt/04_congestion.rpt                          ;# 拥塞热点，决定要不要回头改 floorplan
save_block                                                                  ;# 存盘：这一步之后所有结果都以它为基础
```

`place_opt` 之后必须看四个数：

| 指标 | 在哪看 | 万门级健康范围 | 不正常说明什么 |
|---|---|---|---|
| WNS | `report_qor` | 接近 0 或略负 | 负太多：约束太紧或库太慢 |
| TNS | `report_qor` | 不超过 WNS 的 10 倍 | TNS 巨大说明一大批路径同时差 |
| 利用率 | `report_qor` | 比 floorplan 设定高 5~15 个百分点 | 高太多：buffer 插爆了 |
| 单元数增长 | 对比读入时 | +20%~35% | 超过 50%：约束或库有问题 |

课程环境这次跑出来：**9390 → 12026 个单元，增长 28%**，落在正常区间。多出来的 2636 个主要是 buffer、delay cell 和驱动增强换进来的大尺寸单元。

按平均 2 µm² 估，2636 个新增单元约占 5,272 µm²，是原面积的 21%。这里要弄清"利用率"的分母：按 core（194×194 µm）算约 65%，按 die（222.5×222.2 µm）算才是 49.8%。报告里写哪个口径，取决于工具和设置；比较两个数之前，先确认分母是 core 还是 die。

:::pitfall 静默失败：几秒钟跑完，一个单元都没放
现象：`place_opt` 三秒结束，日志没有 Error，打开布局一看 core 是空的。

原因：ICC2 默认要求有 scan def（扫描链的物理顺序定义）。没有它，布局器选择"跳过布局"，而且只报 warning。

解法：在 `place_opt` 之前设 `place.coarse.continue_on_missing_scandef` 为 true。没有扫描链的设计（比如纯组合加速器）必须设这一条。

**这类"跑得特别快、结果为空"的失败比报错危险**，因为它看起来像成功。判断方法：跑完立刻 `report_qor` 看单元数，是 0 就停。
:::

:::pitfall 利用率飙到 0.9，布线阶段无路可走
现象：`place_opt` 报告利用率 0.88，`route_auto` 之后 DRC 几千个，热点集中在某几个区域。

原因：floorplan 的 core 给小了，或者宏占位太多。布局器为了塞进去，把单元挤成一团，布线轨道不够分。

处理：不要靠 `route_opt` 硬磨。回到第 2 步，把 core 放大 10%，或者把宏改成沿边摆放，重跑 place。**布局阶段的拥塞，布线阶段修不回来。**
:::

## 第 5 步：clock_opt：建树、修 hold {#step5}

CTS 的原理在 03-08 课讲透了，这里只讲 ICC2 里怎么跑、看什么。

ICC2 的 `clock_opt` 默认会"建树 + 优化 setup/hold"一起做。第一次建树建议加 `-only_cts`，把建树和时序优化分开，这样 skew 出问题时能确定是树的问题还是优化的问题。

```tcl
# ---- 第 5 步：时钟树 ----
set_app_options -name cts.optimize.delay -value true     ;# 建树时同时优化 insertion delay，不只压 skew
clock_opt -only_cts                                       ;# 只建树，不做 setup/hold 优化（便于单独看树的质量）
report_clock_timing -type skew > rpt/05_skew.rpt          ;# skew：全局/局部最差值，以及是哪两个叶子
report_clock_timing -type latency > rpt/05_latency.rpt    ;# insertion delay：源到叶子的总延迟分布
report_clock_timing -type transition > rpt/05_trans.rpt   ;# transition：时钟波形质量
save_block                                                ;# 存"纯树"版本，出问题可以回到这里
clock_opt -only_hold_time                                 ;# 单独修 hold（版本不认这个选项时，直接跑 clock_opt）
save_block                                                ;# 存修完 hold 的版本
```

三个报告各看什么：

- **skew**：全局 skew 是否在目标 1.5 倍以内；最差的那对叶子是不是跨了半个芯片（跨得远说明树结构有问题）。
- **latency**：最长 insertion delay 通常 0.8~1.5 ns。超过 2 ns 说明树太深或驱动太弱。
- **transition**：时钟网络上的 transition 超标会直接导致 hold 计算不准，也会加重 EM。

课程环境的数据：`clock_opt` 跑了 **9.5 分钟**，是八步里最慢的；hold 从 CTS 刚结束时的 **−10 ns 量级** 收敛到 **−0.07 ns**。

为什么一开始 hold 会差到 −10 ns？因为 CTS 之前时钟是"理想时钟"（零延迟、零 skew），工具算 hold 时假设时钟同时到达所有触发器，hold 天然满足。CTS 之后切成"传播时钟"，真实延迟出来了，原来藏着的 hold 违例一次性暴露。**这不是树建坏了，是账终于算清了。**

:::pitfall 看到 hold −10 ns 就回去重建树
现象：CTS 后 `report_timing -delay_type min` 一片负值，最差 −10 ns，你怀疑树建错了。

原因：绝大多数是 ideal → propagated 的正常暴露。尤其是同一时钟分支上相邻触发器之间的短路径，逻辑延迟只有几十 ps，时钟 skew 一进来 hold 就负。

怎么判断：看违例路径的起点和终点是不是同一分支、物理距离近不近。近的交给 hold 优化；跨越大半芯片的才是树或约束问题。

处理：先跑 hold 优化（`clock_opt -only_hold_time`），看能收敛到多少。课程环境收敛到 −0.07 ns，剩下的留给 `route_opt`。
:::

## 第 6 步：route_auto / route_opt：把连接变成金属 {#step6}

布线分两级：

- **全局布线（global route）**：给每条连接分配"走哪层、走哪个通道"，不落具体坐标。它决定拥塞。
- **详细布线（detail route）**：在通道内画出具体金属线和 via，遵守 DRC 规则。

`route_auto` 一次把两级都跑完；`route_opt` 在真实寄生提取后做时序优化，会挪线、插 buffer，可能重新引入 DRC。

```tcl
# ---- 第 6 步：布线 ----
route_auto                                                       ;# 全局 + 详细布线，产出第一版可检查的版图
check_routes > rpt/06_drc_after_auto.rpt                          ;# DRC 统计：总违例数、按类型分类
report_timing -max_paths 20 > rpt/06_timing_route.rpt              ;# 真实寄生下的时序（比 place 阶段悲观）
route_opt                                                         ;# 基于提取寄生的时序优化：挪线、插 buffer、换单元
check_routes > rpt/06_drc_after_opt.rpt                            ;# 优化后 DRC 可能反弹，必须复查
route_detail -incremental > rpt/06_drc_detail.rpt                  ;# 只磨残余 DRC，不动时序（版本不支持就去掉这行）
```

DRC 收敛的判断标准，不是"跑了几遍"，而是**违例类型**：

| 类型 | 典型原因 | 能不能靠多跑几遍修 |
|---|---|---|
| short（短路） | 两条线真的碰上了 | 不能，要改布局或加通道 |
| spacing（间距） | 线与线太近 | 部分能，`route_detail` 可解 |
| open（开路） | 线没连上 | 不能，通常是 pin access 问题 |
| via 相关 | via 打不下或规则不符 | 部分能 |

课程环境这次很顺：`route_auto` 首轮 **DRC = 0**，`route_opt` 之后仍然 0，`route_detail` 跑 5 遍也是 0。首轮就 0 说明 floorplan 和布局做对了；真实项目里首轮几百到几千个 DRC 是常态，不要拿这个当标准。

**课表外补充：antenna（天线效应）**。长金属线在等离子刻蚀时会积累电荷，可能击穿栅氧。布线后要单独检查 antenna，违反的靠"跳层"（把长线在中途换到更高层再换回来）解决。ICC2 里有对应的检查命令，具体名字以版本为准，这一课不展开。

:::pitfall DRC 没清零就跑去修时序
现象：`route_auto` 后 3000 个 DRC，你直接 `route_opt` 修时序，结果 DRC 涨到 5000。

原因：`route_opt` 为了修时序会挪线、插 buffer，在已经拥挤的区域雪上加霜。DRC 是"路不够"，时序是"路太长"，先解决路不够。

顺序：**先让 DRC 降到可控（几十个以内），再修时序，最后磨残余 DRC。** 如果 DRC 几千，说明布局/floorplan 有问题，回第 2 步。
:::

## 第 7 步：收尾：filler、全面自检 {#step7}

布线完的版图，标准单元行里还有大量空隙。不填的后果：阱不连续、电源轨断断续续、CMP 抛光不平、LVS/ERC 报错。

```tcl
# ---- 第 7 步：收尾 ----
insert_stdcell_filler -cell_without_metal {FILL64 FILL32 FILL16 FILL8 FILL4 FILL2 FILL1}  ;# 从大到小填空隙（老脚本里叫 insert_filler）
connect_pg_net -net VDD [get_pins -hier -filter "name==VDD"]     ;# filler 也有 VDD/VSS 引脚，填完要重新连
connect_pg_net -net VSS [get_pins -hier -filter "name==VSS"]     ;# 同上
check_routes > rpt/07_drc_final.rpt                               ;# filler 可能引入新的 spacing 违例，必须复查
check_pg_connectivity > rpt/07_pg_conn.rpt                        ;# 电源连通性最终确认
report_timing -max_paths 50 > rpt/07_timing_final.rpt              ;# 最终时序（PR 内部口径）
report_area > rpt/07_area.rpt                                     ;# 面积：单元面积、core 面积、利用率
report_qor > rpt/07_qor_final.rpt                                  ;# 汇总，交给下一环节
```

填 filler 的三个纪律：

1. **从大尺寸填到小尺寸**。先填 FILL64 再填 FILL1，否则大 filler 没地方放，最后剩一堆 1 µm 的缝。
2. **先填不带金属的 filler**。带金属的 filler 会和信号线抢布线资源，通常只在不做 ECO 的最终版才用。
3. **填完必须重跑 DRC 和 PG 连通性**。filler 是"新加的单元"，它也会带来违例。

收尾之后是 signoff：时序交给 PrimeTime（05-02 课），DRC/LVS 交给物理验证工具（05-03 课）。PR 工具里的 `report_timing` 只是自检，不能当签核结论。

按空余面积估 filler 数量：die 49,440 µm² × (1 − 0.498) ≈ 24,800 µm² 的空地，除以平均 filler 面积（课程库约 20 µm²）≈ 1200 个。这个数不用精确，工具会自己算，但你要能判断"报告里 1200 个 filler"是合理还是异常。

为什么不能省掉这一步？三个理由都很硬：

- **阱和电源轨要连续**。标准单元行是一整条，中间空一格，N 阱就断了，ERC 会报 well 相关的错。
- **CMP 要求密度均匀**。金属和 poly 的密度差太多，化学机械抛光会"凹"下去，影响良率。
- **LVS 会把空隙当异常**。有些工艺的 LVS 规则要求单元行填满，空着直接报错。

所以 filler 不是"美化版图"，是电气和工艺的要求。它也是**最后一个能动版图的动作**——填完之后再做 ECO，要先 `remove_stdcell_filler` 把挡路的 filler 删掉。

常见报错：`insert_stdcell_filler` 报找不到合法位置（no legal location），一般是标准单元行不完整（被宏或 blockage 切断），或者 filler 清单里没有足够小的尺寸去填缝。先 `check_floorplan` 看 row，再确认清单里从大到小都有。

## 第 8 步：导出：四份文件，四个下游 {#step8}

导出不是"存个盘"，是**给不同下游交不同格式的同一版设计**。

```tcl
# ---- 第 8 步：导出 ----
set STAMP 20261122_1400                                           ;# 统一时间戳，保证四份文件同源，出问题能对上
write_def ./out/${DESIGN}_${STAMP}.def                            ;# 版图交换格式：给 PV、给其他工具、给工厂
write_verilog ./out/${DESIGN}_${STAMP}.v                          ;# 布线后网表：给 PT 做 STA、给 formal 做等价检查
write_sdc ./out/${DESIGN}_${STAMP}.sdc                            ;# 约束：必须和 PR 用的是同一份，不能另写
write_parasitics -format SPEF -output ./out/${DESIGN}_${STAMP}.spef  ;# 寄生：让 PT 用真实 R/C，而不是估算
```

| 文件 | 给谁 | 用途 | 常见错误 |
|---|---|---|---|
| `.def` | PV / 布局工具 | 版图几何、单元位置、布线 | 版本不匹配，读进去坐标错位 |
| `.v` | PrimeTime / formal | 门级网表，STA 的对象 | 导出的是布局前网表 |
| `.sdc` | PrimeTime | 时序约束 | 和 PR 内部约束不是同一版 |
| `.spef` | PrimeTime | 真实寄生 R/C | 和网表不是同一次运行 |

**四份文件必须同一次运行、同一个时间戳导出。** 这条规矩在 05-01 课会用一次真实事故展开，这里先记住：网表和 SPEF 差一天，时序结果就能差 2 ns，而且看不出来是数据问题。

另外两个容易忽略的点：

**SDC 要从 PR 工具里导，不要复制输入的那份。** PR 过程中工具会补 `set_propagated_clock`、更新时钟不确定性、加 case analysis，导出的是"PR 实际用的那份约束"。直接拷输入 SDC，PT 会因为少了这些设置而算出不同的结果。

**DEF 的版本要写进交接记录。** DEF 有 5.5、5.6、5.7 等多个版本，不同 EDA 工具默认导出的版本不同。PV 读不进去时，第一件事是看版本，而不是怀疑版图。

导完做一次自检：

```bash
# 作用：确认四份文件都在、且时间戳一致
# 用法：在 out/ 目录下执行
ls -lh *20261122_1400*                        # 四个文件应该同时存在，大小都不为 0
grep -c "^module" *20261122_1400.v            # 网表模块数，应该和预期一致
grep -c "^\*D_NET" *20261122_1400.spef        # SPEF 里的网络数，几万到几十万都正常，0 就是错的
```

## 完整脚本 {#script}

下面这份脚本把八步压成六节。每一节开头写清**目的**和**检查点**，跑完一节看一眼检查点，不对就停，不要一口气跑到底。

为什么是六节而不是八节？因为"floorplan + 电源"总是在同一个会话里连着做（改边界就要重画电源），"route + 收尾 + 导出"也总是连着做（导出前必须填完 filler）。**分节的依据不是知识点，而是"哪几步必须一起重跑"**——这才是断点续跑的单位。

支撑"断点续跑"的不只是脚本写法，还有目录骨架本身：

:::fig pr-dir | 推荐的项目目录结构：scripts、db、out、rpt、log 各归各位，run/ 按时间戳留现场，右边是四条配套规矩。重点看第一条——脚本要能从头重跑。本课六节脚本 + 六个检查点的分法，就是照这个骨架组织的。
:::

从图里要看出什么：**目录结构是给"三个月后的你"用的**。哪一步失败就回到哪一节的存盘，配合同节末尾的检查点表，才叫真的能续跑。

脚本用 `tee` 把屏幕输出同时写进日志。`set -e` 那种"一条失败就退出"的机制在 Tcl 里没有默认开启，所以实际项目里会在每个关键命令后加 `if {[catch {...} err]} { puts $err; exit 1 }`。这一课为了可读性省略了，但你要知道它该在。

```tcl
# ============================================================
# 作用：ipa_top 的 ICC2 全流程（课程环境 9390 单元，约 22 分钟）
# 用法：icc2_shell -f run.tcl 2>&1 | tee log/run_$(date +%Y%m%d_%H%M).log
# 前提：PDK 路径已改；netlist/ 和 constraints/ 已就位
# ============================================================

# ---------- 第 1 节：环境与库（目的：确认库版本对；检查点：report_lib 有 Timing Data）----------
set PDK    /pdk/tsmc32                                    ;# PDK 根目录
set DESIGN ipa_top                                        ;# 设计名
set STAMP  [clock format [clock seconds] -format %Y%m%d_%H%M]  ;# 本次运行的时间戳，贯穿所有产物
file mkdir ./rpt ./out ./log                              ;# 建输出目录，已存在也不报错
open_lib $PDK/ndm/tsmc32_tt.ndm                           ;# 打开只读参考库（只为体检；也可不 open，由 -ref_libs 直接引用）
report_lib tsmc32_tt > rpt/00_lib.rpt                     ;# 库体检报告：必须有 Timing Data
read_parasitic_tech -tlup $PDK/tlup/tsmc32.tlup -layermap $PDK/tlup/layer.map -name tt  ;# 读 TLU+ 寄生模型
set_parasitic_parameters -early_spec tt -late_spec tt      ;# early/late 都用 tt，简化成单 corner 教学

# ---------- 第 2 节：建 block + 读网表（目的：单元全部 link 上；检查点：mismatch 为空）----------
create_lib ./work/${DESIGN}.lib -ref_libs [list $PDK/ndm/tsmc32_tt.ndm]  ;# 建设计库并挂参考库
create_block $DESIGN -lib ./work/${DESIGN}.lib            ;# 建 block
open_block ./work/${DESIGN}.lib:$DESIGN                   ;# 打开 block
read_verilog ./netlist/${DESIGN}.v                        ;# 读门级网表
link_block                                                ;# 链接到参考库
report_design_mismatch > rpt/01_mismatch.rpt              ;# 必须为空，否则停下修库
source ./constraints/${DESIGN}.sdc                        ;# 读约束
report_clocks > rpt/01_clocks.rpt                         ;# 时钟个数和周期要符合预期
check_timing -verbose > rpt/01_check_timing.rpt           ;# unconstrained endpoints 必须为 0

# ---------- 第 3 节：floorplan + 电源（目的：定边界、摆宏、通电网；检查点：PG 0 unconnected）----------
initialize_floorplan -core_utilization 0.65 -core_offset {10 10 10 10}  ;# 按 65% 利用率定 core
set_cell_location -coordinates {40 60}  -orientation MY [get_cells u_sram0]  ;# 摆 0 号 SRAM
set_cell_location -coordinates {40 140} -orientation R0 [get_cells u_sram1]  ;# 摆 1 号 SRAM
set_attribute [get_cells u_sram*] is_fixed true            ;# 所有 SRAM 锁定，布局时不许动
create_pg_ring_pattern ring_m5m6 -horizontal_layer M6 -horizontal_width 3 -horizontal_spacing 2 -vertical_layer M5 -vertical_width 3 -vertical_spacing 2  ;# 电源环模板
set_pg_strategy core_ring -core -pattern {{name: ring_m5m6} {nets: {VDD VSS}}}  ;# 套到 core 四边
compile_pg -strategies core_ring                           ;# 生成环的几何
create_power_straps -direction vertical -layer M5 -width 1.5 -spacing 2 -pitch 25 -nets {VDD VSS}  ;# 竖向支管
connect_pg_net -net VDD [get_pins -hier -filter "name==VDD"]  ;# 接 VDD 引脚
connect_pg_net -net VSS [get_pins -hier -filter "name==VSS"]  ;# 接 VSS 引脚
check_pg_connectivity > rpt/02_pg_conn.rpt                 ;# 0 unconnected 才继续
report_qor > rpt/02_qor_fp.rpt                             ;# 利用率、宏是否重叠
save_block                                                 ;# 存 floorplan 版本

# ---------- 第 4 节：place_opt（目的：摆单元+修 setup；检查点：WNS 收敛、利用率正常）----------
set_app_options -name place.coarse.continue_on_missing_scandef -value true  ;# 防止静默跳过布局
set_host_options -max_cores 8                              ;# 并行核数
place_opt > log/04_place.log                               ;# 布局 + 预 CTS 优化
report_qor > rpt/04_qor_place.rpt                          ;# WNS/TNS/面积/利用率
report_timing -max_paths 20 > rpt/04_timing_place.rpt       ;# 最差路径
report_congestion -hotspot > rpt/04_congestion.rpt          ;# 拥塞热点
save_block                                                 ;# 存布局版本

# ---------- 第 5 节：clock_opt（目的：建树+修 hold；检查点：skew 达标、hold 可控）----------
set_app_options -name cts.optimize.delay -value true        ;# 建树同时优化延迟
clock_opt -only_cts > log/05_cts.log                        ;# 只建树
report_clock_timing -type skew > rpt/05_skew.rpt            ;# skew 报告
report_clock_timing -type latency > rpt/05_latency.rpt      ;# insertion delay
save_block                                                 ;# 存纯树版本，便于回退
clock_opt -only_hold_time > log/05_hold.log                 ;# 修 hold
report_timing -delay_type min -max_paths 20 > rpt/05_hold.rpt  ;# hold 最差路径
save_block                                                 ;# 存 CTS 完成版本

# ---------- 第 6 节：route + 收尾 + 导出（目的：连线、清零 DRC、交四件套；检查点：DRC 0、四文件同戳）----------
route_auto > log/06_route.log                               ;# 全局 + 详细布线
check_routes > rpt/06_drc_auto.rpt                          ;# 首轮 DRC
route_opt > log/06_route_opt.log                            ;# 真实寄生下优化时序
check_routes > rpt/06_drc_opt.rpt                           ;# 优化后 DRC
route_detail -incremental > rpt/06_drc_detail.rpt           ;# 磨残余 DRC
insert_stdcell_filler -cell_without_metal {FILL64 FILL32 FILL16 FILL8 FILL4 FILL2 FILL1}  ;# 填 filler
connect_pg_net -net VDD [get_pins -hier -filter "name==VDD"]  ;# filler 的 VDD
connect_pg_net -net VSS [get_pins -hier -filter "name==VSS"]  ;# filler 的 VSS
check_routes > rpt/07_drc_final.rpt                          ;# 最终 DRC
report_timing -max_paths 50 > rpt/07_timing.rpt               ;# 最终时序
report_qor > rpt/07_qor.rpt                                  ;# 最终 QoR
write_def ./out/${DESIGN}_${STAMP}.def                        ;# 版图
write_verilog ./out/${DESIGN}_${STAMP}.v                      ;# 网表
write_sdc ./out/${DESIGN}_${STAMP}.sdc                        ;# 约束
write_parasitics -format SPEF -output ./out/${DESIGN}_${STAMP}.spef  ;# 寄生
```

六节各自的"停或继续"标准：

| 节 | 目的 | 检查点 | 不通过怎么办 |
|---|---|---|---|
| 1 | 库和寄生就位 | `report_lib` 有 Timing Data | 回 04-01 重建 NDM |
| 2 | 网表全部 link | `report_design_mismatch` 为空 | 补库或改网表，别硬跑 |
| 3 | 边界、宏、电源 | PG 0 unconnected；无宏重叠 | 改 floorplan，重跑本节 |
| 4 | 布局和 setup | WNS 收敛、利用率涨幅 <15% | 放宽约束或放大 core |
| 5 | 时钟树 | skew ≤ 目标 1.5 倍、hold 可控 | 改 CTS 约束，回本节 |
| 6 | 布线和交付 | DRC 0、四文件同戳 | 先修 DRC，再修时序 |

## 实测数据（万门设计，9390 单元） {#real}

这组数字来自课程环境的一次完整跑通（**课程环境实测**，单机，CPU 型号不计，工具版本见 run.log 头部）。设计是 IPA 图像处理加速器，6 个 SRAM，9390 个标准单元。

| 阶段 | 耗时 | 结果 |
|---|---|---|
| `place_opt` | 3.5 min | 单元数 9390 → 12026（+2636，+28%） |
| `clock_opt` | 9.5 min | hold 从 −10 ns 量级收敛到 −0.07 ns |
| `route_auto` | 1.7 min | **首轮 DRC = 0** |
| `route_opt` | 2.3 min | DRC 保持 0，setup WNS +1.00 ns |
| `route_detail` ×5 | 2.2 min | DRC 仍 0 |
| **合计** | **21.7 min** | die 222.5×222.2 µm，利用率 49.8% |

四个值得记住的结论：

**第一，`route_auto` 首轮 DRC = 0 是 floorplan 和布局的功劳。** 布线器不是"修 DRC 的"，它只是把已有的空间用起来。空间够，首轮就干净；空间不够，磨十遍也磨不干净。所以看到首轮几千个 DRC，正确反应是回第 2 步，不是加 `route_detail` 的迭代次数。

**第二，`clock_opt` 占了 44% 的时间（9.5/21.7）。** 万门级设计里 CTS 就是最慢的一步，因为它要解 hold 这个"必须精确"的问题。给 CTS 留时间，不要指望它两分钟跑完。

**第三，place 阶段单元涨 28% 是正常的。** buffer、时钟树单元、驱动增强都会加单元。超过 50% 才需要怀疑：约束是不是设得太紧（比如周期给了一半）、库是不是只有慢速单元。

**第四，时间不能线性外推。** 9390 个单元 22 分钟，不代表 93900 个单元 220 分钟。布局和布线的复杂度大约随单元数超线性增长，10 万门设计跑几小时到一天都正常。**"万门 22 分钟"只能用来判断"我这台机器是不是慢得离谱"，不能用来给项目排期。**

## 和 Innovus 流程的对应 {#compare}

| 步骤 | Innovus | ICC2 | 差异要点 |
|---|---|---|---|
| 建库 | 不需要 | `create_workspace` + `commit_workspace` | ICC2 多一道库关 |
| 建设计 | `init_design` | `create_lib` + `create_block` | ICC2 库和 block 分开 |
| 打开 | `restoreDesign x.enc` | `open_lib` + `open_block` | `.enc` 是目录，block 在库里 |
| 读网表 | `read_netlist` | `read_verilog` + `link_block` | ICC2 要显式 link |
| 约束 | `read_sdc` | `source x.sdc` | 基本一致，检查命令不同 |
| 场景 | `create_analysis_view` | `create_scenario` | MMMC vs scenario |
| Floorplan | `floorPlan` | `initialize_floorplan` | ICC1 才叫 `create_floorplan` |
| 摆宏 | `placeInstance` | `set_cell_location` | 都要再设 fixed |
| 电源 | `addRing` / `addStripe` | pattern + `compile_pg` | ICC2 分"模板/策略/生成"三步 |
| 布局 | `place_opt_design` | `place_opt` | 内部阶段划分不同 |
| CTS | `ccopt_design` | `clock_opt -only_cts` | Innovus 用 ccopt 引擎 |
| 布线 | `routeDesign` | `route_auto` | 都是全局+详细 |
| 后优 | `optDesign -postRoute` | `route_opt` | ICC2 把优化并进 route 命令族 |
| 收尾 | `fillCore` 类命令 | `insert_stdcell_filler` | 名字不同，逻辑相同 |
| 导出 | `defOut` / `saveNetlist` | `write_def` / `write_verilog` | 一一对应 |

三个结构性差异，比命令名更重要：

1. **库的管理方式**：Innovus 散着读 LEF/LIB，ICC2 必须先合成 NDM。这决定了 ICC2 项目多一个"建库"角色。
2. **场景的表达**：Innovus 的 MMMC 是 mode/corner/view 三层；ICC2 的 scenario 是一层打包。写约束时不要照搬。
3. **阶段边界**：Innovus 用 `optDesign -preCTS/-postCTS/-postRoute` 在一个命令里切阶段；ICC2 用不同命令（`place_opt`/`clock_opt`/`route_opt`）切。所以 ICC2 的 run 脚本天然是"一段一个命令"，更好断点续跑。

把一条 Innovus 流程迁到 ICC2，正确顺序是三步，不是逐行翻译脚本：

1. **先迁动作**：按上表把每个阶段的主命令换掉，库换成 NDM，先让它"能跑"。
2. **再迁数据**：MMMC 的 view 改成 scenario，约束里的 corner 名字对齐，寄生模型挂对。
3. **最后比 QoR**：同样的网表、同样的约束、同样的库 corner，比较 WNS/TNS/面积/单元数。差异超过 10% 就要找原因，而不是接受"工具不同所以不一样"。

逐行翻译是最容易出事的做法：两边的默认值不同，一条命令翻译对了，隐含的默认参数却变了，最后 QoR 差一大截还找不到原因。

## 每一步的检查点清单（可打印） {#checklist}

这张表的用法不是"跑完看一眼"，而是**把每一行的"通过标准"写成脚本里的断言**。人眼会疲劳，断言不会。

比如第 2 步的"mismatch 为空"，可以在脚本里写成：

```tcl
# 作用：把 link 检查做成断言，报告里出现未解析引用就退出
# 用法：放在 link_block 之后、initialize_floorplan 之前
redirect rpt/01_mismatch.rpt {report_design_mismatch}   ;# 把报告内容写进文件，便于程序判断
set fp [open rpt/01_mismatch.rpt r]                     ;# 以只读方式打开报告
set txt [read $fp]                                      ;# 一次读入全部内容
close $fp                                               ;# 关闭文件，养成习惯
if {[regexp {unresolved|not found|mismatch} $txt]} {     ;# 出现这几类词就说明有单元没对上
    puts "ERROR: unresolved references, see rpt/01_mismatch.rpt"  ;# 打印提示，指明去哪看
    exit 1                                              ;# 非零退出码，外层脚本能感知失败
}
```

同理，"PG 0 unconnected""DRC = 0"都可以先 `redirect` 到报告，再用 `regexp` 判断关键词。**判断标准要落到"报告里有没有这个词"，而不是"我觉得应该没问题"。**

常见报错：`write_def` 报 DEF 版本不兼容，通常是下游工具只认 5.6、你导了 5.7（或反过来），用 `-version` 指定；`write_parasitics` 报没有寄生数据，通常是还没跑布线或没做寄生提取，别在布局阶段导出 SPEF。

| 阶段 | 产物 | 检查命令 | 通过标准 |
|---|---|---|---|
| 0 准备 | 检查记录 | `report_lib` / `check_timing` | Timing Data 存在；unconstrained = 0 |
| 1 建 block | block | `report_design_mismatch` | 输出为空 |
| 2 floorplan | 边界 + 宏 | `report_qor` / GUI | 无重叠；利用率接近设定值 |
| 3 电源 | PG 网络 | `check_pg_connectivity` / `check_pg_drc` | 0 unconnected；无 DRC |
| 4 place | 布局 | `report_qor` / `report_congestion` | WNS 可控；无大面积热点 |
| 5 CTS | 时钟树 | `report_clock_timing` | skew ≤ 目标 1.5 倍 |
| 6 route | 版图 | `check_routes` | DRC 0（或只剩可解释的少数） |
| 7 收尾 | 最终数据 | `check_routes` / `report_qor` | DRC 0；时序达标 |
| 8 导出 | 四件套 | `ls` / `grep` | 四文件同戳、非空 |

这张表里最容易被跳过的是第 0 步和第 3 步。第 0 步看起来"什么都没做"，但库和约束的问题 100% 会在这之后的某一步以别的形式爆出来；第 3 步的 `check_pg_connectivity` 输出很长，很多人直接滚过去，最后在 IR drop 或 ERC 上翻车。

一个实用习惯：**每次跑完把这张表的"通过标准"抄进当日的工作记录**，写清"实际值/标准值"。一周后回头看，你能立刻知道哪一步开始变差，而不是只剩一句"当时好像还行"。

## 工作中怎么用：这条流程在项目里的位置 {#in-work}

**谁做**：PR 工程师。万门级设计通常一个人从头跑到尾；十万门以上会拆成"floorplan + 电源"和"place 之后"两个人，交接点就在 `save_block`。

**输入**：综合后的网表、SDC、NDM 库、TLU+、floorplan 方案（宏坐标表）、电源方案（ring/stripe 宽度间距）。

**输出**：`final.def` / `final.v` / `final.spef` / `final.sdc` 四件套 + 一套报告。交给 STA 签核、PV 做 DRC/LVS、封装做 bump 规划。

**评审会看**：利用率、WNS/TNS、DRC 数、单元增长比例、CTS 的 skew 和 insertion delay。任何一个明显偏离同类项目，都要给出解释。

**做错了会怎样**：这条流程的错误是**放大**的。floorplan core 小 10%，布线阶段多花两天；电源少打 via，IR drop 签核不过，回退到第 3 步重跑全部；网表和 SPEF 不同步，STA 结论作废，整轮重来。所以每一步的检查点不是形式，是止损。

:::lab 动手：把前四步跑通并留下证据
**任务**：在 `~/backend_lab/icc2/` 下，用一个 9390 单元的设计跑完第 0~4 步（准备、建 block、floorplan、电源、place_opt），产出四份报告和一个可打开的 block。

**步骤**：

1. 复制 `run.tcl` 到 `myrun.tcl`，只改 `PDK` 和 `DESIGN` 两个变量；在头部加一行注释写清库版本。
2. 跑到第 2 节结束就停，检查 `rpt/01_mismatch.rpt` 是否为空，`rpt/01_clocks.rpt` 里有几个时钟。
3. 继续跑第 3 节，`check_pg_connectivity` 必须是 0 unconnected；不是 0 就用 `report_pg_connectivity -verbose` 找是哪个区域。
4. 跑第 4 节，记录三个数：place 前单元数、place 后单元数、利用率。算出增长百分比。
5. 把三个数和你算的 core 面积（9390×2.6÷0.65 再开方）写进 `lab04-02.md`。

**过关标准**：mismatch 为空；PG 0 unconnected；单元增长在 20%~35%；能解释"为什么最终利用率比 floorplan 设的 65% 低"。

**如果环境里没有 ICC2 license**：用课程提供的 `rpt/` 全套报告做第 2~5 步的读数练习，并把 `run.tcl` 逐行加注释——能读懂脚本，等价于跑过一遍。
:::

:::quiz
`place_opt` 之前为什么要先读 TLU+？|优化器要算线延迟，没有寄生模型就报 `NEX-018`，进而导致 `OPT-041` 场景创建失败。
`report_design_mismatch` 不为空时为什么不能继续？|有单元没 link 上，它没有时序模型和版图，相关路径全部失真，后面的优化结果不可信。
为什么 `place_opt` 可能几秒钟跑完且不报错？|缺 scan def 时布局器默认跳过布局，只报 warning。要设 `place.coarse.continue_on_missing_scandef` 为 true。
CTS 后 hold 出现 −10 ns，是不是树建坏了？|多数不是。是时钟从 ideal 切成 propagated 后，原来藏着的 hold 违例暴露；看违例是否集中在相邻叶子。
`route_auto` 首轮 DRC = 0 说明什么？|说明 floorplan 和布局留够了空间。首轮几千个 DRC 应该回第 2 步改布局，而不是反复磨布线。
为什么电源条宽度不能随便减？|宽度减半电阻翻倍，IR drop 翻倍。200µm 长、4µm 宽的 M5 条是 2.5Ω，20mA 就有 50mV 压降，已经是 5% 预算。
filler 为什么必须最后填、填完还要查 DRC？|filler 会占掉剩余空间、引入新的 spacing 违例，并需要重新接电源；先填会挡住优化和布线。
四份导出文件为什么要用同一个时间戳？|网表、SPEF、SDC、DEF 必须是同一版设计；差一天就会导致 STA 读到不匹配的延迟数据，结果完全失真。
:::

:::check
- 能按顺序说出八个阶段，以及每个阶段的产物
- 能独立完成"库/约束/网表"三项准备检查，并解释每项不通过的后果
- 能手算 core 面积：单元数 × 平均面积 ÷ 利用率，再开方
- 能说出 `place_opt` 内部的四个阶段，以及单元增长 20%~35% 为什么正常
- 能解释 CTS 后 hold 变差的原因，并知道先跑 hold 优化再判断
- 能按 DRC 类型判断"该磨布线还是回布局"
- 能写出四份导出文件及各自的下游
- 能在 run 脚本里指出六个检查点，并说清不通过时该回到哪一步
:::
