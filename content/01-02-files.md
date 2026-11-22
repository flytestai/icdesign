---
id: 01-02-files
no: 03
stage: 1
title: 文件操作与权限：为什么你的脚本"跑不了"
en: Files & Permissions
hours: 3
minutes: 40
tags: [Linux, 文件, 权限, chmod]
summary: 复制、移动、删除、查看文件；搞懂 rwx 权限和 755/644 这两个天天见的数字，从此不再被 "Permission denied" 卡住。
---

## 文件不止一种 {#types}

`ls -l` 输出的第一列看着像乱码，其实第一位就告诉你这是什么：

```
drwxr-xr-x   2 weizhen weizhen  4096 Nov 22 10:12 scripts
-rw-r--r--   1 weizhen weizhen  1820 Nov 22 10:12 run.tcl
lrwxrwxrwx   1 weizhen weizhen    18 Nov 22 10:12 latest -> runs/20261122
```

| 第一位 | 类型 | 说明 |
|---|---|---|
| `-` | 普通文件 | 文本、网表、报告、压缩包 |
| `d` | 目录 | directory，能进去的"文件夹" |
| `l` | 符号链接 | 快捷方式，指向别处 |

后面那串 `rwxr-xr-x` 是权限，本节后半段专门讲。

:::term Symlink | 符号链接
一个"指向另一个文件的文件"，类似 Windows 的快捷方式。删掉链接不会删掉原文件。

工程里常用来做"最新版本"指针：`latest -> runs/20261122`，脚本永远读 `latest/`，就不用每次改路径。
:::

## 复制、移动、重命名、删除 {#cpmv}

```bash
cp run.tcl run_backup.tcl
# copy：把 run.tcl 复制一份，命名 run_backup.tcl

cp -r scripts/ scripts_bak/
# -r = recursive，目录必须加 -r，否则报 "omitting directory"

cp -p run.tcl /tmp/
# -p = preserve，保留原文件的修改时间和权限（备份时很有用）

mv run.tcl scripts/
# move：把文件移到 scripts 目录下

mv run.tcl run_v2.tcl
# mv 同时承担"重命名"的职责（同一目录内移动就是改名）

rm run_backup.tcl
# remove：删除文件

rm -r old_runs/
# 删目录必须 -r

rm -f *.log
# -f = force，不询问直接删
```

:::pitfall `rm -rf` 是这门课里最危险的命令
`rm -rf /path/to/dir` 会**不问、不回收、不提示**地删掉整个目录。Linux 没有回收站。

三个保命习惯：

1. **删之前先 `ls` 看一眼**。`ls old_runs/` 确认内容，再 `rm -r old_runs/`。
2. **变量要加引号**。`rm -rf $DIR/` 如果 `$DIR` 是空的，就变成了 `rm -rf /`。
3. **路径用绝对路径，别用通配符**。`rm -rf run/*` 手滑打成 `rm -rf run /*`，中间多一个空格，删的就是整个根目录。
:::

:::scene 为什么老工程师删文件前总要 ls 一下
不是谨慎，是被坑过。芯片工程一个目录几十 GB、跑了三天的结果，删错了重跑要三天。所以行业里有个默认规矩：**先看后删，能改后缀就别删**（`mv old old.bak` 比 `rm -r old` 安全得多）。
:::

## 看文件内容：cat / less / head / tail {#view}

```bash
cat run.tcl
# 把整个文件打到屏幕上。小文件用；几千行的报告会刷屏

less timing.rpt
# 分页查看大文件。空格往下翻，b 往上翻，/keyword 搜索，q 退出
# 后端看报告基本都用 less，不用 cat

head -20 timing.rpt
# 只看前 20 行（默认 10 行）

tail -50 run.log
# 只看最后 50 行。跑批时最常用——最新日志永远在末尾

tail -f run.log
# -f = follow，实时盯着日志增长。命令还在跑的时候用这个
# 退出按 Ctrl + C
```

:::tip 看日志的正确姿势
跑一个要 3 小时的流程，不要等 3 小时后再看。开两个终端：一个跑流程，一个 `tail -f run.log`。日志里出现 `Error` 就立刻停下排查，别浪费三小时。

想只挑错误行：`grep -i error run.log`（下一课讲 grep）。
:::

:::sandbox basic | 试：cp pnr.tcl pnr_bak.tcl、mv、rm、chmod 755、ls -l

## 权限：rwx 到底是什么 {#perm}

`ls -l` 的那串 `-rw-r--r--` 拆成四段看：

```
-      rw-        r--        r--
类型   属主权限    属组权限    其他人权限
```

三个字母对应三种动作：

| 字母 | 含义 | 对文件 | 对目录 |
|---|---|---|---|
| `r` | read 读 | 能看内容 | 能列出里面有什么（`ls`） |
| `w` | write 写 | 能修改 | 能在里面新建/删除文件 |
| `x` | execute 执行 | 能当程序运行 | 能进去（`cd`） |

所以 `-rw-r--r--` 的意思是：**属主能读写，同组和其他人只能读。**

:::term Permission | 权限
谁能对某个文件做什么。Linux 用三组 rwx 表示，分别对应"文件的主人 / 同组的同事 / 其他所有人"。

权限不对，工具就读不到库、脚本就跑不起来——这是新手最常遇到的"环境问题"，其实 90% 是权限问题。
:::

### 数字表示法：755 和 644

r=4，w=2，x=1，三个加起来就是一个数字：

| 权限 | 数字 | 常见用途 |
|---|---|---|
| `rwx` | 4+2+1 = **7** | 目录、可执行脚本 |
| `rw-` | 4+2 = **6** | 普通文本文件 |
| `r-x` | 4+1 = **5** | 只读可执行的目录 |
| `r--` | 4 | 只读文件（如 RTL、库文件） |

于是：

- **755** = `rwxr-xr-x`：我能改，别人能进能读。**目录和脚本的标准权限。**
- **644** = `rw-r--r--`：我能改，别人只能读。**普通文件的标准权限。**

```bash
chmod 755 run.sh
# 把 run.sh 变成"可执行"——脚本跑不了的第一解法

chmod 644 config.tcl
# 普通配置文件

chmod +x run.sh
# 另一种写法：只加执行位，不动其他权限

chmod -R 755 scripts/
# -R = 递归，把整个目录下所有东西都改掉（慎用）
```

:::pitfall Permission denied：脚本明明在，为什么跑不了
现象：

```
$ ./run.sh
-bash: ./run.sh: Permission denied
```

原因：文件没有 `x`（执行）权限。`ls -l run.sh` 会看到 `-rw-r--r--`，没有 x。

解法：`chmod +x run.sh`，再 `ls -l` 确认变成 `-rwxr-xr-x`。

顺带一个更隐蔽的版本：

```
$ ./run.sh
-bash: ./run.sh: /usr/bin/tcsh^M: bad interpreter
```

这是文件里混进了 Windows 的换行符（`^M`）。解法：`dos2unix run.sh`，或者 `sed -i 's/\r$//' run.sh`。**从 Windows 传到 Linux 的脚本，十有八九要过这一道。**
:::

:::scene EDA 工具报 "cannot open library"
你跑综合，报错：

```
Error: Cannot open library file 'slow.db'. (LCSH-3)
```

文件明明在啊？看权限：

```bash
ls -l lib/slow.db
# ---------- 1 weizhen weizhen 1820000 ... slow.db
```

权限是 `----------`（000），谁都读不了。`chmod 644 lib/slow.db` 之后正常。

这类问题在跨团队拷库、从压缩包解压时特别常见——**解压工具的 umask 设置不同，出来的文件权限就不一样**。
:::

## 小组：属主和属组 {#owner}

`ls -l` 中间两列是属主（owner）和属组（group）：

```
-rw-r--r-- 1 weizhen  pdteam  1820 Nov 22 10:12 run.tcl
             属主      属组
```

多人协作时，同一组的同事需要能改你的文件，就会把文件属组设成 `pdteam` 并给组写权限（`664`）。

```bash
chown weizhen:pdteam run.tcl     # 改属主和属组（通常要 sudo）
chgrp pdteam run.tcl             # 只改属组
id                               # 看自己属于哪些组
```

:::lab 动手：亲手制造一次（再解决）Permission denied
```bash
cd ~/demo 2>/dev/null || { mkdir -p ~/demo && cd ~/demo; }

# 1. 写一个最小脚本
echo 'echo hello-from-script' > hello.sh

# 2. 看它的权限：应该是 -rw-r--r--
ls -l hello.sh

# 3. 直接跑，观察报错
./hello.sh
# 预期：-bash: ./hello.sh: Permission denied

# 4. 加执行权限
chmod +x hello.sh
ls -l hello.sh
# 预期：-rwxr-xr-x

# 5. 再跑
./hello.sh
# 预期输出：hello-from-script
```

过关标准：能解释第 3 步为什么失败、第 4 步改了什么、为什么第 5 步就成功了。
:::

:::check
- 能用 `ls -l` 第一列判断文件类型和权限
- 能说出 755 / 644 对应的 rwx 组合，以及各自用在什么文件上
- 遇到过 `Permission denied` 时知道先 `ls -l` 再 `chmod +x`
- 知道 `rm -rf` 的三个保命习惯
- 会用 `tail -f` 盯日志
:::

:::quiz
`-rw-r--r--` 里属主有什么权限？|读和写（rw-），不能执行。
755 展开成 rwx 是什么？|rwxr-xr-x：属主读写执行，同组读执行，其他人读执行。
为什么删目录必须加 `-r`？|`-r` 是递归。不加的话 rm 认为目录不是普通文件，会报 "omitting directory" 并跳过。
脚本报 `bad interpreter: ^M` 是什么原因？|文件里混入了 Windows 换行符（CRLF）。用 dos2unix 或 sed 去掉 \r。
`chmod +x` 和 `chmod 755` 有什么区别？|`+x` 只给三组都加上执行位，其他权限不变；`755` 是把权限整体重设为 rwxr-xr-x。
:::
