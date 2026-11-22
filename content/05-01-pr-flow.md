---
id: 05-01-pr-flow
no: 27
stage: 5
title: 28nm 全流程（一）：把 PR 串成项目
en: 28nm PR Flow
hours: 4
minutes: 40
tags: [流程, 28nm, 交接]
summary: 前面学的是"每个阶段怎么做"，这一课讲"怎么把它们串成一条不会断的流水线"：目录怎么分、每步产物叫什么、怎么交接给 PT。
---

## PR 阶段的项目视角 {#project}

单机跑一个流程，和项目里跑一个流程，差别在这几点：

| 单机练习 | 真实项目 |
|---|---|
| 一个目录随便放 | 按阶段/日期分目录，可回溯 |
| 脚本改完就覆盖 | 脚本进版本管理，每次跑记录版本号 |
| 跑完看报告 | 每步产出固定格式报告，自动汇总成一张表 |
| 一个人跑 | 交接给别人能复现 |

:::term Run Directory | 运行目录
每次跑流程新建一个带时间戳的目录（如 `run/20261122_1400/`），里面放本次的脚本副本、日志、报告、结果。

好处：任何时候都能回答"三天前那版是怎么跑的、结果是什么"。
:::

## 推荐目录结构 {#tree}

```
proj/28nm/
├── rtl/                    # 只读
├── syn/
│   ├── scripts/            # 综合脚本
│   ├── netlist/ipa_top.v   # ← PR 的输入
│   └── reports/
├── pnr/
│   ├── scripts/
│   │   ├── 01_init.tcl
│   │   ├── 02_floorplan.tcl
│   │   ├── 03_power.tcl
│   │   ├── 04_place.tcl
│   │   ├── 05_cts.tcl
│   │   ├── 06_route.tcl
│   │   └── 07_finish.tcl
│   ├── db/                 # 每阶段存盘
│   ├── out/                # def / gds / spef / v
│   └── reports/
├── sta/
│   ├── scripts/
│   └── reports/
├── pv/
└── run/
    └── 20261122_1400/      # 每次跑的完整现场
```

**要点：脚本按阶段编号。** 想重跑"从 CTS 开始"，只要 `restoreDesign db/04_place.enc` 再跑 05、06、07，不用从头来。

## 每步的产物与检查 {#artifacts}

| 步骤 | 产物 | 关键检查 |
|---|---|---|
| 01 初始化 | `db/01_init.enc` | 单元数、时钟、`checkDesign` |
| 02 floorplan | `db/02_fp.enc` | 利用率、宏位置、无重叠 |
| 03 power | `db/03_power.enc` | 连通性、via 覆盖 |
| 04 place | `db/04_place.enc` | 密度、拥塞、setup WNS |
| 05 cts | `db/05_cts.enc` | skew、insertion delay、hold WNS |
| 06 route | `db/06_route.enc` | DRC、open net |
| 07 finish | `out/*.def/.gds/.spef` | 最终 DRC、时序、面积 |

:::tip "每步都存盘"的真实价值
不是怕崩，是**怕改错**。

比如 CTS 之后发现 floorplan 有问题，你可以 `restoreDesign db/02_fp.enc` 改完重跑 03~07；如果没有存盘，只能从 01 开始。

**存盘的时间成本是 1 分钟，不存盘的代价是 4 小时。**
:::

## 交接给 PT：要交什么 {#handoff}

PR 做完，STA 工程师（或者你自己）要用 PrimeTime 复签。需要三样东西：

| 文件 | 内容 | 为什么需要 |
|---|---|---|
| `final.v` | 布线后的网表 | PT 要读设计 |
| `final.spef` | 寄生参数（R/C） | 让 PT 用真实线延迟 |
| `ipa.sdc` | 约束 | 和 PR 用同一份，保证口径一致 |

```bash
# PR 侧导出
write_verilog out/final.v
write_parasitics -format SPEF -output out/final.spef
```

:::pitfall 网表和 SPEF 不匹配
现象：PT 读入后报大量 `cannot find pin` 或时序完全对不上。

原因：网表是布线**前**导出的，SPEF 是布线**后**生成的（或者反过来）。两者单元名、连线名对不上。

**规矩：网表和 SPEF 必须同一次运行、同一时刻导出。** 导出后立刻用 `grep` 核对几个关键单元名是否都在。
:::

:::scene 一次典型的交接事故
PR 工程师交了网表和 SPEF，STA 一跑，WNS −2.3ns，完全不可能。

排查发现：SPEF 是三天前那版（改过布局），网表是新的。**延迟数据对不上，时序当然离谱。**

从此这个团队的规定：导出脚本必须在同一条命令里同时产生 `.v` 和 `.spef`，并在文件名里带同一个时间戳。
:::

:::check
- 能画出 28nm 项目的目录结构，并说明为什么脚本按阶段编号
- 知道每步该存什么盘、检查什么
- 能说出交接给 PT 的三件套
- 明白网表和 SPEF 必须同时导出
:::

:::quiz
为什么按阶段编号写脚本、每步存盘？|可以从任意阶段重跑，不必从头；改错时能快速回到上一个可用状态。
交接给 PT 需要哪三个文件？|布线后网表 `.v`、寄生参数 `.spef`、约束 `.sdc`。
网表和 SPEF 不匹配会有什么现象？|PT 报找不到引脚，或时序结果完全不合理（因为延迟数据对应的是另一个版本）。
为什么要建带时间戳的 run 目录？|留存每次运行的完整现场（脚本、日志、报告），可以回溯和复现。
:::
