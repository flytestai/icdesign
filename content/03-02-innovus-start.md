---
id: 03-02-innovus-start
no: 33
stage: 3
title: 启动 Innovus：版本、常用选项与帮助系统
en: Starting Innovus: Options and Help
hours: 2
minutes: 0
tags: [Innovus, 启动, -log, -files, -no_gui, -cpus, SetMultiCpuUsage, Tab, help]
summary: 从 Encounter/ICC 到 Innovus/ICC2 的换代原因讲起，然后真刀真枪地启动工具：怎么确认版本、九个最常用的启动选项（写 log、自动跑脚本、无界面、定时、多核、帮助、GUI 开关）、CPU 该给多少核以及为什么不能给太多、启动后怎么调核数，最后把界面分成四块认识一遍。
---

## 启动命令、核心数与任务队列 {#source-01}

:::note 资料来源
以下小节按《04 innovus项目(1).docx》原顺序收录。命令、用语及示例按原文保留；命令适用性以课程使用的工具版本与项目环境为准。
:::

:::source
"二、Innovus工具的使用"
"1）innovus的启动"
"启动命令：  innovus"
"启动的选项："
"1.1 自定义指定日志的前缀名  -log"
"innovus  -log   test_0125.log"
"1.2 启动之后运行指定的脚本 -files"
"innovus  -files   脚本路径"
"1.3 设置运行innovus的核心数 -cpus"
"innovus  -cpus  2"
"启动innovus之后如果需要改变核心数"
"setMultiCpuUsage -localCpu 2"
"公司的服务器是任务job提交的形式"
"会有一个job的id"
"查询job的id ：    bjobs   -w  |  grep  linux账号名"
"杀死不需要的job ：   bkill    job的id"
"bqueues 查看服务器集群使用情况"
:::

## 启动后生成的三个文件 {#source-02}

:::source
"2）启动产生的文件"
"innovus每次启动会产生3个文件"
"innovus.cmd   记录innovus使用过程中使用的命令"
"innovus.log     记录工具行为日志"
"innovus.logv   详细日志文件"
:::

## 快捷键与常用窗口 {#source-03}

:::source
"3）innovus的一些快捷键"
"z  放大"
"shift+z  缩小"
"u  回退操作"
"shift  + u  撤销回退"
"q  打开cell、net等任何对象的属性栏"
"f  恢复自动适应大小"
"shift+g   拆分模块group"
"g            合并模块"
"shift+R  可以移动object"
"使用尺子   k"
"删除尺子  shift+k"
"关闭尺子   a"
"关闭innovus     exit"
"一些常用窗口"
"做fp的工具箱"
:::

:::fig innovus-doc-02.png | 原文图 02 · 快捷键与常用窗口
:::

:::source
"设计的结构浏览"
:::

:::fig innovus-doc-03.png | 原文图 03 · 快捷键与常用窗口
:::

:::source
"查看vio的违例窗口，例如drc、short、power的问题"
:::

:::fig innovus-doc-04.png | 原文图 04 · 快捷键与常用窗口
:::

:::fig innovus-doc-05.png | 原文图 05 · 快捷键与常用窗口
:::

:::source
"定义global的power connect"
:::

:::fig innovus-doc-06.png | 原文图 06 · 快捷键与常用窗口
:::

## 保存和恢复设计数据 {#source-04}

:::source
"4) innovus的数据的保存和读取"
"saveDesign    保存路径/db名字.enc"
"保存完成会有两个文件"
"恢复数据"
"source    enc文件"
:::

:::fig innovus-doc-07.png | 原文图 07 · 保存和恢复设计数据
:::

:::source
"restoreDesign   enc.dat    当前tile名称"
:::

:::fig innovus-doc-08.png | 原文图 08 · 保存和恢复设计数据
:::

## 补充复习：原站课程内容 {#previous-material}

:::note 来源区分
以下为网站此前根据 PR 理论材料整理的补充内容；与上方本次上传的 Word 原文区分。
:::

## 为什么是 Innovus / ICC2 {#tools}

:::goal 能说出 Innovus/ICC2 各自替代的老工具与换代原因；能用一条命令完成"无界面启动 + 自动跑脚本 + 写 log"；能解释 -log / -files / -no_gui / -wait / -cpus 五个选项的真实语义与风险；能用 which、nproc、help *关键字* 三件事把环境摸清。
:::

| 时代 | Cadence | Synopsys | 适用工艺 |
|---|---|---|---|
| 老一代 | **Encounter** | **ICC** | 90nm 及以上 |
| 主流 | **Innovus** | **ICC2** | 65nm 及以下，28/16/7nm |

文档给的理由很实在：**"工艺越来越先进，原有的架构已经无法满足新的架构"**，具体对比就是**运行时间**。

老引擎的几个硬伤，在先进工艺下会直接暴露：

- 一次跑不完几十万 instance 的优化，跑一天还没到 route；
- 不支持多重曝光（double patterning）的染色约束；
- 时序/拥塞/功耗三者不能联合优化，只能一轮轮手调。

所以你在招聘要求里看到"熟悉 Innovus 或 ICC2"，指的是**这一代工具**；只会 Encounter/ICC，在 28nm 以下基本没有用武之地。本课程后面所有实操都用 Innovus。

## 第一步：启动与确认版本 {#start}

在 Linux 终端里，进入你的工作目录，直接敲工具名：

```bash
# 启动 Innovus（图形界面模式），前提是环境变量已由公司/学校的 module 或 cshrc 配好
innovus

# 如果提示 command not found，先用 which 确认工具在不在 PATH 里
which innovus
```

`which innovus` 的返回值一举两得，文档说得很清楚：**"结果会显示 innovus 所在目录以及 innovus 的版本"**：

```
/opt/cadence/INNOVUS201/innovus      ← 目录里带 201，说明是 Innovus 20.1 版本
```

**为什么第一件事是查版本？** 因为不同版本的命令行为有差异（尤其 `ccopt`、`setPlaceMode` 的参数），网上抄来的脚本报错，八成是版本不匹配。项目里也会明确要求"用 21.1 及以上"，出了问题才有人背书。

:::tip 环境没配好怎么办
三种常见情况：
1. `command not found` → PATH 没配，找 `source /xxx/setup.csh` 或 `module load innovus`；
2. 报 **license** 相关错误 → license 服务器不通或没有空闲 license，找 IT/管理员，不是你的脚本问题；
3. 启动卡在 `Loading...` 很久 → 磁盘 IO 慢或家目录配额满，`df -h ~` 看一眼。
:::

:::term license | 许可证
EDA 工具的授权凭证，按工具、按功能、**按核数**计量。启动失败里最常见的一类就是拿不到 license——它和脚本写错是两回事，先分清再排查。抢不到时可以带 `-wait` 排队等。
:::

:::term GUI | 图形界面模式
带版图窗口的运行模式（默认）。与之相对的 `-no_gui` 只跑命令、不加载图形引擎。**GUI 用来 debug，脚本用来干活**——这是 PR 工作的基本分工。
:::

## 九个常用启动选项 {#options}

文档列了九条，我按"一定会用到的程度"重排，并补上实际工作中的注意点。

### 1. `-log`：把这一趟的全部输出记下来 {#log}

```bash
# 启动时指定 log 文件名，工具的所有输出都会写进 test.log
innovus -log test.log
```

:::term log | 运行日志
记录这一趟运行中**所有**内容：你在界面上做的操作、输入的每条命令、命令的返回结果、warning 与 error。**它是唯一能事后追溯的证据。**
:::

为什么这条最重要？因为 Innovus 跑到一半崩了、或者同事问你"你昨天那个 run 到底怎么配的"，**只有 log 能回答**。文档原话："log 内容一般是界面做的操作，以及操作的结果，输入的 cmd 等等。"

实操约定：

- 文件名带版本和日期，比如 `-log pr_v3_1025.log`，别都叫 `innovus.log` 互相覆盖；
- 界面上的操作也会进 log，**所以你点过的每一步都能被还原成命令**——这是新人学命令最快的方法：点一遍，然后去 log 里看它对应哪条命令；
- 报错时先 `grep -n "ERROR" pr_v3_1025.log | head`，比在滚屏里找快一百倍。

### 2. `-files`：启动后自动跑脚本 {#files}

```bash
# 启动完成后自动执行 run.tcl，脚本跑完就停在那儿等你的命令
innovus -files run.tcl
```

文档的说明："脚本的内容可以自己定义，亦或是项目中的一些配置文件。"

这条是**自动化的入口**。实际项目里没人手点界面，都是：

```bash
# 无界面 + 自动跑 init 脚本 + 写 log：一条命令完成整个导入，扔后台等结果
innovus -no_gui -files scripts/init_design.tcl -log init.log
```

一条命令把"启动 → 导入数据 → 检查 → 退出"全做完，扔到后台跑。**这是 PR 工程师的日常姿势**，界面只是用来 debug 的。

:::tip -files 与 source 的区别
- `-files run.tcl`：**启动时就带上**，工具启动完立刻执行；
- 进去以后 `source run.tcl`：手动执行，随时可以再来一遍。

两者执行效果一样，区别只是时机。改脚本调试时用 `source` 反复跑，正式跑用 `-files`。
:::

### 3. `-no_gui`：不开图形界面，快得多 {#nogui}

```bash
# 无界面启动：只跑命令，不加载图形引擎
innovus -no_gui -files run.tcl -log run.log
```

**为什么值得单独记一条？** 图形界面会吃掉大量内存和启动时间（还要连 X server / VNC）。服务器上批量跑 run 时，`-no_gui` 能省下可观的内存，让同一个节点多跑几个 run。

进去了想再打开界面？文档给了答案：

```tcl
# 在 innovus 的命令行里输入，图形界面就出来了（前提是你有可用的显示环境）
win on
```

反过来，想临时关掉界面：

```tcl
# 关闭图形界面，回到纯命令模式
win off
```

:::pitfall 在 no_gui 里截图/开窗
**现象**：`win on` 报错，提示无法连接 display。
**原因**：`-no_gui` 启动的进程通常没有有效的 `DISPLAY` 环境变量（或者通过 ssh 没带 `-X`）。
**解决**：要么用 VNC/远程桌面登录后再启动（课程环境推荐），要么 `export DISPLAY=:1` 指向你已登录的桌面会话。远程纯 ssh 场景下就别指望开窗了，看 log 和报告文件即可。
:::

### 4. `-wait`：等 license 再启动 {#wait}

```bash
# license 被占满时，最多等 120 秒再启动
innovus -wait 120
```

文档叫它"定时启动"，实际语义是：**license 不够时排队等，而不是直接失败退出。**

这个功能在项目冲刺期特别有用——几十个人抢同一批 license，你的脚本半夜排队，等到就自动开跑。不带 `-wait` 的话，脚本会因为拿不到 license 直接死掉，白排一晚上。

### 5. `-cpus`：多核启动 {#cpus}

```bash
# 用 8 个核启动
innovus -cpus 8
```

文档的提醒非常关键：

> 实际工作根据需要确定核数，一般最高可以设置 32 或者 16。**不要设置过高，否则可能会被 kill。**

原因有两个，都要知道：

1. **license 是按核计费的**。你申请 32 核，可能消耗 32 份并行 license 额度，管理员看到会来找你；
2. **集群有空闲核数上限**（LSF/SGE 之类调度器会限制每用户/每任务的核数），超了直接被调度器 kill，跑了几小时的 run 白费。

文档还提到一个现场细节：**"可以看到有 28 个 cpu，每个 cpu 有 4 核"**——意思是物理机 28 路、每路 4 核。**看核数别只看 CPU 个数**，`nproc` 才是你能用的逻辑核数：

```bash
# 看这台机器到底能给我多少逻辑核
nproc

# 看物理 CPU 路数与每路核数
lscpu | grep -E "^CPU\(s\)|Thread|Core|Socket"
```

### 6. 启动后调整核数：SetMultiCpuUsage {#setcpu}

已经进去了才发现核给少了，不用退出重开：

```tcl
# 改成 32 核，并允许工具根据当前任务自动调整实际使用核数
setMultiCpuUsage -localCpu 32 -cpuAutoAdjust true
```

:::term setMultiCpuUsage | 多核使用设置
Innovus 里控制并行线程数的命令。`-localCpu` 指定本机可用核数，`-cpuAutoAdjust true` 让工具在不同阶段自动升降（比如 placement 用得多、report 用得少）。
:::

注意大小写：Innovus 的命令是**驼峰式**（`setMultiCpuUsage`、`setPlaceMode`、`optDesign`），而它内部很多底层命令是小写下划线式（`ccopt_design`、`place_opt_design`）。两种都存在，别以为敲错了。

### 7. `-help`：不知道参数就查 {#help}

```bash
# 看 innovus 本身有哪些启动选项
innovus -help

# 看某条命令的完整参数（在 innovus 命令行里执行）
ccopt_design -help
place_opt_design -help
```

**这是最省时间的习惯**：任何命令后面加 `-help`，立刻看到全部参数、默认值、示例。比翻文档快得多。

### 8. `help *关键字*`：按关键字搜命令 {#helpsy}

只记得"跟 place 有关"，不记得命令名？用通配符搜：

```tcl
# 搜索所有名字里带 place 的命令，会列出命令名和一行说明
help *place*

# 搜索所有时序报告相关的命令
help *report*

# 看某条命令的详细解释（等价于 cmd -help）
help setPlaceMode
```

:::tip 三个帮助入口的分工
| 入口 | 用来查 |
|---|---|
| `innovus -help` | 启动选项（`-log` `-files` `-cpus` 这些） |
| `cmd -help` | 某条命令的完整参数表 |
| `help *kw*` | 只记得关键字，找命令名 |
:::

### 9. Tab 键补全 {#tab}

文档把"TAB 键"单独列成一条，因为它真的能救命：

- 敲 `setPlace` + Tab → 自动补成 `setPlaceMode`；
- 敲 `setPlaceMode -` + Tab → **列出所有可用参数**；
- 路径也能补：`source scr` + Tab → `source scripts/`。

**养成"敲一半就按 Tab"的习惯**，能避掉大量拼写错误。Innovus 命令长、驼峰多，手打几乎必错。

## 界面分四块认识 {#gui}

启动后（不带 `-no_gui`）你会看到一个典型的三段式布局，先认地方再学操作：

```
┌────────────────────────────────────────────────────────────┐
│  菜单栏 File / Edit / View / Design / Timing / ...          │
├──────────────────────────────────────────────┬─────────────┤
│                                              │  右侧面板    │
│           版图显示区（Layout View）           │  ├ Design   │
│                                              │  ├ Physical │
│   · 左边是 Design Browser（层次树）           │  └ Timing   │
│   · 中间是芯片版图，滚轮缩放、中键平移         │             │
│                                              │             │
├──────────────────────────────────────────────┴─────────────┤
│  命令行（Command Line）：所有 Tcl 命令在这里敲               │
├────────────────────────────────────────────────────────────┤
│  输出窗（Log / Console）：命令的返回、warning、error 都在这 │
└────────────────────────────────────────────────────────────┘
```

四个地方必须会用：

1. **版图区**：`f` 键 fit 全图，滚轮缩放，中键拖动平移。**看图先 fit 一次**，不然你可能在某个角落放大到看不见全局。
2. **命令行**：所有操作都能在这里敲。**界面点一遍，然后去 log 里抄命令**，是学命令最快的路。
3. **输出窗**：warning 和 error 在这里滚。**别忽略 warning**，很多"结果莫名其妙"的根因就藏在几百行 warning 里。
4. **Design Browser**：层次结构树。找某个 instance、某个 net 就从这里搜。

:::lab 启动一次，把九个选项过一遍
在课程环境的终端里（真机或模拟终端均可，`innovus` 相关命令在模拟终端里只会演示语法）：

```bash
# 1. 确认工具在哪、什么版本——这是每次上机的第一个动作
which innovus

# 2. 看启动选项全表，找到 -log / -files / -no_gui / -wait / -cpus 五条
innovus -help | head -40

# 3. 看本机有多少逻辑核，决定 -cpus 给多少（别超过这个数）
nproc

# 4. 用带 log 的无界面方式跑一个空脚本，验证自动化链路通不通
echo "puts \"innovus is ready\"" > run.tcl
innovus -no_gui -files run.tcl -log run.log -cpus 4

# 5. 跑完检查 log 里有没有 ERROR
grep -n "ERROR" run.log | head
```

进去以后在命令行里再敲这三条：

```tcl
# 看 place 相关命令有哪些（帮助系统按关键字搜）
help *place*

# 把核数调成 8 并开启自动调整
setMultiCpuUsage -localCpu 8 -cpuAutoAdjust true

# 打开图形界面看版图区（需要有显示环境）
win on
```

验收标准：能报出工具版本、本机逻辑核数、`-log` 与 `-files` 的作用差别，并成功用一条命令完成"启动→跑脚本→写 log"。
:::

:::quiz
Innovus 与 ICC2 分别属于哪家公司？它们替代的老工具是什么？| Innovus 是 Cadence 的，替代 Encounter；ICC2 是 Synopsys 的，替代 ICC。老一代适用于 90nm 以上，先进工艺必须用新一代。
为什么每次上机第一件事是 `which innovus`？| 它同时给出工具所在目录和版本号；版本不同命令行为有差异，脚本报错常因版本不匹配。
`-log` 和 `-files` 分别做什么？| `-log` 把这一趟的所有输出（界面操作、输入命令、结果、warning/error）写进指定文件；`-files` 让工具启动后自动执行指定 tcl 脚本。
`-no_gui` 有什么好处？进去后怎么再打开界面？| 省内存、省启动时间，适合服务器批量跑 run；进去后执行 `win on` 打开，`win off` 关闭。
`-cpus` 为什么不能设太高？| 会消耗大量并行 license，且可能超过集群每任务核数上限被调度器 kill，导致长时间 run 白跑。
进去之后怎么改核数？| `setMultiCpuUsage -localCpu 32 -cpuAutoAdjust true`。
想找所有名字里带 place 的命令，怎么做？| `help *place*`；看某条命令的完整参数用 `cmd -help`；看启动选项用 `innovus -help`。
Tab 键有两个什么用法？| 补全命令/路径名；在命令后加空格再按 Tab 列出该命令的所有可用参数。
:::

:::check
- 能说出 Innovus/ICC2 对应替代的老工具，以及换代的核心原因（运行时间与先进工艺约束）
- 能用一条命令完成"无界面启动 + 自动跑脚本 + 写 log"
- 能解释 `-wait` 的真实语义（license 排队）
- 能说出 `-cpus` 给太高会被 kill 的两个原因
- 能用 `which` / `nproc` / `lscpu` 三个命令确认环境
- 能说出三个帮助入口各自查什么
- 能把界面分成版图区、命令行、输出窗、层次树四块并说出各自用途
:::
