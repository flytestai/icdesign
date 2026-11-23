/**
 * playground.js — /playground/ 代码练习场
 * 两种模式：Linux 命令（MiniShell 模拟终端） / Tcl 代码（内置解释器）
 * 练习内容严格按课程顺序组织：Linux 第 2-6 课 → Tcl 第 1-10 讲
 */
(function () {
'use strict';

/* ================================================================
 * 一、练习内容（按课程顺序）
 * ================================================================ */
var LINUX_PLAN = [
  { group: 'Linux 第 2 课 · 连接服务器与目录结构', items: [
    { name: '我是谁、我在哪（whoami / pwd / hostname / echo $HOME）', code:
'# 登录后第一件事：确认身份和位置\n' +
'whoami\n' +
'pwd\n' +
'hostname\n' +
'echo $HOME' },
    { name: '逛一逛系统目录（cd / → ls → /etc）', code:
'# / 根目录：所有文件都挂在它下面\n' +
'cd /\n' +
'ls\n' +
'cd /etc\n' +
'ls | head -8          # /etc 放的是配置文件\n' +
'cd ~                  # cd ~ 或直接 cd 都回家' },
    { name: '来去自如（cd - 回到上一次的目录）', code:
'cd /tmp\n' +
'pwd\n' +
'cd -                  # 回到上一次的目录\n' +
'pwd\n' +
'cd ~/backend_lab\n' +
'pwd' }
  ]},

  { group: 'Linux 第 3 课 · 目录与文件操作', items: [
    { name: 'ls 全家桶（-l -a -h -t 和 tree）', code:
'cd ~\n' +
'ls                    # 当前目录有什么\n' +
'ls -l                 # 详细信息（简写 ll）\n' +
'ls -a                 # 连隐藏文件一起（.bashrc）\n' +
'ls -lh                # 大小换算成 K/M/G\n' +
'ls -t                 # 按修改时间排序\n' +
'tree backend_lab      # 看目录层级' },
    { name: 'mkdir 建目录链 + 练习一（PT 目录全套）', code:
'cd ~\n' +
'rm -rf PT                       # 存在就先删掉，保证从头练\n' +
'mkdir -p PT/P1 PT/D2 PT/K3      # -p 按层级创建\n' +
'mkdir PT/K3/P4\n' +
'touch PT/P1/txt1 PT/D2/txt2     # 同时建多个文件\n' +
'touch PT/asd111 PT/qwe222 PT/zxc333 PT/asd444 PT/asd555\n' +
'mkdir PT/poi111 PT/lkjs222 PT/mnb333 PT/psaik61\n' +
'ls PT' },
    { name: '通配符筛选 + 批量删除（练习一 14-18 题）', code:
'cd ~/PT\n' +
'ls p*                 # p 开头\n' +
'ls *222               # 222 结尾\n' +
'ls asd*               # asd 开头\n' +
'rm -f mnb333          # 删 m 开头的\n' +
'rm -f *asd*           # 删包含 asd 的\n' +
'ls                    # 看看剩下的' }
  ]},

  { group: 'Linux 第 4 课 · 查看与编辑文件', items: [
    { name: '五种查看方式（cat / head / tail / wc / nl）', code:
'cd ~/backend_lab/soc/dc\n' +
'cat soc.sdc           # 整个文件打出来\n' +
'head -3 soc.sdc       # 前 3 行（默认 10 行）\n' +
'tail -2 soc.sdc       # 后 2 行\n' +
'wc -l dc.log          # 数行数\n' +
'nl soc.sdc | head -4  # 带行号看' },
    { name: '重定向 > 与管道 |（history 写文件）', code:
'cd ~\n' +
'history > my_hist.txt         # 把历史命令写进文件\n' +
'nl my_hist.txt | head -5      # 带行号看前 5 行\n' +
'ls -l | wc -l                 # 管道：ls 的结果交给 wc 数行\n' +
'cd ~/backend_lab/soc/pnr/reports\n' +
'cat timing.rpt | grep -n slack' },
    { name: '找文件（find / du / which）', code:
'cd ~\n' +
'find . -name "*.tcl"          # 全目录找 tcl 脚本\n' +
'find backend_lab -type d      # 只找目录\n' +
'du -sh backend_lab            # 看目录占多大\n' +
'which ls                      # 命令装在哪' }
  ]},

  { group: 'Linux 第 5 课 · 搜索、权限与正则表达式', items: [
    { name: 'grep 基础四连（-n / -c / -i / -v）', code:
'cd ~/backend_lab/soc/pnr/reports\n' +
'grep -n slack timing.rpt          # 带行号\n' +
'grep -c slack timing.rpt          # 只数命中行数\n' +
'grep -i warning ../dc/dc.log      # 忽略大小写\n' +
'grep -v "^#" paths.rpt            # 排除 # 开头的注释行' },
    { name: '权限 chmod（数字法与目录 644/755）', code:
'cd ~\n' +
'touch secret.txt\n' +
'ls -l secret.txt\n' +
'chmod 600 secret.txt    # rw------- 只有自己能读写\n' +
'ls -l secret.txt\n' +
'chmod 755 secret.txt    # rwxr-xr-x 所有人可执行\n' +
'ls -l secret.txt\n' +
'rm -f secret.txt' },
    { name: '复制 / 移动 / 排序去重 / 扩展正则', code:
'cd ~\n' +
'cp notes.txt notes.bak        # 复制\n' +
'mv notes.bak notes_copy.txt   # 移动即重命名\n' +
'ls *.txt\n' +
'cd ~/backend_lab/soc/pnr/reports\n' +
'grep -E "slack|VIOLATED" timing.rpt | head -3   # 扩展正则：或\n' +
'sort paths.rpt | head -4      # 排序\n' +
'cut -d" " -f1 paths.rpt | sort -u | head -4     # 取第一列去重' }
  ]},

  { group: 'Linux 第 6 课 · 文本三剑客 sed / awk', items: [
    { name: 'sed 打印指定行 + 全局替换', code:
'cd ~/backend_lab/soc/pnr/reports\n' +
'sed -n "1,4p" drc.rpt          # 打印 1-4 行\n' +
'sed -n "2p" paths.rpt          # 只打印第 2 行\n' +
'sed "s/u_core/CORE/g" paths.rpt | head -3   # 全局替换' },
    { name: 'awk 取列（$1 / $NF / NR 条件）', code:
'cd ~/backend_lab/soc/pnr/reports\n' +
'awk "{print $1}" drc.rpt | head -4\n' +
'awk "{print $1, $2}" paths.rpt | head -4     # 第 1、2 列\n' +
'awk "NR==2{print $0}" drc.rpt                # 只打印第 2 行\n' +
'awk "{print $NF}" paths.rpt | head -4        # 最后一列' },
    { name: '综合实战：grep → awk → sort 一条链', code:
'# 工作里最典型的套路：过滤 → 取列 → 排序\n' +
'cd ~/backend_lab/soc/pnr/reports\n' +
'grep -v "^#" paths.rpt | awk "{print $1, $2}" | sort | head -5' }
  ]}
];

var TCL_PLAN = [
  { group: 'Tcl 第 1 讲 · 开工准备：环境与第一个命令', items: [
    { name: '第一个 Tcl 脚本：puts 输出', code:
'# puts 就是 Tcl 的"打印"\n' +
'puts "Hello, TCL!"\n' +
'puts "这是我的第一条 Tcl 命令"\n' +
'\n' +
'# 分号可以分隔同一行的多条命令\n' +
'puts "第一句"; puts "第二句"' }
  ]},
  { group: 'Tcl 第 2 讲 · 变量与替换规则', items: [
    { name: '变量、$替换、${} 与 dict', code:
'puts "Hello, TCL!"\n' +
'set name "Zhang San"   ;# 字符串变量\n' +
'set age 25             ;# 数值变量\n' +
'set score 98.5         ;# 浮点型变量\n' +
'puts "姓名：$name，年龄：$age，成绩：$score"\n' +
'\n' +
'set a.1 100\n' +
'puts ${a.1}            ;# 特殊变量名要用 ${} 包裹\n' +
'\n' +
'set info {age 20 name zhangsan}\n' +
'puts [dict get $info age]' }
  ]},
  { group: 'Tcl 第 3 讲 · 三剑客 append / incr / expr', items: [
    { name: 'append / incr / expr 运算', code:
'set str "Hello"\n' +
'append str " " "World" "!"\n' +
'puts $str\n' +
'\n' +
'set num1 10\n' +
'incr num1      ;# +1\n' +
'incr num1 5    ;# +5\n' +
'incr num1 -3   ;# -3\n' +
'puts "num1最终值：$num1"\n' +
'\n' +
'set a 3\n' +
'set b 5\n' +
'puts [expr {$b / $a}]    ;# 整数除法：5/3=1\n' +
'puts [expr {5.0 / $a}]   ;# 浮点除法' }
  ]},
  { group: 'Tcl 第 4 讲 · 数组（键-值对）', items: [
    { name: '数组定义、遍历、删除', code:
'set student(001) "Xiao Ming"\n' +
'set student(002) "Xiao Fang"\n' +
'set student(class) "三年级2班"\n' +
'puts "学号001：$student(001)"\n' +
'\n' +
'array set product {id001 手机 id002 电脑 id003 平板}\n' +
'foreach key [array names product] {\n' +
'    puts "产品$key：$product($key)"\n' +
'}\n' +
'foreach {k v} [array get product] {\n' +
'    puts "key=$k val=$v"\n' +
'}\n' +
'unset product(id002)\n' +
'puts "还剩 [array size product] 个产品：[array get product]"' }
  ]},
  { group: 'Tcl 第 5 讲 · 列表（上）：定义与读取', items: [
    { name: 'list / lindex / llength / lappend', code:
'set num_list [list 1 2 3 4 5]\n' +
'puts "列表：$num_list"\n' +
'puts "第3个元素：[lindex $num_list 2]，长度：[llength $num_list]"\n' +
'\n' +
'lappend num_list 6 7        ;# 修改源数据\n' +
'puts "lappend 后：$num_list"\n' +
'\n' +
'set class_list {\n' +
'    {001 "Xiao Ming" 95}\n' +
'    {002 "Xiao Fang" 92}\n' +
'}\n' +
'puts "嵌套取值：[lindex $class_list 1 1]"' }
  ]},
  { group: 'Tcl 第 6 讲 · 列表（下）：增删改查、排序与转换', items: [
    { name: 'lreplace / lsearch / lsort / concat / split / join', code:
'set num_list {1 2 3 4 5}\n' +
'set new_list [lreplace $num_list 1 2 apple]  ;# 不改源数据\n' +
'puts "lreplace 后新列表：$new_list"\n' +
'puts "源列表没变：$num_list"\n' +
'\n' +
'puts "找到 3 的索引：[lsearch $num_list 3]"\n' +
'puts "数字排序：[lsort -integer {10 9 2 100}]"\n' +
'puts "字符串排序：[lsort {10 9 2 100}]  ;# 字典序陷阱！"\n' +
'puts "拼接：[concat {1 2} {3 4}]"\n' +
'puts "split：[split "woaixuexi" x]  join：[join {a b c} -]"' }
  ]},
  { group: 'Tcl 第 7 讲 · 流程控制（上）：if 与用户输入', items: [
    { name: 'if 条件判断 + gets 输入（先在右侧 stdin 写 85）', code:
'puts "Please enter the score："\n' +
'gets stdin score\n' +
'if {$score >= 90} {\n' +
'    puts "成绩等级：A（优秀）"\n' +
'} elseif {$score >= 80} {\n' +
'    puts "成绩等级：B（良好）"\n' +
'} elseif {$score >= 60} {\n' +
'    puts "成绩等级：C（及格）"\n' +
'} else {\n' +
'    puts "成绩等级：D（不及格）"\n' +
'}\n' +
'puts "再来个随机数：[expr {rand()}]"' }
  ]},
  { group: 'Tcl 第 8 讲 · 流程控制（下）：三种循环', items: [
    { name: 'while / foreach / for 三种循环', code:
'# while 三要素：初始化→判断→更新\n' +
'set i 0\n' +
'while {$i < 5} {\n' +
'    puts "i = $i"\n' +
'    incr i\n' +
'}\n' +
'\n' +
'# 倒序复制列表\n' +
'set source_list {100 200 300 400 500}\n' +
'set target_list ""\n' +
'set i [expr {[llength $source_list] - 1}]\n' +
'while {$i >= 0} {\n' +
'    lappend target_list [lindex $source_list $i]\n' +
'    incr i -1\n' +
'}\n' +
'puts "倒序列表：$target_list"\n' +
'\n' +
'# foreach 求和 / for 计数\n' +
'set num_list {1 2 3 4 5}\n' +
'set sum 0\n' +
'foreach num $num_list {\n' +
'    set sum [expr {$sum + $num}]\n' +
'}\n' +
'puts "列表元素总和：$sum"\n' +
'\n' +
'for {set j 0} {$j < 3} {incr j} {\n' +
'    puts "for 第 $j 轮"\n' +
'}' }
  ]},
  { group: 'Tcl 第 9 讲 · 定义 / 使用函数 proc', items: [
    { name: 'proc 定义、默认参数、args、global', code:
'proc sayHello {} {\n' +
'    puts "Hello, Tcl!"\n' +
'}\n' +
'sayHello\n' +
'\n' +
'proc add {a b} {\n' +
'    return [expr {$a + $b}]\n' +
'}\n' +
'puts "10 + 20 = [add 10 20]"\n' +
'\n' +
'proc addDefault {a {b 5}} {\n' +
'    return [expr {$a + $b}]\n' +
'}\n' +
'puts "[addDefault 3]  /  [addDefault 3 7]"\n' +
'\n' +
'proc sumAll {args} {\n' +
'    set total 0\n' +
'    foreach num $args {\n' +
'        set total [expr {$total + $num}]\n' +
'    }\n' +
'    return $total\n' +
'}\n' +
'puts "sumAll 1..5 = [sumAll 1 2 3 4 5]"\n' +
'\n' +
'set globalVal 100\n' +
'proc testGlobal {} {\n' +
'    global globalVal\n' +
'    set localVal 200\n' +
'    puts "全局 $globalVal / 局部 $localVal"\n' +
'}\n' +
'testGlobal' }
  ]},
  { group: 'Tcl 第 10 讲 · 综合实战', items: [
    { name: 'EDA 风格综合：批量处理内存单元', code:
'# 模拟版图工具里批量处理内存单元\n' +
'set mem_list {\n' +
'    I_CONTEXT_MEM/I_CONTEXT_RAM_0_4\n' +
'    I_CONTEXT_MEM/I_CONTEXT_RAM_0_3\n' +
'    I_CONTEXT_MEM/I_CONTEXT_RAM_0_2\n' +
'}\n' +
'proc report {mem idx total} {\n' +
'    puts "进度：$idx / $total —— 正在处理：$mem"\n' +
'}\n' +
'set total [llength $mem_list]\n' +
'set idx 0\n' +
'foreach mem $mem_list {\n' +
'    incr idx\n' +
'    report $mem $idx $total\n' +
'    puts "  change_selection [get_cells $mem]"   ;# 工具命令这里用 puts 模拟\n' +
'    puts "  move_objects -delta {-50 0}"\n' +
'}\n' +
'puts "全部 $total 个单元处理完毕"' },
    { name: '猜数字游戏（把 3 次猜测写进右侧 stdin）', code:
'set answer [expr {int(rand()*100)}]\n' +
'set times 0\n' +
'while {1} {\n' +
'    incr times\n' +
'    puts "第 $times 次猜：请输入 0-99 的数字"\n' +
'    gets stdin guess\n' +
'    if {$guess == $answer} {\n' +
'        puts "猜对了！答案是 $answer"\n' +
'        break\n' +
'    } elseif {$guess > $answer} {\n' +
'        puts "大了"\n' +
'    } else {\n' +
'        puts "小了"\n' +
'    }\n' +
'}' }
  ]}
];

/* ================================================================
 * 二、UI 与运行
 * ================================================================ */
var state = { mode: 'linux' };

function el(id) { return document.getElementById(id); }

function escHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function clearOut() { var o = el('pg-out'); if (o) o.innerHTML = ''; }

function line(text, cls) {
  var out = el('pg-out');
  var d = document.createElement('div');
  d.className = 'sbx-l' + (cls ? ' ' + cls : '');
  d.innerHTML = escHtml(text) || '&nbsp;';
  out.appendChild(d);
  out.scrollTop = out.scrollHeight;
}

function planOf(mode) { return mode === 'linux' ? LINUX_PLAN : TCL_PLAN; }

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

function storeKey() { return 'pg_code_' + state.mode; }

function saveCode() {
  try { localStorage.setItem(storeKey(), el('pg-code').value); } catch (e) {}
}

function loadCode() {
  var def = planOf(state.mode)[0].items[0].code;
  try {
    var s = localStorage.getItem(storeKey());
    el('pg-code').value = s || def;
  } catch (e) { el('pg-code').value = def; }
}

function runLinux(code) {
  if (typeof MiniShell === 'undefined') { line('% 终端组件未加载，请刷新页面', 'err'); return; }
  var sh = new MiniShell.Shell(null, 'basic');   // 每次运行都是全新终端
  var lines = code.split('\n');
  line('% 新终端 · 从 ~ 开始（每次运行都重置环境，放心 rm -rf）', 'dim');
  for (var i = 0; i < lines.length; i++) {
    var raw = lines[i];
    var t = raw.trim();
    if (!t) continue;
    if (t.charAt(0) === '#') { line(t, 'cmt'); continue; }
    if (t === 'clear') { continue; }
    line(sh.ps1() + ' ' + t, 'cmd');
    var out = sh.run(t);
    if (out) line(out.replace(/\n$/, ''));
  }
  line('% 运行结束（提示符里的 ~ 是家目录 /home/autumn）', 'dim');
}

function runTcl(code) {
  if (typeof TclKit === 'undefined') { line('% Tcl 解释器未加载，请刷新页面', 'err'); return; }
  var ip = new TclKit.Interp();
  var stdinEl = el('pg-stdin');
  ip.stdin = (stdinEl.value || '').split('\n').filter(function (x) { return x !== ''; });
  var con = new TclKit.Console(el('pg-out'), ip);
  con.print('% tclsh 运行开始', 'dim');
  con.runScript(code);
  if (ip.stdin && ip.stdin.length) con.print('% stdin 还有 ' + ip.stdin.length + ' 行没被读走（gets stdin 没用到？）', 'dim');
  con.print('% 运行结束', 'dim');
}

function run() {
  clearOut();
  var code = el('pg-code').value;
  if (state.mode === 'linux') runLinux(code);
  else runTcl(code);
  saveCode();
}

function setMode(mode) {
  state.mode = mode;
  var btns = document.querySelectorAll('.pg-mode');
  for (var i = 0; i < btns.length; i++) {
    btns[i].className = 'pg-mode' + (btns[i].getAttribute('data-mode') === mode ? ' on' : '');
  }
  el('pg-eh').textContent = mode === 'linux'
    ? 'Linux 命令（一行一条，按顺序执行；# 开头是注释）'
    : 'Tcl 代码（可多行；Ctrl+Enter 运行）';
  el('pg-stdin-box').style.display = mode === 'tcl' ? '' : 'none';
  el('pg-note').innerHTML = mode === 'linux'
    ? 'Linux 练习跑在浏览器内置的模拟终端里：<b>每次点运行都是一个全新环境</b>（家目录 /home/autumn，里面有 backend_lab、pdk、logs 等真实项目结构），所以可以放心练 rm -rf。支持的命令：ls·cd·pwd·mkdir·touch·rm·cp·mv·cat·head·tail·wc·nl·grep·sed·awk·sort·uniq·cut·find·du·chmod·tree·which·history·echo·管道与重定向。tar / ln / md5sum 这类需要真实文件系统的命令，请在课程页的练习终端或真机上练。'
    : 'Tcl 解释器覆盖课程全部命令：set·puts·expr·incr·append·unset·array(set/get/names/size)·dict get·list/lindex/llength/lappend/lreplace/lsearch/lsort/concat/split/join·if·while·foreach·for·break·continue·proc（含默认参数与 args）·global·return·gets stdin·rand()。需要用户输入时，先在右侧 stdin 框里预写好，一行一个值。';
  buildSelect();
  loadCode();
  clearOut();
}

function mount() {
  var codeEl = el('pg-code');
  if (!codeEl) return;

  var btns = document.querySelectorAll('.pg-mode');
  for (var i = 0; i < btns.length; i++) {
    btns[i].addEventListener('click', function () {
      setMode(this.getAttribute('data-mode'));
    });
  }
  el('pg-example').addEventListener('change', function () {
    if (this.value === '') return;
    var p = this.value.split('-');
    var item = planOf(state.mode)[+p[0]].items[+p[1]];
    if (item) { codeEl.value = item.code; clearOut(); saveCode(); }
  });
  el('pg-run').addEventListener('click', run);
  el('pg-clear').addEventListener('click', clearOut);
  el('pg-reset').addEventListener('click', function () {
    codeEl.value = planOf(state.mode)[0].items[0].code;
    var sd = el('pg-stdin'); if (sd) sd.value = '';
    try { localStorage.removeItem(storeKey()); } catch (e) {}
    clearOut();
  });
  codeEl.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); run(); }
    if (e.key === 'Tab') {
      e.preventDefault();
      var s = codeEl.selectionStart;
      codeEl.value = codeEl.value.slice(0, s) + '    ' + codeEl.value.slice(codeEl.selectionEnd);
      codeEl.selectionStart = codeEl.selectionEnd = s + 4;
    }
  });
  codeEl.addEventListener('input', saveCode);

  setMode('linux');
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
}
})();
