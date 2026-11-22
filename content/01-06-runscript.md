---
id: 01-06-runscript
no: 07
stage: 1
title: 实战：用 Tcsh 写一个真正能用的跑批脚本
en: Tcsh in Practice
hours: 2.5
minutes: 38
tags: [tcsh, 脚本, module, 自动化, 日志]
summary: 把前两课拼起来：读懂公司的 .cshrc、用 module 切工具版本、写出一个带参数校验/时间戳目录/日志/失败即停的跑批脚本，并在它跑一半停住时按固定顺序排查。
---

## 公司的 .cshrc 里到底写了什么 {#cshrc}

:::goal 学完这一课，你能从零写出一个"别人拿去也能跑"的跑批脚本：参数有校验、日志有时间戳、失败会立刻停、退出码能区分是哪一类错。
:::

新账号登进去第一件事，是看 `.cshrc`。它决定了你这一个终端里工具能不能用。上一课讲了它**什么时候被读**，这一课讲它**里面写了什么**、为什么那样分层。

一个典型的芯片公司 `.cshrc`：

```csh
# 作用：公司/项目环境配置的典型结构（三层：系统 → 项目 → 个人）
# 用法：放在 ~/.cshrc；改之前先 cp ~/.cshrc ~/.cshrc.bak
set path = ( $HOME/bin /usr/local/bin /usr/bin /bin $path )   # ① 基础 PATH

setenv PDK_ROOT   /home/proj/pdk/28nm        # ② 工艺库根目录（全组共用）
setenv PROJ_ROOT  /home/proj/28nm/backend    # ② 项目根目录
setenv LM_LICENSE_FILE 27000@lic.company.com # ② license 服务器

alias ll 'ls -lht'                           # ③ 个人习惯
alias cd.. 'cd ..'

if ( -f $PROJ_ROOT/setup.csh ) then          # ④ 项目级环境：存在才加载
    source $PROJ_ROOT/setup.csh              #    工具版本、额外的库路径都在里面
endif
```

这份文件体现的纪律是**分层**：

- **系统级**（`/etc/csh.cshrc`、`/etc/profile.d/`）由 IT 维护，你不用碰。
- **项目级**（`$PROJ_ROOT/setup.csh`）由项目负责人维护，切项目就换它。
- **个人级**（`~/.cshrc` 里的别名和小工具路径）只影响你自己。

新人常犯的错是把自己的工具路径直接写进 `~/.cshrc`，结果换项目、换版本时忘了删，`which dc_shell` 指向去年那个版本，跑出来的报告和同事对不上。**工具版本应该由 `module` 管，不该写死在 `.cshrc` 里。**

`source` 那一行还有个细节：`if ( -f ... ) then` 先判断文件存在。不判断的话，项目目录被归档、`setup.csh` 不在了，你每开一个终端都报一次 `No such file or directory`，一天看几十遍。

## module：一人一套工具版本 {#module}

大公司不会让你手动 `set path`。他们用 **module** 系统：一堆工具版本登记在册，你按需加载。

```csh
# 作用：module 的五条常用命令
# 用法：在终端里交互使用；写进脚本时要放在所有工具调用之前
module avail                    # 列出所有可加载的模块（按名字排序，q 退出分页）
module avail synopsys           # 只看含 synopsys 的（很多系统的 avail 支持过滤）
module load synopsys/dc/R-2020.09   # 加载某个版本：本质是改 PATH/LD_LIBRARY_PATH
module list                     # 看当前加载了哪些（写进日志，事后能查版本）
module show synopsys/dc/R-2020.09   # 看这个模块到底改了哪些变量（排障神器）
module unload synopsys/dc/R-2020.09 # 卸载
module purge                    # 全卸，回到干净状态
module switch innovus/20.1 innovus/21.1  # 换版本（等价 unload 旧的 + load 新的）
```

`module load` 不是一个程序，而是一个 shell 里的函数/别名，它执行一段叫 modulefile 的脚本，往你的环境里写 PATH、`LD_LIBRARY_PATH`、`MANPATH` 和一堆 `XXX_ROOT` 变量。所以：

**第一，它只影响当前 shell。** 你在终端 A 里 `module load`，终端 B 里没有。脚本里也一样，脚本开头必须自己 load 一次，不能指望"我终端里有"。

**第二，版本冲突的表现很隐蔽。** 先 load 2019 再 load 2021，PATH 里两个目录都在，前面的优先——你以为在用 2021，其实用的是 2019。`module list` 会同时列出两个，这就是信号。正确做法是先 `module purge` 再 load，或者用 `module switch`。

**第三，`module show` 是排障的钥匙。** 工具起来了但报找不到库，`module show 模块名` 能看到它有没有把库目录加进 `LD_LIBRARY_PATH`。看不到，就说明这个 modulefile 写得有问题，该找 CAD 组。

:::term Module | 模块系统
管理"同一软件多个版本共存"的工具。`module load` 帮你改 PATH、LD_LIBRARY_PATH 等一批环境变量，让你在不同版本之间秒切。

好处是不用手写 `setenv`，不会互相污染；`module purge` 就回到干净状态。代价是它只作用于当前 shell，脚本里必须自己加载。
:::

:::scene 两个项目要用不同版本的 ICC2
A 项目跑 2019 版，B 项目跑 2021 版，同一个人同一天都要跑，而且两个项目的回归脚本都写死了自己的版本。

如果靠改 PATH，你会在两个终端之间来回切、改到疯，还容易在错误的终端里提交任务。用 module 之后，脚本开头各写各的：

```csh
# 作用：脚本自己声明用哪个版本，不依赖当前终端
# 用法：放在脚本最前面，在任何工具调用之前
module purge                  # 先清干净，避免继承终端里的残留
module load icc2/2019.03      # A 项目脚本写这一行
# module load icc2/2021.06    # B 项目脚本写这一行
```

这样"哪个脚本用哪个版本"写在文件里，可 review、可追溯。**这就是公司都上 module 的原因：版本变成代码的一部分，而不是某个人的终端状态。**
:::

:::pitfall 脚本里 module load 了，用的还是旧版本
现象：脚本开头 `module load icc2/2021.06`，日志里 `icc2_shell -version` 却打印 2019。

原因：加载前 PATH 里已经有 2019 的目录（来自终端或 `.cshrc`），新版本被加在后面，查找时旧版本先命中。

怎么查：`module list` 看是不是同时挂着两个版本；`which icc2_shell` 看实际路径里的版本号；`echo $PATH | tr ':' '\n' | grep -i icc2` 看顺序。

怎么改：`module purge` 之后再 `module load`；或者用 `module switch 旧 新`。脚本里养成"先 purge 再 load"的习惯，并且把 `module list` 的输出写进日志。
:::

## 一个能用的跑批脚本：五个必备件 {#script}

新手写的脚本通常只有一行：

```csh
# 作用：反面教材——能跑，但出了事查不出来
# 用法：不要这么写
dc_shell -f syn.tcl
```

它的问题：参数写死、没日志、不看退出码、跑一半失败也不知道、第二次跑覆盖第一次结果。合格的版本必须有五件东西：

| # | 必备件 | 不做会怎样 |
|---|---|---|
| 1 | 参数校验 | 参数为空，命令变成 `rm -rf /` 或读一个不存在的目录 |
| 2 | 时间戳运行目录 | 第二次跑覆盖第一次，想对比时没数据 |
| 3 | 日志（输出+错误） | 任务挂了，屏幕上什么都没有，事后无从查起 |
| 4 | 失败即停 | 综合失败了还继续跑 PNR，浪费三小时 |
| 5 | 有意义的退出码 | 上层脚本（或回归系统）不知道失败在哪一类 |

完整的骨架长这样，逐段都有注释：

```csh
#!/bin/tcsh -f
# ================================================================
# run_syn.csh —— 跑一次综合，带参数校验 / 时间戳目录 / 日志 / 失败即停
# 用法: ./run_syn.csh <top> <period_ns>
# 退出码: 0 成功 / 1 参数错 / 2 环境错 / 3 工具失败
# ================================================================

# ---- 1. 参数校验：缺参数就退出，别带着空变量往下跑 ----
if ( $#argv < 2 ) then
    echo "usage: $0 <top> <period_ns>"
    exit 1
endif
set TOP    = $1
set PERIOD = $2

# ---- 2. 环境校验：工具在不在、项目变量有没有 ----
which dc_shell >& /dev/null
if ( $status != 0 ) then
    echo "[ERROR] dc_shell not in PATH; run: module load synopsys/dc"
    exit 2
endif
if ( ! $?PROJ_ROOT ) then          # $?VAR 判断变量是否已定义（不是退出码！）
    echo "[ERROR] PROJ_ROOT not set; source setup.csh first"
    exit 2
endif

# ---- 3. 建时间戳目录：精确到秒，一天跑十次也不会撞 ----
set STAMP  = `date +%Y%m%d_%H%M%S`
set RUNDIR = $PROJ_ROOT/run/${TOP}_${STAMP}
mkdir -p $RUNDIR/log
if ( $status != 0 ) then
    echo "[ERROR] cannot create $RUNDIR"
    exit 2
endif

# ---- 4. 记录这一次的版本和参数（事后能回答"这是哪一版跑的"）----
module list >& $RUNDIR/log/env.txt
echo "top=$TOP period=$PERIOD stamp=$STAMP" > $RUNDIR/log/args.txt

# ---- 5. 生成这次要用的 tcl：把参数注入模板 ----
sed -e "s/@TOP@/$TOP/g" -e "s/@PERIOD@/$PERIOD/g" \
    $PROJ_ROOT/scripts/syn.tcl > $RUNDIR/syn.tcl
if ( $status != 0 ) then
    echo "[ERROR] failed to generate tcl"
    exit 2
endif

# ---- 6. 跑工具：输出和错误都进日志（tcsh 用 >&，不是 2>&1）----
cd $RUNDIR || exit 2               # cd 失败就退出，别在错误的目录里跑工具
dc_shell -f syn.tcl >& log/syn.log
set RC = $status                   # 立刻存下来，下一条命令会覆盖它

# ---- 7. 判定：先看退出码，再看日志里的 Error ----
if ( $RC != 0 ) then
    echo "[FAIL] dc_shell rc=$RC, see $RUNDIR/log/syn.log"
    grep -i -m 5 "error" log/syn.log
    exit 3
endif
set ERRS = `grep -ci "^Error" log/syn.log`
if ( $ERRS > 0 ) then
    echo "[WARN] $ERRS lines start with Error, check the log"
endif

echo "[DONE] $TOP period=$PERIOD at $STAMP"
echo "[DONE] result: $RUNDIR"
exit 0
```

几个设计决定值得解释：

- **`$?PROJ_ROOT` 不是退出码。** tcsh 里 `$?变量名` 表示"这个变量定义了没有"，返回 1/0。退出码是 `$status`。这两个概念在 bash 里都叫 `$?`，所以在 tcsh 里混用是高频错误。
- **`>&` 而不是 `2>&1`。** tcsh 没有文件描述符写法，`>&` 就是"输出+错误一起"。
- **参数用 `sed` 注入模板，而不是 `setenv`。** 环境变量会被子进程继承，但 tcl 脚本里读环境变量要写 `$::env(TOP)`，容易漏。用 `sed` 把 `@TOP@` 替换掉，生成的 tcl 打开就能看懂。
- **退出码分段。** 1 是"你参数写错了"，2 是"环境没配好"，3 是"工具跑挂了"。上层批量脚本一看退出码就知道该重试还是该找人。

:::term Exit Code | 退出码 / 返回码
每个命令执行完返回给 shell 的一个整数：0 成功，非 0 失败，不同数字代表不同错误。

tcsh 里用 `$status` 读，而且**只保留上一条命令的**，必须紧接着读（或者立刻 `set rc = $status`）。脚本用 `exit N` 把退出码传给调用者。
:::

:::term Positional Parameter | 位置参数
脚本收到的参数，按位置编号：`$1`、`$2`…… `$0` 是脚本自己的名字，`$#argv` 是参数个数，`$*` 是全部参数。

用法第一条永远是 `if ( $#argv < N ) then ... exit 1`，否则 `$2` 为空时后面的命令会做出你完全没预料的事。
:::

:::pitfall tcsh 里写 2>&1 报 Ambiguous output redirect
现象：

```
Ambiguous output redirect.
```

原因：从 bash 抄来的 `cmd > log 2>&1`。tcsh 不认识 `2>&1` 这种文件描述符写法，`>&` 在 tcsh 里本身就有"输出和错误一起"的意思，两个语法撞在一起。

怎么改：`cmd >& log`（都进文件）、`cmd >& /dev/null`（都丢掉）、`cmd |& tee log`（都进管道，`|&` 是 tcsh 的"连错误一起管道"）。

判断依据：只要报错里有 `redirect`，先看这一行是不是用了 `2>&1`。
:::

## 失败即停：tcsh 里没有 set -e {#failfast}

bash 脚本开头常写 `set -e`：任何命令返回非 0 就立刻退出。**tcsh 没有这个开关。**

tcsh 的默认行为是：命令失败了，脚本继续往下跑。所以这一步 `mkdir` 失败、下一步 `cd` 到一个不存在的目录、再下一步 `dc_shell` 在错误的目录里跑，最后你拿到一份"成功"的日志，结果是错的。

有三种写法，从简到繁：

**写法一：一行搞定的用 `&&`。**

```csh
# 作用：把"成功才继续"写在同一行
# 用法：只适合单条命令，不适合大段逻辑
mkdir -p $RUNDIR && cd $RUNDIR || exit 2   # mkdir 成功才 cd，cd 失败就退出
```

`&&` 是"前面成功才执行后面"，`||` 是"前面失败才执行后面"。tcsh 两者都支持，写短逻辑最省事。

**写法二：每个关键步骤后面检查 `$status`。** 就是上一节脚本里的样子。啰嗦，但最直白，别人接手一眼能看懂。要点是**立刻存**：

```csh
# 作用：检查上一步，立刻存退出码
# 用法：每一条"不能失败"的命令后面接这三行
dc_shell -f syn.tcl >& log/syn.log
set RC = $status          # 必须紧邻，中间插任何命令都会覆盖
if ( $RC != 0 ) exit 3
```

**写法三：把检查抽成一个被 source 的小文件。** 老手会这么干，但要知道它的代价：

```csh
# 作用：check.csh —— 通用检查器，被主脚本 source 调用
# 用法：source check.csh $status "步骤名"；第一个参数必须是刚拿到的退出码
if ( $1 != 0 ) then
    echo "[FATAL] $2 failed, rc=$1"
    exit 9
endif
```

主脚本里写 `source check.csh $status "generate tcl"`。注意必须把 `$status` 作为参数传进去——`source` 自己也会执行命令，进去之后 `$status` 已经变了。

:::note 那 bash 的 set -u 呢
`set -u`（用未定义变量就报错）在 tcsh 里也没有直接等价物。替代做法是显式判断：`if ( ! $?TOP ) exit 1`。

另外 bash 的 `set -o pipefail` 在 tcsh 里同样没有。所以 tcsh 脚本里**不要依赖"管道失败会自动暴露"**，该检查的地方手动检查。
:::

## 脚本跑一半停了：按这个顺序查 {#debug}

"跑到一半没动静了"是最常见的求助。按固定顺序走，别乱试：

**第一步：看日志尾部。** `tail -50 log/syn.log`。脚本自己不打印的错（工具崩了、license 拿不到、磁盘满）都在这里。如果日志最后一行是半句话，说明进程是被强杀的（OOM 或 `kill -9`）。

**第二步：确认进程还在不在。** `ps -p <那个 PID>` 或者 `ps -ef | grep 关键词`。进程没了但日志没写完 = 被杀；进程在但 CPU 0% = 在等 license 或在等 I/O。

**第三步：开 `-x` 重跑，看脚本走到哪一行。**

```bash
# 作用：逐行回显展开后的命令，定位脚本停在哪
# 用法：不改脚本，命令行加 -x；输出重定向到文件方便翻
tcsh -x run_syn.csh ipa_top 2.5 >& trace.log
grep -n "Undefined variable\|No match\|not found" trace.log | head
```

`-x` 的输出是"展开后"的命令，所以你能看到 `$TOP` 到底是空的还是拼错了。查 `if` 为什么没进去，这是唯一可靠的办法。

**第四步：单独跑失败的那一条。** 把 `-x` 里最后成功的那行和它下一行复制出来，手工执行一遍，看报什么。脚本环境和交互环境的差别（当前目录、变量）在这一步会暴露。

**第五步：看退出码。** `echo $status`。0 和非 0 是两条完全不同的排查路径：非 0 是"某一步明确失败"，0 但没产出，说明脚本逻辑漏了检查（比如 `cd` 失败但没判断）。

五个常见原因，按出现频率排：

| 现象 | 原因 | 怎么确认 |
|---|---|---|
| `TOP: Undefined variable` | 参数没传，或变量名拼错 | `tcsh -x` 看展开值 |
| `No such file or directory` | 路径用了相对路径，`cd` 之后失效 | 脚本里一律用绝对路径 |
| `Permission denied` | 脚本没有 x 权限，或目录不可写 | `ls -l`、`touch` 试写 |
| 卡住不动、CPU 0% | 等 license，或等一个交互式提示 | `ps` 看状态，日志里找 `Waiting` |
| 日志突然截断 | 磁盘满、被 OOM 杀、被 `kill -9` | `df -h .` 看空间，`dmesg` 看有没有 OOM 记录 |

:::pitfall cd 失败了，脚本还在错误目录里跑
现象：脚本先 `mkdir -p $RUNDIR`，再 `cd $RUNDIR`，但 `$RUNDIR` 因为权限问题没建成。`cd` 失败，脚本继续，工具在**当前目录**（项目根目录）里跑，生成的文件撒了一地。

原因：tcsh 不检查命令失败，`cd` 失败只会在屏幕上闪一行，脚本照跑。

怎么查：日志里搜 `cd:`；或者看工具产出的文件出现在哪——出现在项目根目录而不是 run 目录，就是这个问题。

怎么改：`cd $RUNDIR || exit 2`，或者 `cd` 之后立刻 `if ( $status != 0 ) exit 2`；更稳的是 `pwd` 打一行，日志里就能看到实际工作目录。
:::

## 把脚本做成可复用：参数化 {#reuse}

一次性的脚本写死就行，要给别人用的脚本必须参数化。三个层次，够用一辈子：

**第一层：位置参数 + 默认值。**

```csh
# 作用：必填参数 + 可选参数带默认值
# 用法：./run_syn.csh ipa_top 2.5 [effort]
if ( $#argv < 2 ) then
    echo "usage: $0 <top> <period_ns> [effort]"
    exit 1
endif
set TOP    = $1
set PERIOD = $2

set EFFORT = "medium"                 # 默认值，先设再覆盖
if ( $#argv >= 3 ) set EFFORT = $3    # 给了第三个参数才覆盖

echo "[INFO] top=$TOP period=$PERIOD effort=$EFFORT"
```

先设默认值、再有条件覆盖，是参数化脚本的标准套路。这样老调用方式（只给两个参数）不会因为新增参数而失效。

**第二层：把所有可调项集中到文件头。** 脚本开头一段 `# ==== 可配置项 ====`，路径、版本、线程数都放这儿，改的人不用读完全文。

**第三层：批量跑用外层循环，而不是复制脚本。**

```csh
# 作用：一组参数批量跑，一个失败不影响后面的记录
# 用法：./sweep_util.csh；每组跑完记一行结果
foreach u ( 0.30 0.35 0.40 )          # 三组利用率
    echo "==== util=$u ===="
    ./run_pnr.csh soc_top $u
    set rc = $status
    echo "util=$u rc=$rc" >> sweep_summary.txt   # 不管成败都记一行
end
```

关键在"不管成败都记一行"。批量脚本最怕的是中途挂掉、前面的结果也没记录，第二天完全不知道跑了几组、哪组失败。

:::term Dry Run | 空跑
只把"要执行的命令"打印出来，不真正执行。用来在跑 6 小时之前检查参数、路径、工具版本对不对。

实现上就是加一个开关：用 `$?DRY_RUN` 判断这个变量有没有设——设了就只把命令 `echo` 出来，没设才真正执行，两条分支用 `then ... else ... endif` 分开。跑长流程前先空跑一次，能省掉"参数拼错白跑一夜"。
:::

:::lab 动手：用假工具跑通这个脚本的三种结局
**任务**：不装 DC 也能练。造一个假 `dc_shell`，让脚本分别走"成功 / 参数错 / 工具失败"三条路。

```bash
# 作用：造一个可控的假工具，然后用真脚本打三种结局
# 用法：在 ~/demo 下执行
mkdir -p ~/demo/bin ~/demo/scripts && cd ~/demo

cat > bin/dc_shell <<'EOF'
#!/bin/bash
# 假 DC：根据环境变量 FAKE_RC 决定成功还是失败
echo "Fake DC start, args: $*"
echo "compiling..."
exit ${FAKE_RC:-0}
EOF
chmod +x bin/dc_shell
echo 'puts "top=@TOP@ period=@PERIOD@"' > scripts/syn.tcl
```

把上一节的 `run_syn.csh` 存到 `~/demo/run_syn.csh`，然后：

```bash
# 作用：三条验收路径
# 用法：每条跑完立刻 echo $status
export PATH=$HOME/demo/bin:$PATH        # 让 which dc_shell 找得到
export PROJ_ROOT=$HOME/demo             # 脚本要求的项目根目录
chmod +x run_syn.csh

./run_syn.csh                            # ① 不给参数 → usage，退出码 1
./run_syn.csh soc_top 2.5                # ② 正常 → [DONE]，退出码 0
FAKE_RC=3 ./run_syn.csh soc_top 2.5      # ③ 工具失败 → [FAIL] rc=3，退出码 3
```

**过关标准**：

1. 三条路径的退出码分别是 1、0、3，能自己解释每个数字的含义。
2. `run/soc_top_*/log/` 下能看到 `syn.log`、`env.txt`、`args.txt` 三个文件。
3. 连跑两次，产生**两个**不同时间戳的目录，互不覆盖。
4. 故意把 `scripts/syn.tcl` 改名，脚本应该以退出码 2 退出，而不是继续跑。
:::

## 工作中怎么用：脚本是团队资产 {#in-work}

**谁写**：项目里的资深工程师或 CAD 团队写第一版，之后每个用它的人都会改一点。所以脚本的读者不只是你，还有三个月后接手的人（很可能就是你自己）。

**评审会看什么**：参数有没有校验、日志够不够定位问题、失败会不会静默继续、退出码有没有区分、版本有没有记录。这五条就是这一课的五件必备品。

**交接时最值钱的一句话**：这个脚本跑完，结果在哪个目录、日志叫什么、失败时先看哪一行。写不进脚本的，就写进 README。

**做错了会怎样**：脚本没做失败检查，综合挂了但 PNR 照跑，用了一个空的网表，跑完 3 小时布局布线，最后报告全是 `unresolved reference`——三小时白烧，而且你会先怀疑工具、怀疑库、怀疑机器，最后才怀疑脚本。**加一行 `if ( $status != 0 ) exit` 的成本是 5 秒。**

:::quiz
tcsh 里 `2>&1` 应该写成什么？|`>&`。`cmd >& log` 表示输出和错误都进日志，`cmd |& tee log` 表示都进管道。
`$status` 和 `$?VAR` 有什么区别？|`$status` 是上一条命令的退出码；`$?VAR` 是"变量 VAR 有没有定义"，返回 1/0。bash 里两者都写 `$?`，tcsh 里必须分清。
为什么 tcsh 脚本要自己做"失败即停"？|tcsh 没有 `set -e` 等价物，命令失败后默认继续执行，会在错误的状态下跑完整个流程并产出一份"成功"的日志。
脚本里为什么要用时间戳目录？|防止第二次运行覆盖第一次的结果；出问题时能回溯"当时那一版跑的是什么、参数是什么"，两次结果也能并排对比。
`module load` 之后版本还是旧的，最可能是什么原因？|PATH 里已经有旧版本目录且在更前面。先 `module purge` 再 load，或用 `module switch`，并用 `which` 确认实际路径。
`cd $RUNDIR` 失败了脚本会怎样？|tcsh 默认继续往下跑，工具会在原来的目录（通常是项目根目录）里执行，产出文件撒在错误的位置，日志看起来还"正常"。
为什么把 `$status` 立刻存进 `set RC`？|它只反映上一条命令，中间插任何一条命令（包括 `echo`）都会被覆盖，判断就永远进不去。
脚本里的退出码为什么要分段（1/2/3）？|让调用者（人或上层批量脚本）能区分"参数错、环境错、工具错"，决定是该改用法、找 CAD，还是重跑。
`source check.csh $status "步骤名"` 里为什么要把 `$status` 传进去？|`source` 本身会执行命令，进去之后 `$status` 已经变成 source 内部上一条命令的返回值，必须先把原值作为参数带进去。
:::

:::check
- 能读懂公司 `.cshrc` 的三层结构，知道工具版本为什么不该写死在里面
- 会用 `module avail / load / list / show / purge / switch`，知道它只影响当前 shell
- 能写出含"参数校验 + 时间戳目录 + 日志 + 失败即停 + 分段退出码"的脚本
- 知道 tcsh 没有 `set -e`，会用 `&&` 或 `if ( $status != 0 )` 手动停
- 知道 `>&` 对应 bash 的 `2>&1`，`|&` 对应 `2>&1 |`
- 能用 `tcsh -x` 定位脚本停在哪一行，并按"日志 → 进程 → 跟踪 → 单跑 → 退出码"排查
- 能把写死参数的脚本改成带默认值的参数化版本，并写一个批量循环
:::
