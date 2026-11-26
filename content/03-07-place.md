---
id: 03-07-place
no: 37
stage: 3
title: Place：标准单元布局、时序与利用率
en: Placement
hours: 0
tags: [Innovus, 40nm, 项目实操]
summary: 布局目标与摆放流程；分析模式、OCV 与路径分组；布局命令及静态时序分析；布局摘要与设计规则违例；利用率与面积计算脚本；布局后检查与修复。按《04 innovus项目(1).docx》原文顺序整理，保留原图。
---

## 布局目标与摆放流程 {#source-01}

:::note 资料来源
以下小节按《04 innovus项目(1).docx》原顺序收录。命令、用语及示例按原文保留；命令适用性以课程使用的工具版本与项目环境为准。
:::

:::source
"五、Place"
"1）主要的目标"
"合理规范摆放标准单元："
"stdcell的方向正确"
"stdcell不能出现overlap(单元重叠的情况)"
"stdcell必须在row上，基于site进行摆放"
"没有违反fp的constrain(布局约束 region partial 等)"
"2）place的流程"
"2.1 global place"
"全局性摆放单元，确定大致的位置,比较粗糙的走线，主要目的为了评估congestion是否有问题，以及density是否合理"
"2.2 Scan Reorder 扫描链重组"
"扫描链Scan Chain  DFT(design for test)部门设计专门网表"
"一种测试的手段，验证芯片功能是否满足要求"
"认识cell的常见pin"
"D pin"
"Q pin"
"SI pin  scan input"
"SO pin scan output"
"SE pin scan exable"
"CK pin"
:::

:::fig innovus-doc-31.png | 原文图 31 · 布局目标与摆放流程
:::

:::source
"DFF = D Flip-Flop，D 触发器（后端最核心时序单元，也常叫寄存器 reg）"
"MUX选择器  "
"2.3 detail place"
"globalroute 全局布线  "
"MultuiBit  Banking   "
"将多个完全相同的cell进行合并，"
:::

:::fig innovus-doc-32.png | 原文图 32 · 布局目标与摆放流程
:::

:::source
"inst的数量越多，runtime就越长"
"runtime也看服务器的配置，256G内存，核心16 "
:::

## 分析模式、OCV 与路径分组 {#source-02}

:::source
"关于analysis mode"
"onChipVariation  简称OCV 偏上芯片误差"
"不同区域的单元的PVT环境不一样"
"OCV会引入derate（一个系数）的设置"
"OCV的弊端：设置统一的dreate,会导致，path越长，时序越悲观"
"为了解决OCV，设置CPPR（共同路径悲观去除）"
"AOCV 自动的OCV"
"更加智能，根据cell的级数，电路结构(距离) 设置不同derate"
"和电路级数成反比，级数越多，derate就越小"
"和距离distance 成正比, 距离越远，dreate越大"
"SOCV/POCV   "
"相比较AOCV更乐观"
"引入正态分布的思想，计算不同cell的延迟落在不同区间的概率，设置derate，尽量覆盖大部分场景"
"CPPR： 公共路径悲观去除"
"修复时序方法--设置group组"
"create path groups (reg2reg, in2reg, reg2out, in2out  reg2mem  mem2mem  mem2reg  reg2cg  )"
"group_path -name reg2reg -from [all_registers] -to [all_registers]"
"group_path -name in2reg -from [all_inputs] -to [all_registers]"
"group_path -name reg2out -from [all_registers] -to [all_outputs]"
"group_path -name in2out -from [all_inputs] -to [all_outputs]"
"setPathGroupOptions reg2reg -effortLevel high"
"setPathGroupOptions in2reg -effortLevel low"
"setPathGroupOptions reg2out -effortLevel low"
"setPathGroupOptions in2out -effortLevel low"
"group_path -name CLKM -from   [get_ports UFF0/CK ]  -to  [get_ports UFF1/D]"
"setPathGroupOptions CLKM -effortLevel high"
"set_interactive_constraint_modes [all_constraint_modes -active]    开启约束的修改"
"set_max_transition -clock_path 200 [all_clocks ] -override"
"set_max_transition -data_path 400 [all_clocks ] -override"
"set_interactive_constraint_modes {}   结束约束的修改"
:::

## 布局命令及静态时序分析 {#source-03}

:::source
"跑place的超级指令"
"place_opt_design"
"STA静态时序分析"
:::

:::fig innovus-doc-33.png | 原文图 33 · 布局命令及静态时序分析
:::

:::source
"建立时间检查 setup检查"
"第一次数据到达时间要比第一次检查时间要快"
"Trequire - Tarrive > 0"
"Trequire > Tarrive"
"Tarrive 数据到达时间"
"= Tlunch +Tck2q+Tdatapath "
"Trequire第一次检查时间"
"= Tcapture+Tck时钟周期-Tsetup(uncertainty)"
"保持时间检查 hold检查"
"第二次数据到达时间要比第一次检查时间要慢"
"Tarrive2 - Trequire > 0 "
"Tarrive2 > Trequire"
"第二次数据到达时间应该比第一次到达时间多一个周期"
"Tarrive2 = Tlunch +Tck2q+Tdatapath + Tcycle"
"Trequire = Tcapture+Tcycle +Thold(uncertainty)"
"Tlunch +Tck2q+Tdatapath - (Tcapture+Thold(uncertainty)) > 0"
"Tlunch +Tck2q+Tdatapath > Tcaputure + Tuncertainty"
"注意：place阶段不看hold，因为clock的idea的，此时hld天生就满足"
"延伸："
"addInstancePrefix"
"添加的实例的名字前缀"
"作用： debug一些单元在什么时候插入的"
"为了修复什么问题才添加的这个缓冲器"
"Instance  实例化的对象"
"fanout   扇出"
:::

:::fig innovus-doc-34.png | 原文图 34 · 布局命令及静态时序分析
:::

:::source
"设置grouppath"
"对时序路径进行分组"
"group_path -name in2out -from [all_inputs] -to [all_outputs]"
"setPathGroupOptions in2out -effortLevel low"
:::

## 布局摘要与设计规则违例 {#source-04}

:::source
"placement summary"
:::

:::fig innovus-doc-35.png | 原文图 35 · 布局摘要与设计规则违例
:::

:::source
"DRV  "
"design rule vertation"
"设计规则违反"
"基本四种drv"
"max_transtion   最大转换时间"
"分为data transtion  和clock transtion"
"max_fanout    最大扇出"
"max_length   最大长度"
"max_cap     最大负载电容"
"其他的drv："
"setup、hold、dontuse、clock transtion"
"min_pluse"
"设置约束"
"set_interactive_constraint_modes [all_constraint_modes -active]  开始设置约束"
"set_max_transition -clock_path 200 [all_clocks ] -override"
"set_max_transition -data_path 400 [all_clocks ] -override"
"set_interactive_constraint_modes {}  结束设置约束"
"place的summary"
"WNS 表示最差的结果    一般place阶段不要超过 -100ps  /   -0.1ns"
"TNS  所有违例的总和"
:::

:::fig innovus-doc-36.png | 原文图 36 · 布局摘要与设计规则违例
:::

## 利用率与面积计算脚本 {#source-05}

:::source
"3）利用率"
"一般Place的利用率在45%-50% "
"postroute不超过60%"
:::

:::fig innovus-doc-37.png | 原文图 37 · 利用率与面积计算脚本
:::

:::source
"根据利用率调整die的面积"
"innovus计算面积的脚本"
"计算整个模块中std+mem的总面积"
"set all_cells [dbGet top.insts.name * -p]   #抓到所有的单元，包括mem和stdcell"
"set all_cells_area 0   #定义所有单元面积之和为0"
"foreach cell $all_cells {"
"set cell_area [dbGet ${cell}.area]   #获取单个遍历取到的单元的面积"
"set all_cells_area [expr $all_cells_area+$cell_area]"
"}"
"echo \"The total area of all cells is $all_cells_area um^2.\""
"计算所有的mem的总面积"
"set all_macros [dbGet top.insts.cell.subClass block -p2]"
"set all_macros_area 0"
"foreach macrocell $all_macros {"
"set macro_area [dbGet ${macrocell}.area]"
"set all_macros_area [expr $all_macros_area+$macro_area]"
"}"
"echo \"The total area of all macro cells is $all_macros_area um^2.\""
"计算所有的stdcell的总面积"
"set all_stdcells_area [expr $all_cells_area - $all_macros_area]"
"echo \"The total area of all std cells is $all_stdcells_area um^2.\""
"计算出当前模块应该设置的大小"
"set total_estimate_area [expr $all_stdcells_area / 0.6 + $all_macros_area / 0.7]"
"echo \"The estimated area is $total_estimate_area um^2.\""
"icc版本计算面积的脚本"
"ICC2 :"
"area"
"set stdcell_areas 0"
"set cells [get_cells -q -hier -filter \"@is_hierarchical == false \"]"
"set stdcells [get_cells -q -hier -filter \"@is_hierarchical == false && @is_hard_macro == false \"]"
"foreach_in_coll cell $stdcells {"
"set stdcell_area [get_attr $cell area]"
"set stdcell_areas [expr $stdcell_areas +$stdcell_area]"
"}"
"puts \"area of standard cell is $stdcell_areas\""
"##macro cell"
"set macro_areas 0"
"set macro_cells [filter_coll $cells \"@design_type =~ macro\"]"
"foreach_in_coll cell $macro_cells {"
"set macro_area [get_attr $cell area]"
"set macro_name [get_object_name $cell]"
"set macro_areas [expr $macro_areas +$macro_area]"
"puts \"area of $macro_name is $macro_area\""
"}"
"puts \"area of macro is $macro_areas\""
"set total_estimate_area [expr $stdcell_areas / 0.65 + $macro_areas / 0.82]"
"puts \"The estimated area is $total_estimate_area um^2."
"设置display能显示的最大行数量"
"set enc_tcl_return_display_limit 99999"
:::

## 布局后检查与修复 {#source-06}

:::source
"跑完place需要check什么"
"1）检查setup的时序是否符合预期，一般在-100ps左右都是合理的，需要关注reg2reg  reg2cg  reg2mem(除了In\\out那些)"
"2）检查是否有congestion的问题，先看congestion map,其次看overflow的值是否符合要求，一般在1.5%"
"3）cell 的density (单元摆放密度)不要超过80%"
"4）检查设计的ut利用率（随着步骤往后，利用率是不断上升的，place阶段利用率大概在45%左右）"
"5）检查DRV是否有违例(四种基本DRV)"
"修复setup"
"设置group单独对有违例的path进行优化"
"group_path -name  gp1  -from  [get_cells {cell1 cell2 cell3}]"
"group_path -name gp2  -to [get_cells {cell1 cell2 cell3}]"
"setPathGroupOptions gp1 -effortLevel high"
"setPathGroupOptions gp2 -effortLevel high"
"设置pathmargin/input_delay "
"例如：  原本违例  -20ps, 设置pathmargin, 会变成-120或者-220ps，工具修复到-80ps"
"等工具修完之后，在拿掉这个margin，违例可能就修复掉了"
:::
