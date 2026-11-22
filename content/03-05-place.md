---
id: 03-05-place
no: 16
stage: 3
title: Placement：几万个单元怎么摆
en: Placement
hours: 4
minutes: 45
tags: [Innovus, placement, 拥塞, 密度]
summary: 布局是在"连线短"和"放得下"之间找平衡。这一课讲清密度、拥塞、合法化、扫描链重排，以及怎么从报告判断布局好不好。
---

## 布局在权衡什么 {#tradeoff}

把几万个标准单元摆进标准单元区，目标有两个，而且互相打架：

- **线要短** → 有连接的单元靠在一起 → 局部挤爆 → 布不通
- **要布得通** → 摊开 → 线变长 → 时序变差

工具的做法分两步：

1. **全局布局（global placement）**：先算一个"理论最优位置"，允许重叠。目标是最小化总线长。
2. **合法化（legalize）**：把重叠的单元挪开，落到合法的行/站点上。

:::term Legalize | 合法化
把单元坐标调整到"行"上、对齐到"站点"网格、且互不重叠的过程。

没合法化的位置叫 illegal，工具不能布线，必须先 legalize。
:::

## 三个关键指标 {#metrics}

| 指标 | 含义 | 看哪份报告 | 健康值 |
|---|---|---|---|
| 密度（density） | 局部区域单元占用比例 | `reportDensityMap` | 平均 <0.75，峰值 <0.90 |
| 拥塞（congestion） | 走线需求 / 可用轨道 | `reportCongestion` | overflow = 0 最好 |
| 线长（wirelength） | 总线长 | `reportWirelength` | 与上一版对比 |

:::term Overflow | 溢出
某块区域的走线需求超过可用轨道数，多出来的部分叫 overflow。

`reportCongestion` 里 `Total Overflow = 0` 是最理想的状态。几百以内还能靠布线工具消化；上千就必须回去改布局。
:::

## 命令与参数 {#cmd}

```tcl
# 基本布局（时序驱动）
setPlaceMode -place_global_timing_effort high \
             -place_global_cong_effort high \
             -place_global_place_io_pins false

place_opt_design
# 这个命令会做：全局布局 + 合法化 + 初步时序优化（插 buffer、换单元）

# 看结果
reportDensityMap                 # 密度热图（GUI 里看更直观）
reportCongestion -hotSpot        # 拥塞热点
reportArea                       # 面积/利用率
reportTiming -max_paths 10       # 最差 10 条路径

saveDesign db/04_place.enc
```

三个参数的作用：

- `timing_effort high`：花更多时间优化时序（跑得慢，结果好）。
- `cong_effort high`：更努力避免拥塞。
- `place_io_pins false`：不动 IO 引脚位置（引脚是 floorplan 定的，别让布局工具乱挪）。

## 扫描链重排：一个容易忽略的步骤 {#scan}

DFT 插入了扫描链，把几千个触发器串成一条长链。如果按综合顺序连，线会绕遍全片，既长又占资源。

**扫描链重排（scan chain reorder）**：按物理位置重新串，让相邻的触发器串在一起。

```tcl
# 布局之后做，因为需要坐标
setPlaceMode -place_global_reorder_scan true
# 或在布局后单独执行
scanReorder
```

:::scene 不做扫描链重排的后果
一条扫描链 3000 个触发器，按逻辑顺序连，物理上满片乱窜。布线时这条链占用大量资源，还会造成局部拥塞。

重排之后线长能降 30%~50%。**这一步不花钱，但不做就是白白浪费。**
:::

:::pitfall 布局"看起来不错"，但时序一塌糊涂
现象：`reportDensityMap` 很均匀、`reportCongestion` overflow 0，但 `reportTiming` 有 200 条 setup 违例。

原因通常是：**约束没读对**（时钟周期写错、false path 没设），或者**时序库 corner 用错**（用了 fast corner 算 setup）。

排查顺序：
1. `report_clocks` 看时钟周期对不对。
2. `report_timing -path_group` 看违例集中在哪个时钟域。
3. 抽一条路径 `report_timing -from xx -to yy -path_type full_clock_expanded`，看延迟构成。

**不要一上来就改布局参数** —— 先确认约束是对的。
:::

:::term Useful Skew | 有用偏斜
故意让时钟到达某些触发器的时间不同，把时间"借"给紧张的路径。

比如 A→B 这条路径差 100ps，可以让 B 的时钟晚到 100ps（相当于多给它 100ps 时间），代价是 B→C 那条路径少了 100ps。

这是 CTS 阶段的手段，但布局阶段就要预留可能性。
:::

:::lab 动手：读懂一份拥塞报告
```bash
# 典型 reportCongestion 输出（摘录）
cat > cong.rpt <<'EOF'
Layer    Total Capacity   Total Usage   Overflow
M2       120000           118900        0
M3       120000           122500        2500
M4       120000           119200        0
M5       120000           117800        0
Region (1200 800) (1800 1400): overflow 1800
EOF

# 哪一层最拥塞
awk 'NR>1 && $4>0 {print $1, "overflow="$4}' cong.rpt

# 总 overflow
awk 'NR>1 && $4 ~ /^[0-9]+$/ {s+=$4} END {print "total:", s}' cong.rpt
```

预期：M3 overflow 2500，total 2500。

过关标准：能指出"问题在 M3 层 + 特定区域 (1200,800)-(1800,1400)"，并说出至少两个可能原因（宏单元通道太窄 / 该区域密度过高）。
:::

:::check
- 能说出全局布局和合法化的区别
- 知道 density / congestion / overflow 三个指标的健康值
- 会用 `place_opt_design` 及三个关键参数
- 知道扫描链重排的作用和时机
- 遇到时序违例先查约束再查布局
:::

:::quiz
全局布局和合法化的区别？|全局布局算理论最优位置（允许重叠），合法化把单元挪到合法行/站点且互不重叠。
`reportCongestion` 里 overflow 是什么？|走线需求超出可用轨道的部分，0 最理想。
`place_io_pins false` 为什么要设？|IO 引脚位置由 floorplan/封装决定，不该让布局工具改动。
扫描链重排解决什么问题？|按物理位置重排扫描链顺序，缩短线长、减少拥塞。
布局后时序很差，第一步应该查什么？|先查约束（时钟周期、false path）和时序库 corner，排除约束错误再动布局参数。
:::
