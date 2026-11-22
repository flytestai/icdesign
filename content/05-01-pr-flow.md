---
id: 05-01-pr-flow
no: 32
stage: 5
title: 28nm 全流程（一）：把 PR 串成项目
en: 28nm PR Flow
hours: 4
minutes: 40
tags: [流程, 28nm, 交接]
summary: 前面学的是"每个阶段怎么做"，这一课讲"怎么把它们串成一条不会断的流水线"：目录怎么分、每步产物叫什么、通过标准是什么、怎么交接给 PT、跑批脚本怎么写才能失败即停、断点续跑。
---

## PR 阶段的项目视角 {#project}

:::goal 学完这一课，你能为一个 28nm 项目搭出可回溯的目录和脚本骨架，说清每个阶段的产物与通过标准，并把一套"网表 + SPEF + SDC + 报告 + 脚本版本"完整交给 STA。
:::

单机跑通一个设计，靠的是"我记得刚才点了什么"。项目里跑一个设计，靠的是"任何人拿到的目录，都能复现出同样的结果"。

这两件事的差别，像**装修工人**和**装修项目经理**：

- 工人关心"这面墙怎么刷平"——对应 floorplan 怎么摆、CTS 怎么调。
- 项目经理关心"水电什么时候进场、瓷砖什么时候到、验收单谁签"——对应每个阶段的输入输出、交接物、通过标准。

后端工程师在项目里，一半时间是在做项目经理的事：**管交付物**，而不是敲命令。命令敲错可以重跑，交付物管错会让下游白干一周。

先把自己在这条流水线里的位置钉死——后端管的是中间那一段：

:::fig flow-overview | 全流程图：左边灰色虚线框是前端做完交给你的东西，右边蓝色框是后端的各个阶段直到交付。本课关心的是"怎么把 PR 这几步串成项目"——每一步的输入从哪来、产物交给谁、通过标准是什么。
:::

从图里要看出什么：**PR 的交付物不是给自己看的，是给右边 STA、PV 接力的**。后面目录、命名、交接的所有规矩，都是为了让这条接力不断棒。

:::scene 一次交接会，三个问题全答不上来
周五下午，STA 工程师来要数据："你们 PR 这版跑完了吗？给我网表、SPEF 和 SDC。"

你打开 `pnr/out/`，里面有 `final.v`、`final.spef`、`final.sdc`，还有 `final_v2.v`、`final_old.spef`。你也不知道哪个是最后一版。

STA 问了三句话：

1. "这三个文件是同一次导出的吗？"
2. "SPEF 对应的是哪次布线？"
3. "PR 用的约束和你要给我的这份，是同一个版本吗？"

你答不上来。STA 只能说："那我先不跑，你确认完再给我。"

一个下午没了。**这就是"会跑流程"和"能交付"的差距。**
:::

:::term Run Directory | 运行目录
每次跑流程新建一个带时间戳的目录（如 `run/20261122_1400/`），里面放本次的脚本副本、日志、报告、结果。它回答"三天前那版是怎么跑的、结果是什么"。
:::

:::term Handoff | 交接
把一套完整、自洽、可复现的数据交给下游（STA、PV、封装）。"自洽"是关键：网表、SPEF、SDC 必须来自同一次运行。
:::

:::term Checkpoint | 检查点
每个阶段结束时留下的"可回退状态"：数据库存盘 + 报告 + 日志 + 一个标记文件。出问题时从最近的检查点重跑，而不是从零开始。
:::

:::term Manifest | 清单文件
一次运行结束时生成的文本清单：工具版本、库版本、脚本 git 版本、输入文件校验和、各阶段产物路径、关键指标。它是这次运行的"身份证"。
:::

单机练习和真实项目的差别，逐条列出来：

| 单机练习 | 真实项目 | 不管的后果 |
|---|---|---|
| 一个目录随便放 | 按阶段/日期分目录 | 找不到三天前那版 |
| 脚本改完就覆盖 | 脚本进 git，每次记录 commit | 无法复现结果 |
| 跑完看屏幕 | 每步固定格式报告存档 | 出问题没有证据 |
| 一个人跑 | 交接给别人能复现 | 请假三天项目停摆 |
| 失败了从头再来 | 断点续跑 | 一次小错重跑一天 |

**算一笔时间账**：一个万门设计全流程约 22 分钟，十万门约 6~10 小时。如果因为"没存盘"从第一步重跑，损失的是整轮时间；如果因为"网表和 SPEF 不同步"被 STA 退回，损失的是**两个人**的一轮时间。而每步存盘只要几十秒。

## 推荐目录结构 {#tree}

```
proj/28nm/
├── rtl/                       # RTL 源码，只读；PR 不改，出问题找前端
├── syn/
│   ├── scripts/               # 综合脚本
│   ├── netlist/ipa_top.v      # ← PR 的输入（综合后的门级网表）
│   └── reports/               # 综合的时序/面积报告，PR 对照用
├── pnr/
│   ├── scripts/
│   │   ├── 00_setup.tcl       # 变量、路径、库版本，所有脚本都 source 它
│   │   ├── 01_init.tcl        # 读库、读网表、读约束
│   │   ├── 02_floorplan.tcl   # 边界、宏、row
│   │   ├── 03_power.tcl       # 电源环、电源条、PG 连接
│   │   ├── 04_place.tcl       # 布局 + 预 CTS 优化
│   │   ├── 05_cts.tcl         # 时钟树
│   │   ├── 06_route.tcl       # 布线 + 后优
│   │   └── 07_finish.tcl      # filler、导出、最终报告
│   ├── db/                    # 每阶段存盘：01_init.enc ... 07_finish.enc
│   ├── out/                   # 交付物：def / v / spef / sdc
│   ├── rpt/                   # 每阶段报告
│   └── log/                   # 每阶段日志
├── sta/
│   ├── scripts/               # PrimeTime 脚本
│   └── reports/
├── pv/                        # DRC / LVS
└── run/
    └── 20261122_1400/         # 本次运行的完整现场（软链到上面各目录）
```

这张目录图上的规矩，比目录本身更重要：

:::fig pr-dir | 推荐的项目目录结构，右边是四条配套规矩。重点看第一条：脚本要能从头重跑——左边目录树里的 scripts/、db/、run/ 怎么分，全是围绕这一条服务的。
:::

从图里要看出什么：**目录是给别人的接口**。STA 找 out/，接手人找 scripts/ 和 run/latest，评审找 rpt/——每个人都能在固定位置拿到固定东西，这个项目才接得住。

每个目录放什么、谁能删，必须写清楚：

| 目录 | 放什么 | 谁写 | 谁读 | 能不能删 |
|---|---|---|---|---|
| `rtl/` | RTL 源码 | 前端 | 综合、验证 | 不能，只读 |
| `syn/netlist/` | 门级网表 | 综合 | PR | 不能，按版本保留 |
| `pnr/scripts/` | 分阶段 Tcl | PR | PR、接手人 | 不能，进 git |
| `pnr/db/` | 阶段存盘 | PR | PR | 只保留最近 2~3 版 |
| `pnr/out/` | 交付物 | PR | STA、PV、封装 | 按版本保留 |
| `pnr/rpt/` | 报告 | PR | PR、review | 随 run 目录保留 |
| `pnr/log/` | 日志 | 工具 | 所有人 | 至少留到项目结束 |
| `run/<时间戳>/` | 本次现场 | 脚本 | 追溯 | 项目结束前不删 |

**脚本按阶段编号**，是整个结构的关键。想重跑"从 CTS 开始"，只要 `restoreDesign db/04_place.enc` 再跑 05、06、07，不用从头来。

编号还有一个隐性好处：**看文件名就知道依赖顺序**。`05_cts.tcl` 一定在 `04_place.tcl` 之后，新人不用问人。

`scripts/` 和 `db/` 一定要分开，而且 `db/` 不进 git。脚本是文本、要版本管理、要 review；数据库是二进制、动辄几百 MB、每次跑都变。把 `.enc` 提交进 git，仓库几天就爆了。正确做法是脚本进 git，数据库靠 run 目录和 manifest 追溯。

`run/latest` 是一个软链，不是副本。它让你永远能一句 `cd run/latest` 找到最近一次，而不必记时间戳；但它也意味着**删 run 目录前要先确认 latest 指向哪**。软链指向已删除的目录时，`ls` 会报 "No such file or directory"，这是新手常见的惊吓。

:::pitfall 脚本互相 source，改一个变量全崩
现象：`00_setup.tcl` 里改了 `DESIGN` 名字，跑到 `03_power.tcl` 报找不到网表。

原因：有的脚本用 `$DESIGN`，有的写死了 `ipa_top`；或者 `00_setup.tcl` 没有被每个脚本 source。

规矩：**所有路径、名字、库版本只在 `00_setup.tcl` 里定义一次，其他脚本第一行 `source ./00_setup.tcl`。** 禁止在 02~07 里出现硬编码的设计名。

检查方法：`grep -n "ipa_top" pnr/scripts/*.tcl`，除了 `00_setup.tcl`，其他地方出现就是隐患。
:::

## 阶段命名与产物链 {#naming}

命名不是审美问题，是**可追溯性**问题。推荐一条规则，全项目统一：

```
<两位阶段号>_<内容>_<时间戳>.<扩展名>
例：04_place_20261122_1400.enc
    06_route_20261122_1400.def
```

三个字段各有作用：阶段号决定排序，内容决定"这是什么"，时间戳决定"哪一次"。

产物是一条链，每一环都依赖上一环：

```
netlist.v ──▶ 01_init.enc ──▶ 02_fp.enc ──▶ 03_power.enc ──▶ 04_place.enc
                                                                  │
                                                                  ▼
final.spef ◀── final.def ◀── final.v ◀── 07_finish.enc ◀── 06_route.enc ◀── 05_cts.enc
```

链上的每一环都要能回答："我是从哪个上游来的、我下游是谁。" 这就是为什么 `db/` 里的文件名必须带阶段号，`out/` 里的文件名必须带时间戳。

时间戳建议精确到分钟，不要只到天。同一天跑两版很常见（上午改 floorplan、下午重跑），只写日期就会互相覆盖。如果团队并发跑同一个设计，还要加人名或工位号，比如 `04_place_20261122_1400_zhang.enc`。

交付版本再额外打一个语义化 tag：`v0.1` 表示第一次内部交付，`v0.2` 表示修完 floorplan，`v1.0` 表示送签核。tag 和 run 目录的对应关系写进交接邮件，别只存在脑子里。

**磁盘要算一下**：一个万门设计的 `.enc` 约 100~300 MB，八个阶段约 1.5~2.5 GB；跑十次就是 15~25 GB。十万门设计单个 `.enc` 可能 1~2 GB，不能无限留。

保留策略（典型做法）：

- `db/`：只留每个阶段最新一版 + 上一版（回退用），旧的删。
- `out/`：每次交付的版本都留，按 `v0.1`、`v0.2` 打 tag。
- `log/`：全留，文本不占空间。
- `run/`：项目结束后归档到冷存储。

## 每步的产物与检查 {#artifacts}

“跑完了”不算完，“检查通过”才算完。每个阶段都要有**一条命令 + 一个数**作为通过标准。

| 阶段 | 产物 | 检查命令 | 通过标准 |
|---|---|---|---|
| 01 初始化 | `db/01_init.enc` | `checkDesign` / `report_clocks` | 单元数与网表一致；时钟数正确；无 unresolved |
| 02 floorplan | `db/02_fp.enc` | `checkFPlan -reportUtil` / `report_area` | 利用率接近目标；宏无重叠；row 完整 |
| 03 power | `db/03_power.enc` | `verifyPowerVia` / `checkPGConnectivity` | PG 0 unconnected；via 覆盖完整 |
| 04 place | `db/04_place.enc` | `report_qor` / `reportCongestion` | WNS 可控；无大面积拥塞热点 |
| 05 cts | `db/05_cts.enc` | `report_clock_timing -type skew` | skew ≤ 目标 1.5 倍；hold 有基线 |
| 06 route | `db/06_route.enc` | `check_routes`（按 short/open/spacing 分类看） | DRC 0 或只剩可解释少数；无 open |
| 07 finish | `out/*.def/.v/.spef/.sdc` | 文件自检 + 最终报告 | 四件套同戳；DRC 0；时序达标 |

三个最容易被糊弄过去的检查，单独说：

**单元数**。初始化后 `report_qor` 的单元数应该和网表里的实例数基本一致（差几个黑盒正常）。差 10% 说明网表读漏了，或者库里有单元没 link 上。这个数不对，后面所有结果都不用看。

**WNS 的趋势，不是绝对值**。place 后 WNS −0.3 ns、CTS 后 −0.2 ns、route 后 −0.1 ns，是健康的收敛趋势。如果 place 后 +0.5 ns、route 后 −0.8 ns，说明布线阶段引入了大量真实线延迟，要回头看布局和拥塞。

**DRC 的类型**。总数是 0 最好；不是 0 时，必须按类型分类（short / spacing / open / via）。short 和 open 是"硬伤"，磨不掉；spacing 和 via 才可能靠 `route_detail` 收敛。

检查要尽量自动化。人眼每天看八份报告，第三天就会开始"扫一眼觉得差不多"。把通过标准写成断言（单元数偏差 <1%、WNS 不回退超过 50 ps、DRC 不增加），让脚本打印 PASS/FAIL。**人只负责解释 FAIL，不负责发现 FAIL。**

```tcl
# 作用：每个阶段结束时统一产出"一页纸"检查报告
# 用法：放在各阶段脚本末尾；报告文件名带阶段号，便于横向对比
report_qor > rpt/${STAGE}_qor.rpt                  ;# WNS/TNS/面积/利用率/单元数，一页看全
report_timing -max_paths 20 > rpt/${STAGE}_setup.rpt  ;# setup 最差 20 条，看趋势
report_timing -delay_type min -max_paths 20 > rpt/${STAGE}_hold.rpt  ;# hold 最差 20 条
checkDesign -all > rpt/${STAGE}_check.rpt          ;# 结构检查：悬空、多驱动、无负载（命令名以版本为准）
```

## 交接给 PT：要交什么 {#handoff}

PR 做完，STA 要用 PrimeTime 复签。只交"网表 + SPEF + SDC"三件是不够的——出问题时需要报告和版本信息定位。完整的交接是六件：

| # | 文件 | 内容 | 为什么必须 |
|---|---|---|---|
| 1 | `final.v` | 布线后门级网表 | PT 读设计；必须是布线后，不是布局前 |
| 2 | `final.spef` | 每根线的 R/C | 让 PT 用真实延迟，而不是估算 |
| 3 | `final.sdc` | 约束 | 和 PR 内部用的同一版，口径一致 |
| 4 | `final.def` | 版图几何 | PV 做 DRC/LVS；也用于 cross-check 单元位置 |
| 5 | 报告包 | QoR / timing / DRC / skew | 让 STA 知道 PR 自检结论，重点看哪里 |
| 6 | 脚本与版本 | git commit、工具版本、库版本 | 复现和定位"是不是环境变了" |

```tcl
# 作用：一次导出六件套里的前四件（Innovus 写法；ICC2 对照写在注释里）
# 用法：07_finish.tcl 末尾执行；STAMP 由 00_setup.tcl 统一生成
set STAMP 20261122_1400                                    ;# 统一时间戳，四份文件必须同源
defOut -netlist -routing ./out/final_${STAMP}.def           ;# DEF：含布线和网表连接（ICC2: write_def）
saveNetlist ./out/final_${STAMP}.v                          ;# 布线后网表（ICC2: write_verilog）
write_sdc ./out/final_${STAMP}.sdc                          ;# 约束，从工具里导，不要拷输入那份（ICC2: write_sdc）
rcOut -spef ./out/final_${STAMP}.spef                       ;# 寄生参数（ICC2: write_parasitics -format SPEF）
```

每份文件给谁、缺了会怎样：

- **`.v` + `.spef` 必须成对**。只有网表没有 SPEF，PT 只能用估算线延迟（`set_wire_load_model`），结果和 PR 差很多；只有 SPEF 没有匹配网表，PT 会报大量 `cannot find pin`。
- **`.sdc` 必须从 PR 工具导**。PR 过程中工具会补 `set_propagated_clock`、更新 uncertainty、加 case analysis。直接拷输入 SDC，PT 算的是另一套条件。
- **`.def` 不是给 PT 的，是给 PV 的**。但交接时一起给，方便交叉核对"PT 读到的单元位置和版图是不是一致"。
- **报告包是"论点"，不是"附件"**。你要在交接邮件里写："这版 WNS −0.08 ns，只有 3 条违例，都在 u_core 到 SRAM 的路径上，建议 PT 重点看。" 而不是把 20 份报告一丢。

清单文件（manifest）建议每次自动生成：

```text
# 本次运行的身份证：工具、库、脚本、输入、产物、关键指标
run_id       : 20261122_1400
tool         : Innovus 21.1（以实际版本为准）
pdk          : tsmc28 / NDM 或 LEF 版本号
script_git   : a1b2c3d（pnr/scripts 的 commit）
netlist_md5  : 9f2c...（输入网表校验和）
cells        : 12026
wns_setup    : -0.08 ns
drc          : 0
artifacts    : out/final_20261122_1400.{v,spef,sdc,def}
```

`script_git` 和 `netlist_md5` 这两行最有价值：一周后有人问"这版和那版差在哪"，看这两个值就知道是不是同一套输入。

:::pitfall 网表和 SPEF 不匹配，STA 结果全废
现象：PT 读入后报大量 `cannot find pin`，或者时序结果完全不合理（WNS −2.3 ns，PR 里明明是 +0.1）。

原因：网表是布线**前**导出的，SPEF 是布线**后**生成的；或者反过来。两者的单元名、连线名对不上，PT 把延迟挂到了不存在的网络上。

怎么查：比两个文件的生成时间；`grep` 几个关键单元名，看是否两边都有；看 manifest 里的时间戳是不是同一个。

规矩：**网表和 SPEF 必须同一次运行、同一时刻导出，文件名带同一个时间戳。** 导出脚本里两行命令紧挨着写，中间不许插其他步骤。
:::

:::pitfall 交了一份"看起来最新"的 SDC
现象：PT 跑出来 setup 比 PR 乐观 300 ps，怎么也对不上。

原因：交的是综合用的 SDC，里面没有 PR 阶段补的 `set_propagated_clock`，时钟还是理想时钟，skew 被当成 0。

规矩：SDC 从 PR 工具 `write_sdc` 导出，并在交接单上写清"来源：07_finish 导出"。不要从 `constraints/` 目录直接拷。
:::

## 跑批工程化：让脚本自己停 {#batch}

手工敲命令的问题是：**错了不停**。第三条命令失败了，第四条照样跑，最后你在第 20 步看到一个莫名其妙的错误。

工程化的三条底线：

1. **失败即停**：任何一步返回非零，整个流程立刻退出。
2. **日志不覆盖**：每次运行一个日志文件，带时间戳。
3. **断点可续**：每步成功留一个标记，重跑时跳过已完成的步骤。

```bash
#!/bin/bash
# 作用：PR 流程跑批驱动——建 run 目录、逐阶段执行、失败即停、留标记
# 用法：bash run_flow.sh 2>&1 | tee -a log/driver.log；在 pnr/ 目录下执行
set -euo pipefail                                   # -e 失败即停；-u 未定义变量报错；-o pipefail 管道失败也停
STAMP=$(date +%Y%m%d_%H%M)                          # 本次运行的时间戳，所有产物共用
RUN=run/${STAMP}                                    # 本次运行的现场目录
mkdir -p "$RUN"/{db,out,rpt,log,done}               # 一次建好五类子目录
ln -sfn "$RUN" run/latest                           # latest 永远指向最近一次，方便找
cp scripts/*.tcl "$RUN"/                            # 复制脚本快照：以后改脚本不影响这次复现
git rev-parse --short HEAD > "$RUN"/script_git.txt  # 记录脚本版本，出问题能回到那个 commit

for stage in 01_init 02_floorplan 03_power 04_place 05_cts 06_route 07_finish; do
    if [ -f "$RUN/done/${stage}.done" ]; then       # 已有完成标记就跳过，实现断点续跑
        echo "[skip] $stage"                        # 打印跳过原因，日志里能看出来
        continue                                    # 进入下一阶段
    fi
    echo "[run ] $stage $(date +%H:%M:%S)"          # 记录开始时间，便于估算每步耗时
    innovus -no_gui -files "${RUN}/${stage}.tcl" \
        -log "${RUN}/log/${stage}.log"              # 每阶段独立日志，不覆盖
    touch "$RUN/done/${stage}.done"                  # 只有上一条命令成功才会执行到这里
done

echo "[done] all stages, artifacts in $RUN/out"     # 全部完成提示
```

逐段解释为什么这么写：

- `set -euo pipefail`：没有它，`innovus` 失败了脚本还会继续跑下一阶段，最后你拿到的是"半新半旧"的数据库。`-u` 能抓住拼错的变量名（空字符串当路径用，会把文件写到根目录）。
- `RUN=run/${STAMP}`：所有产物进同一个目录，而不是散落在 `db/`、`out/`、`rpt/`。这样"这一次运行"是一个整体，可以打包、可以删。
- `cp scripts/*.tcl "$RUN"/`：脚本快照。**这一条最容易被省略，也最有用**——三个月后你改了脚本，想复现老结果，没有快照就永远回不去。
- `git rev-parse`：如果脚本在 git 里，记 commit 比拷文件更轻。两个都做最稳。
- `if [ -f done/... ]`：判断"完成"用**标记文件**，不用数据库文件的时间戳。原因见下一个坑。
- `touch done/...`：放在 `innovus` 之后、`set -e` 的保护下，只有成功才执行。这是"断点续跑"的核心。

工具版本也要记。在 `00_setup.tcl` 里加一行，或者在驱动里加：

```bash
# 作用：把工具版本写进本次 run 目录，交接时一起给
# 用法：在 run_flow.sh 建完目录之后执行
innovus -version > "$RUN/tool_version.txt" 2>&1     # 工具版本：PT/PR 对不上时第一个要查的
echo "PDK=$PDK_VERSION" >> "$RUN/tool_version.txt"  # PDK 版本：库换了结果会变
```

## 失败与断点续跑 {#fail}

流程跑到第 5 步失败，正确的处理顺序是：**保留现场 → 看第一条错误 → 修脚本 → 从失败那步重跑**。不是"删掉重来"。

保留现场包括：日志不要覆盖、失败的数据库不要删（可能只写了一半，但能看出卡在哪）、把错误行号记进 issue。

```bash
# 作用：失败后的三件事——定位、隔离、续跑
# 用法：在 run/<时间戳>/ 目录下执行
grep -n "^Error\|^ERROR\|FATAL" log/05_cts.log | head -5   # 找第一条错误，不看最后一条
ls -lh db/05_cts.enc                                        # 看失败阶段的库是不是只写了一半
rm -f done/05_cts.done                                      # 删掉标记，让下一次重跑这一步
bash ../../run_flow.sh                                      # 重跑：01~04 会跳过，从 05 开始
```

注意 `rm -f done/05_cts.done` 这一句：如果失败阶段留下了"完成标记"（比如上一次成功过，这次改脚本重跑失败），不删标记，下次会被跳过，你会在第 7 步用着一个旧的 CTS 结果。

:::pitfall 续跑时读了半成品数据库
现象：断点续跑后，第 6 步报"database corrupted"，或者时序结果明显不对。

原因：上一次在第 5 步中途失败，`05_cts.enc` 写了一半；但脚本用"文件存在"判断是否完成，于是跳过了重建，直接读半成品。

规矩：**判断完成用 `.done` 标记，不用文件是否存在。** 标记只在命令成功返回后 `touch`。数据库文件存在不等于可用。

另外：如果工具是"先删旧目录再写新目录"，失败时旧版本也没了。重要的阶段存盘前先 `cp -r` 一份上一版，或者写到临时目录再 `mv`。
:::

:::pitfall 日志被覆盖，出事只剩最后一屏
现象：流程失败，你想看两小时前的那条 warning，发现 `run.log` 里只有最后 200 行。

原因：脚本用 `>` 重定向，每次运行覆盖同一个日志；或者 `tee` 没带 `-a`。

规矩：日志文件名带时间戳（`log/05_cts_20261122_1400.log`），驱动层再统一 `tee -a log/driver.log`。**日志是事后唯一的证据，比数据库更值得保留。**
:::

## 工作中怎么用：这条流水线在项目里的节奏 {#in-work}

**每周的节奏**（典型）：

- 周一：拿到新网表，跑 01~04，看 WNS 趋势和拥塞，决定这周要不要改 floorplan。
- 周二到周三：CTS + route，收敛 DRC 和 hold。
- 周四：导出六件套，自查 manifest，发交接邮件。
- 周五：STA 复签，把违例反馈回来，排下周 ECO。

**谁读你的目录**：STA 读 `out/`，PV 读 `def`，接手同事读 `scripts/` 和 `run/latest/`，leader 读 `rpt/` 里的一页纸 QoR。**目录结构是给别人的接口**，不是给自己看的。

**评审会看什么**：这版和上版的 WNS/TNS/面积/DRC 对比；每一步的检查是否都过；交接物是否齐全且同源。没有人会看你的命令敲得漂不漂亮。

**做错了会怎样**：目录乱，接手人要花两天重建上下文；版本不清，出问题无法复现；网表和 SPEF 不同步，STA 结论作废，整轮返工。**流程工程化的价值不在"跑得快"，在"错了能定位、换人能接手"。**

:::lab 动手：搭一个能续跑的 run 目录
**任务**：在 `~/backend_lab/28nm/pnr/` 下搭出本课的目录骨架，跑通 01~02 两个阶段，并模拟一次失败续跑。

**步骤**：

1. 建目录：`mkdir -p scripts db out rpt log run done`。
2. 把课程给的 `01_init.tcl`、`02_floorplan.tcl` 放进 `scripts/`，确认它们都 `source ./00_setup.tcl`。
3. 写一个最小 `run_flow.sh`（照抄本课模板，阶段只留 01、02），跑一遍。
4. 检查 `run/latest/` 下是否有 `done/01_init.done`、`done/02_floorplan.done`、两份日志、两份报告。
5. 故意把 `02_floorplan.tcl` 里改一个错的库路径，删掉 `done/02_floorplan.done` 重跑，确认：01 被跳过、02 失败、脚本非零退出。
6. 生成一份 manifest（工具版本、git commit、单元数、WNS），写进 `run/latest/manifest.txt`。

**过关标准**：`bash run_flow.sh; echo $?` 在失败时返回非零；重跑时 01 显示 `[skip]`；`run/latest` 指向最新目录；manifest 里六个字段都有值。

**如果环境里没有 Innovus license**：用一个假的 `innovus` 脚本（打印参数、`sleep 1`、按参数决定返回 0 或 1）代替，专门练"失败即停 + 断点续跑"这套机制。机制和工具无关。
:::

:::quiz
为什么脚本要按阶段编号、每步存盘？|可以从任意阶段重跑，不必从头；改错时能快速回到上一个可用状态。
交接给 PT 的六件套是什么？|布线后网表 `.v`、寄生 `.spef`、约束 `.sdc`、版图 `.def`、报告包、脚本与工具版本。
网表和 SPEF 不匹配会有什么现象？|PT 报大量找不到引脚，或时序完全不合理，因为延迟数据对应的是另一个版本的网表。
为什么要建带时间戳的 run 目录？|留存每次运行的完整现场（脚本快照、日志、报告、产物），可以回溯和复现。
`set -euo pipefail` 三个选项各管什么？|`-e` 命令失败即退出；`-u` 使用未定义变量报错；`-o pipefail` 管道中任一命令失败都算失败。
断点续跑为什么用 `.done` 标记而不是判断文件存在？|数据库文件可能存在但只写了一半；标记只在命令成功返回后创建，才代表这一步真的完成。
SDC 为什么要从 PR 工具导出，而不是拷输入那份？|PR 过程会补 propagated clock、uncertainty、case analysis；直接拷输入 SDC，PT 算的是另一套条件。
manifest 里最该记哪两项？|脚本 git commit 和输入网表校验和。它们能回答"这版和那版是不是同一套输入"。
:::

:::check
- 能画出 28nm 项目的目录结构，并说明每个目录放什么、谁能删
- 能说出脚本按阶段编号带来的两个好处（可续跑、依赖顺序清晰）
- 能给出每个阶段的产物和一条通过标准
- 能背出交接六件套，并解释网表与 SPEF 为什么必须同源
- 能写出"失败即停 + 日志不覆盖 + 标记续跑"的跑批脚本骨架
- 知道判断完成要用 `.done` 标记，而不是数据库文件是否存在
:::
