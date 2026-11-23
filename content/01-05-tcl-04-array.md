---
id: 01-05-tcl-04-array
no: 4
stage: 1
title: TCL 第 4 讲 · 数组：键-值对（相当于 Python 的字典）
en: Tcl 4 - Arrays (Key-Value)
hours: 1
minutes: 50
tags: [Tcl, 数组, array, dict, unset]
summary: 数组是"键-值对"集合，对应 Python 的字典。定义与访问、array set 批量赋值与两个易错点、嵌套列表写法与 dict get、增改、unset 删除与两种报错、foreach 两种遍历、{} "" [] 原理复用、文档原题 fruit 练习。
---

## 数组是什么、怎么定义 {#define}

:::goal 会用 set arr(key) 定义并访问数组；会用 array set 批量赋值并避开两个易错点；会用嵌套列表写法 + dict get 取嵌套字段；会用 unset 删元素/删数组并认识两种报错；会两种 foreach 遍历。
:::

数组是"键 - 值对"的集合，键（索引）可以是字符串或数字，值可以是任意数据类型，适合存储关联数据（如学生姓名-学号、产品编号-价格）。**它对应 Python 的 dict**。

**定义与访问：`set 数组名(键名) 值`**

:::tclrun
;# 定义学生数组：键为学号，值为姓名
set student(001) "Xiao Ming"
set student(002) "Xiao Fang"
set student(003) "Xiao Zhang"
set student(class) "三年级2班"    ;# 键也可以是字符串

;# 访问数组元素
puts "学号001：$student(001)"     ;# 输出：学号001：Xiao Ming
puts "班级：$student(class)"      ;# 输出：班级：三年级2班
:::

## 批量赋值：array set（标准写法） {#arrayset}

:::tclrun
;# 标准写法：array set 数组名 {key1 val1 key2 val2}  批量一次性赋值
array set person  {name zhangsan age 20}  ;# person 是数组名称 {}里为键值key/val
puts [array get person]   ;# 返回 name zhangsan age 20
puts [array names person] ;# 只拿所有键名
puts [array size person]  ;# 键值对个数
:::

:::pitfall 两个易错点（文档强调）
1. **不可以**写 `array set person(001) {...}` ——`array set` 的第一个参数必须是**数组名字**（单纯名字，不带括号和 key），否则直接报错。
2. 想"每个键又是一个小信息包"，用嵌套列表写法（见下一章）。
:::

**嵌套写法**：`{}` 里为列表，取值后用 dict get 拿字段：

:::tclrun
;# 不可以：array set person(001) {name zhangsan age 20}
;# 可以写成：
array set person {001 {name zhangsan age 20}  002 {name lisi age 25}}
set val $person(001)   ;# 定义 val 接收列表值
puts $val              ;# 打印列表：name zhangsan age 20
puts [dict get $person(002) name]   ;# 取嵌套字段：lisi
:::

## 数组增加 / 修改 {#change}

**增加：`set 数组名(键) 值`**——存在已有的键就是**修改**，不存在就是**新增**。（和 Python 的 dict 赋值一模一样。）

## 数组删除（unset） {#unset}

使用 `unset` 删除数组中的某个元素或整个数组：

**语法**：`unset 数组名(键名)`（删除单个元素）/ `unset 数组名`（删除整个数组）

:::tclrun
array set person  {name zhangsan age 20}
unset person(name)   ;# 删除 键：name
puts [array get person]   ;# 返回 age 20 无 name

unset person          ;# 删除整个数组
puts [array get person]   ;# 返回空值
:::

删除后再访问会报错（两种报错信息要认识）：

```tcl
;# 承接上面的 student 数组
unset student(002) ;# 删除学号002的元素
puts $student(002) ;# 错误！can't read "student(002)": no such element in array

unset student ;# 删除整个student数组
puts $student(001) ;# 错误！can't read "student(001)": no such array
```

:::note 两种报错的区别
`no such element in array` = 数组还在、键没了；`no such array` = 整个数组没了。看到报错能立刻分清删的是键还是整个数组，调试就快一半。
:::

## 数组遍历（foreach + array names / array get） {#iterate}

通过 `array names 数组名` 获取所有键名，再用 foreach 遍历；`array names` 是 Tcl 内置数组专用命令，属于固定语法。

**方法 1：foreach + array names（拿到 key，再用 key 取值）**

:::tclrun
;# 重新定义数组
set product(id001) "手机"
set product(id002) "电脑"
set product(id003) "平板"

;# foreach 循环变量 获取数组 {循环代码块}
foreach key [array names product] {
    puts "产品$key：$product($key)"
}
;# 输出：
;# 产品id001：手机
;# 产品id002：电脑
;# 产品id003：平板
:::

**方法 2：foreach {k v} + array get（一轮循环同时拿一个键值对）**

:::tclrun
array set product {001 shouji 002 diannao 003 pingban}
;# 循环获取键值对
foreach {k v} [array get product] {
    puts "key=$k val=$v"
}
:::

原理：`{k v}` 是变量列表，告诉 foreach：每一轮循环，从数据源取出 2 个元素，依次赋值给 k、v；循环体 `puts "key=$k val=$v"` 打印每一轮的值。（{}（不读变量）和 ""（读变量）是同一类——分组；[] 完全是另一类——替换，第 2 讲的原理在这里再次用到。）

**只遍历 val / 只遍历 key**：

:::tclrun
array set product {001 shouji 002 diannao 003 pingban}
foreach key [array names product] { puts $product($key) }   ;# 循环获取val
foreach key [array names product] { puts $key }             ;# 循环获取key
:::

:::note 小结速查（文档原文）
`array names 数组` 获取 key；`array get 数组` 获取 key 和 val。
:::

## 动手练 {#lab}

:::lab 文档原题：fruit 数组
定义一个数组 `fruit`，里面编号为 001、002、003，分别是 apple、banana、orange。遍历它的键、遍历它的值。
:::

:::tclsh 参考写法在下面，先自己写，再对照（练习台里改改玩）
:::

:::tclrun
set fruit(001) apple
set fruit(002) banana
set fruit(003) orange
foreach key [array names fruit] { puts $key }           ;# 遍历它的键
foreach key [array names fruit] { puts $fruit($key) }   ;# 遍历它的值
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
