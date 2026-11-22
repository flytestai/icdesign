---
id: 01-04-process
no: 05
stage: 1
title: 进程、后台任务与环境变量
en: Processes & Environment
hours: 3
minutes: 42
tags: [Linux, 进程, PATH, license]
summary: 为什么 `dc_shell` 会"command not found"、为什么你的任务一关终端就死、license 和环境变量到底怎么配——这一课把 EDA 环境问题一次讲透。
---

## 程序跑起来，就成了进程 {#proc}

磁盘上的 `dc_shell` 只是一个文件（程序）。你敲下命令回车，系统把它读进内存开始执行，这时候它就成了一个**进程**（Process），系统会给它一个编号，叫 PID。

```bash
ps
# process status：看当前终端里的进程

ps -ef
# 看系统里所有进程（-e 全部，-f 完整格式）

ps -ef | grep dc_shell
# 看综合工具还在不在跑

top
# 实时看 CPU / 内存占用，按 q 退出
# 后端跑大流程时，用 top 确认"到底是在算，还是卡死了"

kill 12345
# 给 PID 12345 发终止信号

kill -9 12345
# -9 = 强杀。普通 kill 没用时再用（不给它保存现场的机会）

pkill -f dc_shell
# 按名字杀所有相关进程，比一个个 kill 快
```

:::pitfall 别在服务器上乱 kill
公司服务器几十个人共用。`pkill -9 -u weizhen` 会杀掉你自己所有进程，包括别人帮你挂的回归任务。

**只杀自己确认过的 PID**。杀之前 `ps -ef | grep 进程号` 看清楚命令行是什么。
:::

## 后台跑：关掉终端任务也不能停 {#bg}

综合、布局布线动辄几小时。如果你直接敲命令，一断网、一关窗口，任务就跟着死了。

```bash
dc_shell -f syn.tcl > syn.log 2>&1 &
# 末尾的 & 表示"放到后台跑"，终端立刻还给你

jobs
# 看当前 shell 里有哪些后台任务

fg %1
# 把 1 号后台任务调回前台

nohup dc_shell -f syn.tcl > syn.log 2>&1 &
# nohup = no hang up：退出登录也不受影响，任务继续跑
# 这是跑长流程的标准写法

disown -h %1
# 让任务彻底脱离当前 shell 的管理
```

:::tip 跑长流程的模板
```bash
mkdir -p run/$(date +%m%d_%H%M)
cd run/$(date +%m%d_%H%M)
nohup icc2_shell -f ../../scripts/pnr.tcl > pnr.log 2>&1 &
echo "started, pid=$!"
```
按时间建目录 + nohup + 日志，第二天回来 `tail -f` 看进度。**这个模板可以直接抄进你的工作习惯。**
:::

## PATH：为什么命令会"找不到" {#path}

你敲 `ls`，系统怎么知道该执行哪个文件？它去 `PATH` 这个环境变量里列的目录，一个一个找。

```bash
echo $PATH
# 输出类似：/usr/local/bin:/usr/bin:/bin:/home/weizhen/bin
# 冒号分隔，从左到右找，找到第一个就用

which ls
# 告诉你 ls 到底在哪：/usr/bin/ls

which dc_shell
# 如果输出为空 → 说明 PATH 里没有它所在的目录
```

:::term Environment Variable | 环境变量
存在系统里的一组"键=值"，所有程序都能读到。它决定程序的行为，比如去哪里找命令（PATH）、去哪里找 license（LM_LICENSE_FILE）、去哪里找动态库（LD_LIBRARY_PATH）。

查看：`echo $变量名`；临时设置：`export 变量名=值`（bash）。
:::

:::pitfall `dc_shell: command not found` 的四种原因
按概率排：

1. **PATH 没包含工具目录**。`echo $PATH` 看不到 `/usr/Synopsys/...`。
2. **没加载环境脚本**。公司一般有个 `setup.sh` / `cshrc` 要 `source` 一下。
3. **工具根本没装**，或者装的是别的版本。
4. **你在 tcsh 里用了 bash 语法**（`export` 在 tcsh 里叫 `setenv`），环境没设成功。

排查顺序：`which` → `echo $PATH` → `env | grep -i synopsys` → 问组长要 setup 脚本。
:::

## 环境变量里最重要的三个 {#three-env}

| 变量 | 作用 | 出问题的症状 |
|---|---|---|
| `PATH` | 去哪找命令 | `command not found` |
| `LM_LICENSE_FILE` | 去哪找 license 服务器 | `Unable to checkout license` |
| `LD_LIBRARY_PATH` | 去哪找 `.so` 动态库 | `error while loading shared libraries: libXXX.so` |

```bash
# 临时设置（只对当前终端有效，关掉就没了）
export PATH=/usr/Synopsys/syn/R-2020.09-SP4/bin:$PATH
# 注意 $PATH 放在后面，意思是"新目录优先，但保留原来的"

export LM_LICENSE_FILE=27000@license-server

export LD_LIBRARY_PATH=/usr/Synopsys/lib/AMD.64:$LD_LIBRARY_PATH
```

:::scene 一次真实的排障（我们自己的环境里踩过）
装好 Library Compiler 后，`lc_shell` 能启动，但一直报降级模式：

```
LCSH-1: Cannot locate installation ...
```

第一反应"是不是没装全"——其实不是。真实原因是：缺 `SYNOPSYS_LC_ROOT` 这个环境变量，而且引擎依赖的三个动态库（`libtbb.so.2` 等）不在 `LD_LIBRARY_PATH` 里。

补齐两样之后立刻正常。**EDA 的"装不上"，八成是环境变量，而不是安装包。**
:::

:::sandbox proc | 试：env | grep PDK、export A=1、echo $A、ps、which ls

## 配置文件：bash 用 .bashrc，tcsh 用 .cshrc {#rc}

每次开终端都手动 export 太蠢。把设置写进配置文件，登录时自动执行。

```bash
# bash（Linux 默认）
vim ~/.bashrc
# 末尾加：
export PATH=/opt/tools/bin:$PATH
export LM_LICENSE_FILE=27000@lic

source ~/.bashrc
# 让改动立刻生效，不用重开终端
```

```csh
# tcsh（芯片公司常用）
vim ~/.cshrc
# 末尾加：
setenv PATH /opt/tools/bin:$PATH
setenv LM_LICENSE_FILE 27000@lic

source ~/.cshrc
```

:::term source | 加载
读一个脚本并**在当前 shell 里执行**它，所以脚本里设的变量会影响你当前这个终端。

不 source 直接跑脚本，变量只在那个脚本的子进程里有效，回到你的终端就没了。这是"我明明设了变量却不生效"的头号原因。
:::

:::pitfall `export` 和 `setenv` 混用
bash 里写 `setenv` → `command not found`
tcsh 里写 `export` → `Command not found` 或 `export: Command not found.`

先确认自己在哪个 shell：`echo $SHELL`。看到 `bash` 用 export，看到 `csh`/`tcsh` 用 setenv。
:::

:::lab 动手：把工具目录加进 PATH 并验证
```bash
cd ~/demo 2>/dev/null || { mkdir -p ~/demo && cd ~/demo; }

# 1. 造一个假的"工具"
cat > mytool <<'EOF'
#!/bin/bash
echo "mytool v1.0 running"
EOF
chmod +x mytool

# 2. 现在直接敲名字，找不到
mytool
# 预期：mytool: command not found

# 3. 把当前目录加进 PATH
export PATH=$PWD:$PATH

# 4. 再敲
mytool
# 预期：mytool v1.0 running

# 5. 关掉终端重开，再敲一次
# 预期：又找不到了 —— 因为 export 只在当前终端有效
```

过关标准：能解释第 2 步为什么失败、第 4 步为什么成功、第 5 步为什么又失败，以及怎么让它永久生效（写进 `~/.bashrc`）。
:::

:::check
- 会用 `ps -ef | grep` 找进程、`kill` 结束进程
- 知道 `nohup ... &` 三个部分各自的作用
- 能解释 `command not found` 的排查顺序
- 分得清 `PATH` / `LM_LICENSE_FILE` / `LD_LIBRARY_PATH` 各自管什么
- 知道 bash 用 `export`、tcsh 用 `setenv`
:::

:::quiz
`nohup cmd > log 2>&1 &` 里四个部分分别起什么作用？|nohup 让退出登录后进程不死；`> log` 输出到日志；`2>&1` 错误也进同一日志；`&` 放到后台。
`export PATH=$PWD:$PATH` 为什么要把 `$PATH` 放后面？|因为 PATH 从左到右查找，新目录放前面才优先；同时保留原有目录，否则 ls 之类的系统命令都会找不到。
报 `error while loading shared libraries: libtbb.so.2` 说明什么？|动态库找不到。需要把库所在目录加进 `LD_LIBRARY_PATH`，或把库放到系统库路径。
为什么 `source` 之后环境变量才生效，直接执行脚本不生效？|source 在当前 shell 里执行，变量留在当前环境；直接执行是在子进程里跑，子进程结束后变量就没了。
bash 和 tcsh 设置环境变量的命令分别是什么？|bash: `export NAME=value`；tcsh: `setenv NAME value`。
:::
