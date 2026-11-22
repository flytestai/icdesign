# -*- coding: utf-8 -*-
"""终端类配图：真实会话的「界面照」。零基础最先卡住的地方都是这里。"""

from figs.style import page

FIGS = []
MONO = '"Cascadia Mono",Consolas,"Courier New",monospace'
FONT = '"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif'

# 行类型：c=命令行  o=普通输出  g=绿色（成功）  y=黄色（警告）  r=红色（错误）
#        d=灰色（注释）  b=蓝色（高亮）  t=标题


def term(title, lines, w=1000, h=None, sub="bash", fg="#cfdcea"):
    h = h or (52 + 19 * len(lines))
    body = []
    y = 20
    for kind, t in lines:
        col = {"c": "#eaf2fa", "o": "#a9bed2", "g": "#7fd6a3", "y": "#e6b455",
               "r": "#ef8b84", "d": "#5f7d99", "b": "#7cb8e8", "t": "#ffffff"}[kind]
        weight = "600" if kind == "t" else "400"
        body.append(f'<text x="16" y="{y + 14}" font-family={MONO!r} font-size="12.5" fill="{col}" '
                    f'font-weight="{weight}" xml:space="preserve">{t}</text>')
        y += 19
    inner = "".join(body)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
           f'<rect width="{w}" height="{h}" rx="8" fill="#0f1a26"/>'
           f'<rect width="{w}" height="30" rx="8" fill="#1b2b3a"/>'
           f'<rect y="22" width="{w}" height="8" fill="#1b2b3a"/>'
           f'<circle cx="18" cy="15" r="4.2" fill="#e0847c"/><circle cx="32" cy="15" r="4.2" fill="#e0b45c"/>'
           f'<circle cx="46" cy="15" r="4.2" fill="#7cc98d"/>'
           f'<text x="{w / 2}" y="19" text-anchor="middle" font-family={FONT!r} font-size="11.5" '
           f'fill="#8fa6bc">{title}</text>'
           f'<text x="{w - 14}" y="19" text-anchor="end" font-family={MONO!r} font-size="10.5" fill="#5f7d99">{sub}</text>'
           f'<g>{inner}</g></svg>')
    return f'<div style="padding:14px;background:#fff">{svg}</div>'


def add(fid, caption, html, w=1000, h=0):
    FIGS.append((fid, w, h or 200, page(html), caption))


# 每张图的实际高度由 term() 算出，这里统一在收集时回填
_PENDING = []


def sess(fid, w, caption, lines, sub="bash"):
    _PENDING.append((fid, w, caption, lines, sub))


# ---------------------------------------------------------------- 定义全部会话
sess("term-login", 960, "第一次登录服务器。注意提示符从「本机」变成「服务器」——之后所有命令都跑在远端的 Linux 上，不是你自己的电脑。",
     [("c", "$ ssh weizhen@132.226.110.78"),
      ("o", "weizhen@132.226.110.78's password: "),
      ("o", "Last login: Mon Nov 16 09:12:04 2026 from 10.8.4.21"),
      ("o", "=================================================================="),
      ("b", "  项目库目录：/home/weizhen/backend_lab/soc"),
      ("b", "  工具已配好：module load innovus / pt / calibre"),
      ("o", "=================================================================="),
      ("c", "weizhen@srv01:~$ pwd"),
      ("o", "/home/weizhen"),
      ("c", "weizhen@srv01:~$ ls"),
      ("o", "backend_lab  logs  notes.txt  run.sh"),
      ("d", "# 提示符里的 srv01 说明你现在在服务器上；掉线后重连会回到 ~ 目录")],
     sub="ssh")

sess("term-ls", 960, "ls -l 的输出怎么读。第一列那串 rwxr-xr-x 是权限，后面依次是链接数、属主、属组、大小、时间、文件名。看不清这一列，就解释不了「为什么脚本跑不了」。",
     [("c", "weizhen@srv01:~/backend_lab$ ls -l"),
      ("o", "total 28"),
      ("o", "drwxr-xr-x  4 weizhen  staff   4096 Nov 16 09:20 soc"),
      ("o", "-rw-r--r--  1 weizhen  staff   1821 Nov 15 22:04 run.sh"),
      ("o", "-rwxr-xr-x  1 weizhen  staff    612 Nov 15 21:58 clean.sh"),
      ("o", "lrwxrwxrwx  1 weizhen  staff     24 Nov 14 10:11 pdk -> /opt/pdk/nangate45"),
      ("d", "# d=目录  -=普通文件  l=软链接"),
      ("d", "# rwxr-xr-x = 属主可读写执行 / 同组可读执行 / 其他可读执行"),
      ("c", "weizhen@srv01:~/backend_lab$ ls -lh soc"),
      ("o", "total 1.2G"),
      ("o", "drwxr-xr-x  2 weizhen staff 4.0K Nov 16 09:20 dc"),
      ("o", "drwxr-xr-x  2 weizhen staff 4.0K Nov 16 09:20 pnr"),
      ("o", "-rw-r--r--  1 weizhen staff 1.2G Nov 16 08:41 soc_top.enc.dat"),
      ("d", "# -h 把字节换成人能读的 K/M/G，看大文件必备")],
     sub="bash")

sess("term-cd", 960, "绝对路径和相对路径的区别。以 / 开头的是绝对路径（从根开始），以名字开头的是相对路径（从当前位置开始），~ 永远代表你的家目录。",
     [("c", "weizhen@srv01:~$ cd backend_lab/soc"),
      ("c", "weizhen@srv01:~/backend_lab/soc$ pwd"),
      ("o", "/home/weizhen/backend_lab/soc"),
      ("c", "weizhen@srv01:~/backend_lab/soc$ cd .."),
      ("c", "weizhen@srv01:~/backend_lab$ cd /opt/pdk"),
      ("o", "bash: cd: /opt/pdk: Permission denied"),
      ("d", "# 权限不够 —— 别人的目录你只能看，不能进"),
      ("c", "weizhen@srv01:~/backend_lab$ cd"),
      ("c", "weizhen@srv01:~$ cd -"),
      ("o", "/home/weizhen/backend_lab"),
      ("d", "# 只敲 cd = 回家目录；cd - = 回到上一个目录（来回切换神器）")],
     sub="bash")

sess("term-redirect", 960, "重定向与管道。> 是「覆盖写入文件」，>> 是「追加」，| 是「把上一条命令的输出当成下一条的输入」。这三样组合起来，就是日志分析和报告筛选的全部基础。",
     [("c", "weizhen@srv01:~/pnr$ dc_shell -f run.tcl > dc.log 2>&1"),
      ("d", "# > dc.log 把正常输出写进文件；2>&1 把错误也并进同一个文件"),
      ("c", "weizhen@srv01:~/pnr$ grep -c \"Error\" dc.log"),
      ("o", "3"),
      ("c", "weizhen@srv01:~/pnr$ grep \"Error\" dc.log >> issues.txt"),
      ("d", "# >> 追加：不清空已有内容，适合「每天往里加一条」"),
      ("c", "weizhen@srv01:~/pnr$ cat timing.rpt | grep -E \"slack\" | sort -n | head -3"),
      ("o", "  slack (VIOLATED)            -0.412"),
      ("o", "  slack (VIOLATED)            -0.318"),
      ("o", "  slack (VIOLATED)            -0.207"),
      ("d", "# 管道把三条命令串成流水线：捞行 → 排序 → 取前三")],
     sub="bash")

sess("term-grep", 960, "在几十万行的报告里找东西：grep 捞行、sed 替换、awk 取列。下面这一行命令，是从 timing.rpt 里捞出「最差的那条路径的 slack」的完整写法。",
     [("c", "weizhen@srv01:~/pnr$ grep -n \"slack (VIOLATED)\" timing.rpt | head -2"),
      ("o", "1421:  slack (VIOLATED)            -0.412"),
      ("o", "1489:  slack (VIOLATED)            -0.318"),
      ("c", "weizhen@srv01:~/pnr$ awk '/slack \\(VIOLATED\\)/{print $NF}' timing.rpt | sort -n | head -1"),
      ("o", "-0.412"),
      ("d", "# $NF = 每一行的最后一列；sort -n 按数值排序；head -1 取最小"),
      ("c", "weizhen@srv01:~/pnr$ sed -n '1418,1424p' timing.rpt"),
      ("o", "  data required time            2.3117"),
      ("o", "  data arrival time            -2.7237"),
      ("o", "  ------------------------------------------"),
      ("o", "  slack (VIOLATED)            -0.412"),
      ("d", "# sed -n 'a,bp' = 只打印第 a 到 b 行，看上下文最快")],
     sub="bash")

sess("term-ps", 960, "进程与后台任务。跑综合要好几个小时，关掉终端就死掉是最常见的翻车——正确做法是 nohup 或 screen。",
     [("c", "weizhen@srv01:~/pnr$ ps -ef | grep innovus | grep -v grep"),
      ("o", "weizhen  31842  31840 98 09:20 pts/3  04:12:31 innovus -files run.tcl"),
      ("d", "# 第 2 列是 PID=31842；98 是 CPU 占用"),
      ("c", "weizhen@srv01:~/pnr$ kill -9 31842"),
      ("d", "# -9 强杀（进程不响应普通 kill 时才用）；先试 kill -15 让它自己收尾"),
      ("c", "weizhen@srv01:~/pnr$ nohup innovus -files run.tcl > run.log 2>&1 &"),
      ("o", "[1] 32117"),
      ("d", "# nohup + & ：关掉终端也不死，输出进 run.log，[1] 是任务号"),
      ("c", "weizhen@srv01:~/pnr$ jobs"),
      ("o", "[1]+  Running                 nohup innovus -files run.tcl > run.log 2>&1 &")],
     sub="bash")

sess("term-module", 960, "module load 是芯片公司的标配：同一个人可能同时跑三个项目，各要不同版本的工具。module 就是「切环境变量」的开关。",
     [("c", "weizhen@srv01:~/pnr$ which innovus"),
      ("o", "/usr/bin/which: no innovus in (/usr/local/bin:/usr/bin:/bin)"),
      ("r", "bash: innovus: command not found"),
      ("d", "# 工具装了，但没进 PATH —— 所以「找不到命令」不一定是没装"),
      ("c", "weizhen@srv01:~/pnr$ module avail"),
      ("o", "innovus/21.10  innovus/21.15  pt/2022.03  calibre/2023.2"),
      ("c", "weizhen@srv01:~/pnr$ module load innovus/21.15"),
      ("c", "weizhen@srv01:~/pnr$ which innovus"),
      ("o", "/opt/eda/innovus/21.15/bin/innovus"),
      ("g", "OK：PATH 已被 module 改好"),
      ("c", "weizhen@srv01:~/pnr$ module list"),
      ("o", "Currently Loaded Modulefiles:"),
      ("o", "  1) innovus/21.15")],
     sub="bash")

sess("term-tcsh", 960, "tcsh 在公司里很常见（历史原因）。它和 bash 最大的差别是：设环境变量用 setenv，设本地变量用 set，两者不能混。",
     [("c", "[weizhen@srv01 ~]% setenv PROJECT soc_top"),
      ("c", "[weizhen@srv01 ~]% echo $PROJECT"),
      ("o", "soc_top"),
      ("c", "[weizhen@srv01 ~]% set n = 3"),
      ("c", "[weizhen@srv01 ~]% echo $n"),
      ("o", "3"),
      ("d", "# setenv = 环境变量（子进程可见）；set = shell 变量（只在当前 shell）"),
      ("c", "[weizhen@srv01 ~]% set path = ($path /opt/eda/bin)"),
      ("d", "# tcsh 的 PATH 是一个数组，追加要写 ($path 新目录)，不是 PATH=$PATH:..."),
      ("c", "[weizhen@srv01 ~]% foreach f (dc pnr rtl)"),
      ("c", "[weizhen@srv01 ~]?   echo \"处理 $f\" ./$f"),
      ("c", "[weizhen@srv01 ~]? end"),
      ("o", "处理 dc ./dc"),
      ("o", "处理 pnr ./pnr"),
      ("o", "处理 rtl ./rtl")],
     sub="tcsh")

sess("term-git", 960, "git 三个区：工作区（你改的文件）→ 暂存区（git add 之后）→ 仓库（git commit 之后）。搞清这三个区，git 就没有神秘感了。",
     [("c", "weizhen@srv01:~/pnr$ git status"),
      ("o", "On branch main"),
      ("o", "Changes not staged for commit:"),
      ("r", "        modified:   scripts/run.tcl"),
      ("o", "Untracked files:"),
      ("r", "        timing.rpt"),
      ("c", "weizhen@srv01:~/pnr$ git add scripts/run.tcl"),
      ("c", "weizhen@srv01:~/pnr$ git commit -m \"约束加了一条 clock gating check\""),
      ("o", "[main 3f9c1a2] 约束加了一条 clock gating check"),
      ("o", " 1 file changed, 2 insertions(+)"),
      ("c", "weizhen@srv01:~/pnr$ git log --oneline -3"),
      ("o", "3f9c1a2 约束加了一条 clock gating check"),
      ("o", "a71b0d4 floorplan 通道加宽到 43um"),
      ("o", "9e02f13 初始版本：能跑通到 route"),
      ("d", "# 报告文件（timing.rpt）通常不进 git，写进 .gitignore")],
     sub="git")

sess("term-make", 960, "Makefile 最常见的一行报错：missing separator。99% 的原因是把 Tab 打成了空格——这不是格式洁癖，是 make 的语法要求。",
     [("c", "weizhen@srv01:~/pnr$ cat Makefile"),
      ("o", "run:"),
      ("o", "        innovus -files run.tcl | tee logs/run_$(shell date +%Y%m%d).log"),
      ("c", "weizhen@srv01:~/pnr$ make run"),
      ("r", "Makefile:2: *** missing separator.  Stop."),
      ("d", "# 第 2 行缩进用了空格，make 要求必须是真正的 Tab"),
      ("c", "weizhen@srv01:~/pnr$ cat -A Makefile | head -2"),
      ("o", "run:$"),
      ("o", "        innovus -files run.tcl ...$"),
      ("d", "# cat -A 显示不可见字符：行首应该是 ^I（Tab），如果是空格一眼就看出来"),
      ("g", "修好之后：make run 一行跑完整套流程，日志自动带日期")],
     sub="make")

sess("term-dc", 960, "Design Compiler 综合的最小脚本。它把 RTL 变成门级网表，是后端的「原料供应商」——看懂这几行，你就知道后端拿到的 .v 是怎么来的。",
     [("c", "dc_shell -f syn.tcl | tee logs/syn.log"),
      ("o", "Information: Loading target library 'tcbn40lpbwp'..."),
      ("o", "Information: Elaborating design 'soc_top'..."),
      ("o", "Warning: Inferred latch in u_cpu/alu/result_reg (SYN-7)."),
      ("y", "# 推断出锁存器通常是代码写漏了 else，必须回头找设计确认"),
      ("o", "  Number of ports:   148"),
      ("o", "  Number of cells:  9390"),
      ("o", "  Number of nets:  12031"),
      ("g", "  Critical path slack: 0.21 (MET)"),
      ("o", "Information: Writing netlist to ./output/soc_top.v"),
      ("o", "Information: Writing SDC  to ./output/soc_top.sdc")],
     sub="dc_shell")

sess("term-tail", 960, "日志怎么盯：tail -f 实时跟，grep 只留关键行。-f 是「follow」，工具在跑的时候你就盯着这个窗口。",
     [("c", "weizhen@srv01:~/pnr$ tail -f logs/route.log"),
      ("o", "[INFO] Route stage: detail_route  (iteration 3)"),
      ("o", "[INFO] Violations: 312 -> 46"),
      ("o", "[WARN] Net u_dsp/n_1284: detour 412um (congestion)"),
      ("o", "[INFO] Violations: 46 -> 7"),
      ("o", "[INFO] Violations: 7 -> 0"),
      ("g", "[INFO] Detail route finished. Total DRC = 0"),
      ("d", "# Ctrl+C 退出 tail，不会影响正在跑的工具"),
      ("c", "weizhen@srv01:~/pnr$ grep -E \"\\[WARN\\]|\\[ERROR\\]\" logs/route.log | wc -l"),
      ("o", "19"),
      ("d", "# 收工前扫一遍 WARN：19 条里通常有 2~3 条是真问题")],
     sub="bash")

sess("term-eco", 960, "ECO 落地：PT 出改动清单 → Innovus 按清单改 + 局部重布线 → 复算签核。注意最后那行 Formality 检查，它保证「改了版图但功能没变」。",
     [("c", "pt_shell> fix_eco_timing -type hold -slack_lesser_than 0 -verbose"),
      ("o", "Information: 3 hold violations found in path group clk"),
      ("c", "pt_shell> write_changes -format icctcl -output eco_hold.tcl"),
      ("g", "Information: Wrote 3 ECO changes to eco_hold.tcl"),
      ("c", "innovus> source eco_hold.tcl"),
      ("o", "ecoChangeCell: 2 cells upsized"),
      ("o", "insertBuffer: 1 buffer inserted (BUF_X2)"),
      ("c", "innovus> legalizePlace -incremental"),
      ("c", "innovus> routeDesign -incremental"),
      ("g", "DRC = 0, 局部重布完成"),
      ("c", "innovus> write_verilog -netlist post_eco.v"),
      ("c", "fm_shell> verify"),
      ("g", "Verification SUCCEEDED: 12031 compare points matched")],
     sub="PT + Innovus")

sess("term-error", 960, "三个你会反复遇到的报错。记住「报错前半句是现象、后半句才是原因」这个规律，排查速度会快很多。",
     [("c", "innovus> read_verilog soc_top.v"),
      ("r", "Error: Cannot open file 'soc_top.v' (File not found)."),
      ("d", "# 现象=打不开；原因=路径不对。先 pwd，再看文件名大小写"),
      ("c", "pt_shell> link_design soc_top"),
      ("r", "Error: Cannot find the design 'soc_top' in the library. (LINK-5)"),
      ("d", "# 网表还没读，或顶层模块名和你想的不一样（用 list_designs 看）"),
      ("c", "innovus> read_mmmc soc_top.mmmc"),
      ("r", "**ERROR: (OPT-906): The following library is missing: slow.db"),
      ("d", "# 缺 corner 库。设计要三个 corner，你只给了 typical → 工具直接罢工"),
      ("c", "weizhen@srv01:~/pnr$ cp $PDK/lib/*.db ./lib/"),
      ("g", "补齐后重跑，通过")],
     sub="bash")


# ---- 收集（延迟到此处才拿到真实高度）----
for fid, w, cap, lines, sub in _PENDING:
    html = term("终端 — " + sub, lines, w, sub=sub)
    # 高度：54 + 19*行数 + 22
    h = 52 + 19 * len(lines) + 28
    FIGS.append((fid, w + 28, h, page(html), cap))
