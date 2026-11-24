---
id: _abbr
title: 缩写解码表
en: Abbreviation Decoder
tags: [速查, 缩写, 术语, PR]
summary: PR 里那些三字母缩写，按"你在哪一步遇到它"分成七组：角色、流程、文件、时序、物理、单元、工具。每条一句话讲清它在流程里扮演什么角色，不是词典式定义。
---

## 怎么用这一页 {#how}

这一页不是术语词典（要看完整解释去 [术语表](/glossary/)），它解决的是另一种卡顿：**同事说了一串缩写，你听懂了每个字母，但不知道它在流程里是干什么的。**

三点用法：

1. **按"你卡在哪"跳组**：听人聊天听不懂→第一组；不知道下一步跑什么→第二组；收文件不知道哪份是哪份→第三组；时序报告看不懂→第四组；route 绕不通→第五组。
2. **每条只记"角色"，不记全称**。全称是给简历和文档用的，工作里你只需要知道它占哪个位置。
3. **每组标题下都标了出处课**，想深挖点链接回去读那一讲。

## 最容易混的六对 {#confuse}

这六对是新人问得最多的，先分清再往下看。

| 一对 | 区别一句话 |
|---|---|
| LEF 与 DEF | LEF 描述"**长什么样**"（单元/工艺的规格，全项目通用）；DEF 记录"**这次摆在哪**"（本设计的实际坐标，一人一份） |
| lib 与 rc tech | lib 管 **cell 延迟**（晶体管快慢）；rc tech 管 **线延迟**（导线寄生 RC） |
| pin 与 port | pin 在 **Cell 层**（单元身上的引脚）；port 在 **Block 层**（模块对外的端口），位置由 Top 指定 |
| WCS 与 BCF | WCS = 最慢条件，**查 setup**；BCF = 最快条件，**查 hold**。记反了报告全绿但芯片是废的 |
| S1 与 S2 | S1 是**纯功能**网表（用来估面积）；S2 是**带 scan** 的网表（门数涨 20%~100%，真正要做的版本） |
| PV 与 PA | PV 是 **Physical Verification**（DRC/LVS/天线）；PA 是 **Power Analysis**（IR drop/电迁移）。同在 ECO 阶段，修的东西完全不同 |

## 一、角色：你在跟谁打交道 {#people}

出处：[什么是布局布线（PR）](/lesson/02-02-pr-what/)、[SDC 时序约束](/lesson/02-08-pr-sdc/)

| 缩写 | 全称 · 中文 | 它在流程里是什么 |
|---|---|---|
| PR / PnR | Place and Route · 布局布线 | 把网表变成版图的那段活，也就是本课程的主体 |
| PD | Physical Design · 物理设计 | "后端"的正式叫法；PR 是 PD 的主战场 |
| DE | Design Engineer · 前端设计 | 写 RTL、做综合、交网表给你的人。逻辑太深摆不下去，就找他改代码 |
| ME | Middle End Engineer · 中端 | 夹在前后端之间：做 DFT、formal、MMMC 环境，网表也常从他那儿出 |
| AE | Application Engineer · 应用工程师 | 工具厂商派到项目上的技术支持，内部命令不懂就问他 |
| FCT | Full Chip Timing · 全芯片时序 | 写 SDC 的部门。约束不合理要提给他们改，不能自己偷偷改一版 |
| Top | 顶层 | 整个芯片那一层，负责给各 block 下发边界、port 位置和约束 |
| Block | 模块 | 你实际负责的那一块，有明确物理边界，接口由 Top 定 |
| Fabless | 无晶圆厂设计公司 | 只设计不生产，把制造交给 foundry |
| Foundry | 晶圆代工厂 | 台积电、中芯这类，卖的是产能和工艺 |
| IDM | Integrated Device Manufacturer | 自己设计自己造，如 Intel |

## 二、流程：一天到晚在跑什么 {#flow}

出处：[PR 全流程九步](/lesson/02-03-pr-flow/)

| 缩写 | 全称 · 中文 | 它在流程里是什么 |
|---|---|---|
| init | 初始化 · 导入设计 | 把网表、lef、lib、sdc 吃进工具，建立初始数据库 |
| floorplan / FLP | 布局规划 | 定 die 面积、摆 mem/macro、加物理单元；全流程里手动活最多的一步 |
| powerplan | 供电规划 | 打电源网络（VDD/VSS），先有电才能摆单元 |
| place | 布局 | 工具自动摆几百万个标准单元，人只给密度和约束 |
| CTS | Clock Tree Synthesis · 时钟树综合 | 专门绕时钟线，让时钟同时到达所有触发器 |
| optCTS | 时钟树优化 | CTS 做完时序通常更差（多了 buffer），这一轮专门修 |
| route | 布线 | 把所有信号线真正连起来，目标是 open 与 short 清零 |
| optRoute / OBT | 布线优化 · 流片前优化 | 同一件事的两个名字：真实 RC 下修最后的时序与 DRC |
| chipfinish | 收尾 | 出 GDSII，做交付前的清理与检查 |
| preCTS opt | 布局优化 | place 之后、CTS 之前那一轮，用估算时钟修 setup |
| FINAL PR | 终版 PR | 反复跑多个 run 后选定的那一版，之后只能走 ECO |
| ECO | Engineering Change Order · 工程变更 | 版图定死后的小修：改一根线、换一个 cell，不能挪 memory |
| tapeout | 流片 | 把 GDSII 交给 foundry 做掩膜 |
| BTO / MTO | Before / Mask Tape Out | 送厂前的数据整合检查；MTO 之后数据彻底锁死 |
| run | 一次跑流 | 把一串命令丢进 Queue 跑完的一轮，几个钟头到几天 |
| Try | 试版本 | 同一阶段试不同参数的多版（FLP1、FLP2），比哪个结果好 |

## 三、数据：别人交给你的文件 {#files}

出处：[数据准备](/lesson/02-04-pr-data/)、[lib 与 rc tech](/lesson/02-06-pr-lib-rctech/)

| 缩写 | 全称 · 中文 | 它在流程里是什么 |
|---|---|---|
| netlist | 网表（.v / .v.gz） | 逻辑连接关系：谁连谁。PR 的第一份输入 |
| GDSII / GDS | 版图数据 | PR 的最终输出，foundry 拿它做掩膜 |
| DEF | Design Exchange Format | 物理信息交换格式：die 大小、单元坐标、port 位置都在这 |
| LEF | Library Exchange Format | 技术描述格式，分 tech lef 与 cell lef 两种 |
| tech lef | 工艺 LEF | 有哪些金属层、线宽间距、via 规则，是 DRC 的源头 |
| cell lef | 单元 LEF | 每个 cell 多大、pin 在哪、什么形状 |
| lib | Liberty · 时序库 | cell 延迟表：给定输入转换与输出负载，查出延迟 |
| rc tech | RC 工艺文件 | 线的寄生参数模型，同一根线在不同 corner 下 R、C 不同 |
| TLU+ / ITF | 两种 RC tech 格式 | TLU+ 是 Cadence 的叫法，ITF 是 Synopsys 的叫法，同一类东西 |
| SDC | Synopsys Design Constraints | 时序"要求"：周期多长、外部给多少延迟、哪些是假路径 |
| MMMC | Multi-Mode Multi-Corner | 多模式多端角配置，实际落在 viewDefinition.tcl 里 |
| SPEF | Standard Parasitic Exchange Format | 抽出来的真实寄生 RC，PT 用它算线延迟 |
| PG netlist | 带电源地的网表 | 电源网络也连好的网表，做 LVS 时用它 |
| UPF | Unified Power Format | 低功耗意图：哪块能关电、工作在什么电压 |

## 四、时序：这门课的心脏 {#timing}

出处：[Setup 与 Hold](/lesson/02-06a-setup-hold/)、[MMMC](/lesson/02-07-pr-mmmc/)

| 缩写 | 全称 · 中文 | 它在流程里是什么 |
|---|---|---|
| setup | 建立时间 | 数据不能太晚：下一个时钟沿来之前必须稳定 |
| hold | 保持时间 | 数据不能太早：当前时钟沿采完之后才能变 |
| slack | 余量 | 到达时间与要求时间之差，必须大于等于 0 |
| arrival / required | 到达时间 / 要求时间 | 一个是你实际什么时候到，一个是规定最晚什么时候到 |
| WNS | Worst Negative Slack | 最差那条路径差多少；负数就是没过，日常就看这一个数 |
| TNS | Total Negative Slack | 所有违例路径的 slack 累加，衡量"烂得多不多" |
| skew | 时钟偏斜 | 同一个时钟到达两个触发器的时间差 |
| insertion delay | 时钟插入延迟 | 时钟从源头走到触发器花了多久 |
| corner | 端角 | 工艺/电压/温度/RC 的一组组合，代表"一种可能的芯片" |
| PVT | Process / Voltage / Temperature | 工艺、电压、温度，也就是 corner 的三要素 |
| SS / FF / TT | Slow-Slow / Fast-Fast / Typical | 管子和线都慢 / 都快 / 都典型 |
| WCS | Worst Case Slow | SS + 低压 + 高温 + RCmax，查 setup 用它 |
| BCF | Best Case Fast | FF + 高压 + 低温 + RCmin，查 hold 用它 |
| OCV | On-Chip Variation | 同一颗芯片内部也有快慢，统一加个百分比余量 |
| POCV | Parametric OCV | 用统计分布代替固定百分比，更准也更省 |
| derate | 降额系数 | OCV 的落地方式：晚路径乘 1.05、早路径乘 0.95 |
| STA | Static Timing Analysis | 静态时序分析，不仿真、靠遍历路径算时序 |
| PT | PrimeTime | Synopsys 的 STA 签核工具，报告以它为准 |
| RCmax / RCmin | 最坏 / 最好 RC | 线最慢与最快的两种假设，分别给 setup 与 hold |

## 五、物理：绕不通的时候看这些 {#physical}

出处：[PR 全流程九步](/lesson/02-03-pr-flow/)、[LEF 详解](/lesson/02-05-pr-lef/)

| 缩写 | 全称 · 中文 | 它在流程里是什么 |
|---|---|---|
| DRC | Design Rule Check | 设计规则检查：线太细、间距不够就报错，必须清零 |
| LVS | Layout vs Schematic | 版图与网表是否一致，多一根线少一个孔都算错 |
| via | 通孔 | 上下两层金属之间的连接柱 |
| pitch | 节距 | 相邻两根线的中心距，工艺定死，单元高度按它算 |
| track | 布线轨道 | 线只能走在固定网格上，轨道数决定能走多少线 |
| M1~M9 | Metal 1~9 | 第几层金属，下层细、上层粗，走线方向逐层交替 |
| 1P9M | 1 Poly + 9 Metal | 工艺层数的写法：1 层多晶硅 + 9 层金属 |
| OBS | Obstruction | 单元内部不许走线的区域，摆单元时工具自动避开 |
| antenna | 天线效应 | 长金属在制造中积电荷打穿栅氧，靠跳层或二极管泄放 |
| density | 密度 | 单位面积里有多少图形，太低太高都影响良率 |
| congestion | 拥塞 | 走线资源不够，route 绕不出来；根因通常在 floorplan |
| utilization | 利用率 | 单元面积占 core 面积的比例，定太高必然拥塞 |
| halo | 保护区 | macro 周围不许摆单元的一圈缓冲，用来留走线通道 |
| tap cell / endcap | 衬底接触 / 边界单元 | 没有逻辑但必须铺的单元，保证衬底电位与边界完整 |
| NDR | Non-Default Rule | 非默认布线规则：给时钟等关键信号加宽、加倍间距 |
| IR drop | 电压降 | 电流流过电源网络导致电压下降，降太多单元会变慢甚至失效 |

## 六、单元与接口 {#cells}

出处：[数字电路基础](/lesson/02-01a-chip-basics/)、[Pin 与 Port](/lesson/02-05a-pin-port/)

| 缩写 | 全称 · 中文 | 它在流程里是什么 |
|---|---|---|
| stdcell | Standard Cell · 标准单元 | 库里的基本逻辑单元，高度统一，工具自动摆 |
| macro | 宏单元 | 预先做好的大块（memory、PLL、IP），只能整体摆不能拆 |
| SRAM | 静态随机存储器 | 最典型的 macro，面积大，位置决定 floorplan 成败 |
| DFF | D Flip-Flop · D 触发器 | 存一拍数据的单元，时序分析的起点与终点 |
| CLK / CK | Clock | 触发器的时钟端 |
| pin | 引脚 | 单元身上的连接点，属于 Cell 层 |
| port | 端口 | 模块对外的接口，属于 Block 层，位置由 Top 指定 |
| IO | Input / Output | 芯片或模块对外的出入口 |
| orientation | 朝向 | 单元能怎么翻转旋转（N/S/E/W 加镜像），受 SYMMETRY 限制 |
| SITE | 站位 | 单元放置的最小网格单位，单元宽度是它的整数倍 |
| SYMMETRY | 对称性 | lef 里声明这个单元允许沿哪个轴翻转 |
| MUX | Multiplexer · 多路选择器 | 多选一的组合逻辑单元 |
| BUF / INV | Buffer / Inverter | 缓冲器 / 反相器，用来驱动长线、重整 transition |
| ALU | Arithmetic Logic Unit | 算术逻辑单元，CPU 里做运算的那部分 |

## 七、测试、工具与其它 {#tools}

出处：[网表版本与 Release](/lesson/02-04a-netlist-release/)、[PR 全流程九步](/lesson/02-03-pr-flow/)

| 缩写 | 全称 · 中文 | 它在流程里是什么 |
|---|---|---|
| DFT | Design for Test | 可测性设计：插扫描链，让测试机测得出坏点 |
| scan chain | 扫描链 | DFT 插进来的移位寄存器链，测试时把内部状态移出来看 |
| S1 / S2 | 第一版 / 第二版网表 | S1 纯功能（估面积用），S2 带 scan（真正要做的版本） |
| VCS | Verilog Compiled Simulator | Synopsys 的仿真工具，前端用它验功能 |
| DC | Design Compiler | Synopsys 的综合工具，RTL 变网表 |
| Genus | Cadence 的综合工具 | 跟 DC 抢同一个位置，项目里二选一 |
| Formality | 形式验证工具 | 证明综合后的网表与 RTL 逻辑等价 |
| PLL | Phase-Locked Loop | 锁相环，产生芯片内部时钟，本身是个 macro |
| EDA | Electronic Design Automation | 电子设计自动化，泛指这一类工具软件 |
| SOC | System on Chip | 系统级芯片，把 CPU、memory、各种 IP 塞进一颗 |
| IP | Intellectual Property | 可复用的设计模块，买来的或内部积累的 |
| PV | Physical Verification | 物理验证：DRC、LVS、天线，ECO 阶段专门修它 |
| PA | Power Analysis | 功耗分析：IR drop、电迁移，ECO 阶段另一条线 |
| DDR / USB / PCIe | 常见高速接口 | 最值钱的几类 block，做这些的 PR 岗位溢价明显 |

## 还看不懂怎么办 {#next}

| 症状 | 去哪儿 |
|---|---|
| 想看完整解释与出处 | [术语表](/glossary/)：全站术语可搜、按阶段筛 |
| 分不清某个文件归谁管 | [数据准备](/lesson/02-04-pr-data/) 的文件职责表 |
| 时序报告看不懂 | [Setup 与 Hold](/lesson/02-06a-setup-hold/) 先读，再回 [MMMC](/lesson/02-07-pr-mmmc/) |
| 缩写记住了但串不起流程 | [PR 全流程九步](/lesson/02-03-pr-flow/) 那张九行表 |
