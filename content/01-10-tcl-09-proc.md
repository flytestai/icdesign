---
id: 01-10-tcl-09-proc
no: 10
stage: 1
title: TCL 第 9 讲 · 定义 / 使用函数（proc）
en: Tcl 9 - proc Functions
hours: 1
minutes: 55
tags: [Tcl, proc, return, args, global]
summary: proc 函数全套：无参、带参数（return 语义与 [ ] 接收返回值）、默认参数、args 可变参数（必须放最后）、global 全局变量声明、max 综合示例、proc 核心语法总结（文档原文）。
---

## 1. 最简单的无参函数 {#noparam}

:::goal 会写 proc 的四种形态（无参/带参/默认参数/args）；会用 [ ] 接收返回值；会用 global 声明全局变量；背下 proc 核心语法总结。
:::

```tcl
# 定义一个函数：输出 hello
proc sayHello {} {
    puts "Hello, Tcl!"
}

# 使用（调用）函数
sayHello   # 调用时无 {}
```

:::tclrun
proc sayHello {} {
    puts "Hello, Tcl!"
}
sayHello
;# 输出：Hello, Tcl!
:::

## 2. 带参数的函数（最常用） {#param}

```tcl
# 定义：接收两个数字，相加并返回结果
proc add {a b} {
    set sum [expr {$a + $b}]
    return $sum
}

# `return`：退出当前 proc，并且把指定值作为这个 proc 的返回结果。

# 调用
set result [add 10 20]
puts "10 + 20 = $result"
```

:::tclrun
proc add {a b} {
    set sum [expr {$a + $b}]
    return $sum
}
set result [add 10 20]
puts "10 + 20 = $result"
;# 输出：10 + 20 = 30
:::

**调用规则**：

- 普通调用：`函数名 参数1 参数2`（直接写名字，不需要括号）。
- **获取返回值**：`[函数名 参数]`——用命令替换 `[ ]` 接住返回值。

:::tip PYTHON 类比
`def add(a, b): return a + b`；`result = add(10, 20)`。
:::

## 3. 带默认参数的函数 {#default}

TCL 用 args 或直接给参数默认值：

```tcl
# 定义：b 默认是 5
proc addDefault {a {b 5}} {
    return [expr {$a + $b}]
}
# 只传一个参数（使用默认值）
puts [addDefault 3]   ;# 3+5=8
# 传两个参数（覆盖默认值）
puts [addDefault 3 7] ;# 3+7=10
```

:::tclrun
proc addDefault {a {b 5}} {
    return [expr {$a + $b}]
}
puts [addDefault 3]     ;# 8
puts [addDefault 3 7]   ;# 10
:::

:::tip PYTHON 类比
`def addDefault(a, b=5):`——默认参数写成 `{参数名 默认值}` 放在参数列表里。
:::

## 4. 可变参数函数（任意个数参数） {#args}

args 是 TCL 特殊参数：接收调用时传入的所有参数，打包成一个列表。调用 `sumAll 1 2 3 4 5` → args = {1 2 3 4 5}；调用 `sumAll 10 20` → args = {10 20}。

**规则**：args 必须写在参数列表最后；如果只有 args，代表可以传 0、1、任意多个参数。

:::tclrun
;# 定义：求任意多个数字之和
proc sumAll {args} {
    set total 0
    foreach num $args {
        set total [expr {$total + $num}]
    }
    return $total
}
;# 调用
puts [sumAll 1 2 3 4 5]   ;# 15
puts [sumAll 10 20]       ;# 30
:::

**混合写法**（固定参数 + 可变参数）：

:::tclrun
proc test {a args} {
    puts "a = $a"
    puts "剩下所有参数args = $args"
}
test 10 20 30 40
;# 输出 a = 10，args = 20 30 40
:::

:::tip PYTHON 类比
`args` ≈ `*args`。
:::

## 5. 函数内使用局部变量 / 全局变量 {#global}

TCL 函数内部默认访问不到外面的变量（比 Python 严格：读也要声明）。要用全局变量，必须先 `global` 声明：

:::tclrun
set globalVal 100 ;# 全局变量
proc testGlobal {} {
    global globalVal ;# 声明使用全局变量
    set localVal 200 ;# 局部变量（函数外无法访问）
    puts "全局变量 globalVal = $globalVal"
    puts "局部变量 localVal = $localVal"
}
testGlobal
:::

:::tip PYTHON 类比
函数里改全局变量要先 `global x`——TCL 更严格，**读**也要声明。
:::

## 6. 完整实用示例：计算两数最大值 {#max}

:::tclrun
;# 定义函数：返回两个数的最大值
proc max {x y} {
    if {$x > $y} {
        return $x
    } else {
        return $y
    }
}
;# 调用
puts "max(5, 9) = [max 5 9]"
;# 输出：max(5, 9) = 9
:::

## proc 核心语法总结（文档原文） {#summary}

```tcl
proc 函数名 {参数1 参数2 ...} {
    ;# 函数体
    return 返回值
}
```

关键点：

- proc = 定义函数
- {} 包裹参数列表
- return 返回值（**不写则返回最后一条命令结果**）
- 调用：函数名 参数1 参数2
- 获取返回值：[函数名 参数]

**总结**：Tcl 用 proc 定义函数；支持无参、有参、默认参数、可变参数；返回值用 return；调用方式：函数名 参数 或 [函数名 参数] 接收返回值。

## 动手练 {#lab}

:::lab 本讲练习（3 题）
1. 写一个 proc `area {w h}` 返回长方形面积，调用并打印。
2. 写一个 proc `greet {name {prefix "Hello"}}` 练默认参数。
3. 写一个 proc `avg {args}` 求任意多个数的平均值（foreach + expr + llength，注意整数除法陷阱——用 `double()` 转浮点）。
:::

:::tclrun
;# 参考答案（先自己写再对照）
;# 1
proc area {w h} { return [expr {$w * $h}] }
puts "面积 = [area 3 4]"          ;# 12

;# 2
proc greet {name {prefix "Hello"}} { return "$prefix, $name!" }
puts [greet "TCL"]                ;# Hello, TCL!
puts [greet "TCL" "Hi"]           ;# Hi, TCL!

;# 3
proc avg {args} {
    set total 0
    foreach num $args { set total [expr {$total + $num}] }
    return [expr {$total / double([llength $args])}]
}
puts [avg 1 2 3 4]                ;# 2.5
:::

:::quiz
proc 不写 return，返回什么？| 最后一条命令的结果。
默认参数怎么写？| `proc f {a {b 5}} { ... }`——{参数名 默认值}。
args 必须写在参数列表什么位置？| 最后。只有 args 时可传 0、1、任意多个参数，args 把传入参数打包成列表。
函数内要用外面的变量怎么办？| 先 `global x` 声明（读和写都要），否则访问不到。
怎么接收函数返回值？| `[函数名 参数]`——命令替换接住返回值。
:::

:::check
- proc 四种形态都会写
- 能说清 return 的语义与省略 return 的行为
- global 声明的必要性说得清
:::
