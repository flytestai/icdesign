---
id: 03-12-chipfinish
no: 23
stage: 3
title: ChipFinish：收尾这一步，决定能不能送厂
en: Chip Finishing & Tapeout Handoff
hours: 2
minutes: 28
tags: [ChipFinish, filler, metal fill, tapeout, 交付物]
summary: 布完线、时序过了，还差七件收尾事：填 filler、铺 metal fill、加 seal ring 与 pad、跑最终 DRC/LVS、出交付物、写报告、做一次"别人能接手"的交接。
---

## ChipFinish 到底在收什么 {#what}

`route_opt` 之后，版图上到处是空隙：单元之间有空位、金属层有大片空白、芯片边缘没有保护环。这些东西不影响时序，但**会让工厂做不出来或者做出来就坏**。

| 收尾动作 | 为什么必须做 | 不做会怎样 |
|---|---|---|
| 填 filler cell | 标准单元行里不能留空，否则阱/衬底不连续 | 工艺厂拒收；LVS 报大量错误 |
| 铺 metal fill | 金属密度不均会导致化学机械抛光（CMP）不平 | 芯片表面不平，后层光刻失焦 |
| 加 seal ring | 芯片四周的保护环，防止切割时裂开 | 切割崩边、水汽进入，良率暴跌 |
| 加 bond pad | 对外连接的焊盘 | 无法封装 |
| 最终 DRC/LVS | 确认版图与网表都合法、且一致 | 送厂被拒，或做出来是错的 |
| 出交付物 | 给工厂的文件包 | 工厂没法开工 |

:::term Filler Cell | 填充单元
没有逻辑功能的标准单元，只用来"占位"。填在标准单元行的空隙里，保证每行的阱、电源轨、衬底是连续的。

库里通常有 `FILL_X1/X2/X4/X8` 几种宽度，工具按空隙宽度自动选。
:::

:::scene 送厂前一周被退回
你交了 GDS，工厂回邮件：**"Metal density violation on Metal3: 18% (min 30%)"**。

意思是 metal3 这一层只铺了 18% 的金属，低于工艺要求的最低密度 30%。原因：你没铺 metal fill。补一遍要重跑 DRC + 重新出 GDS，一周没了。
:::

## 填 filler：顺序错了会把时序搞坏 {#filler}

```tcl
# Innovus
addFiller -cell {FILL_X8 FILL_X4 FILL_X2 FILL_X1} -prefix FILLER
# 从大到小填：先大块填掉大部分空隙，小块补缝

# ICC2
create_stdcell_fillers -lib_cells {FILL_X8 FILL_X4 FILL_X2 FILL_X1}
# 同样从大到小
```

| 顺序 | 结果 |
|---|---|
| 大到小（X8 → X1） | 空隙填得满，filler 数量少，正确 |
| 小到大（X1 → X8） | 全是 X1，数量爆炸；或者大块空隙填不进 X8 留下缝 |
| 只填一种 | 缝隙填不满，阱不连续，LVS 报错 |

:::pitfall 填完 filler 不重新检查时序
filler 会改变局部电容，理论上影响很小，但**如果 filler 用了带 decap 的单元（去耦电容），会影响电源网络的充放电行为**。

规矩：填完 filler 后重跑一次 `report_timing`，确认 WNS 没变。变了就查是不是 filler 引起的。
:::

## metal fill：为了抛光平整 {#metalfill}

化学机械抛光（CMP）是把芯片表面磨平。如果某一层金属疏密不均，磨的时候软的地方磨得多、硬的地方磨得少，表面就不平，下一层光刻就会失焦。

所以工艺厂规定：**每一层金属的密度必须在某个范围内**（比如 30%~70%），而且要分窗口检查（每 100×100um 一个窗口）。

```tcl
# 铺之前先看密度
check_metal_density            # 或 verifyMetalDensity
# 铺（工具自动在空白处插不连接的金属块）
addMetalFill -layer {metal1 metal2 metal3} -timingAware true
```

:::note `-timingAware` 是什么
普通 metal fill 会随便插金属块，可能插在关键路径旁边，**增加耦合电容，把时序搞崩**。

`-timingAware`（或 `-netAware`）让工具避开关键网络，代价是跑得慢、密度可能达不到，需要迭代。
:::

## seal ring 与 pad：芯片的"外壳" {#seal}

| 结构 | 作用 | 谁提供 |
|---|---|---|
| Seal ring（密封环） | 环绕芯片四周的金属/通孔墙，挡住切割裂纹和水汽 | 工艺厂提供模板，你按规则画 |
| Bond pad（焊盘） | 对外打线的金属块，通常 60~80um 见方 | IO 库提供 |
| Scribe line（划片道） | 芯片之间的切割通道，放测试结构 | 工艺厂规定宽度 |

这些通常由**顶层集成者**负责，做 block 的人不用管。但你要知道它们存在——因为它们占了芯片边缘 30~50um 的空间，**算 die 面积时不能算进去**。

## 最终检查清单（送厂前必须全绿）{#checklist}

这张表按顺序过，任何一项红都不能送：

| # | 检查 | 命令（ICC2 / Innovus） | 通过标准 |
|---|---|---|---|
| 1 | 连接性 | `check_lvs` / `verifyConnectivity` | 无 open、无 floating |
| 2 | DRC | `check_routes` / `verify_drc` | 0 条 |
| 3 | 金属密度 | `check_metal_density` | 每层在每个窗口内都达标 |
| 4 | 天线 | `check_antenna` | 0 条 |
| 5 | 时序 setup | `report_qor` | WNS ≥ 0 |
| 6 | 时序 hold | `report_qor` | WNS ≥ 0（或已 waiver） |
| 7 | 功耗 | `report_power` | 在预算内 |
| 8 | 面积 | `report_area` | 在预算内 |
| 9 | LVS（版图 vs 网表） | Calibre / PVS | 完全一致 |
| 10 | ERC（电气规则） | Calibre | 无 latch-up / 无浮栅 |

:::term LVS | Layout Versus Schematic，版图与原理图一致性
从 GDS 里"提取"出电路（哪些器件、怎么连），再和网表对比。**不一致就是做出来功能不对**，比 DRC 更致命。

DRC 错了工厂不收货；LVS 错了工厂收货、但芯片是坏的。
:::

## 交付物：给工厂和给下一个人 {#deliver}

| 交给谁 | 文件 | 说明 |
|---|---|---|
| 工厂（foundry） | GDSII | 最终版图，唯一必需的制造文件 |
| 工厂 | 层次化结构说明、密度报告 | 附带 |
| 封装厂 | bond diagram、pad 坐标 | 打线用 |
| 测试 | STIL / WGL（ATPG 向量） | 量产测试用 |
| 项目组 | DEF、网表、SPEF、SDF | 后续 ECO、板级仿真用 |
| 项目组 | 签核报告（PT/PV/功耗） | 证明"我们查过了" |
| 项目组 | README：版本、corner、已知问题 | **最容易漏、最有用** |

:::note 那个 README 为什么最重要
半年后有人要在这个设计上做 ECO，他需要知道：用的是哪个库版本、哪个 corner 签的、有没有 waiver 掉的违例、哪些路径是 known issue。

没有这份说明，他要花两周重新摸一遍；有的话，半天就能上手。**写交接文档是工程师的基本功，不是额外工作。**
:::

## 我们的环境能做到哪一步 {#ourlimit}

诚实说明（这套课程环境是 Synopsys 单工具链 + 开源 45nm 库）：

| 环节 | 我们能做到 | 缺什么 |
|---|---|---|
| filler | ✅ `create_stdcell_fillers` 可跑 | — |
| metal fill | ⚠️ 命令可跑，密度检查不完整 | 完整 deck 需工艺厂提供 |
| seal ring / pad | ❌ 不做 | 需要 IO 库与工艺厂模板 |
| DRC | ✅ 工具内部 DRC 可跑到 0 | 签核级需 Calibre + deck |
| LVS | ❌ 做不了 | 需 Calibre/PVS + LVS deck |
| GDS 导出 | ⚠️ 可 `write_gds`，但无标准单元 GDS 合并 | 需完整库 GDS |

所以这一课的目标是：**知道收尾有哪七件事、每件事为什么做、检查清单长什么样**。真正送厂那一步，你会在有完整 PDK 和 Calibre 的公司环境里做。

:::lab 动手：把收尾清单变成一份可勾选的检查表
在模拟终端里建一个自己的 checklist 文件（这是真实工作习惯）：

```bash
cd ~
cat > finish_checklist.txt <<'EOF'
[ ] connectivity clean
[ ] DRC 0
[ ] metal density OK
[ ] antenna 0
[ ] setup WNS >= 0
[ ] hold WNS >= 0
[ ] power within budget
[ ] LVS clean
[ ] deliverables archived
[ ] README written
EOF
cat finish_checklist.txt
```

过关标准：能解释清单里每一项"不做的后果"，而不是只知道要做。
:::

:::check
- 能说出 ChipFinish 的七件事
- 知道 filler 必须从大到小填，填完要复查时序
- 知道 metal fill 是为了 CMP 平整，`-timingAware` 是为了不破坏时序
- 能背出送厂前 10 项检查、以及 DRC 与 LVS 的区别
- 知道交付物里最容易漏、但最重要的是那份 README
:::

:::quiz
DRC 和 LVS 的区别是什么？哪个更致命？|DRC 查"画得合不合法"，LVS 查"版图与网表是否一致"。DRC 错工厂不收货；LVS 错工厂收货但芯片是坏的，所以 LVS 错更致命。
filler cell 为什么必须从大到小填？|先用大块填掉大部分空隙，再用小块补缝；反过来会全是小块、数量爆炸，或者大空隙填不满导致阱不连续。
metal fill 的作用是什么？|让每层金属密度均匀，保证化学机械抛光（CMP）后表面平整，否则后层光刻失焦。
`-timingAware` 的 metal fill 解决什么问题？|避免把填充金属插到关键网络旁边增加耦合电容，防止收尾阶段把时序搞崩。
交付物里为什么需要一份 README？|让接手的人知道库版本、签核 corner、waiver 项和已知问题，避免重新摸索两周。
:::
