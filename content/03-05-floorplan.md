---
id: 03-05-floorplan
no: 35
stage: 3
title: Floorplan：芯片尺寸、端口、宏与约束
en: Floorplan
hours: 0
tags: [Innovus, 40nm, 项目实操]
summary: 视图与布局规划基础；定义芯片尺寸与异形 Die；摆放端口与引脚约束；摆放 Memory、SRAM 与宏单元；添加物理单元；布局与布线约束练习；导入导出与质量评估；常见问题；实操：定义形状与抓取、摆放端口。按《04 innovus项目(1).docx》原文顺序整理，保留原图。
---

## 视图与布局规划基础 {#source-01}

:::note 资料来源
以下小节按《04 innovus项目(1).docx》原顺序收录。命令、用语及示例按原文保留；命令适用性以课程使用的工具版本与项目环境为准。
:::

:::source
"三、Floorplan"
"innovus的几种视图"
:::

:::fig innovus-doc-09.png | 原文图 09 · 视图与布局规划基础
:::

:::source
"1）一些floorplan的概念"
"site:  placement的最小单位，任何cell的宽度一定是site的整数倍"
:::

:::fig innovus-doc-10.png | 原文图 10 · 视图与布局规划基础
:::

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

:::source
"port:  是整个模块的端口、信号接口"
:::

:::fig innovus-doc-12.png | 原文图 12 · 视图与布局规划基础
:::

:::source
"pin：标准单元或者mem的输入端口输出端口"
:::

:::fig innovus-doc-13.png | 原文图 13 · 视图与布局规划基础
:::

:::source
"terminal：为了将port的逻辑连接，变成物理连接，需要创建metalshape，也就是一段金属，这就是terminal"
:::

:::fig innovus-doc-14.png | 原文图 14 · 视图与布局规划基础
:::

:::source
"cell density  单元的密度"
"如果density过高，会导致什么问题？会导致routing resource（绕线的资源） 不足"
"出现short"
:::

## 定义芯片尺寸与异形 Die {#source-02}

:::source
"2） floorplan的流程"
"教学版："
"1、定义芯片的大小"
"页面上的操作"
:::

:::fig innovus-doc-15.png | 原文图 15 · 定义芯片尺寸与异形 Die
:::

:::fig innovus-doc-16.png | 原文图 16 · 定义芯片尺寸与异形 Die
:::

:::source
"定义异形die（针对die区域剪切的）"
"界面："
:::

:::fig innovus-doc-17.png | 原文图 17 · 定义芯片尺寸与异形 Die
:::

:::source
"命令："
"设置支持异型剪切：setPreference EnableRectilinearDesign 1"
"剪切命令：addObjFPlanCutBox cell leon 0 0 20 80"
"吐出die的命令：writeFPlanScript -fileName box.tcl -sections {boundary block pins}"
:::

:::fig innovus-doc-18.png | 原文图 18 · 定义芯片尺寸与异形 Die
:::

## 摆放端口与引脚约束 {#source-03}

:::source
"2、摆放port"
:::

:::fig innovus-doc-19.png | 原文图 19 · 摆放端口与引脚约束
:::

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

## 摆放 Memory、SRAM 与宏单元 {#source-04}

:::source
"3、摆放mem/sram/macro"
"摆放mem的规则"
"1）所有的mem需要根据模块进行划分、标记, 同模块的要尽量摆在一块"
:::

:::fig innovus-doc-21.png | 原文图 21 · 摆放 Memory、SRAM 与宏单元
:::

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

:::fig innovus-doc-23.png | 原文图 23 · 摆放 Memory、SRAM 与宏单元
:::

## 添加物理单元 {#source-05}

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

## 布局与布线约束练习 {#source-06}

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

:::source
"5.4布线的约束"
"概念：routing blockage 不允许工具在指定的范围内走线"
"命令："
"createRouteBlk  -box {743 173 876 228} -layer {M3 M5} -name route_blk01"
"页面"
:::

:::fig innovus-doc-26.png | 原文图 26 · 布局与布线约束练习
:::

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

## 导入导出与质量评估 {#source-07}

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

## 常见问题 {#source-08}

:::source
"8 floorplan的一些问题"
"8.1 init design之后有很多mem/分给自己的模块有很多mem/mcaro，怎么更快的进行fp"
"1）使用工具自动摆放macro的界面，但是这种方法较为粗糙"
"或者使用命令   "
"Set_fp_stragety  -macros_on_edge  on  "
:::

:::fig innovus-doc-28.png | 原文图 28 · 常见问题
:::

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

## 实操：定义形状与抓取、摆放端口 {#source-09}

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
