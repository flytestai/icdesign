---
id: 01-02-files
no: 03
stage: 1
title: 文件操作与权限：为什么你的脚本"跑不了"
en: Files & Permissions
hours: 3
minutes: 40
tags: [Linux, 文件, 权限, chmod]
summary: 复制移动删除、cat/less/head/tail 看报告、rwx 三段权限与 755 的 4/2/1 加法、属主属组、umask，以及脚本跑不了的三个检查点（权限位、shebang、CRLF）。
---

## 文件不止一种 {#types}

:::goal 学完这一课，你能用 `ls -l` 第一列判断文件类型和权限，独立算出任意 chmod 数字，并在脚本报 "Permission denied" 或 "bad interpreter" 时三分钟内定位原因。
:::

`ls -l` 输出的第一列看着像乱码，其实第一位就告诉你这是什么：

```
drwxr-xr-x   2 weizhen pdteam  4096 Nov 22 10:12 scripts
-rw-r--r--   1 weizhen pdteam  1820 Nov 22 10:12 run.tcl
lrwxrwxrwx   1 weizhen pdteam    18 Nov 22 10:12 latest -> runs/20261122
```

| 第一位 | 类型 | 说明 | 工程里的例子 |
|---|---|---|---|
| `-` | 普通文件 | 文本、网表、报告、压缩包 | `timing.rpt`、`soc.v`、`.db` |
| `d` | 目录 | directory，能进去的"文件夹" | `pnr/`、`scripts/` |
| `l` | 符号链接 | 快捷方式，指向别处 | `latest -> runs/20261122` |

Linux 里"一切皆文件"，所以还会见到 `c`（字符设备，如 `/dev/tty`）、`b`（块设备，如硬盘）、`s`（socket）、`p`（管道）。**这四个你不用记，只要认得前三个就够干活了。**

一个实用技巧：`ls -F` 会在目录名后加 `/`、可执行文件后加 `*`、符号链接后加 `@`，一眼分清：

```bash
# 作用：用后缀区分类型；在任意目录下执行
ls -F                    # pnr/  scripts/  run.sh*  latest@
ls -lF                   # 长格式 + 类型后缀，两个信息一起看
```

:::term Symlink（Symbolic Link） | 符号链接
一个"指向另一个文件的文件"，类似 Windows 的快捷方式。删掉链接不会删掉原文件；原文件被删，链接会变成"断链"（红色闪烁或 `ls -l` 显示目标不存在）。

工程里常用来做"最新版本"指针：`latest -> runs/20261122`，脚本永远读 `latest/`，就不用每次改路径。
:::

## 复制、移动、重命名、删除 {#cpmv}

```bash
# 作用：文件的复制、移动、删除；在工程目录下执行，动手前先 ls 看一眼
cp run.tcl run_backup.tcl       # copy：复制一份，命名 run_backup.tcl
cp -r scripts/ scripts_bak/     # -r = recursive，目录必须加 -r，否则报 "omitting directory"
cp -p run.tcl /tmp/             # -p = preserve，保留原文件的修改时间和权限（备份时有用）
cp -a scripts/ scripts_bak2/    # -a = archive，等于 -rp 再加保留链接，整目录备份用这个
cp run.tcl{,.bak}               # 花括号展开：等价于 cp run.tcl run.tcl.bak，改配置前必备份

mv run.tcl scripts/             # move：把文件移到 scripts 目录下
mv run.tcl run_v2.tcl           # mv 同时承担"重命名"（同一目录内移动就是改名）
mv old_dir/ old_dir.bak/        # 比 rm -r 安全得多的"删除"：先改名，确认没用了再删

rm run_backup.tcl               # remove：删除文件
rm -r old_runs/                 # 删目录必须 -r
rm -f *.log                     # -f = force，不询问直接删
rm -i *.log                     # -i = interactive，逐个问你要不要删（批量删时先这么跑一遍）

mkdir scripts2                  # 建目录
mkdir -p a/b/c                  # -p：父目录不存在就一起建
rmdir empty_dir                 # 只能删空目录，有文件会报 "Directory not empty"
touch new.tcl                   # 建一个空文件；文件已存在则只更新修改时间
```

`cp` 和 `mv` 有一个很多人不知道的语义差别：**`mv` 是同文件系统内的"改名"，不复制数据，瞬间完成；跨文件系统时它才真的复制再删除。** 所以把 6GB 的数据库 `mv` 到另一个挂载点时，会等很久——这不是卡住了。

:::pitfall `rm -rf` 是这门课里最危险的命令
`rm -rf /path/to/dir` 会**不问、不回收、不提示**地删掉整个目录。Linux 没有回收站。

三个保命习惯：

1. **删之前先 `ls` 看一眼**。`ls old_runs/` 确认内容，再 `rm -r old_runs/`。
2. **变量要加引号**。`rm -rf $DIR/` 如果 `$DIR` 是空的，就变成了 `rm -rf /`。
3. **路径别用通配符**。`rm -rf run/*` 手滑打成 `rm -rf run /*`，中间多一个空格，删的就是整个根目录。

再加一条工程习惯：**能改名就别删**。`mv old old.bak` 之后，你还有一次反悔的机会；`rm -r old` 之后没有。
:::

:::scene 周五 18:40，一条 rm 让整个组加班
你入职两个月，在 route 阶段负责清理磁盘。师傅说过"`run/` 下超过三天的都可以删"，于是你敲了：

```
rm -rf run/2026111*
```

本来想删 `20261110`、`20261111` 这几天的旧目录，结果把当天的 `20261119_0930` 也匹配进去了——那个目录里是刚跑完、还没保存到 `pnr/db/` 的布线结果。

Linux 没有回收站，也没有"撤销"。**唯一的补救是重跑，7 小时。**

老工程师删文件前总要先 `ls` 一眼，不是谨慎，是被这么坑过。所以行业里有个默认规矩：**先看后删，能改后缀就别删**（`mv old old.bak` 比 `rm -r old` 安全得多）。你会在很多老脚本里看到 `mv` 到 `trash/` 目录而不是 `rm`，那不是啰嗦，是工程成本算出来的。
:::

## 看文件内容：cat / less / head / tail {#view}

```bash
# 作用：查看文件内容；在报告所在目录执行
cat run.tcl                     # 把整个文件打到屏幕上。小文件用；几万行的报告会刷屏
cat -n run.tcl                  # -n 带行号，方便对照报错里的行号
less timing.rpt                 # 分页查看大文件：空格下翻、b 上翻、/关键字 搜索、n 下一个、q 退出
less +F run.log                 # 进入 less 后直接跟随末尾（等价于 tail -f，但能用 / 搜索）
head -20 timing.rpt             # 只看前 20 行（默认 10 行）
head -n 20 timing.rpt           # 同上，写法更明确
tail -50 run.log                # 只看最后 50 行。跑批时最常用——最新日志永远在末尾
tail -f run.log                 # -f = follow，实时盯着日志增长；Ctrl+C 退出
tail -F run.log                 # -F = follow by name，日志被轮转（改名重建）后还能继续跟
wc -l timing.rpt                # 数行数。判断"报告是不是空的"第一招
wc -lc timing.rpt               # 行数 + 字节数
```

`less` 里必须会的六个键：

| 键 | 作用 |
|---|---|
| `空格` / `b` | 下翻一页 / 上翻一页 |
| `g` / `G` | 跳到文件头 / 跳到文件尾 |
| `/关键字` | 向下搜索；`n` 下一个，`N` 上一个 |
| `q` | 退出 |

:::tip 看日志的正确姿势
跑一个要 3 小时的流程，不要等 3 小时后再看。开两个终端：一个跑流程，一个 `tail -f run.log`。日志里出现 `Error` 就立刻停下排查，别浪费三小时。

只想挑错误行：`grep -i error run.log`（下一课讲 grep）。

还有一个更省事的组合：`tail -f run.log | grep -i -E "error|warning"`，只让错误和警告滚出来，其余噪音全部过滤。
:::

下面的黑框是 basic 预设，起点在家目录。提示语里的 `cp pnr.tcl ...` 要先 `cd backend_lab/soc/pnr` 才能跑——**这正是"相对路径依赖当前位置"的现场演示**，直接在家目录敲会报 `No such file or directory`。

:::sandbox basic | 试：cp pnr.tcl pnr_bak.tcl、mv、rm、chmod 755、ls -l
:::

## 权限：rwx 到底是什么 {#perm}

`ls -l` 的那串 `-rw-r--r--` 拆成四段看：

```
-      rw-        r--        r--
类型   属主权限    属组权限    其他人权限
```

三个字母对应三种动作：

| 字母 | 含义 | 对文件 | 对目录 |
|---|---|---|---|
| `r` | read 读 | 能看内容（`cat`） | 能列出里面有什么（`ls`） |
| `w` | write 写 | 能修改内容 | 能在里面新建/删除文件 |
| `x` | execute 执行 | 能当程序运行 | 能进去（`cd`）、能穿过它访问子路径 |

所以 `-rw-r--r--` 的意思是：**属主能读写，同组和其他人只能读。**

注意目录那一列容易反直觉：**目录的 `w` 不是"能改目录名"，而是"能在里面增删文件"**。所以一个只有 `r` 没有 `w` 的目录，你能看列表但删不掉里面的东西；只有 `x` 没有 `r` 的目录，你能 `cd` 进去、能访问已知文件名，但 `ls` 会报 `Permission denied`。

:::term Permission | 权限
谁能对某个文件做什么。Linux 用三组 rwx 表示，分别对应"文件的主人 / 同组的同事 / 其他所有人"。

权限不对，工具就读不到库、脚本就跑不起来——这是新手最常遇到的"环境问题"，其实 90% 是权限问题。
:::

### 数字表示法：755 和 644 是怎么加出来的

r=4，w=2，x=1，**每一组内部把字母对应的数字加起来**，就是一个 0~7 的数：

| 权限 | 加法 | 数字 |
|---|---|---|
| `rwx` | 4+2+1 | **7** |
| `rw-` | 4+2 | **6** |
| `r-x` | 4+1 | **5** |
| `r--` | 4 | **4** |
| `-wx` | 2+1 | **3** |
| `-w-` | 2 | **2** |
| `--x` | 1 | **1** |
| `---` | 0 | **0** |

三组数字连起来就是 `chmod` 的参数。手算三个例子：

- **755** = `rwx` + `r-x` + `r-x` = 7/5/5：我能读写执行，同组和其他人能读能执行。**目录和脚本的标准权限。**
- **644** = `rw-` + `r--` + `r--` = 6/4/4：我能读写，别人只能读。**普通文件的标准权限。**
- **640** = `rw-` + `r--` + `---` = 6/4/0：同组能读，**其他人完全看不到**。放敏感配置（含密钥、工艺参数）时用。

反过来算：`750` 是什么？7=`rwx`，5=`r-x`，0=`---`，即 `rwxr-x---`——属主全权限，同组能读能进，外人无权限。这是团队共享目录的常见配置。

```bash
# 作用：改权限；在文件所在目录执行，改完用 ls -l 验证
chmod 755 run.sh                # 数字法：整体重设成 rwxr-xr-x
chmod 644 config.tcl            # 普通配置文件
chmod 640 soc.sdc               # 只让同组看，外人看不到
chmod +x run.sh                 # 符号法：只给三组都加执行位，其他权限不动
chmod u+x,go-w run.sh           # 符号法精确控制：属主加 x，同组和其他人去掉 w
chmod -R 755 scripts/           # -R = 递归，把整个目录下所有东西都改掉（慎用）
chmod -R u+rwX scripts/         # 大写 X 只给目录加 x，不给普通文件加（比 -R 755 安全）
```

**`+x` 和 `755` 的区别**：`+x` 是"在现有基础上加"，会保留原来的 6 或 4；`755` 是"整体覆盖"。所以 `chmod 755` 一个原本 600 的私钥文件，等于把它变成了所有人可读——**这是安全事故**。改权限前先 `ls -l` 看现状。

:::pitfall Permission denied：脚本明明在，为什么跑不了
现象：

```
$ ./run.sh
-bash: ./run.sh: Permission denied
```

原因：文件没有 `x`（执行）权限。`ls -l run.sh` 会看到 `-rw-r--r--`，第三位是 `-` 不是 `x`。

查法：`ls -l run.sh` 看第一列。**注意报错说的是 `-bash:` 开头**，说明 shell 读到了这个文件、只是不让执行——这和"文件不存在"是两回事，别去查路径。

解法：`chmod +x run.sh`，再 `ls -l` 确认变成 `-rwxr-xr-x`。
:::

:::scene EDA 工具报 "cannot open library"
你跑综合，报错：

```
Error: Cannot open library file 'slow.db'. (LCSH-3)
```

文件明明在啊？看权限：

```bash
# 作用：排查"文件存在但读不到"；在库文件所在目录执行
ls -l lib/slow.db               # 输出 ---------- 1 weizhen weizhen ... slow.db
```

权限是 `----------`（000），谁都读不了。`chmod 644 lib/slow.db` 之后正常。

这类问题在跨团队拷库、从压缩包解压时特别常见——**解压工具的 umask 设置不同，出来的文件权限就不一样**（umask 在最后一章讲）。判断依据：报错里出现 "Cannot open" 而不是 "Cannot find"，八成是权限，不是路径。
:::

## 小组：属主和属组 {#owner}

`ls -l` 中间两列是属主（owner）和属组（group）：

```
-rw-r--r-- 1 weizhen pdteam 1820 Nov 22 10:12 run.tcl
             │        │
            属主      属组
```

权限的三段就是按这两个身份划分的：**你是属主，看你那段；你不是属主但在属组里，看中间那段；都不是，看最后一段。**

多人协作时，同一组的同事需要能改你的文件，就会把文件属组设成 `pdteam` 并给组写权限（`664` 或 `775`）。

```bash
# 作用：查看和修改归属；改属主通常需要 sudo
id                              # 看自己的 uid、gid、以及属于哪些组
groups                          # 只看组名列表
ls -ln                          # -n = numeric，把用户名显示成 uid，排查"同名不同号"时用
chgrp pdteam run.tcl            # 只改属组（你要先是该组成员）
chown weizhen:pdteam run.tcl    # 同时改属主和属组（一般要 sudo）
chown -R weizhen:pdteam pnr/    # 递归改整个目录（跨团队交接时用）
```

为什么会有"文件明明可读，工具却说读不到"？一个常见原因：**你的账号不在这个文件的属组里，而其他人权限是 `---`**。`id` 一看就知道。这在跨部门拿库、或者从别人目录里直接拷文件时特别常见。

三个工作中真实的归属问题，每个都有对应的解法：

**第一，"我拷过来的文件，属主还是他"。** 用 `cp` 复制别人目录里的文件，新文件的属主是你（因为是你创建的），但**如果你用 `cp -p` 保留了原属性，属主会试图保持原样——普通用户做不到，只有 root 能改属主**。所以交接库文件时，正确做法是让对方把文件放进共享目录、由管理员统一 `chown`，而不是各自拷来拷去。

**第二，"同组同事改不了我的文件"。** 这是 `umask` 和属组共同决定的。共享目录的标准配置是：

```bash
# 作用：搭一个团队共享目录；目录属主执行，成员需先加入 pdteam 组
mkdir -p /proj/share
chgrp pdteam /proj/share          # 属组设成团队
chmod 2775 /proj/share            # 2 = setgid：新建的子文件自动继承 pdteam 属组
umask 002                         # 配合 775，同组才能写
```

`2775` 里最前面那个 `2` 是 **setgid（设置组 ID）**：目录带上它以后，**在里面新建的任何文件都自动属于 `pdteam` 组**，而不是创建者自己的主组。没有它，每个人建的文件属组都不一样，权限规则就永远对不齐——这是团队共享目录必须加的一个位。

**第三，"离职同事的文件谁都动不了"。** 属主账号被删后，文件属主显示成 uid 数字（`ls -ln` 能看到），这时只能由 root `chown` 给接手的人。所以项目交接清单里，一定要有"目录属主改成接手人"这一条。

## 一个文件在磁盘上是什么：inode、硬链接、软链接 {#inode}

这一节解释一个困扰很多人的现象：**为什么删了大文件，磁盘空间没释放？为什么"文件还在"却打不开？**

先说结论：Linux 里文件名不是文件本身。文件的内容和元数据（权限、属主、大小、时间、数据块位置）存在一个叫 **inode** 的结构里，目录只是"文件名 → inode 编号"的一张映射表。

:::term inode（Index Node） | 索引节点
文件系统里描述一个文件的"档案卡"：存权限、属主、大小、时间戳、数据块在哪，但**不存文件名**。文件名存在目录里，目录项指向 inode 编号。所以同一个 inode 可以有多个名字（硬链接），也可以有零个名字（文件被删但进程还开着）。
:::

`ls -l` 第二列那个数字（`-rw-r--r-- 1 ...` 里的 `1`）就是**硬链接数**，即"有多少个文件名指向这个 inode"。

```bash
# 作用：观察 inode 与链接；在自己的 demo 目录里执行
ls -i run.tcl                   # -i 显示 inode 编号，比如 1318422 run.tcl
ln run.tcl run_hard.tcl         # 硬链接：两个名字，同一个 inode
ls -li run.tcl run_hard.tcl     # 两个文件的 inode 号相同，链接数变成 2
ln -s run.tcl run_soft.tcl      # 软链接：新建一个 inode，内容是"指向 run.tcl"的路径
ls -li run.tcl run_soft.tcl     # inode 号不同，软链接的类型位是 l
rm run.tcl                      # 删掉原名
cat run_hard.tcl                # 还能读：inode 还有 1 个名字
cat run_soft.tcl                # 报错：No such file or directory（断链）
```

两者的差别，一张表说清：

| | 硬链接（hard link） | 软链接（symlink） |
|---|---|---|
| 能否跨文件系统 | 不能 | 能 |
| 能否指向目录 | 不能（防止环） | 能 |
| 删掉原文件后 | 仍可访问（链接数减一） | 变成断链 |
| 占用 inode | 不额外占 | 占一个 |

**"删了文件空间不释放"的真相**：`rm` 只是把目录项去掉、链接数减一；只要还有进程开着这个文件（比如你 3 小时前启动、还在写日志的工具），inode 和数据块就不会回收。`df -h` 显示满了、`du -sh` 却算不出谁占的——就是这种情况。查法：`lsof | grep deleted`（真机命令），杀掉那个进程空间立刻回来。

**"磁盘没满却写不进去"的真相**：inode 用完了。文件系统在格式化时就把 inode 总数定死了。

手算一次：一个 500GB 的盘，inode 总数 300 万。你的流程每天产生 20 万个 1KB 的小报告文件，30 天就是

`20万 × 30 = 600 万个文件 > 300 万 inode`

于是第 15 天左右，`df -h` 还显示剩 400GB，但任何写入都报：

```
-bash: echo: write error: No space left on device
```

`df -h` 看空间、`df -i` 看 inode，**两个都要看**。这是后端服务器上真实发生过无数次的事故，根源是脚本把每一轮迭代都单独存了一个小文件。

## 脚本为什么"跑不了"：三个检查点 {#script}

"跑不了"有三种完全不同的原因，报错也完全不同。分不清就会在错的方向上修半天。

| 报错首行 | 原因 | 修法 |
|---|---|---|
| `-bash: ./run.sh: Permission denied` | 没有 `x` 权限 | `chmod +x run.sh` |
| `-bash: ./run.sh: /bin/bash^M: bad interpreter: No such file or directory` | 文件里有 Windows 换行符（CRLF） | `dos2unix run.sh` |
| `-bash: ./run.sh: /bin/tcsh: bad interpreter: No such file or directory` | shebang 指向的解释器不存在（本机没装在 `/bin`） | `which tcsh` 查真实路径，改 shebang |
| `-bash: run.sh: command not found` | 只写了 `run.sh`，而当前目录不在 `PATH` 里 | 写成 `./run.sh` |

按这个顺序查，三步就能定位：

```bash
# 作用：脚本跑不了时的标准排查；在脚本所在目录执行
ls -l run.sh                    # 第一步：看第一列有没有 x
head -1 run.sh                  # 第二步：看 shebang 指向哪个解释器
file run.sh                     # 第三步：看是不是 "with CRLF line terminators"（真机命令）
```

### 检查点一：shebang

脚本第一行 `#!/bin/bash` 叫 **shebang**（读作"沙邦"），作用是指定"用哪个解释器来读这个文件"。`#!` 后面必须是**解释器的绝对路径**，因为内核要直接执行它。

```bash
#!/bin/bash
# ↑ shebang：必须是文件第一行、第一列，前面不能有空行、空格、注释
# 作用：一个最小可用脚本；放在任意目录，chmod +x 后 ./脚本名 运行
echo "hello from $(basename "$0")"     # $0 是脚本自己的名字，便于日志里区分是哪个脚本
```

三个常见错误：

1. **shebang 不在第一行**。前面有空行、有注释，shebang 就失效，内核会当成 sh 脚本跑（很多 bash 语法会报错）。
2. **解释器路径不存在**。`#!/usr/bin/tcsh` 但机器上 tcsh 装在 `/bin/tcsh`，就报 `bad interpreter: No such file or directory`。用 `which tcsh` 确认真实路径。
3. **写成相对路径**。`#!bash` 不合法，必须 `/bin/bash` 这种绝对路径。

### 检查点二：执行位

`chmod +x` 只是"允许执行"，**还需要 shebang 告诉系统用什么执行**。两者缺一不可：

- 有 x、没 shebang：系统会用默认 shell 尝试执行，语法不兼容时报一堆莫名其妙的错。
- 有 shebang、没 x：`Permission denied`。

### 检查点三：CRLF

Windows 的换行是 `\r\n`（CRLF），Linux 是 `\n`（LF）。把 Windows 上编辑的脚本传上去，shebang 行实际是 `#!/bin/bash\r`，内核会去找一个名字叫 `bash\r`（显示成 `bash^M`）的解释器——当然找不到。

```bash
# 作用：去掉 Windows 换行符；在脚本所在目录执行，先备份再改
cat -A run.sh | head -3         # 看到行尾是 ^M$ 就是 CRLF，$ 是行尾标记
sed -i.bak 's/\r$//' run.sh     # 去掉行尾的 \r，.bak 留一份原件（改坏了能回退）
dos2unix run.sh                 # 专用工具，等价效果（装了 dos2unix 才有）
```

**判断依据**：报错里出现 `^M` 或 `bad interpreter`，且这个脚本是从 Windows 传过来的、或者用 Windows 编辑器改过——直接按 CRLF 处理，不用怀疑别的。

:::term Shebang | 释伴（脚本首行的解释器声明）
脚本第一行的 `#!` 加上解释器绝对路径，例如 `#!/bin/bash`。内核执行脚本时先读这一行，决定用哪个程序来解释剩下的内容。写错或放错位置，脚本必然跑不起来。
:::

:::lab 动手：亲手制造三种"跑不了"，再逐个修好
**任务**：在真机（或 WSL）上把三种失败各复现一次。只有自己制造过，下次看到报错才能立刻对上。

```bash
# 作用：复现权限、CRLF、解释器三种失败；在 ~/demo 下执行，不要在共享目录里跑
mkdir -p ~/demo && cd ~/demo

# ---- 失败一：没有执行位 ----
printf '#!/bin/bash\necho hello\n' > a.sh   # 写一个最小脚本，默认权限 644
./a.sh                                      # 预期：-bash: ./a.sh: Permission denied
chmod +x a.sh                               # 加执行位
./a.sh                                      # 预期输出 hello

# ---- 失败二：CRLF 换行 ----
printf '#!/bin/bash\r\necho hello\r\n' > b.sh   # \r\n 模拟 Windows 换行
chmod +x b.sh
./b.sh                                      # 预期：-bash: ./b.sh: /bin/bash^M: bad interpreter
cat -A b.sh | head -1                       # 确认行尾是 ^M$，这就是证据
sed -i.bak 's/\r$//' b.sh                   # 去掉 \r
./b.sh                                      # 预期输出 hello

# ---- 失败三：shebang 指向不存在的解释器 ----
printf '#!/bin/tcsh\necho hello\n' > c.sh   # 假设本机 tcsh 不在 /bin 下
chmod +x c.sh
./c.sh                                      # 预期：bad interpreter: No such file or directory
which tcsh || echo "本机没装 tcsh，这条正好复现了报错"
```

**说明**：不同 bash 版本的措辞略有差异（`bad interpreter` 后面可能带 `: No such file or directory`），但**首行关键词一致**：`Permission denied` / `bad interpreter` / `^M`。

**过关标准**：三次失败都能复现，且能不看笔记说出"看到哪句话 → 对应哪个检查点 → 用哪条命令修"。
:::

## umask：新文件的权限从哪来 {#umask}

你已经知道 `644` 和 `755` 是标准值。问题是：**你 `touch` 一个文件、`mkdir` 一个目录，权限为什么自动就是这两个数？** 答案是 umask。

:::term umask（User File-creation Mask） | 权限掩码
新建文件/目录时，"从默认权限里扣掉哪些位"的掩码。规则是**按位清除**：新文件 = `666` 去掉 umask 里的位；新目录 = `777` 去掉 umask 里的位。

为什么文件默认是 666 而不是 777？因为新建的文本文件不该默认可执行——这是 Unix 很早以前就定下的安全默认值。
:::

手算三个常见 umask：

| umask | 新文件 = 666 去掉掩码 | 新目录 = 777 去掉掩码 | 用在什么环境 |
|---|---|---|---|
| `022` | **644** | **755** | 最常见：自己写，别人读 |
| `002` | **664** | **775** | 团队共享：同组也能写 |
| `027` | **640** | **750** | 保密：外人完全看不到 |

验算 `022`：`666` 里每一位减去 2（去掉 w）→ `644`；`777` 每一位减去 2 → `755`。**注意是"按位清除"不是"减法借位"**，`6-2=4`、`7-2=5`，不会出现负数。

```bash
# 作用：查看和临时修改 umask；在任意目录执行
umask                           # 输出 0022（前导 0 表示八进制）
umask -S                        # 用符号显示：u=rwx,g=rx,o=rx
umask 027                       # 只在当前 shell 生效，关掉窗口就恢复
touch t1 && mkdir d1 && ls -ld t1 d1   # 验证：t1 是 640，d1 是 750
```

这个数字解释了前面那个"从压缩包解压出来的库文件权限是 000"的场景：**打包时的 umask 和你在自己机器上的不一样**，解压后权限就可能是任何值。所以拿到别人给的库，第一件事是 `ls -l` 看一眼，必要时统一 `chmod -R 644`。

:::check
- 能用 `ls -l` 第一列判断文件类型和权限，读出属主、属组、大小、时间
- 能说出 755 / 644 / 640 对应的 rwx 组合，并**手算**一个任意三位数
- 知道目录的 `x` 和 `r` 分别意味着什么，以及"能 ls 不能 cd"是哪种组合
- 遇到过 `Permission denied` 时知道先 `ls -l` 再 `chmod +x`
- 能说出脚本跑不了的三种原因，并各给一条排查命令
- 知道 `rm -rf` 的三个保命习惯，以及为什么 `mv` 比 `rm` 安全
- 能算出 umask 022 下新建文件和目录的权限
:::

:::quiz
`-rw-r--r--` 里属主有什么权限？|读和写（rw-），不能执行。
755 展开成 rwx 是什么？|rwxr-xr-x：属主读写执行，同组读执行，其他人读执行。手算：7=4+2+1，5=4+1。
为什么删目录必须加 `-r`？|`-r` 是递归。不加的话 rm 认为目录不是普通文件，会报 "omitting directory" 并跳过。
脚本报 `bad interpreter: ^M` 是什么原因？|文件里混入了 Windows 换行符（CRLF），shebang 变成 `#!/bin/bash\r`，内核找不到叫 `bash\r` 的解释器。用 dos2unix 或 `sed -i 's/\r$//'` 去掉。
`chmod +x` 和 `chmod 755` 有什么区别？|`+x` 只给三组都加上执行位，其他权限不变；`755` 是把权限整体重设为 rwxr-xr-x。对 600 的文件执行 `chmod 755` 会变成所有人可读。
一个目录权限是 `--x`，你能做什么、不能做什么？|能 `cd` 进去、能访问已知文件名（如 `cat d/file`），但不能 `ls` 列目录（需要 r）。
`rm` 删了大文件，为什么 `df -h` 显示空间没释放？|还有进程开着这个文件，inode 的链接数不为 0，数据块不会回收。用 `lsof` 配合 `grep deleted` 找到那个进程，结束它空间才回来。
umask 是 027 时，新建文件和目录分别是什么权限？|文件 640（666 去掉 027 的位）、目录 750（777 去掉 027 的位）。
硬链接和软链接最本质的区别是什么？|硬链接是同一个 inode 的另一个名字（链接数加一，删原名仍可访问）；软链接是独立 inode，内容是一个路径，原文件删了就断链。
:::
