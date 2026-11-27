---
id: 03-06-powerplan
no: 36
stage: 3
title: PowerPlan：供电结构与检查
en: Power Planning
hours: 0
tags: [Innovus, 40nm, 项目实操]
summary: 电源规划、供电结构与 DRC 检查；扩展：流程脚本与三种布线。按《04 innovus项目(1).docx》原文顺序整理，保留原图。
---

## 电源规划、供电结构与 DRC 检查 {#source-01}

:::note 资料来源
以下小节按《04 innovus项目(1).docx》原顺序收录。命令、用语及示例按原文保留；命令适用性以课程使用的工具版本与项目环境为准。
:::

:::source
"四、PowerPlan 电源规划"
"又叫打PG（power    ground）"
"powerplan的脚本一般有DFP负责"
"powerplan的目标："
"建立一个强壮的供电网络，避免IRDROP和EM的现象"
"EM：电迁移现象，电子的流动会带动金属原子一起运动，形成堆积或者是侵蚀，出现short或open的情况"
"Power Rail / Follow Pin   主要是给stdcell进行供电，连接到std的vdd和vss的pin"
"Power Ring   电源环线  主要给mem进行供电的一种方式"
"power Stripe  电源条线  "
"Via Piller 给stdcell增强供电的一种打pg的方式"
"Metal_stack   1P15M  block level不会用完所有的层，预留两层给top "
"跑完了powerplan需要检查什么内容？"
"检查drc"
"verify_drc -limit 99999"
"检查是否有floating open的问题"
"verifyConnectivity -net {VDD VSS}"
"editDelete "
"-use {CLOCK POWER SIGNAL}    删除的线的类型"
"-shape {RING STRIPE FOLLOWPIN}  删除电源线的类型"
"addStripe"
"addRing "
:::

:::fig innovus-doc-30.png | 原文图 30 · 电源规划、供电结构与 DRC 检查
:::

:::source
"掌握三种power的区别"
"理解powergroud的结构"
"掌握power打完之后是否有short或者open的问题"
"verifyConnectivity  -net {VDD VSS} -error 99999"
:::

## 扩展：流程脚本与三种布线 {#source-02}

:::source
"延伸："
"1)flow的代码结构："
"1、导入各种定义、文件、变量"
"2、读取数据"
"3、代码核心部分"
"4、保存数据"
"5、output一些文件（rpt、log）"
"2）三种绕线"
"power  电源线  clock  时钟走线  signal  信号走线"
:::

## 原创实操：验收一个 SRAM 宏的电源与地 {#powerplan-pg-lab}

:::note 原创教学
本节是独立纸笔练习。实例名、连通记录、电阻、电流和门槛均为虚构教学输入，不来自外部资料或工具实测；不需要运行任何版图命令。
:::

你拿到两份电源规划快照 `C0`、`C1`，要判断是否可以交接给后续实现。接口清单规定：`U_SRAM0/VP` 接开关域的 `VDD_SRAM_SW`，`U_SRAM0/VN` 接公共地 `VSS`；邻近常开域的 `VDD_AO` 即使在本场景也是 0.80 V，仍不允许与开关域短接。测试模式固定为开关域开启，检查路径从各 pin 经局部金属和条带到指定源端，不以画面上两层重叠代替过孔。

```text
# 原创模拟连通记录；预期两只 PG pin 都能到自己的源端，且无跨网短路。
快照  引脚          期望网         局部实际网     同网源端可达    备注
C0    U_SRAM0/VP   VDD_SRAM_SW    VDD_SRAM_SW    是              —
C0    U_SRAM0/VN   VSS            VSS            否              局部地与地条带间缺过孔
C1    U_SRAM0/VP   VDD_SRAM_SW    VDD_SRAM_SW    是              —
C1    U_SRAM0/VN   VSS            VSS            是              仅补接地过孔
C0/C1 检查范围：以上两个必检端点，三个相关网之间的短路数均为 0
```

:::lab 先判能不能交接，再算端点电压
1. 在 `C0` 标出哪个引脚不能到源端、缺的是什么，不改任何网络归属。说明为什么不能把 `C0` 的地端当成理想 0 V 来算宏电压。
2. 在 `C1` 核对“端点 2/2、开路 0、跨网短路 0”。假设固定负载是 30 mA，源端供电差是 0.80 V，电源路径电阻 0.30 Ω、返回地路径电阻 0.20 Ω；用 `1 mA × 1 Ω = 1 mV` 算出电源跌落、地抬升和宏端有效供电差。
3. 写一条交接记录，包含唯一改动、连通结果、压降及未做的项目检查。课堂静态预算为不超过 20 mV。
:::

验算：`C0` 不能交接；`C1` 的电源跌落为 9 mV、地抬升为 6 mV。宏端 `VP` 扣到 0.791 V，`VN` 相对源端地升到 0.006 V，因此两脚之间只有 0.785 V，有效供电差比源端少 15 mV，满足课堂静态预算。只看 `VP` 会误报为 9 mV 漏掉返回地贡献。

:::check
- 能用“`C1` 只补 `VN` 的地过孔，2/2 端点可达，开路和跨网短路均为 0”描述连通回归。
- 能把“静态手算 15 mV，课堂通过”和“布局 DRC、实际静态/动态 IR 与 EM 签核未运行”分开记录。连通和手算都过，不等于项目签核。
:::

进阶可读[从 PG 连通到 IR/EM 修复回归](/lesson/03-12-pg-ir-em/#pg-domain-and-macro-pins)。
