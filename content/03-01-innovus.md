---
id: 03-01-innovus
no: 12
stage: 3
title: Innovus 起步：一个后端工具到底在管什么
en: Getting Started with Innovus
hours: 2
minutes: 35
tags: [Innovus, 工具, 数据库]
summary: 后端工具不是"画图软件"，它管的是一个巨大的数据库、一个优化引擎和一堆报告。这一课讲清数据库里存了什么、为什么必须用命令行、第一个能跑通的命令序列，以及 Innovus 与 ICC2 的十六组命令对应。
---

## 工具在管什么 {#what}

:::goal 能说出 Innovus 里"设计、库、约束"三类数据各自存在哪、用一条 `dbGet` 查出来，并用纯命令行跑通一次初始化到存盘。
:::

一个布局布线工具（Innovus / ICC2）本质是三样东西：

1. **一个数据库**：几万个单元、几十万条连线、几百层几何图形，全在里面。
2. **一个优化引擎**：决定"放哪、怎么连、插不插缓冲器"。
3. **一堆报告**：时序、拥塞、DRC、面积、功耗。

你敲的每条命令，都是在**改数据库**或者**让引擎干活**，然后**读报告**判断下一步。三件事循环，就是整个后端工作。

数据库里其实装的是"一设计 + 三份资料"：

| 组成 | 内容 | 从哪来 | 少了会怎样 |
|---|---|---|---|
| 设计（design） | 单元实例、连线、引脚、电源网络 | `.v` 网表 + `.def` | 没有东西可摆 |
| 库（library） | 每个单元的尺寸、引脚、延迟 | `.lef` + `.lib`/`.db` | 不知道单元长什么样 |
| 约束（constraint） | 时钟、IO 延迟、例外 | `.sdc` / MMMC | 不知道要多快，优化没目标 |
| 工艺（tech） | 层、线宽、间距、via | tech LEF + TLU+ | 不知道怎么画线 |

:::term Innovus | Cadence 的布局布线工具
数字后端两大主流 PR（Place & Route，布局布线）工具之一，另一个是 Synopsys 的 ICC2。命令语言是 Tcl，所有操作都能写成脚本。

课程阶段三用 40nm 走 Innovus，阶段四用 32nm 走 ICC2。**两套工具，一套方法论**：先想清"这一步在改什么数据"，再查命令名。
:::

:::term Instance | 实例
网表里"用了一个单元"这件事的实体。`U1234` 是一个实例，它的类型（cell）是 `NAND2_X1`，位置是 (120.5, 340.2)。

**cell 是"图纸"，instance 是"按图纸造出来的那一颗"**：一个 `INV_X1` 可以被实例化一万次，库里的定义只有一份。
:::

## GUI 和命令行：到底用哪个 {#gui}

新手最容易犯的错：以为要用鼠标拖。

真实情况：

- **GUI 用来"看"**：看布局、看拥塞热图、看某条路径的走向、看 flyline。
- **命令行/脚本用来"做"**：所有设置、所有流程，都写成 `.tcl` 脚本跑。

原因不是"显得专业"，是三个很实际的工程需求：

**1. 可重复。** 同一份脚本，今天跑和下周跑结果一样；换个同事跑，结果也一样。用鼠标点的流程，第二次就复现不出来——你不知道自己当时点了哪几个按钮。

**2. 可存档。** 脚本是文本，能进版本管理（git），能 diff 出"这一版改了哪三个参数"。数据库存档（`.enc`）是二进制，只能整体回退，看不出改了什么。

**3. 可批量。** 想试 6 组利用率（0.60/0.65/0.70/0.75/0.80/0.85），脚本套一层循环就跑完；用 GUI 你要点 6 遍，还得手工记录每次的结果。

```bash
# 作用：两种启动方式，批处理跑脚本 vs 带界面调试
# 用法：在 pnr/ 目录下执行；run.tcl 里写完整流程，日志重定向到 log/
innovus -no_gui -files run.tcl -log log/run_0901.log -overwrite   # 无界面跑脚本，服务器上跑批用这个
innovus                                                          # 带 GUI 启动，交互式调试用；进去后 source run.tcl
```

参数逐个说：

- `-no_gui`：不启动图形界面。省内存、能在没有显示器的服务器上跑，**这是正式跑流程的唯一方式**。
- `-files run.tcl`：启动后自动执行这个脚本。可以跟多个文件，按顺序执行。
- `-log log/xxx.log`：把终端输出写进日志。**必须给**，否则出问题没有证据。
- `-overwrite`：允许覆盖同名日志（不加时工具会拒绝写已存在的日志，批处理会直接退出）。

:::term Batch Mode | 批处理模式
不给图形界面、直接跑脚本的运行方式（`-no_gui`）。特点是可排队、可并行、日志完整。

公司里的常规做法：本地 GUI 调脚本，提交到计算集群用批处理跑全流程。**你写的脚本要能在两种模式下都跑通**，这是基本要求。
:::

:::scene 凌晨两点，GUI 断了，跑了 5 小时的流程没了
你在自己电脑上开着 GUI 跑布线，跑了 5 小时到 80%。凌晨两点 VPN 断了一下，X11 转发断开，进程跟着被杀。日志只写到一半，数据库没存。

第二天早上你面对两个选择：重跑 5 小时，或者跟组长解释为什么延期。

老手的做法从一开始就不一样：

```bash
# 作用：把长任务丢到后台，断线也不影响
# 用法：在服务器上执行；nohup 让进程脱离终端，日志照样落盘
nohup innovus -no_gui -files run_route.tcl -log log/route_0901.log -overwrite > /dev/null 2>&1 &
```

公司里更常见的是提交到作业队列（LSF 的 `bsub`、SGE 的 `qsub`）：进程跑在计算节点上，本来就不跟着你的终端。命令不同，原则一样——**长任务不能挂在你的一次 SSH 会话上**。

配合脚本里每阶段 `saveDesign`，最坏情况也只是从上一个存档重跑一小时，而不是从零开始。
:::

## 数据库里有什么 {#db}

打开一个设计后，数据库里至少存了这些：

| 内容 | 说明 | 对应报告 |
|---|---|---|
| 单元实例 | 每个标准单元的类型、坐标、朝向 | `report_area` |
| 连线（net） | 谁连谁、走哪层、多长 | `reportCongestion -hotSpot` |
| 引脚（pin/terminal） | IO 位置、方向、所在层 | `dbGet top.terms` |
| 电源网络 | ring / stripe / rail | `verifyPowerVia` |
| 时序图 | 每条路径的门延迟、线延迟 | `report_timing` |
| 约束 | 时钟、IO 延迟、false path | `report_clocks` |

### 用 `dbGet` 直接查数据库

Innovus 的所有数据都能用 `dbGet` 查。它的语法是 `dbGet 对象.属性`，可以在 Tcl 里当普通命令用：

```tcl
# 作用：不打开 GUI，直接从数据库里数单元、查坐标、找特定实例
# 用法：init_design 之后在 Innovus 命令行里敲；输出格式随版本略有差异，语义一致

dbGet top.insts                    # 返回所有实例的句柄列表（一长串 0x... 的指针）
llength [dbGet top.insts]          # 数一数有多少个实例，这是"单元数"的来源
dbGet top.insts.name               # 只要名字，返回 u_core/u_alu/u_alu/add_1 这样的列表
dbGet -p top.insts.name u_sram0    # 按名字过滤，只返回叫 u_sram0 的那个实例句柄
dbGet [dbGet -p top.insts.name u_sram0].box   # 再取它的坐标框，四个数：llx lly urx ury
dbGet top.nets.name                # 所有连线的名字，用来确认某个 net 在不在
```

为什么要会这个：报告不够用时，`dbGet` 是唯一能"自己造一份报告"的办法。比如"列出所有面积大于 1000µm² 的实例"，报告命令里没有，一行 `dbGet` 加 `foreach` 就能出来。

:::term dbGet | 数据库查询命令
Innovus 的 Tcl 数据库接口：`dbGet 对象.属性` 取数据，`dbSet 对象.属性 值` 改数据，`-p` 用来按值过滤。

**它相当于直接读内存里的数据库**，比报告命令灵活，也比报告命令危险：`dbSet` 改错了不会有人拦你。
:::

## 第一个能跑通的序列 {#first}

下面这一串是 Innovus 的"最小可运行流程"：从零到有一个能存盘的设计。**顺序不能乱**，每一段的作用写在注释里。

```tcl
# 作用：Innovus 从零初始化一个设计的完整序列（MMMC 流程）
# 用法：innovus -no_gui -files init.tcl；所有相对路径以 pnr/ 为当前目录

# ---- 1. 读设计数据（此时还没有数据库）----
read_verilog ../syn/netlist/ipa_top.v            # 读门级网表，建立逻辑连接关系
read_lef ../lib/lef/tsmc40_tech.lef              # 先读 tech LEF：有哪些层、线宽、间距、via
read_lef ../lib/lef/tsmc40_stdcell.lef           # 再读单元 LEF：每个单元的尺寸和引脚位置
read_lef ../lib/lef/sram_2048x64.lef             # 宏单元 LEF，用不到 SRAM 时可以省
read_mmmc ../constraints/mmmc.tcl                # 读 MMMC：库集合、约束模式、分析视图三件套

# ---- 2. 建数据库（把上面这些绑成一个设计）----
set init_top_cell ipa_top                        # 指定顶层单元名，必须和网表里的 module 一致
init_design                                      # 建立内部数据库；这一步之后才能真正操作设计

# ---- 3. 灌入已有的物理信息（可选）----
read_def ../def/02_fp.def                        # 有现成 floorplan 就灌进来；没有则从空 die 开始

# ---- 4. 自检：确认读对了 ----
report_area                                      # 总面积、单元数；为 0 说明网表或库没读进来
report_clocks                                    # 时钟列出来了吗？没有就是 MMMC/SDC 没生效
checkDesign -all                                 # 一致性检查：悬空引脚、未连接端口、非法实例
check_timing -include unconstrained              # 有没有完全没约束的端点

# ---- 5. 存盘：这一步不做，前面全白干 ----
saveDesign db/01_init.enc                        # 二进制存档，实际生成的目录叫 01_init.enc.dat/
```

几点必须解释清楚：

- **`read_lef` 要读两次**：tech LEF 定"规则"，cell LEF 定"形状"。只读后者，工具知道单元多大但不知道怎么画线。
- **`read_mmmc` 替代了 `read_sdc`**：MMMC（Multi-Mode Multi-Corner，多模式多工艺角）把"用哪套库 + 用哪份约束 + 看哪个 corner"打包成分析视图。小项目也可以直接 `read_sdc`，但公司流程基本都用 MMMC。
- **`read_def` 必须在 `init_design` 之后**：`init_design` 建空数据库，`read_def` 往里灌坐标。顺序反了会报"没有设计"。
- **`checkDesign` 不要跳**：它会把"某个输入端口没接驱动"这种问题提前暴露，比在布线阶段发现便宜一百倍。

:::pitfall 忘了 saveDesign，几小时白干
Innovus 不会自动存。跑到一半崩溃、或者你自己想回退，没有存盘就只能从零开始。

**规矩：每完成一个阶段就 `saveDesign db/NN_阶段名.enc`。** 出问题可以 `restoreDesign db/05_cts.enc.dat ipa_top` 回到上一个可用状态。

`NN` 用序号，方便排序和回退。存档目录会越来越大（一个设计几个 GB），定期清理中间版本，但**每个阶段的最后一版必须留**。
:::

:::term .enc | Innovus 设计数据库
Innovus 自己的二进制存盘格式，实际是一个目录（`01_init.enc/` 里面若干文件）。存了设计的完整状态：布局、布线、约束、工具设置。

和它对应的是 ICC2 的 block 数据库（NDM 库 + `save_block`）。格式不同，作用相同：**给流程留一个可回退的锚点。**
:::

:::pitfall 脚本里用了相对路径，换个目录就跑不了
现象：在 `pnr/` 下跑得好好的脚本，`cd` 到别处再跑，报 `Cannot open file ../lib/...`。

原因：路径是相对当前工作目录的。批处理系统提交任务时，工作目录经常不是你以为的那个。

怎么改：脚本开头统一 `set PRJ [pwd]`，所有路径写成 `$PRJ/../lib/...`；或者在启动脚本里先 `cd` 到固定目录。**路径问题占了新手报错的一半**，一次性写对能省很多时间。
:::

## 与 ICC2 的对应关系 {#icc2}

工具不同，动作一样。这张表建议存下来，面试前看一遍：

| 动作 | Innovus | ICC2 |
|---|---|---|
| 启动并跑脚本 | `innovus -no_gui -files run.tcl` | `icc2_shell -f run.tcl` |
| 读网表 | `read_verilog` / `read_netlist` | `read_verilog` |
| 读物理库 | `read_lef`（tech + cell 各一次） | `read_lef`（或建 NDM 时已包含） |
| 读约束 | `read_mmmc` / `read_sdc` | `read_sdc` |
| 初始化设计 | `init_design` | `link_block` |
| 存盘 | `saveDesign db/x.enc` | `save_block` |
| 布局规划 | `floorPlan` | `initialize_floorplan` |
| 布局 | `place_opt_design` | `place_opt` |
| 时钟树 | `ccopt_design` | `clock_opt` |
| 布线 | `routeDesign` | `route_auto` |
| 布线后优化 | `optDesign -postRoute` | `route_opt` |
| 时序报告 | `report_timing` | `report_timing` |
| QoR 汇总 | `report_qor` | `report_qor` |
| 面积报告 | `report_area` | `report_area` |
| DRC 检查 | `verify_drc` | `check_routes` |
| 导出 DEF | `defOut -floorplan` | `write_def` |
| 导出 GDSII | `streamOut` | `write_gds` |

两点说明：

- 命令名在不同版本里会有细微差别（尤其 ICC2 的 application options 体系），上表是主流版本的动作对应，**具体敲之前用 `man` 或 `help` 确认一次**。
- 真正相通的是**顺序和判断标准**：先读库再 init、布局前必须有 floorplan、CTS 后必须看 skew。这些换工具也不会变。

:::term MMMC | 多模式多工艺角
Multi-Mode Multi-Corner。把"用哪套时序库（library set）+ 用哪份约束（constraint mode）+ 看哪个 corner（analysis view）"组合成若干分析视图，一次性管住所有场景。

典型配置：`func_ss`（功能模式 + 慢角，查 setup）、`func_ff`（功能模式 + 快角，查 hold）、`scan_ss`（测试模式 + 慢角）。**少一个视图，就少一类签核场景。**
:::

:::lab 动手：用纯命令行跑通一次初始化
**任务**：不用 GUI，把上面的序列跑一遍，产出 `db/01_init.enc`，并用 `dbGet` 报出单元数。

**步骤**：

```bash
# 作用：无界面启动 Innovus 并执行初始化脚本，日志落盘
# 用法：在 pnr/ 目录下执行；先确认 ../syn/netlist/ipa_top.v 存在
mkdir -p db log                                              # 建存档和日志目录
innovus -no_gui -files init.tcl -log log/init.log -overwrite  # 跑脚本，全程无界面
grep -i "error" log/init.log                                  # 先看有没有 error（warning 可以后看）
ls db/                                                        # 确认 01_init.enc.dat 目录生成
```

```tcl
# 作用：在 Innovus 里恢复存档并查数据库，验证存盘真的有效
# 用法：重新启动 innovus 后执行，或写在下一个脚本开头
restoreDesign db/01_init.enc.dat ipa_top     # 恢复存档；第二个参数是顶层名
puts "instances = [llength [dbGet top.insts]]"   # 打印实例数，应等于网表里的单元数
puts "nets      = [llength [dbGet top.nets]]"    # 打印连线数
```

**过关标准**：三个数对得上——`dbGet` 数出的实例数与 `report_area` 里的单元数一致、`report_clocks` 能看到时钟、日志里 error 数为 0。任何一项不对，先回去查输入，不要往下做 floorplan。
:::

:::quiz
为什么后端流程强调"写脚本"而不是用 GUI 点？|因为要可复现、可存档、可批量：一次运行几小时、参数几十个，只有脚本能重跑、能 diff、能循环扫参数。
`-no_gui` 和 `-files` 分别是什么意思？|`-no_gui` 不启动图形界面（服务器批处理）；`-files` 启动后自动执行指定的 Tcl 脚本。
`saveDesign` 为什么每个阶段都要做？|工具不会自动存盘，崩溃或需要回退时没有存档就得从头再来；每个阶段留一版才能精确回退。
Innovus 的 `.enc` 和 ICC2 的数据库有什么区别？|格式不同（Cadence 私有目录 vs Synopsys NDM + block），作用相同：保存设计的完整状态。
`init_design` 做了什么？|把网表、物理库、时序库、约束绑定在一起，建立可操作的内部数据库；之后才能读 DEF、做布局。
为什么 `read_def` 要放在 `init_design` 之后？|`init_design` 建空数据库，`read_def` 往已有设计里灌坐标；反了就没有设计可灌。
`dbGet top.insts` 和 `dbGet top.insts.name` 有什么区别？|前者返回实例句柄列表（对象指针），后者返回名字列表；要取坐标得先拿句柄再取 `.box`。
:::

:::check
- 能说出后端工具管的三样东西（数据库、引擎、报告），以及数据库里的"一设计三资料"
- 能说出必须用命令行的三个理由：可重复、可存档、可批量
- 知道 `-no_gui`、`-files`、`-log`、`-overwrite` 四个参数各自的作用
- 能按正确顺序写出初始化序列，并说清 `read_lef` 为什么读两次
- 能用 `dbGet` 数出实例数、查出某个实例的坐标
- 记得每个阶段结束必须 `saveDesign`，并知道怎么 `restoreDesign` 回退
- 能背出至少 10 组 Innovus / ICC2 命令对应
:::
