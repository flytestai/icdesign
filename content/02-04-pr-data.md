---
id: 02-04-pr-data
no: 23
stage: 2
title: PR 的数据准备：一次 init 到底要喂几个文件
en: PR Data Preparation
hours: 2
minutes: 30
tags: [PR, netlist, def, lef, lib, sdc, MMMC, init]
summary: 把 init 阶段要导入的文件一次列全：design data（netlist）与 physical data（tech lef / cell lef / def）、timing data（lib / rc tech / sdc）、MMMC 环境。重点讲清 netlist 和 def 这两个"最容易被误解"的文件，并给出缺文件时的真实报错对照表。
---

## 先把清单摆出来 {#list}

:::goal 能说出 init 需要的全部文件及其作用；能解释 netlist 与 def 的区别；看到 `Cannot find library` 这类报错能定位到缺哪个文件。
:::

新人接手一个项目，第一件事不是敲命令，而是**确认数据齐不齐**。缺一个文件，后面所有工作都是零。

文档把 PR 的数据分成两大类，我们按这个分类来记：

| 大类 | 文件 | 后缀 | 谁给 | 一句话作用 |
|---|---|---|---|---|
| **design data** | netlist（网表） | `.v.gz` | 前端（综合后） | 有哪些单元、怎么连 |
| **physical data** | tech lef | `.lef` | 工艺厂/库组 | 工艺规则：金属层、宽度、间距、via |
| | cell lef | `.lef` | 库组 | 每个单元的形状、引脚位置 |
| | def | `.def.gz` | 上一道工序/顶层 | 这一版设计的实际物理数据（位置） |
| **timing data** | lib | `.lib` | 库组 | 单元的延迟与功耗（工具算 cell delay） |
| | rc tech file | `.tluplus` / QRC tech | 工艺厂/库组 | 单位电阻电容（工具算 net delay） |
| | sdc | `.sdc` | FCT/时序组 | 时序约束：优化的目标 |
| **环境** | MMMC（viewDefinition.tcl） | `.tcl` | 项目组 | 多模式多端角的配置 |

:::term physical data | 物理数据
和"物理形状、位置、工艺规则"有关的数据：lef、def 都属于这一类。它们决定"东西长什么样、放在哪"，但不决定"延迟是多少"。
:::

:::term timing data | 时序数据
和"延迟、约束"有关的数据：lib（单元延迟）、rc tech（线延迟）、sdc（约束）。它们决定工具算出来的时序对不对、优化目标是什么。
:::

一句记法：**physical data 管形状位置，timing data 管快慢与目标。**

## netlist：逻辑连接的文字描述 {#netlist}

:::term gate-level netlist | 门级网表
综合之后的网表，里面全是标准单元和宏单元（触发器、与非门、mem 等）的实例与连线，不再有 `always`、`if` 这种行为级描述。文件名一般就是模块名（tile 名）加 `.v.gz`。
:::

理解 netlist 最好的办法是看一个"从行为到门"的例子。RTL 里可能只写了一行：

```verilog
// RTL：一个 8 位计数器，rst 下降沿异步清零
always @(posedge clk or negedge rst)
  if (!rst) cnt <= 8'd0;      // 复位有效（低电平）就清零
  else      cnt <= cnt + 1;   // 否则每个时钟加一
```

综合工具把它翻译成实际电路后，netlist 里看到的是这种东西：

```verilog
// 综合后的网表（节选，示意）：只剩单元实例和连线
DFFR_X1  cnt_reg_0_  (.D(cnt_n_0_), .CK(clk), .RN(rst_n), .Q(cnt[0]));  // 第 0 位触发器
INV_X2   g12         (.A(cnt[0]),   .ZN(cnt_n_0_));                     // 反相器：计数取反
NAND2_X1 g13         (.A(cnt[1]),   .B(cnt[0]), .ZN(n_23));             // 与非门：进位逻辑
```

差别一眼可见：**RTL 描述行为，netlist 描述连接**。而两者都**没有坐标**——这就是为什么还需要 def 和 lef。

:::pitfall 拿到的 netlist 是 RTL 而不是门级
**现象**：init 之后工具报大量 `Cannot find cell`，说找不到 `always`、`if` 之类的东西。
**原因**：给的是 RTL 源文件，没有经过综合，里面的语法不是单元实例。
**怎么确认**：打开文件搜一下，如果满屏 `module ... always @(...)` 就是 RTL；门级网表里全是 `XXX_X1 u123 (...)` 这种实例行。
:::

## 文件名不是随便起的：命名是防事故的第一道墙 {#naming}

真实项目里，**你从目录里一堆文件里挑对那一份**的能力，比你想象的更重要。所以先认清命名规则。

### 网表：模块名 + 后缀 {#naming-netlist}

| 后缀 | 含义 | 备注 |
|---|---|---|
| `.v` | 明文 Verilog | 能直接 `grep`，但文件大 |
| `.v.gz` | gzip 压缩 Verilog | **最常见** |
| `.gz` | 压缩包 | 有时多个文件打一起 |

规则只有一条：**文件名主体 = 模块名，全部小写**。模块叫 `ALU` 就是 `alu.v.gz`，叫 `IOU` 就是 `iou.v.gz`。因为脚本会拿模块名拼路径（`./data/${top}.v.gz`），大小写不一致就找不到。

### sdc：把"模式 + 角落"写进名字 {#naming-sdc}

:::fig pr-netlist-sdc | 典型交付文件：网表 leon.vnet.gz 与 sdc leon.func.slow_rcworst.sdc.gz
:::

看右边那个 sdc 文件名，它把三件事写全了：

```
leon . func . slow_rcworst . sdc.gz
 │      │        │            └── 后缀：sdc 约束文件
 │      │        └────────────── 端角：慢速 + 最坏 RC（slow / rcworst）
 │      └─────────────────────── 模式：功能模式（func）
 └────────────────────────────── 设计名：leon
```

**为什么 sdc 要按 mode × corner 分开？** 因为不同模式、不同角落的约束本来就不一样（上一章 MMMC 讲过）。如果一个项目里有 func/scan 两种模式、slow/fast 两个角落，那就会有 4 个 sdc——名字必须能区分，否则你一定会拿错。

### 文件放在哪：Release 路径 {#naming-path}

```
/proj/<项目名>/ME/<模块名>/xxx.v.gz     ← 中端（综合后）release 的网表在这
/proj/<项目名>/DE/<模块名>/xxx_rtl.v    ← 前端 release 的 RTL 在这
```

**Release 是个动作**：把本地做好的东西**上传到服务器约定路径**，让下游能取。所以接手一个模块，第一句该问的是"**release 路径在哪**"——有路径就有版本、有时间戳、有 owner。

:::tip 这一节的详细版在单独一课
网表版本怎么迭代（V1.0 → V9.0）、S1/S2 两版网表各干什么、instance 数为什么从 200 万跳到 400 万、模块从矩形变 L 型为什么白干两个月——这些都放进了 [网表版本、Release 与迭代协作](/lesson/02-04a-netlist-release/) 那一课。
:::

## def：这一版设计的"实际位置" {#def}

:::term DEF | 设计交换格式
Design Exchange Format。存储一个设计**当前的实际物理数据**：design 名、die 大小、track 信息、每个单元/端口的具体坐标与朝向、布线结果（视导出阶段而定）。
:::

def 最大的价值是**跨工具、跨团队交换**。文档给了两个典型场景：

1. **跨工具**：用 Innovus 跑到 place，接着想用 ICC2 跑 cts——就把到 place 为止的所有物理信息导出成 def，喂给 ICC2。
2. **跨层级**：top 确定好每个 block 的面积和 port 位置后，用 def 发给每个 block 的 **harden owner**（模块负责人）。

命令对照（记住这一对就够用）：

```tcl
# Innovus：导出 / 读入 def
defOut floorplan.def        ;# 把当前物理数据吐成 def 文件
defIn  floorplan.def        ;# 读入别人给的 def（比如 top 下发的边界）

# ICC2 / Fusion Compiler：同一件事，命令名不同
write_def floorplan.def     ;# 导出
read_def  floorplan.def     ;# 读入
```

:::term harden | 硬化（模块定版）
block 做到"形状、端口、时序都定下来，可以被顶层直接当黑盒使用"的状态。owner 就是负责这块的人。top 给他 def 定边界，他做完再交回 def/GDS。
:::

:::term Hard Block / harden | 硬块
口语里的 **Hard**、**Hard Block**、**harden 过的模块**，说的是同一件事：**已经有真实物理信息（面积、pin 位置、布线结果）的模块**。

与之相对的是"软"的 netlist——只有逻辑连接，没有面积和位置。**从软到硬，就是 PR 干的事。**
:::

:::note 为什么 def 比 GDS 更适合当"合同"
GDS 是最终版图，信息量大但改起来重；def 是轻量的"位置清单"，读入快、可编辑、工具间通用。所以 block 与 top 之间反复迭代阶段用 def 交接，最后定版才用 GDS。
:::

## lef：两个文件，两种信息 {#lef}

lef 有两个，名字像但作用完全不同，**这是新人最容易混的一对**：

:::term tech lef | 工艺 LEF
描述**工艺本身**：能用哪些金属层（M0/M1/M2…，层数取决于工艺）、每层的最小宽度与间距、via 的定义与电阻、横纵向走线方向等。它跟具体设计无关，一个工艺一份。
:::

:::term cell lef | 单元 LEF
描述**每个单元**：长、宽、高，有几个输入 pin、几个输出 pin、pin 在什么位置、什么方向。工具靠它知道"这个单元占多大地方、线该接到哪"。
:::

下一课会用一整课把这两种 lef 拆开看（含 pitch、DRC、obs 这些细节）。

## lib / rc tech / sdc：三个"算延迟和定目标"的文件 {#timing-files}

这三个是 timing data，作用一句话区分：

| 文件 | 回答什么问题 | 缺了会怎样 |
|---|---|---|
| **lib** | 这个单元在给定输入转换时间、给定负载下，延迟是多少？ | 工具算不出 cell delay，时序报告全是 0 或直接报错 |
| **rc tech** | 这段线每单位长度的电阻电容是多少？ | 算不出 net delay，长线的影响被低估 |
| **sdc** | 我要优化到什么程度？时钟多快？哪些路径不用管？ | 工具没有目标，等于没有优化 |

:::term lib | 单元时序/功耗库
描述每个标准单元的延迟、功耗、功能与面积。工具用**查表**的方式算延迟：给一个输入转换时间（input transition）和一个输出负载（output load），在二维表里插值出延迟值。
:::

:::term rc tech file | RC 工艺文件
记录单位长度的寄生电阻 R 与寄生电容 C，供工具抽取/估算 net 的寄生参数，进而算线延迟。抽取寄生参数的专业工具是 **StarRC**（Synopsys）和 **QRC**（Cadence）。
:::

lib 和 rc tech 的细节在第 6 课（cell delay 与 net delay 怎么算），sdc 在第 8 课，MMMC 在第 7 课。这一课你只要建立"哪个文件解决哪类问题"的直觉。

## init 的顺序感：为什么先物理后时序 {#order}

工具内部的顺序其实很朴素：

1. 先读 **lef**：知道这个工艺有哪些层、每个单元长什么样（没有 lef，工具连"地方"都画不出来）；
2. 再读 **netlist**：知道有哪些单元实例、怎么连；
3. 再读 **lib + rc tech**：知道延迟怎么算；
4. 再读 **sdc + MMMC**：知道优化目标与场景；
5. `init_design`：把上面这些"组装"成一个可操作的设计。

所以报错也基本按这个顺序出现：先报找不到 lef，再报找不到 cell，再报找不到 library，最后才是约束相关的警告。

## 缺文件的真实报错对照 {#errors}

文档没给报错原文，这里补上你在 Innovus/ICC2 里真会看到的几类，按"报错 → 缺什么 → 怎么查"记：

| 报错关键词 | 真正缺的 | 怎么查 |
|---|---|---|
| `Cannot find library 'xxx' in the search path` | lib 没读到，或库名与 lef/网表里写的不一致 | 打印库搜索路径；`ls` 确认 .lib/.db 文件名 |
| `Cannot find cell 'INV_X1'` | cell lef 没读全，或工艺库版本不对 | 在 cell lef 里搜 `MACRO INV_X1` |
| `Cannot find port/pin ...` | def 与当前 lef 版本不匹配（pin 名或形状变了） | 对比 def 与 lef 的版本/日期 |
| `No link library` / `link 失败` | 只有 netlist，没给 lib/lef | 按上面 init 顺序补 |
| 时序报告全是 0 或没有 clock | sdc 没读进来、`create_clock` 没生效 | 打印时钟列表，看有没有 clock |

:::pitfall 版本对不上比缺文件更麻烦
**现象**：文件都在，但 def 读进去后一堆单元位置"漂"了，或 pin 找不到。
**原因**：def 是用旧版 lef 导出的，而你现在用的是新版库——单元尺寸或 pin 位置变了。
**怎么避免**：交付目录里永远记下 lef/lib 的版本号与日期；跨团队交接时，先对一遍"你用的库版本和我的一样吗"。
:::

:::lab 给自己列一张交接清单
假设 leader 让你接手一个 block，请写出一张"我要什么文件"的清单，每项包含：文件名/后缀、谁给、用来干什么、缺了会报什么错。

再补一条软性要求：向对方要文件时，必须同时要到**库版本号**（lef/lib 的日期或版本），否则后面所有对不上的问题都会算在你头上。

验收标准：清单不少于 8 项（netlist、tech lef、cell lef、def、lib、rc tech、sdc、MMMC）；能说出 def 与 lef 的区别；能背出 Innovus 与 ICC2 导入/导出 def 的命令差异。
:::

:::quiz
init 阶段需要哪几类文件？| design data（netlist）、physical data（tech lef / cell lef / def）、timing data（lib / rc tech / sdc），外加 MMMC 环境（viewDefinition.tcl）。
netlist 和 def 的核心区别是什么？| netlist 只描述逻辑连接（谁连谁），没有坐标；def 描述这一版设计的实际物理数据（die 大小、单元与端口的具体位置）。
lef 为什么有两个？| tech lef 描述工艺规则（金属层、宽度、间距、via），与设计无关；cell lef 描述每个单元的形状与引脚。两者作用完全不同。
top 为什么用 def 而不用 GDS 给 block owner 定边界？| def 轻量、可编辑、工具间通用，适合反复迭代；GDS 信息量大但改动成本高，一般只在定版后交接。
导出/读入 def 的命令在 Innovus 和 ICC2 里分别是什么？| Innovus：`defOut` / `defIn`；ICC2（及 Fusion Compiler）：`write_def` / `read_def`。
`Cannot find cell 'INV_X1'` 通常说明什么？| cell lef 没读全，或工艺库版本与网表不匹配；也可能库搜索路径没配对。
:::

:::check
- 能不看书列出 init 需要的 8 类文件并说出各自作用
- 能解释 netlist 是逻辑连接、def 是物理数据
- 能说出 tech lef 与 cell lef 的分工
- 能写出 Innovus 与 ICC2 的 def 导入导出命令
- 看到 `Cannot find library` / `Cannot find cell` 能定位到缺哪个文件
:::
