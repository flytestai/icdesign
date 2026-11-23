---
id: 01-06-tcl-05-list
no: 6
stage: 1
title: TCL 第 5 课 · 列表：定义、读取与全部操作
en: Tcl Basics 5 - Lists
hours: 1
minutes: 45
tags: [Tcl, 列表, lindex, llength]
summary: 列表是 TCL 最常用的数据结构。两种定义方法、lindex/llength、嵌套列表访问，加上 9 个操作函数全家桶（concat/lappend/lreplace/lsearch/lsort/split/join）与两个必考陷阱（谁改源数据、lsort 字典序）。一课拿下列表。
---

## 列表是什么、两种定义方法 {#define}

:::goal 会用大括号和 list 命令两种方法定义列表；会用 lindex 取元素、llength 求长度；会取嵌套列表里的值（两种写法都熟）。
:::

列表是 TCL 中**最常用**的数据结构，用于存储**有序**的多个元素（元素可以是字符串、数字、甚至另一个列表），支持增删改查、排序、拼接等操作。对应 Python 的 list。

**方法 1：大括号 {} 定义（适合多行元素）**——大括号会保留元素的原始格式（如换行、空格），无需转义，**空格和换行都是元素分隔符**：

:::tclrun
set fruit_list {apple banana orange}
puts $fruit_list
puts [llength $fruit_list]   ;# 3 个元素

;# 元素含空格时需用双引号
set with_space {one "two words" three}
puts $with_space
puts [lindex $with_space 1]  ;# two words
:::

多行写也完全没问题，`{}` 把换行当分隔符：

:::tclrun
set cell_list {
    RAM_0_4
    RAM_0_3
    RAM_0_2
}
puts $cell_list
puts "共 [llength $cell_list] 个元素"
:::

**方法 2：list 命令定义（适合单行 / 嵌套列表）**——list 命令会自动处理元素的分隔，嵌套列表时更清晰：

:::tclrun
;# 普通列表
set num_list [list 1 2 3 4 5]
puts $num_list

;# 嵌套列表（列表中包含列表）
set nested_list [list 10 {20 30} {40 50 60}]
puts $nested_list
:::

## 读取：lindex 与 llength {#read}

**索引从 0 开始**（和 Python 一样）。`lindex $列表 索引` 取元素，`llength $列表` 求长度：

:::tclrun
set num_list [list 1 2 3 4 5]
puts [lindex $num_list 2]    ;# 取第 3 个元素 → 3
puts [llength $num_list]     ;# → 5
:::

Python 类比：`lindex $l 2` ≈ `l[2]`；`llength $l` ≈ `len(l)`。

## 嵌套列表访问（实操示例） {#nested}

一个班级名单：每个学生是"编号 姓名 成绩"的子列表：

:::tclrun
set class_list {
    {001 "Xiao Ming" 95}
    {002 "Xiao Fang" 92}
    {003 "Xiao Zhang" 88}
}
;# 取第2个学生的姓名（索引1的子列表，索引1的元素）
set name [lindex [lindex $class_list 1] 1]
puts "第2个学生姓名：$name"

;# 取第3个学生的成绩（索引2的子列表，索引2的元素）
set score [lindex [lindex $class_list 2] 2]
puts "第3个学生成绩：$score"
:::

读法拆解：`[]` 是命令替换——先算里面的；`[lindex [lindex $class_list 外层索引] 内层索引]` 由内向外先取子列表、再取子列表里的元素。

**简写形式**：多级索引可以直接连写（由外向内）：

:::tclrun
set class_list {
    {001 "Xiao Ming" 95}
    {002 "Xiao Fang" 92}
}
set name [lindex $class_list 1 1]   ;# 等价于 lindex [lindex $class_list 1] 1
puts $name
:::

Python 类比：`lindex $L 1 1` ≈ `L[1][1]`。

## 列表操作函数总表 {#table}

:::goal 记住 9 个列表函数各自的用途和语法；背下"谁改源数据"和"lsort 字典序"两个必考陷阱；能用 split/join 做字符串与列表的互转。
:::

以下示例都基于 `set num_list [list 1 2 3 4 5]`。

| 函数名 | 功能描述 | 语法 | 示例 |
|---|---|---|---|
| concat | 拼接多个列表 | `concat $列表1 $列表2 ...` | `set new_list [concat $num_list {6 7}]` → 1 2 3 4 5 6 7 |
| lindex | 根据索引取元素（索引从 0 开始） | `lindex $列表 索引` | `lindex $num_list 2` → 3 |
| llength | 获取列表长度（元素个数） | `llength $列表` | `llength $num_list` → 5 |
| lappend | 向列表末尾追加元素（支持多个） | `lappend 列表 元素1 元素2 ...` | `lappend num_list 6 7` → **修改源数据** |
| lreplace | 替换列表中指定索引的元素 | `lreplace $列表 起始索引 结束索引 新元素` | `lreplace $num_list 1 2 apple` → 把索引 1-2 的内容换成 apple，**不修改源数据** |
| lsearch | 搜索元素位置（返回索引，未找到返回 -1） | `lsearch $列表 元素` | `lsearch $num_list 3` → 2（给值找索引，和 lindex 方向相反） |
| lsort | 对列表排序 | `lsort [-decreasing] [-integer] $列表` | 默认升序；数字排序必须加 `-integer` |
| split | 将字符串按分隔符转为列表 | `split 字符串 分隔符` | `set lis [split "woaixuexi" x]` |
| join | 将列表按分隔符转为字符串 | `join 列表 分隔符` | `set res [join $lst "-"]` |

挨个跑一遍：

:::tclrun
set num_list [list 1 2 3 4 5]

;# concat：拼接（不改源）
puts [concat $num_list {6 7}]

;# lappend：追加（改源数据）
lappend num_list 6
puts $num_list

;# lreplace：替换（不改源数据，用 set 接住新列表）
set new_list [lreplace $num_list 1 2 apple]
puts $new_list
puts $num_list

;# lsearch：给值找索引
puts [lsearch $num_list 3]
:::

:::pitfall 必考陷阱一：谁改源数据，谁不改
`lappend` 直接**修改源数据**；`lreplace`、`lsort` 都**不修改源数据**——它们返回一个新列表，必须用 `set` 接住结果，否则白算。
:::

:::tclrun
;# 陷阱二现场演示：lsort 默认是字符串字典排序！
puts [lsort {10 9 2 100}]              ;# 字典序：10 100 2 9（不是你想要的）
puts [lsort -integer {10 9 2 100}]     ;# 数字排序：2 9 10 100
puts [lsort -integer -decreasing {10 9 2 100}]   ;# 降序：100 10 9 2
:::

:::pitfall 必考陷阱二：lsort 默认是字符串字典排序，不是数字排序
排数字必须加 `-integer` 参数（浮点用 `-real`）；降序加 `-decreasing`。排错的典型症状：100 排在 2 前面。
:::

## split 与 join：字符串 ↔ 列表互转 {#splitjoin}

`split` 把字符串撕开变列表，`join` 把列表粘起来变字符串——一对互逆操作：

:::tclrun
set lis [split "woaixuexi" x]      ;# 按字符 x 撕开
puts $lis                          ;# woai ue i

set lst {hello world tcl}
set res [join $lst "-"]            ;# 按 - 粘回去
puts $res                          ;# hello-world-tcl
:::

常见实战：处理带分隔符的文件名、路径、报告行。

:::tclrun
set path "I_CONTEXT_MEM/I_CONTEXT_RAM_0_4"
set parts [split $path /]
puts "模块：[lindex $parts 0]"
puts "单元：[lindex $parts 1]"
:::

## split 与 join：字符串 ↔ 列表互转 {#splitjoin}

`split` 把字符串撕开变列表，`join` 把列表粘起来变字符串——一对互逆操作：

:::tclrun
set lis [split "woaixuexi" x]      ;# 按字符 x 撕开
puts $lis                          ;# woai ue i

set lst {hello world tcl}
set res [join $lst "-"]            ;# 按 - 粘回去
puts $res                          ;# hello-world-tcl
:::

常见实战：处理带分隔符的文件名、路径、报告行。

:::tclrun
set path "I_CONTEXT_MEM/I_CONTEXT_RAM_0_4"
set parts [split $path /]
puts "模块：[lindex $parts 0]"
puts "单元：[lindex $parts 1]"
:::

## 动手练 {#lab}

:::lab 定义城市列表并取值
用 `{}` 定义一个多行列表，装 4 个城市名，其中一个城市名带空格；用 lindex 取第 2 个、用 llength 求长度。再用多级连写法取一个嵌套子列表的值。
:::

:::tclsh 把城市列表练习敲进来跑一遍
:::

:::quiz
列表的索引从几开始？| 0，和 Python 一样。
两种定义方法怎么选？| 多行、元素含空格用大括号 {}（保留原始格式，空格换行都是分隔符，含空格的元素套双引号）；单行、嵌套列表用 list 命令（自动处理分隔）。
取嵌套列表第 2 行第 2 列的两种写法？| `lindex [lindex $L 1] 1` 或 `lindex $L 1 1`（由外向内）。
`{}` 定义的列表里某元素自带空格怎么办？| 给这个元素套双引号，如 `{"grape juice"}`。
:::

:::check
- 能用两种方法定义列表并说清适用场景
- lindex / llength 不看资料能写
- 嵌套列表两种取值写法都能写对
:::
