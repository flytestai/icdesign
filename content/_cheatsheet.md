---
id: _cheatsheet
title: 命令速查
en: Cheat Sheet
tags: [速查]
summary: Tcl 常用命令一页查：变量、运算、数组、列表、流程控制、函数、输入输出。
---

## 变量与输出 {#var}

| 功能 | 写法 |
|---|---|
| 赋值 | `set x 5` |
| 取值 | `$x`（特殊变量名用 `${a.1}`） |
| 打印 | `puts $x` / `puts "a=$x"` |
| 追加 | `append x "!"` |
| 递增递减 | `incr i` / `incr i -3` |
| 删除 | `unset x` / `unset arr(k)` / `unset arr` |
| 注释 | 行中 `;#`、行首 `#` |
| 分组规则 | `""` 读变量；`{}` 原样；`[cmd]` 命令替换 |

## 运算 {#expr}

| 功能 | 写法 |
|---|---|
| 四则运算 | `expr {$a + $b}` |
| 整数除法陷阱 | `expr {5/3}` → 1；要小数用 `5.0/3` |
| 取余 | `expr {$i % 2}` |
| 比较 | `expr {$x >= 80}` |
| 逻辑 | `expr {$a > 0 && $b > 0}`、`||`、`!` |
| 随机数 | `expr {rand()}`（0~1 不含 1）、`expr {int(rand()*100)}` |

## 数组（键值对） {#array}

| 功能 | 写法 |
|---|---|
| 单个赋值 | `set student(001) "Xiao Ming"` |
| 批量赋值 | `array set person {name zhangsan age 20}` |
| 取键列表 | `array names person` |
| 取键值对 | `array get person` |
| 键值对个数 | `array size person` |
| 取嵌套字段 | `dict get $person(001) name` |

## 列表 {#list}

| 功能 | 写法 |
|---|---|
| 定义 | `set l {a b c}` / `set l [list 1 2 3]` |
| 取元素 | `lindex $l 2`（多级：`lindex $L 1 1`） |
| 长度 | `llength $l` |
| 末尾追加（改源） | `lappend l x y` |
| 替换（不改源） | `lreplace $l 1 2 apple` |
| 查索引 | `lsearch $l 3`（找不到 -1） |
| 排序（不改源） | `lsort -integer -decreasing $l` |
| 拼接 | `concat $l1 $l2` |
| 拆分 / 粘合 | `split "a,b" ,` / `join $l -` |

## 流程控制 {#flow}

| 功能 | 写法 |
|---|---|
| 条件 | `if {$x >= 90} { ... } elseif {...} { ... } else { ... }` |
| 当循环 | `while {$i < 5} { ... incr i }` |
| 遍历 | `foreach x $lst { ... }`（双变量：`foreach {k v} $pairs { ... }`） |
| 计数 | `for {set i 0} {$i < 5} {incr i} { ... }` |
| 跳出 / 下一轮 | `break` / `continue` |
| 无限循环 | `while {1} { ... break }` |
| 加载脚本 | `source 文件` |

## 函数 {#proc}

| 功能 | 写法 |
|---|---|
| 定义 | `proc name {a b} { ... return $v }` |
| 默认参数 | `proc f {a {b 5}} { ... }` |
| 可变参数 | `proc f {args} { ... }`（必须放最后） |
| 调用 | `f 1 2`，取返回值 `[f 1 2]` |
| 全局变量 | 函数内先 `global x` |
| 返回值 | `return $v`；不写则返回最后一条命令结果 |

## Linux 常用（阶段一配套） {#linux}

| 功能 | 写法 |
|---|---|
| 环境加载 | `source ~/.bashrc`（工具脚本写进 .bashrc） |
| 打开/关闭 Innovus 界面 | `win` / `exit`、`close` |
| 找文件 | `grep -r "pattern" .` |
| 看进程 | `ps -ef | grep innovus` |

## 常见报错速查 {#errors}

| 报错信息 | 原因 | 解决办法 |
|---|---|---|
| `can't read "a": no such variable` | 用 `$a.1` 调用含 `.` 的变量名，被解析成变量 a | 用 `${a.1}` 包裹调用 |
| `can't read "student(002)": no such element in array` | 数组元素已被 unset 删除 | 重新 `set` 赋值后再用 |
| `can't read "student(001)": no such array` | 整个数组已被 unset 删除 | 重新定义数组 |
| 死循环（程序卡住不动） | while 缺了"更新"要素 | 检查循环体内有没有 `incr i` 等更新语句 |
| if 语法错误 / 命令提前结束 | `}` 和 elseif 不同行、条件没用 {}、用了中文符号 | 检查四大铁律（第 7 讲） |
| `array set` 报参数错误 | 第一个参数带了括号（如 `person(001)`） | 只写数组名，键放 `{}` 里 |
