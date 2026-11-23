---
id: 01-07-tcl-06-list-b
no: 6
stage: 1
title: TCL 第 6 讲 · 列表（下）：增删改查、排序与转换
en: Tcl 6 - List Operations
hours: 1
minutes: 50
tags: [Tcl, concat, lappend, lreplace, lsearch, lsort, split, join]
summary: 列表核心操作函数总表（concat/lindex/llength/lappend/lreplace/lsearch/lsort/split/join）+ 两个必考陷阱（谁改源数据、lsort 默认字典序）+ split/join 互逆转换 + 本讲练习。
---

## 列表核心操作函数（含示例） {#table}

:::goal 记住 9 个列表函数的用途和语法；背下"谁改源数据"和"lsort 字典序"两个必考陷阱；会用 split/join 互转字符串与列表。
:::

以下示例都基于 `set num_list [list 1 2 3 4 5]`。

| 函数名 | 功能描述 | 语法 | 示例（基于 num_list = [list 1 2 3 4 5]） |
|---|---|---|---|
| concat | 拼接多个列表 | `concat $列表1 $列表2 ...` | `set new_list [concat $num_list {6 7}]` → 1 2 3 4 5 6 7 |
| lindex | 根据索引取元素（索引从 0 开始） | `lindex $列表 索引` | `lindex $num_list 2` → 3（取第 3 个元素） |
| llength | 获取列表长度（元素个数） | `llength $列表` | `llength $num_list` → 5 |
| lappend | 向列表末尾追加元素（支持多个） | `lappend 列表 元素1 元素2 ...` | `lappend num_list 6 7` → **修改源数据** |
| lreplace | 替换列表中指定索引的元素 | `lreplace $列表 起始索引 结束索引 新元素` | `lreplace $num_list 1 2 apple` → 把列表中索引 1-2 的内容换成 apple，**不修改源数据** |
| lsearch | 搜索元素位置（返回索引，未找到返回 -1） | `lsearch $列表 元素` | `lsearch $num_list 3` → 2；找到元素的索引号，和 lindex 相反（一个给索引拿值，一个给值找索引） |
| lsort | 对列表排序（默认升序，-decreasing 降序） | `lsort [-decreasing] [-integer] $列表` | 排序不修改源数据；默认是字符串字典排序，不是数字排序，数字排序需要加参数 `-integer` |
| split | 将字符串按分隔符转为列表 | `split 字符串 分隔符` | `set lis [split "woaixuexi" x]` |
| join | 将列表按分隔符转为字符串 | `join 列表 分隔符` | `set lst {hello world tcl}`、`set res [join $lst "-"]` 接收结果后 `puts $res` |

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
puts $lis                          ;# woai ue i（我爱学习）

set lst  {hello world tcl}
set res  [join $lst "-"]           ;# 接收结果
puts $res                          ;# hello-world-tcl
:::

常见实战：处理带分隔符的文件名、路径、报告行：

:::tclrun
set path "I_CONTEXT_MEM/I_CONTEXT_RAM_0_4"
set parts [split $path /]
puts "模块：[lindex $parts 0]"
puts "单元：[lindex $parts 1]"
:::

## 动手练 {#lab}

:::lab 本讲练习（3 题，验证两个陷阱）
1. 用 lappend 往 `num_list` 追加 6，验证源列表变了；再用 lreplace 替换索引 0 的元素，验证源列表没变。
2. `set s "a,b,c"`，用 split 拆成列表，再用 join 用 `-` 拼回字符串。
3. 分别跑 `lsort {9 100 20}` 和 `lsort -integer {9 100 20}`，对比结果。
:::

:::quiz
lappend 和 lreplace 谁修改源数据？| lappend 修改源数据；lreplace 不修改，返回新列表要用 set 接住。
lsort 排数字要加什么参数？| -integer（整数）或 -real（浮点）；默认是字符串字典排序，100 会排在 2 前面。
lsearch 返回什么？| 元素所在的索引号；找不到返回 -1。
split 和 join 的关系？| 互逆操作：split 撕开字符串变列表，join 粘合列表变字符串。
:::

:::check
- 9 个列表函数能说出用途和语法
- 两个必考陷阱都能背下来并演示
- split/join 能互转一段实际数据（如路径）
:::
