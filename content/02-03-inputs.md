---
id: 02-03-inputs
no: 11
stage: 2
title: 开工前要拿到什么：设计数据准备与自检
en: Design Data Preparation & Sanity Checks
hours: 3
minutes: 38
tags: [输入数据, lib, lef, tluplus, sdc, 自检]
summary: 后端项目 80% 的"莫名报错"其实是输入数据不全或版本不对。这一课把 7 类输入文件讲清楚：各自是什么、少了会报什么错、SDC 最小五条怎么读、以及开工前 10 分钟怎么一次性查完。
---

## 一个项目开工，桌上应该有 7 样东西 {#seven}

:::goal 拿到一个新工程，能在 10 分钟内核对完 7 类输入文件是否齐全、版本是否匹配，并能读懂"缺文件"的报错指向哪一样。
:::

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

这七样东西分三类，**分类比背清单有用**：

- **逻辑**：1（网表）
- **物理 + 电气**：2、3、4、5（库和工艺）
- **意图**：6、7（约束和功耗）

报错时先问自己"缺的是哪一类"：说"找不到单元"是第 2 类；说"没有层"是第 4 类；说"全是 0"是第 6 类。分类一对，方向就出来了。

:::scene 拿到一个"跑不起来"的工程
同事交接给你一个工程，说"脚本都在，直接跑就行"。你跑第一步就报：

```
Error: Unable to resolve reference 'DFF_X1' in design 'soc_top'. (LINK-5)
```

看着像脚本问题，其实是 **`link_library` 指错了目录，或者 `.db` 版本和网表不匹配**（网表是 A 版库综合的，你读的是 B 版）。

会查输入数据的人 10 分钟解决；不会的人会重装工具、重下 PDK、怀疑 License，一天就过去了。

判断方法：`ls` 一下 `link_library` 里的文件是否存在，再用 `report_lib` 看这个库里到底有没有 `DFF_X1` 这个名字。两个动作，两分钟。
:::

:::term Black Box | 黑盒
网表里引用了、但库里找不到定义的单元。工具不会因此停下，而是给它留个空壳：没有延迟、没有面积、没有引脚。

**黑盒是"沉默的杀手"**：时序分析会直接跳过它，报告看起来干干净净，流片回来功能全错。所以 `link_design` 之后必须确认未解析引用是 0。
:::

## `.lib` / `.db` / `.lef`：菜谱、压缩包、占地证 {#libdb}

初学者最容易混的就是这三个。用一个类比锁死：

| 类比 | 文件 | 回答什么问题 | 格式 |
|---|---|---|---|
| 菜谱 | `.lib` | 这个单元多快、多耗电、多大面积 | 纯文本，能打开看 |
| 压缩包（同一本菜谱的电子版） | `.db` | 同上，内容一模一样 | 二进制，打不开 |
| 占地证 | `.lef` | 这个单元在版图上占多大、引脚在哪个坐标 | 纯文本，能打开看 |

三句话记住区别：

1. **`.lib` 和 `.db` 是同一份数据的两种形态**，一个是源文件，一个是编译产物。换 `.db` 不会改变时序结果，只会让读取变快。
2. **`.lef` 里没有任何延迟信息**。它只管形状：`SIZE 0.76 BY 1.4`、引脚矩形在哪。
3. **两张表必须互相匹配**。同一个单元名，`.lib` 说面积 0.76，`.lef` 说 0.76×1.4，如果版本对不上（比如 `.lef` 是 2019 版、`.lib` 是 2021 版），工具不会报错，但算出来的利用率、延迟全是错的。

`.lib` 里真正有用的部分：

```tcl
# 作用：看清一个单元在时序库里的三样关键数据——面积、引脚电容、延迟查找表
# 用法：直接用文本编辑器打开 .lib，搜 cell (INV_X1)；下面只保留关键行
cell (INV_X1) {
  area : 0.760;                       # 面积，算利用率要用这个数
  pin (A)  { direction : input;  capacitance : 0.0021; }   # 输入电容，决定前一级要驱动多大负载
  pin (ZN) { direction : output;      # 输出引脚，延迟从这里查
    timing () {
      related_pin : "A";              # 这条延迟是 A -> ZN
      cell_rise (delay_template_7x7) { ... }   # 7×7 查找表：输入 transition × 输出负载 -> 延迟
    }
  }
}
```

:::term Lookup Table (LUT) | 查找表
标准单元的延迟不是固定数字，而是**输入信号变化快慢（transition）× 输出带多大负载（capacitance）** 的函数。工艺厂把它做成一张 7×7 的表存在 `.lib` 里，工具查表 + 插值得到延迟。

这就是为什么"换一个 corner、换一个负载"延迟就变了——不是工具在猜，是在查不同的表。**也是为什么 transition 超标必须先修：表的外插区域不准。**
:::

:::term Corner | 工艺角
同一套库在不同工艺偏差、电压、温度下的多个版本：`tt`（typical）、`ss`（slow）、`ff`（fast），还会带电压温度后缀，如 `ss_0p99v_125c`。

签核要在最坏角（setup 用 ss、hold 用 ff）都过。**混用 corner 是后端最隐蔽的错误**：单看每份报告都"过"，合起来不成立。
:::

:::pitfall 用了 `.lib` 但 corner 是 ss，时序全"过"
典型事故：综合用 `tt`，PR 用了 `ss`，PT 又用回 `tt`。三次报告的 WNS 各不相同，签字的人以为都过了。

**规矩：全流程记录 corner。** 每个阶段日志第一行打印用的是哪个库文件，归档时一起存。签核用的 corner 必须写在报告封面。

自查一句话：把三个阶段日志的库路径 `grep` 出来并排放，文件名不一样就是隐患。
:::

## LEF：单元的"占地证" {#lef}

LEF 描述物理形状，分两种，都必须有：

| 类型 | 文件名常见 | 内容 | 少了会怎样 |
|---|---|---|---|
| 技术 LEF（tech LEF） | `tech.lef` / `*.techlef` | 有哪些金属层、每层的最小线宽/间距、via 定义 | 工具不知道能画几层线、线能多宽 |
| 宏 LEF（macro LEF） | `*_macro.lef` / `*.lef` | 每个标准单元的尺寸、引脚位置、阻挡层 | 单元没有尺寸，布局器无法摆放 |

一个单元在 LEF 里的样子：

```text
# 作用：看清一个标准单元在 LEF 里的尺寸和引脚坐标（真实结构，数值为示例）
# 用法：文本编辑器打开 macro LEF，搜 MACRO INV_X1
MACRO INV_X1
  CLASS CORE ;                 # 标准单元（CORE），不是 IO 也不是宏单元
  ORIGIN 0 0 ;
  SIZE 0.76 BY 1.4 ;           # 宽 0.76um、高 1.4um —— 行高由它决定
  PIN A
    DIRECTION INPUT ;
    PORT
      LAYER metal1 ;
      RECT 0.10 0.30 0.20 1.10 ;   # 引脚在 metal1 上的矩形：左下 (0.10,0.30)、右上 (0.20,1.10)
    END
  END A
END INV_X1
```

`RECT` 后面四个数是 `llx lly urx ury`：左下角坐标 + 右上角坐标。所以这个引脚宽 0.1µm（0.20−0.10）、高 0.8µm（1.10−0.30），位置在单元左侧。

**为什么引脚位置重要**：布线只能在引脚上打孔。引脚在单元内部还是边缘、在哪一层，直接决定这条路好不好走。

:::note 为什么行高是 1.4µm
因为库里所有标准单元都是 1.4µm 高（`SIZE ... BY 1.4`）。**行高由库决定，不由你决定。** 你算"能放几行"时用的就是这个数：芯片高度 ÷ 1.4 = 行数。

课程环境实测：万门设计 222.2µm 高，正好 153 行（`222.2 ÷ 1.4 ≈ 158`，去掉上下边距后 153）。
:::

:::pitfall `.lef` 和 `.lib` 版本不匹配
现象：布局正常、时序正常，但 `report_area` 算出来的面积和综合报告差 12%，利用率怎么调都对不上。

原因：`.lef` 是旧版（单元尺寸改过），`.lib` 是新版。工具不校验两者的一致性，各用各的。

怎么查：挑三个常用单元（INV_X1、DFF_X1、BUF_X4），把 `.lib` 的 `area` 和 `.lef` 的 `SIZE` 宽×高对一遍。对不上就说明版本串了。
:::

## 寄生参数模型：为什么缺了优化器直接不干活 {#parasitic}

这一项最容易被漏，因为**缺了不一定马上报错，可能到优化阶段才炸**。

先说清它是什么：布线画出来的金属线不是理想导线，有电阻、有对地电容、有和邻线的耦合电容。这些参数叫**寄生参数（parasitic）**。工具要算真实延迟，就必须知道"每微米某层金属大概多少电阻、多少电容"——这个"每单位的 RC 表"就是寄生参数模型。

| 文件 | 工具 | 用途 |
|---|---|---|
| `.itf` / `.tluplus` | ICC2 / Innovus | 每层金属的电阻、电容、边缘电容参数（按宽度/间距建的表） |
| `.qrc` / `.captable` | StarRC / QRC | 高精度提取用的电容表，签核阶段用 |

课程手册里的真实案例：

```text
Error: Design has atleast one corner with no Parasitic information. (OPT-906)
```

这句话逐词读：`at least one corner`（至少一个 corner）`with no Parasitic information`（没有寄生信息）。注意它说的是 **corner**，不是 design——所以问题多半不在"你没做提取"，而在"corner 没绑上"。

修法两步：

```tcl
# 作用：读入 TLU+ 寄生模型，并把它绑定到 RC corner 上
# 用法：Innovus 里 init_design 之后、任何优化之前执行；路径按项目实际改
read_parasitic_tech -tlup ./tlup/NangateOpenCellLibrary.tlup \
                    -layermap ./tlup/NangateOpenCellLibrary.layermap -name nt   # ① 读进内存，起名 nt
set_parasitic_parameters -early_spec nt -late_spec nt                          # ② 把 nt 绑到 early/late 两个 corner
```

:::term Parasitic Extraction (RC Extraction) | 寄生参数提取
从版图几何算出每根线的电阻和电容，输出 `.spef` 文件。STA 用它算真实线延迟。

提取有两个精度档：**估算**（布线前，按扇出和距离估）和**签核级**（布线后，按真实几何算）。签核必须用后者。
:::

:::pitfall 只 `read_parasitic_tech` 不 `set_parasitic_parameters`
第一条命令只是"把文件读进内存"，第二条才是"告诉 corner 用它"。少了第二条，优化器依然认为没有寄生信息，照样报 `OPT-906`。

课程环境里我们在这上面卡了一整轮：日志里 `NEX-018` 和 `OPT-906` 前后脚出现，一开始以为是文件路径错，真正的原因是后者没绑。
:::

## SDC：最小可用的约束集 {#sdc}

:::term SDC | 时序约束文件
Synopsys Design Constraints，本质是一串 Tcl 命令。它不描述电路长什么样，只描述"这块电路要在多快下工作、哪些路径不用管"。

**SDC 是设计的"考试大纲"**：工具会严格照着它优化，写错就是照错的目标优化，越努力越偏。
:::

一个能跑起来的 SDC 只需要五类语句。**先跑通这五条，再谈别的。**

```tcl
# 作用：一个能跑通时序分析的最小 SDC，五条覆盖"时钟、抖动预算、输入、输出、波形质量"
# 用法：综合和 PR 都 source 这一份；周期、端口名按设计改
create_clock -name clk -period 2.0 [get_ports clk]        # ① 时钟：2ns = 500MHz，没有它所有时序都是 0
set_clock_uncertainty 0.06 [get_clocks clk]               # ② 抖动+skew 预算：周期的 3%
set data_in [remove_from_collection [all_inputs] [get_ports clk]]   # 时钟端口本身不是"输入数据"，先剔掉
set_input_delay  0.30 -clock clk $data_in                 # ③ 外部器件送数据进来要 0.3ns
set_output_delay 0.30 -clock clk [all_outputs]            # ④ 外部器件要求数据 0.3ns 内到位
set_max_transition 0.15 [current_design]                  # ⑤ 任何引脚 transition 不得超过 150ps
```

逐条解释，重点是"为什么是这个数"：

**① `create_clock`**：定义周期和源端口。周期从 spec 来（500MHz → 2ns），不是拍的。这一条缺失，所有路径变 unconstrained，报告显示"无违例"——这是假绿，签核必挂。

**② `set_clock_uncertainty`**：给时钟留的余量，包含 PLL 抖动（jitter）和 CTS 之后的 skew。经验值取周期的 3%~5%；2ns 周期 → 60~100ps。给太小，时序过于乐观，芯片回来 fail；给太大，工具拼命优化，面积功耗上去还收不敛。

**③ `set_input_delay`**：描述芯片**外面**的世界。上游器件从时钟沿到把数据送到你的引脚，花了多久（它的 Tco + 板级走线）。这个数不从你的设计里来，要从系统时序预算或接口 spec 里拿。

注意上面先把时钟端口 `clk` 从 `all_inputs` 里剔掉了：给时钟端口加 input delay 等于凭空挪动时钟沿，时序报告会整体偏掉。这是新手最常写出的一个错。

**④ `set_output_delay`**：描述下游器件的**要求**。你的数据必须在下一个时钟沿前多久稳定，才能被对方采到（对方的 setup + 走线）。

**⑤ `set_max_transition`**：限制信号边沿的陡缓。这一条最容易被当成"次要规则"，其实它是延迟准确性的前提：transition 太差时，`.lib` 查找表要外插，算出来的延迟不可信，后面所有优化都建立在错数上。

手算一次，理解 ③④ 为什么不能省：周期 2.0ns，input delay 0.3ns，内部组合逻辑 0.9ns，触发器 setup 0.05ns，uncertainty 0.06ns。

- 正确的 slack = `2.0 − 0.3 − 0.9 − 0.05 − 0.06 = 0.69ns`
- 如果偷懒把 input delay 写成 0：slack 变成 `0.99ns`，**凭空多出 0.3ns 假余量**

这就是"SDC 写错比不写更危险"的具体含义：不写，工具会警告"没有约束"；写错，工具会一本正经给你一份全过的报告。

| 少了哪条 | 后果 |
|---|---|
| `create_clock` | 所有路径 unconstrained，报告"无违例"——假的 |
| `set_clock_uncertainty` | 时序过于乐观，芯片回来 fail |
| `set_input_delay` / `set_output_delay` | IO 路径按 0 延迟算，签核时全线违例 |
| `set_max_transition` | transition 失控，延迟查表外插，优化方向全错 |

另外两条常用但不算"最小集"的：`set_false_path`（异步复位、跨时钟域不用查的路径）和 `set_max_capacitance`（负载上限）。写完五条再加这两条，顺序别反。

:::pitfall SDC 里的端口名和网表对不上
现象：`create_clock` 报了 warning 但流程继续跑，最后所有时序都是 unconstrained。

原因：`get_ports clk` 里的 `clk` 在综合后被改名了（比如变成了 `clk_pad`），或者大小写不一致。`get_ports` 找不到东西时只 warning，不 error。

怎么查：`report_clocks` 必须能看到你定义的那个时钟名；`check_timing -include unconstrained` 的 `unconstrained_endpoints` 必须是 0。两个都为真才算 SDC 真的生效了。
:::

## 开工前的 5 项自检（10 分钟，省两天）{#check}

每次拿到新工程，按这个顺序查一遍。顺序有讲究：**从"库"查到"设计"，再从"约束"查到"数"**，前面的错了，后面的检查没有意义。

```tcl
# 作用：新工程上手第一件事，5 步确认库、网表、约束真的生效了
# 用法：存成 check_inputs.tcl，每次 init_design 之后 source 一次；下列以 DC/ICC2 命令为主
report_lib tt_1v0_25c        # ① 库读进来了吗？看 cell count；Nangate45 是 130 多个，0 就是没读进来
link_design                  # ② 网表里的单元都能在库里找到吗？有 unresolved 就是库不全，别往下跑
report_area                  # ③ 单元数和总面积是多少？0 说明网表没读对（ICC2 用 report_design -physical）
report_clocks                # ④ 时钟读到了吗？必须能看到 SDC 里定义的名字
report_timing -unconstrained # ⑤ 有没有完全没约束的路径？有输出就是 SDC 漏了 IO delay
```

每一项的判据要具体到"看到什么数算过"：

| 检查 | 通过标准 | 不通过说明什么 |
|---|---|---|
| ① 库单元数 | 与库文档一致（Nangate45 约 130+） | 库路径错、只读了半个库 |
| ② 未解析引用 | 0 个 | 网表和库版本不匹配 |
| ③ 单元数/面积 | 与综合报告差 <2% | 网表读错、层次没展开 |
| ④ 时钟 | 名字、周期都对 | SDC 没读、端口名变了 |
| ⑤ 未约束端点 | 0 个 | IO delay 缺失、false path 写反 |

:::tip 把自检写成脚本
把这五条存成 `check_inputs.tcl`，每次新工程第一件事就是 `source check_inputs.tcl`，输出重定向到 `rpt/00_check.log` 存档。

老手和新手的差别不在会不会修 DRC，而在**新工程上手的前十分钟**：老手先查输入，新手直接跑流程，然后花两天查一个"库版本不对"的问题。

更进一步：把这五条写进 flow 的第一步，检查不过就 `exit`，不让错误数据往下流。
:::

:::lab 动手：算一次"这个库能放多少单元"
**任务**：用 `.lib` 里的面积和 LEF 里的尺寸做一次手算，理解利用率的来源，并核对课程环境的实测值。

**步骤**：

```bash
# 作用：从库里取一个单元的面积，再按平均面积估算整个设计的利用率
# 用法：在 ~/pdk/nangate45/lib 下执行；只读文件，不改任何东西
cd ~/pdk/nangate45/lib                                    # 进库目录
grep -A2 "cell (INV_X1)" NangateOpenCellLibrary_typical.lib | head -3   # 取出 INV_X1 的 area 行
grep -c "^  cell (" NangateOpenCellLibrary_typical.lib     # 数一数这个库有多少个单元
```

看到 `area : 0.760` 之后手算：

- 芯片 222.5 × 222.2 µm = 49440 µm²
- 12026 个单元，平均面积按 2.0 µm² 估 = 24052 µm²
- 利用率 = `24052 ÷ 49440 ≈ 48.6%`（课程环境实测 49.8%，差在平均面积是估的）
- 行数 = `222.2 ÷ 1.4 ≈ 158`，去掉边距 153 行

**过关标准**：能说出三件事——利用率的分母是芯片面积不是单元面积；行高来自 LEF 的 `SIZE ... BY 1.4`；把平均面积从 2.0 改成 2.4，利用率会变成约 58%，并解释这对布线意味着什么。
:::

:::quiz
`.lib`、`.db`、`.lef` 三者各自回答什么问题？|`.lib`/`.db` 回答"多快、多耗电、多大面积"（菜谱/压缩包，内容相同）；`.lef` 回答"占多大、引脚在哪"（占地证）。
只有 tech LEF 没有 macro LEF 会怎样？|工具知道有哪些层、线宽间距，但不知道每个标准单元多大、引脚在哪，无法布局布线。
`OPT-906` 报"没有寄生信息"，最常见的原因是什么？|寄生文件没读，或者读了没绑到 corner（缺 `set_parasitic_parameters`）。
SDC 里少了 `create_clock` 会怎样？|所有路径 unconstrained，报告显示"无违例"，但这是假的，签核必挂。
`set_input_delay` 描述的是芯片内部还是外部？|外部。它表示上游器件把数据送到本芯片引脚所花的时间，要从系统时序预算或接口 spec 拿，不能拍。
为什么 `set_max_transition` 算"最小五条"之一？|transition 太差时延迟查找表要外插，算出的延迟不可信，后面所有优化都建立在错数上。
为什么利用率不是越高越好？|超过 80~85% 后布线资源不够，拥塞和 DRC 会爆炸，反而要花更多时间收敛；经验值 50~70% 比较稳。
新工程上手前 10 分钟应该先查什么？|先查库（单元数）、再查网表（未解析引用）、再查时钟和未约束端点，最后看面积/单元数是否合理。
:::

:::check
- 能背出 7 类输入文件，并把它们分成逻辑、物理电气、意图三类
- 能用"菜谱 / 压缩包 / 占地证"讲清 `.lib`、`.db`、`.lef` 的区别
- 知道 tech LEF 和 macro LEF 分别给什么，会读 `RECT llx lly urx ury`
- 能写出 SDC 最小五条，并说出每条缺失的后果
- 能手算一次 input delay 少写导致 slack 虚高的例子
- 遇到 `OPT-906` 知道先查寄生参数有没有绑到 corner
- 能按顺序跑完 5 项自检，并说清每项的通过标准
:::
