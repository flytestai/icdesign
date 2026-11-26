---
id: 03-01-innovus-plan
no: 31
stage: 3
title: 阶段三导读：40nm Innovus 项目实操路线
en: Stage 3 Guide: Innovus 40nm Project Lab
hours: 0
tags: [导读, 阶段三, Innovus, 学习路线]
summary: 以钉钉知识库的 20 项资料顺序为主线，串起 Floorplan 实操、Innovus 全流程和进阶专题，另列上传的 Word 课件入口。
---

## 课程顺序：以钉钉知识库为准 {#plan}

先做 [第 01 项：Floorplan 实操](/lesson/03-01a-flp-lab/)，认清芯片轮廓、切角与端口清单。下表保留知识库原顺序：已有网站课件的，可从对应入口先学；未成课的条目保留位置，不用其他资料替代。

| 知识库顺序 | 资料主题 | 网站课件安排 |
|---|---|---|
| 01 | flp实操 | [第一讲：芯片切角与端口清单](/lesson/03-01a-flp-lab/)，原文和图来自上传的 Word |
| 02 | 教案-何济达 | 原资料正文待核实 |
| 03 | 芯片后端理论 | 原资料正文待核实 |
| 04 | 数字后端理论及实践-Innovus教程终极版.docx | WPS 预览正文待核实 |
| 05 | INNOVUS项目 | [项目主线：从准备到 ECO](/lesson/03-01b-innovus-flow/) |
| 06 | 新版floorplan | 独立保留，原资料正文待核实 |
| 07 | INNOVUS项目基础 | [补充实操：Memory 面积、Floorplan 评估与密度检查](/lesson/03-01c-project-details/) |
| 08 | Floorplan | [进阶 Floorplan：按层级摆放宏单元](/lesson/03-01d-floorplan-advanced/) |
| 09 | Placement | [Placement：从布局流程到密度与拥塞诊断](/lesson/03-01e-placement-diagnostics/) |
| 10 | Cts | [CTS：从前置检查到时钟树验收](/lesson/03-01f-cts-practice/) |
| 11 | Route | [Route：检查天线、串扰、短路与开路](/lesson/03-01g-route-debug/) |
| 12 | Setup、Hold、Max Cap、Max Tran、Max Fanout、Noise 优化 | [按流程阶段诊断时序与噪声](/lesson/03-01h-timing-noise/) |
| 13 | 手动修复 Calibre DRC（Innovus） | [Calibre DRC：手修与复查](/lesson/03-01i-calibre-drc/) |
| 14 | dbGet 用法详细教程 | [dbGet：只读查询与结果验证](/lesson/03-01j-dbget/) |
| 15 | 闩锁效应（Latch-up） | [闩锁效应：理解触发与预防](/lesson/03-01k-latch-up/) |
| 16 | Overflow | [Overflow：算 GCell 溢出、读拥塞热力图](/lesson/03-01l-overflow/) |
| 17 | ECO 常用命令 | [ECO 命令：变更、合法化与验证](/lesson/03-01m-eco-commands/) |
| 18 | 修复 DRV | [修复 DRV：分类、修改与复查](/lesson/03-01n-drv-repair/) |
| 19 | 分析 Clock Skew | [Clock Skew：从三类报告定位偏斜](/lesson/03-01o-clock-skew/) |
| 20 | 先进工艺 | [双重图形化：光刻分解与签核](/lesson/03-01p-double-patterning/) |

## 补充课：按需要回看，不改变主线顺序 {#supplement}

第 05 项讲完整流程：项目准备 → Innovus 启动 → Floorplan → PowerPlan → Place → CTS → Route / OptRoute → ECO。现有补充材料按这条流程定位；第 07 项不另讲一遍流程。

| 学到哪里 | 可回看的已有课件 |
|---|---|
| 上机前 | [项目环境](/lesson/03-04-project-env/)、[Innovus 工具使用](/lesson/03-02-innovus-start/)、[init_design](/lesson/03-03-innovus-init/) |
| 布局前 | [Floorplan](/lesson/03-05-floorplan/)、[PowerPlan](/lesson/03-06-powerplan/) |
| 布局与时钟 | [Place](/lesson/03-07-place/)、[CTS](/lesson/03-08-cts/) |
| 布线与收尾 | [Route](/lesson/03-09-route/)、[OptRoute](/lesson/03-10-optroute/)、[ECO](/lesson/03-11-eco/) |

:::note 资料来源
知识库决定主题与顺序。第 01 项使用上传的 Word 对应示例；第 05、07–20 项是依据核实主题编写的原创专题，案例用于教学，不是钉钉原文或原图。已导入的九个 Word 主题仍保留原文及随文图；init_design 是原站补充课。第 02、03、04、06 项暂保留目录位置，不用猜测补写原资料。
:::
