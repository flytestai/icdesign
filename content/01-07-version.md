---
id: 01-07-version
no: 08
stage: 1
title: 版本管理与自动化：git、make 和日志归档
en: Version Control & Automation for Backend Engineers
hours: 4
minutes: 42
tags: [git, make, 脚本, 自动化, 日志]
summary: 后端工程师一天改二十次脚本，改错了必须能退回；跑一次几小时，跑完必须知道哪个版本跑的。这一课讲 git 最小命令集、make 三步流水线、以及用时间戳目录归档结果。
---

## 为什么后端工程师必须会 git {#why}

先看一个真实场景：

:::scene 改参数改崩了，想回到昨天
周三你把 `pnr.tcl` 里的利用率从 0.30 改到 0.40，跑了一夜，DRC 从 0 变成 1874。你想回到 0.30 那一版——但你手上只有 `pnr.tcl`、`pnr.tcl.bak`、`pnr_new.tcl`、`pnr_new2.tcl`、`pnr_final.tcl`，**不知道哪个是 0.30**。

有 git 的话，一条命令：`git checkout HEAD~1 -- pnr.tcl`。
:::

:::term Git | 版本管理工具
记录"每次改了什么、谁改的、为什么改"的工具。每个版本是一个 **commit（提交）**，可以随时回到任意一个历史版本。

后端用它主要做三件事：**回退**（改坏了退回去）、**对比**（这版和上版差在哪）、**交接**（别人接手能看懂历史）。
:::

## git 最小命令集（够用 90% 的场景）{#basic}

先建立一个概念：git 有三层。

| 层 | 英文 | 是什么 | 对应命令 |
|---|---|---|---|
| 工作区 | working tree | 你现在正在编辑的文件 | 直接用编辑器改 |
| 暂存区 | staging area / index | "这次要提交哪些改动"的清单 | `git add` |
| 仓库 | repository | 已保存的历史版本 | `git commit` |

```bash
# ---- 第一次：初始化 ----
git init                          # 在当前目录建一个仓库（生成 .git/）
git config user.name  "weizhen"   # 提交记录里显示的名字（只需设一次）
git config user.email "w@x.com"

# ---- 日常：改完文件，提交 ----
git status                        # 看哪些文件改了（红色=未暂存，绿色=已暂存）
git diff                          # 看具体改了哪几行（最重要的命令之一）
git add pnr.tcl                   # 把这个文件放进暂存区
git commit -m "util 0.30->0.40, DRC 0->1874"   # 存成一个版本

# ---- 看历史 ----
git log --oneline                 # 一行一个版本，带 hash（版本号）
git show a1b2c3                   # 看某个版本具体改了什么

# ---- 回退 ----
git checkout HEAD~1 -- pnr.tcl    # 只把 pnr.tcl 退回上一个版本（别的文件不动）
git revert a1b2c3                 # 生成一个"反向提交"，把那次改动撤销（推荐，历史保留）
```

:::pitfall `git checkout` 会覆盖你现在的改动
`git checkout HEAD~1 -- pnr.tcl` 是**直接覆盖**，你在这个文件里没提交的改动会**永久丢失**，没有任何提示。

正确姿势：回退前先 `git status` 看清楚，或者先 `git stash`（把当前改动暂存起来）再操作。这是新人最常哭着来问的一条。
:::

:::term commit | 提交（一个版本快照）
一次 commit 保存的是"整个项目在这一刻的样子"，不是"这次改的那几行"。所以回到任意 commit，你拿到的是完整的、当时能跑的状态。

提交信息（`-m` 后面的字）要写**为什么改**，不是"改了 pnr.tcl"。三个月后你只记得原因，不记得文件名。
:::

## 分支：拿来做参数实验最合适 {#branch}

后端的典型用法：**主线保持能跑，实验在分支上做**。

```bash
git branch                          # 看有哪些分支，* 是当前分支
git checkout -b exp_util40          # 新建并切到实验分支
# ...在实验分支上把利用率改成 0.40，提交...
git checkout main                   # 切回主线（文件立刻变回 0.30 的样子）
git merge exp_util40                # 如果实验结果好，合并进主线
git branch -D exp_util40            # 如果不好，直接删掉，主线一点没脏
```

| 场景 | 怎么做 |
|---|---|
| 试一个新参数，不确定好不好 | 开分支，跑完看结果，不好就删 |
| 线上流程突然崩了，要紧急修 | 从能跑的 tag 拉一个 `hotfix` 分支 |
| 交接给同事 | 让他 `git log --oneline` 看你的提交信息 |

:::tip 用 tag 标记"能签核的版本"
`git tag v1.0-drc0` 给当前版本起一个不会变的名字。以后说"用 v1.0-drc0 那一版网表"，比说"用上周三那版"靠谱得多。
:::

## 哪些东西不能提交进 git {#ignore}

后端目录里有很多"大且会变"的东西，提交进去会让仓库变成几个 GB。

```bash
# .gitignore：列在这儿的文件，git 一律不管
*.log                # 日志，跑一次几百 MB
*.rpt                # 报告，每次跑都变
*.db *.ndm *.enc     # 二进制数据库，大且无法对比
work/  run*/         # 运行目录
*.spef *.sdf         # 寄生与延时文件，体积大
```

判断标准：**这个文件是"人写出来的"，还是"工具跑出来的"？** 人写的（脚本、约束、Makefile）要提交；工具跑的（日志、报告、数据库）不提交。

例外：**最终的交付物**（GDS、最终网表、签核报告）不进 git，但要单独归档到发布目录，并记录版本号。

## make：把三步流程变成一个命令 {#make}

真实项目不会让人记"先跑 dc 再跑 pnr 最后跑 pt"。用 `make` 管：

```makefile
# Makefile  —— 注意：命令行前面必须是 Tab，不是空格（这是 make 最大的坑）
DESIGN  := ipa_top
RUN_DIR := run_$(shell date +%Y%m%d_%H%M)

.PHONY: all syn pnr signoff clean      # 声明"这些不是文件名，是动作"

all: syn pnr signoff                   # make 不带参数时，依次做这三步

syn:                                   # 综合
	@mkdir -p $(RUN_DIR)/syn
	dc_shell -f scripts/dc.tcl 2>&1 | tee $(RUN_DIR)/syn/dc.log

pnr: syn                               # 布局布线依赖综合（make 会自动先跑 syn）
	@mkdir -p $(RUN_DIR)/pnr
	cd $(RUN_DIR)/pnr && icc2_shell -f ../../scripts/pnr.tcl 2>&1 | tee pnr.log

signoff: pnr                           # 签核依赖 pnr
	@mkdir -p $(RUN_DIR)/sign
	pt_shell -f scripts/pt.tcl 2>&1 | tee $(RUN_DIR)/sign/pt.log

clean:
	rm -rf run_*
```

用法：

```bash
make            # 跑全流程
make pnr        # 只跑到布局布线（make 会自动先做 syn）
make clean      # 清掉所有运行目录
```

:::term Makefile | 任务编排文件
一个文本文件，里面写着"哪个任务依赖哪个任务、执行哪条命令"。`make pnr` 会先检查 `pnr` 依赖的 `syn` 有没有做过，没做过就先做。

后端用它管流程顺序，好处是**顺序写死在文件里**，不会有人漏跑一步。
:::

:::pitfall make 报 `missing separator`
```
Makefile:6: *** missing separator.  Stop.
```

99% 是因为命令行前面用了**空格**而不是 **Tab**。Makefile 对缩进极其严格：规则下面的命令，必须用一个 Tab 开头。

在 vim 里按 `:set list` 能看到 Tab 显示为 `^I`，一眼就能查出来。
:::

## 日志归档：跑完必须知道是哪一版跑的 {#log}

一次 PR 跑 3 小时，一天跑 4 次。**如果日志都叫 `pnr.log`，第二天你不知道哪个是哪个。**

规矩：**每次运行一个带时间戳的目录**。

```bash
# 建目录：日期_时分 + 一句话说明
RUN=run_$(date +%m%d_%H%M)_util30
mkdir -p $RUN/{log,rpt,db}

# 跑的时候同时输出到屏幕和文件（tee = 分叉）
icc2_shell -f pnr.tcl 2>&1 | tee $RUN/log/pnr.log

# 关键信息单独抽出来，方便对比
grep -E "Total number of DRCs" $RUN/log/pnr.log > $RUN/rpt/drc.txt
```

| 做法 | 好处 |
|---|---|
| 目录带时间戳 | 一天跑十次也不会互相覆盖 |
| 目录名带关键参数 | 一眼看出这次试的是什么（util30） |
| `2>&1 \| tee` | 屏幕能看进度，文件能事后查 |
| 单独抽 DRC/时序到小文件 | 对比两次结果时不用翻几万行日志 |

:::note `2>&1` 到底在干嘛
`2>&1` 的意思是"把标准错误（2）也送到标准输出（1）去"。不加这一句，工具报的 **Error 只会显示在屏幕上，不会进日志文件**——你事后查日志会发现"怎么没有报错"，其实报错根本没被记下来。

顺序不能反：`2>&1 | tee` 对，`| tee 2>&1` 错。管道只接管标准输出，所以必须先把错误并进标准输出，再进管道。
:::

:::lab 动手：在模拟终端里做一个"带时间戳的运行目录"
模拟终端里跑这一段（`tee` 不支持时用重定向代替，效果一样）：

```bash
cd ~
mkdir -p run_1122_2014/log
echo "iteration 1 DRC 6000" > run_1122_2014/log/pnr.log
echo "iteration 2 DRC 156"  >> run_1122_2014/log/pnr.log
cat run_1122_2014/log/pnr.log | grep DRC | tail -1

ls run_1122_2014/log
```

预期最后一行输出：`iteration 2 DRC 156`。

再过关一步：把日志里 DRC 的数字单独抽出来

```bash
awk '{print $4}' run_1122_2014/log/pnr.log
```

预期输出两行：`6000` 和 `156`。这就是"从日志里抽指标"的最小动作，真实项目里每天要做几十次。
:::

:::check
- 能说出 git 三层（工作区 / 暂存区 / 仓库）分别对应哪条命令
- 知道 `git checkout -- file` 会覆盖未提交改动，回退前先 `git status`
- 能写出一个含 `syn/pnr/signoff` 三个目标、带依赖关系的 Makefile
- 知道 Makefile 命令行必须用 Tab
- 能给每次运行生成 `run_日期_时分_说明` 目录，并用 `2>&1 | tee` 同时留屏和留档
:::

:::quiz
`git add` 和 `git commit` 分别做了什么？|add 把改动放进暂存区（准备提交的清单），commit 把暂存区的内容存成一个不可变的历史版本。
为什么日志要用 `2>&1 | tee log`，而不是 `> log`？|`> log` 只接标准输出，错误信息会丢在屏幕上不进文件；`2>&1` 先把错误并进标准输出，tee 再同时写屏幕和文件。
Makefile 报 missing separator 是什么原因？|规则下面的命令行没有用 Tab 开头（用了空格）。Makefile 对缩进要求是硬性的。
为什么日志目录要带时间戳和参数说明？|一天多次运行会互相覆盖；带时间和参数能立刻知道"这份结果是哪一版、试的什么"，对比和回溯才有意义。
哪些文件不该提交进 git？|工具跑出来的大文件：日志、报告、数据库（.db/.ndm/.enc）、SPEF/SDF。人写的脚本和约束要提交。
:::
