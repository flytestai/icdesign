# -*- coding: utf-8 -*-
"""补充配图：输入数据、corner 矩阵、IR drop、UPF、ICC2、收尾检查、目录结构、ECO、简历。"""

from figs.style import page, svgwrap
from figs.parts import (menu, tbar, tree, side, canvas, cons, ps, status, window,
                        die, macro, stripes, ring, rows, cells_grid, label, callout, esc)

FIGS = []
FONT = '"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif'
MONO = '"Cascadia Mono",Consolas,monospace'


def txt(x, y, s, size=12, fill="#3d4d5f", anchor="start", mono=False, weight="400"):
    fam = MONO if mono else FONT
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x}" y="{y}" font-family={fam!r} font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def add_svg(fid, w, h, caption, body):
    FIGS.append((fid, w, h, page(svgwrap(w, h, body)), caption))


def add_html(fid, w, h, caption, body):
    FIGS.append((fid, w, h, page(body), caption))


def card(x, y, w, h, fill="#ffffff", stroke="#dfe6ee", r=7):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'


# ================================================================ 输入数据地图
def fig_inputs():
    W, H = 1120, 500
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "开工前必须到手的 7 样东西：谁给、什么格式、缺了会怎样", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "后端不是「拿到工具就能干」。这 7 样缺任何一样，要么工具直接报错，要么跑出来的结果全是错的——后者更危险。", 11.5, "#6b7f99"))

    items = [("① 门级网表", "netlist.v", "综合（DC/Genus）", "#2f7fd0", "缺 → 没东西可摆"),
             ("② 时序库 .lib/.db", "slow/typ/fast.db", "工艺厂 / 库团队", "#7a5cd6", "缺 → link_design 失败"),
             ("③ 物理库 LEF", "*.lef (tech+cell+macro)", "工艺厂 / 库团队", "#7a5cd6", "缺 → 不知道单元多大"),
             ("④ 寄生技术文件", "TLU+ / QRC tech", "工艺厂", "#d9901e", "缺 → OPT-906 类报错"),
             ("⑤ 时序约束 SDC", "*.sdc", "设计者 / 前端", "#18a07a", "缺 → 工具不知道查什么"),
             ("⑥ 功耗意图 UPF", "*.upf", "低功耗设计者", "#d9534f", "缺 → 多电压域跑不起来"),
             ("⑦ 宏单元模型", "SRAM/ROM 的 .lef+.lib+.v", "IP 提供方", "#e07a5f", "缺 → 宏是黑盒没法接")]
    x0, y0 = 40, 82
    for i, (name, fmt, who, col, risk) in enumerate(items):
        col_i = i % 4
        row_i = i // 4
        x = x0 + col_i * 268
        y = y0 + row_i * 176
        s.append(card(x, y, 246, 152))
        s.append(f'<rect x="{x}" y="{y}" width="246" height="4" rx="2" fill="{col}"/>')
        s.append(txt(x + 14, y + 30, name, 12.5, "#1a2430", weight="650"))
        s.append(txt(x + 14, y + 54, fmt, 10, "#1d6fb8", mono=True))
        s.append(txt(x + 14, y + 78, "来自：" + who, 10, "#6b7f99"))
        s.append(txt(x + 14, y + 104, risk, 10, "#b3382f"))
        # 小图标：文件
        s.append(f'<rect x="{x + 190}" y="{y + 20}" width="34" height="42" rx="3" fill="#f3f8fe" stroke="{col}"/>')
        s.append(txt(x + 207, y + 46, "F", 13, col, "middle", mono=True, weight="700"))

    s.append(card(40, 434, 1040, 50, "#f3f8fe", "#bcd7f0"))
    s.append(txt(54, 456, "开工自检 5 件事（10 分钟省两天）：", 11.5, "#1d6fb8", weight="650"))
    s.append(txt(230, 456, "① 顶层模块名对得上  ② 库的 corner 齐了（slow/typ/fast）  ③ SDC 里时钟周期与规格书一致", 10.5, "#3d4d5f"))
    s.append(txt(54, 476, "④ LEF 里能找到网表用到的每个单元（report_lib 比对）  ⑤ UPF 里的电源域名字与网表一致", 10.5, "#3d4d5f"))
    add_svg("inputs-map", W, H, "七类输入数据一览。每一格写清「文件名长什么样、谁给你、缺了会报什么错」。右下角是开工前的 5 项自检——这 10 分钟能省掉后面两天的空跑。",
            "".join(s))


# ================================================================ corner 矩阵
def fig_corner():
    W, H = 1120, 486
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "多 corner 签核：为什么要算好几遍，每遍看什么", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "同一颗芯片，在「慢工艺 + 低电压 + 高温」和「快工艺 + 高电压 + 低温」下表现完全不同。前一种最坏 setup，后一种最坏 hold。", 11.5, "#6b7f99"))

    # 表格
    cols = ["Corner 名", "工艺", "电压", "温度", "查什么", "为什么"]
    widths = [148, 108, 88, 88, 132, 476]
    x0, y0 = 40, 82
    rows = [("ss_0p81v_125c", "slow", "0.81V", "125℃", "setup (max)", "管子最慢 + 电压最低 + 线最慢 → 数据最容易迟到", "#b3382f"),
            ("tt_0p90v_25c", "typical", "0.90V", "25℃", "参考 / 功耗", "不是签核依据，用来对比与估功耗", "#6b7f99"),
            ("ff_1p10v_m40c", "fast", "1.10V", "-40℃", "hold (min)", "管子最快 + 电压最高 → 数据最容易早到", "#1d6fb8"),
            ("ss_0p81v_m40c", "slow", "0.81V", "-40℃", "hold 交叉", "慢工艺但低温，某些路径的 hold 最差在这里", "#7a5cd6"),
            ("ff_1p10v_125c", "fast", "1.10V", "125℃", "setup 交叉", "快工艺但高温，某些 setup 最差在这里", "#d9901e")]
    xx = x0
    s.append(card(x0, y0, 1040, 30, "#eef3f9", "#eef3f9", 0))
    for c, w in zip(cols, widths):
        s.append(txt(xx + 10, y0 + 20, c, 10.5, "#42566b", weight="600"))
        xx += w
    y = y0 + 30
    for i, r in enumerate(rows):
        bg = "#ffffff" if i % 2 == 0 else "#fafcfe"
        s.append(f'<rect x="{x0}" y="{y}" width="1040" height="36" fill="{bg}" stroke="#eef2f7"/>')
        s.append(f'<rect x="{x0}" y="{y}" width="4" height="36" fill="{r[6]}"/>')
        xx = x0
        for j in range(5):
            s.append(txt(xx + 10, y + 23, r[j], 10.5, r[6] if j == 4 else "#22303f",
                         mono=(j == 0), weight="600" if j == 4 else "400"))
            xx += widths[j]
        s.append(txt(xx + 10, y + 23, r[5], 10, "#5b7089"))
        y += 36

    s.append(card(40, 300, 510, 140, "#fdf6e6", "#edd9a8"))
    s.append(txt(54, 324, "为什么「不止两个 corner」", 12, "#96660f", weight="650"))
    for i, t in enumerate(["温度对电阻和阈值电压的影响不是单调的：",
                           "高温 → 线电阻变大（setup 更差）",
                           "低温 → 晶体管更快（hold 更差）但线电阻更小",
                           "所以 slow+低温、fast+高温这两个「交叉 corner」",
                           "有时比 SS/FF 更差，必须实际算过才知道。"]):
        s.append(txt(56, 348 + i * 19, "· " + t, 10.5, "#3d4d5f"))

    s.append(card(570, 300, 510, 140, "#f3f8fe", "#bcd7f0"))
    s.append(txt(584, 324, "签核时怎么报（一句能背下来的话）", 12, "#1d6fb8", weight="650"))
    for i, t in enumerate(["「SS 0.81V 125℃ 下 setup WNS −0.05ns，TNS −0.3ns，",
                           "14 条违例，全部在 u_dsp 的乘法器上；",
                           "FF 1.10V −40℃ 下 hold WNS +0.02ns，已收敛。",
                           "留了 3 条 false path，理由写在 constraints/README。」"]):
        s.append(txt(586, 348 + i * 19, t, 10.5, "#3d4d5f"))

    s.append(txt(40, H - 26, "corner 数量由项目定：小项目 2~3 个，先进工艺常常 6~12 个（还要加 RC corner：cworst / cbest / rcworst / rcbest）。",
                 10.5, "#93a4b8"))
    s.append(txt(40, H - 8, "跑一个 corner 动辄几小时，所以先跑最可能违例的那个，别按字母顺序排队。", 10.5, "#93a4b8"))
    add_svg("corner-matrix", W, H, "多 corner 签核表。每一行是一个 corner（工艺+电压+温度的组合），要查的东西不一样。记住结论：SS 查 setup、FF 查 hold，但真正最差的那个 corner 必须实算才知道。",
            "".join(s))


# ================================================================ IR drop
def fig_irdrop():
    W, H = 1120, 520
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "IR drop：为什么芯片会「电压不够」", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "电源网络有电阻，电流一流过就掉压。掉得太多，单元就跑不动——这不是设计错误，是物理规律。", 11.5, "#6b7f99"))

    # 左侧：电阻链
    s.append(card(40, 82, 330, 210))
    s.append(txt(54, 106, "静态 IR drop（电阻分压）", 12, "#1d6fb8", weight="650"))
    s.append(txt(56, 132, "V_drop = I × R", 12, "#b3382f", mono=True, weight="700"))
    for i, t in enumerate(["假设某单元要 1A 电流", "到它的路径总电阻 10mΩ",
                           "→ 掉压 10mV（0.9V 的 1.1%）", "电阻翻倍 → 掉压翻倍 → 单元变慢"]):
        s.append(txt(56, 158 + i * 22, "· " + t, 10.5, "#3d4d5f"))
    s.append(txt(56, 262, "目标：全片 < 5% VDD（0.9V → 45mV）", 10.5, "#157a5b", weight="600"))

    s.append(card(40, 306, 330, 126))
    s.append(txt(54, 330, "动态 IR drop（di/dt）", 12, "#d9901e", weight="650"))
    for i, t in enumerate(["时钟沿一到，几万个单元同时翻转", "瞬时电流突然拉大 → 掉压瞬间加深",
                           "所以动态 drop 常是静态的 2~3 倍"]):
        s.append(txt(56, 354 + i * 22, "· " + t, 10.5, "#3d4d5f"))

    # 右侧热图
    gx, gy, cell, n, m = 410, 92, 26, 26, 13
    import math
    hot = [(9, 7, 1.5), (19, 10, 1.2), (6, 15, 0.9)]
    for r in range(m):
        for c in range(n):
            v = 0.05
            for hx, hy, amp in hot:
                v += amp * math.exp(-((c - hx) ** 2 + (r - hy) ** 2) / 12.0)
            v = min(v, 1.0)
            if v < 0.15:
                col, op = "#18a07a", 0.30
            elif v < 0.32:
                col, op = "#d9901e", 0.45
            elif v < 0.55:
                col, op = "#e07a3f", 0.65
            else:
                col, op = "#d9534f", 0.85
            s.append(f'<rect x="{gx + c * cell}" y="{gy + r * cell}" width="{cell - 1.2}" height="{cell - 1.2}" '
                     f'fill="{col}" opacity="{op:.2f}"/>')
    s.append(f'<rect x="{gx}" y="{gy}" width="{n * cell}" height="{m * cell}" fill="none" stroke="#c9d5e2"/>')
    s.append(txt(gx + n * cell / 2, gy - 8, "电压热图（红色 = 掉压最严重）", 10.5, "#5b7089", "middle"))
    # 图例
    for i, (lbl, col, op) in enumerate([("<3%（安全）", "#18a07a", .30), ("3~5%", "#d9901e", .45),
                                        ("5~8%", "#e07a3f", .65), (">8%（会失效）", "#d9534f", .85)]):
        s.append(f'<rect x="{gx + i * 176}" y="{gy + m * cell + 12}" width="14" height="14" fill="{col}" opacity="{op}"/>')
        s.append(txt(gx + i * 176 + 20, gy + m * cell + 23, lbl, 10, "#3d4d5f"))

    # 右侧说明
    bx = 800
    s.append(card(bx, 82, 280, 210, "#f3f8fe", "#bcd7f0"))
    s.append(txt(bx + 14, 106, "热点为什么总在同一个地方", 11.5, "#1d6fb8", weight="650"))
    for i, t in enumerate(["① 离电源 pad 最远（电阻最长）", "② 单元密度最高（电流最大）",
                           "③ 只有一层金属供电（并联不够）", "④ 交叉点没打满 via（接触电阻）",
                           "⑤ 时钟树缓冲器集中（瞬时电流大）"]):
        s.append(txt(bx + 16, 130 + i * 22, t, 10.5, "#3d4d5f"))

    s.append(card(bx, 306, 280, 126, "#fdf6e6", "#edd9a8"))
    s.append(txt(bx + 14, 330, "四种修法（成本从低到高）", 11.5, "#96660f", weight="650"))
    for i, t in enumerate(["加 via（几乎免费）", "加 stripe / 加宽（小）",
                           "改 floorplan 挪单元（中）", "加去耦电容 / 改封装（大）"]):
        s.append(txt(bx + 16, 354 + i * 20, t, 10.5, "#3d4d5f"))

    s.append(txt(40, H - 26, "RedHawk / Voltus 这类工具就是算这个：输入 def + spef + 功耗活动文件，输出每个单元的电压值与热图。",
                 10.5, "#93a4b8"))
    s.append(txt(40, H - 8, "课程环境跑不了，但报告结构与判据必须看得懂——面试问「IR drop 超了怎么办」，问的就是这张图右边的四种修法。", 10.5, "#93a4b8"))
    add_svg("ir-drop", W, H, "IR drop 的成因与热图。左边两个公式（静态 V=IR、动态 di/dt）解释了为什么掉压；右边的热图是工具的输出，红区就是「电压最低、最容易失效」的位置。",
            "".join(s))


# ================================================================ UPF 电源域
def fig_upf():
    W, H = 1120, 440
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "多电压域：一块芯片上跑不同电压，交界处要加两种单元", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "省电最有效的办法是「用不到的模块直接断电」。但断电域和常开域之间传信号，必须加隔离单元和电平转换——这就是 UPF 要描述的东西。", 11.5, "#6b7f99"))

    # 两个域
    s.append(card(40, 84, 470, 190, "#f3f8fe", "#9dc4e8"))
    s.append(txt(56, 108, "PD_CPU（可关断域）  0.81V", 12, "#1d6fb8", weight="650"))
    for i in range(3):
        s.append(f'<rect x="{70 + i * 140}" y="128" width="110" height="56" rx="5" fill="#fff" stroke="#9dc4e8"/>')
        s.append(txt(125 + i * 140, 152, ["u_alu", "u_reg", "u_ctrl"][i], 10.5, "#1d6fb8", "middle", mono=True))
        s.append(txt(125 + i * 140, 170, "可断电", 9, "#93a4b8", "middle"))
    s.append(txt(56, 208, "开关单元（power switch）：断电时把这一域的 VDD 断开", 10, "#b4531a"))
    s.append(card(56, 220, 436, 40, "#fdf6e6", "#edd9a8"))
    s.append(txt(68, 245, "省电效果：这一域不工作时功耗直接归零（漏电也归零）", 10.5, "#96660f"))

    s.append(card(560, 84, 520, 190, "#f7f9fc", "#dbe4ee"))
    s.append(txt(576, 108, "PD_AON（常开域）  0.90V", 12, "#5b7089", weight="650"))
    for i in range(3):
        s.append(f'<rect x="{590 + i * 150}" y="128" width="120" height="56" rx="5" fill="#fff" stroke="#c9d5e2"/>')
        s.append(txt(650 + i * 150, 152, ["u_rtc", "u_pmu", "u_wake"][i], 10.5, "#3d4d5f", "middle", mono=True))
        s.append(txt(650 + i * 150, 170, "一直供电", 9, "#93a4b8", "middle"))

    # 交界处
    s.append(f'<path d="M 510 180 L 558 180" stroke="#7e93a8" stroke-width="1.6" marker-end="url(#ah)"/>')
    s.append(f'<rect x="498" y="132" width="72" height="30" rx="4" fill="#fdeeec" stroke="#efc5c1"/>')
    s.append(txt(534, 152, "ISO", 10.5, "#b3382f", "middle", mono=True, weight="700"))
    s.append(f'<rect x="498" y="196" width="72" height="30" rx="4" fill="#eaf8f2" stroke="#b6e0d0"/>')
    s.append(txt(534, 216, "LS", 10.5, "#157a5b", "middle", mono=True, weight="700"))

    # 说明
    s.append(card(40, 296, 500, 116))
    s.append(txt(54, 320, "ISO 隔离单元（isolation cell）", 11.5, "#b3382f", weight="650"))
    for i, t in enumerate(["作用：断电域的输出去驱动常开域时，把输出「钳」在固定电平",
                           "否则浮空电压会让常开域的输入乱翻，漏电剧增甚至烧掉",
                           "规则：谁输出谁隔离（output isolation）"]):
        s.append(txt(56, 344 + i * 21, "· " + t, 10, "#3d4d5f"))

    s.append(card(560, 296, 520, 116))
    s.append(txt(574, 320, "LS 电平转换器（level shifter）", 11.5, "#157a5b", weight="650"))
    for i, t in enumerate(["作用：0.81V 的信号送进 0.90V 的域时，把高电平抬上去",
                           "没有它，0.81V 的高电平可能识别不成「1」",
                           "规则：低压 → 高压必须加；同压或高压 → 低压可以不加（但要确认 VIH）"]):
        s.append(txt(576, 344 + i * 21, "· " + t, 10, "#3d4d5f"))

    s.append(txt(40, H - 12, "对后端的影响：这些单元是「额外多出来的实例」，会占面积、占布线资源，而且必须放在域边界上——floorplan 时就要预留位置。",
                 10.5, "#93a4b8"))
    add_svg("upf-domain", W, H, "两个电源域与交界处的两种特殊单元。ISO 负责「断电时把输出钳住」，LS 负责「把低电压的高电平抬到高电压域能识别的程度」。缺任何一个，芯片行为都会错乱。",
            "".join(s))


# ================================================================ ICC2 窗口
def fig_icc2():
    scene = ('<div style="position:absolute;left:16px;top:26px;width:660px;height:380px">'
             + die(ring(0, 0, 660, 380, 4) + stripes(True, 6, (12, 12, 636, 356), 3)
                   + "".join(macro(n, x, y, 96, 62, pins=8) for n, x, y in
                             [("SRAM0", 24, 34), ("SRAM1", 540, 34), ("SRAM0", 24, 284), ("SRAM1", 540, 284)])
                   + rows(140, 34, 380, 312) + cells_grid(140, 34, 380, 312)
                   + label("soc_top  (core)", 8, 4, "#7fa8c9", 9.5), 0, 0, 660, 380))
    inner = (menu(["File", "Edit", "View", "Select", "Design", "Floorplan", "Place", "Clock",
                   "Route", "Timing", "ECO", "Power", "Window", "Help"], "Design")
             + tbar(9, hot=(1, 4))
             + '<div class="body">'
             + side("Design Hierarchy", tree([(0, "▾ soc_top", 0), (1, "▾ SRAM0", 0), (2, "core", 0),
                                              (1, "▾ SRAM1", 0), (2, "core", 0), (0, "▸ u_cpu", 0),
                                              (0, "▸ u_dsp", 0), (0, "▸ u_dma", 0)]), 180)
             + canvas(scene, "Layout — soc_top", "Layer: all  Zoom 1:8", 690, 406)
             + '</div>'
             + cons([ps("create_lib soc_top_lib -ref_libs {tcbn40lpbwp.db}",
                        "Library 'soc_top_lib' created.", "out"),
                     ps("read_verilog ./netlist/soc_top.v", "Read 1 design, 9390 cells.", "out"),
                     ps("link_block", "Linking block 'soc_top' ... done.", "out"),
                     ps("link_block", 'Error: Cannot resolve reference "SRAM_16K" (LINK-5)', "err")], 96)
             + status(["Ready", "soc_top", "Linked", "MW lib: soc_top_lib", "X 0.000  Y 0.000"]))
    add_html("icc2-gui", 1000, 600,
             "ICC2 主窗口。结构和 Innovus 几乎一样（左边层次、中间版图、底部命令窗），但菜单名与命令完全不同——命令窗最后那行 LINK-5 就是 ICC2 最经典的报错：库里有东西没找到。",
             window("IC Compiler II 2022.03 — soc_top", inner, 1000, 600, "Synopsys ICC2"))


# ================================================================ 收尾检查
def fig_finish():
    W, H = 1120, 545
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "送厂（tapeout）前必须过的 10 道关", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "每一条都是「不通过就不能发」的硬指标。这份清单可以当 checklist 用——真实项目里它就是评审会上被逐条问的东西。", 11.5, "#6b7f99"))

    checks = [("① 时序签核", "SS/FF 全 corner WNS ≥ 0", "PT 报告 + 场景表", "#b3382f"),
              ("② DRC 归零", "DRC = 0（含密度、天线）", "Calibre DRC 报告", "#e07a5f"),
              ("③ LVS 一致", "版图与网表完全对应", "Calibre LVS 报告", "#e07a5f"),
              ("④ 天线检查", "无 antenna 违例", "Calibre ANT 报告", "#d9901e"),
              ("⑤ ERC", "电源地无短路/浮空", "Calibre ERC", "#d9901e"),
              ("⑥ IR drop", "静态 < 5%，动态 < 8%", "RedHawk/Voltus", "#7a5cd6"),
              ("⑦ EM 电迁移", "电流密度 < 限值", "RedHawk EM 报告", "#7a5cd6"),
              ("⑧ 密度", "金属密度 30%~70%", "DRC density check", "#2f7fd0"),
              ("⑨ 版图尺寸", "与封装/切割道匹配", "die size 与 seal ring", "#18a07a"),
              ("⑩ 交付物齐", "GDS/OASIS + 全部报告 + README", "交付清单", "#18a07a")]
    x0, y0 = 40, 82
    for i, (name, crit, tool, col) in enumerate(checks):
        c, r = i % 2, i // 2
        x = x0 + c * 530
        y = y0 + r * 76
        s.append(card(x, y, 508, 64))
        s.append(f'<rect x="{x}" y="{y}" width="4" height="64" rx="2" fill="{col}"/>')
        s.append(txt(x + 16, y + 24, name, 12, "#1a2430", weight="650"))
        s.append(txt(x + 16, y + 44, "判据：" + crit, 10, "#5b7089"))
        s.append(txt(x + 320, y + 44, tool, 9.5, "#93a4b8", mono=True))

    s.append(card(40, 466, 1040, 56, "#fdeeec", "#efc5c1"))
    s.append(txt(54, 488, "最容易「以为过了其实没过」的三条：", 11.5, "#b3382f", weight="650"))
    s.append(txt(300, 488, "① DRC 报告是旧的（没重跑）  ② LVS 用了错误的网表（改过版图没重新导出）", 10.5, "#3d4d5f"))
    s.append(txt(54, 510, "③ 时序只看了 typical corner（签核必须看 SS 与 FF，typical 只用于对比）", 10.5, "#3d4d5f"))
    add_svg("finish-checklist", W, H, "送厂前 10 项检查。左边是每条的名字与判据，右边是出报告的工具。底部三条是「最常见的形式主义错误」——报告在，但报告是旧的。",
            "".join(s))


# ================================================================ 项目目录
def fig_dir():
    W, H = 1120, 460
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "一个能被别人接手的工作目录长什么样", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "后端项目的痛点不是「跑不出来」，是「三个月后没人知道这版是怎么跑出来的」。目录结构解决的就是这个问题。", 11.5, "#6b7f99"))

    tree_txt = [
        (0, "soc_top/", "项目根目录，名字就是设计名"),
        (1, "README.md", "五要素：目标 / 怎么跑 / 数据在哪 / 当前状态 / 已知问题"),
        (1, "run/", "所有脚本（唯一入口）"),
        (2, "01_init.tcl", "读库、读网表、读约束"),
        (2, "02_floorplan.tcl", "布局规划"),
        (2, "03_place.tcl / 04_cts.tcl / 05_route.tcl", "按阶段分文件，不要写成一个巨型脚本"),
        (2, "99_signoff.tcl", "出报告"),
        (1, "inputs/", "只读：网表、库、LEF、SDC（软链接到项目库，不要复制）"),
        (1, "output/", "每阶段的数据库与中间结果（.enc.dat / .def）"),
        (1, "reports/", "报告按阶段分子目录，文件名带时间戳"),
        (1, "logs/", "日志，同样带时间戳；出问题第一件事是翻这里"),
        (1, "Makefile", "把「按顺序跑 6 个脚本」变成一个命令"),
        (1, ".gitignore", "忽略 output/ logs/ 大报告；只提交脚本与文档"),
    ]
    y = 86
    for lv, name, desc in tree_txt:
        x = 44 + lv * 24
        col = "#1d6fb8" if lv == 0 else ("#1a2430" if lv == 1 else "#5b7089")
        s.append(txt(x, y, ("▾ " if lv < 2 else "· ") + name, 11, col, mono=True,
                     weight="700" if lv <= 1 else "400"))
        s.append(txt(470, y, desc, 10, "#93a4b8"))
        y += 26

    s.append(card(760, 86, 320, 210, "#f3f8fe", "#bcd7f0"))
    s.append(txt(774, 110, "四条硬规矩", 11.5, "#1d6fb8", weight="650"))
    for i, t in enumerate(["脚本必须能从头重跑（幂等）",
                           "每个产物能追溯到「哪个脚本、哪版数据」",
                           "报告文件名带时间戳，不要覆盖",
                           "inputs 只读，永远不改"]):
        s.append(txt(776, 134 + i * 24, "· " + t, 10.5, "#3d4d5f"))
    s.append(card(760, 310, 320, 120, "#fdf6e6", "#edd9a8"))
    s.append(txt(774, 334, "交接时对方最先看的三样", 11.5, "#96660f", weight="650"))
    for i, t in enumerate(["README 的「怎么跑」", "Makefile 的默认目标", "reports/ 里最新的时序汇总"]):
        s.append(txt(776, 358 + i * 22, "· " + t, 10.5, "#3d4d5f"))
    add_svg("pr-dir", W, H, "推荐的项目目录结构。右边四条规矩里最重要的是第一条：脚本要能从头重跑——这决定了别人（和三个月后的你）能不能复现结果。",
            "".join(s))


# ================================================================ ECO 链路
def fig_eco():
    W, H = 1120, 400
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "ECO 的五个环节：从「发现违例」到「验证没改坏」", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "ECO（Engineering Change Order）是版图已经基本成型之后的小改动。它的核心约束是：只动必要的线，不动已经收敛的部分。", 11.5, "#6b7f99"))

    steps = [("① PT 出清单", "fix_eco_timing\nwrite_changes", "#2f7fd0"),
             ("② 人工审核", "改动是否合理\n会不会引入新违例", "#7a5cd6"),
             ("③ 脚本改动", "size_cell\ninsert_buffer", "#18a07a"),
             ("④ 局部重布线", "legalize\necroute", "#d9901e"),
             ("⑤ 复算签核", "PT 重跑 + Formality", "#b3382f")]
    x0 = 50
    for i, (t, sub, col) in enumerate(steps):
        x = x0 + i * 210
        s.append(card(x, 92, 180, 84))
        s.append(f'<rect x="{x}" y="{92}" width="180" height="4" rx="2" fill="{col}"/>')
        s.append(txt(x + 14, 120, t, 12, "#1a2430", weight="650"))
        for j, ln in enumerate(sub.split("\n")):
            s.append(txt(x + 14, 142 + j * 16, ln, 9.5, col, mono=True))
        if i < 4:
            s.append(f'<path d="M {x + 184} {134} L {x + 206} {134}" stroke="#7e93a8" stroke-width="1.6" marker-end="url(#ah)"/>')

    s.append(card(50, 200, 490, 150, "#f3f8fe", "#bcd7f0"))
    s.append(txt(64, 224, "为什么不能「改完就发」", 11.5, "#1d6fb8", weight="650"))
    for i, t in enumerate(["改一个单元的驱动能力，会让它的输入电容变 → 上一级变慢",
                           "插一个 buffer，会占用布线轨道 → 旁边那条线可能绕远",
                           "所以每次 ECO 之后必须重新算时序，而且要看「有没有新违例」"]):
        s.append(txt(66, 248 + i * 22, "· " + t, 10.5, "#3d4d5f"))
    s.append(txt(66, 326, "→ 这就是 ECO 必须「一次只改一类、改完立刻复算」的原因", 10.5, "#b3382f", weight="600"))

    s.append(card(580, 200, 490, 150, "#fdf6e6", "#edd9a8"))
    s.append(txt(594, 224, "Formality / SVF 为什么必须有", 11.5, "#96660f", weight="650"))
    for i, t in enumerate(["ECO 改的是网表（换单元、插 buffer），功能必须不变",
                           "Formality 拿「综合前的 RTL」和「ECO 后的网表」做等价性证明",
                           "SVF 是综合时导出的「工具做过哪些变换」的记录，没有它 FM 会误报",
                           "结果只有两种：Verification SUCCEEDED / FAILED，没有「大概对」"]):
        s.append(txt(596, 248 + i * 22, "· " + t, 10.5, "#3d4d5f"))

    s.append(txt(50, H - 12, "四条纪律：一次只改一类 / 每轮复算 / 记录版本（git）/ 留回退点（改动前的数据库另存一份）", 10.5, "#93a4b8"))
    add_svg("eco-flow", W, H, "ECO 五环节。关键是第 ② 步和第 ⑤ 步最容易被跳过：人工审核决定「这个改法合不合理」，复算与等价性检查决定「有没有改坏」。跳过这两步的 ECO，是所有深夜事故的来源。",
            "".join(s))


# ================================================================ 简历对照
def fig_resume():
    W, H = 1120, 460
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "同一件事，两种写法：差简历与好简历的差别", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "面试官看一行的判断标准只有三个：你做了什么、怎么做的、结果如何。缺任何一个，这一行就白写。", 11.5, "#6b7f99"))

    pairs = [("负责数字后端物理实现工作",
              "用 Innovus 完成 soc_top（9390 单元 / 0.65 利用率）从 floorplan 到 GDS 的全流程；写 Tcl 脚本把 6 个阶段串成 make 一条命令，单次全流程从 4 小时压到 2.5 小时"),
             ("参与时序优化，修复违例",
              "定位 setup WNS −0.41ns 的根因（乘法器组合逻辑级数 14 级）；用 upsize + 插 buffer + useful skew 三招把 WNS 收到 +0.05ns，TNS 从 −18.6 降到 0"),
             ("熟悉 Linux 环境",
              "在 4 核 24G 服务器上用 tcsh 写批处理脚本跑 3 个 corner 并行签核，用日志 grep 自动提取 WNS/TNS 生成汇总表，把每周签核时间从半天压到 1 小时"),
             ("了解 DRM/DRC 检查",
              "用 Calibre 跑 DRC/LVS，把 312 条 DRC 按规则归类（M1.S 148 条 / V1.EN 92 条），定位到「宏通道里 via 没打满」这个根因，一次修掉 240 条")]
    y = 82
    for i, (bad, good) in enumerate(pairs):
        s.append(card(40, y, 490, 82, "#fdeeec", "#efc5c1"))
        s.append(txt(54, y + 22, "✗ 差", 10.5, "#b3382f", weight="700"))
        # 折行
        line, lines = "", []
        for ch in bad:
            line += ch
            if len(line) >= 24:
                lines.append(line); line = ""
        if line:
            lines.append(line)
        for j, ln in enumerate(lines[:2]):
            s.append(txt(54, y + 42 + j * 18, ln, 10.5, "#8a5a56"))

        s.append(card(560, y, 520, 82, "#eaf8f2", "#b6e0d0"))
        s.append(txt(574, y + 22, "✓ 好", 10.5, "#157a5b", weight="700"))
        line, lines = "", []
        for ch in good:
            line += ch
            if len(line) >= 26:
                lines.append(line); line = ""
        if line:
            lines.append(line)
        for j, ln in enumerate(lines[:3]):
            s.append(txt(574, y + 42 + j * 18, ln, 10.5, "#2f5f4c"))
        y += 92

    s.append(card(40, 452, 1040, 0, "#fff", "#fff"))
    s.append(txt(40, H - 6, "公式：动作（用了什么工具/方法）+ 对象（哪个设计、什么规模）+ 结果（数字）。三者缺一，面试官就没法判断你的水平。",
                 10.5, "#93a4b8"))
    add_svg("resume-compare", W, H, "简历对照。左边四行是「听起来很忙但什么都没说」的写法，右边同样四件事换成了「动作 + 对象 + 数字」。注意每一条右栏里都有至少一个具体数字。",
            "".join(s))


# ================================================================ 多时钟建树
def fig_multiclk():
    W, H = 1120, 420
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "多时钟设计怎么建树：分组、分频、MUX 后面怎么办", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "CTS 的核心假设是「这些触发器的时钟要一样快一样齐」。一旦设计里有多个时钟或分频时钟，这个假设就要靠约束来告诉工具。", 11.5, "#6b7f99"))

    # 时钟源
    s.append(card(40, 84, 240, 90))
    s.append(txt(56, 108, "主时钟 clk  400MHz", 11.5, "#1a2430", weight="650"))
    s.append(txt(56, 132, "create_clock -period 2.5", 10, "#1d6fb8", mono=True))
    s.append(txt(56, 152, "起点的唯一时间基准", 9.5, "#93a4b8"))

    # 分频
    s.append(f'<path d="M 284 129 L 330 129" stroke="#7e93a8" stroke-width="1.5" marker-end="url(#ah)"/>')
    s.append(card(334, 84, 250, 90))
    s.append(txt(350, 108, "分频时钟 clk_div2", 11.5, "#1a2430", weight="650"))
    s.append(txt(350, 132, "create_generated_clock -divide_by 2", 9.5, "#1d6fb8", mono=True))
    s.append(txt(350, 152, "由主时钟派生，不是新时钟源", 9.5, "#93a4b8"))

    # MUX
    s.append(f'<path d="M 588 129 L 634 129" stroke="#7e93a8" stroke-width="1.5" marker-end="url(#ah)"/>')
    s.append(card(638, 84, 250, 90, "#fdf6e6", "#edd9a8"))
    s.append(txt(654, 108, "时钟 MUX（多路选择）", 11.5, "#96660f", weight="650"))
    s.append(txt(654, 132, "clk 或 test_clk 二选一", 10, "#3d4d5f"))
    s.append(txt(654, 152, "MUX 后面的树要按两个时钟都建", 9.5, "#b3382f"))

    # 叶子
    s.append(f'<path d="M 892 129 L 938 129" stroke="#7e93a8" stroke-width="1.5" marker-end="url(#ah)"/>')
    s.append(card(942, 84, 138, 90, "#eef7f1", "#7cc4a4"))
    s.append(txt(958, 108, "1284 个叶子", 11.5, "#157a5b", weight="650"))
    s.append(txt(958, 130, "skew 目标 42ps", 10, "#157a5b", mono=True))
    s.append(txt(958, 150, "按组平衡", 9.5, "#93a4b8"))

    # 分组说明
    s.append(card(40, 200, 500, 176, "#f3f8fe", "#bcd7f0"))
    s.append(txt(54, 224, "时钟分组（skew group）怎么写", 11.5, "#1d6fb8", weight="650"))
    for i, t in enumerate(["create_clock_tree_spec 之后，编辑 .ctstch 文件",
                           "同一组内的叶子之间做平衡（skew 小）",
                           "不同组之间不做平衡（省 buffer、省电）",
                           "分错的后果：把异步时钟放进一组，工具会插几百个 buffer 去",
                           "「对齐」两个根本不需要对齐的时钟 —— 功耗白涨、还收不干净"]):
        s.append(txt(56, 248 + i * 22, "· " + t, 10.5, "#3d4d5f"))

    s.append(card(560, 200, 520, 176, "#fdf6e6", "#edd9a8"))
    s.append(txt(574, 224, "MUX 后面为什么特别麻烦", 11.5, "#96660f", weight="650"))
    for i, t in enumerate(["MUX 输出在功能模式下是 clk，测试模式下是 test_clk",
                           "工具分不清当前走哪一路，只能两条路都满足",
                           "所以 MUX 之后的树要按「两个时钟的公共部分」建",
                           "做法：把 MUX 输出定义成一个 generated clock，",
                           "并在 spec 里把它和两个源时钟都关联上"]):
        s.append(txt(576, 248 + i * 22, "· " + t, 10.5, "#3d4d5f"))

    s.append(txt(40, H - 12, "自检：report_clock_tree -summary 看每个时钟的 sinks/skew/levels；再看 report_clock_tree -skipped 有没有「被跳过没进树」的引脚（常开宏的 CK 常常漏在这里）。",
                 10.5, "#93a4b8"))
    add_svg("cts-multiclock", W, H, "多时钟建树的三层关系：主时钟 → 分频（generated clock）→ MUX → 叶子。每一层的约束写法都不一样，最容易被忽略的是 MUX——它让工具必须同时满足两条时钟路径。",
            "".join(s))


# ---- 收集
for _n, _f in list(globals().items()):
    if _n.startswith("fig_") and callable(_f):
        _f()
