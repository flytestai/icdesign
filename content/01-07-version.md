---
id: 01-07-version
no: 08
stage: 1
title: 版本管理与自动化：git、make 和日志归档
en: Version Control & Automation for Backend Engineers
hours: 4
minutes: 42
tags: [git, make, 脚本, 自动化, 日志]
summary: 后端一天改二十次脚本，改错了必须能退回；跑一次几小时，跑完必须知道是哪一版跑的。这一课讲 git 三层与最小命令集、分支做参数实验、.gitignore 该写什么、make 的规则与 Tab 坑，以及把版本号写进运行目录。
---

## 为什么后端工程师必须会 git {#why}

:::goal 学完这一课，你能用 git 管住脚本的每一次改动、用分支做参数实验、用 make 把三步流程压成一个命令，并让每个运行目录自己说清"我是哪一版、用什么参数、几点跑的"。
:::

:::scene 改参数改崩了，想回到昨天
周三你把 `pnr.tcl` 里的利用率从 0.30 改到 0.40，跑了一夜，DRC 从 0 变成 1874。你想回到 0.30 那一版——但目录里只有 `pnr.tcl`、`pnr.tcl.bak`、`pnr_new.tcl`、`pnr_new2.tcl`、`pnr_final.tcl`，**你不知道哪个是 0.30**，而且 `pnr.tcl.bak` 是上周备份的，中间还改过三次别的参数。

有 git 的话，一条命令：`git checkout HEAD~1 -- pnr.tcl`，文件立刻回到上一版，其他文件不动。
:::

后端的日常是这样的：一天改二十次脚本、跑四次长流程、跟三个人交接。这三件事每一个都会逼你回答同一个问题——**"现在这个结果，是用哪一版脚本、哪一套参数跑出来的？"**

回答不了，就会出现这些场景：

- DRC 从 0 变成 1874，你改了五个地方，不知道是哪个引起的，只能一个一个回退重跑，每次 3 小时。
- 同事接手你的项目，看到 `pnr_final_v2_new.tcl`，不敢动，只能全部重写。
- 签核报告出问题，想知道当时用的约束，发现约束文件已经被覆盖了。

git 解决第一、第三个问题（能回退、能对比），规范的目录命名和 make 解决第二个（能看懂、能复现）。

:::term Git | 版本管理工具
记录"每次改了什么、谁改的、什么时候改的"的工具。每个版本叫一个 **commit（提交）**，可以随时回到任意历史版本、对比任意两个版本的差异。

后端用它主要做三件事：**回退**（改坏了退回去）、**对比**（这版和上版差在哪几行）、**交接**（别人能看懂历史）。
:::

## git 的三层与最小命令集 {#basic}

先建立最重要的一个概念：git 有三层，文件在它们之间单向流动。

```
工作区（你正在编辑的文件）
   │  git add
   ▼
暂存区（这次要提交的清单）
   │  git commit
   ▼
仓库（历史版本，.git/ 目录）
```

| 层 | 英文 | 是什么 | 对应命令 | 类比 |
|---|---|---|---|---|
| 工作区 | working tree | 你现在打开的那个文件 | 编辑器直接改 | 桌上的草稿 |
| 暂存区 | staging area / index | "这次提交包含哪些改动" | `git add` | 装进信封的纸 |
| 仓库 | repository | 已保存的历史 | `git commit` | 寄出去存档的信 |

为什么要中间这个"暂存区"？因为你改了五个文件，但这次只想提交其中两个（另外三个还没改完）。暂存区让你**挑着提交**。跳过它直接用 `git commit -a` 也行，但你会失去"这次改动的边界"——而边界正是三个月后你能看懂历史的原因。

```bash
# 作用：git 的最小命令集，覆盖日常 90% 的操作
# 用法：在项目根目录执行；第一次用先 init 和 config
git init                              # 在当前目录建仓库（生成 .git/，只需一次）
git config user.name  "weizhen"       # 提交记录里显示的名字（--global 是全局）
git config user.email "w@company.com" # 邮箱，和名字一起只需设一次

git status                            # 哪些文件改了：红色=未暂存，绿色=已暂存
git diff                              # 工作区 vs 暂存区，具体改了哪几行（最常用）
git diff --cached                     # 暂存区 vs 上次提交，commit 前最后看一眼
git add pnr.tcl                       # 把这个文件放进暂存区
git add -p pnr.tcl                    # 同一个文件里挑着加（改动多时很有用）
git commit -m "util 0.30->0.40, DRC 0->1874"   # 存成一个版本

git log --oneline                     # 一行一个版本，带短 hash
git log --oneline -5                  # 只看最近 5 条
git show a1b2c3                       # 某个版本具体改了什么
git diff HEAD~1 HEAD -- pnr.tcl       # 上一版和这一版在这个文件上的差异

git checkout HEAD~1 -- pnr.tcl        # 只把这个文件退回上一版（别的文件不动）
git revert a1b2c3                     # 生成一个"反向提交"撤销那次改动（推荐，历史保留）
git stash                             # 把没提交的改动先收起来，工作区变干净
git stash pop                         # 再放回来
```

几个必须理解的点：

**commit 保存的是"整个项目的快照"，不是"这次改的那几行"。** 所以你回到任意 commit，拿到的是完整的、当时能跑的状态，不会出现"只回退了一半"。

**`HEAD` 是"当前版本"的指针，`HEAD~1` 是上一个，`HEAD~2` 是上上个。** `HEAD~1` 和 `HEAD^` 等价（都是父提交）。

**hash 是一串 40 位十六进制，日常只用前 7 位。** `a1b2c3d` 就够了，git 会自动补全。写 `git show a1b2c3` 比写"上周三那版"可靠一万倍。

**提交信息写"为什么"，不写"改了什么"。** `git diff` 已经能告诉你改了什么；三个月后你想知道的是"当时为什么把 util 从 0.30 调到 0.40"。所以 `-m "util 0.30->0.40, 想压 congestion, 结果 DRC 爆炸"` 比 `-m "update pnr.tcl"` 有用得多。

:::term Commit | 提交（版本快照）
一次 commit 把暂存区的内容固化成历史里的一个节点，带一个 hash、一条说明、一个作者、一个时间。它是不可变的——要"撤销"不是删掉它，而是再加一个反向的 commit（`git revert`）。
:::

:::pitfall git checkout 会静默覆盖你没提交的改动
现象：`git checkout HEAD~1 -- pnr.tcl` 之后，你在这个文件里写了两小时还没提交的改动**全部消失**，没有任何提示、没有备份。

原因：这条命令的语义是"用历史版本覆盖工作区文件"，它不问你、也不留副本。

怎么避免：回退前先 `git status` 看清哪些文件有未提交改动；有的话先 `git commit` 或 `git stash`。已经覆盖了也不是完全没救：`git fsck --lost-found` 有时能捞到未提交的 blob，但别指望它。

判断依据：**任何 `git checkout <版本> -- <文件>` 都是破坏性操作**，和 `rm` 一个级别。新版 git 里 `git restore pnr.tcl` 做同样的事，风险一样。
:::

## 分支：拿来做参数实验最合适 {#branch}

后端的典型用法：**主线永远保持"能跑"，实验在分支上做。** 这不是软件工程的洁癖，是因为你的"实验"经常要跑一整夜，中途还可能改好几版。

```bash
# 作用：开分支做参数实验，好了合并、不好删掉
# 用法：在项目根目录执行
git branch                          # 看有哪些分支，* 是当前分支
git checkout -b exp_util40          # 新建并切到实验分支（等价 git switch -c）
# ... 在实验分支上把利用率改成 0.40，提交 ...
git checkout main                   # 切回主线（文件立刻变回 0.30 的样子）
git merge exp_util40                # 实验结果好，合并进主线
git branch -D exp_util40            # 结果不好，直接删掉，主线一点没脏
```

分支的本质是一个"指向某个 commit 的指针"，创建它几乎不花时间和空间。所以"随手开个分支试试"是零成本的，不开才是浪费。

三条分支纪律，能省掉大部分麻烦：

1. **一个分支只试一个变量。** `exp_util40` 里只改利用率，不要再顺手改时钟周期，否则结果好坏说不清是谁的功劳。
2. **分支名带参数值。** `exp_util40`、`exp_density07` 比 `test1`、`test2` 强太多——三个月后你还知道它在试什么。
3. **合并前先切回主线跑一次。** 有人合并完才发现主线跑不起来，而问题在三天前就引入了。

冲突（conflict）只在"同一个文件的同一行被两个分支改过"时出现。表现是文件里出现三段标记：

```
<<<<<<< HEAD
set_util 0.30
=======
set_util 0.40
>>>>>>> exp_util40
```

处理只有三步：手工把这段改成你要的内容（删掉三行标记）→ `git add 文件` → `git commit`。**不要用"随便选一边"的心态处理**，先想清楚这一行到底该是什么值。

:::term Branch | 分支
指向某个 commit 的可移动指针。切分支就是"把工作区换成那个 commit 的样子"，创建分支只是写一个几十字节的文件。

后端用它隔离实验：主线可靠，实验随便折腾，不好就删。
:::

:::tip 用 tag 标记"能签核的版本"
```bash
# 作用：给某个 commit 起一个不会变的名字
# 用法：签核通过、交付客户、流片前各打一个
git tag -a v1.0-drc0 -m "DRC clean, timing WNS -0.02"   # 带说明的标签
git tag                            # 列出所有标签
git show v1.0-drc0                 # 看这个标签指向哪次提交
```
`git tag v1.0-drc0` 之后，说"用 v1.0-drc0 那一版网表"就永远指向同一份文件；说"用上周三那版"永远会扯皮。**分支会随提交移动，tag 不会**——这是两者的关键区别。
:::

## 哪些东西不能提交进 git {#ignore}

后端目录里有大量"大且每次跑都变"的文件。提交进去，仓库会从几十 MB 变成几十 GB，而且**永远清不掉**（git 保留每一个历史版本的对象）。

```gitignore
# 作用：后端项目根目录的 .gitignore（注释必须单独成行，写行尾会让模式失效）
# 日志与报告：跑一次几百 MB
*.log
*.rpt

# 工具数据库：几个 GB，二进制，无法 diff
*.db
*.ndm
*.enc

# 运行目录
work/
run*/

# 寄生参数与时序文件
*.spef
*.sdf

# 交付物：单独归档到发布目录，不进 git
*.v.gz
*.gds

# 例外：这个日志要提交（必须写在 *.log 之后才生效）
!keep.log

# 开头加斜杠：只忽略仓库根目录下的 build，子目录里的同名目录不管
/build/
```

注意 `.gitignore` 的一个小陷阱：`#` 只有**单独成行**才是注释，写在模式后面会变成模式的一部分，`*.log  # 日志` 实际匹配的是"以 .log 开头的含 # 日志 的文件名"，等于什么都没忽略。所以上面每个注释都单独占一行。

判断标准一句话：**这个文件是"人写出来的"，还是"工具跑出来的"？** 人写的（脚本、约束、Makefile、README）要提交；工具跑的（日志、报告、数据库、网表）不提交。

算一笔账：一个 `.enc` 数据库 3GB，你一天提交 4 次，一周 20 次。如果它被跟踪，仓库一周涨 `3 × 20 = 60GB`，一个月 240GB——因为 git 不知道"这是同一份文件的新版本"，它只会老老实实存每一个对象。同事 clone 你的仓库要下 240GB，IT 会来找你。

已经提交进去的怎么办？`.gitignore` 对**已跟踪**的文件无效，必须先从索引里移除：

```bash
# 作用：把已跟踪的大文件移出 git，但保留磁盘上的文件
# 用法：先 git status 确认，再执行；记得提交这次移除
git rm --cached pnr.enc          # 只从索引移除，文件还在（不会真删）
git rm -r --cached run_1122/     # 目录同理
echo "*.enc" >> .gitignore       # 补上规则，防止下次又加进来
git commit -m "stop tracking .enc databases"
```

注意 `--cached` 不能省。省了就变成 `git rm`，磁盘上的文件也没了——在一个跑了 6 小时的运行目录上执行这条，会很痛苦。

:::pitfall git add . 把 3GB 数据库加进去了
现象：`git add .` 之后 `git status` 刷了几屏，`git commit` 卡了两分钟，之后每次 `git clone` 都要下几个 GB。

原因：`.` 表示"当前目录下所有未忽略的文件"。`.gitignore` 还没写，或者规则写错了（比如写了 `*.enc` 但文件叫 `.enc.gz`）。

怎么查：`git ls-files | xargs du -h | sort -h | tail` 看仓库里最大的几个文件；`git count-objects -vH` 看仓库总大小。

怎么改：`git rm --cached` 移除 + 补 `.gitignore`。如果已经推送过，历史里仍然有那个大文件，需要 `git filter-repo` 重写历史——那是另一个量级的操作，要跟全组打招呼。**所以规则要在第一次 add 之前写好。**
:::

## make：把三步流程变成一个命令 {#make}

真实项目不会让人记"先跑 dc 再跑 pnr 最后跑 pt"。用 `make` 管：顺序写死在文件里，没人会漏跑一步。

一条 make 规则由三部分组成：

```
目标(target): 依赖(prerequisites)
	命令(recipe)          ← 前面必须是一个 Tab
```

- **目标**：要生成的东西，或要执行的动作名（`syn`）。
- **依赖**：做这件事之前必须先完成什么（`pnr` 依赖 `syn`）。
- **命令**：怎么做的。一行一条，每行前面是 Tab。

```makefile
# 作用：三步流程的编排，一条 make 跑完综合→布局布线→签核
# 用法：放在项目根目录，文件名必须是 Makefile（或 makefile）
DESIGN  := soc_top
RUN_DIR := run_$(shell date +%Y%m%d_%H%M)   # := 只求值一次，整次 make 用同一个目录
SEED    := 1

.PHONY: all syn pnr signoff clean report    # 声明这些是"动作"不是文件名

all: signoff                                # 不带参数时 make，等于做到 signoff

syn:                                        # 综合
	@mkdir -p $(RUN_DIR)/syn                 # @ 表示不回显这条命令本身
	dc_shell -f scripts/dc.tcl 2>&1 | tee $(RUN_DIR)/syn/dc.log

pnr: syn                                    # 依赖 syn：没跑过就先跑 syn
	@mkdir -p $(RUN_DIR)/pnr
	cd $(RUN_DIR)/pnr && icc2_shell -f ../../scripts/pnr.tcl 2>&1 | tee pnr.log
# 注意：cd 必须和工具写在同一个"物理行"上（用 && 连），原因见下面的坑

signoff: pnr                                # 依赖 pnr
	@mkdir -p $(RUN_DIR)/sign
	pt_shell -f scripts/pt.tcl 2>&1 | tee $(RUN_DIR)/sign/pt.log

report: signoff                             # 从日志里抽关键指标
	@grep -E "Total number of DRCs|slack" $(RUN_DIR)/sign/pt.log > $(RUN_DIR)/summary.txt

clean:
	rm -rf run_*
```

用法：

```bash
# 作用：make 的四种调用方式
# 用法：在 Makefile 所在目录执行
make              # 跑 all（这里是 syn → pnr → signoff）
make pnr          # 只做到 pnr；make 发现 syn 没做过会自动先跑 syn
make -n pnr       # 空跑：只打印要执行的命令，不真跑（跑 6 小时前必做）
make -j4          # 允许 4 个任务并行（有依赖关系的仍然串行）
make clean        # 清掉所有 run_ 目录（危险，先看 -n）
```

三个容易忽略但很重要的细节：

**`:=` 和 `=` 的差别会毁掉一次运行。** `RUN_DIR := run_$(shell date ...)` 在 make 启动时求值一次，所有目标共用同一个目录。写成 `RUN_DIR = run_$(shell date ...)`，每次引用都会重新执行 `date`——syn 和 pnr 就会落到**两个不同的时间戳目录**，pnr 找不到 syn 的产出，报 `Cannot find netlist`。这种 bug 看起来像工具问题，其实是 Makefile 一行的问题。

**`@` 只是不回显命令，不影响执行。** `@mkdir -p` 让屏幕干净，日志里也不会出现这行；调试时把 `@` 去掉能看到完整命令。

**`make -n` 是免费的保险。** 它把要执行的每条命令打印出来但不执行。跑长流程前 `make -n` 看一眼，能发现路径写错、变量为空、目录不对——成本 1 秒，收益 6 小时。

:::term Makefile | 任务编排文件
一个文本文件，写着"哪个目标依赖哪些前置、用什么命令生成"。`make pnr` 会先检查 `pnr` 依赖的 `syn` 有没有做过，没做过就先做。

后端用它管流程顺序，好处是**顺序写死在文件里**，不会有人漏跑一步，也不需要每个人记命令。
:::

:::pitfall make 报 missing separator
现象：

```
Makefile:6: *** missing separator.  Stop.
```

原因：99% 是命令行前面用了**空格**而不是 **Tab**。Makefile 对缩进极其严格：规则下面的命令必须以一个 Tab 开头，四个空格不行。

怎么查：`cat -A Makefile | head -20`，Tab 显示成 `^I`，行尾显示成 `$`。看到命令那一行开头是四个空格而不是 `^I`，就是它。vim 里 `:set list` 也能看到。

怎么改：把那几行行首的空格换成一个真 Tab。注意很多编辑器默认"按 Tab 插入 4 个空格"，要关掉这个设置（vim：`:set noexpandtab`）。GNU make 3.82 以后可以用 `.RECIPEPREFIX = >` 把前缀改成别的字符，但公司里一律用 Tab，别自创。
:::

:::pitfall Makefile 里 cd 不生效，下一行还在原目录
现象：

```makefile
# 反例：cd 和工具分成两条命令，cd 对下一行无效
pnr:
	cd $(RUN_DIR)/pnr
	icc2_shell -f pnr.tcl
```

工具报 `Cannot open pnr.tcl`，而且产出文件出现在项目根目录，不是 `pnr/` 里。

原因：make 的**每条命令都在独立的 shell 里执行**。第一行的 `cd` 只影响那个 shell，shell 退出后目录就回来了。

怎么改：把 `cd` 和命令用 `&&` 连在同一条命令里：`cd $(RUN_DIR)/pnr && icc2_shell -f pnr.tcl`。或者用 `make -C 目录` 进入子目录再跑。
:::

## Makefile 的 Tab：一个字符让你查半小时 {#tab}

Tab 这个坑值得单独一章，因为它有三个特点：报错信息看不懂、肉眼看不出来、每个人都会踩一次。

先看现象和原因。make 解析规则时，判断"这一行是命令还是新规则"的唯一依据是**行首是不是 Tab**。看到 Tab 就把整行当成命令交给 shell；看到空格就以为还是规则的一部分，于是去里面找冒号，找不到就报 `missing separator`——"缺少分隔符"。这个措辞和"缩进错了"完全没关系，所以新人根本想不到。

三种查看方式，按方便程度排：

```bash
# 作用：三种看出 Tab / 空格的方法
# 用法：在 Makefile 所在目录执行
cat -A Makefile | head -20      # Tab 显示为 ^I，行尾是 $，一眼分辨
sed -n '10,20l' Makefile        # -l 选项：Tab 显示为 \t
grep -nP "^\t" Makefile         # 列出所有以 Tab 开头的行（GNU grep 支持 -P）
grep -nP "^    " Makefile       # 列出所有以 4 个空格开头的行——重点怀疑对象
```

vim 里用 `:set list` 打开可见字符，Tab 会显示成 `^I`；`:set list!` 关掉。更根本的办法是改 vim 配置：写 Makefile 时 `:set noexpandtab tabstop=8`，别让编辑器把 Tab 自动换成空格。

还有两个相关的坑，一并记住：

**从网页/文档里复制 Makefile 会丢 Tab。** 很多网页把 Tab 渲染成空格，你复制下来看着一样，但已经全是空格了。**永远不要从浏览器里复制 Makefile**，宁可照着重敲一遍。

**IDE 和 Git 也可能改掉 Tab。** 有些编辑器保存时"自动格式化"，或者在 `.editorconfig` 里配了 `indent_style = space`。团队里如果有人加了这种配置，Makefile 会在某次提交后突然坏掉——所以 Makefile 这种文件最好固定用 Tab，并在 review 时留意。

:::note 为什么 make 不改成用空格
因为 1976 年的 make 就是这么设计的，改成空格会让全世界几十亿行 Makefile 失效。工具可以改，生态改不动。这和 tcsh 还在用是同一个道理。
:::

## 日志归档：跑完必须知道是哪一版跑的 {#log}

一次 PR 跑 3 小时，一天跑 4 次。**如果日志都叫 `pnr.log`，第二天你不知道哪个是哪个。**

规矩：**每次运行一个带时间戳的目录，目录名里带上关键参数。**

```bash
# 作用：带时间戳和参数名的运行目录，日志同时进屏幕和文件
# 用法：在项目根目录执行；RUN 变量后面所有命令都用它
RUN=run_$(date +%m%d_%H%M)_util30        # 月日_时分 + 这次试的关键参数
mkdir -p $RUN/{log,rpt,db}               # 一次建三个子目录（花括号展开）

icc2_shell -f pnr.tcl 2>&1 | tee $RUN/log/pnr.log
# 2>&1 把错误并进标准输出，tee 同时写屏幕和文件
# 不写 2>&1 的话，工具报的 Error 只在屏幕上，日志里查不到

grep -E "Total number of DRCs" $RUN/log/pnr.log > $RUN/rpt/drc.txt
# 关键指标单独抽成小文件，两次对比时不用翻几万行
```

为什么目录名要带参数？因为**对比才是目的**。你跑 0.30 和 0.40 两版，看目录名就知道哪份是哪份；如果都叫 `run_1122_1915`，你得打开日志翻到第一行才知道。

为什么日志要 `tee`？两个需求同时存在：跑的时候你想看进度（屏幕），跑完你要留证据（文件）。只重定向到文件，你会盯着一个不动的终端怀疑它死了；只打屏幕，ssh 一断就全没了。

| 做法 | 解决什么 |
|---|---|
| 目录带时间戳（到分钟） | 一天跑十次也不覆盖 |
| 目录名带关键参数（util30） | 一眼看出这次试的是什么 |
| `2>&1` 后再接 `tee` | 屏幕看进度，文件留证据 |
| 指标单独抽到 `rpt/` | 对比两次结果不用翻全量日志 |
| 运行结束写一行 `DONE`/`FAIL` | 一眼看出这份日志跑完了没有 |

最后一条容易被忽略：日志末尾有没有明确的结束标记，决定了你能否在三十份日志里快速分出"跑完的"和"挂掉的"。在脚本最后加一句 `echo "[DONE] $(date)" >> $RUN/log/pnr.log` 就够了。

算一下空间：一次 PNR 的日志 400MB（典型值），一天 4 次 = 1.6GB，一周 5 天 = 8GB，一个月 32GB。所以归档还要配清理策略：`find run_* -maxdepth 0 -mtime +14 -exec rm -rf {} \;` 只留两周。**先确认哪些还被引用再删**——有人三个月后回来找某次失败的日志，是很常见的事。

:::note 2>&1 到底在干嘛
`2>&1` 的意思是"把标准错误（2 号）送到标准输出（1 号）当前指向的地方"。不加这一句，工具报的 Error 只显示在屏幕上，不会进日志——你事后查日志会发现"怎么没有报错"，其实报错根本没被记录。

顺序不能反：`2>&1 | tee` 对，`| tee 2>&1` 错。管道只接管标准输出，所以必须先把错误并进标准输出，再进管道。
:::

## 让结果自证：把版本写进运行目录 {#trace}

时间戳解决"什么时候跑的"，参数名解决"试的什么"，还差最后一个：**哪一版脚本**。答案不能靠记忆，要靠文件。

```bash
# 作用：把"这一次运行的完整身份"写进运行目录
# 用法：放在跑工具之前；$RUN 是运行目录
{
  echo "time    : $(date '+%Y-%m-%d %H:%M:%S')"
  echo "host    : $(hostname)"
  echo "user    : $(whoami)"
  echo "git     : $(git rev-parse --short HEAD)"      # 当前提交的短 hash
  echo "branch  : $(git rev-parse --abbrev-ref HEAD)" # 当前分支名
  echo "dirty   : $(git status --porcelain | wc -l) 个文件未提交"
  echo "tag     : $(git describe --tags --always)"
} > $RUN/version.txt

module list >& $RUN/env.txt      # 工具版本存档（bash 里写 2>&1，tcsh 里写 >&，效果相同）
cp pnr.tcl $RUN/pnr.tcl.used     # 把实际用的脚本也复制一份进去
```

四样东西，缺一不可：

1. **git hash** —— 精确到"哪一次提交"。有它就能 `git show` 出当时的全部文件。
2. **分支名** —— 万一两次运行用的是同名但不同分支的脚本，靠它区分。
3. **`dirty` 的数量** —— 最容易被忽略，也最要命。hash 只记录已提交的内容；如果你改了三个文件没提交就跑了，这份结果是"hash + 三个未提交改动"，只有 hash 是查不回来的。**所以规矩是：跑长流程之前先 commit。**
4. **工具版本** —— 同一个脚本在 2019 和 2021 版工具上跑，结果可能不同。`module list` 的输出就是证据。

`git describe --tags --always` 的输出形如 `v1.0-drc0-3-ga1b2c3`，读作"最近的标签是 v1.0-drc0，之后又提交了 3 次，当前是 a1b2c3"。这一串比单纯 hash 有信息量得多，交接时直接贴这句话就行。

再往前一步：把"这次运行的结论"也写回文件。跑完在 `$RUN/result.txt` 里写 `DRC=0 WNS=-0.02 AREA=1.23mm2`，下次对比时 `diff run_A/result.txt run_B/result.txt` 就够了，不用打开任何报告。

:::term Tag | 标签
给某个 commit 起的一个不会移动的名字，比如 `v1.0-drc0`。和分支的区别是：分支随新提交往前走，标签永远钉在那一个 commit 上。

用途：标记"能签核的版本""交付客户的版本""流片版本"。`git describe` 就是靠标签给出人类可读的版本描述。
:::

:::lab 动手：用 git 管住一次参数实验
**任务**：建一个仓库，在分支上把参数从 0.30 改到 0.40，对比差异，再退回主线。

```bash
# 作用：走一遍"主线 → 实验分支 → 对比 → 回退"的完整流程
# 用法：在 ~/demo/gitlab 下执行（没有就 mkdir -p）
mkdir -p ~/demo/gitlab && cd ~/demo/gitlab

git init -q                                  # 建仓库
git config user.name "student"               # 本地配置，只影响这个仓库
git config user.email "s@demo.local"

printf 'set_util 0.30\nset_density 0.70\n' > pnr.tcl   # 造一个"参数文件"
printf '*.log\nrun*/\n' > .gitignore                   # 一开始就写好忽略规则
git add pnr.tcl .gitignore
git commit -q -m "init: util 0.30, density 0.70"

git checkout -b exp_util40                   # 开实验分支
sed -i 's/0.30/0.40/' pnr.tcl                # 改一个参数
git commit -q -am "exp: util 0.40"
git diff main -- pnr.tcl                     # 看两个分支在这个文件上的差异

cat pnr.tcl                                  # 当前是 0.40
git checkout main                            # 切回主线
cat pnr.tcl                                  # 变回 0.30 —— 这就是"能退回"

mkdir -p run_1122 && echo "drc 156" > run_1122/pnr.log
git status --short                           # 什么都不显示：日志被 .gitignore 挡住了
```

**过关标准**：

1. `git log --oneline` 能看到两个提交，`git branch` 能看到 `* main` 和 `exp_util40`。
2. `git diff main exp_util40 -- pnr.tcl` 里只有 `set_util` 这一行不同（`0.30` → `0.40`）。
3. 在 `main` 上 `cat pnr.tcl` 是 0.30；`git checkout exp_util40` 后是 0.40。
4. 造一个 `run_1122/pnr.log`，`git status` 里**不出现**它（被 `.gitignore` 挡住了）。
:::

:::lab 动手：写一个只做三件事的 Makefile
**任务**：不装 EDA 也能验。用 `echo` 假装工具，验证依赖顺序、`-n` 空跑、Tab 规则。

```makefile
# 作用：最小可验证的 Makefile——只验证"顺序"和"目录"两件事
# 用法：make / make pnr / make -n / make clean
RUN := run_test

.PHONY: all syn pnr clean

all: pnr

syn:
	@mkdir -p $(RUN)/syn
	@echo "fake dc_shell -f scripts/dc.tcl" | tee $(RUN)/syn/dc.log

pnr: syn
	@mkdir -p $(RUN)/pnr
	cd $(RUN)/pnr && echo "fake icc2_shell" | tee pnr.log

clean:
	rm -rf run_*
```

**过关标准**：

1. `make` 的输出里，`fake dc_shell` 出现在 `fake icc2_shell` **之前**（依赖生效）。
2. `make -n pnr` 只打印命令、不创建任何目录。
3. `make pnr` 之后 `run_test/pnr/pnr.log` 存在（`cd` 生效了）。
4. 把 `syn:` 下面那行的 Tab 换成 4 个空格，`make` 报 `missing separator`——然后用 `cat -A` 找出来改回去。
:::

## 工作中怎么用：版本、流程、证据三件套 {#in-work}

**谁做**：每个后端工程师自己。没有人会替你 commit，也没有人会替你记"这次用的是哪版"。CAD 团队提供 Makefile 模板和目录规范，具体到每个项目、每次运行，责任在你。

**一天的标准动作**：

1. 早上 `git pull`，确认主线是最新的（多人项目）。
2. 改脚本前先 `git status` 确认工作区干净；不干净先 commit 或 stash。
3. 改完 `git diff` 看一眼，再 `git commit -m "为什么改"`。
4. 跑长流程用 `make`，别手敲三步。
5. 跑完把 `version.txt`、`result.txt` 一起留在运行目录里。
6. 实验结果好，`git tag` 标一下；不好，分支删掉。

**评审（review）会看什么**：提交信息有没有说清原因、Makefile 有没有 `-n` 验证过、运行目录里有没有版本信息。这三条决定了别人能不能复现你的结果。

**做错了会怎样**：最常见也最贵的错误是"没提交就跑了 6 小时，结果很好，但说不清用的是哪版脚本"。你只能重跑。第二贵的是"在主线直接改参数跑崩了，忘了原来是什么值"——有 git 的话 `git diff` 一秒解决，没有的话就只能猜。**git 的价值不在于它高级，而在于它把"我忘了"这个概率降到零。**

:::term Target | 目标（make 的规则名）
Makefile 里冒号左边那个名字，比如 `syn`、`pnr`。它可以是一个真实文件（`report.txt`），也可以是一个纯动作（`.PHONY` 声明过）。

`make 目标名` 执行对应规则；不带参数时执行第一个目标（惯例命名为 `all`）。
:::

:::quiz
`git add` 和 `git commit` 分别做了什么？|add 把改动放进暂存区（准备提交的清单），commit 把暂存区的内容固化成一个不可变的历史版本。
为什么日志要用 `2>&1 | tee log`，而不是 `> log`？|`> log` 只接标准输出，工具的报错会留在屏幕上不进文件；`2>&1` 先把错误并进标准输出，tee 再同时写屏幕和文件。
Makefile 报 `missing separator` 是什么原因，怎么查？|规则下面的命令行没有用 Tab 开头（用了空格）。用 `cat -A Makefile` 看 `^I`，或 vim 里 `:set list`。
为什么 `RUN_DIR := run_$(shell date ...)` 要用 `:=` 而不是 `=`？|`:=` 在 make 启动时求值一次，所有目标共用同一个目录；`=` 每次引用都重新求值，syn 和 pnr 会落到两个不同的时间戳目录，pnr 找不到 syn 的产出。
Makefile 里连续两行 `cd 目录` 和 `跑命令` 为什么不对？|每条命令在独立的 shell 里执行，`cd` 只影响那一行；必须写成 `cd 目录 && 跑命令` 放在同一条命令里。
哪些文件不该提交进 git？|工具跑出来的大文件：日志、报告、数据库（.db/.ndm/.enc）、SPEF/SDF、运行目录。人写的脚本、约束、Makefile 要提交。
`.gitignore` 对已经提交过的文件有用吗？|没用。要先 `git rm --cached 文件` 把它从索引里移除（磁盘文件保留），再提交，之后忽略规则才生效。
分支和 tag 的区别是什么？|分支是指针，会随新提交往前走；tag 钉死在某个 commit 上，用来标记"能签核的版本"，`git describe` 靠它给出可读版本号。
运行目录里为什么要记 `git status --porcelain` 的文件数？|hash 只代表已提交的内容。如果有未提交改动，这个结果就是"hash + 未知改动"，只有 hash 查不回来，所以跑长流程前要先 commit。
`make -n` 有什么用？|空跑，只打印将执行的命令而不执行。跑几小时的长流程前用它检查路径、变量、目录对不对，成本 1 秒。
:::

:::check
- 能说出 git 三层（工作区/暂存区/仓库）分别对应哪条命令，知道 commit 是整项目快照
- 知道 `git checkout <版本> -- <文件>` 会静默覆盖未提交改动，操作前先 `git status`
- 会用分支做单变量实验，能处理一次简单的合并冲突，会用 tag 标记签核版本
- 能写出针对后端目录的 `.gitignore`，知道已跟踪文件要 `git rm --cached`
- 能写含 `all/syn/pnr/signoff/clean` 的 Makefile，会用 `.PHONY`、`:=`、`-n`
- 遇到 `missing separator` 能立刻想到 Tab，并会用 `cat -A` 验证
- 能建 `run_日期_时分_参数` 目录，用 `2>&1 | tee` 留档，并把 git hash、分支、工具版本写进 `version.txt`
:::
