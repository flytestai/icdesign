---
id: 03-03-innovus-init
no: 27
stage: 3
title: init_design：把数据导进 Innovus，并证明它导对了
en: init_design: Importing Data into Innovus
hours: 2
minutes: 0
tags: [init_design, Innovus脚本, netlist, lef, mmmc, DEF, 报错排查, checkDesign]
summary: 数据准备的文件清单前面讲过，这一课讲怎么把它们真正喂进工具。对比脚本方式与 GUI 方式、逐段拆一份能跑的 init 脚本、说清 init_design 那一刻工具做了什么，然后给出导入后的五条验证检查和一张报错对照表——绝大多数"跑出来结果不对"的问题，都死在这一步没验干净。
---

## 两条路：脚本是主干，GUI 是拐杖 {#two}

:::goal 能默写一份 init 脚本的骨架（mmmc → lef → verilog+top → pwr/gnd → init_design）；能说出 init_design 内部五个动作，尤其是 link；能跑完五条验证检查并读懂异常信号；遇到 Cannot find cell、0 clocks defined、Unconnected power pin 能当场说出原因与修法。
:::

初始化一个设计，Innovus 给了两条路：

| | 脚本方式（推荐） | GUI 方式 |
|---|---|---|
| 怎么干 | 写一份 tcl，`innovus -files init.tcl` | 菜单 File → Import Design，一项项选文件 |
| 可重复性 | 完全可重复，改一行重跑 | 靠人记，第二次就配不一样 |
| 出错排查 | log 里全有，能 diff | 不知道哪一步点错了 |
| 团队协作 | 脚本进版本库，谁都能复现 | 别人无法复现你的环境 |
| 文档评价 | **主推** | **"一般不用，需要配置太多"** |

文档这句"一般不用，需要配置太多"是实话：GUI 的导入对话框有几十个输入项（lef 列表、lib 列表、verilog 列表、top cell 名、power/ground net 名、MMMC 文件……），**手点一遍比写十行脚本还慢，而且点漏一项工具不一定报错**。

所以本课只讲脚本。GUI 只有一个用处：**新手第一次搞不清哪个参数对应哪个文件时，点一遍看看它填什么，然后照着写脚本**。

## 数据清单：init 要喂进去什么 {#files}

先把清单摆全，缺一样都跑不起来：

| 类别 | 文件 | 作用 | 缺了会怎样 |
|---|---|---|---|
| 设计 | **netlist**（`.v.gz`） | 门级网表，逻辑连接 | 无设计可导 |
| 物理 | **tech lef** | 工艺层与规则 | 不知道能用哪些层、间距多少 |
| 物理 | **cell lef** | 每个单元的形状与引脚 | 所有单元都找不到 |
| 物理 | **def**（可选） | 已有布局，接着往下跑 | 从零 floorplan |
| 时序 | **lib** | 单元延迟功耗 | 算不出 cell delay |
| 时序 | **rc tech** | 线上寄生参数 | 算不出 net delay |
| 时序 | **sdc** | 约束（目标） | 不知道往哪优化 |
| 环境 | **viewDefinition.tcl** | MMMC 组合 | 只有默认一套环境 |
| 电源 | power/ground net 名 | 电源网络名 | 电源规划找不到网络 |

前八项的作用在 02-04 ~ 02-08 已经逐个讲过，这里只强调**两件工程上的事**：

:::tip 版本一致性，比文件齐全更重要
netlist v3、lef v2、sdc v1 混着用会怎样？工具**不会报错**，它会认真地给你算出一个数——只是这个数没有任何意义。

所以拿到一份新数据，第一件事是核对：**netlist 里 instance 的名字，能在 def 里找到；def 里的单元名，能在 cell lef 里找到；sdc 里的端口名，能在 netlist 的 top 上找到。** 三者对得上，才叫一套数据。
:::

:::tip power/ground 网络名必须问清楚
`VDD` / `VSS`？`VDD_CORE` / `VSS_CORE`？还是 `VDDPST` / `VSSPST`？**这个名字要以 netlist 为准**，不是随便写。

写错的后果：电源规划阶段工具找不到电源网络，打出来的 power mesh 是悬空的；或者它认为所有单元都没接电源，报一堆"unconnected power pin"。
:::

## 一份能跑的 init 脚本 {#script}

下面这份脚本是**最常见的写法**（`set init_*` 风格），几乎每个项目都能看到它的影子。逐段读：

```tcl
# ============ 第 0 段：基础设置 ============
setMultiCpuUsage -localCpu 16 -cpuAutoAdjust true   ;# 16 核，允许自动升降
setDesignMode -process 28                           ;# 告诉工具是 28nm 工艺，影响内部算法阈值
setLibraryUnit -time 1ns -cap 1pF                   ;# 统一时间与电容单位，与 lib 保持一致

# ============ 第 1 段：MMMC 环境 ============
set init_mmmc_file "scripts/viewDefinition.tcl"     ;# 多模式多端角配置，必须先指定
# 这一步会顺带读入 lib、rc tech 和所有 sdc，所以 lib 与 sdc 不用单独列

# ============ 第 2 段：物理库 ============
set init_lef_file {                                 \
    /pdk/tech/tech28.lef                            \
    /pdk/lib/stdcell_lvt.lef                        \
    /pdk/lib/memory_sram.lef                        \
    /pdk/lib/io.lef                                 \
}                                                   ;# 顺序无所谓，但 tech lef 一定要在里面

# ============ 第 3 段：网表与顶层 ============
set init_verilog "netlist/top_v3.v.gz"              ;# 门级网表，可以是列表（多个 .v）
set init_top_cell "top"                             ;# 顶层模块名，必须和 verilog 里 module 名一致
set init_design_uniquify 1                          ;# 自动给重复层次改名，避免同名冲突

# ============ 第 4 段：电源网络名 ============
set init_pwr_net "VDD"                              ;# 电源网络名，以 netlist 为准
set init_gnd_net "VSS"                              ;# 地网络名

# ============ 第 5 段：真正执行导入 ============
init_design                                         ;# 上面全是"配置"，这一行才真正干活

# ============ 第 6 段：接着吃已有的布局（block 流程常用）============
# defIn floorplan.def                               ;# 若从别人手里接过来的 def，在这里读入
```

几个必须说清的点：

**① 为什么 lib 和 sdc 没有单独列？** 因为 `init_mmmc_file` 指向的 `viewDefinition.tcl` 里已经用 `create_library_set` 和 `create_constraint_mode` 把 lib 和 sdc 都引用进去了。**这是最容易漏的一环**——只给了 lef 和 verilog，忘了 mmmc，工具照样能 `init_design` 成功，但它只有一套默认环境，lib 用的是猜的。

**② `set init_top_cell` 写错会怎样？** 网表里可能有十几个 module（顶层 + 各层子模块），工具不知道从哪个开始。名字写错就报 `Cannot find module 'xxx'`。

**③ `init_design` 之前所有 `set init_*` 都只是"记下来"**，不产生任何实际动作。所以顺序上，**所有配置必须在 `init_design` 之前**——写在它后面就完全无效，而且不会报错。

:::note 新版本还有一套 read_* 写法
```tcl
# 新一代写法：读什么就调什么，语义更直白
read_mmmc scripts/viewDefinition.tcl     ;# 读 MMMC（含 lib / rc / sdc）
read_physical -lef {tech28.lef stdcell_lvt.lef}  ;# 读物理库
read_netlist netlist/top_v3.v.gz         ;# 读网表
init_design                              ;# 最后统一建库
```
两套写法效果等价，**老项目多为 `set init_*`，新项目多用 `read_*`**。看到别人的脚本别慌，认得出是哪一套就行。
:::

## init_design 那一刻，工具做了什么 {#what}

:::term init_design | 初始化设计
Innovus 里把"配置"变成"真设计"的那一条命令：建库、链接、建层次、建时序图、挂约束，五件事一次做完。**执行它之前所有的 `set init_*` 都只是在记配置，不产生任何动作。**
:::

理解这一步干了什么，你就知道后面为什么会有那些报错：

1. **建库（build library）**：把 lef 里的形状信息、lib 里的时序信息合并成内存中的单元库；
2. **链接（link）**：把 netlist 里每个实例（instance）映射到库里的某个 cell。**找不到就是 link 失败**；
3. **建层次**：按 `init_top_cell` 展开层次树，处理重复名（uniquify）；
4. **建时序图**：把 net、pin、时钟关系建成图结构，供后面所有时序计算使用；
5. **挂约束**：把每个 view 的 sdc 挂到对应的分析环境上。

第 2 步是事故高发区。**link 失败的本质永远是"名字对不上"**：netlist 里叫 `NAND2_X1`，库里叫 `NAND2X1`（差一个下划线），就找不到。

:::term link | 链接
把网表里的每个实例映射到库（lef + lib）里的具体 cell。**link 成功 = 名字能对上**；link 失败无一例外是网表版本与 lef/lib 版本不匹配，或者少导入了某个 lef。
:::


## 导入成功怎么验证：五条检查 {#verify}

:::tip 关键认知
`init_design` **不报错** ≠ 导入成功。它经常"成功地"导入了一个缺库、缺约束、缺时钟的设计。**必须自己验。**
:::

```tcl
# 1. 设计概况：实例数、端口数、单元数——数量级对不上就是网表拿错了
report_summary

# 2. 设计规则体检：悬空输入、无驱动网络、多驱动、未连接电源
checkDesign -all

# 3. 约束体检：有没有时钟、有没有未约束的路径、有没有时序环路
check_timing

# 4. 时钟是否真的建上了：数量、名字、周期对不对
report_clocks

# 5. 全局时序概览：WNS/TNS 的量级是否合理（此时还没优化，差是正常的，差得离谱才是问题）
report_timing_summary
```

五条各自的判读标准：
| 检查 | 看什么 | 异常信号 |
|---|---|---|
| `report_summary` | instance 数、port 数 | 数量差一个量级 → 网表版本错 / top 选错 |
| `checkDesign` | unconnected、no driver、multi driver | 大量 no driver → 库缺 cell 或电源没接上 |
| `check_timing` | no_clock、unconstrained endpoint | `no_clock` 非零 → 时钟没建上，sdc 没生效 |
| `report_clocks` | 时钟列表 | 空列表 → mmmc 没读进来；周期不对 → sdc 版本错 |
| `report_timing_summary` | WNS / TNS | WNS 差几十 ns → 约束写错（比如周期少写一个 0） |

:::term 未约束路径 | unconstrained path
没有被任何时钟或 io delay 覆盖到的时序路径。工具**不会优化它，也不算进 WNS**——报告看起来"没问题"，实际是定时炸弹。`check_timing` 输出里的 unconstrained endpoint 计数就是查这件事。
:::

**这五条命令建议直接写进 init 脚本末尾**，每次跑完自动打印，不用靠人记。

:::pitfall 只看"没有 ERROR"就往下走
**现象**：跑完 floorplan、place、cts 一路顺畅，到 route 阶段突然发现某些单元根本不在库里的正确位置，或者时序报告里一半路径是 unconstrained。

**原因**：init 阶段漏了检查。工具对"缺 cell""缺时钟"这类问题往往只给 **warning**，不给 error——因为它允许你后面再补。

**代价**：错误在 init 埋下，要到 route 之后才暴露，那时**重跑一次要几小时到几天**。

**正确做法**：init 后**当场**跑完上面五条检查，把输出贴进 run 的记录里。这一步只花两分钟。
:::

## 报错对照表：init 阶段九成的问题都在这 {#errors}

| 报错/现象 | 原因 | 怎么修 |
|---|---|---|
| `Cannot find library 'xxx'` | mmmc 里 lib 路径写错，或文件不存在 | `ls` 确认路径；检查 viewDefinition.tcl 里的绝对路径 |
| `Cannot find cell 'NAND2_X1'` | link 失败：lef/lib 里没这个单元 | 比对 netlist 与 lef 的单元名；确认 lef 版本与网表匹配 |
| `Cannot find module 'top'` | `init_top_cell` 名与 verilog 的 module 名不一致 | `grep -n "^module" top.v` 看真实名字 |
| `0 clocks defined` | mmmc 没读进来，或 sdc 里没 `create_clock` | `report_clocks` 确认；检查 `init_mmmc_file` 路径 |
| `Library unit mismatch` | lef/lib 的单位与 `setLibraryUnit` 不一致 | 统一成 ns / pF，或去掉 setLibraryUnit 让工具自取 |
| `DEF version not supported` | def 版本比工具新 | 让上游用兼容版本导出，或用工具自带转换 |
| `Unconnected power pin` 大量出现 | power/ground 网络名写错 | `set init_pwr_net VDD` 按 netlist 实际名字改 |
| `Net xxx has no driver` | 网表本身残缺（综合时被优化掉/黑盒） | `checkDesign` 定位具体 net，找前端确认 |
| 跑得极慢，内存爆 | `-cpus` 给太高、或 lef 里带了几百个 macro | 降核数；确认 lef 只导入了需要的库 |

:::lab 跑一次 init，并留下证据
在真机环境里按下面步骤走一遍；模拟终端只演示命令语法。

```bash
# 1. 先确认四类文件都在，缺哪个当场就能看出来
ls -lh netlist/top_v3.v.gz
ls -lh /pdk/tech/tech28.lef /pdk/lib/stdcell_lvt.lef
ls -lh scripts/viewDefinition.tcl
grep -c "create_clock" scripts/func.sdc        # 确认 sdc 里有主时钟

# 2. 无界面启动 + 自动跑 init 脚本 + 写 log，一条命令搞定
innovus -no_gui -files scripts/init.tcl -log logs/init_v3.log -cpus 8

# 3. 跑完先看错误，再看警告，最后看五条检查的输出
grep -n "ERROR" logs/init_v3.log | head -20
grep -c "Warning" logs/init_v3.log
grep -n -A2 "report_summary\|check_timing\|report_clocks" logs/init_v3.log | head -40

# 4. 确认设计存下来了（下次可以 loadDesign 续跑，不用重新 init）
ls -lh DBS/top.enc
```

脚本末尾建议固定加上这几行（每次跑自动留证据）：

```tcl
# init 之后的五条体检，输出直接进 log
report_summary
checkDesign -all
check_timing
report_clocks
report_timing_summary

# 存库，下次用 loadDesign DBS/top.enc 直接续跑
saveDesign DBS/top.enc
```

验收标准：能报出实例数、时钟个数与主时钟周期、`check_timing` 里 unconstrained 端点数，并确认 log 中无 ERROR。
:::

:::quiz
为什么推荐脚本方式而不是 GUI 导入？| 脚本完全可重复、可进版本库、出错有 log 可查；GUI 输入项多、容易点漏且漏了不一定报错，别人无法复现。
init 脚本里为什么常常只列 lef 和 verilog，不单独列 lib 和 sdc？| 因为 `init_mmmc_file` 指向的 viewDefinition.tcl 里已经引用了 lib 与 sdc；但这也意味着漏了 mmmc 会导致没有时钟、只有默认环境。
`init_design` 之前和之后的 `set init_*` 有什么区别？| 之前是配置、之后才生效；写在 `init_design` 之后的配置完全无效且不报错。
init_design 内部的 link 是在做什么？link 失败的本质原因是什么？| 把 netlist 里每个实例映射到库里的具体 cell；失败本质是名字对不上（网表与 lef/lib 版本或命名不一致）。
为什么"init_design 不报错"不能算导入成功？| 工具对缺时钟、缺 cell 等问题常只给 warning，允许你后面补；错误会埋到 route 之后才暴露，重跑代价极大。
列出 init 后的五条验证检查。| report_summary、checkDesign -all、check_timing、report_clocks、report_timing_summary。
`report_clocks` 返回空列表说明什么？| MMMC 没读进来，或 sdc 里没有 create_clock，时序约束完全没生效。
`Library unit mismatch` 一般怎么修？| 统一时间/电容单位（如 ns、pF），或去掉 setLibraryUnit 让工具从 lib 自动获取。
:::

:::check
- 能说出脚本方式相对 GUI 的三个优势，并解释为什么 GUI 会漏项
- 能背出 init 需要的数据清单（netlist / tech lef / cell lef / lib / rc tech / sdc / mmmc / def / pwr-gnd 名）
- 能默写一份 init 脚本的骨架（mmmc → lef → verilog+top → pwr/gnd → init_design）
- 能解释 init_design 五个内部动作，尤其是 link
- 能列出五条验证检查及各自的异常信号
- 遇到 `Cannot find cell` / `0 clocks defined` / `Unconnected power pin` 能立刻说出原因与修法
- 知道用 saveDesign / loadDesign 保存与续跑
:::

:::note 接下来
init 之后再往下就是 floorplan（课表 10 学时）——决定芯片面积、摆 macro、打物理约束。在那之前，建议先把这一课的五条检查在实际数据上跑通一遍：**init 阶段埋的每个坑，都会在 floorplan 阶段以"面积不够""通道被堵"的形式再出现一次。**
:::
