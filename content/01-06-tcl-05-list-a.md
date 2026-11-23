---
id: 01-06-tcl-05-list-a
no: 6
stage: 1
title: TCL 第 5 讲 · 列表（上）：定义与读取
en: Tcl 5 - Lists I
hours: 1
minutes: 45
tags: [Tcl, 列表, lindex, llength, 嵌套列表]
summary: 列表是 TCL 最常用的数据结构。两种定义方法（大括号 {} 适合多行 / list 命令适合单行嵌套）、lindex 取元素、llength 求长度、嵌套列表的两种访问写法（双层 lindex 与多级连写）。
---

## 列表是什么、两种核心定义方法 {#define}

:::goal 会用 {} 和 list 两种方法定义列表；会用 lindex / llength 读取；会取嵌套列表里的值（两种写法都熟）。
:::

列表是 TCL 中**最常用**的数据结构，用于存储**有序**的多个元素（元素可以是字符串、数字、甚至另一个列表），支持增删改查、排序、拼接等操作。对应 Python 的 list。

### 方法 1：大括号 {} 定义（适合多行元素） {#brace}

大括号会保留元素的原始格式（如换行、空格），无需转义，**空格和换行都是元素分隔符**：

:::tclrun
set fruit_list {apple banana orange}
puts $fruit_list
puts [llength $fruit_list]   ;# 3 个元素

;# 元素含空格时需用双引号
set with_space {one "two words" three}
puts $with_space
puts [lindex $with_space 1]  ;# two words
:::

多行写完全没问题，`{}` 把换行当分隔符（第 2 讲的分组原理）：

:::tclrun
set cell_list {
    RAM_0_4
    RAM_0_3
    RAM_0_2
}
puts $cell_list
puts "共 [llength $cell_list] 个元素"
:::

### 方法 2：list 命令定义（适合单行 / 嵌套列表） {#listcmd}

list 命令会自动处理元素的分隔，嵌套列表时更清晰：

:::tclrun
;# 普通列表
set num_list [list 1 2 3 4 5]
puts $num_list   ;# 输出：1 2 3 4 5

;# 嵌套列表（列表中包含列表）
set nested_list [list 10 {20 30} {40 50 60}]
puts $nested_list   ;# 输出：10 {20 30} {40 50 60}
:::

## 读取：lindex（索引从 0 开始）与 llength {#read}

**索引从 0 开始**（和 Python 一样）：

:::tclrun
set num_list [list 1 2 3 4 5]
puts [lindex $num_list 2]    ;# 根据索引取元素：取第 3 个元素 → 3
puts [llength $num_list]     ;# 获取列表长度（元素个数）→ 5
:::

:::tip PYTHON 类比
`lindex $l 2` ≈ `l[2]`；`llength $l` ≈ `len(l)`。
:::

## 列表实操示例：嵌套列表访问 {#nested}

一个班级名单：每个学生是"编号 姓名 成绩"的子列表：

:::tclrun
set class_list {
    {001 "Xiao Ming" 95}
    {002 "Xiao Fang" 92}
    {003 "Xiao Zhang" 88}
}
;# 取第2个学生的姓名（索引1的子列表，索引1的元素）
set name [lindex [lindex $class_list 1] 1]
puts "第2个学生姓名：$name"    ;# 输出：第2个学生姓名：Xiao Fang

;# 取第3个学生的成绩（索引2的子列表，索引2的元素）
set score [lindex [lindex $class_list 2] 2]
puts "第3个学生成绩：$score"   ;# 输出：第3个学生成绩：88
:::

读法拆解：`set name [lindex ...]` 中，`[]` 是命令替换——先算里面的；`[lindex [lindex $class_list 外层索引] 内层索引]` 由内向外先取子列表、再取子列表里的元素。

**简写形式**：多级索引可以直接连写（由外向内）：

:::tclrun
set class_list {
    {001 "Xiao Ming" 95}
    {002 "Xiao Fang" 92}
}
set name [lindex $class_list 1 1]   ;# 等价于 lindex [lindex $class_list 1] 1
puts $name
:::

:::tip PYTHON 类比
`lindex $L 1 1` ≈ `L[1][1]`。
:::

## 动手练 {#lab}

:::lab 本讲练习
用 `{}` 定义一个多行列表，装 4 个城市名，其中一个城市名带空格；用 lindex 取第 2 个、用 llength 求长度；再用多级连写法取一个嵌套子列表的值。
:::

:::quiz
列表的索引从几开始？| 0，和 Python 一样。
两种定义方法怎么选？| 多行、保留原始格式用大括号 {}（空格换行都是分隔符，含空格元素套双引号）；单行、嵌套列表用 list 命令（自动处理分隔）。
取嵌套列表第 2 行第 2 列的两种写法？| `lindex [lindex $L 1] 1` 或 `lindex $L 1 1`（由外向内）。
:::

:::check
- 能用两种方法定义列表并说清适用场景
- lindex / llength 不看资料能写
- 嵌套列表两种取值写法都能写对
:::
