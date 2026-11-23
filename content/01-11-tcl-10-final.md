---
id: 01-11-tcl-10-final
no: 11
stage: 1
title: TCL 第 10 讲 · 综合实战 + 结课自测
en: Tcl 10 - Final Project & Self Test
hours: 1
minutes: 60
tags: [Tcl, 综合实战, EDA, 自测, 结课]
summary: EDA 风格综合脚本（列表+proc+foreach+命令替换串起全部知识点）、结课自测 10 题（覆盖全部知识点）、知识点全覆盖清单（31 条对照表）、后续学习路线。
---

## 10.1 EDA 风格综合脚本（文档场景） {#final}

把变量、列表、循环、函数、命令替换**全部用上**——模拟版图工具里批量处理内存单元：

:::goal 读懂并跑通 EDA 综合脚本；通过结课自测 10 题验证全部知识点掌握；对照知识点清单查漏补缺。
:::

```tcl
;# 1. 定义数据（列表 + 嵌套）
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
    change_selection [get_cells $mem]   ;# 选中当前内存单元
    move_objects -delta {-50 0}         ;# 向左移动50个单位
}

;# 4. 结果统计
puts "全部 $total 个单元处理完毕"
```

:::tclrun
;# 1. 定义数据（列表 + 嵌套）
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
    change_selection [get_cells $mem]
    move_objects -delta {-50 0}
}

;# 4. 结果统计
puts "全部 $total 个单元处理完毕"
:::

逐行拆解用到的知识点：

| 代码 | 用到的知识点 | 出处 |
|---|---|---|
| `set mem_list {...}` 多行 | `{}` 定义列表（可跨行） | 第 5 讲 |
| `proc report {mem idx total}` | 带参函数 + return | 第 9 讲 |
| `[llength $mem_list]` | 命令替换 + 列表长度 | 第 3 / 6 讲 |
| `foreach mem $mem_list` | 遍历列表 | 第 8 讲 |
| `incr idx` | 整数自增 | 第 3 讲 |
| `report $mem $idx $total` | 直接调用函数 | 第 9 讲 |
| `[get_cells $mem]` | 命令替换嵌套（EDA 命令） | 第 2 / 3 讲 |
| `puts "全部 $total 个..."` | 双引号内变量替换 | 第 2 讲 |

## 10.2 结课自测（覆盖全部知识点） {#quiz10}

每题先自己作答，再点开看参考答案：

:::quiz
环境类：innovus 打不开怎么办？win / exit 是干什么的？| 打开 `~/.bashrc` 增加 `source /opt/cadence/cds.sh` 等工具脚本行，然后 `source .bashrc` 重新加载。`win` 打开 Innovus 版图窗口；`exit` / `close` 关闭。
变量类：set a.1 100 后如何正确调用它？| 用 `${a.1}` 包裹调用。直接写 `$a.1` 会被解析成"变量 a + 字符串 .1"，报错 can't read "a": no such variable。
append、incr、expr 各解决什么问题？整数除法的坑是什么？| append 做字符串追加拼接；incr 做整数递增/递减（默认 +1，负数为递减）；expr 做数值运算。坑：整数除整数结果还是整数（5/3=1），想得到小数至少一边要写成浮点数（5.0/3）。
数组类：array set 第一个参数有什么限制？unset 数组(键) 和 unset 数组的区别？| array set 第一个参数必须是不带括号和 key 的纯数组名。`unset 数组(键)` 只删除单个元素（再访问报 no such element in array）；`unset 数组` 删除整个数组（再访问报 no such array）。
列表类：lappend 和 lreplace 谁改源数据？lsort 排数字要加什么参数？| lappend 直接修改源数据；lreplace 不修改源数据（返回新列表，需要 set 接住）。lsort 排数字必须加 `-integer`（默认是字符串字典排序），降序加 `-decreasing`。
取嵌套列表第 2 行第 3 列的两种写法？| ① 双层写法：`lindex [lindex $class_list 1] 2`；② 多级连写：`lindex $class_list 1 2`（由外向内）。
if 的四大语法铁律？| ① `}` 和 elseif/else 同行且中间有空格；② 条件必须用 {} 包裹且 { 不能换行；③ 全部用英文半角符号；④ TCL 严格一行一条命令，不能用换行切开 if 命令。
while 三要素是什么？缺了哪个会死循环？| 初始化 → 判断 → 更新。缺了"更新"（如 `incr i`）就死循环；另可用 `while {1}` + `break` 做无限循环。
args 必须写在参数列表什么位置？| 必须写在参数列表最后；只有 args 时表示可传 0、1、任意多个参数，args 把传入参数打包成一个列表。
proc 不写 return，返回什么？| 返回最后一条命令的结果。
:::

## 10.3 知识点全覆盖清单（文档 → 课程对照） {#checklist}

对照文档章节逐条检查，全部打勾 = 文档知识点无一遗漏：

| 文档章节 | 知识点 | 课程位置 |
|---|---|---|
| 开篇 | innovus 打不开 / .bashrc 配置 / source / win / exit | 第 1 讲 1.1 |
| 开篇 | puts 输出 | 第 1 讲 1.2 |
| 一、1 | 变量命名规则 / set 语法 / 三种类型变量 / puts 多变量 | 第 2 讲 2.1 |
| 一、1 | "名字绑值"心智模型 | 第 2 讲 2.1 |
| 一、1 | {} "" [] 三种替换原理 | 第 2 讲 2.2 |
| 一、1 | set 不支持多变量 → 字典 dict get | 第 2 讲 2.5 |
| 一、2 | 特殊变量名 ${} 调用 | 第 2 讲 2.4 |
| 一、3(1) | append 追加（两种方法 + 对比拼接） | 第 3 讲 3.1 |
| 一、3(2) | incr 递增递减（默认1 / 正负步长 / 仅整数） | 第 3 讲 3.2 |
| 一、3(3) | expr 计算 / 整数除法 / 浮点除法 | 第 3 讲 3.3 |
| 二、1 | 数组定义 set arr(key) / 键可为字符串 / 访问 | 第 4 讲 4.2 |
| 二、1 | array set 批量赋值 / array get / 参数限制 / 嵌套写法 / dict get | 第 4 讲 4.3 |
| 二、1 | 数组增加/修改（同键覆盖） | 第 4 讲 4.4 |
| 二、2 | unset 删元素 / 删整个数组 / 两种报错 | 第 4 讲 4.5 |
| 二、3 | array names / foreach 遍历 / foreach {k v} + array get / 练习 fruit | 第 4 讲 4.6 |
| 三、1 | {} 定义列表（多行 / 含空格元素加引号） | 第 5 讲 5.2 |
| 三、1 | list 命令定义（单行 / 嵌套） | 第 5 讲 5.3 |
| 三、2 | concat / lindex / llength / lappend / lreplace / lsearch / lsort / split / join 与源数据规则 | 第 6 讲总表 |
| 三、3 | 嵌套列表访问（双层 lindex 与多级连写） | 第 6 讲末 |
| 四、1 | if-elseif-else 语法 / 比较与逻辑运算符 / 四大铁律 | 第 7 讲 7.1-7.2 |
| 四、1 | gets stdin 输入 / rand() 随机数 / 猜数字 / 成绩等级 | 第 7 讲 7.3-7.4 |
| 四、2 | while 三要素 / 死循环 / while {1} / break / 倒序复制 / 倒序遍历 | 第 8 讲 8.1 |
| 四、3 | foreach 语法 / EDA 移动对象示例 / 列表求和及原理 | 第 8 讲 8.2 |
| 四、4 | for 语法 / 1-100偶数减奇数练习 | 第 8 讲 8.3 |
| 四、4 | source 文件 | 第 8 讲 8.5 |
| 五、1 | 无参函数 / 调用规则 | 第 9 讲 9.1 |
| 五、2 | 带参函数 / return 语义 / [ ] 接收返回值 | 第 9 讲 9.2 |
| 五、3 | 默认参数 / args 混合写法 | 第 9 讲 9.3-9.4 |
| 五、4 | args 可变参数规则（放最后 / 打包成列表） | 第 9 讲 9.4 |
| 五、5 | global 全局变量 / 局部变量 | 第 9 讲 9.5 |
| 五、6 | max 综合示例 / proc 核心语法总结 | 第 9 讲 9.6-9.7 |

## 10.4 从这里继续走 {#next}

学完本课程，你就具备读/写 EDA 工具（Innovus、DC、PT）TCL 脚本的**核心语法**了。

下一步建议：

1. **直接上手真实项目脚本**——遇到不认识的命令查工具手册（`man` 命令）。
2. **语法层面你已经是"全科医生"**——剩下的是熟练度和工程习惯。
3. 继续本站课程：阶段二的数字 IC 后端概念 → Innovus / ICC2 实操，那里大量用到本课程语法。

:::check
- EDA 综合脚本逐行能说清用了哪个知识点
- 结课自测 10 题全部答对
- 知识点清单 31 条全部打勾
:::
