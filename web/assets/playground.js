/**
 * playground.js — /playground/ 代码练习场
 * 两种模式：Linux 命令（MiniShell 模拟终端） / Tcl 代码（内置解释器）
 * 练习内容严格按课程顺序组织：Linux 第 2-6 课 → Tcl 第 1-10 讲
 * 每一行命令/代码都带中文注释
 */
(function () {
'use strict';

/* ================================================================
 * 一、练习内容（按课程顺序，逐行注释）
 * ================================================================ */
var LINUX_PLAN = [
  { group: 'Linux 第 2 课 · 连接服务器与目录结构', items: [
    { name: '我是谁、我在哪（whoami / pwd / hostname）', code:
'whoami                  # 当前登录的用户名（模拟环境里是 autumn）\n' +
'pwd                     # 当前所在目录的绝对路径\n' +
'hostname                # 服务器主机名\n' +
'echo $HOME              # 打印家目录环境变量：/home/autumn' },
    { name: '逛一逛系统目录（cd / → ls → /etc）', code:
'cd /                    # 进入根目录，所有目录的起点\n' +
'ls                      # 列出根目录下的内容：etc home tmp usr ...\n' +
'cd /etc                 # /etc 专门放配置文件（密码、网络、端口）\n' +
'ls | head -8            # 管道：只显示前 8 项，避免刷屏\n' +
'cd ~                    # 回到自己的家目录，等价于直接敲 cd' },
    { name: '来去自如（cd - 回到上一次的目录）', code:
'cd /tmp                 # 先进临时目录\n' +
'pwd                     # 确认位置：/tmp\n' +
'cd -                    # 回到上一次的目录，来回切换神器\n' +
'pwd                     # 看到又回到 ~ 了\n' +
'cd ~/backend_lab        # 进练习工程目录\n' +
'pwd                     # 确认：/home/autumn/backend_lab' }
  ]},

  { group: 'Linux 第 3 课 · 目录与文件操作', items: [
    { name: 'ls 全家桶（-l -a -h -t 和 tree）', code:
'cd ~                    # 回到 家目录\n' +
'ls                      # 只列文件名，最简洁\n' +
'ls -l                   # 详细信息：权限/属主/大小/时间，ll 就是它的别名\n' +
'ls -a                   # 连隐藏文件一起显示（.bashrc 这类点开头的）\n' +
'ls -lh                  # -h 把字节换算成 K/M/G，看着舒服\n' +
'ls -t                   # 按修改时间排序，最新的在最上面\n' +
'tree backend_lab        # 树状显示整个工程目录层级' },
    { name: 'mkdir 建目录链 + 练习一（PT 目录全套）', code:
'cd ~                            # 回家目录\n' +
'rm -rf PT                       # 先删掉旧的 PT，保证每次从零开始\n' +
'mkdir -p PT/P1 PT/D2 PT/K3      # -p：父目录不存在也能一路建下去\n' +
'mkdir PT/K3/P4                  # 在 K3 里再建子目录 P4\n' +
'touch PT/P1/txt1 PT/D2/txt2     # touch：一次创建多个空文件\n' +
'touch PT/asd111 PT/qwe222 PT/zxc333 PT/asd444 PT/asd555   # 再建 5 个测试文件\n' +
'mkdir PT/poi111 PT/lkjs222 PT/mnb333 PT/psaik61           # 再建 4 个测试目录\n' +
'ls PT                           # 看看 PT 里现在都有什么' },
    { name: '通配符筛选 + 批量删除（练习一 14-18 题）', code:
'cd ~/PT                 # 进入 PT 目录\n' +
'ls -d p*                # p 开头：poi111 psaik61（-d 只列表名字；P1 大写不算）\n' +
'ls -d *222              # 222 结尾：lkjs222 qwe222\n' +
'ls -d asd*              # asd 开头：asd111 asd444 asd555\n' +
'rm -rf mnb333           # 删目录要带 -r，-f 表示不问直接删\n' +
'rm -f *asd*             # 删掉名字里含 asd 的全部文件：asd111 asd444 asd555\n' +
'ls                      # 看看剩下的结果' }
  ]},

  { group: 'Linux 第 4 课 · 查看与编辑文件', items: [
    { name: '五种查看方式（cat / head / tail / wc / nl）', code:
'cd ~/backend_lab/soc/dc   # 进综合（DC）目录\n' +
'cat soc.sdc               # 整个文件一次打出来，短文件用\n' +
'head -3 soc.sdc           # 只看前 3 行，默认是前 10 行\n' +
'tail -2 soc.sdc           # 只看最后 2 行，查 log 最常用\n' +
'wc -l dc.log              # 统计行数，-l 只数行\n' +
'nl soc.sdc | head -4      # 带行号显示前 4 行' },
    { name: '重定向 > 与管道 |（history 写文件）', code:
'cd ~                          # 回家目录\n' +
'history > my_hist.txt         # > 重定向：把命令历史覆盖写入文件\n' +
'nl my_hist.txt | head -5      # 带行号看前 5 行，确认写进去了\n' +
'ls -l | wc -l                 # 管道：把 ls 的输出交给 wc 数行数\n' +
'cd ~/backend_lab/soc/pnr/reports   # 进布局布线的报告目录\n' +
'cat timing.rpt | grep -n slack     # 管道串联：cat 出内容 → grep 过滤' },
    { name: '找文件（find / du / which）', code:
'cd ~                          # 回家目录\n' +
'find . -name "*.tcl"          # 从当前目录递归找所有 .tcl 脚本\n' +
'find backend_lab -type d      # 只找目录，-type f 则是找文件\n' +
'du -sh backend_lab            # 看这个目录总共占多大，-s 只显示汇总\n' +
'which ls                      # 查命令装在哪：/bin/ls' }
  ]},

  { group: 'Linux 第 5 课 · 搜索、权限与正则表达式', items: [
    { name: 'grep 基础四连（-n / -c / -i / -v）', code:
'cd ~/backend_lab/soc/pnr/reports    # 进报告目录\n' +
'grep -n slack timing.rpt            # -n 显示关键字所在行号\n' +
'grep -c slack timing.rpt            # -c 只输出命中行数\n' +
'grep -i warning ../../dc/dc.log    # -i 忽略大小写（从 reports 往上两层才是 soc）\n' +
"grep -v '^#' paths.rpt              # -v 反向：排除 # 开头的注释行" },
    { name: '权限 chmod（数字法 644/755）', code:
'cd ~                      # 回家目录\n' +
'touch secret.txt          # 建个测试文件\n' +
'ls -l secret.txt          # 看默认权限：-rw-r--r--\n' +
'chmod 600 secret.txt      # 6=r+w：只有自己能读写，其他人全禁\n' +
'ls -l secret.txt          # 权限变成 -rw-------\n' +
'chmod 755 secret.txt      # 7=rwx：自己也拿到执行权限\n' +
'ls -l secret.txt          # 权限变成 -rwxr-xr-x\n' +
'rm -f secret.txt          # 练完删掉' },
    { name: '复制 / 移动 / 排序去重 / 扩展正则', code:
'cd ~                          # 回家目录\n' +
'cp notes.txt notes.bak        # 复制一份，复制目录要加 -r\n' +
'mv notes.bak notes_copy.txt   # mv 改名，本质是移动到新路径\n' +
'ls *.txt                      # 确认新文件在\n' +
'cd ~/backend_lab/soc/pnr/reports    # 进报告目录\n' +
"grep -E 'slack|VIOLATED' timing.rpt | head -3   # -E 扩展正则：匹配 slack 或 VIOLATED\n" +
'sort paths.rpt | head -4      # 按整行字典序排序\n' +
'cut -d" " -f1 paths.rpt | sort -u | head -4     # 取第 1 列 → 排序去重' }
  ]},

  { group: 'Linux 第 6 课 · 文本三剑客 sed / awk', items: [
    { name: 'sed 打印指定行 + 全局替换', code:
'cd ~/backend_lab/soc/pnr/reports    # 进报告目录\n' +
"sed -n '1,4p' drc.rpt               # -n 静默 + p 打印：只输出 1-4 行\n" +
"sed -n '2p' paths.rpt               # 只打印第 2 行\n" +
"sed 's/u_core/CORE/g' paths.rpt | head -3   # s///g 全局替换，只改输出不改文件" },
    { name: 'awk 取列（$1 / $NF / NR 条件）', code:
'cd ~/backend_lab/soc/pnr/reports    # 进报告目录\n' +
"awk '{print $1}' drc.rpt | head -4          # 打印第 1 列（程序必须用单引号）\n" +
"awk '{print $1, $2}' paths.rpt | head -4    # 打印第 1、2 列，逗号默认补空格\n" +
"awk 'NR==2{print $0}' drc.rpt               # NR 是行号：只打印第 2 行整行\n" +
"awk '{print $NF}' paths.rpt | head -4       # $NF = 最后一列" },
    { name: '综合实战：grep → awk → sort 一条链', code:
'cd ~/backend_lab/soc/pnr/reports    # 进报告目录\n' +
"grep -v '^#' paths.rpt | awk '{print $1, $2}' | sort | head -5   # 排除注释行 → 取前两列 → 排序 → 前 5 行" }
  ]}
];

var TCL_PLAN = [
  { group: 'Tcl 第 1 讲 · 开工准备：环境与第一个命令', items: [
    { name: '第一个 Tcl 脚本：puts 输出', code:
'puts "Hello, TCL!"              ;# 输出一行文字\n' +
'puts "这是我的第一条 Tcl 命令"   ;# 中文也没问题\n' +
'puts "第一句"; puts "第二句"     ;# 分号分隔：同一行执行两条命令' }
  ]},
  { group: 'Tcl 第 2 讲 · 变量与替换规则', items: [
    { name: '变量、$替换、${} 与 dict', code:
'puts "Hello, TCL!"              ;# 先打个招呼\n' +
'set name "Zhang San"            ;# set 定义变量，字符串用引号\n' +
'set age 25                      ;# 整数变量\n' +
'set score 98.5                  ;# 浮点变量\n' +
'puts "姓名：$name，年龄：$age，成绩：$score"   ;# $变量名 直接取值\n' +
'set a.1 100                     ;# 变量名里带点号\n' +
'puts ${a.1}                     ;# 带点号必须用 ${} 包起来才能取\n' +
'set info {age 20 name zhangsan} ;# 建一个列表：键和值交替排列\n' +
'puts [dict get $info age]       ;# 当字典用：取出 age 对应的值 20' }
  ]},
  { group: 'Tcl 第 3 讲 · 三剑客 append / incr / expr', items: [
    { name: 'append / incr / expr 运算', code:
'set str "Hello"                 ;# 初始字符串\n' +
'append str " " "World" "!"      ;# append：把后面几段依次拼到末尾\n' +
'puts $str                       ;# 输出 Hello World!\n' +
'set num1 10                     ;# 初始数字\n' +
'incr num1                       ;# incr 默认 +1\n' +
'incr num1 5                     ;# 指定步长 +5\n' +
'incr num1 -3                    ;# 写负数就是减 3\n' +
'puts "num1最终值：$num1"         ;# 输出 13\n' +
'set a 3                         ;# 分子\n' +
'set b 5                         ;# 分母\n' +
'puts [expr {$b / $a}]           ;# 整数除法：5/3 = 1，不是 1.67\n' +
'puts [expr {5.0 / $a}]          ;# 用浮点数就得到 1.666...' }
  ]},
  { group: 'Tcl 第 4 讲 · 数组（键-值对）', items: [
    { name: '数组定义、遍历、删除', code:
'set student(001) "Xiao Ming"     ;# 给数组元素赋值，下标是 001\n' +
'set student(002) "Xiao Fang"     ;# 下标 002\n' +
'set student(class) "三年级2班"    ;# 下标也可以是字符串\n' +
'puts "学号001：$student(001)"     ;# 取值写法：$数组名(下标)\n' +
'array set product {id001 手机 id002 电脑 id003 平板}   ;# 一次性批量设置键值\n' +
'foreach key [array names product] {                    ;# array names：取所有键\n' +
'    puts "产品$key：$product($key)"                     ;# 按键逐个取值打印\n' +
'}                                                       ;# 第一个遍历结束\n' +
'foreach {k v} [array get product] {                     ;# array get：键值平铺成列表\n' +
'    puts "key=$k val=$v"                                ;# 每轮取两个：键和值\n' +
'}                                                       ;# 第二个遍历结束\n' +
'unset product(id002)                                    ;# 删掉一个键\n' +
'puts "还剩 [array size product] 个产品：[array get product]"   ;# size 数个数' }
  ]},
  { group: 'Tcl 第 5 讲 · 列表（上）：定义与读取', items: [
    { name: 'list / lindex / llength / lappend', code:
'set num_list [list 1 2 3 4 5]    ;# list 命令造一个列表\n' +
'puts "列表：$num_list"            ;# 直接打印整个列表\n' +
'puts "第3个元素：[lindex $num_list 2]，长度：[llength $num_list]"   ;# 下标从 0 开始；llength 数元素个数\n' +
'lappend num_list 6 7             ;# lappend：往列表末尾追加，会修改原列表\n' +
'puts "lappend 后：$num_list"      ;# 变成 1 到 7\n' +
'# 嵌套列表：每个元素本身又是一个列表\n' +
'set class_list {}                         ;# 先准备一个空列表\n' +
'lappend class_list {001 "Xiao Ming" 95}   ;# 追加第 1 条记录：学号 姓名 成绩\n' +
'lappend class_list {002 "Xiao Fang" 92}   ;# 追加第 2 条记录\n' +
'puts "嵌套取值：[lindex $class_list 1 1]"  ;# 先取第 2 条，再取它的第 2 项 → Xiao Fang' }
  ]},
  { group: 'Tcl 第 6 讲 · 列表（下）：增删改查、排序与转换', items: [
    { name: 'lreplace / lsearch / lsort / concat / split / join', code:
'set num_list {1 2 3 4 5}                       ;# 原始列表\n' +
'set new_list [lreplace $num_list 1 2 apple]    ;# 把下标 1-2 换成 apple，不改原列表\n' +
'puts "lreplace 后新列表：$new_list"             ;# 得到 1 apple 4 5\n' +
'puts "源列表没变：$num_list"                     ;# 原列表仍是 1 到 5\n' +
'puts "找到 3 的索引：[lsearch $num_list 3]"      ;# lsearch 返回元素下标\n' +
'puts "数字排序：[lsort -integer {10 9 2 100}]"   ;# -integer 按数值大小排\n' +
'puts "字符串排序：[lsort {10 9 2 100}]"          ;# 默认字典序：10 会排最前\n' +
'puts "拼接：[concat {1 2} {3 4}]"                ;# concat 把两个列表接成一个\n' +
'puts "split：[split "woaixuexi" x]  join：[join {a b c} -]"   ;# split 按 x 切；join 用 - 连起来' }
  ]},
  { group: 'Tcl 第 7 讲 · 流程控制（上）：if 与用户输入', items: [
    { name: 'if 条件判断 + gets 输入（下方 stdin 已预填 85）', stdin: '85', code:
'puts "Please enter the score："   ;# 提示用户输入分数\n' +
'gets stdin score                  ;# 从键盘读一行，存进 score\n' +
'if {$score >= 90} {               ;# 90 分及以上走这个分支\n' +
'    puts "成绩等级：A（优秀）"   ;# 90 分以上\n' +
'} elseif {$score >= 80} {         ;# 80-89\n' +
'    puts "成绩等级：B（良好）"   ;# 80-89 分\n' +
'} elseif {$score >= 60} {         ;# 60-79\n' +
'    puts "成绩等级：C（及格）"   ;# 60-79 分\n' +
'} else {                          ;# 60 以下\n' +
'    puts "成绩等级：D（不及格）"   ;# 60 分以下\n' +
'}                                 ;# 整个 if 判断结束\n' +
'puts "再来个随机数：[expr {rand()}]"   ;# rand() 生成 0-1 之间的小数' }
  ]},
  { group: 'Tcl 第 8 讲 · 流程控制（下）：三种循环', items: [
    { name: 'while / foreach / for 三种循环', code:
'set i 0                ;# while 第一步：初始化\n' +
'while {$i < 5} {       ;# 第二步：判断条件，真就继续\n' +
'    puts "i = $i"      ;# 循环体：打印当前值\n' +
'    incr i             ;# 第三步：更新，漏了这行就死循环\n' +
'}                      ;# 第一个 while 结束\n' +
'set source_list {100 200 300 400 500}     ;# 倒序练习的源列表\n' +
'set target_list ""                        ;# 目标列表先置空\n' +
'set i [expr {[llength $source_list] - 1}] ;# 最后一项的下标 = 长度 - 1\n' +
'while {$i >= 0} {                         ;# 从最后一项往前取\n' +
'    lappend target_list [lindex $source_list $i]   ;# 取出元素追加到目标列表\n' +
'    incr i -1                                       ;# 下标递减 1\n' +
'}                                                  ;# 倒序 while 结束\n' +
'puts "倒序列表：$target_list"              ;# 输出 500 400 300 200 100\n' +
'set num_list {1 2 3 4 5}                  ;# foreach 求和的列表\n' +
'set sum 0                                 ;# 累加器归零\n' +
'foreach num $num_list {                   ;# 依次把每个元素放进 num\n' +
'    set sum [expr {$sum + $num}]          ;# 累加\n' +
'}                                         ;# foreach 结束\n' +
'puts "列表元素总和：$sum"                  ;# 输出 15\n' +
'for {set j 0} {$j < 3} {incr j} {         ;# 初始化 / 条件 / 每轮收尾三要素\n' +
'    puts "for 第 $j 轮"                   ;# 循环体\n' +
'}                                         ;# for 结束' }
  ]},
  { group: 'Tcl 第 9 讲 · 定义 / 使用函数 proc', items: [
    { name: 'proc 定义、默认参数、args、global', code:
'proc sayHello {} {          ;# 定义无参函数\n' +
'    puts "Hello, Tcl!"      ;# 函数体\n' +
'}                           ;# 函数定义结束\n' +
'sayHello                    ;# 调用函数\n' +
'proc add {a b} {                          ;# 定义两个参数的函数\n' +
'    return [expr {$a + $b}]               ;# return 返回计算结果\n' +
'}                                         ;# add 定义结束\n' +
'puts "10 + 20 = [add 10 20]"              ;# 用 [] 取函数返回值\n' +
'proc addDefault {a {b 5}} {               ;# 第二个参数带默认值 5\n' +
'    return [expr {$a + $b}]               ;# 没传 b 就用默认值 5\n' +
'}                                         ;# addDefault 定义结束\n' +
'puts "[addDefault 3]  /  [addDefault 3 7]"   ;# 不传 b 用默认 5；传了就用 7\n' +
'proc sumAll {args} {                      ;# args 收集任意多个参数\n' +
'    set total 0                           ;# 累加器\n' +
'    foreach num $args {                   ;# 遍历所有传入的参数\n' +
'        set total [expr {$total + $num}]  ;# 累加\n' +
'    }                                     ;# foreach 结束\n' +
'    return $total                         ;# 返回总和\n' +
'}                                         ;# sumAll 定义结束\n' +
'puts "sumAll 1..5 = [sumAll 1 2 3 4 5]"      ;# 想传几个就传几个，结果 15\n' +
'set globalVal 100                         ;# 定义全局变量\n' +
'proc testGlobal {} {                      ;# 定义无参函数，专门验证 global\n' +
'    global globalVal                      ;# 声明后函数里才能用外部的全局变量\n' +
'    set localVal 200                      ;# 局部变量，函数外看不到\n' +
'    puts "全局 $globalVal / 局部 $localVal"   ;# 全局 100 / 局部 200\n' +
'}                                         ;# testGlobal 定义结束\n' +
'testGlobal                                ;# 调用，验证 global 生效' }
  ]},
  { group: 'Tcl 第 10 讲 · 综合实战', items: [
    { name: 'EDA 风格综合：批量处理内存单元', code:
'# 模拟版图工具里批量处理内存单元，EDA 脚本的典型写法\n' +
'set mem_list {}                                    ;# 先建空列表，装待处理的单元名\n' +
'lappend mem_list I_CONTEXT_MEM/I_CONTEXT_RAM_0_4   ;# 第 1 个单元：I_CONTEXT_RAM_0_4\n' +
'lappend mem_list I_CONTEXT_MEM/I_CONTEXT_RAM_0_3   ;# 第 2 个单元\n' +
'lappend mem_list I_CONTEXT_MEM/I_CONTEXT_RAM_0_2   ;# 第 3 个单元\n' +
'proc report {mem idx total} {                      ;# 进度上报函数\n' +
'    puts "进度：$idx / $total —— 正在处理：$mem"    ;# 打印第几个/共几个\n' +
'}                                                  ;# 函数定义结束\n' +
'set total [llength $mem_list]                      ;# 总数 = 列表长度\n' +
'set idx 0                                          ;# 计数器从 0 开始\n' +
'foreach mem $mem_list {                            ;# 逐个处理每个单元\n' +
'    incr idx                                       ;# 计数 +1\n' +
'    report $mem $idx $total                        ;# 调函数报进度\n' +
'    puts "  change_selection [get_cells $mem]"     ;# 选中该单元（工具命令这里用 puts 模拟）\n' +
'    puts "  move_objects -delta {-50 0}"           ;# 向左移动 50，模拟摆放调整\n' +
'}                                                  ;# foreach 结束\n' +
'puts "全部 $total 个单元处理完毕"                   ;# 收尾提示' },
    { name: '猜数字游戏（下方 stdin 已预填 3 次猜测）', stdin: '50\n75\n25', code:
'set answer [expr {int(rand()*100)}]  ;# 随机生成 0-99 的答案\n' +
'set times 0                          ;# 记录已经猜了几次\n' +
'while {1} {                          ;# 条件恒为真：死循环，靠 break 退出\n' +
'    incr times                       ;# 次数 +1\n' +
'    puts "第 $times 次猜：请输入 0-99 的数字"   ;# 提示输入\n' +
'    gets stdin guess                 ;# 读入这次猜的数\n' +
'    if {![string length $guess]} {   ;# stdin 读光了（下方预输入已用完）\n' +
'        puts "stdin 读完了（下方只有 3 行），答案是 $answer"   ;# 公布答案，免得死循环\n' +
'        break                        ;# 跳出循环\n' +
'    }                                ;# 守卫 if 结束\n' +
'    if {$guess == $answer} {         ;# 猜中了\n' +
'        puts "猜对了！答案是 $answer"   ;# 恭喜\n' +
'        break                        ;# break 跳出 while 循环\n' +
'    } elseif {$guess > $answer} {    ;# 猜大了\n' +
'        puts "大了"                  ;# 提示往小猜\n' +
'    } else {                         ;# 猜小了\n' +
'        puts "小了"                  ;# 提示往大猜\n' +
'    }                                ;# 猜大/猜小判断结束\n' +
'}                                    ;# while 结束' }
  ]}
];

/* ================================================================
 * 二、UI：交互终端 / 解释器 + 练习代码编辑器
 *   下面是能自己敲的终端（Linux）/ 解释器（Tcl）
 *   「跑整段」= 把上面逐条敲进去；「下一行」= 一条一条来
 * ================================================================ */
var state = { mode: 'linux', cursor: 0 };

function el(id) { return document.getElementById(id); }
function termSh() { var n = el('pg-term'); return n ? n.__sh : null; }
function tclRepl() { var n = el('pg-tcl'); return n ? n.__tsbx : null; }
function codeEl() { return el('pg-code'); }
function planOf(mode) { return mode === 'linux' ? LINUX_PLAN : TCL_PLAN; }

/** 编辑器里的非空行（注释行也算一步，方便照着课一行一行过） */
function codeLines() {
  return codeEl().value.split('\n')
    .map(function (s) { return s.replace(/\s+$/, ''); })
    .filter(function (s) { return s.trim() !== ''; });
}

/** Tcl：把代码按"逻辑块"切开——花括号/中括号没闭合就并到下一行 */
function tclBlocks() {
  var out = [], buf = '';
  var kit = (typeof TclKit !== 'undefined') ? TclKit : null;
  codeLines().forEach(function (line) {
    buf = buf ? buf + '\n' + line : line;
    var done = true;
    if (kit && kit.isComplete) { try { done = kit.isComplete(buf); } catch (e) { done = true; } }
    if (done) { out.push(buf); buf = ''; }
  });
  if (buf.trim()) out.push(buf);
  return out;
}

/* ---------------- Linux：往终端里喂 ----------------- */
function feedLinux(line) {
  var sh = termSh();
  if (!sh) return;
  var t = line.trim();
  if (!t) return;
  if (t.charAt(0) === '#') { sh.print(t, 'cmt'); return; }   // 整行注释：灰字回显，不执行
  if (t === 'clear') { sh.clear(); return; }
  sh.feed(t);
}

function runLinuxAll() {
  var sh = termSh();
  if (!sh) { showTip('% 终端组件未加载，请刷新页面'); return; }
  var lines = codeLines();
  if (!lines.length) { sh.print('（上面的练习代码是空的）', 'dim'); return; }
  sh.print('—— 开始执行上面这 ' + lines.length + ' 行（跑完可以继续在下面自己敲）——', 'dim');
  for (var i = 0; i < lines.length; i++) feedLinux(lines[i]);
  state.cursor = lines.length;
  syncStep();
  focusTerm();
}

/* ---------------- Tcl：往解释器里喂 ----------------- */
function tclSetupStdin(repl) {
  var sd = el('pg-stdin');
  var arr = (sd && sd.value.trim()) ? sd.value.split('\n').filter(function (x) { return x !== ''; }) : [];
  repl.setStdin(arr);
  return arr.length;
}

function feedTclBlock(repl, block) {
  var echo = block.split('\n').map(function (l, i) { return (i === 0 ? 'tclsh> ' : '   ...> ') + l; }).join('\n');
  repl.echo(echo);
  repl.run(block);
}

function runTclAll() {
  var repl = tclRepl();
  if (!repl) { showTip('% Tcl 解释器未加载，请刷新页面'); return; }
  var blocks = tclBlocks();
  if (!blocks.length) { repl.print('（上面的练习代码是空的）', 'dim'); return; }
  var n = tclSetupStdin(repl);
  repl.print('—— 开始执行上面这片代码（' + blocks.length + ' 段' + (n ? '，stdin 预输入 ' + n + ' 行' : '') + '）——', 'dim');
  for (var i = 0; i < blocks.length; i++) feedTclBlock(repl, blocks[i]);
  var left = repl.stdinLeft();
  if (left) repl.print('% stdin 还剩 ' + left + ' 行没被 gets 读走', 'dim');
  state.cursor = blocks.length;
  syncStep();
  repl.focus();
}

/* ---------------- 公共：整段 / 下一行 / 清空 / 重置 ----------------- */
function totalSteps() {
  return state.mode === 'linux' ? codeLines().length : tclBlocks().length;
}

function syncStep() {
  var btn = el('pg-step');
  if (!btn) return;
  var total = totalSteps();
  var done = Math.min(state.cursor, total);
  btn.textContent = '⏭ 下一条 (' + done + '/' + total + ')';
  btn.disabled = done >= total;
}

function stepOnce() {
  if (state.mode === 'linux') {
    var lines = codeLines();
    if (state.cursor >= lines.length) return;
    feedLinux(lines[state.cursor]);
  } else {
    var repl = tclRepl();
    var blocks = tclBlocks();
    if (!repl || state.cursor >= blocks.length) return;
    if (state.cursor === 0) tclSetupStdin(repl);
    feedTclBlock(repl, blocks[state.cursor]);
  }
  state.cursor++;
  syncStep();
}

function runAll() {
  saveCode();
  if (state.mode === 'linux') runLinuxAll(); else runTclAll();
}

function clearTerm() {
  if (state.mode === 'linux') { var sh = termSh(); if (sh) sh.clear(); }
  else { var repl = tclRepl(); if (repl) repl.clear(); }
}

function resetEnv() {
  if (state.mode === 'linux') {
    var sh = termSh();
    if (sh) sh.reset(true);
  } else {
    var repl = tclRepl();
    if (repl) {
      repl.fresh();
      repl.print('—— Tcl 解释器已重置（变量、数组、proc 全清）——', 'dim');
      repl.focus();
    }
  }
  state.cursor = 0;
  syncStep();
}

function focusTerm() {
  var box = state.mode === 'linux' ? el('pg-term') : el('pg-tcl');
  var inp = box && box.querySelector('.sbx-in');
  if (inp) inp.focus();
}

function showTip(text) {
  if (state.mode === 'linux') { var sh = termSh(); if (sh) sh.print(text, 'err'); }
  else { var r = tclRepl(); if (r) r.print(text, 'err'); }
}

/* ---------------- 下拉选择 / 存档 ---------------- */
function buildSelect() {
  var sel = el('pg-example');
  sel.innerHTML = '';
  var blank = document.createElement('option');
  blank.value = ''; blank.textContent = '—— 按课程顺序选一组练习 ——';
  sel.appendChild(blank);
  planOf(state.mode).forEach(function (g, gi) {
    var og = document.createElement('optgroup');
    og.label = g.group;
    g.items.forEach(function (it, ii) {
      var o = document.createElement('option');
      o.value = gi + '-' + ii;
      o.textContent = it.name;
      og.appendChild(o);
    });
    sel.appendChild(og);
  });
}

// 代码框高度跟着内容走：正好比代码多留一行空白，超过 480px 就内部滚动。
// 早期固定 430px，短代码下方会空出一大片，看着像"题目区"很重。
function fitCode() {
  var ta = codeEl();
  if (!ta) return;
  var cs = window.getComputedStyle(ta);
  var lh = parseFloat(cs.lineHeight) || 23;
  var pad = (parseFloat(cs.paddingTop) || 0) + (parseFloat(cs.paddingBottom) || 0);
  var bd = (parseFloat(cs.borderTopWidth) || 0) + (parseFloat(cs.borderBottomWidth) || 0);
  var lines = String(ta.value || '').split('\n').length;
  var rows = Math.max(lines + 1, 4);
  ta.style.height = Math.min(Math.round(rows * lh + pad + bd), 480) + 'px';
}

function storeKey() { return 'pg_code_v3_' + state.mode; }

function saveCode() {
  try { localStorage.setItem(storeKey(), codeEl().value); } catch (e) {}
}

function loadCode() {
  var def = planOf(state.mode)[0].items[0].code;
  try {
    var s = localStorage.getItem(storeKey());
    codeEl().value = s || def;
  } catch (e) { codeEl().value = def; }
  state.cursor = 0;
  syncStep();
  fitCode();
}

/* ---------------- 模式切换 ---------------- */
function setMode(mode, focus) {
  state.mode = mode;
  state.cursor = 0;
  var btns = document.querySelectorAll('.pg-mode');
  for (var i = 0; i < btns.length; i++) {
    btns[i].className = 'pg-mode' + (btns[i].getAttribute('data-mode') === mode ? ' on' : '');
  }
  el('pg-term').style.display = mode === 'linux' ? '' : 'none';
  el('pg-tcl').style.display = mode === 'tcl' ? '' : 'none';
  el('pg-stdin-box').style.display = mode === 'tcl' ? '' : 'none';
  el('pg-eh').textContent = mode === 'linux'
    ? 'Linux 命令（一行一条；# 开头是注释。下面可以自己敲，也可以点「下一行」一条条来）'
    : 'Tcl 代码（;# 或 # 开头都是注释。下面解释器可以一行一敲，变量会一直留着）';
  el('pg-note').innerHTML = mode === 'linux'
    ? '上下两个环境是同一个：下面终端里自己敲的命令，和「跑整段」执行的是同一套文件系统，所以 <b>rm 掉的文件真的会没</b>；想恢复初始状态点「重置环境」或终端右上角的「重置」。支持的命令：ls（-l -a -h -t -d）·cd（含 cd -）·pwd·mkdir·touch·rm·cp·mv·cat·head·tail·wc·nl·grep（含 -R）·sed·awk·sort（含 -u）·uniq·cut·find·du·chmod·tree·which·history·echo·通配符 <code>*</code>·管道与重定向。注意：awk / sed 的程序要写单引号，双引号里 <code>$1</code> 会先被 shell 吃掉。tar / ln / md5sum 这类需要真实文件系统的命令，请在课程页的练习终端或真机上练。'
    : '下面的解释器是有状态的：<b>set 过的变量、proc 定义都留着</b>，敲一行看一行结果，最适合试 `expr`、`lindex`、`string` 这类小命令。需要 <code>gets stdin</code> 的练习，先在下面 stdin 框里预写好每行一个值。支持：set·puts·expr·incr·append·unset·array·dict get·list/lindex/llength/lappend/lreplace/lsearch/lsort/concat/split/join·if·while·foreach·for·break·continue·proc（默认参数与 args）·global·return·gets stdin·rand()。';
  buildSelect();
  loadCode();
  if (focus !== false) focusTerm();
}

/* ---------------- 初始化 ---------------- */
function mount() {
  var ta = codeEl();
  if (!ta) return;

  var btns = document.querySelectorAll('.pg-mode');
  for (var i = 0; i < btns.length; i++) {
    btns[i].addEventListener('click', function () { setMode(this.getAttribute('data-mode')); });
  }

  el('pg-example').addEventListener('change', function () {
    if (this.value === '') return;
    var p = this.value.split('-');
    var item = planOf(state.mode)[+p[0]].items[+p[1]];
    if (!item) return;
    ta.value = item.code;
    var sd = el('pg-stdin');
    if (sd) sd.value = item.stdin || '';
    state.cursor = 0;
    fitCode(); saveCode(); syncStep(); clearTerm(); focusTerm();
  });

  el('pg-run').addEventListener('click', runAll);
  el('pg-step').addEventListener('click', stepOnce);
  el('pg-clear').addEventListener('click', clearTerm);
  el('pg-reset').addEventListener('click', resetEnv);

  // 终端/解释器自带的「重置」按钮：换成练习场的重置语义（连文件系统一起重置）
  [['pg-term', resetEnv], ['pg-tcl', resetEnv]].forEach(function (pair) {
    var box = el(pair[0]);
    if (!box) return;
    var old = box.querySelector('.sbx-rst');
    if (!old) return;
    var fresh = old.cloneNode(true);
    old.parentNode.replaceChild(fresh, old);
    fresh.addEventListener('click', pair[1]);
  });

  ta.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); runAll(); }
    if (e.key === 'Tab') {
      e.preventDefault();
      var s = ta.selectionStart;
      ta.value = ta.value.slice(0, s) + '    ' + ta.value.slice(ta.selectionEnd);
      ta.selectionStart = ta.selectionEnd = s + 4;
    }
  });
  ta.addEventListener('input', function () { saveCode(); state.cursor = 0; syncStep(); fitCode(); });

  var sd = el('pg-stdin');
  if (sd) sd.addEventListener('input', function () { state.cursor = 0; syncStep(); });

  setMode('linux', false);
  var repl = tclRepl();
  if (repl) repl.print('—— 这里可以直接敲 Tcl 命令，一行一执行 ——', 'dim');
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
}
})();
