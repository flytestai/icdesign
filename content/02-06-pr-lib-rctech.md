---
id: 02-06-pr-lib-rctech
no: 22
stage: 2
title: lib 与 rc tech：延迟到底是怎么算出来的
en: lib and RC Tech: How Delay Is Computed
hours: 2
minutes: 30
tags: [lib, 单元延迟, 查表, transition, load, rc tech, 寄生参数, PVT, 温度反转]
summary: 时序数据只有两份文件：lib 负责单元延迟，rc tech 负责线延迟。这一课打开 lib 看它到底存了什么、工具怎么用查表的方式算出一个 cell 的 delay，讲清 input transition 与 output load 这两个决定性变量，再把 lib 文件名的每一段（台积电/lvt/ssg/0p81v/125c）拆开读，最后讲 PVT 与先进工艺的温度反转效应。
---

## 两种延迟，两份文件 {#why}

:::goal 能说出"路径延迟 = Σ cell delay + Σ net delay"并指出两部分各由 lib 还是 rc tech 提供；能解释查表的两个索引、index 从 0 开始这件事；能逐段读出 lib 文件名里的工艺、阈值电压、快慢组、电压与温度；能说出温度反转效应的成因与后果。
:::

一条路径的延迟由两部分组成，缺一不可：

```
路径延迟 = Σ 单元延迟（cell delay） + Σ 线延迟（net delay）
                ↑                        ↑
            由 lib 提供             由 rc tech 提供
```

- **单元延迟**：信号穿过一个 stdcell（反相器、与非门、触发器）花的时间。数据在 **lib** 里。
- **线延迟**：信号沿着一根导线从上一级输出走到下一级输入花的时间。数据由 **rc tech file** 提供的寄生参数算出来。

前面几课讲的 netlist、def、lef 全是"连接关系与几何形状"，这一课才进到"时间"。**PR 工具优化的目标就是这两项之和**——所以你必须知道它们各自受什么影响，否则看到时序报告里的 violation 只会干瞪眼。

## lib：单元延迟与功耗的字典 {#lib}

:::term lib | 单元库时序功耗文件
Liberty 格式的库文件，描述每个标准单元的：物理属性（面积、引脚电容）、功能（是 and 还是 or）、时序信息（延迟查表）、功耗信息（漏电、内部功耗）。**一个 PVT 组合一份 lib**，所以一个工艺往往有几十份 lib。
:::

文档说 lib 主要包括三块内容，我们逐块看：

### 1. 物理单元库的基本属性 {#attr}

```liberty
library (tsc28_lvtssg0p81v125c) {     # 库名，通常就写在文件名里
  delay_model : table_lookup ;        # 关键：延迟用查表模型算，不是公式现算
  time_unit : "1ns" ;                 # 时间单位 1ns
  capacitive_load_unit (1, pf) ;      # 负载电容单位 1pF
  voltage_unit : "1V" ;
  current_unit : "1mA" ;
  pulling_resistance_unit : "1kohm" ;
  leakage_power_unit : "1nW" ;
```

这几行看起来是"模板废话"，但它们决定了你读报告时数字的量级。**单位看错十倍，结论就全错**——延时报告里 `0.052` 到底是 52ps 还是 52ns，全看这里。

### 2. 每个 cell 的功能 {#func}

```liberty
cell (NAND2_X1) {
  area : 1.4 ;                        # 面积，布局时用来估算占用
  cell_leakage_power : 0.0032 ;       # 静态漏电功耗（不翻转也在漏）
  pin (A) {
    direction : input ;
    capacitance : 0.0021 ;            # 输入引脚电容：上一级要驱动它
  }
  pin (B) {
    direction : input ;
    capacitance : 0.0021 ;
  }
  pin (ZN) {
    direction : output ;
    function : "!(A B)" ;             # 功能：A 与 B 再取反 → 这就是"与非"
    max_capacitance : 0.15 ;          # 这个输出最多能带多大负载，超了不保证时序
  }
}
```

`function : "!(A B)"` 这一行告诉工具"这个单元干什么"。**注意它和 lef 的分工**：lef 只说"A 是输入、在左边、尺寸 0.5×1.2"，lib 才说"它把 A 和 B 做与再取反"。所以 lef 缺了工具不知道怎么连，lib 缺了工具不知道算什么。

`max_capacitance` 也是新人常踩的点：**一个输出的驱动能力有上限**，负载超了就算"电气违规（electrical violation）"，工具会插 buffer 或者直接把单元换成驱动更大的版本（X1 → X2 → X4）。

### 3. 时序与功耗信息：查表 {#table}

这是 lib 最核心的部分。工具**不用公式现算延迟，而是查表 + 插值**，这就是 `delay_model : table_lookup` 的含义。

一张 3×3 的延迟表长这样（单位 ps）：

```
                          output load (pF)
                        0.5     1.0     2.0
             0.02  →   12.1    18.4    27.9
input        0.05  →   15.6    22.0    31.2
transition   0.10  →   21.3    28.5    38.7
```

:::term 查表 table lookup
按两个索引（输入 transition、输出 load）去表里定位，落在格点之间就做线性插值。文档里的说法："输入 pin 是第二个值，输出是第三个值，就查表中（1，2）——**索引从 0 开始**。" 所以实际表里的第 2 行第 3 列，代码里写的是 `[1][2]`。
:::

为什么是这两维？因为它们就是决定延迟的两个物理量，看下一节。

### 决定 cell delay 的两个量（本课最该记住的一句） {#two}

:::tip 一个 cell 的延迟，只由两件事决定
1. **input transition（输入转换时间）**——信号从 0 爬到 1 有多"软"；
2. **output load（输出负载）**——这个输出身上挂了多少电容要它充放电。
:::

物理直觉很好理解：

- **输入越"软"（transition 越大）**，晶体管在阈值附近停留的时间越长，通过的电流越小，**延迟越大**；
- **负载越重（load 越大）**，要搬的电荷越多，充放电越慢，**延迟越大**。

所以延迟表一定是"右下角最大"——这跟你开车一样：起步越肉、拉得越重，到终点越慢。

### transition 的值从哪来 {#transition}

新人常问："表里第一维是 input transition，可这个值是谁给我的？"

答案是**上一级的输出 transition 传下来的**：

```
前一级输出的 transition  →  成为后一级的 input transition  →  决定后一级的 cell delay
                                                              ↓
                                                    产生新的 output transition
                                                              ↓
                                                    继续往下一级传……
```

所以时序计算是**沿路径逐级传播**的链式过程，起点是输入端口的 transition 或者时钟源的 transition。这也解释了两个常见现象：

1. **输入端口的 transition 必须约束**（SDC 里的 `set_input_transition`）——它是整条链的源头，源头不给值，后面全算不准；
2. **长链上串了太多级，transition 会逐级恶化**，最后一级延迟暴增——这就是为什么工具要插 buffer 来"重整" transition，而不是只看级数。

## lib 文件名：一串密码，读懂就知快慢 {#naming}

```
tsc28_lvtssg0p81v125c.lib
 │     │   │  │     │
 │     │   │  │     └── 125c   = 125°C（m40c 就是 -40°C）
 │     │   │  └──────── 0p81v  = 0.81V（p 代表小数点）
 │     │   └─────────── ssg    = 慢速低压（slow-slow global）
 │     └─────────────── lvt    = 低阈值电压（low Vt）
 └───────────────────── tsc    = 台积电（TSMC）
```

逐个拆开：

| 段 | 含义 | 说明 |
|---|---|---|
| `tsc` | 台积电 | 不同晶圆厂的库前缀不同，S 家/中芯各有一套 |
| `lvt` | 阈值电压等级 | `lvt` 低阈值（快、漏电大）、`svt` 标准阈值、`hvt` 高阈值（慢、省电） |
| `ssg` / `ffg` | 工艺快慢 | `ssg` 慢速低压、`ffg` 快速高压；`tt` 是典型（typical） |
| `0p81v` | 电压 | 0.81V |
| `125c` / `m40c` | 温度 | 125°C / -40°C（`m` = minus） |

:::term PVT | 工艺-电压-温度
**P**rocess（工艺变化参数，P 对应 ss/tt/ff）、**V**oltage（电压）、**T**emperature（温度）。三者一起定义了"这颗芯片在什么条件下工作"，一个 PVT 组合对应一份 lib。PR 必须同时满足**最慢**和**最快**两端，所以库里同时要看 ss 和 ff。
:::

规律记两条，够用了：

- **电压越大，delay 越小**（电压高压差大、驱动电流强）；
- **同工艺下 ss 组（慢速低压）延迟最大，ff 组（快速高压）延迟最小**。

## 温度：常规规律与温度反转 {#temp}

正常情况下，**温度越高，delay 越大**。原因是高温下晶格振动加剧，载流子迁移率下降，电流变小。

但文档特别点出了先进工艺的一个反直觉现象：

:::pitfall 温度反转效应（temperature inversion）
在先进工艺（大致 28nm 往下越来越明显）里，**温度越低，delay 反而越大**。

**原因**：低电压下，晶体管的阈值电压 Vt 随温度降低而升高，"过驱动电压（Vdd - Vt）"被压缩，电流急剧变小——这个效应盖过了迁移率的影响。低压 + 低温是最坏的组合。

**后果**：不能想当然地"高温才算最坏 corner"。setup 检查里必须把低温 corner（如 `m40c`）也拉进来一起看，否则流片后在冷机启动/低温环境里翻车。

**怎么用**：看到库里同时有 `125c` 和 `m40c` 两个版本，就说明签核必须两端都跑。
:::

## rc tech file：线延迟从哪来 {#rctech}

:::term rc tech file | 寄生参数工艺文件
描述金属层与通孔的**单位长度电阻、单位长度电容**等寄生参数模型，工具用它把版图上的几何形状（多长、多宽、周围有什么）换算成实际的寄生 R 和 C，进而算出线延迟。
:::

文档的定义很干脆：**"存储线上的寄生参数，用于抽取寄生电阻和电容，用于计算 net delay。"**

### 为什么线延迟不能简单按长度算 {#whyrc}

一根导线的延迟不是一个固定系数乘长度就完事，它取决于：

1. **导线自身**：长度、宽度、所在金属层（层越高越厚、电阻越小）；
2. **周围环境**：上下左右有没有别的线（耦合电容）、离电源地多远；
3. **工艺参数**：这一层的方块电阻、单位面积电容、通孔电阻。

所以公式的形态是：

```
net delay = f( R_寄生 , C_寄生 , 驱动能力 )
            ↑           ↑
       rc tech 给出系数 × 版图几何
```

文档把它和 lib 对照着说得很清楚：**"cell delay 是一个函数，net delay 也是一个函数，和电阻和电容有关。"** 两个都是函数，只是一个查表、一个算 RC。

### 谁来抽寄生参数 {#extract}

| 工具 | 厂商 | 说明 |
|---|---|---|
| **StarRC** | Synopsys | 文档写作 Starrc，最主流的寄生抽取工具 |
| **QRC** | Cadence | Cadence 体系里的对应工具（Quantus） |

PR 过程中工具自己会做**估算型抽取**（estimate / trial route 阶段用简化的 RC 模型，跑得快）；等到 route 完成要签核时，才用 StarRC/QRC 做**精确抽取**，吐出 SPEF 文件给 STA 用。所以你会看到同一版设计在不同阶段报告的数字不一样——**不是工具算错了，是抽取精度不同**。

### 各种不同的环境 {#env}

同一根线，在不同环境下 RC 差别很大，所以 rc tech 也是**一组**文件而不是一个：

- **不同金属层**：M1 细而薄、电阻大；高层金属厚、电阻小，常用于长线；
- **不同 RC corner**：工艺偏差导致 R、C 各有快慢，组合出 `cworst`（电容最大）、`rcworst`（都最坏）、`cbest`（电容最小）等；
- **不同温度**：温度升高，金属电阻变大（文档原话："一段导线，温度越高，电阻越大"）。

:::tip 一句话区分 setup 和 hold 该看哪个 corner
- **线越慢 → setup 越差**（信号来不及到）；
- **线越快 → hold 越差**（信号来得太早，把该留的旧值冲掉了）。

所以 setup 用"慢"的 RC corner，hold 用"快"的 RC corner。这也是下一课 MMMC 要解决的核心问题。
:::

## 三份文件的分工，一张表看完 {#summary-table}

| 文件 | 管什么 | 决定什么 | 谁提供 |
|---|---|---|---|
| **lib** | 每个 cell 的时序/功耗/功能 | cell delay | 库组 / 晶圆厂 |
| **rc tech** | 线上的寄生 R、C 模型 | net delay | 工艺厂 / 库组 |
| **sdc** | 时钟、输入输出延迟、假路径 | 优化的**目标** | FCT 部门（下一课） |

前三者提供"事实"，sdc 提供"要求"。**没有 lib 和 rc tech，工具算不出时间；没有 sdc，工具不知道该往哪优化。**

:::lab 在 lib 里查三样东西
用课程页的练习终端（或真机）跑下面几条，边跑边看输出：

```bash
# 看库的基本单位与延迟模型：确认时间单位是 ns 还是 ps
grep -n "time_unit\|delay_model\|capacitive_load_unit" tsc28_lvtssg0p81v125c.lib | head

# 找一个单元，看它的功能和引脚电容
grep -n -A12 "^  cell (NAND2_X1)" tsc28_lvtssg0p81v125c.lib

# 数一数这个库里有多少个单元
grep -c "^  cell (" tsc28_lvtssg0p81v125c.lib

# 看它有哪些 RC corner 相关的环境目录
ls -d */ | head -20
```

验收标准：能说出这个 lib 的时间单位、`NAND2_X1` 的功能表达式、它的输入引脚电容值，以及它是 ss 组还是 ff 组（从文件名判断）。
:::

:::quiz
一个 cell 的延迟由哪两个量决定？| input transition（输入转换时间）和 output load（输出负载电容）。transition 越大、load 越重，延迟越大。
工具怎么用 lib 算延迟？| 查表 + 插值。按（input transition, output load）两个索引定位表项，落在格点之间做线性插值；索引从 0 开始。
input transition 这个值是谁给的？| 上一级输出的 transition 传下来的，沿路径逐级传播；源头是输入端口或时钟源的 transition，所以要用 set_input_transition 约束。
lib 与 rc tech 各算哪种延迟？| lib 算 cell delay（单元延迟）；rc tech 提供寄生 R/C 用于算 net delay（线延迟）。
`tsc28_lvtssg0p81v125c.lib` 这个文件名能读出什么？| 台积电 28nm、lvt 低阈值电压、ssg 慢速低压、0.81V、125°C。
电压和温度对 delay 的影响是什么？| 电压越大 delay 越小；常规情况温度越高 delay 越大，但先进工艺存在温度反转效应——低压低温时温度越低 delay 反而越大。
为什么线延迟需要用 StarRC/QRC 抽取而不是按长度估？| 因为线延迟取决于长度、宽度、金属层、周围耦合环境等多个因素，要靠寄生抽取把版图几何换算成实际 R/C。
:::

:::check
- 能说出"路径延迟 = Σ cell delay + Σ net delay"，并指出两部分各由哪份文件提供
- 能解释查表的两个索引是什么，以及为什么索引从 0 开始
- 能背出"一个 cell 的延迟由 input transition 与 output load 决定"
- 能逐段读出 lib 文件名里的工艺、Vt 类型、快慢组、电压、温度
- 能说出 PVT 三个字母各代表什么，以及温度反转效应的原因与后果
- 能说出 setup 看慢 corner、hold 看快 corner 的理由
:::
