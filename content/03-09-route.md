---
id: 03-09-route
no: 39
stage: 3
title: Route：布线引擎与短路、开路排查
en: Routing
hours: 0
tags: [Innovus, 40nm, 项目实操]
summary: 三种布线引擎；短路和开路检查；天线效应与串扰。按《04 innovus项目(1).docx》原文顺序整理，保留原图。
---

## 三种布线引擎 {#source-01}

:::note 资料来源
以下小节按《04 innovus项目(1).docx》原顺序收录。命令、用语及示例按原文保留；命令适用性以课程使用的工具版本与项目环境为准。
:::

:::source
"七、Route 布线"
"基本概念"
"route的三种绕线引擎"
"global route"
"sroute"
"nanoroute"
:::

## 短路和开路检查 {#source-02}

:::source
"重点检查内容"
"重点检查short的数量、open的数量"
"一般short的数量在2位数算是比较好的结果"
"如果short数量很多，上千或者上万的，需要debug"
"如何分析short   "
"应该提前要看place之后congestion map，map的红色位置，一般就是route之后的short位置"
"看分布情况， 看short的聚集点"
"1、在top边上，mem的出pin和某一条边 的port绕线打架，也有可能是cell的走线和port的走线打架 "
"解决方案：在边界打partical blkage ,打的大小、深度取决short的深度，目的推开这些cell"
"如果是mem，增加mem的channel   "
"注意：blackage不能一直存在，在route之前删除"
"2、存在mem和mem之间"
"拉开mem之间的间距，或者在channel中间打blkage"
"3、出现在mem的拐角"
"打blkage、添加keepoutmargin、调整floorplan"
:::

## 天线效应与串扰 {#source-03}

:::source
"Antenta  天线效应"
"也可以插buf修复，还有增加shape面积"
"工具自动尝试修复"
"setNanoRouteMode -drouteFixAntenna true -routeInsertAntennaDiode true"
"crosstalk  串扰"
"两根走线较长，且并行时，容易引起串扰"
:::
