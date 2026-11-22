---
id: 03-09-route
no: 20
stage: 3
title: 布线、优化与收尾：从能连到能交付
en: Routing, Optimization & Chip Finish
hours: 7
minutes: 55
tags: [Route, DRC, filler, GDSII]
summary: 布线分全局和详细两步，跑完还有 optRoute 和收尾。这一课讲清 DRC 违例从哪来、怎么清，以及 Chip Finish 到底在收什么尾。
---

## 布线的两步 {#two-steps}

### 全局布线（Global Route）

规划"大致走哪条通道"，不决定具体用哪根轨道。像导航先规划"走沪宁高速"，不管走哪条车道。

输出：每条网络的走线路径 + 各区域的轨道占用预估。

### 详细布线（Detail Route）

精确到**具体层、具体轨道、具体过孔**。要同时满足：连通、不短路、满足 DRC。

```tcl
# 全局布线
setRouteMode -earlyGlobalMaxRouteLayer M6
globalRoute

# 详细布线
routeDesign
# 或者分步
setNanoRouteMode -routeWithTimingDriven true
detailRoute
```

:::term Track | 轨道
每一层金属上，走线只能放在等间距的"轨道"上（因为工艺规定了最小间距）。

一个区域能走多少根线，等于它能容纳多少条轨道。**拥塞的本质就是"要走的线比轨道多"。**
:::

## DRC 违例从哪来 {#drc}

DRC（设计规则违例）常见四类：

| 类型 | 含义 | 常见原因 |
|---|---|---|
| Short | 短路：两根线碰到了 | 布线太密、局部拥塞 |
| Spacing | 间距不足 | 同层线太近 |
| Width | 线宽不足 | 非默认规则没设对 |
| Via | 过孔问题（太少、太大、包边不足） | 电源 via 或 cut 数量不够 |

```
Spacing violation 示意（同层两条线距离 < 规则要求）

  ━━━━━━━━━━
        ↕ 0.08µm  ← 规则要求 0.10µm → 违例
  ━━━━━━━━━━
```

:::pitfall "DRC 清不干净"的真相：通常是布局问题
现象：布线跑了 6 小时，DRC 还有 2000 条，反复 `routeDesign -incremental` 也降不下去。

打开违例分布图，发现集中在某几个区域 → 那里拥塞。

这时候继续磨布线没用。**必须回 floorplan 或 placement 解决空间不足。** 我们在实测里验证过：同一套布线参数，floorplan 改对之后 DRC 从 6000 直接到 0。

**记住：布线只能"在给定空间里找解"，空间不够它不是万能的。**
:::

## optRoute：布线后的最后优化 {#optroute}

布线完成后，线延迟已经确定（有真实的 R 和 C），此时再做一轮时序优化最准确。

```tcl
setOptMode -effort high
optDesign -postRoute          # 修 setup / DRV
optDesign -postRoute -hold    # 修 hold
```

:::term Post-Route Optimization | 布线后优化
基于真实寄生参数（R/C）重新优化时序。因为布线前用的是估算线延迟，布线后有了真实值，可能发现新违例。

这一步通常能修掉 80% 的残留违例，剩下的靠手工 ECO。
:::

:::scene 为什么布线后时序会"变差"
布线前，工具用"估算线长"算延迟，往往偏乐观。布线后真实走线绕了弯、换了层，延迟变大。

所以：

- 布线前 setup slack 要留 100~150ps 余量。
- 不然布线后一波新违例，又要重跑。

**"估算乐观"是后端永恒的主题，留余量是唯一对策。**
:::

## Chip Finish：收尾四件事 {#finish}

### 1. 插 filler

标准单元行里会有空隙（因为单元宽度不一）。空隙不填，工厂做 CMP（化学机械抛光）时表面不平，会导致后续层光刻失焦。

```tcl
addFiller -cell {FILLCELL_X1 FILLCELL_X2 FILLCELL_X4 FILLCELL_X8} -prefix FILLER
# 从最小的开始填，工具自动组合
```

### 2. 补 well tap / endcap

```tcl
addWellTap -cell TAPCELL -cellInterval 40     # 每 40µm 打一个井接触
addEndCap                                      # 行两端加端帽
```

### 3. 最终 DRC / 连通性检查

```tcl
verifyGeometry            # DRC
verifyConnectivity        # 连通性（有没有悬空/短路）
checkDesign -all
```

### 4. 导出交付物

```tcl
# DEF：布局布线信息（给下游工具）
defOut -floorplan -netlist -routing final.def

# GDSII：完整版图（给工厂/DRC/LVS）
streamOut final.gds -mapFile layer.map

# 网表（带寄生信息前的连接关系）
saveNetlist final.v

# 寄生参数（SPEF，给 PT 做签核）
rcx -spef final.spef
```

:::term SPEF | 标准寄生交换格式
Standard Parasitic Exchange Format。记录每根线的电阻、电容。

PrimeTime 读它之后，时序分析才基于"真实线延迟"，而不是估算值。**这是签核精度的关键。**
:::

## 交付前的检查清单 {#checklist}

| 项目 | 命令 | 通过标准 |
|---|---|---|
| DRC | `verifyGeometry` | 0 违例（或已 waiver） |
| 连通性 | `verifyConnectivity` | 无开路/短路 |
| 时序 | `timeDesign -postRoute` | WNS ≥ 0（留余量） |
| 面积 | `reportArea` | 符合预期 |
| 单元数 | `reportArea` | 无异常膨胀 |
| filler 覆盖 | `checkFiller` | 无空隙 |
| 电源 | `verifyPowerVia` | via 覆盖率达标 |

:::lab 动手：清一遍我们实测过的流程（ICC2 版，可在本课程环境跑）
```tcl
# 这是 ICC2 的等价动作，和 Innovus 一一对应
open_lib ./work
open_block ipa_top

route_auto
route_opt
route_detail -incremental 10     # 10 轮增量，磨掉残余违例

check_routes > rpt/drc.rpt
report_timing -max_paths 10 > rpt/timing.rpt

write_def ./out/final.def
write_verilog ./out/final.v
```

实测结果（万门设计）：`route_auto` 首轮 DRC 0；再跑 `route_opt` 保持 0；`route_detail -incremental` 十轮仍为 0。

过关标准：能解释"为什么 route_opt 之后还要跑 route_detail"（答：route_opt 插了 buffer、改了线，可能引入新违例，detail 负责精确修复）。
:::

:::check
- 能说出全局布线和详细布线的分工
- 知道四类 DRC 违例及常见成因
- 明白"DRC 清不干净多半是布局问题"
- 会做 Chip Finish 的四件事
- 能列出交付前检查清单的六项
:::

:::quiz
全局布线和详细布线分别做什么？|全局规划大致走线和层分配；详细精确到具体轨道和过孔，保证 DRC 干净。
Short 和 Spacing 违例的区别？|Short 是两根线真的连上了（短路）；Spacing 是没连上但距离小于规则要求。
为什么布线后时序可能比布线前差？|布线前用估算线延迟（偏乐观），布线后有真实绕线和换层，延迟变大。
`addFiller` 的作用是什么？|填满标准单元行的空隙，保证每层密度均匀，避免 CMP 不平导致光刻问题。
SPEF 是给谁用的？|给 PrimeTime 等签核工具，用时序分析基于真实 RC。
:::
