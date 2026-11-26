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
