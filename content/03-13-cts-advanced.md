---
id: 03-13-cts-advanced
no: 26
stage: 3
title: CTS（二）：约束、NDR、屏蔽与多时钟
en: CTS Constraints and Multi-Clock
hours: 4
minutes: 50
tags: [CTS, NDR, skew group, useful skew, multi-clock]
summary: 一棵树建得好不好，八成取决于约束写得对不对。这一课讲清 skew group、NDR 的施加范围、leaf/trunk 的单元选择、哪些引脚要屏蔽，以及多时钟与 generated clock 怎么分别建树。
status: live
---

## 分组：先决定"谁和谁比" {#group}

:::goal 学完这一课，你能写出一份完整的 CTS 约束文件——目标、NDR、单元、分组、屏蔽五节各有依据，并用五条命令自检，指出文件里每个数字为什么是那个值。
:::

先想一个运动会的场景。裁判要给运动员排名，前提是他们跑的是同一场比赛。把一百米选手和马拉松选手放进同一个榜单，第一名永远是最先冲过百米线的人，这个榜单没有意义。

CTS 也是这个道理。工具并不会把"全片所有触发器"当成一棵树去平衡，它先问一句：**这些叶子是同一场比赛的吗？** 是，才放进同一个组里互相对齐；不是，各建各的树，谁也不管谁。

这个"组"就是 **skew group（偏斜组）**。分组是 CTS 的第一步，也是最不该出错的一步，因为它出错时不报错——树照样建，报告照样出，只是你拿到的 skew 数字从一开始就没有意义。

:::term Skew Group | 偏斜组
一组由 CTS 工具放在一起做平衡的时钟叶子。工具只保证"同组内的叶子到达时间接近"，跨组不做任何平衡。

一个时钟默认对应一个 skew group；同一时钟如果物理上分成几块独立子树，也可以拆成多个组，分别压 skew。
:::

:::term Clock Group | 时钟组（异步组）
SDC 里用 `set_clock_groups -asynchronous` 声明的一组时钟：它们之间没有时序路径，STA 不做跨组检查。

它的作用是**告诉工具"这两边不用比"**。CTS 读到这个声明，就不会跨组做平衡。
:::

这两个词很容易混。一句区分：**clock group 是逻辑上的"不同步"，skew group 是物理上的"要对齐"。** 前者写在 SDC 里，影响 STA 和 CTS 的判断；后者写在 CTS 约束里，直接决定工具插多少 buffer。两者必须一致——SDC 说异步，CTS 却放进同一组，就会出现下面这种账。

### 分组错了会怎样：白插 300 个 buffer

假设一个设计里有两个时钟：`clk_cpu` 300MHz（周期 3.33ns），`clk_uart` 100MHz（周期 10ns），各自约 3000 个叶子。两个时钟来自不同晶振，异步。

正确的做法是两组分开建：`clk_cpu` 的树做到 latency 1.10ns，`clk_uart` 的做到 1.50ns，各管各的。

但如果约束里漏了分组，工具把它们当成一组，就必须把两边的叶子拉到同一时间。它会在 `clk_cpu` 那棵较浅的树上补延迟：

```
需要补的差 = 1.50 − 1.10 = 0.40ns
每级 buffer 延迟 ≈ 0.08ns  →  需要补 5 级
最后两级的分支数 ≈ 60 条  →  5 × 60 = 300 个 buffer
```

300 个 buffer 是什么概念？按后面第三课的手算，单个时钟 buffer 约 17µW，300 个就是 **5.1mW**。一个万门级设计总功耗常在 100mW 量级，这一下吃掉 5%。更糟的是 `clk_cpu` 那边多插了 5 级，级数变深、噪声变大，**skew 反而从 60ps 变成 85ps**——你付出了功耗，指标还退步了。

所以分组的第一原则不是"按频率分"，而是问一句：**这两个时钟之间有数据路径吗？**

| 两个时钟的关系 | 要不要同组 | 理由 |
|---|---|---|
| 同一 PLL 出来的 `clk` 与 `clk_div2`，之间有路径 | 同组 | 有路径就要对齐，不对齐的差直接吃这条路径的余量 |
| 不同 PLL、不同晶振，异步 | 不同组 | 没有路径可比，平衡纯属浪费 buffer |
| 同一时钟，物理上分左右两块子树 | 看跨区路径量 | 跨区路径多就同组；几乎没有就拆组，各自压更紧 |
| 同一时钟，功能模式与测试模式各一套 | 用 mode 定义隔离，不靠分组 | 测试时钟频率低，和功能时钟平衡没有意义 |

最后一行的做法值得单独说：**不要用"分组"去解决"模式"问题**。测试模式的时钟该用 `set_case_analysis` 或 mode 定义隔离，而不是硬塞进一个组里，否则功能模式下工具会为测试逻辑的引脚反复调平衡。

:::scene 周三下午，skew 报告里两个时钟打成一团
你接手一个双核 SoC 的 CTS。`report_clock_timing -type skew` 打出来，`clk_core` 的 skew 是 210ps，`clk_peri` 是 240ps，都超标。你第一反应是把 `target_skew` 从 80ps 收到 50ps，重跑一遍——结果 buffer 从 1800 涨到 2900，skew 只降到 190ps。

组长看了一眼你的 `cts.tcl`，问："这两个时钟之间有几条路径？"你打开 SDC 才发现，`clk_peri` 是独立晶振，和 `clk_core` 完全异步，但你的约束里没有分组，工具一直在把它们往一块拉。他把 `set_clock_groups -asynchronous` 加进去，重跑，buffer 回到 1750，两个时钟各自 70ps 和 85ps。

**你花了一下午调的那个参数，本来不该调。**
:::

:::pitfall 把异步时钟放进同一组，工具白插 300 个 buffer
现象：两个异步时钟的 skew 都超标，`target_skew` 收紧后 buffer 数暴涨、skew 只降一点，功耗涨了 5%。

原因：SDC 里没有 `set_clock_groups -asynchronous`，CTS 默认把它们当成一组，为了"组内平衡"在较浅的那棵树上补了 5 级 buffer。

怎么查：先跑 `report_clocks` 列出全部时钟，再问自己每个时钟和别的时钟有没有路径。有路径才能同组；没路径就在 SDC 里声明异步。

怎么避免：分组写在 CTS 约束之前，作为第 0 步。写完用 `report_ccopt_skew_group`（不同版本命令名可能不同）确认组的数量与预期一致。
:::

## NDR：加在树的哪一段 {#ndr}

NDR 的定义在《CTS 时钟树（一）》里讲过：给时钟网络单独指定的线宽与间距。这一课要解决的是**加在哪一段**。

一棵树从根到叶子，物理性质完全不同，所以不能一刀切：

```text
# 示意图：三段时钟网络的划分（不是命令输出）
  端口 / PLL 输出
        │
        ├── top 段：源到第一个 buffer，往往最长、最靠近模拟电路
        │
     [buf] ── trunk 段：前 1~2 级，一个 buffer 驱动几十个分支，电流最大
        │
   ┌────┴────┐
 [buf]     [buf] ── leaf 段：最后一级到触发器 CK，线短、数量多、贴着标准单元
   │         │
  FF FF     FF FF
```

三段的划分在真实版图上长这样：

:::fig innovus-cts | 时钟树综合后的版图：绿色线条是时钟网络，绿点是工具插入的缓冲器。重点看从树根分出来的粗壮主干（trunk，该上 2w2s）和贴着标准单元的末端细枝（leaf，1w2s 就够）——NDR 的三段规则就是照这个形状给的。
:::

从这张图里要看出什么：离根越近的线越少越粗、越靠近叶子越密越细——三段的电流、线长、周边环境都不同，这就是"不能一刀切"的依据。

:::term Trunk / Leaf / Top | 主干 / 叶子 / 根网
CTS 工具把时钟网络按位置分三段：

**top**：从时钟源（端口或 PLL）到第一个 buffer 的那一段，通常最长。
**trunk**：树的前 1~2 级，负责把时钟扇出去，一根线要驱动几十个下游分支。
**leaf**：最后一级 buffer 到触发器时钟引脚的那一小段，线很短，但条数最多。

三段的电流、线长、周边环境都不同，所以 NDR 要分开给。
:::

为什么要分？看三个物理事实：

1. **top 段最长，电阻最大。** 这段线的延迟能占整个 insertion delay 的三成。线宽加倍、电阻减半，收益最直接。
2. **trunk 段电流最大。** 它要给下游所有叶子供电，电流是 leaf 段的几十倍，电迁移（EM）风险最高。宽线是唯一解。
3. **leaf 段最密。** 它挤在标准单元中间，线宽加倍会挤占邻居的布线空间，触发 spacing 违例。

所以工程上的常见配置是：**top 和 trunk 用 2w2s（双宽双距），leaf 用 1w2s（单宽双距）**。

| 段 | 典型 NDR | 理由 | 用错的后果 |
|---|---|---|---|
| top | 2w2s | 最长、最敏感，需要最低电阻 | 用 1w2s：延迟大 100~200ps |
| trunk | 2w2s | 电流最大，EM 卡得最紧 | 用默认规则：EM 违例，签核不过 |
| leaf | 1w2s | 短，双宽收益小；双距防串扰 | 用 2w2s：leaf 区 spacing DRC 成片 |

### 过用 NDR 的代价：12% 的布线资源

NDR 不是免费的。一条 2w2s 的线，占用的横向资源不是 2 倍，而是接近 3 倍：线宽占 2 条轨道，两侧间距各占 1 条，合计约 4 条轨道减去原本的 1 条。

算一笔账。全片 40000 条信号网络，其中时钟网络 2000 条（5%）：

```
普通网络：40000 条 × 1 条轨道 = 40000 轨道当量
时钟网络： 2000 条 × 2.5 条轨道 = 5000 轨道当量（2w2s 取 2.5，偏保守）
总需求  = 45000 轨道当量
时钟占比 = 5000 ÷ 45000 = 11.1%
```

如果把 leaf 也全部上 2w2s，系数从 2.5 涨到 3.0，时钟占用变成 6000，占比 13%。**所以"时钟网络吃掉 12% 布线资源"是个可信的量级**——它只占 5% 的网络条数，却占了八分之一的地。

这个数字在 review 里有实际用途：当布线阶段出现大面积拥塞，而时序又没明显问题时，先问一句"时钟 NDR 是不是给太满了"。把 leaf 从 2w2s 降到 1w2s，通常能收回 2~3 个百分点的布线资源，代价只是 leaf 的 transition 差 10~15ps。

:::pitfall NDR 写了但没生效
现象：布线后抽一条时钟线量宽度，还是默认的 1 倍；EM 报告照样一片红。

原因有三种，按出现频率排：① 属性写在了错的 net type 上（写在 leaf，实际那段是 trunk）；② NDR 定义在 `add_ndr` 之后又被别的约束覆盖；③ 时钟网络在布线时被当成普通信号网络处理（`setAttribute` 里的 net type 没打上）。

怎么查：布线后 `dbGet` 一条主干 net 的 `wire.width`，和默认宽度比；不看报告，看实际几何。**属性是意图，宽度是事实。**
:::

## 单元选择：leaf 只用 X4 以上 {#cells}

时钟树上的单元清单，是 CTS 约束里最容易被抄来抄去的部分。抄错一个 X1，后面 transition 怎么修都修不干净。

先解释 `X` 是什么。库里的单元名常写成 `BUFX4`、`INVX8`，X 后面的数字是**驱动能力倍数**，以最小驱动单元为 1。X4 的意思是"在同样负载下，输出电阻约为 X1 的四分之一"。

延迟的粗略关系是 `t ∝ R_eq × C_load`。R_eq 减到 1/4，延迟也接近 1/4（实际没这么理想，还有自载和输入电容）。

手算一次，看 X1 为什么不能做 leaf。假设一个 leaf buffer 要带 12 个触发器，总负载 25fF，输出电阻取量级假设值：

```
X1：R_eq ≈ 4kΩ  →  驱动项 ≈ 4k × 25f = 100ps，加上本身延迟，transition 到 180ps
X4：R_eq ≈ 1kΩ  →  驱动项 ≈ 1k × 25f =  25ps，transition 约 70ps
```

时钟网络的目标 transition 是 120ps。X1 一开始就超了，而且工具会为了修这个违例在它前面再插一级——**一个错误的单元选择，会连锁产生三四个多余的 buffer**。

所以 leaf 的规则是硬的：**最小 X4，常用 X4/X8 混搭**。trunk 可以用到 X8/X12，因为要驱动几十个分支。

### inverter 成对使用：为什么能省面积

《CTS 时钟树（一）》提过 `use_inverters true`，这里讲原理。

一个 buffer 在电路上就是两级反相器串联。库里卖的 `BUFX4`，内部通常就是一个弱反相器加一个强反相器，封在一个单元里。

CTS 工具更愿意用**分立的两个反相器**，原因有三个：

1. **中间多了一个节点。** 两级分开，工具可以在中间接一小段线、分摊负载，比封装在一起更灵活。
2. **尺寸可以自由组合。** `INVX2 → INVX8` 这种"前小后大"的组合，输入电容只有 X2 那么大，上一级的 transition 更好；输出却能驱动 X8 的负载。
3. **面积更小。** 同样驱动能力下，两个分立反相器的面积通常比一个 buffer 小 10%~20%（典型值，具体看库）。

代价是极性。一级反相会把时钟翻过来，**必须成对出现**。这也是为什么约束里要写 `use_inverters true` 而不是让工具随便用——它要保证从根到每片叶子的反相次数奇偶一致。

如果同一条时序路径的发射端和捕获端反相次数一奇一偶，两端的有效时钟沿就差半个周期。这种错**在 skew 报告里看不出来**（skew 只看到达时间，不看极性），只有 hold 检查或功能仿真会暴露。所以反相器好用的前提，是工具真的在数极性。

| 单元类型 | 允许用在哪 | 理由 |
|---|---|---|
| `BUFX4` / `BUFX8` | leaf、trunk | 驱动够，面积可接受 |
| `BUFX12` 及以上 | 只 trunk | leaf 用大驱动是浪费，输入电容还拖累上一级 |
| `INVX4` / `INVX8` | leaf、trunk（成对） | 省面积，输入电容低 |
| `BUFX1` / `BUFX2` | 不用 | transition 超标，会连锁插 buffer |
| `DEL*`（延迟单元） | 不用 | 它不是时钟单元，延迟随电压漂移大 |
| 低 Vt 单元 | 不用 | 漏电高，时钟又不能关断，功耗常驻 |

### `dont_use` 清单怎么定

做法不是"把清单写成允许清单"，而是**两头都写**：先 `set_dont_use` 禁掉不该出现的，再用 `buffer_cells` 限定可用的。只写一头，工具总能在缝隙里找到你没禁的怪单元。

```tcl
# 作用：把时钟树上不该出现的单元禁掉，再给出允许清单
# 用法：读入库之后、ccopt_design 之前执行；单元名按你的库改，先用 get_lib_cells 列一遍
set_dont_use [get_lib_cells */*BUFX1]        ;# 驱动太弱，leaf 上必超 transition
set_dont_use [get_lib_cells */*BUFX2]        ;# 同上，X2 只适合极短的内部分支
set_dont_use [get_lib_cells */*DEL*]         ;# 延迟单元：延迟随 PVT 漂移，不适合时钟
set_dont_use [get_lib_cells */*LVT*]         ;# 低阈值单元：漏电大，而时钟关不掉

set_ccopt_property buffer_cells   {BUFX4 BUFX8 BUFX12}    ;# 允许的缓冲器
set_ccopt_property inverter_cells {INVX4 INVX8 INVX12}    ;# 允许的反相器
set_ccopt_property use_inverters  true                    ;# 允许成对反相，省面积
```

表里那条"低 Vt 不用"值得多说一句。低阈值单元的开关速度快，很多设计会在关键路径上大量使用。代价是它的**静态漏电**明显高于标准单元，而时钟网络上的这类单元数量多、又没法用 power gating 关掉（时钟必须一直通着），这部分漏电是常驻的。一个设计里时钟网络常占三成以上的单元数，这笔常驻漏电在功耗报告里能直接看到。

:::pitfall 把时钟 MUX 也 dont_use 了
现象：CTS 报错说某个时钟网络找不到可用单元，或者 MUX 后面的树根本没建起来。

原因：`set_dont_use */*MUX*` 这种通配写得太狠，把时钟 MUX（glitch-free 的那种）也禁了。时钟 MUX 是时钟路径上的合法单元，不能禁。

处理：通配符要收敛到具体单元名，或者禁完之后用 `get_lib_cells` 反查一遍清单里还剩什么。**通配符是省事，也是事故来源。**
:::

## 屏蔽：哪些引脚不该进树 {#skip}

"屏蔽"（skip / exclude）的意思是：这个引脚挂在时钟网络上，但**不要参与平衡**。

听起来矛盾——时钟树的目的不就是让所有引脚对齐吗？不是。有些引脚的时序根本不靠对齐来保证，把它们拉进来反而有害。

三类该屏蔽的引脚：

**第一类：测试逻辑。** BIST（内建自测试）控制器、扫描链的测试时钟引脚，在功能模式下是静态的。它们和功能触发器之间没有功能路径，拉进同一组平衡只会让工具为了一个从不翻转的引脚去调整整棵树。

**第二类：常开宏的 CK。** 电源域不同（always-on 域），时钟来自独立的常开时钟源。它和主树的电源、电压、延迟特性都不一样，物理上也不该绑在一起。

**第三类：手工平衡的部分。** 模拟 IP 内部自带时钟树，或者某个高速接口已经用 H 树手工做完了平衡。这些部分的延迟是设计好的，工具再插一级就破坏了。

```tcl
# 作用：把不该参与平衡的时钟引脚排除掉（属性名各版本有差异，敲前 man 一次）
# 用法：ccopt_design 之前执行；先跑 report_clock_tree -skipped 看当前清单
set_ccopt_property -pin [get_pins u_dft/mbist_ctrl/CK] sink_type ignore   ;# 测试时钟，功能模式静态
set_ccopt_property -pin [get_pins u_pmu/ao_ctl/CLK]    sink_type ignore   ;# 常开域，独立时钟源
set_ccopt_property -pin [get_pins u_ddr_phy/clk_in]    sink_type ignore   ;# PHY 内部已手工平衡
```

上面三行的属性名和取值在不同 Innovus 版本里不一样（有的版本写作 `exclude`，有的用单独的 skew group 排除名单）。**课程环境跑不了完整 CTS，真实项目里先 `man set_ccopt_property` 查一次再写。** 要记住的是机制，不是拼写：

- 屏蔽是**按引脚**打的，不是按网络；
- 屏蔽只影响"平衡"，不影响"布线"；
- 屏蔽清单要能在报告里被列出来，否则等于没写。

### 屏蔽写错的两个方向

**屏蔽多了**：那些触发器不在任何组里，skew 报告里看不到它们。你以为 skew 达标了，等 STA 用真实延迟一算，接口路径全崩。判断方法：每个时钟域的 sink 数应该等于该域触发器数 + ICG 数 + 宏的 CK 数，对不上就说明有引脚被漏掉了。

**屏蔽少了**：工具去平衡一个本来不该平衡的引脚，白插 buffer；更麻烦的是测试模式下时钟被"优化"过，扫描链移位的时序出问题。

查的办法就一条命令：

```tcl
# 作用：列出所有被排除在时钟树之外的引脚，逐条核对
# 用法：ccopt_design 之后执行；清单条数应等于你预期的屏蔽数
report_clock_tree -skipped > rpt/cts_skipped.rpt   ;# 被 skip 的引脚清单
```

读这份报告的方法：不要只看条数，要**按前缀归类**。如果 `u_dft/*` 有 128 条、`u_pmu/*` 有 4 条、`u_ddr_phy/*` 有 2 条，加起来 134 条，和你写的屏蔽清单对得上，就说明没有意外遗漏。

:::pitfall skip 写成了"不布线"
现象：CTS 完成后，某一片触发器的时钟引脚完全没有连线，`check_timing` 报这些端点没有时钟。

原因：把"不进平衡"和"不布线"当成了一件事。前者是 `sink_type ignore` 这类属性，后者是 `set_dont_touch` 或 net 级别的 `skip_routing`。后者会让时钟线根本不画。

处理：屏蔽只用"平衡"这一类属性；确认方法是在布线后看那条 net 有没有几何。**"不参与"和"不存在"是两件事。**
:::

## 多时钟：主时钟、generated clock 与 MUX {#multi}

一个芯片里通常不止一个时钟。CTS 要处理的不是"一个时钟建一棵树"，而是"每个时钟源各建一棵树，交叉的地方特殊处理"。

多时钟的整体关系，先看这张三层图：

:::fig cts-multiclock | 多时钟建树的三层关系：主时钟 → 分频（generated clock）→ MUX → 叶子。重点看 MUX 那一层——它让工具必须同时满足两条时钟路径，也最容易被漏掉约束；每一层的约束写法都不一样，正是接下来两小节的内容。
:::

从这张图里要看出什么：每个时钟源各建一棵树，真正的难点在交叉点——generated clock 的 -source 和 MUX 的 SEL，这两处写错树照样建，只是从一开始就建错了。

### 主时钟与 generated clock

`create_clock` 定义的是**源头**：外部晶振送进来的、PLL 输出的，都算源头。`create_generated_clock` 定义的是**从某个时钟派生出来的**：分频器输出、门控后的时钟、MUX 选出来的时钟。

```tcl
# 作用：定义主时钟与分频时钟，让 CTS 知道这是两棵有关系的树
# 用法：SDC 里写，CTS 之前 source 进来；-source 指向分频器的输入引脚，不是输出
create_clock -name clk_ref -period 10.0 [get_ports clk_ref]         ;# 100MHz 主时钟
create_generated_clock -name clk_div2 \
    -source [get_pins u_div/CK] \
    -divide_by 2 [get_pins u_div/Q]                                 ;# 50MHz 分频时钟，源指向 CK
```

`-source` 指错是这里最常见的错。指向分频器的**输入**（CK），工具才知道"这个时钟是从主时钟分出来的，两者有相位关系"；指向输出（Q），工具会把它当成一个独立时钟，两棵树之间不做任何关联，跨这两个域的路径时序就没法算。

分频和倍频的区别要记：

| 派生方式 | 写法 | CTS 怎么处理 |
|---|---|---|
| 二分频 | `-divide_by 2` | 与主时钟同组平衡（有路径） |
| 三分频 | `-divide_by 3` | 同上，但只有部分沿对齐，平衡要求更严 |
| PLL 倍频输出 | 直接 `create_clock` | 它是新源，单独一组，不和输入时钟平衡 |
| 门控时钟 | 不需要单独定义 | ICG 的输出仍在同一棵树里，但要做 clock gating check |

PLL 倍频为什么用 `create_clock` 而不是 `create_generated_clock`？因为 PLL 输出经过了模拟电路，相位和输入的关系由 PLL 自己保证，工具不该假设它和输入同相。把它当新源，独立建树，是最安全的做法。

### 时钟 MUX 后面怎么建树

时钟 MUX 是 CTS 里最麻烦的结构：两路时钟进一个 MUX，出一路时钟驱动一大片逻辑。工具站在 MUX 输出往上看，看到两个"父亲"。

正确的理解是：**MUX 输出是一个新的根，从它往下的树是共享的；从每个输入到 MUX 是各自的 top 段。**

```text
# 示意图：时钟 MUX 的两段结构
  PLL_A ──┐
          ├──[MUX]──┬── buf ──┬── FF ...
  PLL_B ──┘   ↑     │         └── FF ...
            SEL     └── 共享树（一段）
```

建树时工具会做两件事：给 MUX 输出往下建一棵共享树；给两个输入各建一段到 MUX 的 top 段。麻烦在于 **SEL 端**——CTS 时它是什么值，工具不知道。

三种处理方式，按场景选：

| 场景 | 写法 | 结果与风险 |
|---|---|---|
| SEL 是静态的（strap 引脚、测试模式引脚） | `set_case_analysis 0 [get_pins u_mux/SEL]` | 只按一路建树，跑得快；另一模式必须单独复查 |
| SEL 运行时切换（两个 PLL 做备份） | 不做 case analysis，让工具两路都建 | 两路 latency 分别报告；共享树要同时满足两路 |
| 两路互斥、从不同时有效 | `set_clock_groups -logically_exclusive` | STA 分别检查，CTS 不跨组平衡 |

第一种最常用，也最容易埋坑：你 `set_case_analysis` 设了 0，只检查了 A 路，B 路从来没建过树。等芯片切到 B 路，skew 大得离谱。**所以用 case analysis 之后，必须把 SEL 换成另一个值再跑一遍 CTS 的报告检查**，至少确认 B 路的树能建起来、latency 在可接受范围。

第二种的风险是工具会试图"兼顾"两路，可能在共享段上插一堆 buffer 去平衡两种 latency，结果两路都不理想。判断标准是看 `report_clock_timing` 里两路的 latency 差：差超过 200ps 就说明共享段在妥协，要考虑把共享树拆短，让 MUX 更靠近叶子。

还有一条物理约束：**时钟 MUX 必须是 glitch-free 的**（切换时不会产生窄脉冲）。这不是 CTS 能修的，是设计阶段选型的事。后端能做的是检查：切换瞬间两路时钟是否都在低电平。课程环境跑不了这个检查，真实项目里用门级仿真或专门的 clock glitch 检查。

:::term Generated Clock | 生成时钟
由 `create_generated_clock` 定义的、从另一个时钟派生出来的时钟。分频器输出、MUX 输出、门控后的时钟都属于这一类。

关键是 `-source` 要指向派生点的**输入**，这样工具才知道它和父时钟的相位关系。
:::

:::term Clock MUX | 时钟多路选择器
两路或多路时钟进、一路时钟出的选择器。CTS 把它当作一个新的根：输出往下建共享树，每个输入到 MUX 各是一段 top。

它不是普通 MUX——切换时不能产生窄脉冲，否则下游触发器会采到半个周期。
:::

## 一份完整的 CTS 约束文件 {#script}

前面五块拼起来，就是一份能交给批处理跑的 `cts.tcl`。分六节，每节开头一行注释说明这一节负责什么。

```tcl
# ============================================================================
# cts.tcl —— CTS 约束：目标 / 规则 / 单元 / 分组 / 屏蔽
# 用法：在 ccopt_design 之前 source；前提是 SDC 已经把时钟定义清楚
# ============================================================================

# ---- 0. 开工检查：时钟认得全不全 ----
report_clocks                                 ;# 列出全部时钟：名字、周期、源端口
check_timing -include {unconstrained}         ;# 有未约束端点就先停下，别急着建树

# ---- 1. 目标：三个数 ----
set_ccopt_property target_skew       0.080    ;# 全局 skew 80ps（2.5ns 周期的 3.2%）
set_ccopt_property target_max_trans  0.120    ;# 时钟网络 transition 上限 120ps
set_max_transition 0.120 [get_clocks *]       ;# SDC 侧再写一遍，两处一致才不会被覆盖

# ---- 2. 规则：NDR 分三段 ----
add_ndr -name cts_2w2s -width_multiplier 2 -spacing_multiplier 2   ;# 双宽双距：根与主干
add_ndr -name cts_1w2s -width_multiplier 1 -spacing_multiplier 2   ;# 单宽双距：叶子
set_ccopt_property -net_type top   ndr cts_2w2s   ;# 源到第一个 buffer
set_ccopt_property -net_type trunk ndr cts_2w2s   ;# 前 1~2 级
set_ccopt_property -net_type leaf  ndr cts_1w2s   ;# 最后一级到 sink

# ---- 3. 单元：先禁弱的，再给允许清单 ----
set_dont_use [get_lib_cells */*BUFX1]         ;# X1 驱动不够，leaf 上必超 transition
set_dont_use [get_lib_cells */*BUFX2]         ;# X2 同样偏弱
set_dont_use [get_lib_cells */*DEL*]          ;# 延迟单元不是时钟单元
set_ccopt_property buffer_cells   {BUFX4 BUFX8 BUFX12}    ;# 允许的缓冲器
set_ccopt_property inverter_cells {INVX4 INVX8 INVX12}    ;# 允许的反相器
set_ccopt_property use_inverters  true        ;# 成对反相，省面积、输入电容低

# ---- 4. 分组：谁和谁比 ----
# 前提：SDC 里已声明 clk_core 与 clk_ddr 异步（set_clock_groups -asynchronous）
create_ccopt_skew_group -name sg_core -sources [get_ports clk_core] -auto_sinks  ;# 核心时钟单独成组
set_ccopt_property -skew_group sg_core target_skew 0.060   ;# 核心域更紧
create_ccopt_skew_group -name sg_ddr -sources [get_ports clk_ddr] -auto_sinks    ;# DDR 时钟单独成组
set_ccopt_property -skew_group sg_ddr target_skew 0.100    ;# DDR 负载少，可放宽

# ---- 5. 屏蔽：不该进树的引脚 ----
set_ccopt_property -pin [get_pins u_dft/mbist_ctrl/CK]  sink_type ignore  ;# 测试时钟
set_ccopt_property -pin [get_pins u_pmu/ao_ctl/CLK]     sink_type ignore  ;# 常开域
set_ccopt_property -pin [get_pins u_ddr_phy/clk_in]     sink_type ignore  ;# PHY 内已平衡

# ---- 6. 建树 ----
ccopt_design -cts
```

逐节说清"这行在干什么、写错了会怎样"：

- **第 0 节**：`report_clocks` 是给自己看的，确认工具认到的时钟数量和你以为的一致。`check_timing` 里 `unconstrained_endpoints` 不为 0 就先修约束——树一旦按错的时钟建完，后面全要重来。
- **第 1 节**：`target_skew` 按周期的 3%~5% 给，不要拍脑袋。`set_max_transition` 在 SDC 和 ccopt 属性里各写一遍是刻意的：有些流程会用 SDC 的值覆盖属性，两处一致才不会互相打架。
- **第 2 节**：`add_ndr` 只是定义规则，`-net_type` 才是施加。三段都写上，等于告诉工具"别用默认规则"。
- **第 3 节**：`dont_use` 和允许清单是两道闸。只写允许清单，工具仍可能在合法集合里挑到你不想要的低 Vt 版本。
- **第 4 节**：`-auto_sinks` 让工具自己找该时钟域下的所有叶子。这里的前提是第 0 节的时钟定义准确——源写错，叶子就找错。
- **第 5 节**：屏蔽放在分组之后，因为分组会先"认领"叶子；先屏蔽再分组，可能出现某个组空了。
- **第 6 节**：建树。跑完立刻存盘，`saveDesign db/06_cts.enc`，这是后面所有对比的基线。

最容易写错的八行，单独列一张对照表。评审前拿它逐行扫一遍，比通读全文快。

| 行 | 常见的错写法 | 后果 |
|---|---|---|
| `target_skew 0.080` | 写成 `0.008`（少一个零） | buffer 数暴涨两三倍，功耗翻倍，skew 只改善几十 ps |
| `set_max_transition` | 只写在 ccopt 属性里，SDC 里没写 | 被 SDC 的默认值覆盖，属性白设 |
| `-net_type top` | 漏掉 top 这一行 | 端口到第一级仍是默认线宽，延迟多 100ps 量级 |
| `add_ndr` 的 multiplier | 只加 spacing、不加 width | 电阻没降，延迟和 EM 都不改善，只省了串扰 |
| `set_dont_use` | 通配写成 `*BUF*1` | 把 BUFX1 之外的一批单元也误禁，工具找不到可用单元 |
| `-auto_sinks` | 手写 `-sinks` 且漏了一部分 | 漏掉的叶子不在组里，skew 报告里看不见它们 |
| `sink_type ignore` | 写成 `skip_routing` 一类 | 时钟线根本不画，端点变成"没有时钟" |
| `ccopt_design -cts` | 漏了 `-cts` | 建树和时序优化一起跑，出问题分不清是哪一步 |

## 约束写完的自检清单 {#checklist}

约束文件写完不能直接跑，先用五条命令过一遍。每条都有明确的判据。

```tcl
# 作用：CTS 约束的五项自检，全过才允许 ccopt_design
# 用法：source 完 cts.tcl、建树之前逐条执行；输出存 rpt/ 并写进交接记录
check_timing -include {unconstrained}        ;# ① 未约束端点必须为 0
report_clocks                                ;# ② 时钟数量、周期、源端口逐个核对
report_ccopt_skew_group                      ;# ③ 每个组的 sink 数是否等于该域触发器数
get_ccopt_property -net_type trunk ndr       ;# ④ 读回 NDR，确认三段都挂上了
report_clock_tree -skipped                   ;# ⑤ 屏蔽清单条数与预期一致
```

| # | 检查项 | 判据 | 不通过先查什么 |
|---|---|---|---|
| 1 | 未约束端点 | `unconstrained` 为 0 | 时钟没定义、名字写错、经过非时钟单元断了传播 |
| 2 | 时钟清单 | 数量、周期、源端口与 SDC 一致 | 用了旧的 SDC、generated clock 的 `-source` 指错 |
| 3 | 分组 | 每组 sink 数 = 该域 FF + ICG + 宏 CK | 分组漏了某个时钟、`-auto_sinks` 没找到 |
| 4 | NDR | 三段都能读回规则名 | 属性写在错的 net type、被后续约束覆盖 |
| 5 | 屏蔽 | 条数 = 预期，且前缀能归类 | 通配符打太宽、只写了 skip 布线没写 skip 平衡 |

第 3 项的判据值得单独强调。**sink 数是唯一能证明"分组没漏"的数字。** 假设 `clk_core` 域有 5800 个触发器、210 个 ICG、4 个宏的 CK，那 `sg_core` 的 sink 数就该是 6014。报出来是 5000，说明有 1000 个叶子没被认领；报出来是 6300，说明混进了别的域的叶子。两个方向都要查。

第 4 项在读回的时候要注意：`get_ccopt_property` 返回空，不一定是没设，也可能是设在了另一个 net type 上。逐段读——top、trunk、leaf 各读一次，别只读一个就下结论。

:::note 五项之外，还有一项靠人看
五项都是"数字对不对"，还有一项是"图对不对"：打开时钟树的飞线图，看主干是不是从根均匀扇出去、有没有一条分支绕了大半个芯片。这一项没有命令，三十秒能看出来，但九成的绕线问题都是这么发现的。
:::

## 工作中怎么用：约束是谁的责任 {#in-work}

**谁写**：PR 工程师本人。CTS 约束通常不是从零写，而是从上个项目或模板改——这既是效率，也是风险来源。改模板时最容易漏的三处：分组没跟着新时钟更新、`dont_use` 清单里还留着上个项目的单元名、屏蔽清单指向了不存在的实例（工具不报错，因为 `get_pins` 返回空）。

**谁 review**：资深 PR 或 STA 工程师。review 只看四件事：分组和 SDC 是否一致、NDR 三段是否合理、单元清单里最小的驱动是多少、屏蔽清单能不能逐条说出理由。

**交付什么**：一份 `cts.tcl`、一份五项自检的输出、一页说明（每个数字的依据）。三样东西缺一样，下一版就没人敢改。

**做错了会怎样**：约束错的代价不是"重跑一次"。分组错，树建完才发现，要重建；NDR 错，布线后才发现，要重布；屏蔽错，STA 签核时才发现，要回退到 CTS。**这三件事的返工量依次是小时、天、周。** 所以约束阶段的半小时自检，是整条流程里性价比最高的半小时。

:::lab 动手：把一份 CTS 约束补齐并自检
**任务**：下面这份 `cts.tcl` 有 5 处空缺（标了 `TODO`），补全后用命令验证。

```tcl
# 作用：待补全的 CTS 约束骨架
# 用法：复制到 cts_lab.tcl，补完 5 个 TODO 后 source
# ---- 目标 ----
set_ccopt_property target_skew TODO1          ;# 周期 2.0ns，按 4% 给
set_ccopt_property target_max_trans 0.120
# ---- 规则 ----
add_ndr -name cts_2w2s -width_multiplier 2 -spacing_multiplier 2
set_ccopt_property -net_type trunk ndr TODO2  ;# 主干用什么规则
set_ccopt_property -net_type leaf  ndr cts_1w2s
# ---- 单元 ----
set_dont_use [get_lib_cells */*BUFX1]
set_ccopt_property buffer_cells TODO3         ;# 只允许 X4 及以上
# ---- 分组 ----
create_ccopt_skew_group -name sg_a -sources [get_ports clk_a] -auto_sinks
set_ccopt_property -skew_group sg_a target_skew 0.080
# ---- 屏蔽 ----
set_ccopt_property -pin [get_pins TODO4] sink_type ignore   ;# 测试时钟引脚
```

**步骤**：
1. 补 `TODO1`：算出 2.0ns 周期的 4% 是多少 ps，写成 ns。
2. 补 `TODO2`：主干该用 `cts_2w2s` 还是 `cts_1w2s`，说一句理由。
3. 补 `TODO3`：写出允许清单（至少三个单元）。
4. 补 `TODO4`：写一个合理的测试时钟引脚路径。
5. 跑五项自检命令，把每项的输出各抄一行到一张表里。

**过关标准**：能说出 `TODO1` 是 0.08 而不是 0.02 的理由；能解释 `TODO2` 为什么主干用双宽；能在自检表里指出哪一项不通过、下一步改哪一行。
:::

:::quiz
skew group 和 clock group 的区别是什么？|skew group 是 CTS 里"放在一起做平衡的叶子集合"，决定工具插多少 buffer；clock group 是 SDC 里"彼此异步、不做时序检查"的时钟集合，决定工具要不要跨组比较。两者必须一致。
把两个异步时钟放进同一组，会发生什么？|工具为了组内平衡，在较浅的那棵树上补延迟。按 400ps 差、每级 80ps 算要补 5 级，涉及约 60 个分支，就是 300 个多余 buffer，功耗涨约 5mW，skew 还可能变差。
NDR 为什么要分 top / trunk / leaf 三段？|三段物理性质不同：top 最长、电阻最大；trunk 电流最大、EM 最紧；leaf 最密、线最短。统一规则要么收益不足，要么造成 spacing DRC。
2w2s 的时钟网络大概吃掉多少布线资源？|时钟网络约占网络条数的 5%，但每条占 2.5~3 倍轨道，折算下来占 12% 左右的布线资源。
leaf 为什么不允许用 X1、X2？|驱动太弱，带 12 个触发器（约 25fF）时 transition 会到 180ps，超过 120ps 的目标；工具为了修它会在前面再插级，连锁产生多余 buffer。
inverter 成对使用为什么能省面积？|两级反相等于 buffer，但中间多一个节点可以分摊负载、尺寸能自由组合（前小后大降低输入电容），同驱动下面积比 buffer 小 10%~20%。
generated clock 的 -source 应该指向哪里？|指向派生点的输入引脚（比如分频器的 CK），这样工具才知道它和父时钟的相位关系；指向输出会被当成独立时钟，跨域路径没法算。
时钟 MUX 的 SEL 用 set_case_analysis 固定后，还必须做什么？|把 SEL 换成另一个值再检查一遍，确认另一路的树也能建起来、latency 可接受。只查一路等于只验了一半芯片。
report_clock_tree -skipped 用来查什么？|列出被排除在时钟树平衡之外的引脚，用来核对屏蔽清单有没有多写或漏写；条数要能和预期逐条对上。
:::

:::check
- 能说清 skew group 与 clock group 的区别，并判断两个时钟该不该同组
- 能手算"分组错误导致多插多少 buffer、多耗多少功耗"
- 能说出 NDR 三段各自用什么规则，以及过用 NDR 的资源代价量级
- 能解释 leaf 为什么最小 X4，以及 inverter 成对使用省面积的三条原因
- 能列出三类该屏蔽的引脚，并用 `report_clock_tree -skipped` 核对
- 能写出一份分六节的 `cts.tcl`，并说清每节写错的后果
- 能跑完五项自检，并用 sink 数判断分组有没有漏
:::
