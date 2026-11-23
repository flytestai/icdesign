---
id: 01-02-tcl-01-start
no: 2
stage: 1
title: TCL 第 1 课 · 环境准备与第一个命令
en: Tcl Basics 1 - Environment & First Command
hours: 1
minutes: 45
tags: [Tcl, 入门, puts]
summary: TCL 是 EDA 工具的标准脚本语言，Innovus、DC、PT 全用它。这一课先搞定 EDA 环境加载，写出第一个 puts，弄懂注释怎么写。学完你就能在网页里的 Tcl 练习台上跑出第一行输出。
---

## 先认识 TCL：为什么后端工程师必须会它 {#what}

:::goal 知道 TCL 是什么、为什么 IC 后端离不开它；配好 EDA 环境；能用 puts 输出一句话，并用两种写法加注释。
:::

TCL 是一门非常简单的脚本语言，核心哲学只有一句话：**一切都是命令 + 参数**。

它是 EDA 工具的标准脚本语言——Cadence Innovus、Synopsys DC、PrimeTime 的命令行全是 TCL。你在工具里敲的每一条命令、写的每一个自动化脚本，都是 TCL。所以学 TCL 不是"多学一门语言"，而是**打开后端工具的钥匙**。

好消息：你会 Python（甚至不会也行），学 TCL 就是"换一种说话方式"。对照着学，一周就能上手。

| 你在 Python 里写的 | 在 TCL 里要这样写 |
|---|---|
| `print("hello")` | `puts "hello"` |
| `name = "Tom"` | `set name "Tom"` |
| 注释 `#` | `;#`（行中）或 `#`（行首） |

## 环境准备：EDA 工具怎么加载 {#env}

:::term EDA 环境 | 让工具命令能被找到的一堆配置
TCL 平时不是独立运行的，而是"寄生"在 EDA 工具里。工具装在 Linux 服务器上，环境脚本把它们的位置、许可、路径写进终端会话。
:::

**问题场景**：运行 `innovus -cpus 2` 打不开——终端说找不到命令。

**解决办法**：打开 `~/.bashrc` 文件，在末尾增加以下几行（把各家工具的环境脚本加载进来）：

```tcl
source /opt/cadence/cds.sh
source /opt/mentor/mentor.sh
source /opt/synopsys/snop.sh
source /opt/ansys/rh.sh
```

然后重新加载配置：

```tcl
source .bashrc
```

**打开 Innovus 图形界面**：

```tcl
win
```

**关闭**：`exit` 或 `close`。

:::tip
`source` 就是"把一个脚本文件的内容当场执行一遍"。配置改完忘了 source，等于没改。
:::

## 第一个命令：puts {#puts}

`puts` = put string，作用和 Python 的 `print()` 一样：输出内容并换行。字符串用双引号 `"..."` 包起来。

:::tclrun
puts "Hello, TCL!"
puts "我是后端工程师"
:::

点"运行这段代码"——这就是你的第一行 TCL。下面的输入行可以直接继续敲命令，敲 `set name "张工"` 回车，再敲 `puts "你好，$name"` 回车试试（`$name` 是取变量的值，下一课细讲）。

## 注释：两种写法 {#comment}

- **行首注释**：用 `#`，和 Python 一样。
- **行中注释**：命令后面接 `;#`——分号表示"这一行命令到此结束"，然后 `#` 开始注释。

:::tclrun
set age 25   ;# 这是行中注释
# 这是整行注释
puts $age
:::

:::pitfall 忘了分号直接写 # 注释，命令被吞掉
`set age 25 # 注释` 是错的：TCL 会把 `#` 也当成 set 的参数，报参数错误。行中注释必须写成 `;#`——先分号结束命令，再井号注释。
:::

## 动手练 {#lab}

:::lab 在练习台上跑通三句话
用下面的练习台完成：1）输出"我要学 TCL 了"；2）定义变量 `age` 并打印；3）给其中一句加行中注释。敲错了看报错，报错也是学习的一部分。
:::

:::tclsh 提示：先用 puts 输出一句话试试；命令敲错会看到和真实 tclsh 一样的报错
:::

:::quiz
TCL 的核心哲学是什么？| 一切都是命令 + 参数。
innovus 命令找不到，第一步检查什么？| 检查 `~/.bashrc` 里有没有 source 各家工具的环境脚本，改完记得 `source .bashrc` 重新加载。
puts 的作用相当于 Python 里的什么？| print()，输出内容并换行。
行中注释怎么写？| 用 `;#`：分号结束当前命令，# 开始注释。
:::

:::check
- 能说出 TCL 和 EDA 工具的关系
- 能在网页练习台里用 puts 输出任意一句话
- 能区分 `#` 和 `;#` 两种注释的用法
:::
