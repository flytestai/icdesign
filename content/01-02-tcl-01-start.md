---
id: 01-02-tcl-01-start
no: 2
stage: 1
title: TCL 第 1 讲 · 开工准备：环境与第一个命令
en: Tcl 1 - Environment & First Command
hours: 1
minutes: 45
tags: [Tcl, 入门, puts, EDA环境]
summary: TCL 平时不是独立运行的，而是"寄生"在 EDA 工具里。这一课搞定 innovus 打不开的排查、写出第一个 puts、弄清两种注释写法，并在网页练习台上跑出第一行输出。全程 Python 对照。
---

## 为什么第一讲讲环境 {#env}

:::goal 知道 TCL 与 EDA 工具的关系；能排查 innovus 打不开；会 source 加载环境；能用 puts 输出一句话；会用 `#` 和 `;#` 两种注释。
:::

TCL 是 EDA 工具（Cadence Innovus、Synopsys DC 等）的标准脚本语言，所以第一步是把 EDA 环境配好——这是实际工作里天天打交道的部分。

**问题场景**：运行 `innovus -cpus 2` 打不开（命令找不到）。

**解决办法**：打开 `~/.bashrc` 文件，在末尾增加以下几行（把各家 EDA 工具的环境脚本加载进来）：

```tcl
source /opt/cadence/cds.sh
source /opt/mentor/mentor.sh
source /opt/synopsys/snop.sh
source /opt/ansys/rh.sh
```

然后运行（重新加载配置）：

```tcl
source .bashrc
```

**打开 Innovus 图形界面**：

```tcl
win
```

**关闭**：`exit` 或 `close`。

:::note 一句话记住 source
`source` = 把一个脚本文件的内容当场执行一遍。配置改完忘了 source，等于没改。
:::

## 第一个命令：puts {#puts}

`puts` = put string，作用和 Python 的 `print()` 一样：输出内容并换行。字符串用双引号 `"..."` 包起来（也可以用花括号 `{...}`，第 2 讲讲区别）。

:::tclrun
puts "Hello, TCL!"
:::

下面的输入行可以直接继续敲命令：敲 `set name "张工"` 回车，再敲 `puts "你好，$name"` 回车——`$name` 是取变量的值，第 2 讲细讲。

**先记住一张总对照表，心里就有地图了：**

| 你在 Python 里写的 | 在 TCL 里要这样写 |
|---|---|
| `name = "Tom"` | `set name "Tom"` |
| `print(x)` | `puts $x` |
| `x = x + 1` | `incr x` |
| `x + y * 2` | `expr {$x + $y * 2}` |
| 字典 `d = {"a": 1}` | 数组 `set d(a) 1` |
| 列表 `lst = [1,2,3]` | `set lst {1 2 3}` |
| `for i in lst:` | `foreach i $lst { ... }` |
| `def f(a, b):` | `proc f {a b} { ... }` |
| `*args` | `args` |

:::term TCL | Tool Command Language，EDA 工具的脚本语言
核心哲学只有一句话：**一切都是命令 + 参数**。Innovus、DC、PT 的命令行全是 TCL。
:::

## 注释怎么写 {#comment}

- **行首注释**：用 `#`（和 Python 一样）。
- **行中注释**：命令后面接 `;#`——分号表示"这一行命令到此结束"，然后 `#` 开始注释。

:::tclrun
set age 25   ;# 这是注释
:::

:::pitfall 忘了分号直接写 #，命令被吞掉
`set age 25 # 注释` 是错的：TCL 会把 `#` 当成 set 的参数，报参数错误。行中注释必须 `;#`——先分号结束命令，再井号注释。
:::

## 动手练 {#lab}

:::lab 本讲练习（2 题）
1. 配好环境，打开并关闭一次 Innovus 窗口。
2. 用 `puts` 输出"我要学 TCL 了"。
:::

:::quiz
练习 2 怎么写？| `puts "我要学 TCL 了"`。注意英文双引号；puts 自动换行。
innovus 打不开第一件事查什么？| `~/.bashrc` 里有没有 source 各家工具脚本，改完 `source .bashrc`。
TCL 的核心哲学是什么？| 一切都是命令 + 参数。
`puts` 相当于 Python 的什么？| print()，输出内容并换行。
:::

:::check
- 能说出 TCL 和 EDA 工具的关系
- 能在练习台用 puts 输出任意一句话
- 能区分 `#` 和 `;#` 两种注释
:::
