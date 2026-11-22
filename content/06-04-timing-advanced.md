---
id: 06-04-timing-advanced
no: 39
stage: 6
title: 高级时序分析：多 corner、报告瓶颈与噪声余量
en: Advanced Timing Analysis
hours: 5
minutes: 50
tags: [PVT corner, derate, report_bottleneck, SI, noise]
summary: 课件里「时序分析 1/2」讲的是签核时真正会用到的手法：为什么要跑多个 corner、global 与 local 的区别、怎么用 report_bottleneck 一次看清所有瓶颈、以及串扰噪声为什么必须留余量。
status: live
---

## 一个 WNS 数字，签不了字 {#why}

:::goal 学完这一课，你能独立组织一次多 corner 时序签核：说清每个 corner 查什么、算清 derate 与 CPPR 对 slack 的影响、用两份聚合报告定位瓶颈，并把结果写成评审会能直接看的汇总表。
:::

时序分析的基础是 `slack = required − arrival`，这条公式在 05-02 和 06-01 已经拆得很细。但真实签核面对的从来不是"一条路径、一个条件"，而是：

- 工艺有 SS/TT/FF，电压有 0.99V/1.10V，温度有 −40℃/25℃/125℃，组合出十几个 corner；
- 同一颗芯片内部，不同位置的晶体管也有快慢差异，要在 corner 之上再加 derate（降额）；
- 线之间有耦合电容，邻居一翻转，victim 的延迟就变；
- 违例不是一条，是几千条，必须先聚合再决定从哪下手。

只会看单条路径的 slack，到了签核会上会被三个问题问住：**这个数是在哪个 corner 下跑的？derate 加了多少？另一个 corner 呢？**

:::scene 周五下午，四个 corner 给出四个结论
明天上午 signoff review。你手上四份 PT 报告：

| corner | WNS | hold 最差 | 违例条数 |
|---|---|---|---|
| `ss_125c_0p99v` | −0.08ns | +0.03ns | 214 |
| `ss_m40c_0p99v` | −0.21ns | +0.01ns | 587 |
| `ff_m40c_1p10v` | +0.15ns | −0.12ns | 96 |
| `ff_125c_1p10v` | +0.19ns | −0.09ns | 61 |

leader 问："哪个 corner 签字？−0.21 那 587 条是什么类型？为什么低温和高温都要跑？ff 角 setup 是正的，能不能说明没问题？"

你如果只会回答"ss 最差"，这关就过不去。这一课就是把这张表读成一句结论：**setup 由 ss_m40c 卡住、hold 由 ff_m40c 卡住，两类违例要分开修，四个角一个都不能少。**
:::

## PVT 三角：三个变量，不是三个开关 {#pvt}

**PVT** 是 Process（工艺）、Voltage（电压）、Temperature（温度）的缩写。三者对延迟的影响方向不同，而且**不是简单叠加**。

| 变量 | 变"慢"的方向 | 机理 |
|---|---|---|
| Process | SS（慢片） | 沟道掺杂、氧化层厚度偏离，驱动电流变小 |
| Voltage | 低电压 | 过驱动电压 `Vgs − Vth` 变小，电流下降 |
| Temperature | 不一定 | 迁移率随温度升高而下降（变慢），但阈值电压随温度升高而下降（变快） |

温度这一栏是新人最容易想错的。经典结论是"温度越高越慢"，但在低电压、先进工艺下会出现 **temperature inversion（温度反转）**：`Vth` 下降带来的收益超过了迁移率下降的损失，**高温反而更快**。所以 foundry 的 SS 角通常同时给 `−40℃` 和 `125℃` 两档，不是重复劳动——哪一个更慢，必须实算。

电压也不只是"标称值上下浮动"。芯片内部因为 IR drop，实际到达单元的电压可能比电源引脚低 5%~10%；签核用的 0.99V 已经是"电源最差 + 一定压降"的结果。如果 IR drop 分析发现某块区域压降更大，那一块要单独用更低的电压再跑一次，不能拿全局 corner 蒙混过去。

:::term PVT | 工艺-电压-温度
Process、Voltage、Temperature 三个工作条件的组合。签核要覆盖它们的极端组合，因为芯片在真实环境里会遇到全部范围，而延迟对三者的敏感度不同。
:::

:::term Corner | 工艺角
一组固定的 PVT 取值，如 `ss_125c_0p99v`。命名规则通常是"工艺_温度_电压"。SS 查 setup，FF 查 hold，但"最差"的那个角只能通过实算确定。
:::

## global corner 与 local corner：同一颗芯片也不均匀 {#ocv}

Corner 描述的是"整颗芯片都是慢片"或"整颗都是快片"。但真实芯片内部，同一个 die 上不同位置的晶体管也有差异：光刻邻近效应、掺杂波动、温度梯度，都会让这一片的单元比那一片慢 3%~8%。

这种片内差异叫 **OCV（On-Chip Variation，片内偏差）**。签核的处理方式是在 global corner 之上再加一层 **derate（降额）**：

- 对"晚到"的路径（setup 的 data、launch clock）乘一个大于 1 的系数，比如 1.05；
- 对"早到"的路径（setup 的 capture clock、hold 的 data）乘一个小于 1 的系数，比如 0.95。

这样，同一条路径的起点被"故意算慢"、终点被"故意算快"，人为拉大两端差异，覆盖片内不一致的最坏情况。

业界还有更精细的 AOCV（考虑逻辑级数与距离）和 POCV（统计分布），原理相同：**用位置/级数相关的系数替代一个全局固定系数**，减少过度悲观。入门阶段先掌握固定 derate 的算法，AOCV/POCV 只是在系数上更聪明。

:::term OCV (On-Chip Variation) | 片内偏差
同一颗芯片内部不同位置、不同单元之间的延迟差异。global corner 只描述整片偏慢或偏快，OCV 描述片内相对差异，用 derate 建模。
:::

:::term Derate | 降额
在已算出的延迟上乘一个系数，人为放大或缩小，以覆盖未建模的偏差。setup 检查中 data/launch 乘 >1、capture 乘 <1；hold 检查方向相反。
:::

## 手算一次：derate 和 CPPR 到底吃掉多少余量 {#derate}

设核心时钟周期 `T = 2.00ns`，一条 setup 路径：

- launch 时钟延迟 `0.70ns`，capture 时钟延迟 `0.70ns`；
- 两者有一段公共路径（common path）`0.55ns`；
- 数据路径（Tcq + 逻辑 + 线）`1.12ns`；
- 终点触发器 setup `0.05ns`；
- 先不考虑 uncertainty。

### 第一步：不加 derate

`slack = T + capture_clk − launch_clk − setup − data`

`= 2.00 + 0.70 − 0.70 − 0.05 − 1.12 = 0.83ns`

看起来余量很足。

### 第二步：加 derate

setup 的悲观方向：launch 和 data 算晚（×1.05），capture 算早（×0.95）。

- data 晚：`1.12 × 1.05 = 1.176ns`
- launch 晚：`0.70 × 1.05 = 0.735ns`
- capture 早：`0.70 × 0.95 = 0.665ns`

`slack = 2.00 + 0.665 − 0.735 − 0.05 − 1.176 = 0.704ns`

一条路径被 derate 吃掉 `0.83 − 0.704 = 0.126ns`。几千条路径同时被吃，WNS 就是这么从正变负的。

### 第三步：CPPR 加回一部分

**CPPR（Clock Path Pessimism Removal，时钟路径悲观度移除）** 处理的是：launch 和 capture 的时钟有一段是**同一根线**，它不可能同时"又慢又快"。上面 launch 乘 1.05、capture 乘 0.95，对公共段 `0.55ns` 就重复悲观了。

加回量 = `common_path × (late_derate − early_derate)`

`= 0.55 × (1.05 − 0.95) = 0.055ns`

最终 `slack = 0.704 + 0.055 = 0.759ns`

:::term CPPR | 时钟路径悲观度移除
Clock Path Pessimism Removal。launch 与 capture 共享的时钟路径被同时按"最慢"和"最快"各算了一次，CPPR 把这段重复的悲观量加回 slack。PT 里由 `timing_remove_clock_reconvergence_pessimism` 控制。
:::

三个数要记住：**0.83（理想）→ 0.704（加 derate）→ 0.759（加 CPPR）**。评审时别人问"这条路径余量多少"，你要说清是哪一个口径。只报 0.83 是外行，只报 0.704 是漏了 CPPR。

hold 检查的方向完全相反：data 和 launch 按早到算（×0.95），capture 按晚到算（×1.05），CPPR 的加回量仍然取公共段 ×(1.05−0.95)。所以同一条路径，setup 和 hold 的 derate 后 slack 不能互相套用，必须分开算。上面的数字只用来理解机制，真实报告里每一段延迟都带 derate 系数；有的 PT 版本提供 `report_timing -derate` 把系数逐行列出来，跑之前先用 `-help` 确认当前版本支持。

## 多 corner 矩阵怎么读 {#matrix}

05-02 已经出现过一张 corner 表，那一课解决的是"PT 怎么跑起来"；这一节解决的是"十几个 corner 怎么组织、谁卡签核、缺了怎么记"。两者不重复：前者是单次签核的操作，后者是签核矩阵的设计。

| corner | 工艺 | 温度 | 电压 | 主要查 | 原因 |
|---|---|---|---|---|---|
| `ss_125c_0p99v` | SS | 125℃ | 0.99V | setup | 慢片 + 低压，经典最慢组合 |
| `ss_m40c_0p99v` | SS | −40℃ | 0.99V | setup | 温度反转时可能比 125℃ 更慢 |
| `ff_m40c_1p10v` | FF | −40℃ | 1.10V | hold | 快片 + 高压 + 低温，数据来得最早 |
| `ff_125c_1p10v` | FF | 125℃ | 1.10V | hold | 高温下 hold 也可能变差，需实测 |

两条纪律：

1. **SS 查 setup、FF 查 hold** 是起点，不是终点。`ss_m40c` 和 `ss_125c` 谁更慢，取决于工艺是否温度反转；`ff_m40c` 和 `ff_125c` 谁 hold 更差，取决于时钟树和温度系数。**四个角都跑，别用推理代替实算。**
2. **cross corner（交叉角）必须实算**。比如 `ss` 工艺配 `cbest` 寄生、`ff` 工艺配 `cworst` 寄生，看起来"不搭"，但签核矩阵里常常有；哪一对最差，只有跑过才知道。

:::fig corner-matrix | 这张表把每个 corner 的工艺、电压、温度、要查的项目排在一起。看的时候先找"SS 行查 setup、FF 行查 hold"，再看最后一列——真正的最差 corner 不是命名推出来的，是实算出来的。
:::

寄生 corner 和晶体管 corner 是两套坐标：`ss` 配 `cworst` 或 `rcworst` 查 setup，`ff` 配 `cbest` 或 `rcbest` 查 hold。两套组合起来才是完整场景，别只换晶体管库、SPEF 还用同一份。

工程上还要注意 corner 命名不一定统一：同一个 `ss_125c_0p99v`，有的项目写成 `ssg_125_0p99`，有的把电压写在前面。汇总时以"库文件 + SPEF 文件的实际路径"为准，别靠名字猜。缺一个角的库或 SPEF，就在汇总表里写"未覆盖，原因：缺 xx 库"，不要用相邻角替代——替代出来的数不是签核数。

## report_constraint：一次列出所有类型违例 {#violators}

签核不是只看 setup。一个设计可能 setup 干净、hold 干净，但 transition 超标 3000 条——这些"非时序"违例同样会让芯片不能工作。

```tcl
# 作用：按类型列出所有违例，先看总量再分头修
# 用法：update_timing 之后执行；输出重定向到 rpt/ 存档
report_constraint -all_violators > rpt/all_viol.rpt              ;# 全部类型一网打尽
report_constraint -all_violators -max_delay > rpt/setup.rpt      ;# 只看 setup
report_constraint -all_violators -min_delay > rpt/hold.rpt       ;# 只看 hold
report_constraint -all_violators -max_transition > rpt/trans.rpt ;# 只看转换时间
report_constraint -all_violators -max_capacitance > rpt/cap.rpt  ;# 只看负载电容
grep -c "slack" rpt/all_viol.rpt                                 ;# 先数总量，判断严重程度
```

各类违例的阈值含义：

| 类型 | 阈值来自 | 超标意味着 |
|---|---|---|
| `max_delay`（setup） | 时钟周期 − setup − uncertainty | 跑不到目标频率 |
| `min_delay`（hold） | 触发器 hold 时间 | 数据太早，可能冲掉上一拍 |
| `max_transition` | 库单元/线模型的有效范围 | 延迟模型失效，串扰和漏电变差 |
| `max_capacitance` | 库输出引脚驱动能力 | 驱动不足，延迟非线性上升 |
| `max_fanout` | 设计规则（项目自定） | 一个单元带太多负载，transition 必差 |

修复顺序有讲究：**先修 transition / cap / fanout，再修 setup/hold**。原因在 03-08 讲过：电气违例没修，工具算出的延迟本身就是错的，你按错的数修时序等于白修。

:::pitfall 只修 setup，hold 越修越糟
现象：setup 违例从 500 条降到 30 条，hold 违例从 80 条涨到 600 条。

原因：修 setup 的常用手段是加大驱动、缩短路径、插 buffer，这些动作会让数据到得更早，直接恶化 hold。反过来，修 hold 加延迟又会吃掉 setup 余量，两者天然对立。

怎么查：每次优化后同时跑 `report_constraint -all_violators -max_delay` 和 `-min_delay`，把两个数并排记。如果 hold 涨幅超过 setup 降幅的 30%，说明优化方向太激进，要改用"只动违例路径、不动全局"的策略，或者留到 post-route 用 ECO 精修。
:::

## report_bottleneck：从几千条违例里找共性 {#bottleneck}

`report_constraint` 告诉你"有多少条"，`report_bottleneck` 告诉你"为什么"。它把违例按瓶颈类型聚合：是某一类单元太慢、某一类网络太长、还是某一组路径逻辑级数太深。

```tcl
# 作用：按瓶颈类型聚合，找"最费时间的一类对象"
# 用法：update_timing 之后；选项随版本不同，先看帮助再写脚本
report_bottleneck > rpt/bottleneck.rpt        ;# 默认聚合视图
report_bottleneck -help                       ;# 查当前版本支持的聚合维度
```

报告通常按三个维度聚合，读法不同：

1. **按单元类型**：如果前几名是 `BUFX1`、`INVX1` 这类小驱动单元，说明瓶颈是驱动不足，修法是换大驱动或减负载，不是改逻辑。
2. **按网络**：如果某几条 net 反复出现，说明是长线/高扇出，修法是重布线、插 buffer、调布局。
3. **按路径组/逻辑级数**：如果某一组路径级数明显高于其他，说明是结构问题，靠优化工具修不动，要回到 RTL 做流水线。

聚合报告的价值在于**决定方向**：5000 条违例，如果 60% 集中在 20 个网络上，你修 20 个网络就解决一半；如果均匀分布在 5000 条路径上，说明是全局约束或工艺问题，逐条修没有意义。

:::fig report-timing-annotated | 这张图把 report_timing 的每一段都标注了：起点时钟、数据路径、终点要求、slack。聚合报告只能告诉你方向，最终确认还要回到这样一条具体路径——看它的 launch/capture 时钟延迟和 derate 标注，才能判断是设计慢还是约束紧。
:::

## 噪声与串扰：邻居翻身，你被拉偏 {#si}

前面所有延迟都假设"线是孤立的"。真实版图里，两条线之间有耦合电容 `Cc`，当 aggressor（攻击线）翻转时，会通过 `Cc` 往 victim（受害线）注入电荷。

两种后果：

**第一，延迟变化（delta delay）。** 如果 aggressor 与 victim 同向翻转，victim 被"推着走"，变快；反向翻转，victim 被"拖着"，变慢。同一根线在不同数据模式下延迟能差 10%~30%。这叫 **SI（Signal Integrity，信号完整性）** 引起的时序变化。

**第二，功能失效（noise bump）。** 如果 victim 本来稳定在 0，aggressor 一个大翻转通过耦合电容把它抬到阈值以上，下游可能误判。这种毛刺不改变静态时序，但会让功能出错，属于 noise 检查的范畴。

签核的处理：

- **SI-aware timing**：延迟计算时把耦合电容按"最坏翻转方向"折算（Miller 系数），分别算 late/early 两个值。PT 里通常用 SI 模式跑，报告会标 `delta delay`。
- **噪声余量**：给 victim 的电压摆幅留 margin，保证毛刺不超过接收端的噪声容限。margin 的大小与电源电压直接相关——**IR drop 越大，噪声容限越小**，这也是为什么低功耗签核和时序签核要一起看。
- **物理手段**：加大间距、加屏蔽线（shield）、换层、减少并行长度。CTS 课里的 NDR（双倍间距）就是干这个的。

:::term Crosstalk | 串扰
相邻网络通过耦合电容互相影响的现象。后果分两类：改变延迟（delta delay）和产生电压毛刺（noise bump）。前者影响时序，后者影响功能。
:::

:::term SI (Signal Integrity) | 信号完整性
信号在传输过程中因寄生耦合、电源噪声、反射等发生波形畸变的现象总称。时序签核里的 SI 分析主要量化串扰对延迟的影响。
:::

:::fig ir-drop | 这张图左边两个公式说明电压为什么会掉，右边热图红区是电压最低的位置。把它和噪声余量联系起来看：电压越低，门的噪声容限越小，同样的耦合毛刺更容易把 victim 推翻。所以 IR drop 超标的设计，时序余量也不能只按标称电压算。
:::

:::note 噪声余量不是"多加一点 slack"
给时序加 margin 只能防"慢"，防不了"毛刺导致的功能错"。噪声检查是独立的一套判据：看 victim 的电压峰值是否超过接收端的 VIH/VIL。两者要分开做，不能用一个 slack 数字代替。
:::

## 一个完整的多 corner 签核脚本 {#script}

下面这份脚本按"定义场景 → 读寄生 → 逐 corner 跑 → 出报告"四段组织。真实项目会把它拆成 shell 循环 + 单 corner Tcl，便于并行；这里合成一份，方便看清结构。

```tcl
# 作用：多 corner 时序签核主脚本（PrimeTime）
# 用法：pt_shell -f signoff_all.tcl，在 sta/ 目录下执行；库与 SPEF 路径按项目改

set design soc_top
set corners {ss_125c_0p99v ss_m40c_0p99v ff_125c_1p10v ff_m40c_1p10v}

# ---- 第一步：corner → 库文件、SPEF 后缀的映射 ----
array set lib_db {
  ss_125c_0p99v /lib/std_ss_0p99_125.db
  ss_m40c_0p99v /lib/std_ss_0p99_m40.db
  ff_125c_1p10v /lib/std_ff_1p10_125.db
  ff_m40c_1p10v /lib/std_ff_1p10_m40.db
}
array set spef_tag {
  ss_125c_0p99v cworst
  ss_m40c_0p99v rcworst
  ff_125c_1p10v cbest
  ff_m40c_1p10v rcbest
}

# ---- 第二步：逐 corner 重建设计 ----
foreach c $corners {
  remove_design -all                                  ;# 清掉上一个 corner 的所有对象
  set link_path "* $lib_db($c) /lib/sram_$c.db"       ;# 标准单元 + SRAM 用同 corner 库
  read_verilog ../netlist/${design}.v                 ;# 网表每个 corner 相同
  link_design $design                                 ;# 按 link_path 解析单元
  read_sdc ../sdc/${design}.sdc                       ;# 冻结版约束
  read_parasitics -format spef \
    ../spef/${design}_$spef_tag($c).spef              ;# 读该 corner 的真实寄生

  # ---- 第三步：签核设置 ----
  set_propagated_clock [all_clocks]                   ;# 时钟走真实树
  set_timing_derate -late  1.05 -cell_delay           ;# 单元延迟晚到方向
  set_timing_derate -late  1.05 -net_delay            ;# 线延迟晚到方向
  set_timing_derate -early 0.95 -cell_delay           ;# 单元延迟早到方向
  set_timing_derate -early 0.95 -net_delay            ;# 线延迟早到方向
  set_app_var timing_remove_clock_reconvergence_pessimism true ;# 打开 CPPR
  update_timing -full                                 ;# 全量重算，别用增量

  # ---- 第四步：出该 corner 的报告 ----
  report_constraint -all_violators > ../rpt/${c}_viol.rpt
  report_timing -max_paths 20      > ../rpt/${c}_setup.rpt
  report_timing -delay_type min -max_paths 20 > ../rpt/${c}_hold.rpt
}
```

几个容易写错的点：

- `remove_design -all` 不能省。不清设计直接换库，PT 会沿用上一个 corner 的链接结果，报告看起来正常，其实库没换。
- `link_path` 里的 SRAM 库也要按 corner 换。只换标准单元，SRAM 还是典型值，宏单元附近的路径会算错。
- `update_timing -full` 而不是增量。签核要的是"从零算一遍"的结果，增量更新可能残留上一轮缓存。
- derate 不要写成一条 `set_timing_derate -late 1.05` 就完事：不加 `-cell_delay` / `-net_delay` 时作用范围不同版本有差异，写清楚最稳。

课程环境没有完整的四套库与 SPEF，这份脚本跑不出真实报告；真实项目里你会看到项目组用 shell 包一层，把每个 corner 丢到不同机器并行跑，最后合并成一张表。

跑完四个 corner 后，用一段 shell 把关键数字抽成 CSV，避免手工抄错：

```bash
# 作用：把每个 corner 的 WNS 与违例条数抽成一行，拼成汇总表
# 用法：在 rpt/ 下执行；报告格式不同时，awk 的字段号要按实际调整
printf "corner,wns,violations\n" > summary.csv          # 先写表头
for c in ss_125c_0p99v ss_m40c_0p99v ff_125c_1p10v ff_m40c_1p10v; do
  wns=$(grep -m1 "slack" ${c}_setup.rpt | awk '{print $1}')  # 首条路径的 slack
  n=$(grep -c "slack" ${c}_viol.rpt)                         # 违例行数
  echo "$c,$wns,$n" >> summary.csv                           # 追加一行
done
column -s, -t summary.csv                                # 对齐打印，贴进评审邮件
```

这只是"抄数"，不是分析：CSV 里的 WNS 要能追回原始报告，签字时附的是报告路径，不是 CSV 本身。

## 时序汇总表：把几十份报告压成一页 {#table}

签核评审不看 40 页报告，看一张表。表的列固定为：**corner / WNS / TNS / 违例数 / 结论**。

| corner | WNS (ns) | TNS (ns) | 违例端点 | 结论 |
|---|---|---|---|---|
| ss_125c_0p99v | −0.08 | −1.42 | 214 | 需 ECO，集中在 u_core 的乘法器 |
| ss_m40c_0p99v | −0.21 | −6.85 | 587 | **签核阻塞项**，逻辑级数过深 |
| ff_125c_1p10v | +0.19 | 0.00 | 0 | setup 通过；hold −0.09，见下行 |
| ff_m40c_1p10v | +0.15 | 0.00 | 96 | hold 违例，需加延迟 |

（以上数字是格式示例，不是实测。）

三个指标的分工：

- **WNS（Worst Negative Slack）**：最差一条路径的 slack。它告诉你"最坏有多坏"，但不告诉你"有多少条"。
- **TNS（Total Negative Slack）**：所有负 slack 之和。它衡量"总共欠多少"，WNS 相同、TNS 差 10 倍，工作量完全不同。
- **违例端点数**：有多少个终点不满足。它决定 ECO 的规模。

读表顺序：先看有没有负 WNS 的 corner（有就不能签），再看 TNS 最大的那个（工作量在这里），最后看违例是否集中在同一模块（集中好修，分散难修）。

WNS 和 TNS 要一起看。两个设计都报 WNS −0.10ns：一个 TNS −0.12ns、只有 3 条违例，说明是孤立的边界路径，改一条就完；另一个 TNS −15ns、800 条违例，说明是系统性问题，可能整块逻辑都要重做。只报 WNS 会把这两种情况说成一样糟，评审无法判断工作量。

:::fig timing-summary | 这张图讲的是汇总表第一页怎么读：先看 WNS/TNS/条数三个数决定方向，再按现象分流到具体路径。评审会上报的就是这三个数加一句"卡在哪个 corner、哪类路径"，不是逐条念报告。
:::

## 工作中怎么用：评审会上报哪几个数 {#in-work}

**谁做**：STA 工程师主导多 corner 签核，PR 工程师提供 SPEF 与修复，设计者决定是否改 RTL。签核结论由项目负责人签字。

**输入**：冻结的网表、每个 corner 的库、每个 corner 的 SPEF、冻结版 SDC、derate 策略（项目签核规范里写死）。

**输出**：一张汇总表、每个 corner 的 `report_timing` 与 `report_constraint`、一份"违例分类与修复计划"。表要能追到原始报告的文件名和生成时间。

**评审会只报五个数**：

1. 全局最差 WNS 及其 corner；
2. 对应 TNS 与违例端点数；
3. hold 最差 slack 及其 corner；
4. 有没有 corner 没跑（缺库、缺 SPEF 都要明说）；
5. 修复计划与预计风险（哪些能 ECO，哪些要改 RTL）。

**不要做的事**：不要报"平均 slack"，不要只报最好的 corner，不要用"应该没问题"代替实算。签核的价值在于**可复现**：别人拿同样的输入，要能跑出同样的五个数。

**做错了会怎样**：漏一个 corner，可能漏掉一整类违例；derate 少加，报告漂亮但硅片上失效；把 SI 关掉跑，长线延迟偏乐观。这些问题在报告上都看不出来，只在流片后暴露。

:::lab 动手：把四份 corner 报告汇总成一张签核表
**任务**：`~/backend_lab/soc/sta/rpt/` 下有四个 corner 的 `*_viol.rpt` 和 `*_setup.rpt`。填出一张五列汇总表，并给出"能不能签"的结论。

**步骤**：
1. `ls rpt/*_viol.rpt` 确认四个 corner 齐全，缺哪个要写进结论。
2. 对每份报告 `grep -m1 "slack"` 取 WNS，`grep -c "slack"` 数违例条数。
3. `grep -E "max_delay|min_delay|max_transition" rpt/${c}_viol.rpt | awk '{print $1}' | sort | uniq -c` 看违例类型分布。
4. 把四行填进表格，标出 setup 最差与 hold 最差的 corner。
5. 用 06-04 的手算例子，验算其中一条路径的 derate 后 slack 是否与报告一致（差 5% 以内算对）。

**过关标准**：表格四行齐全；能指出"哪个 corner 阻塞签核、阻塞的是 setup 还是 hold、违例集中在哪类对象"，并给出下一步是先修电气违例还是先修时序。
:::

:::quiz
为什么 SS 角要同时跑 −40℃ 和 125℃？|温度对延迟的影响不单调：迁移率随温度升高下降（变慢），阈值电压随温度升高下降（变快），低电压下可能出现温度反转，哪个更慢必须实算。
global corner 和 OCV derate 分别描述什么？|global corner 描述整颗芯片偏慢或偏快；derate 描述同一颗芯片内部不同位置的相对差异，在 global 结果上再放大两端。
一条 1.12ns 的数据路径，late derate 1.05 后是多少？|1.12 × 1.05 = 1.176ns；setup 检查中数据与 launch 时钟按晚到算，capture 时钟按早到算。
CPPR 为什么能把 slack 加回来？|launch 与 capture 共享的时钟路径被同时按最慢和最快各算了一次，属于重复悲观；CPPR 把公共段 ×(late−early) 的差值加回。
SS 和 FF 分别主要查 setup 还是 hold？为什么还要跑交叉角？|SS 查 setup（慢），FF 查 hold（快）；交叉角（如 ss 配 cbest、ff 配 cworst）可能产生更差组合，必须实算。
report_constraint 和 report_bottleneck 的分工是什么？|前者按违例类型列数量与 slack，回答"有多少"；后者按单元/网络/路径聚合，回答"为什么、先修哪一类"。
串扰对时序的两种后果是什么？|delta delay（邻居翻转改变 victim 延迟，同向变快、反向变慢）和 noise bump（毛刺超过阈值导致功能错）。
为什么不能只报一个 WNS 就签字？|WNS 只说明最坏一条有多坏，不说明违例规模（TNS/端点数）、不说明 hold、不说明其他 corner；签核必须覆盖全部场景。
:::

:::check
- 能说清 P/V/T 各自对延迟的影响方向，并解释温度反转
- 能手算 derate 前后的 slack，并单独算出 CPPR 加回量
- 能读懂四 corner 矩阵，指出 setup/hold 各由哪个角卡住
- 能用 report_constraint 按类型统计违例，并说出五类阈值的含义
- 能用 report_bottleneck 判断瓶颈是单元、网络还是逻辑级数
- 能解释串扰的两种后果，以及噪声余量与 IR drop 的关系
- 能把多份 corner 报告汇总成 WNS/TNS/条数/结论五列表
:::
