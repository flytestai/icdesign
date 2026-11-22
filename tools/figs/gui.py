# -*- coding: utf-8 -*-
"""工具界面类配图：Innovus / PrimeTime / Calibre / Verdi / DC 的窗口版式。

说明：这是按真实工具的窗口结构**重绘的示意图**（菜单、面板、命令窗的位置与
真实工具一致），不是官方截图——为了避免版权与版本差异，图里的设计名、
数字都来自课程用的练习设计 soc_top，可以和你自己跑出来的结果对上。
"""

from figs.style import page
from figs.parts import (menu, tbar, tree, side, canvas, cons, ps, status, window,
                        die, macro, stripes, ring, rows, cells_grid, label, callout, esc)

FIGS = []


def add(fid, w, h, caption, html):
    FIGS.append((fid, w, h, page(html), caption))


# ---------------------------------------------------------------- 共用的芯片底板
def soc_scene(w=760, h=470, mode="floorplan", show_io=True, show_pg=False,
              show_rows=False, show_clk=False, show_cells=False, label_on=True):
    """返回一块画布里的芯片场景（die + 4 个 SRAM + 边角 macro）。

    mode: floorplan / place / cts / route / finish
    """
    pad = 26
    inner = []
    # IO ring 上的引脚
    if show_io:
        for i in range(14):
            x = 30 + i * ((w - 60) / 13)
            inner.append(f'<div class="pin" style="left:{x:.1f}px;top:{pad - 9}px;width:5px;height:9px"></div>')
            inner.append(f'<div class="pin" style="left:{x:.1f}px;top:{h - pad}px;width:5px;height:9px"></div>')
        for i in range(9):
            y = 40 + i * ((h - 80) / 8)
            inner.append(f'<div class="pin" style="left:{pad - 9}px;top:{y:.1f}px;width:9px;height:5px"></div>')
            inner.append(f'<div class="pin" style="left:{w - pad}px;top:{y:.1f}px;width:9px;height:5px"></div>')

    dx, dy, dw, dh = pad + 6, pad + 6, w - 2 * pad - 12, h - 2 * pad - 12

    # 电源环
    if show_pg:
        inner.append(ring(dx, dy, dw, dh, 5))
        inner.append(stripes(True, 7, (dx + 20, dy + 14, dw - 40, dh - 28), 4))
        inner.append(stripes(False, 9, (dx + 14, dy + 20, dw - 28, dh - 40), 4))

    # 宏单元（4 个 SRAM 在四角 + 2 个在中间带）
    macs = [(dx + 18, dy + 20, 118, 84, "SRAM_0 16K"),
            (dx + dw - 150, dy + 20, 118, 84, "SRAM_1 16K"),
            (dx + 18, dy + dh - 108, 118, 84, "SRAM_2 16K"),
            (dx + dw - 150, dy + dh - 108, 118, 84, "SRAM_3 16K"),
            (dx + dw / 2 - 70, dy + 18, 140, 56, "ROM 8K")]
    # 中间做一个通道给逻辑区
    logic_x, logic_y = dx + 155, dy + 20
    logic_w, logic_h = dw - 320, dh - 40

    if show_rows:
        inner.append(rows(logic_x - 4, logic_y + 62, logic_w + 8, logic_h - 66))
    if show_cells:
        inner.append(cells_grid(logic_x - 4, logic_y + 62, logic_w + 8, logic_h - 66,
                                hot=(120, 121, 122, 300), warm=(60, 61, 400)))
    for x, y, mw, mh, nm in macs:
        inner.append(macro(nm, x, y, mw, mh, pins=10))

    # 时钟树
    if show_clk:
        cx, cy = dx + dw / 2, dy + 96
        inner.append(f'<div style="position:absolute;left:{cx}px;top:{cy}px;width:8px;height:8px;background:#8fd6a7;border-radius:50%"></div>')
        inner.append(label("clk root", cx + 12, cy - 3, "#8fd6a7", 9))
        for tx, ty in [(logic_x + 6, logic_y + 78), (logic_x + logic_w * .5, logic_y + 150),
                       (logic_x + 10, logic_y + logic_h - 40), (logic_x + logic_w - 10, logic_y + 70),
                       (logic_x + logic_w * .35, logic_y + logic_h - 60), (dx + 160, dy + dh - 190)]:
            import math
            L = math.hypot(tx - cx, ty - cy)
            ang = math.degrees(math.atan2(ty - cy, tx - cx))
            inner.append(f'<div class="clk" style="left:{cx + 4}px;top:{cy + 3}px;width:{L:.0f}px;'
                         f'transform:rotate({ang:.1f}deg);opacity:.55"></div>')
            inner.append(f'<div style="position:absolute;left:{tx}px;top:{ty}px;width:6px;height:6px;'
                         f'background:#8fd6a7;border-radius:50%;opacity:.8"></div>')

    # 布线（route 模式画几条走线）
    if mode == "route":
        import random
        random.seed(11)
        for i in range(26):
            x1 = logic_x + random.randint(0, logic_w - 60)
            y1 = logic_y + random.randint(60, logic_h - 10)
            seg = [(x1, y1), (x1 + random.randint(20, 50), y1),
                   (x1 + random.randint(20, 50), y1 + random.randint(8, 26))]
            col = "#7cb8e8" if i % 3 else "#e8b45c"
            for (ax, ay), (bx, by) in ((seg[0], seg[1]), (seg[1], seg[2])):
                if ax == bx:
                    inner.append(f'<div style="position:absolute;left:{ax}px;top:{min(ay,by)}px;'
                                 f'width:1px;height:{abs(by - ay)}px;background:{col};opacity:.65"></div>')
                else:
                    inner.append(f'<div style="position:absolute;left:{min(ax,bx)}px;top:{ay}px;'
                                 f'width:{abs(bx - ax)}px;height:1px;background:{col};opacity:.65"></div>')

    if label_on:
        inner.append(label("soc_top  (core)", dx + 6, dy + 2, "#7fa8c9", 9.5))

    return (f'<div style="position:absolute;left:0;top:0;width:{w}px;height:{h}px">'
            + "".join(inner) + "</div>")


BROWSER = [
    (0, "▾ soc_top", 0),
    (1, "▾ SRAM_0", 0), (2, "IO_ring", 0), (2, "core", 0),
    (1, "▾ SRAM_1", 0), (2, "IO_ring", 0), (2, "core", 0),
    (1, "▾ SRAM_2", 0), (2, "IO_ring", 0), (2, "core", 0),
    (1, "▾ SRAM_3", 0), (2, "IO_ring", 0), (2, "core", 0),
    (1, "▾ ROM", 0), (2, "core", 0),
    (0, "▸ u_cpu", 0),
    (0, "▸ u_dsp", 0),
    (0, "▸ u_dma", 0),
]


def _browser(sel=None):
    items = []
    for lv, lab, _ in BROWSER:
        items.append((lv, lab, lab.strip("▾▸ ") == sel))
    return side("设计浏览器 · Design Browser", tree(items), 190)


# ================================================================ 1. Innovus 总览
def fig_gui():
    inner = (menu(["File", "Edit", "View", "Select", "Design", "Floorplan", "Place", "Clock",
                   "Route", "Timing", "ECO", "Power", "Window", "Help"], "Design")
             + tbar(9)
             + '<div class="body">' + _browser("soc_top")
             + canvas(soc_scene(750, 452, "floorplan", show_rows=True, show_pg=True),
                      "Layout View 1 — soc_top", "F 适应窗口   Z 缩放   K 标尺", 750, 452)
             + '</div>'
             + cons([ps("openDesign soc_top.enc.dat soc_top"),
                     ps("report_area", "Total area: 418237.6 um^2   Utilization: 62.4%", "out"),
                     ps("checkPlace", "CheckPlace: 0 placement violations.", "out")], 96)
             + status(["Ready", "soc_top", "Floorplan", "Snap: 0.005", "Lock: none", "X 128.4  Y 96.2"]))
    add("innovus-gui", 1000, 620,
        "Innovus 主窗口。左侧是设计浏览器（点宏单元能在版图里高亮），中间是版图视图（深色底、白色是单元、蓝色块是宏单元、橙色细条是电源条带），底部是 Tcl 命令窗——后面所有操作都在这个窗口里完成。",
        window("Innovus 21.1 — soc_top (Floorplan)", inner, 1000, 620, "Cadence Innovus"))


# ================================================================ 2. floorplan
def fig_floorplan():
    scene = soc_scene(720, 430, "floorplan", show_rows=True, show_io=True, label_on=False)
    inner = (menu(["File", "Edit", "View", "Select", "Design", "Floorplan", "Place", "Clock",
                   "Route", "Timing", "ECO", "Power", "Window", "Help"], "Floorplan")
             + tbar(9, hot=(4,))
             + '<div class="body">' + _browser("SRAM_0")
             + canvas(scene
                      + callout("宏单元沿边摆，引脚朝内→逻辑区", 8, 402, 210, "b")
                      + callout("中间留出布线通道", 300, 12, 120, "g")
                      , "Layout View 1 — soc_top  (floorplan)", "Grid 0.1um   Utilization 62.4%", 720, 430)
             + '</div>'
             + cons([ps("floorplan -site core -d 420 420 8 8 8 8 -r 1 0.624",
                        "Floorplan initialized: die 424.0 x 424.0 um", "out"),
                     ps("placeInstance SRAM_0 24 24 -fixed", "Placed 1 instance (fixed).", "out"),
                     ps("addIoPin ring -pin_size 0.12 0.12 -spacing 1.2",
                        "Created 148 IO pins on 4 sides.", "out")], 96)
             + status(["Ready", "soc_top", "Floorplan", "Util 62.4%", "Macro 5/5 placed"]))
    add("innovus-floorplan", 1000, 600,
        "Floorplan 阶段的界面。四个角上的蓝色块是 SRAM，中间大片是标准单元摆放区；外侧一圈黄色小方块是 IO 引脚。这张图回答的是「先放谁、放哪里、留多宽的通道」三个问题。",
        window("Innovus 21.1 — soc_top (Floorplan)", inner, 1000, 600, "Cadence Innovus"))


# ================================================================ 3. 电源规划
def fig_power():
    scene = soc_scene(720, 430, "floorplan", show_io=False, label_on=False)
    inner = (menu(["File", "Edit", "View", "Select", "Design", "Floorplan", "Place", "Clock",
                   "Route", "Timing", "ECO", "Power", "Window", "Help"], "Power")
             + tbar(9, hot=(6,))
             + '<div class="body">' + _browser()
             + canvas(scene
                      + callout("电源环 ring：围着芯片一圈", 8, 396, 200, "y")
                      + callout("电源条带 stripe：横竖交叉成网格", 250, 396, 210, "b")
                      + callout("交叉点必须打满 via，否则局部掉压", 470, 396, 230, "r")
                      , "Layout View 1 — power grid (M5/M6)", "Net: VDD  VSS", 720, 430)
             + '</div>'
             + cons([ps("addRing -nets {VDD VSS} -type core_rings -layer {top M6 bottom M6 left M5 right M5} -width 3 -spacing 1.2",
                        "Created core ring on M5/M6.", "out"),
                     ps("addStripe -nets {VDD VSS} -layer M5 -direction vertical -width 1.8 -set_to_set_distance 30",
                        "Created 24 stripes on M5.", "out"),
                     ps("verifyPowerVia -nets {VDD VSS}", "WARN: 118 cross points without full via stack", "warn")], 96)
             + status(["Ready", "soc_top", "Power Planning", "Ring: M5/M6", "Stripes: 24"]))
    add("innovus-power", 1000, 600,
        "电源规划界面。橙色一圈是电源环，黄橙色网格是电源条带，它们负责把 pad 上的电送到每一个标准单元。右下角的告警提示「有 118 个交叉点没有打满 via」——这是后面 IR drop 超标最常见的原因。",
        window("Innovus 21.1 — soc_top (Power Planning)", inner, 1000, 600, "Cadence Innovus"))


# ================================================================ 4. placement
def fig_place():
    scene = soc_scene(720, 430, "place", show_rows=True, show_cells=True, label_on=False)
    inner = (menu(["File", "Edit", "View", "Select", "Design", "Floorplan", "Place", "Clock",
                   "Route", "Timing", "ECO", "Power", "Window", "Help"], "Place")
             + tbar(9, hot=(5,))
             + '<div class="body">' + _browser()
             + canvas(scene
                      + callout("红色 = 局部密度过高（拥塞风险）", 8, 396, 240, "r")
                      , "Layout View 1 — soc_top  (placed)", "Density 0.71  Congestion H 0.8% V 1.2%", 720, 430)
             + '</div>'
             + cons([ps("setPlaceMode -place_global_max_density 0.75", "", "out"),
                     ps("place_opt_design",
                        "Placement complete. 9390 instances. Runtime 4m12s.", "out"),
                     ps("reportCongestion -hotSpot",
                        "Hot spot: (312.4, 188.6)  overflow 14 tracks", "warn")], 96)
             + status(["Ready", "soc_top", "Placed", "Density 71%", "Congestion 1.2%"]))
    add("innovus-place", 1000, 600,
        "布局完成后的界面。一排排细横线是标准单元行（cell row），行里的小方块就是一个个标准单元。红色区域表示该处单元挤得太密，布线时会走不通——这就是「拥塞」的直观样子。",
        window("Innovus 21.1 — soc_top (Placement)", inner, 1000, 600, "Cadence Innovus"))


# ================================================================ 5. CTS
def fig_cts():
    scene = soc_scene(720, 430, "cts", show_rows=True, show_clk=True, label_on=False)
    inner = (menu(["File", "Edit", "View", "Select", "Design", "Floorplan", "Place", "Clock",
                   "Route", "Timing", "ECO", "Power", "Window", "Help"], "Clock")
             + tbar(9, hot=(7,))
             + '<div class="body">' + _browser()
             + canvas(scene
                      + callout("绿色圆点 = 时钟缓冲器（buffer/inverter）", 8, 396, 250, "g")
                      + callout("树根到每个叶子的延迟要尽量相等 → skew 小", 300, 396, 240, "b")
                      , "Layout View 1 — clock tree", "Skew 42ps  Latency 0.68ns  Buffers 214", 720, 430)
             + '</div>'
             + cons([ps("create_ccopt_clock_tree_spec", "Generated CTS spec: 3 clock roots, 1284 sinks", "out"),
                     ps("ccopt_design -cts", "Clock tree synthesis finished. Inserted 214 buffers.", "out"),
                     ps("report_clock_tree -summary",
                        "Clock  Sinks  Skew   Latency  Levels\\nclk    1284   42ps   0.68ns   7", "out")], 96)
             + status(["Ready", "soc_top", "CTS done", "Skew 42ps", "Buffers 214"]))
    add("innovus-cts", 1000, 600,
        "时钟树综合后的界面。绿色线条是从时钟源（树根）一路分叉到每个触发器的时钟网络，绿点是工具自动插入的缓冲器。这张图要看的是：分叉是否均匀、有没有某个分支特别长。",
        window("Innovus 21.1 — soc_top (CTS)", inner, 1000, 600, "Cadence Innovus"))


# ================================================================ 6. route
def fig_route():
    scene = soc_scene(720, 430, "route", show_rows=True, show_cells=True, label_on=False)
    inner = (menu(["File", "Edit", "View", "Select", "Design", "Floorplan", "Place", "Clock",
                   "Route", "Timing", "ECO", "Power", "Window", "Help"], "Route")
             + tbar(9, hot=(8,))
             + '<div class="body">' + _browser()
             + canvas(scene
                      + callout("蓝线 = 信号线，橙线 = 换层（via 处）", 8, 396, 250, "b")
                      + callout("红色方块 = DRC 违例（短路/间距）", 300, 396, 230, "r")
                      , "Layout View 1 — routed", "DRC 0   Total wire 41.2m   Vias 28614", 720, 430)
             + '</div>'
             + cons([ps("routeDesign", "Global route done. 0 overflow.", "out"),
                     ps("routeDesign -detail", "Detail route done. DRC violations: 312", "out"),
                     ps("optDesign -postRoute -drv",
                        "Round 1: 312 -> 46 DRC", "out"),
                     ps("verify_drc", "Total DRC violations: 0", "g")], 96)
             + status(["Ready", "soc_top", "Routed", "DRC 0", "Vias 28614"]))
    add("innovus-route", 1000, 600,
        "布线完成后的界面。蓝线是信号走线，橙点是换层用的 via，红色小方块是还没修掉的 DRC 违例。命令窗里的四行是真实收线过程：全局布线 0 溢出 → 详细布线 312 个违例 → 优化后剩 46 → 再修到 0。",
        window("Innovus 21.1 — soc_top (Routing)", inner, 1000, 600, "Cadence Innovus"))


# ================================================================ 7. PT shell
PT_TEXT = [
    ("p", "pt_shell> ", "read_verilog ./netlist/soc_top.v"),
    ("o", "", "Loading db file '/pdk/nangate45/nangate45_typ.db'"),
    ("o", "", "Warning: Unresolved reference to 'SRAM_16K' (link_library)."),
    ("p", "pt_shell> ", "link_design soc_top"),
    ("o", "", "Information: Linking cell 'soc_top'. (LINK-5)"),
    ("o", "", "Design 'soc_top' linked. 9390 cells, 12031 nets."),
    ("p", "pt_shell> ", "read_parasitics -format spef ./spef/soc_top.spef"),
    ("o", "", "Information: Read 12031 RC networks from SPEF. (PARA-012)"),
    ("p", "pt_shell> ", "source ./sdc/soc_top.sdc"),
    ("o", "", "Information: 3 clocks, 148 io delays, 12 exceptions. (SDC-1)"),
    ("p", "pt_shell> ", "check_timing"),
    ("y", "", "Warning: 14 endpoints are unconstrained. (TIM-134)"),
    ("p", "pt_shell> ", "report_timing -max_paths 1 -nworst 1"),
]

PT_RPT = """
<b>Startpoint:</b> u_cpu/reg_bank/q_reg[3]/CK  (rising edge-triggered flip-flop clocked by clk)
<b>Endpoint:</b>   u_dsp/mac_pipe/mult_reg[11]/D (rising edge-triggered flip-flop clocked by clk)
<b>Path Group:</b> clk
<b>Path Type:</b>  max

  <span class="d">Point</span>                                       <span class="d">Incr</span>     <span class="d">Path</span>
  ---------------------------------------------------------------
  clock clk (rise edge)                       0.0000    0.0000
  clock network delay (ideal)                 0.0000    0.0000
  u_cpu/reg_bank/q_reg[3]/CK                  0.0000    0.0000 r
  u_cpu/reg_bank/q_reg[3]/Q                   0.0912    0.0912 f
  u_dsp/mac_pipe/U2214/Z                     0.1843    0.2755 r
  u_dsp/mac_pipe/U1877/Z                     0.2211    0.4966 f
  u_dsp/mac_pipe/U903/Z                      0.2087    0.7053 r
  u_dsp/mac_pipe/mult_reg[11]/D              0.0031    0.7084 r
  data arrival time                                     <span class="n">0.7084</span>

  clock clk (rise edge)                       2.5000    2.5000
  clock network delay (ideal)                 0.0000    2.5000
  clock uncertainty                          -0.1200    2.3800
  u_dsp/mac_pipe/mult_reg[11]/CK              0.0000    2.3800 r
  library setup time                         -0.0683    2.3117
  data required time                                    <span class="g">2.3117</span>
  ---------------------------------------------------------------
  data required time                                    <span class="g">2.3117</span>
  data arrival time                                    <span class="n">-0.7084</span>
  ---------------------------------------------------------------
  slack (MET)                                           <span class="g">1.6033</span>
"""


def fig_pt():
    body = '<div style="padding:14px">'
    body += '<div class="term" style="border-radius:6px 6px 0 0">'
    for kind, p, txt in PT_TEXT[:9]:
        line = (f'<span class="p">{p}</span><span class="c">{esc(txt)}</span>' if p
                else (f'<span class="y">{esc(txt)}</span>' if kind == "y" else f'<span class="o">{esc(txt)}</span>'))
        body += line + "\n"
    body += "</div>"
    body += ('<div class="rpt" style="border-radius:0 0 6px 6px;border-top:0">'
             '<div class="rpt-h">report_timing — 最差一条 setup 路径</div>'
             f'<div class="rpt-b">{PT_RPT}</div></div>')
    body += "</div>"
    add("pt-shell", 1000, 700,
        "PrimeTime 的签核过程。上半部分是命令窗（读库、读网表、读 SPEF、读约束、检查约束），下半部分是 report_timing 的输出。这张报告是整站最重要的一张图：每一列、每一行的含义在第 05-02 课里逐项拆开讲。",
        window("PrimeTime 2022.03-SP5 — soc_top (signoff)", body, 1000, 700, "Synopsys PrimeTime", ))


# ================================================================ 8. Calibre RVE
def fig_calibre():
    rows_html = [
        ("1", "M1.S.1", "0.042", "(128.420 96.180)", "Metal1 spacing < 0.065", "SRAM_0 / core"),
        ("2", "M1.S.1", "0.038", "(129.100 96.180)", "Metal1 spacing < 0.065", "SRAM_0 / core"),
        ("3", "V1.EN.1", "0.011", "(210.960 44.220)", "Via1 enclosure by Metal1", "u_dsp/U903"),
        ("4", "M2.W.1", "0.065", "(88.300 142.700)", "Metal2 width < 0.070", "u_cpu/U2214"),
        ("5", "M4.S.2", "0.088", "(301.550 210.440)", "Metal4 spacing (parallel run)", "u_dma/U117"),
    ]
    tbl = ('<table style="width:100%;border-collapse:collapse;font:11px Consolas">'
           '<tr style="background:#eef3f9;color:#42566b">'
           + "".join(f'<th style="text-align:left;padding:4px 7px;border-bottom:1px solid #dfe6ee;font-weight:600">{h}</th>'
                     for h in ("#", "Rule", "Value", "Coordinate", "Description", "Instance"))
           + "</tr>")
    for i, r in enumerate(rows_html):
        bg = "#fff" if i % 2 == 0 else "#fafcfe"
        tbl += (f'<tr style="background:{bg}">'
                + "".join(f'<td style="padding:3.5px 7px;border-bottom:1px solid #eef2f7;color:{"#b3382f" if j == 2 else "#22303f"}">{c}</td>'
                          for j, c in enumerate(r))
                + "</tr>")
    tbl += "</table>"

    inner = (menu(["File", "Edit", "View", "Tools", "Window", "Help"], "Tools")
             + tbar(8, hot=(1,))
             + '<div class="body">'
             + side("DRC Results · 5 of 312", f'<div style="padding:8px 6px;font-size:11px;line-height:1.9;color:#35495e">'
                                              f'<div>▾ <b>soc_top.gds</b> <span class="k">312</span></div>'
                                              f'<div style="padding-left:14px">▾ M1.S.1 <span class="k">148</span></div>'
                                              f'<div style="padding-left:14px">▾ V1.EN.1 <span class="k">92</span></div>'
                                              f'<div style="padding-left:14px">▾ M2.W.1 <span class="k">51</span></div>'
                                              f'<div style="padding-left:14px">▾ M4.S.2 <span class="k">21</span></div>'
                                              f'</div>', 250)
             + '<div style="flex:1;display:flex;flex-direction:column;min-width:0">'
             + canvas(soc_scene(700, 300, "route", show_cells=True, label_on=False)
                      + '<div style="position:absolute;left:120px;top:96px;width:26px;height:18px;'
                        'border:1.5px solid #ff6b5e;box-shadow:0 0 0 3px rgba(255,107,94,.18)"></div>'
                      + label("← 违例位置（坐标见下表）", 152, 98, "#ff9d92", 10)
                      , "Layout — soc_top.gds  (layer M1)", "Zoom 1:8", 700, 300)
             + f'<div style="background:#fff;border-top:1px solid #dfe6ee;flex:1;overflow:hidden">{tbl}</div>'
             + "</div></div>"
             + status(["Ready", "soc_top.gds", "Rule file: SMC_40nm.drc", "Violations 312", "Cell: SRAM_0"]))
    add("calibre-rve", 1000, 620,
        "Calibre RVE 的结果查看窗口。左边按「规则名」分组列出违例条数，右边上半是版图（红框标出出问题的位置），下半是明细表：规则名、实测值、限制值、坐标、所在单元。学会读这张表，等于学会改 DRC。",
        window("Calibre RVE — soc_top.gds  DRC results", inner, 1000, 620, "Siemens Calibre"))


# ================================================================ 9. dbGet
def fig_dbget():
    body = ('<div style="padding:14px"><div class="term">'
            '<span class="p">innovus&gt;</span> <span class="c">dbGet top.name</span>\n'
            '<span class="o">soc_top</span>\n'
            '<span class="p">innovus&gt;</span> <span class="c">dbGet [dbGet top.insts.cell.name -p2 SRAM*].name</span>\n'
            '<span class="o">SRAM_0 SRAM_1 SRAM_2 SRAM_3</span>\n'
            '<span class="p">innovus&gt;</span> <span class="c">dbGet [dbGet -p top.insts.name SRAM_0].pt</span>\n'
            '<span class="o">24.000 24.000</span>\n'
            '<span class="p">innovus&gt;</span> <span class="c">dbGet head.libCells.name | head -5</span>\n'
            '<span class="o">BUF_X1 BUF_X2 BUF_X4 INV_X1 INV_X2</span>\n'
            '<span class="p">innovus&gt;</span> <span class="c">dbGet [dbGet -p top.nets.name VDD].numPins</span>\n'
            '<span class="y">Error: can\'t read "numPins": no such attribute</span>\n'
            '<span class="p">innovus&gt;</span> <span class="c">dbGet [dbGet -p top.nets.name VDD].term.count</span>\n'
            '<span class="o">4286</span>\n'
            '</div>'
            '<div style="margin-top:10px;display:flex;gap:8px;font-size:11.5px">'
            '<div class="chip c-b">dbGet 对象 → .属性 一层层剥</div>'
            '<div class="chip c-y">属性名写错 → 直接报 can\'t read</div>'
            '<div class="chip c-g">-p 是过滤（filter）</div>'
            '</div></div>')
    add("dbget-shell", 1000, 420,
        "Innovus 的数据库查询命令 dbGet。设计里的每个对象（实例、网络、库单元）都能按「对象.属性」一层层取出来，最后一行那个报错很有代表性：属性名写错时工具不会猜，直接告诉你 can't read。",
        window("Innovus 21.1 — Tcl console (dbGet)", body, 1000, 420, "Cadence Innovus"))


# ---- 模块加载时把本文件里所有 fig_* 函数跑一遍，收集成 FIGS ----
for _n, _f in list(globals().items()):
    if _n.startswith("fig_") and callable(_f):
        _f()
