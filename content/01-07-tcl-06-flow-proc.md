---
id: 01-07-tcl-06-flow-proc
no: 7
stage: 1
title: TCL 第 6 课 · 流程控制与函数：if / 循环 / proc
en: Tcl Basics 6 - Control Flow & proc
hours: 1
minutes: 60
tags: [Tcl, if, while, foreach, for, proc, 函数]
summary: 条件判断 if-elseif-else 与它的四大语法铁律、gets 输入与 rand() 随机数、三种循环（while/foreach/for）怎么选、proc 函数全套（带参/默认参数/args 可变参数/global）。最后一课串起全部知识点做 EDA 风格综合实战。
---

## if 条件判断与四大铁律 {#if}

:::goal 会写 if/elseif/else 并背下四大铁律；会用 gets stdin 读输入、rand() 造随机数；三种循环知道什么时候用哪个；会定义 proc（带参/默认参数/args）并用 global 拿全局变量；能把全部知识串成一个综合脚本。
:::

根据条件执行不同代码块，条件表达式需用 `{}` 包裹。比较运算符：`==` 等于、`!=` 不等于、`>`、`<`、`<=`、`>=`；逻辑：与 `&&`、或 `||`（都写在 expr 里）。

**语法骨架**：

```tcl
if {条件1} {代码块1} elseif {条件2} {代码块2} else {代码块3}
```

**完整示例**（成绩等级）：

:::tclrun
set score 85
if {$score >= 90} {
    puts "成绩等级：A（优秀）"
} elseif {$score >= 80} {
    puts "成绩等级：B（良好）"
} elseif {$score >= 60} {
    puts "成绩等级：C（及格）"
} else {
    puts "成绩等级：D（不及格）"
}
:::

:::pitfall 四大语法铁律（初学者最常踩坑，全部来自文档）
1. `}` 和 `elseif` / `else` 必须**同一行**，中间必须**有空格**。
2. `if` 后面的条件必须包在 `{}` 里，而且 `{` 必须紧跟条件，**不能换行**。
3. 所有大括号、运算符必须是**英文半角符号**，禁止中文括号/空格。
4. TCL 是严格"一行一条命令"：`if` 是单条完整命令，不能用换行把 `}` 和 `elseif` 切开。

为什么？因为 `{...}` 是"分组"——`}` 换行会让 TCL 以为命令提前结束了。
:::

## 用户输入 gets stdin 与随机数 rand() {#input}

`gets stdin 变量` 相当于 Python 的 `input()`——从标准输入读一行存进变量：

:::tclrun
puts "Please enter the score："
gets stdin score
if {$score >= 90} {
    puts "youxiu"
} elseif {$score >= 80} {
    puts "lianghao"
} else {
    puts "jiayou"
}
:::

练习台里的做法：先在下面对话框直接敲 `gets stdin score` 回车，再敲 `85` 回车，最后敲 `puts $score`。如果脚本里有 gets，就先在心里"预输入"一行。

`rand()` 获取 0-1 的随机数（**不可以等于 1**）。先看看它长什么样：

:::tclrun
puts [expr {rand()}]
puts [expr {int(rand()*100)}]   ;# 0-99 的整数随机数（多跑几次看变化）
:::

## while 循环：三要素与死循环 {#while}

适合**不知道要跑几次**、或有明确终止条件的场景（这正是 while 相对 for 突出的地方），循环时用条件加 `break` 结束。

:::note while 就三个要素：初始化 → 判断 → 更新，缺了"更新"就是死循环。
:::

:::tclrun
set i 0                 ;# 1. 初始化
while {$i < 5} {        ;# 2. 条件（花括号必须跟在这一行末尾）
    puts "i = $i"
    incr i              ;# 3. 更新——忘了这行就是死循环
}
:::

**示例：列表倒序复制**

:::tclrun
set source_list {100 200 300 400 500}   ;# 原列表
set target_list ""                      ;# 目标列表（存储倒序结果）
set i [expr {[llength $source_list] - 1}]  ;# 初始索引=列表长度-1（最后一个元素）
while {$i >= 0} {
    lappend target_list [lindex $source_list $i]  ;# 取当前索引元素追加到目标列表
    incr i -1              ;# 索引递减1（向前遍历）
}
puts "原列表：$source_list"
puts "倒序列表：$target_list"
:::

**无限循环写法**：`while {1}`——一直循环（配合 `break` 退出）。练习台里跑了死循环也别怕，解释器有 20 万次保护会自动停。

## foreach 与 for：另外两种循环 {#foreach-for}

**foreach：遍历列表元素（首选）**——直接遍历列表中的每个元素，无需手动控制索引，语法简洁，类似 C 和 Python 中 for 循环的 for-in 写法。语法：`foreach 变量名 列表 { 代码块 }`。

**EDA 真实场景：批量处理内存单元**（这就是后端工程师每天写的 TCL）：

```tcl
;# 定义内存单元列表
set mem_list {
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_4
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_3
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_2
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_1
}
foreach mem $mem_list {
    puts "正在处理：$mem"
    change_selection [get_cells $mem]   ;# 选中当前内存单元
    move_objects -delta {-50 0}         ;# 向左移动50个单位
}
```

`get_cells`、`change_selection`、`move_objects` 都是工具提供的命令，TCL 负责把流程串起来。下面用 puts 模拟跑一遍：

:::tclrun
set mem_list {
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_4
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_3
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_2
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_1
}
foreach mem $mem_list {
    puts "正在处理：$mem"
    puts "  change_selection [get_cells $mem]"
    puts "  move_objects -delta {-50 0}"
}
:::

**示例：计算列表元素总和**

:::tclrun
set num_list {1 2 3 4 5}
set sum 0
foreach num $num_list {
    set sum [expr $sum + $num]   ;# expr 用于数值计算
}
puts "列表元素总和：$sum"   ;# 输出：列表元素总和：15
:::

原理：第一次 0+1，第二次 0+1+2 …… 第五次 0+1+2+3+4+5。Python 类比：`for num in num_list:`。

**for：知道要跑几次时用**——语法 `for {起始} {循环条件} {自增/自减} { 循环体 }`：

:::tclrun
for {set i 0} {$i < 5} {incr i} {
    puts "i = $i"
}
:::

Python 类比：`for i in range(5):`。四段各司其职：起始只跑一次，条件每轮判断，步进每轮结束执行。

**三种循环怎么选**：

| 循环 | 用在什么时候 | Python 对应 |
|---|---|---|
| while | 不知道跑几次、靠条件结束 | `while cond:` |
| foreach | 遍历列表/集合元素 | `for x in lst:` |
| for | 知道次数、按索引走 | `for i in range(n):` |

**source：加载并执行脚本文件**——`source 文件` 把另一个 TCL 脚本的内容载入执行（第 1 课配置环境时已经在用）。练习场不支持 source，把脚本内容直接粘贴即可。

:::lab 文档原题：偶数减奇数
用 for 循环计算 1-100 所有**偶数减奇数**的值。提示：`expr {$i % 2}` 判断奇偶（% 是取余），偶数加、奇数减。答案在 50 左右，跑出来对着看。
:::

:::tclrun
;# 参考实现（先自己写，写完再跑这个对照）
set result 0
for {set i 1} {$i <= 100} {incr i} {
    if {[expr {$i % 2}] == 0} {
        set result [expr {$result + $i}]   ;# 偶数加
    } else {
        set result [expr {$result - $i}]   ;# 奇数减
    }
}
puts "1-100偶数减奇数的值：$result"
:::

## proc：定义函数 {#proc}

**核心语法**：

```tcl
proc 函数名 {参数1 参数2 ...} {
    ;# 函数体
    return 返回值
}
```

关键点：`proc` = 定义函数；`{}` 包裹参数列表；`return` 返回值（**不写 return 则返回最后一条命令的结果**）；调用：`函数名 参数1 参数2`；获取返回值：`[函数名 参数]`。

**无参函数**：

:::tclrun
proc sayHello {} {
    puts "Hello, Tcl!"
}
sayHello    ;# 使用（调用）函数，调用时无 {}
:::

**带参数的函数（最常用）**：`return` 退出当前 proc，并把指定值作为这个 proc 的返回结果。

:::tclrun
proc add {a b} {
    set sum [expr {$a + $b}]
    return $sum
}
set result [add 10 20]
puts "10 + 20 = $result"    ;# 用 [] 接收返回值
:::

**带默认参数的函数**——默认参数写成 `{参数名 默认值}` 放在参数列表里：

:::tclrun
proc addDefault {a {b 5}} {
    return [expr {$a + $b}]
}
puts [addDefault 3]     ;# 只传一个参数（使用默认值）→ 3+5=8
puts [addDefault 3 7]   ;# 传两个参数（覆盖默认值）→ 3+7=10
:::

**可变参数函数（任意个数参数）**——特殊参数名 `args` 接收剩余所有参数（以**列表**方式打包）。调用 `sumAll 1 2 3 4 5` → args = {1 2 3 4 5}。

:::tclrun
proc sumAll {args} {
    set total 0
    foreach num $args {
        set total [expr {$total + $num}]
    }
    return $total
}
puts [sumAll 1 2 3 4 5]
puts [sumAll 10 20]
:::

:::pitfall args 必须写在参数列表最后
如果只有 args，代表可以传 0、1、任意多个参数。固定参数和 args 可以混用：`proc test {a args}`——a 固定，剩下的全进 args。
:::

:::tclrun
proc test {a args} {
    puts "a = $a"
    puts "剩下所有参数args = $args"
}
test 10 20 30 40
:::

**局部变量与全局变量**——TCL 函数内部默认访问不到外面的变量（比 Python 严格：读也要声明）。要用全局变量，必须先 `global` 声明：

:::tclrun
set globalVal 100     ;# 全局变量
proc testGlobal {} {
    global globalVal  ;# 声明使用全局变量
    set localVal 200  ;# 局部变量（函数外无法访问）
    puts "全局变量 globalVal = $globalVal"
    puts "局部变量 localVal = $localVal"
}
testGlobal
:::

**完整实用示例：计算两数最大值**

:::tclrun
proc max {x y} {
    if {$x > $y} {
        return $x
    } else {
        return $y
    }
}
puts "max(5, 9) = [max 5 9]"
:::

## 综合实战：串起全部知识点 {#final}

把变量、列表、循环、函数、命令替换全部用上——EDA 风格的批量处理脚本：

:::tclrun
;# 1. 定义数据（列表）
set mem_list {
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_4
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_3
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_2
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_1
}

;# 2. 定义函数（proc + 参数 + return）
proc report {mem idx total} {
    puts "进度：$idx / $total —— 正在处理：$mem"
    return 0
}

;# 3. 循环处理（foreach + llength + 命令替换）
set total [llength $mem_list]
set idx 0
foreach mem $mem_list {
    incr idx
    report $mem $idx $total
    puts "  change_selection [get_cells $mem]"
    puts "  move_objects -delta {-50 0}"
}

;# 4. 结果统计
puts "全部 $total 个单元处理完毕"
:::

学完这课，阶段一 TCL 部分结课。去**练习场**（顶部导航）把示例脚本全部跑一遍，再回课程首页进入阶段二。

## 动手练 {#lab}

:::lab 四道题验收这一课
1. 写一个 proc `area {w h}` 返回长方形面积，调用并打印。
2. 写一个 proc `greet {name {prefix "Hello"}}` 练默认参数。
3. 写一个 proc `avg {args}` 求任意多个数的平均值（foreach + expr + llength，注意整数除法陷阱）。
4. 猜数字游戏：`expr {int(rand()*100)}` 生成答案，while {1} + gets stdin 循环猜，大了/小了/对了。
:::

:::tclsh 综合练习台：把四道题都做出来，第 4 题把几次猜测依次敲进输入行
:::

:::quiz
if 的四大铁律是什么？| ① } 和 elseif/else 同行且中间有空格；② 条件用 {} 包裹且 { 不换行；③ 全部英文半角符号；④ 一行一条完整命令。
while 三要素？缺了哪个会死循环？| 初始化→判断→更新；缺了"更新"（如 incr i）就死循环，无限循环用 while {1} + break。
三种循环分别用在什么时候？| while 靠条件结束；foreach 遍历列表首选；for 已知次数按索引走。
proc 不写 return，返回什么？| 最后一条命令的结果。
args 必须写在参数列表什么位置？| 最后。只有 args 时可传任意个参数；args 把传入参数打包成列表。
函数内要用外面的变量怎么办？| 先 global 声明（读和写都要声明），否则访问不到。
:::

:::check
- if 四大铁律能背、能识别错误写法
- 三种循环各写一个例子并说清选择依据
- proc 四种形态（无参/带参/默认参数/args）都会写
- 综合脚本不看原文能复写出骨架
:::
