---
id: 01-01-linux-01-intro
no: 1
stage: 1
title: Linux 第 1 课 · 认识 Linux 与行业工具
en: Linux 1 - Intro & Industry Tools
hours: 2
minutes: 55
tags: [Linux, 入门, VNC, Xshell, Innovus, ICC2]
summary: 什么是 Linux、优点、学习目标；工具三件套 VNC / Xshell / MobaXterm；芯片岗位分工与 PR 工具 Innovus / ICC2；后端工程师的工作技能地图。
---

## 1. 什么是 Linux {#what}

:::goal 知道 Linux 是什么、后端为什么离不开它；认识 VNC / Xshell / MobaXterm 三个工具；看懂芯片岗位分工和 PR 工具的两个流派。
:::

Linux 是**操作系统的一种**。它和我们熟悉的 Windows 有几个关键区别：

| 对比项 | Windows | Linux |
|---|---|---|
| 界面 | 一般都有图形界面 | 一般**没有界面**（纯命令行） |
| 装软件 | 下载安装包，一路下一步 | 一般通过命令安装 |
| 更新 | 经常需要更新 | 一般不需要 |
| 用户 | 一般单个用户使用 | 支持**多用户**同时使用 |

**Linux 系统优点**：

1. 支持多用户、多线程；
2. 占用资源少，系统稳定；
3. 开源、免费；
4. 全球的计算机爱好者共同维护。

**本阶段主要学习目标**：

1. 常用的 Linux 命令；
2. 一些简单的 shell 脚本。

:::tip 为什么后端必须会 Linux
EDA 工具（Innovus / ICC2 / PT）每天跑在 Linux 服务器上，所有交互都靠命令行。Linux 不熟，后面每一步都会别扭。
:::

## 2. 关于工具 {#tools}

**VNC**：远程连接云服务器的桌面（能看到图形界面）。

:::fig linux-01 | VNC viewer 快捷方式
:::

**Xshell**：练习 Linux 的工具（个人/学校免费版入口）。

:::fig linux-02 | Xshell 官网下载页
:::

下载地址：https://www.xshell.com/zh/free-for-home-school/

**MobaXterm**：另一款 Linux 练习工具。

:::fig linux-03 | MobaXterm 官网下载页
:::

下载地址：https://mobaxterm.mobatek.net/download.html

## 3. 芯片的相关岗位 {#jobs}

芯片行业的岗位链路：

**芯片的架构师 → 数字前端 → 数字后端 → 数字验证**

- **前端**：主要负责产生 netlist（网表）；
- **后端**：拿到 netlist，开始 **PR**；
- **PnR / PR**：Place and Route，布局和布线。

:::fig linux-04 | 芯片设计到版图的流程示意
:::

## 4. PR 的工具（EDA 工具） {#eda}

两大流派：

| 工具 | 公司 |
|---|---|
| Innovus | Cadence 公司 |
| ICC2 | Synopsys 公司 |

:::fig linux-05 | Innovus（Cadence）
:::

:::fig linux-06 | ICC2（Synopsys）
:::

PR 要同时实现**两个方向**的目标：

- **physical（物理方向）**：短路、断路——foundary 对工艺有约束；
- **timing（时序方向）**：延迟要满足要求。

## 5. 工作技能地图 {#skills}

1. **Linux 命令一定要熟练！熟练！熟练！**
2. **PR 工具**：页面操作、命令操作、简单的 tcl 脚本编写；
3. **PT 工具**：时序的修复。

:::note 学习顺序
先把 Linux 命令练熟（本阶段第 2-6 课），后面阶段的 Innovus / ICC2 课全都在这个基础上展开。
:::

## 动手练 {#lab}

:::sandbox basic | 本课先用模拟终端热热身：敲 ls 看看输出，输入 help 看全部可用命令
:::

:::quiz
Linux 和 Windows 最显著的差别是什么？| Linux 一般没有图形界面、靠命令行交互，且支持多用户、占用资源少、开源免费。
后端岗位拿到的输入是什么？| 前端产生的 netlist（网表），后端据此开始 PR（Place and Route 布局布线）。
PR 的两大 EDA 工具分别来自哪家公司？| Innovus 来自 Cadence，ICC2 来自 Synopsys。
PR 要同时满足哪两个方向的目标？| physical（物理：短路/断路，受 foundary 工艺约束）和 timing（时序：延迟满足要求）。
:::

:::check
- 能说出 Linux 与 Windows 的核心区别
- 知道 VNC / Xshell / MobaXterm 各自的用途
- 能画出 前端→后端 的岗位链路与 PR 的两个目标方向
:::
