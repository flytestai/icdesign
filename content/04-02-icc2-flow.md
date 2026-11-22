---
id: 04-02-icc2-flow
no: 25
stage: 4
title: ICC2 全流程实战：从空目录到导出版图
en: ICC2 Full Flow
hours: 10
minutes: 60
tags: [ICC2, 全流程, place_opt, clock_opt, route_opt]
summary: 一条完整的 ICC2 脚本，从建 block、floorplan、place_opt、clock_opt、route_auto 到 route_opt 和导出，每段都写清"为什么这么设"。
---

## 跑之前先确认三件事 {#prep}

| 检查项 | 命令 | 期望 |
|---|---|---|
| NDM 有 timing view | `report_lib` | 能看到 Timing Data |
| 寄生模型已读 | `get_parasitic_techs` | 有 corner 名 |
| 网表/约束就绪 | `ls` | `.v` + `.sdc` |

三者缺一个，后面的优化命令都会失败。

## 完整脚本 {#script}

```tcl
# ============ 0. 打开库和 block ============
set PDK   /home/proj/pdk/tsmc32
set WORK  ./work

open_lib $PDK/ndm/tsmc32_ts.ndm
# 基于参考库新建一个 block
create_lib -use_technology_lib tsmc32_ts -ref_libs {tsmc32_ts} $WORK
open_lib $WORK
read_verilog ../syn/netlist/ipa_top.v
current_design ipa_top
link_design

# ============ 1. 寄生参数（place_opt 的前提）============
read_parasitic_tech -tlup $PDK/tlup/tsmc32.tlup -layermap $PDK/tlup/layer.map -name tt
set_parasitic_parameters -early_spec tt -late_spec tt

# ============ 2. 约束 ============
source ../constraints/ipa.sdc
report_clocks

# ============ 3. Floorplan ============
initialize_floorplan -core_utilization 0.65 -core_offset {10 10 10 10}
# 摆宏单元（坐标来自你的 floorplan 方案）
set_cell_location -coordinates {40 60} -orientation MY [get_cells u_sram0]

# ============ 4. 电源网络 ============
create_pg_ring -nets {VDD VSS} -layer {M5 M6} -width 3 -spacing 2 -offset 2
create_power_straps -nets {VDD VSS} -direction vertical -layer M5 -width 1.5 -pitch 25
connect_pg_net -all

# ============ 5. 布局优化（时序驱动）============
set_app_options -name place.coarse.continue_on_missing_scandef -value true
# ↑ 没有 scan def 时布局器默认一个单元都不放，且不报致命错，静默失败

place_opt
# 内部会做：全局布局 → 合法化 → 插 buffer/换单元 → 初步时序优化

report_qor > rpt/qor_place.rpt
save_block

# ============ 6. 时钟树 ============
set_app_options -name cts.optimize.delay -value true
clock_opt
# 建树 + 优化 setup/hold

save_block

# ============ 7. 布线 ============
route_auto
# 全局 + 详细布线

route_opt
# 基于真实寄生的时序优化

# ============ 8. 收尾 ============
route_detail -incremental 5      # 磨掉残余 DRC
check_routes > rpt/drc.rpt
report_timing -max_paths 20 > rpt/timing.rpt
report_area > rpt/area.rpt

# ============ 9. 导出 ============
write_def ./out/final.def
write_verilog ./out/final.v
write_parasitics -format SPEF -output ./out/final.spef
```

## 实测数据（万门设计，9390 单元） {#real}

我们用这套流程跑过一个 9390 单元的设计（6 个 SRAM、IPA 图像处理加速器）：

| 阶段 | 耗时 | 结果 |
|---|---|---|
| place_opt | 3.5 min | 单元数 9390 → 12026（插了 2636 个 buffer/时钟树单元） |
| clock_opt | 9.5 min | hold 从 −10ns 级收敛到 −0.07ns |
| route_auto | 1.7 min | **DRC 首轮即 0** |
| route_opt | 2.3 min | DRC 保持 0，setup WNS +1.00ns |
| route_detail ×5 | 2.2 min | DRC 仍 0 |
| **合计** | **21.7 min** | 芯片 222.5×222.2µm，利用率 49.8% |

:::scene 这组数字为什么值得记
- **`route_auto` 首轮 DRC = 0** 说明 floorplan 和 place_opt 做对了。如果首轮就几千个 DRC，别急着磨布线，回头查布局。
- **place_opt 插了 28% 的单元**是正常的（buffer 和时钟树）。如果插得过多（>50%），说明约束太紧或库不合适。
- **clock_opt 花的时间最长**（9.5 min），因为它在解 hold 这个硬骨头。
:::

:::pitfall 静默失败：一个单元都没放
第一次跑 `place_opt`，跑得飞快（几秒），报告也没报错，但打开布局一看：空的。

原因：ICC2 默认要求有 scan def（扫描链定义），没有就直接跳过布局，而且**不报致命错误**。

解法：

```tcl
set_app_options -name place.coarse.continue_on_missing_scandef -value true
```

**这类"跑得特别快、结果为空"的情况，比报错更危险**，因为容易误以为成功。
:::

## 和 Innovus 流程的对应 {#compare}

| 步骤 | Innovus | ICC2 |
|---|---|---|
| 建库 | 不需 | `create_workspace`/`commit_workspace` |
| 打开 | `restoreDesign` | `open_lib`+`open_block` |
| 约束 | `read_sdc` | `source x.sdc` |
| 布局 | `place_opt_design` | `place_opt` |
| 时钟 | `ccopt_design` | `clock_opt` |
| 布线 | `routeDesign` | `route_auto` |
| 后优 | `optDesign -postRoute` | `route_opt` |
| 导出 | `defOut`/`streamOut` | `write_def`/`write_verilog` |

:::check
- 能写出 ICC2 从建 block 到导出的完整顺序
- 知道 `place_opt` 前必须先设寄生参数
- 记得 `continue_on_missing_scandef` 这个静默失败的坑
- 能解释为什么 `route_auto` 首轮 DRC 0 是好兆头
- 能说出 place_opt 后单元数增长多少算正常
:::

:::quiz
`place_opt` 之前为什么必须先读寄生参数？|否则报 `NEX-018: no valid parasitic`，优化器无法计算线延迟，`place_opt` 起不来。
`place.coarse.continue_on_missing_scandef` 解决什么问题？|没有 scan def 时布局器会静默跳过布局（一个单元都不放），设为 true 后可以继续。
`clock_opt` 主要优化什么？|建立时钟树（降 skew），同时优化 setup 和 hold。
`route_auto` 出来 DRC 就是 0，说明什么？|说明 floorplan、布局、时钟树都比较健康；如果 DRC 很多，应该回头查布局而不是硬磨布线。
place_opt 之后单元数涨了 28%，正常吗？|正常。插 buffer、时钟树单元、驱动增强都会增加单元数，超过 50% 才需要怀疑约束或库。
:::
