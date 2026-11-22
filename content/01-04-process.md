---
id: 01-04-process
no: 05
stage: 1
title: 进程、后台任务与环境变量
en: Processes & Environment
hours: 3
minutes: 42
tags: [Linux, 进程, 信号, 后台任务, PATH, DISPLAY, 环境变量]
summary: dc_shell 为什么"command not found"、任务为什么一关终端就死、GUI 为什么起不来——这一课从进程、PID、信号讲到 &、nohup、Ctrl+Z 的区别，再到 PATH、HOME、DISPLAY 和 .bashrc 与 .cshrc 的加载时机。
---

## 程序跑起来，就成了进程 {#proc}

:::goal 学完这一课，你能在一个陌生账号上把环境配到"工具起得来"，并在任务卡住时判断该 `kill -15` 还是 `-9`、该用 `nohup` 还是该先查 `DISPLAY`。
:::

硬盘上的 `dc_shell` 是一个文件。它躺在 `/usr/Synopsys/.../bin/` 里，几万个字节，不会自己动。你敲命令回车，shell 做三件事：在 PATH 里找到这个文件、让内核把它读进内存、给它分配一个编号。做完这三步，文件才变成**进程**（Process）。

类比一下：程序是菜谱，进程是厨房里正在做这道菜的那个厨师。同一份菜谱可以同时有五个人在做（开五个 `dc_shell`），每人有自己的灶台（内存）、自己的进度（寄存器状态）、自己的工牌号。菜谱只有一份，厨师可以有五个。**程序是静态的，进程是动态的。**

| | 程序（program） | 进程（process） |
|---|---|---|
| 存在形式 | 磁盘上的文件 | 内存里的运行实例 |
| 有几个 | 一份 | 可以同时多个 |
| 有编号吗 | 没有 | 有，就是 PID |
| 会出错吗 | 不会，它不动 | 会卡死、会崩、会被杀 |

内核给每个进程至少两样东西：

- **PID（Process ID，进程号）**：一个正整数，同一时刻系统内唯一。`kill` 就是拿这个号去找到它。
- **PPID（Parent PID，父进程号）**：谁把它启起来的。你在终端敲命令，父进程就是那个 shell；shell 自己的父进程是 sshd 或终端程序。

父子这条链是后面所有问题的钥匙。终端断开时，内核会给这个终端上的进程发一个"挂断"信号，进程收到就退出——所以关掉窗口，工具跟着死。而"谁给谁发信号"取决于父子关系，`kill` 只是手动走同一条路。

```bash
# 作用：看"我自己这个终端"的进程号和它的父进程
# 用法：任意目录执行；$$ 是当前 shell 的 PID，bash 和 tcsh 都认
echo $$                          # 打印当前 shell 的 PID，比如 21437
ps -o pid,ppid,user,cmd -p $$    # 只看这一个：PID、父进程、用户、命令行
```

在课程服务器上你会看到类似这样的输出（典型值，PID 每次都不同）：

```
  PID  PPID USER   CMD
21437 21430 autumn -tcsh
```

这行读作："21437 这个 tcsh 进程，是我在 21430（sshd 派生出来的登录 shell）底下开的。" 你后面敲的每一条命令，PPID 都是 21437。

## 用 ps 看清一个进程：PID、PPID 和那几列 {#ps}

`ps` 是 process status 的缩写。最常用的是 `ps -ef`：`-e` 选所有进程，`-f` 用完整格式（多几列）。

```bash
# 作用：把系统里跑着的进程列出来，并筛出你要找的那个
# 用法：在任意目录执行；grep 的关键词换成工具名或你的用户名
ps -ef                        # 全部进程：UID PID PPID C STIME TTY TIME CMD 七列
ps -ef | grep dc_shell        # 只看综合工具还在不在跑（注意会多出一条 grep 自己）
ps -ef | grep "[d]c_shell"    # 方括号技巧：让 grep 匹配不到自己那条，输出干净
ps -u $USER                   # 只看自己的进程（不知道用户名时用 whoami 查）
ps -o pid,ppid,etime,cmd -p 21437   # 指定列：加了 etime（已运行多久）
ps --forest | head -30        # 用树形缩进显示父子关系（Linux 专有）
pstree -p 21437               # 从某个 PID 往下看整棵子进程树
```

`ps -ef` 那七列，只有五列是天天要看的：

| 列 | 含义 | 看它干什么 |
|---|---|---|
| PID | 进程号 | `kill` 要用它 |
| PPID | 父进程号 | 判断"这是谁启的"，父进程死了它可能变成 1 |
| TTY | 挂在哪个终端 | `?` 表示没有终端（后台/守护进程） |
| TIME | 累计占用 CPU 的时间 | 不是"跑了多久"，是"真正算了多久" |
| CMD | 完整命令行 | 判断是不是你要找的那个任务 |

**`TIME` 和 `STIME` 最容易看错。** `STIME` 是启动时刻，`TIME` 是累计 CPU 时间。一个进程跑了 6 小时、`TIME` 只有 12 分钟，说明它 96% 的时间在等 I/O 或等 license，不是在算——这时候你 kill 它重跑，只会浪费 6 小时。

`ps -ef | grep dc_shell` 会多出一条 `grep dc_shell`，因为 grep 自己也在跑，命令行里正好含这个词。这不是 bug，是老手都遇到过的假象。`[d]c_shell` 的写法让 grep 的命令行里出现 `[d]`，自己的模式就匹配不上自己。

:::term Process | 进程
程序被读进内存、正在运行的那一份实例。每个进程有唯一的 PID、一个父进程 PPID、一份独立的内存空间。进程死了，内存被回收，磁盘上的程序文件不受影响。
:::

:::term PID (Process ID) | 进程号
内核分配给进程的正整数编号。同一条命令跑两次，是两个不同的 PID。`kill 12345` 里的 12345 就是它。
:::

:::scene 周一早上，机器上有三个"我的"dc_shell
你上周五挂了三个综合任务，今天回来不知道哪个还活着。`ps -ef | grep dc_shell` 跳出五行，其中一行是 grep 自己，另外四行里有三行是你的、一行是隔壁组同事的（同一个公共账号）。

你需要的判断顺序是：先 `ps -o pid,ppid,etime,cmd` 看运行时长和完整命令行，确认哪个对应哪个 top；再看 `TTY` 是不是 `?`（`?` 说明当初是 nohup 挂的，不会因为断网死）；最后才决定杀谁。**先认领，再动手**——这也是下面 `kill` 那一节的前提。
:::

机器能并行跑几个任务，也要算一下，而不是"能开就开"：

- 一台 64 核、256GB 的机器，一个 PNR 任务峰值占 8GB、8 个线程。
- 按内存算：`256 ÷ 8 = 32` 个。
- 按线程算：`64 ÷ 8 = 8` 个。
- 按 license 算：这版工具有 8 个 license，你只能拿到 8 个。
- 所以并行数 = `min(32, 8, 8) = 8`。

再多开，第 9 个任务会卡在 `Waiting for license`，占着内存不干活——你在 `top` 里看到它 CPU 占用 0%，误以为是"卡死"，其实是排队。

## kill：为什么 -15 比 -9 温柔 {#kill}

`kill` 不是"杀死"，是"发信号"。信号（Signal）是内核递给进程的一张纸条，上面写着一件事。大部分信号进程可以选择"收到，我收拾一下再走"。

```bash
# 作用：给进程发信号，先礼后兵
# 用法：PID 从 ps 里查；不带 -信号 时默认发 15（TERM）
kill 21437            # 等价 kill -15：请它自己退出（TERM），能保存现场
kill -15 21437        # 同上，写全更好读
kill -9 21437         # KILL：内核直接抹掉，进程没有任何机会反应
kill -1 21437         # HUP：挂断。重载配置的老习惯（很多守护进程用它）
kill -0 21437         # 不发信号，只探活：返回 0 说明进程还在
kill -l               # 列出所有信号编号和名字
```

主要的几个信号，记住五个就够：

| 编号 | 名字 | 谁发的 | 进程能拦吗 | 用在哪 |
|---|---|---|---|---|
| 15 | TERM（terminate） | 你敲 `kill` | 能 | 正常收工，先存库再退出 |
| 9 | KILL | 你敲 `kill -9` | **不能** | 前面都不管用时的最后手段 |
| 1 | HUP（hang up） | 终端断开 | 能 | 让服务重读配置 |
| 2 | INT（interrupt） | 你按 `Ctrl+C` | 能 | 中止前台任务 |
| 20 | TSTP | 你按 `Ctrl+Z` | 能 | 挂起（注意不是结束） |

`-15` 和 `-9` 的差别，用一个数字就能说明白。

一个 PNR 任务跑了 5 小时 40 分（340 分钟），工具每 15 分钟自动 `saveDesign` 一次。你 `kill -15`，它收到信号，把当前数据库存盘再退出，你最多损失 15 分钟，重跑接着来。你 `kill -9`，它正在写 `.db` 的半路上被抹掉，文件可能是半截的，工具再打开会报 `Cannot open design`，你损失 340 分钟。

`15 ÷ 340 ≈ 4.4%` 和 `340 ÷ 340 = 100%`——**这就是"多等 10 秒"和"重跑一夜"的差别。**

:::pitfall kill -9 之后设计库打不开了
现象：`kill -9` 掉一个正在 save 的 PNR 任务，再启动工具 `restoreDesign` 报数据库损坏或直接段错误。

原因：`-9` 不给进程任何回调机会，写文件写到一半被切断，`.db`/`.enc` 是二进制格式，缺一段就是废文件。

怎么查、怎么避免：先 `kill -15`，等 30 秒，`ps` 确认真的退了，还赖着才 `-9`。已经被 `-9` 的，去看 `saveDesign` 目录里有没有带时间戳的备份（多数流程会留 `db/` 和 `db.bak/`），没有就只能从上一个检查点重跑。教训是：**跑长任务时把"自动存盘间隔"设短，比任何抢救手段都管用。**
:::

:::pitfall 杀了父进程，子进程还在
现象：`kill` 掉启动脚本，工具还在跑；或者杀掉 shell，`dc_shell` 变成孤儿（PPID 变成 1）继续吃内存。

原因：信号只发给一个 PID，不会自动传给它的子进程。父进程死了，子进程被 init（PID 1）接管，照样活着。

怎么查：`ps -ef | grep 关键词` 看 PPID 是不是 1；`pstree -p 父PID` 看整棵树。要连子进程一起收，用 `kill -- -PGID`（杀整个进程组）或者 `pkill -P 父PID`。**杀之前先看清楚树，别只杀一个头。**
:::

## 后台跑：& 和 Ctrl+Z 不是一回事 {#bg}

综合、布局布线动辄几小时。直接敲命令，一断网、一关窗口，任务跟着没。这里有三个容易混的概念：**前台、后台、挂起**。

| 状态 | 怎么进去 | 终端还能用吗 | 关掉终端会怎样 |
|---|---|---|---|
| 前台（foreground） | 直接敲命令 | 不能，被占住 | 收到 HUP，死 |
| 后台（background） | 命令末尾加 `&`，或 `bg` | 能 | 收到 HUP，死 |
| 挂起（stopped） | 按 `Ctrl+Z` | 能 | 死，而且是不往下跑的"死" |
| 脱离（disowned / nohup） | `nohup`、`disown` | 能 | 活着 |

关键结论先说：**`&` 只是"不占着终端"，不是"不怕断网"。** 两者完全不是一回事，这是新人最大的误解。

```bash
# 作用：把长任务放后台，并在断网后仍然活着
# 用法：在跑批目录执行；日志一定要重定向，否则输出会刷屏
dc_shell -f syn.tcl > syn.log 2>&1 &     # & 放后台，终端立刻还给你（断网仍会死）
jobs                                     # 看当前 shell 管着哪些后台任务（带编号 %1 %2）
jobs -l                                  # 多一列 PID，方便 kill
fg %1                                    # 把 1 号任务调回前台（Ctrl+C 才能中止它）
bg %1                                    # 把"挂起"的 1 号任务改成后台继续跑
kill %1                                  # 按作业号杀，不用记 PID

# 正确姿势：nohup + & + 重定向，三件套
nohup dc_shell -f syn.tcl > syn.log 2>&1 &   # nohup 让它忽略 HUP，断网也不死
echo $!                                  # $! 是刚放到后台那个进程的 PID，记下来
```

`Ctrl+Z` 是第三件事，别和 `Ctrl+C` 混：

- `Ctrl+C` 发 INT（2），**结束**前台任务。
- `Ctrl+Z` 发 TSTP（20），**暂停**前台任务，进程还在内存里，只是不跑了。`ps` 里状态列显示 `T`。
- 暂停之后想让它继续：`bg` 放到后台跑，或 `fg` 调回前台。

所以"我不小心按了 Ctrl+Z，任务是不是没了"——没没，它只是冻住了，`jobs` 能看到，`bg %1` 就活了。**但如果这时候你关掉终端，冻住的任务会直接被杀，而且没有任何存盘机会。**

为什么关终端会死？因为终端断开时，内核会给这个会话里所有进程发 HUP。`nohup` 的作用就是让进程**忽略**这个信号（它把 HUP 的处理方式设成"忽略"），同时如果没有重定向，它会把输出写到当前目录的 `nohup.out`。`disown -h %1` 是另一条路：不改进程，而是告诉 shell"这个作业别给它发 HUP"。

:::term Signal | 信号
内核递给进程的一个编号通知，告诉它"发生了什么"。15 是"请退出"，9 是"立刻消失"，1 是"终端断了"。进程可以为大多数信号注册处理函数，唯独 9 和 19（STOP）拦不住。
:::

:::pitfall 加了 & 就以为安全，断网后任务没了
现象：`dc_shell -f syn.tcl &` 跑了两小时，晚上回家断网，第二天来看日志停在两小时前，`ps` 里没有这个进程。

原因：`&` 只解决"终端被占用"，没解决"终端断开"。断网时 ssh 会话结束，内核给这一批进程发 HUP，工具默认收到就退。

怎么查、怎么改：看日志最后一行有没有 `Hangup` 或者干脆突然截断；`ps -ef` 里那条记录的 `TTY` 列如果是 `pts/3` 而不是 `?`，说明它绑在终端上。正确写法只有一种：`nohup cmd > log 2>&1 &`，然后 `echo $!` 把 PID 记进笔记。跑起来之后用 `ps -o pid,tty,cmd -p PID` 确认 TTY 是 `?`。
:::

:::note 一个能直接抄的启动模板
```bash
# 作用：按时间戳建目录、后台跑、把 PID 写进文件
# 用法：在项目根目录执行，把 icc2_shell 那行换成你的工具
RUN=run/$(date +%Y%m%d_%H%M)
mkdir -p $RUN && cd $RUN
nohup icc2_shell -f ../../scripts/pnr.tcl > pnr.log 2>&1 &
echo $! > pnr.pid
echo "started pid=$(cat pnr.pid) log=$PWD/pnr.log"
```
第二天回来 `tail -f pnr.log` 看进度，或者 `ps -p $(cat pnr.pid)` 看还活着没。**PID 落盘**这一步很关键：终端一关，`$!` 就没了。
:::

## PATH：为什么命令会"找不到" {#path}

你敲 `ls`，系统凭什么知道该执行哪个文件？它不看当前目录，而是读环境变量 `PATH`——一串用冒号隔开的目录，**从左到右**一个一个试，找到第一个同名可执行文件就用。

```bash
# 作用：查命令到底从哪来、当前 PATH 长什么样
# 用法：任意目录执行
echo $PATH            # 冒号分隔的目录列表，顺序就是查找顺序
which ls              # 告诉你 ls 的绝对路径：/usr/bin/ls
which -a python       # 所有同名命令（PATH 里有多份时，看清楚谁优先）
type ll               # 比 which 更准：能分辨别名、函数、内建命令
echo $SHELL           # 当前登录 shell 是 /bin/bash 还是 /bin/tcsh
```

`type` 比 `which` 可靠：`which` 只查 PATH 里的文件，查不到别名和内建命令。你 `alias ll='ls -lht'` 之后，`which ll` 会说找不到，`type ll` 会告诉你"ll 是 ls -lht 的别名"。

"命令找不到"实际有三种完全不同的原因，报错长得很像，处理方式完全不同：

**第一种：目录不在 PATH 里。** 报 `dc_shell: command not found`。这是最常见的，`echo $PATH` 里看不到工具目录。修法是 `export PATH=/工具/bin:$PATH`（写进 `.bashrc` 才永久）。

**第二种：文件在，但没有执行权限。** 报 `./run.sh: Permission denied`。这**不是**找不到，是找到了不让执行。`ls -l run.sh` 看到 `-rw-r--r--` 就说明缺 `x`，`chmod +x run.sh` 解决。

**第三种：文件在、也能执行，但第一行指的解释器不存在。** 报 `bad interpreter: No such file or directory`。脚本第一行写了 `#!/bin/bash`，但这台机器上 bash 在 `/usr/local/bin/bash`，或者你在 Windows 上编辑过、行尾多了 `\r`，内核把 `/bin/bash\r` 当成一个不存在的路径。`head -1 script.sh | cat -A` 看到 `^M$` 就是这个问题，`sed -i 's/\r$//' script.sh` 修掉。

还有一种隐蔽的：**PATH 顺序错了**。机器上装了 2019 和 2021 两个版本的 `dc_shell`，你把新版本目录加在了后面，`which dc_shell` 一直指向旧的。这种不会报错，只会让你"改了半天配置没生效"。

:::term Environment Variable | 环境变量
存在进程里的一组"键=值"，任何程序都能读到。它决定程序去哪找命令（PATH）、去哪找 license（LM_LICENSE_FILE）、去哪找动态库（LD_LIBRARY_PATH）、往哪画图（DISPLAY）。

读：`echo $变量名`。临时设：bash 用 `export 名=值`，tcsh 用 `setenv 名 值`。想永久生效要写进配置文件。
:::

:::pitfall 改了 PATH，当前终端还是找不到
现象：`vim ~/.bashrc` 里加了 `export PATH=/opt/eda/bin:$PATH`，保存了，新开终端能用，**当前这个终端**还是 `command not found`。

原因：配置文件只在"新开 shell"时被读一次。已经开着的终端不会自动重读。

怎么改：`source ~/.bashrc` 立刻生效（`source` 是在当前 shell 里执行这个文件）。另外，如果目录里**新加了**文件，bash 可能还在用缓存，`hash -r` 清一下；tcsh 里对应的命令是 `rehash`。
:::

## 环境变量里最重要的三个：HOME、PATH、DISPLAY {#three-env}

环境变量有几十个，真正会让你"工具起不来"的只有几个。先看这三个，再看两个和 license 相关的。

| 变量 | 作用 | 出问题的症状 |
|---|---|---|
| `HOME` | 你的家目录，`~` 展开成它 | 工具启动报 `Cannot write to ...`；配置读不到 |
| `PATH` | 去哪找命令 | `command not found` |
| `DISPLAY` | GUI 往哪块屏幕画 | `Can't open display`，图形界面起不来 |
| `LM_LICENSE_FILE` | 去哪找 license 服务器 | `Unable to checkout license` |
| `LD_LIBRARY_PATH` | 去哪找 `.so` 动态库 | `error while loading shared libraries` |

**HOME 为什么会影响工具。** 几乎所有 EDA 工具都会把用户配置、临时文件、缓存写到 `$HOME`：`.synopsys_pt.setup`、`.cadence/`、`innovus.cmd`、临时交换文件。家目录配额满了，或者被设成只读（有人用 `sudo` 跑过工具，把文件属主改成了 root），工具会在启动阶段报一个和"家目录"毫无关系的错，比如 `Cannot create log file`。`df -h $HOME` 和 `ls -ld $HOME` 是两个十秒能做完的检查。

**DISPLAY 为什么决定 GUI 能不能起来。** 这要理解 X11 的工作方式：它把"画图"拆成两半——你的 EDA 工具是**客户端**，只负责说"在这个坐标画个框"；真正画出来的是**X server**，跑在有显示器的那台机器上。`DISPLAY` 就是告诉客户端"把画图指令发到哪"。

格式是 `主机:显示号.屏幕号`：

- `:0` —— 本机第一块屏幕（你坐在服务器面前时）。
- `localhost:10.0` —— 通过 `ssh -X` 转发出来的虚拟屏幕。
- 空 —— 没设，所有图形程序都会报 `Can't open display`。

所以"GUI 起不来但 batch 能跑"几乎总是 DISPLAY 的问题，而不是工具装坏了。因为 batch 模式根本不画图，不需要 X server。查的顺序：

```bash
# 作用：确认图形环境通不通，三步定位
# 用法：在你要起 GUI 的那台机器上执行
echo $DISPLAY                 # 空 → 没设；:0 → 本机；localhost:10.0 → ssh 转发
xdpyinfo | head -3            # 能打印出 name of display 说明 X 通；报错说明不通
ssh -X user@server            # 重新登录时加 -X（-Y 是信任模式，公司环境一般用 -X）
```

`xdpyinfo` 报 `No protocol specified` 或 `Authorization required` 是另一类问题：X 的连接许可（xauth cookie）没带过来。通常是 `ssh -X` 登录后 `sudo` 到别的用户再起工具，cookie 丢了。

真机上还有一种"看起来是 GUI 问题"的情况：工具在启动时读 `$DISPLAY` 决定要不要开图形模式，只要变量存在（哪怕是错的 `:99`），它就走图形分支，然后卡在那里等一个永远不会来的 X server。**批量跑脚本时，把 `DISPLAY` unset 掉比设错更安全。**

```bash
# 作用：临时设置环境变量，只对当前终端有效
# 用法：在要启动工具的终端里逐条执行
export PATH=/usr/Synopsys/syn/R-2020.09-SP4/bin:$PATH   # 新目录放前面，保留原来的
export LM_LICENSE_FILE=27000@license-server             # license 服务器端口@主机
export LD_LIBRARY_PATH=/usr/Synopsys/lib/AMD.64:$LD_LIBRARY_PATH   # 补动态库路径
unset DISPLAY                                            # 批量跑时去掉图形依赖
```

`$PATH` 一定放在后面。放前面变成 `PATH=$PATH:/新目录`，系统命令优先，你的工具永远排在最后一个——如果 PATH 里有别的目录也放了同名程序，你就用不上新的。

:::scene 一次真实的排障（我们自己的环境里踩过）
装好 Library Compiler 后，`lc_shell` 能启动，但一直进降级模式：

```
LCSH-1: Cannot locate installation ...
```

第一反应是"是不是没装全"，其实不是。真实原因有两个：缺 `SYNOPSYS_LC_ROOT` 这个变量，工具不知道自己装在哪；以及引擎依赖的三个动态库（`libtbb.so.2` 等）不在 `LD_LIBRARY_PATH` 里。

补齐这两样之后立刻正常。**EDA 的"装不上"，八成是环境变量，而不是安装包。** 判断依据：报错里出现 `Cannot locate`、`Cannot find`、`shared libraries`，先查变量，别急着重装。
:::

:::sandbox proc | 试：env | grep PDK、export A=1、echo $A、ps、which ls、kill 1288
:::

## 配置文件：bash 用 .bashrc，tcsh 用 .cshrc {#rc}

每次开终端都手动 `export` 太蠢。把设置写进配置文件，开终端时自动执行。但"什么时候执行"这件事，bash 和 tcsh 的规则不一样，而且**登录 shell** 和**非登录 shell** 读的文件也不同。

bash 的规则：

| 场景 | 读哪些文件 |
|---|---|
| 登录 shell（ssh 登录、`bash -l`） | `/etc/profile` → `~/.bash_profile` →（通常里面会 source `~/.bashrc`） |
| 非登录交互 shell（在图形界面里开终端、`bash`） | `~/.bashrc` |
| 非交互（`ssh host "命令"`、跑脚本） | 默认**都不读**，只读 `$BASH_ENV` |

tcsh 的规则简单一些：**每个 tcsh 启动都读 `~/.cshrc`**（交互式、跑脚本都一样），只有登录 shell 额外读一次 `~/.login`。所以公司环境变量基本都写在 `.cshrc` 里，写一次全生效。

```bash
# 作用：bash 的配置写法；改完 source 一下立刻生效
# 用法：编辑 ~/.bashrc，追加到末尾
vim ~/.bashrc
# 末尾加：
# export PATH=/opt/tools/bin:$PATH
# export LM_LICENSE_FILE=27000@lic
source ~/.bashrc        # 在当前 shell 里重读，不用关终端
```

```csh
# 作用：tcsh 的配置写法（注意不是 export）
# 用法：编辑 ~/.cshrc，追加到末尾
vim ~/.cshrc
# 末尾加：
# setenv PATH /opt/tools/bin:$PATH
# setenv LM_LICENSE_FILE 27000@lic
source ~/.cshrc
```

:::term source | 加载（在当前 shell 里执行）
读一个脚本并**在当前 shell 里**执行它，所以脚本里设的变量会留在你当前这个终端。

不 source 直接跑（`./setup.sh`），脚本在一个子进程里执行完就没了，变量不会回来。**这是"我明明设了变量却不生效"的头号原因。**

tcsh 里 `source` 也能加载 `.cshrc`；bash 的等价写法是 `. ~/.bashrc`（一个点，后面有空格）。
:::

:::pitfall export 和 setenv 混用
bash 里写 `setenv` → `setenv: command not found`。
tcsh 里写 `export` → `export: Command not found.`。

先确认自己在哪个 shell：`echo $SHELL`。看到 `bash` 用 `export 名=值`，看到 `csh`/`tcsh` 用 `setenv 名 值`。

还有一条更隐蔽的：tcsh 里 `setenv PATH /a:/b` 一般不报错，但 tcsh 里 PATH 还对应一个小写 `path` **数组**，公司脚本统一写 `set path = ( /a $path )`。两种写法混着用，同一份路径要在两处维护，改了一处另一处没改，就会出现"终端里能用、脚本里找不到"。
:::

## 环境排查顺序：从 which 到 setup 脚本 {#debug}

环境出问题，不要东试一下西试一下。按这个顺序走，五步之内一定能定位：

```bash
# 作用：环境排障的五步，每条都能独立回答一个问题
# 用法：在新终端里从上往下执行，遇到第一个异常就停在那一步
echo $SHELL                          # ① 我在哪个 shell？决定后面用 export 还是 setenv
which dc_shell                       # ② 命令找得到吗？空 = 不在 PATH
echo $PATH | tr ':' '\n'             # ③ PATH 里到底有哪些目录（换行更好读）
ls -l $(which dc_shell)              # ④ 找到了的话，有 x 权限吗？指向真实文件吗（不是坏软链）
env | grep -i -E "synopsys|cadence|license"   # ⑤ 工具相关变量有没有、值对不对
```

五步都正常还是起不来，就去 `source` 公司的环境脚本（`setup.csh`、`project.csh`），或者 `module load` 对应版本。**公司环境九成的问题在这五步里能定位，剩下一成是 license 和磁盘。**

:::lab 动手：把工具目录加进 PATH 并验证"三种找不到"
**任务**：造一个假工具，分别复现三种失败，再让它们都能跑。

```bash
# 作用：造一个假工具，走一遍 PATH / 权限 / 解释器三种坑
# 用法：在 ~/demo 下执行（没有就先 mkdir -p ~/demo）
mkdir -p ~/demo/bin && cd ~/demo/bin

# 1. 写一个正常的脚本工具
cat > mytool <<'EOF'
#!/bin/bash
echo "mytool v1.0 running, args=$*"
EOF
chmod +x mytool

# 2. 直接敲名字 → 第一种：不在 PATH 里
mytool                      # 预期：mytool: command not found

# 3. 加进 PATH 再敲 → 成功
export PATH=$PWD:$PATH
mytool                      # 预期：mytool v1.0 running, args=

# 4. 去掉 x 权限 → 第二种：找到了但不让执行
chmod -x mytool
./mytool                    # 预期：Permission denied（不是 not found！）

# 5. 把 shebang 改错 → 第三种：解释器不存在
sed -i '1s|.*|#!/bin/bashh|' mytool
chmod +x mytool
mytool                      # 预期：bad interpreter: No such file or directory
```

**过关标准**：能说出三条报错分别对应"不在 PATH / 没 x 权限 / 解释器不存在"，并知道每条的正确修法（`export PATH` / `chmod +x` / 改 shebang）。再补一步：把 `export PATH=$PWD:$PATH` 写进 `~/.bashrc`，新开一个终端验证 `mytool` 直接可用。
:::

## 工作中怎么用：一个终端从打开到能用 {#in-work}

**谁做**：每个后端工程师自己做，新人第一天上班就要会。这不是"运维的事"——你的账号、你的 `.cshrc`、你的 PATH。

**标准流程**（进公司第一周就该形成肌肉记忆）：

1. 登录后 `echo $SHELL`，确认 shell 类型。
2. `source` 项目环境脚本，或者 `module load` 工具版本。
3. `which dc_shell` 验证工具能找到。
4. `echo $LM_LICENSE_FILE` 验证 license 指向对。
5. 再跑一次 `dc_shell -version`——确认版本号是你以为的那个。

**交接时最容易出事的地方**：老员工把任务交给你，说"跟我的脚本跑就行"。他的脚本依赖他 `.cshrc` 里的 `PDK_ROOT`，你 source 不到，脚本第一次跑就挂在读库。所以**脚本要自己带环境检查**（01-06 那一课就专门写这个）。

**做错了会怎样**：PATH 顺序错，你跑的是去年的工具版本，出来的报告和同事对不上，查两天才发现；`kill -9` 用错地方，一夜的 PNR 结果打不开；`DISPLAY` 设错，GUI 卡在启动界面，你以为机器坏了，重启服务器被全组骂。这三个坑没有一个需要高深知识，全在"知道自己在动什么"。

:::quiz
`nohup cmd > log 2>&1 &` 里四个部分各起什么作用？|nohup 让进程忽略挂断信号（断网不死）；`> log` 把正常输出写进日志；`2>&1` 把错误也并进同一份日志；`&` 放到后台，终端立刻还给你。
`kill -15` 和 `kill -9` 的本质区别是什么？|15 是 TERM，进程能捕获，可以先存盘再退出；9 是 KILL，内核直接抹掉，进程没有任何回调机会，写文件写到一半就会留下损坏的数据库。
末尾加了 `&`，为什么断网后任务还是死了？|`&` 只让任务不占终端，进程仍属于这个会话；终端断开时内核发 HUP，默认动作是退出。要加 `nohup` 或 `disown` 才能活下来。
`Ctrl+Z` 和 `Ctrl+C` 有什么区别？|`Ctrl+C` 发 INT（2），结束前台任务；`Ctrl+Z` 发 TSTP（20），只是暂停（挂起），进程还在，`jobs` 能看到，`bg` 可以让它继续跑。
`ps -ef | grep dc_shell` 为什么会多出一条 grep？|grep 自己也在这个进程列表里，它的命令行含 dc_shell。把模式写成 `"[d]c_shell"` 就不会匹配到自己。
`ps` 输出里 TIME 和 STIME 分别是什么？|STIME 是进程启动的时刻；TIME 是累计占用 CPU 的时间。TIME 远小于"已运行时长"说明进程主要在等 I/O 或等 license。
`export PATH=/新目录:$PATH` 里，为什么 `$PATH` 要放在后面？|PATH 从左到右查找，前面的目录优先；`$PATH` 放后面才能让新目录先被搜到，同时保留原有目录。反过来写就变成系统目录优先。
报 `bad interpreter: No such file or directory` 是什么原因？|脚本第一行 `#!` 指向的解释器路径不存在，常见是路径写错，或文件在 Windows 上编辑过、行尾多了 `\r` 让 `/bin/bash\r` 找不到。
`DISPLAY` 为空时会发生什么，为什么 batch 模式不受影响？|图形程序找不到 X server，报 `Can't open display`；batch 模式不画图，不需要 DISPLAY，所以能正常跑。
`.bashrc` 和 `.cshrc` 分别在什么时候被读？|`.bashrc` 被非登录的交互 bash 读（登录 shell 读 `.bash_profile`，通常里面再 source `.bashrc`）；`.cshrc` 被每个 tcsh 启动时读（交互和脚本都一样），`.login` 只在登录时读一次。
:::

:::check
- 能说出程序和进程的区别，知道 PID 和 PPID 各是什么
- 会用 `ps -ef | grep`、`ps -o pid,ppid,etime,cmd`、`pstree` 定位一个任务
- 能解释 `kill -15` 与 `-9` 的差别，并说出为什么优先用 15
- 分得清 `&`、`Ctrl+Z`、`bg`、`nohup`、`disown` 各自解决什么问题
- 能背出"命令找不到"的三种原因和对应修法
- 知道 `HOME`、`PATH`、`DISPLAY` 各自管什么，能解释 GUI 起不来但 batch 能跑
- 知道 `.bashrc` 与 `.cshrc` 的加载时机，会用 `source` 让改动立刻生效
:::
