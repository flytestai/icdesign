---
id: 01-05-tcl-04-array
no: 5
stage: 1
title: TCL 第 4 课 · 数组：键-值对（相当于 Python 的字典）
en: Tcl Basics 4 - Arrays (Key-Value)
hours: 1
minutes: 50
tags: [Tcl, 数组, array, dict, foreach]
summary: 数组是"键-值对"的集合，对应 Python 的字典。定义、批量赋值 array set、array get/names、删除 unset、两种遍历写法，全在这一课。还有文档反复强调的易错点：array set 第一个参数不能带括号。
---

## 数组是什么、怎么定义 {#define}

:::goal 能用 set arr(key) 定义数组并用键取值；会用 array set 批量赋值；会用两种 foreach 写法遍历数组；会用 unset 删除单个元素或整个数组，并认识对应的两种报错。
:::

数组是"键 - 值对"的集合，键（索引）可以是字符串或数字，值可以是任意数据类型，适合存储关联数据（如学生姓名-学号、产品编号-价格）。**它对应 Python 的 dict**。

**定义与访问：`set 数组名(键名) 值`**

:::tclrun
;# 定义学生数组：键为学号，值为姓名
set student(001) "Xiao Ming"
set student(002) "Xiao Fang"
set student(003) "Xiao Zhang"
set student(class) "三年级2班"    ;# 键也可以是字符串

puts "学号001：$student(001)"     ;# 访问数组元素
puts "班级：$student(class)"      ;# 输出：班级：三年级2班
:::

## 批量赋值：array set（标准写法） {#arrayset}

:::tclrun
array set 数组名 {key1 val1 key2 val2}    ;# 一次性批量赋值（这是写法说明，别直接跑）
:::

真跑的版本：

:::tclrun
array set person  {name zhangsan age 20}  ;# person 是数组名，{}里是键值 key/val 交替
puts [array get person]   ;# 返回 name zhangsan age 20（键值对拍平成列表）
puts [array names person] ;# 只拿所有键名
puts [array size person]  ;# 键值对个数
:::

:::pitfall 两个易错点（文档反复强调）
1. **不可以**写 `array set person(001) {...}` ——`array set` 的第一个参数必须是**数组名字**（单纯名字，不带括号和 key），否则直接报错。
2. 想"每个键又是一个小信息包"，用嵌套列表：`array set person {001 {name zhangsan age 20} 002 {name lisi age 25}}`，然后 `set val $person(001)` 拿到整包，取字段用 `dict get $person(001) name`。
:::

嵌套写法真跑：

:::tclrun
array set person {001 {name zhangsan age 20}  002 {name lisi age 25}}
set val $person(001)      ;# 定义 val 接收列表值
puts $val                 ;# 打印出：name zhangsan age 20
puts [dict get $person(002) name]   ;# 取嵌套字段：lisi
:::

## 增加 / 修改 / 删除 {#change}

**增加与修改是同一句**：`set 数组名(键) 值`——已存在的键就是**修改**，不存在的键就是**新增**。（和 Python 的 dict 赋值一模一样。）

删除用 `unset`：删单个元素 `unset 数组名(键名)`，删整个数组 `unset 数组名`。

:::tclrun
array set person  {name zhangsan age 20}
unset person(name)   ;# 删除键：name
puts [array get person]   ;# 只剩 age 20

unset person         ;# 删除整个 person 数组
puts [array get person]   ;# 输出空
:::

删除后再访问会报错（两种报错信息要认识）：

```tcl
;# 承接上面的 student 数组
unset student(002)
puts $student(002)   ;# 错误！can't read "student(002)": no such element in array

unset student
puts $student(001)   ;# 错误！can't read "student(001)": no such array
```

:::note 两种报错的区别
`no such element in array` = 数组还在、键没了；`no such array` = 整个数组没了。看到报错能立刻分清删的是键还是整个数组，调试就快一半。
:::

## 数组遍历：foreach + array names / array get {#iterate}

`array names 数组名` 获取**所有键名**（Tcl 内置数组专用命令，固定语法）；`array get 数组名` 获取**键和值**。

**方法 1：foreach + array names（拿到 key，再用 key 取值）**

:::tclrun
;# 重新定义数组
set product(id001) "手机"
set product(id002) "电脑"
set product(id003) "平板"

foreach key [array names product] {
    puts "产品$key：$product($key)"
}
:::

**方法 2：foreach {k v} + array get（一轮循环同时拿一个键值对）**

:::tclrun
array set product {001 shouji 002 diannao 003 pingban}
foreach {k v} [array get product] {
    puts "key=$k val=$v"
}
:::

原理：`{k v}` 是变量列表，告诉 foreach——每一轮从数据源取出 2 个元素，依次赋给 k、v。（foreach 的完整讲法在第 8 课。）

**只遍历值 / 只遍历键**：

:::tclrun
array set product {001 shouji 002 diannao}
foreach key [array names product] { puts $product($key) }   ;# 循环获取 val
foreach key [array names product] { puts $key }             ;# 循环获取 key
:::

:::note 小结速查
`array names 数组` 获取 key；`array get 数组` 获取 key 和 val。
:::

## 动手练 {#lab}

:::lab 文档原题：fruit 数组
定义一个数组 `fruit`，编号 001、002、003 分别是 apple、banana、orange。分别遍历它的键、遍历它的值。
:::

:::tclsh 把 fruit 练习敲进来，跑通两种遍历再试 unset
:::

:::quiz
`set 数组名(键) 值` 什么时候是新增、什么时候是修改？| 键已存在就是修改，不存在就是新增。
array set 的第一个参数有什么限制？| 必须是不带括号和 key 的纯数组名，写 person(001) 会直接报错。
unset 数组(键) 和 unset 数组 的区别？| 前者删单个元素（再访问报 no such element in array），后者删整个数组（再访问报 no such array）。
array names 和 array get 分别返回什么？| names 返回所有键名；get 返回键和值交替排列的扁平列表。
:::

:::check
- 能用两种写法定义数组（逐个 set / array set 批量）
- 能写出两种 foreach 遍历并说清区别
- 能背出 array set 首参不能带括号这条铁律
- 能区分两种 unset 报错信息
:::
