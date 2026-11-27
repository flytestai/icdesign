---
id: 03-05-floorplan
no: 35
stage: 3
title: Floorplan：芯片尺寸、端口、宏与约束
en: Floorplan
hours: 10
tags: [Innovus, 40nm, 项目实操, Floorplan]
summary: 从 site/row/port/pin/terminal 这些基本概念，到 Die/Core 定义、端口摆放、宏摆放四规则、六类物理单元、guide/region/fence 三种分组约束、四类 blockage，最后是质量评估标准。每段原文后都有展开讲解，21 张原图配逐图说明。
---

## 先说清楚：Floorplan 定错了，后面全白干 {#why}

Floorplan 是整条流程里**唯一一个"错了要全部重来"**的步骤。

原因很简单：后面所有阶段都在这个地基上干活。

- 宏放错位置 → 布线通道不够 → 大量短路 → 回 Floorplan 挪宏 → place、CTS、route 全部重跑；
- Die 定小了 → 单元摆不下 → 只能压利用率 → 密度过高 → 拥塞和时序双崩；
- 端口分配错了 → 顶层对接不上 → 芯片做出来封不了装。

而且这几件事**互相牵制**：Die 大了浪费成本，Die 小了摆不下；宏集中放省通道，但会造成局部密度爆炸；端口全堆一边好走线，但顶层 PCB 接不出来。

所以 Floorplan 不是"填几个数字"，是在一堆矛盾里找可行解。本课按实际操作顺序走，每一步告诉你**判据是什么、错了会怎样**。

:::term Floorplan | 布局规划
确定芯片物理边界（Die）、可摆放区域（Core）、输入输出端口（Port）位置、宏单元（Memory/IP）位置与朝向，以及各种约束区域的过程。它决定了后续所有阶段可用的空间资源。
:::

## 视图与基本概念：先认词，再动手 {#source-01}

Floorplan 里有五个词天天用，但它们的关系很多人一直没理清：**site、row、port、pin、terminal**。这五个词搞混了，后面所有命令参数都会填错。

### 三种视图，看到的东西不一样

**Floorplan 阶段的视图**和 **place 之后的视图**是两个东西：前者主要看宏、core 边界、端口；后者密密麻麻的标准单元行铺满，宏被单元包围。

切换靠右侧面板的 V/S 两列。**V（Visible）控制看得见，S（Selectable）控制选得中，两者独立。** 这是排查问题的核心技巧——想看清宏之间的通道，把 Standard Row 的 V 关掉，行线消失、通道一目了然；但关掉 V 之后那些行也选不中了。只想看得清又要能选，就留 V 开、只关 S。

:::source
"三、Floorplan"
"innovus的几种视图"
:::

:::fig innovus-doc-09.png | 原文图 09 · 视图与布局规划基础
:::

:::note 这张图该看什么
顶部菜单按工序排列：Floorplan → Power → Place → ECO → Clock → Route → Timing，这就是流程顺序。左侧竖排是快捷按钮，右侧面板的 V/S 两列是工具最实用的设计。版图区颜色不是随意的：紫色通常是宏，细密横纹是标准单元摆放行，黄色小方块是引脚。左上角 `TU=69.9%` 是总利用率。
:::

### site：摆放的最小单位

这句话是整个布局的基础：**任何标准单元的宽度，一定是 site 宽度的整数倍。**

为什么必须这样？因为标准单元的电源轨（VDD/VSS rail）要横贯整行。如果宽度不是 site 整数倍，相邻单元的电源轨就对不上，行就连不起来。

**实用推论**：估算一行能放多少单元，用「行宽 ÷ site 宽度」得到**格数**，再把每个单元占的格数加起来。不是按面积除，是按格子数。

:::source
"1）一些floorplan的概念"
"site:  placement的最小单位，任何cell的宽度一定是site的整数倍"
:::

:::fig innovus-doc-10.png | 原文图 10 · 视图与布局规划基础
:::

:::note 这张图该看什么
右侧控制面板展开后的完整层级。注意 Row 分类下 Standard Row / Row Pattern / CoreSite / Macro Pattern 各有独立的 V 和 S 复选框——不是总开关。

实用场景：检查宏之间通道多宽时，只关 Standard Row 的 V，通道边界立刻清楚。但关 V 后也选不中这些行了。
:::

### row：单元必须站在行上

行（row）是水平条带，高度正好等于标准单元高度，由 site 沿横向重复排成。

原文给了一个很具体的后果链，值得逐个环节理解：

:::source
"row： 约束cell的摆放，必须摆在row上，高度等于stdcell的高度"
"如果不在row上会有什么问题？"
"如果不在row上，就是没有legalize， 会导致底层color不对 ，引发basedrc问题"
"dobulepattern "
"解决方法：  如果数量不多，可以手动legalize,手动挪动cell到row上"
"如果数量较多，用Legalize placement 自动legalize"
:::

:::fig innovus-doc-11.png | 原文图 11 · 视图与布局规划基础
:::

:::note 这张图该看什么
关闭摆放行显示后的同一设计。左侧紫色宏仍可见，中间行线已隐藏，只剩 core 边界和空白区。这就是靠关闭 V 得到的视图——对比前一张图即可建立「开关不同看到的东西完全不同」的直觉。
:::

**后果链拆解**：

1. **不在 row 上 = 没 legalize**：单元坐标不在任何一行的格点上；

2. **底层 color 不对**：20nm 以下工艺的底层金属要做双重图形（double patterning），同一层图形分成两种颜色分别曝光。单元的颜色在库设计时就与位置、朝向绑定，没对齐格点颜色映射就乱了；

3. **base DRC 违例**：颜色冲突直接表现为规则违例，版图做不出来。

修法两档：数量少手动挪，数量多用 `Legalize placement` 自动处理。

:::tip 「没在 row 上」的三个典型来源
1. **手改坐标**：为避让障碍把单元 `dbset` 到任意坐标；
2. **ECO 插单元**：`ecoAddRepeater -loc` 给的坐标不在格点；
3. **导入别处的 DEF**：坐标系或 site 定义不一致。

第三种最隐蔽——DEF 导进来看着都对，一跑 DRC 一片违例。所以导入 DEF 后必须做一次 legalize 检查。
:::

### port、pin、terminal：三个层次别混

:::source
"port:  是整个模块的端口、信号接口"
:::

:::fig innovus-doc-12.png | 原文图 12 · 视图与布局规划基础
:::

:::note 这张图该看什么
局部放大到宏边角的视图。紫色斜纹是宏，红色三角是工具标出的违例/警告标记，黄色交叉线框是选中对象的边界框。

红色三角不要慌，先双击或按 `q` 查它属于哪一类标记——不同原因的标记长得一样，修法完全不同。
:::

:::source
"pin：标准单元或者mem的输入端口输出端口"
:::

:::fig innovus-doc-13.png | 原文图 13 · 视图与布局规划基础
:::

:::note 这张图该看什么
标准单元或宏的引脚在版图上的呈现（黄色小方块/细长条）。这类引脚是有物理尺寸的金属 shape，不是抽象连接点。
:::

:::source
"terminal：为了将port的逻辑连接，变成物理连接，需要创建metalshape，也就是一段金属，这就是terminal"
:::

:::fig innovus-doc-14.png | 原文图 14 · 视图与布局规划基础
:::

:::note 这张图该看什么
terminal 的实际形态——模块边界上的一段金属。它把 port 的逻辑名字变成可布线的物理对象。
:::

三者的关系可以这样串起来：

| 词 | 是什么 | 在哪一层 |
|---|---|---|
| **port** | 整个模块对外的信号接口 | 模块边界（顶层） |
| **pin** | 标准单元或宏的输入输出脚 | 单元/宏边界 |
| **terminal** | port 的物理实现——一段金属 shape | 模块边界上的实际图形 |

**报错信息经常在这三个层次间跳**，分清才知改哪里：

- `port not placed` → 逻辑接口没分配物理位置；
- `terminal out of boundary` → 物理图形超出 die 边界；
- `unconnected port` → 有 port 但没接线。

### cell density：密度高为什么会短路

原文一句话把因果讲完了，展开就是一条完整的链条：

:::source
"cell density  单元的密度"
"如果density过高，会导致什么问题？会导致routing resource（绕线的资源） 不足"
"出现short"
:::

## 定义芯片尺寸与异形 Die {#source-02}

这一节从「概念」进入「动手」：把 die 和 core 的边界定下来。

### 定尺寸的入口

原文流程是「1、定义芯片的大小 → 页面上的操作」，即从菜单进。

:::source
"2） floorplan的流程"
"教学版："
"1、定义芯片的大小"
"页面上的操作"
:::

:::fig innovus-doc-15.png | 原文图 15 · 定义芯片尺寸与异形 Die
:::

:::note 这张图该看什么
Specify Floorplan 菜单的打开路径。下拉按用途分四组：定义边界（Specify/Resize/Relative/Automatic）、辅助工具（Floorplan Toolbox/Trace Macro/Macro Timing Slack Display）、编辑（Edit Floorplan 含各类 blockage、Snap、Clear）、检查生成（Check/Generate）。

日常最常用三个：Specify Floorplan 定尺寸、Floorplan Toolbox 摆宏、Edit Floorplan 加约束区。
:::

:::fig innovus-doc-16.png | 原文图 16 · 定义芯片尺寸与异形 Die
:::

:::note 这张图该看什么
这是整门课最该看懂的一张。逐项拆解：

**① Specify By 三选一**：Core Size by（给利用率反推 die）、Die Size by（直接给宽高，最常见）、Die/IO/Core Coordinates（直接给坐标）。本例选 Core Size by。

**② Aspect Ratio = 0.7097**：高宽比，由封装或顶层占位决定。偏离 1 太多会让长边走线过长，时序吃亏。

**③ Core Utilization 0.706 vs Cell Utilization 0.513**：前者算 core 内所有占用（含宏和物理单元），后者只算标准单元。差值约 19% 就是宏占的面积。

**④ Dimension 596.79 vs Die Size 600.21**：差 3.42，正好等于上下边距 1.71 × 2。所以 Die 高 = Core 高 + 上边距 + 下边距，这个算式每次都要手工核一遍。

**⑤ Core Margins**：Core to IO Boundary（从 IO 环内侧算）或 Core to Die Boundary（从 die 边界算）。本例选后者，左右 0、上下 1.71，不对称是为电源环留空间。

**⑥ Floorplan Origin at**：左下角或中心，影响后续所有坐标解读。以上游交接清单为准，不要凭习惯选。
:::

### 异形 Die：切角怎么写

现实中的芯片很少是纯矩形，经常要切掉一角。看这张图的三个要点：

:::source
"定义异形die（针对die区域剪切的）"
"界面："
:::

:::fig innovus-doc-17.png | 原文图 17 · 定义芯片尺寸与异形 Die
:::

:::note 这张图该看什么
切异形的入口。①切角通常切在 core 边界上，不是 die 边界；②切口是直角台阶（rectilinear）不是斜线——制造用正交掩模；③切掉的区域不能再放东西，注意切口处没有摆放行。

切角的三个常见原因：封装需要（角落有定位结构）、顶层拼接（角落让给相邻模块）、避开物理障碍（TSV、bump）。

拿到切角要求后必须确认：切掉的区域里原本是否计划放宏？如果是，那些宏要重新找位置，可能连带改变通道宽度。
:::

### 命令形式：三个关键参数

:::source
"命令："
"设置支持异型剪切：setPreference EnableRectilinearDesign 1"
"剪切命令：addObjFPlanCutBox cell leon 0 0 20 80"
"吐出die的命令：writeFPlanScript -fileName box.tcl -sections {boundary block pins}"
:::

:::fig innovus-doc-18.png | 原文图 18 · 定义芯片尺寸与异形 Die
:::

:::note 这张图该看什么
floorplan.tcl 脚本内容。最能说明问题的是：GUI 里填的所有参数最终都变成一行 `floorplan` 命令——对照上一张图的对话框，`930.000000 600.210000000` 正是 Die Size 的宽高。

两条 addObjFPlanCutBox 叠加，正好形成上一张图里的 L 形切角。

**为什么必须脚本化**：GUI 参数只在内存，重跑凭记忆重填会有微小差异（这次 1.71、下次 1.7），所有坐标都变，此前检查报告全部作废。
:::

三行命令各有用处：

```tcl
setPreference EnableRectilinearDesign 1     ;# 前提：不开这个，切角命令被忽略
addObjFPlanCutBox cell leon 0 0 20 80       ;# 切角本体
writeFPlanScript -fileName box.tcl -sections {boundary block pins}  ;# 只导边界/阻挡/引脚
```

`-sections` 只导三类，脚本短、可读、适合交接。

## 摆放端口（Port） {#source-03}

端口位置定错了，后果比内部布线错更严重——内部错了还能改，端口错了可能要重新流片。

:::source
"2、摆放port"
:::

:::fig innovus-doc-19.png | 原文图 19 · 摆放端口与引脚约束
:::

:::note 这张图该看什么
Pin Editor 的打开路径。旁边几项也相关：Edit Pin Group（按组编辑，总线常用）、Edit Pin Guide（指定出线方向）、Bus Guide（总线级引导）。
:::

### 单层摆 vs 多层摆

原文给了两套命令，区别在于引脚是否分到多层金属。

:::source
"单层摆port命令："
"editPin -pinWidth 0.08  pin宽"
"-pinDepth 0.32              pin深"
"-fixOverlap 1   禁止重叠"
"-unit TRACK  对齐track"
"-spreadDirection clockwise  顺时针"
"-layer 5      摆pin的层数"
"-spreadType start 从开始点摆"
"-spacing 2 间隔2个track"
"-start 0 220 开始摆port坐标"
"-pin $input_ports 指定摆放的port "
"-fixedPin 固定port"
"-side LEFT 摆放方位"
"多层摆port命令："
"命令"
"editPin -fixOverlap 1 -fixedPin 1 -layer {M6 M8 M10} -pin \"$exif $sif\" -pinDepth 0.6 -pinWidth 0.038 -edge 3 -snap TRACK -spreadDirection counterclockwise -offsetStart 609 -unit TRACK -spacing 1 -pattern fill_checkerboard"
"解析"
"editPin -fixOverlap 1 自动修复引脚重叠"
"-fixedPin 1 锁定引脚位置"
"-layer {M6 M8 M10} 摆放金属层配置"
"-pin \"$exif $sif\" 操作对象"
"-pinDepth 0.6 引脚深度"
"-pinWidth 0.038 引脚宽度"
"-edge 3 摆放位置（0左 1上 2右 3下）"
"-snap TRACK 对齐track"
"-spreadDirection counterclockwise 排布方向逆时针（clockwise 顺时针）"
"-offsetStart 609 从起点开始偏移多少个track"
"-unit TRACK -spacing 1 间隔2个track"
"-pattern fill_checkerboard 交错排布"
"man 命令"
"命令 -help  查看命令详细使用方法"
"port 面宽计算："
"（port数量-1）* track间距/摆port层数"
"例：（51-1）*（0.2*2）/3     单位都是um"
"多层摆port 上下必须同一层（5 7 9）"
" 左右必须同一层（6 8 10）"
"port的约束  pinBlkage"
:::

:::fig innovus-doc-20.png | 原文图 20 · 摆放端口与引脚约束
:::

:::note 这张图该看什么
引脚附近的保护区域。两块红色斜纹矩形上沿标 50%，这是**部分阻挡**——限制该区域密度到 50%，不是完全禁止（完全禁止通常标 100%）。

50% 的用途：既保证有走线空间，又不浪费面积。标 100% 会让那块地方完全空着，变成「有空间但放不了东西」的浪费。

下方可见 proc0/cmem0/dddata0/u0/fd0 和 proc0/cmem0/tags0/u0/fd0 两个实例名，中间黄色虚线是引脚连接。
:::

**选择依据**：引脚少、一层放得下用单层；引脚多（尤其总线）必须多层。

原文还给了一个**面宽计算公式**：

```
port 面宽 = (port数量 - 1) × track间距 / 摆port层数
例：(51 - 1) × (0.2 × 2) / 3 = 33.3 µm
```

这个数用来确认 die 那条边够不够长。算出来要 33.3 µm 而那边只有 30 µm，就必须加层数或改分配。

### 多层摆的两条硬规则

原文两条都是踩坑总结：

```
多层摆port  上下必须同一层（5 7 9）
            左右必须同一层（6 8 10）
```

原因在金属层的 Preferred Direction：M5/M7/M9 通常垂直（上下走），M6/M8/M10 通常水平（左右走）。引脚所在层方向不对，引线就出不来。填错不会立刻报错，布线时才发现「这根线怎么都接不出来」。

### editPin 参数逐个说清

| 参数 | 本例值 | 含义 | 填错的后果 |
|---|---|---|---|
| `-fixOverlap` | 1 | 自动修复引脚重叠 | 0 时引脚可能叠在一起短路 |
| `-fixedPin` | 1 | 锁定位置 | 不加则后续优化会移动引脚，顶层对接错位 |
| `-layer` | {M6 M8 M10} | 可用金属层，按序分配 | 层方向不对，引线出不来 |
| `-pin` | "$exif $sif" | 操作对象（变量） | 变量未定义则空操作 |
| `-pinDepth` | 0.6 | 向内深度（µm） | 太浅接不上，太深占内部空间 |
| `-pinWidth` | 0.038 | 宽度（µm） | 太窄电阻大、EM 风险 |
| `-edge` | 3 | 摆哪条边：**0左 1上 2右 3下** | 数字含义与直觉不同，最易错 |
| `-snap` | TRACK | 对齐轨道 | 不对齐则布线器接不上，报开路 |
| `-spreadDirection` | counterclockwise | 沿边展开方向 | 与相邻模块相反则对接错位 |
| `-offsetStart` | 609 | 起点偏移（track 数） | 与相邻模块不对齐 |
| `-unit` | TRACK | 数值单位 | 填 µm 却给 track 数，位置差几十倍 |
| `-spacing` | 1 | 引脚间隔（track） | 太小串扰，太大放不下 |
| `-pattern` | fill_checkerboard | 交错排布 | 直排占轨道多 |

:::pitfall 引脚摆放最常见的四个坑
1. **漏 `-snap TRACK`**：引脚落在两条 track 之间，布线器接不上，报开路但图上看着连着；
2. **`-edge` 数字搞错**：3 是下边不是右边，放错边等于整个模块接口方向错了；
3. **`-unit` 与数值不匹配**：单位写 TRACK 却按 µm 算，位置差几十倍；
4. **忘了 `-fixedPin`**：摆好的引脚在后续优化中被移动。

这四个在版图上都不明显，只有跑连通性检查才暴露。摆完必须立刻验证：总数、每条边数量、坐标是否在轨道上。
:::

原文最后一句提到 `port的约束 pinBlkage`——引脚附近要留空间，因为引脚本身占金属、引线需要缓冲带、宏的引脚尤其拥挤。

## 摆放 Memory / SRAM / 宏 {#source-04}

宏的摆放是 Floorplan 里最花时间、最影响结果的部分。宏一旦放定，标准单元只能在剩下的空间里挤。

### 四条摆放规则

每条都有明确的工程理由。

:::source
"3、摆放mem/sram/macro"
"摆放mem的规则"
"1）所有的mem需要根据模块进行划分、标记, 同模块的要尽量摆在一块"
:::

:::fig innovus-doc-21.png | 原文图 21 · 摆放 Memory、SRAM 与宏单元
:::

:::note 这张图该看什么
一个典型布局：左侧一块大紫色宏、中间大片灰色标准单元行、下方三块较小深色模块。红箭头指向 Design Browser 打开入口。

这个布局符合四条规则：大宏贴边、标准单元区保持完整、小宏填在底部、黄色引脚朝内。
:::

**规则一：按模块分组摆放**——同一模块内部连线最密集，聚在一起线短、省资源、时序好。分散在两端的话模块内线要横穿整个芯片。

**规则二：贴边放、先大后小**——宏占的地方不能放标准单元，放中间会把核心区打碎成放不下一行单元的碎片。先定对位置敏感的大宏，再用灵活的小宏填空。

:::source
"2）所有的mem尽量贴边摆放，先摆较大的，再摆较小的"
"3）mem和mem之间一定留有channel（沟道）"
"1.如果mem很多，可以用marchlearning跑一版，建议每个阶段都用它跑一版"
"marchlearning可以通过配置文件约束边界要求，间距要求，自动摆一版floorplan"
"2.先摆一版导出，基于这一版做调整"
"4）mem摆放尽量避开io的port位置，mem出pin尽量朝里面"
"摆放fp的工具栏"
:::

:::fig innovus-doc-22.png | 原文图 22 · 摆放 Memory、SRAM 与宏单元
:::

:::note 这张图该看什么
Floorplan Toolbox 的入口（Floorplan 菜单 → Floorplan Toolbox…）。这是摆宏的主力工具窗口。
:::

:::fig innovus-doc-23.png | 原文图 23 · 摆放 Memory、SRAM 与宏单元
:::

:::note 这张图该看什么
Floorplan Toolbox 面板的三组功能（红字已标注）：

**① Shift（贴边）**：To Core Box / To Die Box / 1 by 1，把宏精确推到边界。手工拖很难精确贴边。

**② Space（间距）**：批量设置宏间距。多个宏并排时间距必须一致，否则通道宽度不均匀、布线资源分配失衡。**Honor Halo** 勾选后会考虑 halo 存在，避免算出的间距被 halo 吃掉。

**③ Align（对齐）**：多宏边对齐。不对齐会留锯齿状空隙——放不下单元，布线还要绕，双重浪费。

右侧版图中宏标注的 14.715 是尺寸数字。
:::

**规则三：宏之间一定留 channel**。原文还给了两个实用做法：

```
1. mem 很多时用 marchlearning 跑一版，建议每个阶段都跑一版
2. 先摆一版导出，基于这一版做调整
```

marchlearning 是自动摆宏工具，可配边界和间距要求。**关键在「先摆一版导出，再基于这版调整」**——把它当起步方案生成器，不要指望一次给最优解。

**规则四：避开 IO port，出 pin 朝里**。IO 附近走线需求最大，宏摆那里会抢资源；引脚朝外等于对着墙，线只能绕一大圈回来。

### 通道到底留多宽：原文给了算法

这是原文最有价值的干货之一：

```
根据 mem 出 pin 情况、pin 数量、要走 metal 层的 pitch，算出总线宽
例：出 30 个 pin，走 M6、M8，pitch 0.1 µm
30 × 0.1 / 2 = 1.5 µm
```

推导：30 根线各占 1 个 pitch 需 3 µm 单层宽；分两层每层 15 根，得到 1.5 µm。

**但 1.5 µm 只是理论下限**，工程上要加余量：

| 因素 | 加多少 |
|---|---|
| 线间需要间距（不只占 track） | ×1.5–2 |
| 过孔和绕行空间 | ×1.2 |
| 电源线穿过通道 | 加固定值 2–5 µm |

所以 1.5 µm 的理论值，实际通常留 **4–6 µm**。

:::pitfall 通道留窄了不会立刻报错
后果不是「布线失败」，而是**大量绕远路**：线绕到别处走，那片区域时序变差、拥塞上升。要到 route 阶段才暴露，那时改通道意味着重跑 place、CTS、route 全部流程。

所以 floorplan 阶段要按**上限**估，不要按下限。
:::

### 背靠背摆法

原文提到的进阶技巧：两个宏引脚都朝同侧时，背对背放置（引脚都朝外）中间只需很小通道甚至不需要，相比面对面省下整整一条通道。

**代价**：引脚朝外意味着线要绕过宏才能到内部区域。适合引脚少、连线不密集的宏，或配合顶层走线使用。原文提醒「需要特定的角度」——不是简单贴一起，要考虑出线方向。

:::tip 宏摆放检查清单
1. 每个宏都贴边或有记录的理由
2. 同类宏引脚朝向一致
3. 相邻宏间距相等（用 Space 批量设）
4. 宏与 core 边界之间没有小于 3 µm 的窄缝
5. halo 之间没有互相重叠
6. 宏没有压住电源网格（PowerPlan 后必须复查）

第 6 条最容易漏：宏在 PowerPlan **之前**摆，摆时看不到电源网格。
:::

## 添加物理单元（physical only cell） {#source-05}

概念先行：**physical only cell 是只有物理信息、没有时序信息的单元**。它们不参与逻辑功能、不参与时序分析，但**必须存在**，否则芯片造不出来或有可靠性问题。

:::source
"4、添加physicalcell"
"概念：什么是physical only cell？  只有物理信息，没有时序信息的单元"
"1）endcap cell（boundary cell）"
"目的： 防止边缘效应，防止过刻蚀的情况出现，打在core四周以及mem的四周"
"需要检查：打完之后有没有缺失的情况"
"2）tap cell"
"目的： 为了防止闩锁效应（Latch-up）,（闩锁效应： VDD和VSS形成一个低阻通路，容易造成短路、烧毁）"
"3）tiecell"
"目的：为了防止一些pin出现floating悬空的情况，需要插入tiecell"
"tiecell种类分为两种"
"TieHigh   始终为1"
"TieLow   始终为0"
"4）Decap   cell   "
"目的：为了防止IRDROP的问题，相当于一个小电容，需要额外的电荷时提供电荷，不需要额外电荷时，进行充电到最大"
"IRDROP:电压降，电压经过导线的传输，随着距离的加大，会出现电压降低的现象"
"5）Filler Cell "
"目的： 用于填充空白区域，方便进行生产，形成完整的井连接"
"6）ESD cell"
"目的：防止静电的影响，通过esd释放静电电流"
"特别的单元"
"spare cell    inv最多，buf次之， flop较少  预备单元，在eco阶段使用"
"延伸："
"抓取所有的endcap"
"selectInst [dbGet top.insts.name ENDCAP_*]"
"抓取所有的tapcell"
"selectInst [dbGet top.insts.name WELLTAP_*]"
:::

原文列了六类加一个特殊类别，逐类说清「为什么需要」。

### ① Endcap cell（boundary cell）

防边缘效应和过刻蚀，打在 core 四周以及 mem 四周。

**为什么**：制造时刻蚀速率在图形边缘和中间不同（负载效应）。行两端的单元没有保护会被过刻蚀，导致尺寸偏差、漏电增加。Endcap 是「牺牲边」。

**检查项**：打完查有没有**缺失**。缺失位置往往是宏拐角、异形切口边缘——这些地方工具容易算错。

### ② Tap cell

防闩锁效应（Latch-up）。原文的定义很准确：**VDD 和 VSS 形成一条低阻通路，容易造成短路、烧毁**。

**机理**：CMOS 天然存在寄生的 NPN 和 PNP 三极管，交叉耦合形成可控硅结构。正常时关断，但电流注入（ESD、电源浪涌）会触发导通，形成 VDD→VSS 低阻通路。导通后即使触发条件消失也**自己维持**（这就是「闩锁」），电流持续增大直到烧毁。

Tap cell 给阱和衬底提供密集偏置接触，把寄生三极管的基极电位钉住，让它不容易被触发。

### ③ Tie cell

防 pin 悬空。网表里的 `1'b0`/`1'b1` 常量，综合工具不会真的接电源地，而是留一个待接常量的端口。直接接 VDD/VSS 金属有 ESD 和可靠性风险，所以要插 tie cell：**TieHigh 恒为 1，TieLow 恒为 0**。

### ④ Decap cell

防 IR drop。原文的比喻很到位：**相当于一个小电容，需要电荷时提供，不需要时充电到最大**。

数字电路翻转时瞬间拉大电流，电源网格来不及供就会局部掉压（动态 IR drop）。Decap 就近储能、瞬间放电补上。原文对 IR drop 的定义：**电压经导线传输，随着距离加大出现电压降低**。

### ⑤ Filler cell

填充空白区域，方便生产，**形成完整的阱连接**。单元之间空隙里没有阱接触结构，会导致阱不连续（闩锁风险）和制造图形不连续（DRC 违例）。Filler 让整行阱连成一片。

:::pitfall Filler 的插入时机
**必须在时序优化之后、布线之前。**

- 太早：优化要插 buffer，行里已填满 Filler，插不进去 → 优化失败；
- 太晚：布线已完成，Filler 塞进去和走线冲突 → 大量 DRC。

正确位置：Place → 时序优化 → Filler/Tap → Route。
:::

### ⑥ ESD cell

防静电，通过 ESD 单元释放静电电流。主要用在 IO 附近——生产、封装、测试、使用中都可能遭遇静电放电，瞬时电压可达数千伏，ESD 单元提供安全泄放路径。

### 特别单元：spare cell

原文给了实用经验值：**inv 最多，buf 次之，flop 较少**。

**为什么预留**：流片后的 ECO 不能新增单元（掩模已做好，只能改连线），版图里没有空闲单元就改不了。spare cell 就是留后路。**为什么 inv 最多**：反相器最简单、面积最小、最容易改造成想要的功能（两个串起来就是 buffer）。

### 抓取命令与数量核对

```tcl
selectInst [dbGet top.insts.name ENDCAP_*]   ;# 抓所有 endcap
selectInst [dbGet top.insts.name WELLTAP_*]  ;# 抓所有 tap cell
```

`top.insts` 是顶层所有实例，`.name` 取名字，`ENDCAP_*` 是通配符。dbGet 用法见 [dbGet 专题](/lesson/03-01j-dbget/)。

:::tip 数量核对法
不要只看「抓到几个」，要算**应该有几个**：

```
endcap 数量 ≈ (core 周长 / endcap 宽度) × 2 + 宏周长相关
 tap cell 数量 ≈ core 面积 / tap 间距规则
```

实际与估算差太多就说明有区域漏打。这比肉眼看图可靠。
:::

## 布局与布线约束 {#source-06}

约束区域是「人工干预工具决策」的手段。用得好解决局部问题，用滥了让全局变差。

### 5.1 三种分组约束：guide / region / fence

这三个词的区别是面试常考，也是操作最容易混的。原文定义非常精准，值得逐字读。

:::source
"5、添加布局约束布线约束"
"5.1摆放stdcell的约束"
"guide   可进可出：属于该模块的可以放在guide里面，也可以不放在guide里面，其他模块也可以放guide里面"
"region  可进不可出：属于该模块的stdcell只能放在region里面，不属于的可以放也可以不放  bound"
"fence   不可进不可出：属于该模块的stdcell只能放在fence里面，不属于的不可以放在fence区域"
"创建的命令"
"setup.tcl "
"post init {}"
"prefloorplan {}"
"postfloorplan {    }"
"preplace {  }"
"postplace {}"
"prects {}"
"postcts {}"
"setPlaceMode -place_hard_fence true 强制布局阶段，将region视为强约束"
"setOptMode -opt_honor_fence true  强制优化阶段，遵循region/fence 约束"
"根据group创建约束"
"createInstGroup group1 -fence {58 343 180 388}"
"addInstToInstGroup group1 {proc0/iu0/FE_OCP_DRV_C1140_n_1 proc0/iu0/FE_OFC1055_n_1376}"
"例子"
"createInstGroup group1 -fence {58 343 180 388}"
"createInstGroup group2 -guide  {221 343 347 388}"
"createInstGroup group3 -region   {385 343 520 388}"
"删除fence"
"deleteInstGroup group1"
"5.2阻止工具在区域内摆放单元 placement blockage"
"soft   place阶段不能摆放cell,但是optcts、route等阶段可以"
"hard  任何阶段都不能摆放stdcell"
"partial 需要设置百分比，控制区域内的cell的密度"
"Macro_only  不允许摆放macro，stdcell可以摆放"
"使用命令："
"createPlaceBlockage -box {37 149 156 218} -type hard  -name hard_blk01"
"createPlaceBlockage -box {238 153 390 218} -type soft -density 50 -name soft_blk01"
"createPlaceBlockage -box {478 167 674 228} -type partial   -density 50  -name part_blk01"
"页面"
:::

:::fig innovus-doc-24.png | 原文图 24 · 布局与布线约束练习
:::

:::note 这张图该看什么
工具栏 Create Placement Blockage 按钮（提示文字标注快捷键 Shift+Y，F3 用于切换类型）。版图中中间一块深红色矩形被两侧灰色标准单元行包围，区域内标了引脚位置——这块区域被禁止摆放标准单元。
:::

用一个停车场的比喻理解三者：

- **guide 像「推荐停车区」**：你的车可以停这儿也可以停别处，别人的车也能停这儿；
- **region 像「专属车位」**：你的车必须停这儿，别人的车可以停（但不保证）；
- **fence 像「私家车库」**：你的车只能停这儿，别人的车绝对不能进。

| 类型 | 原文定义 | 通俗解释 |
|---|---|---|
| **guide** | 可进可出 | 建议区，不强制 |
| **region** | 可进不可出 | 软边界 |
| **fence** | 不可进不可出 | 硬边界 |

**选择依据**：想引导聚集但不限制死 → guide；想保证不散开但容忍混入 → region；想彻底隔离（如模拟电路远离数字噪声）→ fence。

创建与删除：

```tcl
createInstGroup group1 -fence  {58 343 180 388}
createInstGroup group2 -guide  {221 343 347 388}
createInstGroup group3 -region {385 343 520 388}
addInstToInstGroup group1 {proc0/iu0/FE_OCP_DRV_C1140_n_1 ...}
deleteInstGroup group1
```

坐标 `{x1 y1 x2 y2}` 是矩形左下角和右上角。

### 两个强制遵循的开关

不加这两行，工具可能「不完全遵守」约束：

```tcl
setPlaceMode -place_hard_fence true   ;# 布局阶段把 region 当强约束
setOptMode -opt_honor_fence true      ;# 优化阶段也遵循 region/fence
```

:::pitfall 加了 fence 但结果没生效
最常见原因是漏了上面两个开关。

判断方法：跑完 place 后用 `dbGet` 查 fence 区域内的实例列表，看有没有不属于该组的实例混进来。有就是没生效。
:::

### setup.tcl 的流程钩子

原文列了一串空函数（`post init {}`、`prefloorplan {}`、`postfloorplan {}`、`preplace {}`、`postplace {}`、`prects {}`、`postcts {}`），这是**流程脚本的钩子机制**：把各阶段前后要执行的操作挂在这些函数里，流程跑到对应阶段自动调用。

实际用途：`postfloorplan` 加约束区并检查宏摆放；`preplace` 设 place 模式参数；`postplace` 跑检查导报告。这样整个流程一条命令跑完，不需要人工中途敲命令——**这也是可复现的关键**。

### 5.2 四种 placement blockage

区别在于「什么时候生效」：

| 类型 | 什么时候挡 | 用途 |
|---|---|---|
| **soft** | place 阶段不能摆，optcts、route 阶段可以 | 给布线留临时通道 |
| **hard** | 任何阶段都不能摆 stdcell | 永久禁放区 |
| **partial** | 按百分比控制密度 | 降低局部密度 |
| **Macro_only** | 不允许摆 macro，stdcell 可摆 | 防宏挤进某区域 |

**soft 与 hard 的核心区别**：soft 只在 place 阶段生效，后续优化和布线阶段单元可以进去。适合「我预留空间给布线，布线完空间可以还回去」的场景。**partial 最实用**：不禁止只限密度，如设 50% 则最多填一半，剩下一半留给布线。

```tcl
createPlaceBlockage -box {37 149 156 218} -type hard -name hard_blk01
createPlaceBlockage -box {238 153 390 218} -type soft -density 50 -name soft_blk01
createPlaceBlockage -box {478 167 674 228} -type partial -density 50 -name part_blk01
```

快捷键 `Shift+Y` 创建，`F3` 切换类型。删除：

```tcl
deletePlaceBlockage -all          ;# 删全部
deletePlaceBlockage <name>        ;# 按名字
deletePlaceBlockage -type soft    ;# 按类型
```

:::pitfall 按类型删很危险
`-type soft` 会删掉**所有** soft blockage，包括精心设置的那些。

调试时想删一个测试用的 blockage，用 `-all` 或 `-type` 都是灾难。正确做法是**给每个 blockage 起有意义的名字**，按名字删。
:::

### 5.3 halo：宏的保护圈

在 mem 四周打一圈 halo，不允许在范围内摆 cell。三个理由：宏引脚要从边上出来需要走线空间、电源环通常布在周围、边界有制造规则要求。

原文提到**「一般 flow 自带会打 halo」**——标准流程脚本通常已设默认 halo。但如果手工挪了宏，要检查 halo 有没有跟着移动。

:::source
"快捷键： shift+y    "
"切换placementblkage 类型:  F3"
"删除palcementblkage"
"deletePlaceBlockage -all"
"deletePlaceBlockage name"
"deletePlaceBlockage  -type  soft"
"5.3 halo  一般flow自带会打halo"
"在mem四周打一圈halo，不允许在mem的halo范围内摆cell"
:::

:::fig innovus-doc-25.png | 原文图 25 · 布局与布线约束练习
:::

:::note 这张图该看什么
Edit Floorplan 子菜单的完整清单，这是约束区域的「总目录」：

| 菜单项 | 阻挡什么 | 用途 |
|---|---|---|
| Cut Rectilinear | —— | 切异形边界 |
| Create Size Blockage | 尺寸调整 | 保护区域不被 resize |
| Create Placement Blockage | 标准单元摆放 | 留通道、避障碍 |
| Create Routing Blockage | 布线 | 保护敏感区域 |
| Create Pin Blockage | 引脚区域 | 引脚附近留缓冲 |
| Edit Halo | 宏保护圈 | 调整禁放范围 |
| Color Module | —— | 视觉区分（不影响物理） |
| Legalize Floorplan | —— | 检查宏重叠、越界 |
:::

### 5.4 布线约束 routing blockage

不允许工具在指定范围内走线。**注意可只挡指定层**，其他层照常走——这是 routing blockage 比 placement blockage 更精细的地方。

:::source
"5.4布线的约束"
"概念：routing blockage 不允许工具在指定的范围内走线"
"命令："
"createRouteBlk  -box {743 173 876 228} -layer {M3 M5} -name route_blk01"
"页面"
:::

:::fig innovus-doc-26.png | 原文图 26 · 布局与布线约束练习
:::

:::note 这张图该看什么
含多种约束区域的实际版图。深红色实心块是 Routing Blockage（线不能过）；棕色 group1(TU=0.1%) 是几乎空的区域；黄色/粉色/白色网格块是不同密度的约束区，粉色标 100% 表示允许填满。

读这张图的方法**不看颜色，看标注的百分比**：0% 完全禁止，100% 允许放满，中间值是密度上限。
:::

```tcl
createRouteBlk -box {743 173 876 228} -layer {M3 M5} -name route_blk01

deleteRouteBlk -all              ;# 删全部
deleteRouteBlk -name <name>      ;# 按名字
deleteRouteBlk -layer {M1 M3}    ;# 按层
deleteRouteBlk -box {}           ;# 按区域
```

快捷键 `Shift+B`。

:::note 四种 Blockage 的关键区别
| | 挡什么 | 挡不挡布线 |
|---|---|---|
| Placement Blockage | 标准单元**摆放** | **不挡**，线可过 |
| Routing Blockage | **布线** | 挡 |
| Pin Blockage | **引脚区域** | 部分挡 |
| Size Blockage | **尺寸调整** | 不挡 |

最容易混的是第一个：**Placement Blockage 不挡布线**。所以「给布线留通道」用它是对的——你只是不让单元占地方，线还是要从这里过。
:::

:::pitfall 约束区域设太多
新手遇到问题就加 blockage，越加越多，最后设计被切得七零八落。

**判断标准**：约束区域总面积超过 core 的 **20%**，就该怀疑 floorplan 本身有问题。正确做法是回去调宏位置或通道宽度，而不是用 blockage 打补丁。

blockage 的正确用途是**局部微调**，不是**全局重排**。
:::

### 原文的 9 步练习

:::source
"快捷键： shift+b"
"删除routeblkage"
"deleteRouteBlk -all   删除所有"
"deleteRouteBlk -name   blk的name"
"deleteRouteBlk -layer  {M1 M3}  "
"deleteRouteBlk -box  {}   删除指定区域的blkage"
"练习："
"1、创建一个fence    "
"2、创建一个hard  placeblkage（用命令）"
"3、创建partial placeblkage（用命令）"
"4、创建soft  blkage （用界面）"
"5、创建routing blkage  (用命令)"
"6、删除hardblkage"
"7、写一个tcl实现上面的操作， 加上注释"
"8、删除之前的所有约束"
"9、执行自己的脚本"
:::

这套练习很完整，**第 7 步是关键**：把界面操作翻译成 tcl。做完这一步才算真的理解每个参数。

## 导入导出与质量评估 {#source-07}

### 吐出与吃进：四种交接方式

:::source
"6、吐出flooplan的tcl文件/产生一个fp.tcl文件"
"产生fp的tcl"
"writeFPlanScript  -selected    -fileName ../scripts/stu_0131_placemem.tcl"
"吃fp的tcl"
"source  ../scripts/stu_0131_placemem.tcl"
"吐出def文件(innovus)        注：01版本只动了mem"
"defOut -floorplan  data/floorplan_01.def "
"读入def文件"
"defIn data/floorplan_01.def"
"7 如何评估floorplan的好坏"
"7.1 整体看上去整齐，美观"
"7.2 要根据place的结果来评判，place的setup时序是否有违例， congestion map是否有大量红色， cell density是否有较高的地方"
"congestion map:  会有个图层可以查看congestion分布，颜色深度就是严重程度，颜色越深，越严重"
"congestion：绕线资源的拥塞程度，congestion越严重，线就越绕不通"
"congestion可以通过命令查看overflow的值  H(横向)和V(纵向)"
"overflow的值不要超过1%    0.1%-0.2%(3nm)"
"reportCongestion -hotSpot -overflow  "
:::

:::fig innovus-doc-27.png | 原文图 27 · 导入导出与质量评估
:::

:::note 这张图该看什么
reportCongestion -overflow 的输出。逐项读：

`Usage: (4.0%H 5.1%V)` 是横向/纵向**轨道使用率**（floorplan 阶段几乎没走线，很低正常）；`(1.521e+05um 2.175e+05um)` 是总轨道长度；`(30183 43159)` 是轨道数量。

`Overflow: 214 = 214 (0.42% H) + 0 (0.00% V)` 是关键：214 个轨道需求超容量，**全部来自横向**（占横向容量 0.42%），纵向为 0。

**判读**：横向轻微溢出，远低于 1% 阈值，横向资源略紧但可接受。横向纵向分开看的意义在于——若横向严重而纵向为 0，说明该增加横向布线层或调整单元朝向。
:::

四组命令对应四种交接方式，区别在于 tcl 与 def：

| | tcl 脚本 | def 文件 |
|---|---|---|
| 内容 | 命令序列（做了什么） | 数据（结果是什么） |
| 可读性 | 人可读，能看懂意图 | 机器可读，格式固定 |
| 可修改 | 能改参数重跑 | 改起来麻烦 |
| 用途 | 交接、复现 | 跨工具交换 |

实践建议：自己用 tcl（能改能读），跨工具/跨团队用 def（标准格式）。

原文有个注记很实用：**「01 版本只动了 mem」**。这是版本命名习惯——每次改动给编号并说明改了什么，出问题能快速回退。

### 怎么评估 floorplan 好不好

原文给两条：

**7.1 整体看上去整齐、美观** —— 听起来主观，但有道理：**整齐意味着资源分配均匀**。宏对齐、间距一致、没有奇形怪状的空隙，通常说明空间利用合理。歪歪扭扭的布局几乎一定有资源分配问题。

**7.2 根据 place 的结果来评判** —— 这才是硬指标，三个检查点：place 的 setup 时序是否违例、congestion map 是否大量红色、cell density 是否有较高处。

**为什么用 place 结果反评 floorplan**？因为 floorplan 阶段还看不出来，只有真正摆了单元、做了全局布线，才知道空间够不够。

### congestion 与 overflow：最硬的判据

原文给了很具体的阈值，这是全书最有价值的数据之一：

```
overflow 的值不要超过 1%    0.1%-0.2%(3nm)
reportCongestion -hotSpot -overflow
```

| 工艺 | 可接受 overflow |
|---|---|
| 一般工艺 | < 1% |
| 3nm 等先进工艺 | 0.1% – 0.2% |

**为什么先进工艺要求更严**：先进工艺 pitch 更小、双重图形等规则更复杂，布线资源更紧张，一点溢出就造成大面积绕不通。

:::tip 用 overflow 做 A/B 对照
调整 floorplan 后用**同样命令参数**再跑一次，对比溢出总量和横纵比例。

这比看拥塞图颜色可靠——颜色受图例阈值影响，数字不会。
:::

## 常见问题与进阶技巧 {#source-08}

原文这节是问答形式，每个问题都是真实遇到的。

:::source
"8 floorplan的一些问题"
"8.1 init design之后有很多mem/分给自己的模块有很多mem/mcaro，怎么更快的进行fp"
"1）使用工具自动摆放macro的界面，但是这种方法较为粗糙"
"或者使用命令   "
"Set_fp_stragety  -macros_on_edge  on  "
:::

:::fig innovus-doc-28.png | 原文图 28 · 常见问题
:::

:::note 这张图该看什么
Generate Floorplan 子菜单，红箭头指向 Place Macros…——自动摆宏的入口。子菜单还有 Prototype Design（原型设计）、Initialize Fast Timing Analysis（快速时序）、Fast Slack Analysis/Display（快速裕量分析）、Analyze Floorplan（分析布局）、Generate Fence（生成围栏）。

**自动摆宏的结果绝不能直接交付**：它的目标函数（通常总线长最短）不等于项目目标，可能把该相邻的宏分开，或把宏放在挡住电源网格的位置。正确用法是「自动摆 → 人工逐个检查调整 → 定稿」。
:::

### 问题一：宏很多，怎么更快做 floorplan

**方案 A 自动摆放**：`Generate Floorplan → Place Macros…`，或命令 `set_fp_strategy -macros_on_edge on`（把宏往边上推）。**原文评价「较为粗糙」**，只能给初始方案。

**方案 B marchlearning**：设置 fp 约束规则，让工具自动摆放 mem。比方案 A 可控，因为能配边界、间距等约束。

两个方案的共同点：生成**初始版本**，然后人工调整。

### 问题二：通道宽度怎么算

原文答得最详细，也是面试高频题：

```
根据 mem 出 pin 情况、pin 数量、metal 层 pitch，算出总线宽
例：30 个 pin，走 M6、M8，pitch 0.1 µm → 30 × 0.1 / 2 = 1.5 µm
```

原文还问了三个反问——这是真正的工作经验：

```
如何确定 mem 之间的 channel 是足够的？依据是什么？
通常你们工作中 mem 之间 channel 留多大？为什么？
```

这三问没有标准答案，取决于项目。但思考框架固定：**按最坏情况估 + 留余量**。

### 问题三：还有别的摆法吗

**背靠背摆法**：channel 可减到最小，节省大量面积。分上下结构（长边相邻）和左右结构（短边相邻）——前者通道更长更窄，后者相反，选哪个看引脚分布。

原文提醒「需要特定的角度」：背靠背不是简单贴一起，要考虑出线方向。两个宏引脚都朝内时背靠背会让引脚面对面，反而更糟。

### 问题四：dontuse cell list

原文这段讲**流程管控**：PR 每个阶段 flow 会设 dontuse cell 禁止使用某些单元；ECO 阶段要检查设计里有没有 dontuse 的单元，需要替换。

**为什么有 dontuse list**：某些单元有已知硅后问题、某些在特定工艺角下时序不收敛、某些功耗或面积过大。

**为什么必须检查**：flow 可能在早期用了某单元，后来该单元被加入禁list。设计里已有它，签核时不替换会被判不合格。这是**签核固定项**，漏了会导致流片后才发现问题。

:::source
"2）使用marchlearning"
"设置fp的一些约束规则，让工具ai自动摆放mem"
"2、macro之间Chanel的计算方法？ "
"如何确定mem之间的chanel是足够的？依据是什么？"
"通常你们工作中mem之间chanel留多大？为什么？"
"根据mem的摆放出pin情况，以及pin的数量，以及要走的metal层的pitch，计算得出总线宽"
"例如：有一个mem，出pin为30个，走M6，M8，假设pitch是0.1um"
"30*0.1/2= 1.5um"
"3、除了通常的摆放mem方法还有什么方法可以摆放"
"背靠背摆法，chanel可以减小到最低，节省大量面积"
"上下结构，左右结构"
"注意：背靠背，中间也会有chanel，只是很小，需要特定的角度"
"4、关于dontuse cell 的list"
"在PR每个阶段，flow会设置dontusecell,禁止工具使用一些指定的cell"
"在eco阶段，会有一个检查，是否有dontuse的cell在design中，需要进行替换"
:::

## 实操：完整的 floorplan 脚本 {#source-09}

原文最后给了一个真实项目的完整操作，值得逐行读。

:::source
"5）实操"
"1.定义形状"
"floorplan -noSnapToGrid -b 0 0 935.712 456.456  0 0 935.712 456.456"
"1.2 1.2285 934.512 455.2275 #die 坐标 IO 坐标 core 坐标"
"addObjFPlanCutBox cell bpu40_vae_top_wrapper  0 0 566.352 228.228"
"#切角坐标。"
:::

:::fig innovus-doc-29.png | 原文图 29 · 实操：定义形状与抓取、摆放端口
:::

:::note 这张图该看什么
完成切角后的版图轮廓，灰色区域呈 L 形：左上角被切掉一块矩形，形成直角台阶。区域内密排横线是标准单元摆放行，左下角黄色小标记是引脚。**这个形状就是脚本里 addObjFPlanCutBox 命令的结果。**
:::

### 第一步：定义形状

:::source
"2.抓取port"
"--抓取所有 port"
"set all_ports [dbget top.terms.name]"
"set fh [open \"ports_from_db.txt\" w]"
"puts $fh [join $all_ports \"\\n\"]"
"close $fh"
"--抓取 unplace 的 port"
"set unplaced [dbget [dbget -p top.terms.pStatus unplaced].name]"
"set f [open \"unplaced_terms.txt\" w]"
"foreach t $unplaced { puts $f $t }"
"close $f"
"1"
"redirect -file physicalcell_name.txt {puts [dbget top.physInsts.name ]}"
"--抓取 input/output port"
"get_ports -filter \"direction == in/out\""
"--取消摆放"
"dbset top.terms.pStatus unplaced"
"dbset selected.pStatus unplaced"
"3.摆放port"
"设置变量"
"set A  [get_object_name [get_ports A*]]"
"命令"
"editPin -fixOverlap 1  -fixedPin 1    -layer {M6 M8 M10}    -pin \"$exif $sif\"    -pinDepth 0.6   -pinWidth 0.038 -edge 3   -snap TRACK -spreadDirection counterclockwise  -offsetStart 609    -unit TRACK -spacing 1   -pattern fill_checkerboard"
"解析"
"editPin -fixOverlap 1        自动修复引脚重叠"
"-fixedPin 1                  锁定引脚位置"
"-layer {M6 M8 M10}           摆放金属层配置"
"-pin \"$exif $sif\"            操作对象"
"-pinDepth 0.6                引脚深度"
"-pinWidth 0.038              引脚宽度"
"-edge 3                      摆放位置（0左 1上 2右 3下）"
"-snap TRACK                  对齐track"
"-spreadDirection counterclockwise  排布方向逆时针（clockwise 顺时针）"
"-offsetStart 609             从起点开始偏移多少个track"
"-unit TRACK -spacing 1       间隔2个track"
"-pattern fill_checkerboard   交错排布"
:::

`-b` 后面是三组坐标，原文注释说得很清楚：`die 坐标 / IO 坐标 / core 坐标`。完整形式是：

```tcl
floorplan -b <die_x1 die_y1 die_x2 die_y2> <io...> <core...>
```

本例 die 和 IO 坐标相同（无独立 IO ring），core 那组在注释里给了（`1.2 1.2285 934.512 455.2275`）。

`-noSnapToGrid` 是不对齐网格，用于大尺寸非整数坐标场景。切角坐标 `0 0 566.352 228.228` 从原点切掉 566 × 228 µm——接近一半面积，说明这是 L 形大模块。

### 第二步与第三步：抓取、验证、摆放

脚本后半段的价值在于展示了**完整工作流**，中间有两次验证动作（抓 port 两次）：

```
定义形状 → 抓取检查 → 摆端口 → 再抓取验证
```

**「抓两次对比」是核心工程习惯**：第一次抓所有 port 知道总数，第二次抓 unplaced 知道还剩多少。摆完再抓一次，应该为空；不空就说明漏了。

**`dbset top.terms.pStatus unplaced` 很危险**——如果之前精心摆过，一执行全没了。所以要先把当前状态导出（`writeFPlanScript`）再操作。

**`set A [get_object_name [get_ports A*]]`** 是变量赋值示例。用变量的理由：端口组经常需要重复操作（摆一次、检查一次、改一次），写死端口名的话加一个端口就要改三处。

## 完整检查清单 {#checklist}

Floorplan 做完，逐项过一遍：

:::check
- Die/Core 尺寸与上游清单一致，手工核对「Die 高 = Core 高 + 上下边距」算式
- 原点位置（左下角/中心）与上游约定一致，没有凭习惯选
- 异形切角坐标与要求一致，切掉的区域原本不需要放宏
- 所有 port 已摆放，`unplaced_terms.txt` 为空或有明确解释
- 端口对齐到轨道（`-snap TRACK`），总数与网表一致
- 多层摆 port 的层方向正确：上下用 5/7/9，左右用 6/8/10
- 引脚附近有 pin blockage，密度设置合理
- 每个宏都贴边或有记录的理由，同类宏引脚朝向一致
- 相邻宏间距相等，宏之间没有小于 3 µm 的窄缝
- 所有宏设了 halo，halo 之间没有重叠
- 通道宽度按「引脚数 × pitch ÷ 层数」估算并留了 1.5–2 倍余量
- 六类 physical cell（endcap/tap/tie/decap/filler/ESD）该加的已加，数量核对过
- `reportCongestion -overflow` 已跑，overflow < 1%，横向纵向分别记录
- guide/region/fence 三种分组约束按需设置，`-place_hard_fence` 已开
- 四类 blockage 没有遗留的临时设置，按名字管理而非按类型批量删
- 所有 floorplan 参数已写入 tcl，可从干净数据库重跑
- dontuse cell 检查已做，设计中没有被禁用的单元
:::

## 自测 {#quiz}

:::quiz
site 和 row 分别是什么？为什么标准单元宽度必须是 site 的整数倍？| site 是摆放的最小宽度单位，row 是高度等于标准单元高度、由 site 横向重复组成的条带。宽度为 site 整数倍才能保证相邻单元电源轨对齐连续。
单元不在 row 上会导致什么问题？为什么？| 没有 legalize，底层图形颜色映射错乱，在双重图形工艺下引发 base DRC 违例。修法是手动或自动 legalize。
port、pin、terminal 三者的区别是什么？| port 是模块对外的逻辑接口名；pin 是单元或宏的输入输出脚；terminal 是 port 的物理实现，即边界上的一段金属 shape。
Core Utilization 0.706 和 Cell Utilization 0.513 差 19 个百分点，差在哪？| 差在宏和其他物理单元占的面积。前者算所有占用，后者只算标准单元。
Dimension 高 596.79、Die Size 高 600.21、Core to Top/Bottom 各 1.71，三者什么关系？| Die 高 = Core 高 + 上边距 + 下边距，600.21 = 596.79 + 1.71 + 1.71。手工核对能确认参数生效。
摆放宏的四条规则是什么？各为什么？| ①按模块分组（模块内连线最密）；②贴边放先大后小（贴边保持核心区完整，大宏对位置敏感）；③宏间留 channel（走线需要空间）；④避开 IO、引脚朝里（IO 附近需求大，朝外等于对墙）。
一个 mem 出 30 个 pin 走 M6/M8，pitch 0.1 µm，通道理论宽度多少？实际留多少？| 理论 30×0.1÷2 = 1.5 µm。实际加线间距、过孔绕行、电源线，通常留 4–6 µm。
guide、region、fence 三种约束的区别？| guide 可进可出（建议区）；region 可进不可出（软边界）；fence 不可进不可出（硬边界）。
placement blockage 的 soft、hard、partial、Macro_only 分别什么时候生效？| soft 只在 place 阶段挡；hard 任何阶段都挡 stdcell；partial 按百分比限密度；Macro_only 只挡宏不挡 stdcell。
Placement Blockage 会不会挡住布线？为什么「留布线通道」用它是对的？| 不挡布线，线可穿过。所以用它只是不让单元占地，走线空间仍保留。
endcap、tap、tie、decap、filler、ESD 六类物理单元各解决什么问题？| endcap 防边缘过刻蚀；tap 防闩锁；tie 防 pin 悬空；decap 抑制 IR drop；filler 填缝保持阱连续；ESD 泄放静电。
filler 为什么必须在时序优化之后、布线之前插入？| 太早占满行导致 buffer 插不进去；太晚和已完成布线冲突产生大量 DRC。
reportCongestion 显示 Overflow: 214 = 214 (0.42% H) + 0 (0.00% V) 怎么解读？| 214 个轨道溢出全部来自横向，占横向容量 0.42%（低于 1% 阈值），纵向无溢出，横向资源略紧。
overflow 的通用阈值是多少？先进工艺呢？| 一般工艺 < 1%；3nm 等先进工艺 0.1%–0.2%。
为什么先进工艺对 overflow 要求更严？| pitch 更小、双重图形等规则更复杂，布线资源更紧张，一点溢出就大面积绕不通。
为什么 floorplan 参数必须写进 tcl 而不能只用 GUI 定稿？| GUI 参数只在内存，重跑凭记忆重填会有微小差异，导致所有坐标变化、此前检查报告作废。只有脚本可复现。
dontuse cell list 是什么？为什么 ECO 阶段要专门检查？| 流程禁止使用的单元清单（可靠性、时序、功耗原因）。早期流程可能用过后来被禁的单元，签核时必须替换。
:::

## 下一步与延伸阅读 {#next}

Floorplan 定稿后，下一步是 [PowerPlan：打电源网格](/lesson/03-06-powerplan/)。

| 主题 | 参考 |
|---|---|
| 切角与端口清单实操 | [Floorplan 实操：看懂切角与端口](/lesson/03-01a-flp-lab/) |
| Memory 面积怎么算、利用率分母怎么取 | [算清 Memory 面积，看懂布局报告](/lesson/03-01c-project-details/) |
| 从 Die Size 输入到 Kick-Off Run | [Floorplan 进阶](/lesson/03-01d-floorplan-advanced/) |
| 布局密度与拥塞诊断 | [Place 诊断](/lesson/03-01e-placement-diagnostics/) |
