---
id: 01-06-runscript
no: 07
stage: 1
title: 实战：用 Tcsh 写一个真正能用的跑批脚本
en: Tcsh in Practice
hours: 2.5
minutes: 38
tags: [tcsh, 脚本, module, 自动化]
summary: 把前两课拼起来：读懂公司的 .cshrc、会用 module 切工具版本、写出一个带参数/日志/时间戳/失败判断的跑批脚本。
---

## 公司的 .cshrc 里到底写了什么 {#cshrc}

新账号登进去第一件事，是看 `.cshrc`。它决定了你这一整个终端里工具能不能用。

一个典型的芯片公司 `.cshrc`：

```csh
# ~/.cshrc
set path = ( $HOME/bin /usr/local/bin /usr/bin /bin $path )

# 工具安装根目录
setenv PDK_ROOT    /home/proj/pdk/28nm
setenv PROJ_ROOT   /home/proj/28nm/backend

# license 服务器
setenv LM_LICENSE_FILE 27000@lic.company.com

# 别名
alias ll 'ls -lht'
alias cd.. 'cd ..'

# 加载项目专用环境
if ( -f $PROJ_ROOT/setup.csh ) then
    source $PROJ_ROOT/setup.csh
endif
```

:::term .cshrc | 登录配置脚本
每次开新终端时自动执行的文件，放在家目录。它做的事情就是"把环境准备好"：PATH、license、别名、项目变量。

`.cshrc` 是给交互式终端用的；`.login` 只在登录时执行一次。日常改环境改 `.cshrc` 就够。
:::

:::pitfall 改坏 .cshrc，终端打不开
如果在 `.cshrc` 里写了死循环或者语法错误，新开的每个终端都会卡住或狂报错。

**改之前先备份**：

```csh
cp ~/.cshrc ~/.cshrc.bak
```

如果已经改坏了：

```bash
# 用一个不读 .cshrc 的 shell 进去修
tcsh -f
# 或者用 bash
bash
vim ~/.cshrc
```
:::

## module：一人一套工具版本 {#module}

大公司不会让你手动 `set path`。他们用 **module** 系统：一堆工具版本登记在册，你按需加载。

```csh
module avail                 # 列出所有可加载的模块
module avail synopsys        # 只看 synopsys 相关

module load synopsys/dc/R-2020.09     # 加载某个版本的综合工具
module load cadence/innovus/21.1      # 加载 Innovus

module list                  # 看当前加载了哪些
module unload synopsys/dc/R-2020.09   # 卸载
module purge                 # 全部卸载，回到干净状态
module switch innovus/20.1 innovus/21.1   # 换版本
```

:::term Module | 模块系统
管理"同一软件多个版本共存"的工具。`module load` 实际上就是帮你改 PATH、LD_LIBRARY_PATH 等一堆环境变量，让你在多个版本之间秒切。

好处：不用手写 export，不会互相污染。用完 `module purge` 就干净了。
:::

:::scene 两个项目要用不同版本的 ICC2
A 项目用 2019 版，B 项目用 2021 版，同一个人同一天都要跑。

没有 module 的话，你改 PATH 改到疯。有 module：

```csh
module purge
module load icc2/2019.03
# 跑 A 项目
...
module purge
module load icc2/2021.06
# 跑 B 项目
```

**这就是为什么公司都上 module。**
:::

## 写一个真正能用的跑批脚本 {#script}

新手写的脚本通常长这样：

```csh
dc_shell -f syn.tcl
```

问题：没日志、没时间戳、不看退出码、跑一半失败也不知道。

合格的版本：

```csh
#!/bin/tcsh -f
# ------------------------------------------------------------
# run_syn.csh : 跑综合，自动建时间戳目录、写日志、判断成败
# 用法: ./run_syn.csh <top_name>
# ------------------------------------------------------------

# 1. 参数检查：没给参数就直接退出，别带着空变量往下跑
if ( $#argv < 1 ) then
    echo "usage: $0 <top_name>"
    exit 1
endif
set TOP = $1

# 2. 环境检查：工具在不在
which dc_shell >& /dev/null
if ( $status != 0 ) then
    echo "[ERROR] dc_shell not found in PATH"
    exit 2
endif

# 3. 建带时间戳的运行目录，避免覆盖上一次结果
set STAMP = `date +%Y%m%d_%H%M`
set RUNDIR = ./run/$STAMP
mkdir -p $RUNDIR
echo "[INFO] run dir = $RUNDIR"

# 4. 生成这一次要用的 tcl（把 top 名字注入进去）
sed "s/@TOP@/$TOP/g" ../scripts/syn.tcl > $RUNDIR/syn.tcl

# 5. 跑，日志进文件（>& 是 tcsh 的"输出+错误都重定向"）
cd $RUNDIR
dc_shell -f syn.tcl > syn.log &
set PID = $!
echo "[INFO] pid = $PID, log = $RUNDIR/syn.log"
wait $PID
set RC = $status

# 6. 判断结果：退出码 + 日志里有没有 Error
if ( $RC != 0 ) then
    echo "[FAIL] dc_shell exit code = $RC"
    grep -i "error" syn.log | head -5
    exit $RC
endif

set ERRCNT = `grep -ci "^Error" syn.log`
if ( $ERRCNT > 0 ) then
    echo "[WARN] found $ERRCNT lines starting with Error, check syn.log"
endif

echo "[DONE] $TOP synthesized at $STAMP"
```

:::term Exit Code | 退出码 / 返回码
每个命令执行完都会返回一个数字给 shell：0 表示成功，非 0 表示失败（不同数字代表不同错误）。

脚本里用 `$status`（tcsh）或 `$?`（bash）读它。**上一句执行完立刻读，读晚了会被下一条命令覆盖。**
:::

:::pitfall tcsh 里 `>&` 和 bash 的 `2>&1` 不一样
| 目的 | bash | tcsh |
|---|---|---|
| 输出+错误都到文件 | `cmd > log 2>&1` | `cmd >& log` |
| 输出+错误都丢掉 | `cmd > /dev/null 2>&1` | `cmd >& /dev/null` |

在 tcsh 脚本里写 `2>&1` 会报 `Ambiguous output redirect`。这是从 bash 抄脚本时最常见的错误。
:::

:::term `$#argv` / `$1` / `$0`
- `$#argv`：参数个数。`if ( $#argv < 1 )` 就是"没给参数"。
- `$1`、`$2`：第 1、2 个参数。
- `$0`：脚本自己的名字。
- `$*`：所有参数。

写脚本一定要先检查参数个数，否则 `$1` 为空时后面的命令会做奇怪的事（比如 `rm -rf $DIR/` 变成 `rm -rf /`）。
:::

:::lab 动手：跑通这个脚本（用假工具）
没有 DC 也能练。把工具换成一个假脚本：

```csh
# 1. 造一个假 dc_shell，模拟成功/失败
mkdir -p ~/demo/bin && cd ~/demo/bin
cat > dc_shell <<'EOF'
#!/bin/bash
echo "Fake DC: synthesizing..."
sleep 1
if [ "$1" = "-f" ]; then echo "Synopsys Design Compiler (fake) done"; fi
exit 0
EOF
chmod +x dc_shell
set path = ( ~/demo/bin $path )

# 2. 造一个最小 tcl
mkdir -p ~/demo/scripts
echo 'puts "top = @TOP@"' > ~/demo/scripts/syn.tcl

# 3. 把上面那个 run_syn.csh 存到 ~/demo/run_syn.csh，然后跑
cd ~/demo
chmod +x run_syn.csh
./run_syn.csh ipa_top
```

预期输出：

```
[INFO] run dir = ./run/20261122_2015
[INFO] pid = 12345, log = ./run/20261122_2015/syn.log
[DONE] ipa_top synthesized at 20261122_2015
```

过关标准：
1. 不带参数跑，应该打印 usage 并退出（`echo $status` 应为 1）。
2. 把假 dc_shell 的 `exit 0` 改成 `exit 3`，脚本应该打印 `[FAIL]` 并以非 0 退出。
:::

## 脚本跑一半停了，怎么查 {#debug}

三个动作按顺序做：

1. **看日志尾部**：`tail -50 syn.log`。tcsh 脚本本身不打印的错，通常在工具日志里。
2. **加 `-x` 跟踪**：`tcsh -x run_syn.csh ipa_top`，会把每一行执行前后的变量值打出来。**这是查"为什么 if 没进去"的唯一可靠办法。**
3. **看退出码**：`echo $status`。0 和非 0 是两套排查路径。

```csh
# 只跟踪某一段：临时打开再关掉
set echo    # 打开回显
... 你要看的几行 ...
unset echo  # 关掉
```

:::check
- 能读懂公司 `.cshrc` 里每一行的作用
- 会用 `module avail / load / list / purge`
- 能写出带"参数检查 + 时间戳目录 + 日志 + 退出码判断"的跑批脚本
- 知道 tcsh 里 `>&` 对应 bash 的 `2>&1`
- 会用 `tcsh -x` 调试脚本
:::

:::quiz
tcsh 里把输出和错误都重定向到日志，应该怎么写？|`cmd >& log`
`$#argv` 是什么？|脚本收到的参数个数。常用来做参数检查。
为什么要用时间戳建 run 目录？|避免覆盖上一次结果，出问题时能回溯"当时那一版跑的是什么"。
`tcsh -x script.csh` 有什么用？|打开跟踪模式，逐行打印执行的命令和变量展开结果，用来定位脚本在哪一步走错。
`$status` 是什么？什么时候必须立刻读？|上一条命令的退出码（0 成功，非 0 失败）。必须紧接着读，因为下一条命令会覆盖它。
:::
