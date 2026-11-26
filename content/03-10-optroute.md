---
id: 03-10-optroute
no: 40
stage: 3
title: OptRoute：布线后优化
en: Post-route Optimization
hours: 0
tags: [Innovus, 40nm, 项目实操]
summary: 布线后调优类型；时序、DRC、短路与开路优化。按《04 innovus项目(1).docx》原文顺序整理，保留原图。
---

## 布线后调优类型 {#source-01}

:::note 资料来源
以下小节按《04 innovus项目(1).docx》原顺序收录。命令、用语及示例按原文保留；命令适用性以课程使用的工具版本与项目环境为准。
:::

:::source
"八、OptRoute"
"主要是绕线之后的优化,一般优化后的结果会比route好很多"
"具体的优化的设置取决于工程师自己的一些配置，加在tune里面"
"tune的类型一般有两种"
"例如：在route阶段,  "
"PreRoute.tcl  在绕线之前执行的脚本"
"PostRoute.tcl 在绕线之后执行的脚本"
:::

## 时序、DRC、短路与开路优化 {#source-02}

:::source
"优化的方向："
"timing"
"DRC"
"short"
"open"
"===========================PR流程结束=============================="
"FinalPR  最后一轮PR，fp不能在调整！"
"进入ECO修复阶段,(如果结果很差，没法eco修复，只能RePR)"
:::
