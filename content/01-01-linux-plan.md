---
id: 01-01-linux-plan
no: 1
stage: 1
title: Linux 基础命令和文本处理进阶（课表 12 学时）
en: Linux Fundamentals & Text Processing
hours: 12
minutes: 40
tags: [Linux, Shell, 文本处理]
summary: 阶段一第一门课：Linux 基础命令和文本处理进阶，课表 12 学时。先给出课程规划与模拟终端练习入口，正文内容建设中。
---

## 这门课讲什么 {#plan}

:::goal 能独立在 Linux 终端里完成文件操作、文本处理与进程管理；为 TCL 课程和后续 EDA 工具课打好终端基本功。
:::

按课表，本门课共 **12 学时**，规划如下（正文建设中，先在此占位）：

| 专题 | 内容要点 |
|---|---|
| 终端与文件系统 | cd / ls / pwd / mkdir / cp / mv / rm，路径与权限 |
| 文本三板斧 | grep / sed / awk，报告行提取实战 |
| 查看与统计 | cat / less / head / tail / wc / sort / uniq |
| 进程与作业 | ps / kill / top / 后台运行 / nohup |
| Shell 基础 | 环境变量、.bashrc、alias、脚本入门 |
| 压缩与传输 | tar / gzip / scp / rsync |

:::note 学完 Linux 直接进入 TCL
阶段一的下一门课是 **TCL 基础和编程（6 课时）**，已经上线——TCL 全部 6 课都带浏览器内可运行的练习台。EDA 工具每天跑在 Linux 上，Linux 不熟，后面每一步都别扭。
:::

## 先用浏览器练终端 {#terminal}

正文建设中，但你现在就可以在页内模拟终端里练 Linux 命令（虚拟文件系统 + 30 多个命令）：

:::sandbox basic | 试敲 ls、cd、cat 这些命令，输入 help 看全部可用命令
:::

:::quiz
TCL 课程需要 Linux 基础吗？| 需要一点点：会开终端、会 cd 和 ls 就能开始学 TCL；其余的可以边学边补。
EDA 环境脚本一般加载到哪个文件？| ~/.bashrc，改完用 source .bashrc 重新加载。
:::

:::check
- 能在模拟终端里完成 ls / cd / cat 基本操作
- 知道本门课 12 学时的内容规划
- 准备好进入 TCL 课程
:::
