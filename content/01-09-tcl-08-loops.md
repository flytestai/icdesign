---
id: 01-09-tcl-08-loops
no: 8
stage: 1
title: TCL 第 8 讲 · 流程控制（下）：三种循环 while / foreach / for
en: Tcl 8 - Loops
hours: 1
minutes: 55
tags: [Tcl, while, foreach, for, break, source]
summary: while 三要素与死循环、while{1}+break、列表倒序复制与倒序遍历单元格（EDA）、foreach 遍历首选与 EDA 移动对象、for 计数循环、三种循环怎么选、source 加载脚本、文档原题偶数减奇数。
---

## 循环 1：while 循环（条件满足时执行） {#while}

:::goal 背下 while 三要素；会用 while{1}+break；能写列表倒序复制；会 foreach 遍历（含 {k v} 双变量）；会用 for 计数；知道三种循环怎么选；会算偶数减奇数。
:::

适合**不知道要跑几次**、或有明确终止条件的场景——不知道跑几次才是 while 相对 for 突出的地方，循环时用条件加 `break` 结束。

:::note while 就三个要素：初始化 → 判断 → 更新，缺了"更新"就是死循环。
:::

```tcl
set i 0                    ;# 1. 初始化
while {$i < 5} {           ;# 2. 条件（花括号必须跟在这一行末尾）
    puts "i = $i"
    incr i                 ;# 3. 更新——忘了这行就是死循环
}
```

:::tclrun
set i 0
while {$i < 5} {
    puts "i = $i"
    incr i
}
:::

### 示例 1：列表倒序复制（文档示例） {#reverse}

:::tclrun
set source_list {100 200 300 400 500} ;# 原列表
set target_list ""                    ;# 目标列表（存储倒序结果）
set i [expr {[llength $source_list] - 1}]  ;# 初始索引=列表长度-1（最后一个元素）
while {$i >= 0} {
    lappend target_list [lindex $source_list $i]  ;# 取当前索引元素追加到目标列表
    incr i -1                           ;# 索引递减1（向前遍历）
}
puts "原列表：$source_list"     ;# 输出：原列表：100 200 300 400 500
puts "倒序列表：$target_list"   ;# 输出：倒序列表：500 400 300 200 100
:::

### 示例 2：遍历列表执行操作（EDA 场景：倒序处理单元格） {#cells}

```tcl
;# 方法2：倒序遍历（更简洁，无需额外 i 变量）
set cell_count [expr [llength $cell_list] - 1]
while {$cell_count >= 0} {
    set current_cell [lindex $cell_list $cell_count]
    puts "倒序处理单元格：$current_cell"   ;# puts 放循环里，因为在循环外没列表接收
    incr cell_count -1
}
```

**无限循环写法**：`while {1}`——一直循环（配合 `break` 退出）。练习台里跑了死循环也别怕，解释器有 20 万次保护会自动停。

## 循环 2：foreach 循环（遍历列表元素）——首选 {#foreach}

直接遍历列表中的每个元素，无需手动控制索引，语法简洁，是列表遍历的首选（类似 C 和 Python 中 for 循环的 for-in 写法）。

**语法**：`foreach 变量名 列表 { 代码块 }`（变量名会依次赋值为列表的每个元素）

### 示例 1：移动对象（文档示例，EDA 真实场景） {#move}

```tcl
;# 定义内存单元列表
set mem_list {
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_4
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_3
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_2
    I_CONTEXT_MEM/I_CONTEXT_RAM_0_1
}
;# 遍历每个内存单元，执行选中和移动操作
foreach mem $mem_list {
    puts "正在处理：$mem"
    change_selection [get_cells $mem]     ;# 选中当前内存单元
    move_objects -delta {-50 0}           ;# 向左移动50个单位
}
```

这就是后端工程师每天写的 TCL：`get_cells`、`change_selection`、`move_objects` 都是工具提供的命令，TCL 负责把流程串起来。练习台内置了这些 EDA 命令桩，可以直接跑：

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

### 示例 2：计算列表元素总和 {#sum}

:::tclrun
set num_list {1 2 3 4 5}
set sum 0
foreach num $num_list {
    set sum [expr $sum + $num]   ;# expr 用于数值计算
}
puts "列表元素总和：$sum"   ;# 输出：列表元素总和：15
:::

原理：第一次：0+1；第二次：0+1+2……第五次：0+1+2+3+4+5。

:::tip PYTHON 类比
`foreach num $num_list { ... }` ≈ `for num in num_list:`
:::

## 循环 3：for 循环（知道次数时用） {#for}

**语法**：`for {起始} {循环条件} {自增/自减} { 循环体 }`

:::tclrun
for {set i 0} {$i < 5} {incr i} {
    puts "i = $i"
}
:::

:::tip PYTHON 类比
`for i in range(5):`。四段各司其职：起始只跑一次，条件每轮判断，步进每轮结束执行。
:::

**三种循环怎么选（速查表）**：

| 循环 | 用在什么时候 | Python 对应 |
|---|---|---|
| while | 不知道跑几次、靠条件结束 | `while cond:` |
| foreach | 遍历列表/集合元素 | `for x in lst:` |
| for | 知道次数、按索引走 | `for i in range(n):` |

## source：加载并执行脚本文件 {#source}

`source 文件`——把另一个 TCL 脚本文件的内容载入执行（第 1 讲配置环境时已经在用）。练习场不支持 source，把脚本内容直接粘贴即可。

## 动手练 {#lab}

:::lab 文档原题：偶数减奇数
用 for 循环计算 1-100 所有**偶数减奇数**的值。提示：`expr {$i % 2}` 判断奇偶（% 是取余），偶数加、奇数减。
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

:::quiz
while 三要素？缺了哪个会死循环？| 初始化→判断→更新；缺了"更新"（如 incr i）就死循环。
无限循环怎么写？| `while {1}`，配合 break 退出。
foreach 的双变量写法？| `foreach {k v} [array get p] { ... }`——每轮取 2 个元素依次赋给 k、v。
三种循环分别用在什么时候？| while 靠条件结束；foreach 遍历列表首选；for 已知次数按索引走。
source 是干什么的？| 把另一个 TCL 脚本文件的内容载入执行。
:::

:::check
- 能背 while 三要素并解释死循环成因
- 倒序复制列表不看原文能写
- 三种循环各写一个例子并说清选择依据
- 偶数减奇数跑出 50
:::
