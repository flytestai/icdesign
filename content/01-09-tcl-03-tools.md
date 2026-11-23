---
id: 01-09-tcl-03-tools
no: 9
stage: 1
title: TCL 第 3 讲 · 变量操作三剑客：append / incr / expr
en: Tcl 3 - append, incr & expr
hours: 1
minutes: 45
tags: [Tcl, append, incr, expr]
summary: 字符串拼接用 append（两种方法 + 与普通拼接对比）、整数加减用 incr（默认 1 / 正负步长）、一切数学运算交给 expr（含整数除法陷阱）。三剑客是写任何 TCL 脚本都绕不开的三个命令。
---

## append：追加内容（字符串拼接） {#append}

:::goal 会用 append 一次追加多个内容；知道 append 后面写变量名不带 $；会用 incr 做整数加减；会用 expr 做所有数学运算并躲开整数除法的坑。
:::

在原有变量值**末尾**添加新内容，无需重新赋值，效率更高。

**语法：`append 变量名 追加内容`**（注意：append 后面直接写变量名，**不带 $**）

**方法 1**：一次追加多个内容

:::tclrun
set str "Hello"
append str "空格"  "World"  "!"   ;# 可一次性追加多个内容
puts $str                          ;# 输出：Hello World!
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
puts $str2                ;# 输出：Hello World!
:::

:::tip PYTHON 类比
`append` ≈ `s += "..."`，但 TCL 里不用写自己拼自己。
:::

## incr：数值递增 / 递减 {#incr}

incr 是 increment 的缩写（读音：/ˈɪŋkrəmənt/）。**仅用于整数变量**，默认递增 1，可指定递增/递减数值（负数为递减）。

**语法：`incr 变量名 [递增数值]`**（中括号内为可选，默认 1）

:::tclrun
set num1 10
incr num1        ;# 默认+1，num1=11
incr num1 5      ;# +5，num1=16
incr num1 -3     ;# -3，num1=13
puts "num1最终值：$num1"   ;# 输出：num1最终值：13

set num2 0
incr num2 -1     ;# 递减为-1
puts "num2：$num2"   ;# 输出：num2：-1
:::

:::tip PYTHON 类比
`incr i` ≈ `i += 1`；`incr i -3` ≈ `i -= 3`。
:::

## expr：计算（数值运算专用） {#expr}

expr 是 expression（/ɪkˈspreʃn/）的缩写。所有数学运算都要交给 `expr` 命令做。

:::tclrun
set a 3
set b 5
expr {$a * 2}      ;# 乘
expr {$b - $a}     ;# 减
expr {$b / $a}     ;# 整数除法：5/3=1（整数相除结果仍是整数！）
expr {5.0 / 3}     ;# 浮点数除法，想得到小数至少一边要是小数
:::

:::pitfall 重点陷阱（文档强调）：整数除整数，小数部分直接扔掉
`expr {5 / 3}` 的结果是 **1**——整数相除结果仍是整数，和 Python 2 类似。想得到小数，把其中一个数写成 `5.0` 这种浮点形式。**惯例**：expr 的表达式用 `{}` 包起来（不读变量、性能好、避免空格歧义）。
:::

:::tip PYTHON 类比
`expr {...}` ≈ 直接写算式，但 TCL 里"算式"是一条命令。
:::

## 动手练 {#lab}

:::lab 本讲练习（3 题）
1. `set s hi`，用 append 拼出 `hi tcl!`。
2. 用 incr 从 10 递减到 0（循环还没学，先手动写三行）。
3. 算一算 `expr {7 / 2}` 和 `expr {7.0 / 2}` 分别是多少。
:::

:::quiz
练习 1 参考写法？| `set s hi` → `append s { tcl!}` → `puts $s`。
练习 3 的答案？| `expr {7 / 2}` = **3**（整数除法丢小数）；`expr {7.0 / 2}` = **3.5**。
append 后面写 $变量名 行不行？| 不行，直接写变量名：`append str "!"`，不是 `append $str`。
:::

:::check
- 能用 append 一次追加多个内容
- 能用 incr 完成加 1、加 N、减 N
- 能背出整数除法陷阱并知道怎么绕开
:::
