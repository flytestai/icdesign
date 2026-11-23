---
id: 01-04-tcl-03-tools
no: 4
stage: 1
title: TCL 第 3 课 · 变量三剑客：append / incr / expr
en: Tcl Basics 3 - append, incr & expr
hours: 1
minutes: 45
tags: [Tcl, append, incr, expr, 运算]
summary: 字符串拼接用 append、整数加减用 incr、一切数学运算交给 expr。这一课还有全课最大的陷阱：整数除整数结果还是整数。三剑客是写任何 TCL 脚本都绕不开的三个命令。
---

## append：追加内容（字符串拼接） {#append}

:::goal 会用 append 在变量末尾追加内容（一次追加多个也行）；会用 incr 做整数加减；会用 expr 做所有数学运算并躲开整数除法的坑。
:::

在原有变量值**末尾**添加新内容，无需重新赋值，效率更高。

**语法：`append 变量名 追加内容`**（注意：append 后面直接写变量名，**不带 $**）

**方法 1**：一次追加多个内容

:::tclrun
set str "Hello"
append str " " "World" "!"   ;# 可一次性追加多个内容
puts $str                    ;# 输出：Hello World!
:::

**方法 2**：用 `{}` 追加

:::tclrun
set str hello
append str { world!}
puts $str
:::

**对比普通拼接**（效果相同，但 append 更简洁）：

:::tclrun
set str2 "Hello"
set str2 "$str2 World!"   ;# 旧办法：读出旧值自己拼自己
puts $str2
:::

Python 类比：`append` ≈ `s += "..."`，但 TCL 里不用写自己拼自己。

## incr：数值递增 / 递减 {#incr}

incr 是 increment 的缩写（读音：/ˈɪŋkrəmənt/）。**仅用于整数变量**，默认递增 1，可指定递增/递减数值（负数为递减）。

**语法：`incr 变量名 [递增数值]`**（中括号内为可选，默认 1）

:::tclrun
set num1 10
incr num1        ;# 默认+1，num1=11
incr num1 5      ;# +5，num1=16
incr num1 -3     ;# -3，num1=13
puts "num1最终值：$num1"

set num2 0
incr num2 -1     ;# 递减为-1
puts "num2：$num2"
:::

Python 类比：`incr i` ≈ `i += 1`；`incr i -3` ≈ `i -= 3`。

## expr：计算（数值运算专用） {#expr}

expr 是 expression（/ɪkˈspreʃn/）的缩写。**所有数学运算都要交给 expr 命令做**。

:::tclrun
set a 3
set b 5
puts [expr {$a * 2}]      ;# 乘
puts [expr {$b - $a}]     ;# 减
puts [expr {$b / $a}]     ;# 整数除法：5/3=1
puts [expr {5.0 / $a}]    ;# 浮点数除法
:::

:::pitfall 整数除整数，小数部分直接扔掉（全课第一大陷阱）
`expr {5 / 3}` 的结果是 **1**，不是 1.67——整数相除结果仍是整数，和 Python 2 一样。想得到小数，把其中一个数写成浮点形式（`5.0 / 3`）。
:::

**惯例**：expr 的表达式用 `{}` 包起来（不读变量、性能好、避免空格歧义）。

比较和逻辑运算也在 expr 里做：`==` 等于、`!=` 不等于、`>`、`<`、`>=`、`<=`、与 `&&`、或 `||`。

:::tclrun
set score 85
puts [expr {$score >= 80}]        ;# 1（真）
puts [expr {$score > 60 && $score < 90}]   ;# 1（与）
puts [expr {$score < 60 || $score > 100}]  ;# 0（或）
:::

## 动手练 {#lab}

:::lab 三道题，敲完看输出对不对
1. `set s hi`，用 append 拼出 `hi tcl!`。
2. 用 incr 从 10 递减到 0（先手动写几行，第 8 课学了 while 再回来优化）。
3. 算一算 `expr {7 / 2}` 和 `expr {7.0 / 2}` 分别是多少。
:::

:::tclsh 练习台在这，把三道题依次敲进来
:::

:::quiz
append 命令后面写变量名还是 $变量名？| 直接写变量名，不带 $。`append str "!"` 而不是 `append $str`。
`incr i -3` 是什么意思？| i 每次（就这一句）减 3。incr 支持负数步长，负数即递减。
`expr {5 / 3}` 结果是多少？为什么？| 1。整数除整数结果仍是整数，小数部分直接扔掉；想要小数用 `5.0 / 3`。
数学运算为什么不直接写 `5 + 3`？| TCL 里 + 不是命令，裸写会被当成字符串参数。必须交给 expr 命令计算。
:::

:::check
- 能用 append 一次追加多个内容
- 能用 incr 完成加 1、加 N、减 N
- 能背出整数除法陷阱并知道怎么绕开
- 比较运算和 && || 都包在 expr 里用
:::
