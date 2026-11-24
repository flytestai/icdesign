---
id: 03-01-innovus-plan
no: 25
stage: 3
title: 阶段三导读：40nm Innovus 项目实操路线
en: Stage 3 Guide: Innovus 40nm Project Lab
hours: 0
minutes: 15
tags: [导读, 阶段三, Innovus, 学习路线]
summary: 阶段三是全课程的重头戏（课表 41 学时）。本页给出完整的工序清单与学时分配，标出已上线与在建的部分，并说明每一道工序在动手前必须先想清楚什么——避免"照抄步骤跑完一遍，却不知道自己在干什么"。
---

## 这一阶段要干什么 {#plan}

:::goal 知道 41 学时怎么分到九道工序上；知道每一道工序的产出物是什么、判断好坏的指标是什么；明白为什么"先上机跑一遍"不如"先想清楚这一步要解决什么问题"。
:::

阶段二讲的是"文件和数据是什么"，阶段三开始动工具。课表给的 **41 学时**分配如下：

| 工序 | 课表学时 | 本站进度 | 这一关的核心问题 |
|---|---|---|---|
| innovus 的使用 | 2 | [已上线 2 讲](/lesson/03-02-innovus-start/) | 怎么启动、怎么自动化、怎么查帮助 |
| floorplan | 10 | 在建 | 芯片多大、macro 摆哪、约束怎么打 |
| powerplan | 2 | 在建 | 电源怎么送到每个单元 |
| Placement / setup 与 hold | 4 | 在建 | stdcell 怎么摆、时序违例怎么读 |
| CTS | 14 | 在建 | 时钟树怎么建、skew 与 insertion delay |
| OptCTS | 2 | 在建 | 时钟树建完怎么收敛 |
| Route | 4 | 在建 | 信号线怎么绕通、DRC 怎么清 |
| OptRoute | 1 | 在建 | 绕完怎么把时序修回来 |
| ChipFinish | 2 | 在建 | 最后要吐哪些文件给签核 |

:::note 学时说明
本页只作路线导读，不占教学学时。阶段三已上线 **4 学时**（Innovus 启动与 init 导入两讲），其余工序随课程建设陆续补齐；全部上线后本阶段合计 41 学时。
:::

## 九道工序的产出物 {#output}

**判断自己有没有真跑通，看的不是"没报错"，而是"这一步该有的产出物有没有、对不对"。**

| 工序 | 产出物 | 判断指标 |
|---|---|---|
| init | 数据库（`.enc`） | instance 数、时钟数、unconstrained 端点为 0 |
| floorplan | 带尺寸与 macro 的 def | 利用率、长宽比、通道宽度、pin 位置 |
| powerplan | power mesh | IR drop、EM、电源连通性（无孤立单元） |
| place | 摆好 stdcell 的 def | 拥塞（congestion）、setup WNS、密度 |
| CTS | 时钟树 | skew、insertion delay、时钟 latency |
| OptCTS | 优化后的时钟树 | setup/hold 双修后的 WNS、时钟 DRC |
| route | 全绕通的版图 | DRC 数、short/open 数、via 数 |
| OptRoute | 修完时序的版图 | 最终 WNS/TNS、DRC 归零 |
| chipfinish | GDSII / DEF / SPEF / 报告 | 交给签核（PT/PV/PA）的文件齐全 |

## 上手前的三个提醒 {#tips}

1. **每道工序都是"配置 → 执行 → 报告 → 判断"四步**。新人常只做前两步（敲了命令、跑完了），不读报告就往下走，错误一路累积到 route 才发现，重跑代价是几小时到几天。
2. **一定要写脚本，不要在界面里点**。界面操作无法复现、无法 diff、无法交给同事。阶段二讲的每一份数据文件，最后都要通过脚本喂给工具。
3. **时序报告要看"前提"**。同一个 design 在不同 corner 下结论可能完全相反——报告第一行写的那个 view 名字，决定你看到的数字意味着什么（见 [MMMC](/lesson/02-07-pr-mmmc/)）。

:::quiz
阶段三课表总学时是多少？九道工序里学时最多的是哪一道？| 41 学时；CTS 占 14 学时，是重头戏。
为什么"跑完没报错"不能作为工序完成的判断标准？| 工具对很多问题只给 warning 甚至完全静默（如缺时钟），必须靠产出物和报告指标判断。
现在阶段三已上线哪几讲？| Innovus 启动与常用选项、init_design 与数据导入，共 2 讲 4 学时。
:::

:::check
- 能按顺序说出九道工序，并说出每一道的产出物
- 能说出 floorplan、place、CTS、route 各自最关键的一个判断指标
- 明确"配置 → 执行 → 报告 → 判断"四步缺一不可
:::
