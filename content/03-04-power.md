---
id: 03-04-power
no: 15
stage: 3
title: 电源规划：给每个单元供上电
en: Power Planning
hours: 2
minutes: 35
tags: [Innovus, power plan, IR drop, via]
summary: 电源网格不是"随便铺几条粗线"。线太细会掉压、太粗会挡线。这一课讲 ring / stripe / rail 三层结构，以及怎么用 via 阵列把电阻压下来。
---

## 电从哪来，到哪去 {#path}

一颗芯片的电从封装的电源引脚进来，经过：

```
封装引脚 → IO 环 → 电源环（ring） → 电源条（stripe） → 单元电源轨（rail） → 单元内部
```

每一段都有电阻，每段都会掉一点电压。**后端能控制的是 ring 和 stripe 的宽度、密度，以及 via 的数量。**

:::term IR Drop | 电压降
电流 × 电阻 = 电压差。芯片内部某点电压低于标称值，差值就是 IR drop。

典型阈值：不超过标称电压的 3%~5%。比如 1.0V 供电，drop 超过 50mV 就要担心了。
:::

## 三层结构 {#layers}

### 1. Power Ring（电源环）

围着核心区一圈，通常是上下两层金属各画一个环（M5/M6 横竖）。

```tcl
addRing -nets {VDD VSS} \
        -type core_rings \
        -layer {top M6 bottom M6 left M5 right M5} \
        -width 4 -spacing 2 -offset 3
# -width 4：环宽 4µm；-spacing 2：VDD 和 VSS 之间隔 2µm；-offset 3：距边界 3µm
```

### 2. Power Stripe（电源条）

从环往内部拉的网格，横竖交错。

```tcl
addStripe -nets {VDD VSS} \
          -layer M5 -direction vertical -width 2 -spacing 1.5 \
          -set_to_set_distance 30 -start_from left
# 每隔 30µm 一根竖条，宽 2µm
```

### 3. Follow Pin / Rail（单元电源轨）

每个标准单元行的电源轨。工具会沿着行自动连，不需要手画，但要检查连接：

```tcl
sroute -connect {corePin} -nets {VDD VSS} -layerChangeRange {M1 M6}
# 把每行的 rail 连到 stripe 上
```

## Via 阵列：最容易被忽略的一步 {#via}

不同层之间靠 via 连接。一层 via 就是一个小电阻，**一个 via 顶不住大电流，要打一片**。

```
❌ 单个 via：电阻大，电流集中，容易烧
┌──────────┐
│    ●     │
└──────────┘

✅ via 阵列：并联，电阻小，电流分散
┌──────────┐
│ ● ● ● ●  │
│ ● ● ● ●  │
│ ● ● ● ●  │
└──────────┘
```

```tcl
# 给电源条和环之间批量加 via
editPowerVia -nets {VDD VSS} -add_vias 1 -orthogonal_only 0
# 或者用更细的控制
addVia -nets {VDD VSS} -area {10 10 200 200} -layers {M5 M6} -via_pitch 2
```

:::pitfall 忘了打 via，IR 分析直接炸
现象：电源网格画得漂漂亮亮，RedHawk 一跑，某些点 IR drop 到 120mV。

原因：金属线没问题，但**层与层之间只有零星几个 via**，所有电流挤在那几个点上。

对策：`verifyPowerVia` 检查 via 覆盖率，不足的地方补阵列。**电源网格看的是"瓶颈"，不是"平均"。**
:::

## 电源规划的四条判断标准 {#rules}

| 指标 | 怎么查 | 合格标准 |
|---|---|---|
| 覆盖率 | `checkPGConnectivity` | 没有悬空的 rail |
| 宽度 | 看 stripe 宽度 vs 电流 | 电流密度不超限（EM） |
| via 密度 | `verifyPowerVia` | 关键节点成阵列 |
| 对信号的影响 | 看利用率变化 | 电源占用面积 <15% |

:::term EM | 电迁移
Electromigration。金属线里电流密度太大时，电子会把金属原子"推着走"，时间长了线就断了。

规则给的是"每微米宽度允许多少 mA"。所以电源线宽不是随便定的，是按电流算出来的。
:::

:::scene 电源做多了也麻烦
新手容易过度设计：ring 宽 10µm、stripe 宽 5µm、间距 10µm，铺满全片。

结果：电源占了 30% 的面积，标准单元没地方放，利用率被顶到 0.85，布线拥塞爆炸。

**电源规划的目标是"够用且不挡路"**，一般电源占用控制在 10%~15%。
:::

:::lab 动手：算一条 stripe 够不够
条件：某条竖直 stripe 要给 2000 个单元供电，每个单元平均电流 0.5µA，stripe 宽 2µm，工艺允许电流密度 0.8mA/µm。

```bash
python3 -c "
n=2000; i_per=0.5e-3; w=2; dens=0.8
I=n*i_per
print('总电流 %.2f mA' % I)
print('该宽度允许 %.2f mA' % (w*dens))
print('是否够用:', 'YES' if I < w*dens else 'NO, 需要宽度 %.2f um' % (I/dens))
"
```

预期：总电流 1000mA，2µm 只允许 1.6mA → 严重不够，需要重新划分 stripe 密度（不是无限加宽，而是增加条数分摊电流）。

过关标准：能解释"为什么不是把这一条加宽到 1250µm"（答案是：要用多条 stripe 并联分摊，单条超宽会挡住信号布线）。
:::

:::check
- 能说出电源从封装到单元的完整路径
- 知道 ring / stripe / rail 三层各自作用
- 会用 `addRing`、`addStripe`、`sroute` 三条命令
- 知道 via 阵列为什么必须打
- 能估算一条 stripe 的载流能力
:::

:::quiz
IR drop 是什么？阈值大概多少？|电流在金属电阻上产生的电压降。一般要求不超过标称电压的 3%~5%。
为什么电源 via 要打成阵列？|单个 via 电阻大、电流集中；阵列并联降低电阻、分散电流，避免局部过热和过大压降。
`addRing` 的 `-width` 和 `-spacing` 分别控制什么？|环的金属宽度（载流能力）和 VDD/VSS 之间的间距（防止短路）。
电源规划过度设计会带来什么问题？|占用过多面积，标准单元可用面积减少、利用率过高，导致布线拥塞和 DRC 违例。
发现某点 IR drop 超标，应该先看什么？|先看 via 覆盖（瓶颈常在层间连接），再看 stripe 密度是否够、电流是否集中。
:::
