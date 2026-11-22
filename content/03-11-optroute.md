---
id: 03-11-optroute
no: 22
stage: 3
title: OptRoute：把 DRC 从几千条磨到零
en: Routing Optimization (OptRoute)
hours: 3
minutes: 42
tags: [布线, OptRoute, DRC, 拥塞, 天线]
summary: 全局布线通了不等于做完。DRC、时序回退、串扰、天线，四类问题都在布线后集中爆发。这一课讲五类 DRC 的成因、OptRoute 的三种模式、增量布线的正确用法，以及我们实测 6000→0 的真实路径。
---

## `route_auto` 返回 0，不代表布线做完了 {#why}

`route_auto`（Innovus 是 `routeDesign`）做完，你通常会看到"布线完成"。但这时报告里至少有四类问题：

| 问题 | 典型数量 | 后果 |
|---|---|---|
| DRC 违例 | 几十到几千 | 签核不过，必须清零 |
| setup 恶化 | 新增几十条 | 布线后线延迟吃掉了余量 |
| 串扰（crosstalk） | 未检 | 信号互相干扰，功能可能出错 |
| 天线违例 | 几十条 | 工艺厂要求修，否则栅氧会被击穿 |

:::scene "不是已经布通了吗，怎么还有 6000 个 DRC"
你第一次看到 `Total number of DRCs: 6000` 会以为工具坏了。

其实这是正常的：全局布线只保证"每个连接有路可走"，细节布线才真的把线画在具体的轨道上。6000 条里绝大多数是**同一类问题**——引脚访问冲突（pin access），一个单元的多个引脚挤在一起，线出不来。
:::

:::term DRC | Design Rule Check，设计规则检查
工艺厂规定的一堆"物理上不许这样画"的规则：两条线不能太近（spacing）、线不能太细（width）、不能有尖角（notch）、不同层的连接必须用 via 等。

DRC 违例不是"工具算错了"，是**你画出来的版图真的违反了工厂的制造能力**。所以必须清零。
:::

## 五类 DRC，认清成因才知道怎么修 {#types}

| 类型 | 英文 | 典型报错 | 成因 | 修法 |
|---|---|---|---|---|
| 间距 | spacing | `Metal2 spacing < 0.07` | 两条线太近 | 让工具重布局部；挪单元 |
| 短路 | short | `Net A shorted to net B` | 两条不同网的线碰上了 | 增量布线路由重解 |
| 开路 | open | `Net A has unconnected pin` | 线没连到引脚 | 检查引脚是否被挡住 |
| 宽度 | width / notch | `Metal1 width < 0.065` | 线太细或有缺口 | 加宽/合并；通常工具自动修 |
| 引脚访问 | pin access | `ZRT-045: pin access conflict` | 单元引脚太密，出线互相打架 | **布局优化**（见下） |

:::note 为什么"引脚访问冲突"最难修
一个 `AOI222_X1` 有 6 个引脚挤在 0.76×1.4um 的框里。如果周围单元摆得太密、或者电源轨占了可用的 metal1，线就没法从引脚出来。

这类 DRC 有个特点：**它不随布线轮数减少**。我们实测第 1 轮 6000 条里，95% 是这一类；单纯增加 `route_detail` 轮数从 6000 只降到 156 就卡住了。
:::

## 三种 OptRoute，代价差很多 {#modes}

| 模式 | Innovus | ICC2 | 改什么 | 耗时 | 何时用 |
|---|---|---|---|---|---|
| 局部增量 | `routeDesign -incremental` | `route_detail -incremental true` | 只重布有问题的局部 | 分钟级 | 已经基本干净，磨最后几十条 |
| 全局优化 | `optDesign -postRoute` | `route_opt` | 重布 + 调尺寸 + 修时序 | 十几分钟 | DRC 收敛后，修时序 |
| 完全重布 | `routeDesign` | `route_auto` | 全部推倒重来 | 最长 | 前面改动太大，增量已无意义 |

:::pitfall 一上来就跑 `route_opt`
`route_opt` 会同时动布线、单元尺寸和缓冲器。如果 DRC 还有几千条，它会在一个很脏的版图上做优化——**结果通常是 DRC 没修好，时序也被搅乱**。

正确顺序：**先增量布线把 DRC 磨到 100 以内，再跑 `route_opt` 修时序，最后再增量磨 DRC 到 0。**
:::

## 增量布线的正确用法：一轮一记录 {#incremental}

```tcl
# ICC2：循环 10 轮，每轮出一份报告 —— 关键是"每轮都留证据"
set it 1
while {$it <= 10} {
  route_detail -incremental true
  redirect check_routes_$it.rpt { check_routes }
  # 从报告里抽 DRC 总数，打印到屏幕，方便一眼看趋势
  set fh [open check_routes_$it.rpt r]
  set txt [read $fh]; close $fh
  regexp {Total number of DRCs\s*:\s*(\d+)} $txt -> n
  puts "@@@ round $it  DRC = $n"
  if {$n == 0} { break }        ;# 归零就提前退出，别白跑
  incr it
}
```

为什么必须每轮存报告：

1. 判断"还在收敛"还是"卡住了"（连续三轮数字不变 = 卡住，别再加轮数）；
2. 出问题时能定位是哪一轮引入的新违例；
3. 汇报时给的是曲线，不是"我跑了十轮就好了"。

## 我们实测的收敛曲线（真实数据）{#real}

万门设计（ipa_top，9390 单元，纯物理流程）第一次跑出来 6000 条 DRC。逐轮记录如下：

| 轮次 | DRC | 本轮做了什么 |
|---|---|---|
| 0（route_auto 后） | 6000 | 全局布线刚结束，几乎全是引脚访问冲突 |
| 1 | 156 | 第一次 `route_detail`，清了绝大多数 |
| 2 | 119 | 增量 |
| 3 | 72 | 增量 |
| 4 | 58 | 增量 |
| 5 | 47 | 增量 |
| 6 | 25 | 增量 |
| 7 | 17 | 增量 |
| 8 | 12 | 增量 |
| 9 | **0** | 增量，归零 |

:::note 关键发现：6000→156 是"布线"的功劳，156→0 是"布局"的功劳
只加布线轮数，卡在 156 下不去。真正的解法是回到布局端改三个开关：

```tcl
set_app_options -name place.coarse.pin_density_aware -value true   ;# 多引脚单元周围留通道
create_placement -effort high
legalize_placement
refine_placement                                                   ;# 局部再挪一次
```

改完重跑，第 1 轮就直接是 156 → 后续每轮都在降。**这就是"DRC 的根因在布局，不在布线"的含义。**
:::

## 拥塞：布线做不下去的真正原因 {#congestion}

DRC 是"已经画错了"，拥塞是"根本画不下"。看这两个数：

| 指标 | 含义 | 红线 |
|---|---|---|
| overflow | 某区域需要的布线轨道数 - 实际可用轨道数 | > 0 就是拥塞 |
| congestion % | 该区域轨道占用率 | > 90% 高危 |

诊断顺序（照这个顺序查，别乱试）：

1. **看热图**：拥塞集中在哪？是一个角落（宏单元周围）、还是全芯片均匀（利用率太高）；
2. **看是不是宏单元通道太窄**：宏和宏之间只留 5um，但那里要过 3000 根线 → 加宽通道；
3. **看是不是引脚密度问题**：某个区域多引脚单元（AOI/OAI/MUX）堆在一起 → 打开 `pin_density_aware`；
4. **最后才降利用率**：从 0.5 降到 0.4，面积变大但能布通。**这是最贵的修法**，放最后。

:::pitfall 拥塞了就降利用率
降利用率能让 DRC 变好，但芯片面积变大、线变长、功耗变高、成本上升。

先试便宜的：挪宏单元、加通道、开 pin_density_aware、调 `place.coarse.max_density`。这些都不行，再降利用率。
:::

## 天线效应：一个容易被忽略的硬违例 {#antenna}

制造过程中，长金属线像天线一样收集电荷，可能击穿晶体管的栅氧化层。规则是：**接到栅极的金属面积不能超过栅面积的某个倍数**。

```tcl
# 检查
check_routes -antenna          # 或 verifyAntenna
# 修：让工具在长线中间断开，跳到更高层再下来（跳线）
route_detail -fix_antenna true
```

| 修法 | 原理 | 代价 |
|---|---|---|
| 跳线（layer jumping） | 长线中途换到高层再回来，减小同层面积 | 多两个 via，占用布线资源 |
| 插二极管 | 加一个反向二极管泄放电荷 | 面积增加，需要库支持 |

## 布线后必须回签的两个数 {#signoff}

布完不是结束，要重新看：

```tcl
report_timing -delay_type max -max_paths 10    # setup 有没有被线延迟拖崩
report_timing -delay_type min -max_paths 10    # hold 有没有变差
check_routes                                    # DRC 是否为 0
```

:::note 我们实测的布线后数据
12026 单元（时序驱动流程）：`route_auto` 首轮 DRC 就是 **0**，`route_opt` 保持 0，10 轮增量全 0；12860 条网 open 0；setup WNS +1.00ns。

对比纯物理流程：首轮 6000，磨 9 轮才 0。**差别不在布线，在于前面有没有做时序驱动的布局。**
:::

:::lab 动手：从 DRC 报告判断"该不该再加一轮"
给定三份连续报告的数字（模拟终端里的 `drc.rpt` 就是这个格式）：

```text
iteration  DRC   opens   short
8          17    0       0
9          12    0       0
10         0     0       0
```

换个情形：

```text
iteration  DRC   opens   short
7          25    0       3
8          25    0       3
9          25    0       3
```

判断：第二种情况**再加轮数没用**，因为 short 数量三轮不变，说明是结构性问题（某个区域真的挤不下），要回去改布局或加通道。

在模拟终端里把这份表读出来：

```bash
cd ~/backend_lab/soc/pnr/reports
cat drc.rpt
awk 'NR>2 {print $1, $2}' drc.rpt      # 只看轮次和 DRC 数
awk '$4 > 0 {print "有 short:", $1}' drc.rpt   # 哪几轮有短路
```

过关标准：能说出"连续三轮数字不变 = 结构性问题，加轮数无效"。
:::

:::check
- 能说出五类 DRC 和各自成因
- 知道引脚访问冲突要靠改布局解决，不是加布线轮数
- 能写出 Innovus / ICC2 的三种布线优化模式对应命令
- 知道正确顺序：增量磨 DRC → route_opt 修时序 → 再增量磨到 0
- 能判断"还在收敛"和"已经卡住"
:::

:::quiz
为什么 `route_auto` 完成后还有几千条 DRC？|全局布线只保证"有路可走"，细节布线才把线画到具体轨道上；大量违例来自引脚访问冲突等局部资源竞争。
引脚访问冲突为什么加布线轮数也修不掉？|它源于布局——多引脚单元周围没有留出线通道。必须回布局端打开 pin_density_aware、refine_placement 才能解决。
DRC 还在几千条时能跑 route_opt 吗？|不建议。脏版图上做优化会同时搅乱时序和布线，正确顺序是先增量磨到 100 以内再优化。
连续三轮 DRC 数字完全一样说明什么？|说明不是随机收敛问题，而是结构性资源不足（拥塞/引脚访问），继续加轮数无效，要改布局。
天线违例的两种修法是什么？|跳线（中途换高层减小同层金属面积）和插二极管（泄放电荷）。
:::
