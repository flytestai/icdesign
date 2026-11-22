# -*- coding: utf-8 -*-
"""版图布局类配图：floorplan / 宏通道 / IO 分配 / 电源层级 / 拥塞热图。"""

from figs.style import page, svgwrap

FIGS = []
FONT = '"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif'
MONO = '"Cascadia Mono",Consolas,monospace'


def add(fid, w, h, caption, body):
    FIGS.append((fid, w, h, page(svgwrap(w, h, body)), caption))


def txt(x, y, s, size=12, fill="#3d4d5f", anchor="start", mono=False, weight="400"):
    fam = MONO if mono else FONT
    return (f'<text x="{x}" y="{y}" font-family={fam!r} font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


# ================================================================ 宏单元通道
def fig_channel():
    W, H = 1120, 470
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 28, "宏单元之间要留多宽的通道？一个能算出来的数", 15, "#1a2430", weight="650"))
    s.append(txt(24, 48, "通道太窄 → 宏的引脚拉不出来、布线堵死；通道太宽 → 面积白送。宽度不是凭感觉，是「引脚数 × 间距 + 电源走廊 + 余量」。", 11.5, "#6b7f99"))

    # 两个 SRAM
    for i, x in enumerate((88, 588)):
        s.append(f'<rect x="{x}" y="90" width="400" height="150" fill="#2b4a68" stroke="#7aa8cd"/>')
        s.append(txt(x + 200, 172, f"SRAM_{i}  256×64", 13, "#cfe2f2", "middle", mono=True))
        s.append(txt(x + 200, 192, "宽 200µm × 高 75µm", 11, "#9fbed9", "middle"))
        # 底部引脚
        for k in range(16):
            px = x + 16 + k * 23
            s.append(f'<rect x="{px}" y="240" width="7" height="14" fill="#e8b45c"/>')
    s.append(txt(288, 272, "16 个信号引脚（朝下）", 10.5, "#b4531a", "middle", mono=True))
    s.append(txt(788, 272, "16 个信号引脚（朝上）", 10.5, "#b4531a", "middle", mono=True))

    # 通道标注
    s.append(f'<rect x="88" y="254" width="900" height="86" fill="#f3f8fe" stroke="#9dc4e8" stroke-dasharray="5 4"/>')
    s.append(txt(96, 272, "宏通道 macro channel（这里是逻辑区 + 布线通道）", 11.5, "#1d6fb8", weight="600"))

    # 宽度分解
    bx, by = 88, 356
    parts = [("16 引脚 × 1.4µm 间距", 224, "#7cb8e8"), ("电源走廊 2 × 6µm", 120, "#d9901e"),
             ("余量 20%", 90, "#18a07a"), ("合计 ≈ 43µm", 140, "#2f7fd0")]
    x = bx
    for name, wpx, col in parts:
        s.append(f'<rect x="{x}" y="{by}" width="{wpx - 4}" height="34" rx="4" fill="{col}" opacity=".22" stroke="{col}"/>')
        s.append(txt(x + (wpx - 4) / 2, by + 22, name, 10.5, "#22303f", "middle"))
        x += wpx
    s.append(txt(bx, by + 56, "16×1.4 = 22.4   电源走廊 12   余量 (22.4+12)×0.2 ≈ 6.9   →   22.4 + 12 + 6.9 ≈ 41.3µm，取 43µm",
                 11, "#3d4d5f", mono=True))
    s.append(txt(bx, by + 78, "布线通道还要按「每行横向走线数」再校验一次：3 层可用 × 0.14µm 间距 ≈ 每 µm 约 21 条轨道，够不够看引脚密度。",
                 11, "#6b7f99"))
    add("fp-channel", W, H, "宏单元通道宽度的手算过程。两个 SRAM 面对面摆，引脚都朝内，中间这条通道要同时容纳：引脚拉出的线、两条电源走廊、以及 20% 的余量。下面的色条把这个加法拆开了。",
        "".join(s))


# ================================================================ IO 分配
def fig_io():
    W, H = 1120, 470
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 28, "IO 引脚怎么分配到四边：按信号流向，不是平均分", 15, "#1a2430", weight="650"))
    s.append(txt(24, 48, "原则只有一条：让信号走最短的路。左边进的数据就给左边的引脚，跨到对面去会平白多出几百微米的线长和一堆时序问题。", 11.5, "#6b7f99"))

    dx, dy, dw, dh = 120, 92, 700, 300
    s.append(f'<rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" fill="#16273a"/>')
    s.append(txt(dx + 8, dy + 16, "soc_top  (die 424 × 424 µm)", 10, "#7fa8c9", mono=True))
    # 内部块
    s.append(f'<rect x="{dx + 60}" y="{dy + 60}" width="180" height="90" fill="#2b4a68" stroke="#7aa8cd"/>')
    s.append(txt(dx + 150, dy + 110, "u_cpu", 11, "#cfe2f2", "middle", mono=True))
    s.append(f'<rect x="{dx + 460}" y="{dy + 60}" width="180" height="90" fill="#2b4a68" stroke="#7aa8cd"/>')
    s.append(txt(dx + 550, dy + 110, "u_dsp", 11, "#cfe2f2", "middle", mono=True))
    s.append(f'<rect x="{dx + 260}" y="{dy + 200}" width="180" height="70" fill="#2b4a68" stroke="#7aa8cd"/>')
    s.append(txt(dx + 350, dy + 240, "u_dma", 11, "#cfe2f2", "middle", mono=True))

    # 引脚（按功能着色）
    def pins(side, items, color):
        out = []
        n = len(items)
        if side in ("top", "bottom"):
            for i, nm in enumerate(items):
                x = dx + 30 + i * ((dw - 60) / max(n - 1, 1))
                y = dy - 8 if side == "top" else dy + dh
                out.append(f'<rect x="{x}" y="{y}" width="7" height="8" fill="{color}"/>')
                if nm:
                    out.append(txt(x + 3.5, y - 4 if side == "top" else y + 20, nm, 9, color, "middle", mono=True))
        else:
            for i, nm in enumerate(items):
                y = dy + 30 + i * ((dh - 60) / max(n - 1, 1))
                x = dx - 8 if side == "left" else dx + dw
                out.append(f'<rect x="{x}" y="{y}" width="8" height="7" fill="{color}"/>')
                if nm:
                    out.append(txt(x - 4 if side == "left" else x + 12, y + 8, nm, 9, color,
                                   "end" if side == "left" else "start", mono=True))
        return "".join(out)

    s.append(pins("left", ["i_data[0]", "i_data[1]", "i_data[2]", "i_data[3]", "", "i_valid", "i_clk"], "#e8b45c"))
    s.append(pins("right", ["o_data[0]", "o_data[1]", "o_data[2]", "", "o_valid", "o_ready"], "#8fd6a7"))
    s.append(pins("top", ["VDD", "VDD", "", "VDDIO", "VDDIO", "", "VSS", "VSS"], "#e07a5f"))
    s.append(pins("bottom", ["VSS", "", "VSS", "", "TEST_EN", "SCAN_IN", "SCAN_OUT"], "#e07a5f"))

    # 说明
    bx = 856
    notes = [("#e8b45c", "左边 = 输入", "数据从左边进 → 引脚放左边，走线最短"),
             ("#8fd6a7", "右边 = 输出", "数据往右边出 → 引脚放右边，直接送到下一级"),
             ("#e07a5f", "电源在上下", "电源引脚优先占上下边，方便打环与接封装")]
    y = 100
    for col, t, d in notes:
        s.append(f'<rect x="{bx}" y="{y}" width="10" height="10" rx="2" fill="{col}"/>')
        s.append(txt(bx + 18, y + 9, t, 11.5, "#22303f", weight="650"))
        # 折行
        line, lines = "", []
        for ch in d:
            line += ch
            if len(line) >= 13:
                lines.append(line); line = ""
        if line:
            lines.append(line)
        for i, ln in enumerate(lines[:3]):
            s.append(txt(bx + 18, y + 26 + i * 15, ln, 10, "#6b7f99"))
        y += 26 + 15 * min(len(lines), 3) + 16

    s.append(txt(24, H - 12, "分配完要自检：① 每个引脚都有名字、没漏 ② 电源引脚数量够（按峰值电流算） ③ 时钟/复位不要与高速数据贴在一起（串扰）",
                 11, "#6b7f99"))
    add("fp-io", W, H, "IO 引脚分配图。黄色是输入、绿色是输出、红色是电源地。分法的依据是信号流向：从哪边进来的数据就放在哪边，别让线横穿整个芯片。",
        "".join(s))


# ================================================================ 电源层级
def fig_pg():
    W, H = 1120, 480
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 28, "电从 pad 到每个单元：五级接力，任何一级断了单元就饿死", 15, "#1a2430", weight="650"))
    s.append(txt(24, 48, "这也是「为什么电源要单独规划」的答案：它不是一根线，而是一套从粗到细的树状网络。", 11.5, "#6b7f99"))

    stages = [("① Pad / Bump", "封装的焊球，电流从这里进芯片", "#e07a5f"),
              ("② 电源环 ring", "沿 die 四周一圈，把电流摊开", "#d9901e"),
              ("③ 电源条带 stripe", "横竖网格，把电送到芯片内部每一处", "#e8b45c"),
              ("④ 单元电源轨 rail", "沿单元行布置的长条（followpin）", "#7cb8e8"),
              ("⑤ 单元内部", "标准单元的 VDD/VSS 引脚", "#2f7fd0")]
    y = 84
    for i, (t, d, col) in enumerate(stages):
        w = 470 - i * 46
        x = 40 + i * 23
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="52" rx="6" fill="{col}" opacity=".18" stroke="{col}"/>')
        s.append(txt(x + 12, y + 22, t, 12.5, "#22303f", weight="650"))
        s.append(txt(x + 12, y + 40, d, 10.5, "#5b7089"))
        if i < 4:
            s.append(f'<path d="M {x + 26} {y + 52} L {x + 26} {y + 62}" stroke="#7e93a8" stroke-width="1.4" '
                     f'marker-end="url(#ah)"/>')
        y += 62

    # 右侧：电流与压降
    bx = 570
    s.append(f'<rect x="{bx}" y="84" width="510" height="150" rx="8" fill="#f3f8fe" stroke="#bcd7f0"/>')
    s.append(txt(bx + 14, 108, "为什么越往上越粗：IR drop 的手算", 12.5, "#1d6fb8", weight="650"))
    s.append(txt(bx + 14, 132, "假设某条 stripe 要供 1.2A 的电流，走的是 M5，方块电阻约 0.02Ω/□", 11, "#3d4d5f"))
    s.append(txt(bx + 14, 154, "长 300µm、宽 1.8µm → 方块数 = 300 ÷ 1.8 ≈ 167 个", 11, "#3d4d5f", mono=True))
    s.append(txt(bx + 14, 176, "电阻 = 167 × 0.02 ≈ 3.3Ω  →  ← 这个量级显然不对", 11, "#b3382f", mono=True))
    s.append(txt(bx + 14, 198, "所以供电必须靠「并联多根 + 上层厚金属」把总电阻压到 mΩ 级", 11, "#3d4d5f"))
    s.append(txt(bx + 14, 220, "1A 电流 × 10mΩ = 10mV，占 0.9V 的 1.1% —— 这才是可接受的目标", 11, "#157a5b", mono=True))

    s.append(f'<rect x="{bx}" y="250" width="510" height="128" rx="8" fill="#fdf6e6" stroke="#edd9a8"/>')
    s.append(txt(bx + 14, 274, "四个必查项", 12.5, "#96660f", weight="650"))
    for i, t in enumerate(["ring 是否闭合（四个角要连上）",
                           "stripe 与 macro 电源引脚是否真的接上",
                           "每个交叉点 via 是否打满（用 verifyPowerVia 查）",
                           "followpin 是否与单元行对齐（行高变了就会错位）"]):
        s.append(txt(bx + 16, 298 + i * 20, "· " + t, 11, "#3d4d5f"))

    s.append(txt(40, H - 12, "经验值：电源网络通常吃掉 8%~15% 的布线资源。规划时留少了，后面 CTS 和 route 会发现「没地方走线」。",
                 11, "#6b7f99"))
    add("pg-tree", W, H, "电源的五级接力。从封装焊球到单元内部，每一级都比上一级更细更密。右边的手算说明了为什么供电必须靠并联和上层厚金属：单根细线的电阻会让电压掉到无法工作。",
        "".join(s))


# ================================================================ 拥塞热图
def fig_congestion():
    W, H = 1120, 440
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 28, "拥塞热图（congestion map）怎么看", 15, "#1a2430", weight="650"))
    s.append(txt(24, 48, "每一格代表一小块区域里「想走的线」比「能走的轨道」多出多少。绿色 = 富余，黄色 = 快满了，红色 = 已经溢出（走不通）。", 11.5, "#6b7f99"))

    import math
    gx, gy, cell, n = 60, 80, 22, 20
    hot = [(6, 4, 3.0), (13, 12, 2.6), (9, 15, 1.8), (4, 13, 1.5)]
    for r in range(12):
        for c in range(n):
            v = 0.0
            for hx, hy, amp in hot:
                v += amp * math.exp(-((c - hx) ** 2 + (r - hy) ** 2) / 9.0)
            v = min(v, 1.6)
            if v < 0.25:
                col, op = "#18a07a", 0.16
            elif v < 0.6:
                col, op = "#d9901e", 0.30
            elif v < 1.0:
                col, op = "#e07a3f", 0.55
            else:
                col, op = "#d9534f", 0.80
            s.append(f'<rect x="{gx + c * cell}" y="{gy + r * cell}" width="{cell - 1}" height="{cell - 1}" '
                     f'fill="{col}" opacity="{op:.2f}"/>')
    s.append(f'<rect x="{gx}" y="{gy}" width="{n * cell}" height="{12 * cell}" fill="none" stroke="#c9d5e2"/>')
    s.append(txt(gx + n * cell / 2, gy - 8, "soc_top  (12 × 20 格)", 10.5, "#5b7089", "middle", mono=True))

    # 图例
    lx, ly = 60, gy + 12 * cell + 20
    for i, (lbl, col, op) in enumerate([("富余 <25%", "#18a07a", .16), ("偏紧 25~60%", "#d9901e", .30),
                                        ("紧张 60~100%", "#e07a3f", .55), ("溢出 >100%", "#d9534f", .80)]):
        s.append(f'<rect x="{lx + i * 150}" y="{ly}" width="14" height="14" fill="{col}" opacity="{op}"/>')
        s.append(txt(lx + i * 150 + 20, ly + 11, lbl, 10.5, "#3d4d5f"))

    # 说明
    bx = 560
    s.append(f'<rect x="{bx}" y="80" width="520" height="164" rx="8" fill="#fdeeec" stroke="#efc5c1"/>')
    s.append(txt(bx + 14, 104, "红色区域的四个常见成因（按排查顺序）", 12.5, "#b3382f", weight="650"))
    for i, t in enumerate(["① 局部单元密度过高 → 回 placement 降 density 或加 blockage",
                           "② 宏通道太窄 → 回 floorplan 加宽通道",
                           "③ 引脚分配把线都赶到同一侧 → 改 IO 分配",
                           "④ 时钟树占了太多轨道 → 收 NDR 或减 buffer"]):
        s.append(txt(bx + 16, 130 + i * 22, t, 11, "#3d4d5f"))

    s.append(f'<rect x="{bx}" y="258" width="520" height="100" rx="8" fill="#f3f8fe" stroke="#bcd7f0"/>')
    s.append(txt(bx + 14, 282, "看图的顺序（别一上来就改布线）", 12.5, "#1d6fb8", weight="650"))
    s.append(txt(bx + 16, 304, "全局溢出 overflow → 热点 hotSpot 位置 → 是不是和宏通道/密度热点重合", 11, "#3d4d5f"))
    s.append(txt(bx + 16, 326, "→ 重合就回上游改；不重合才是布线器的问题（这时才调 route 参数）", 11, "#3d4d5f"))
    add("congestion-map", W, H, "拥塞热图。颜色越红表示该处「想走的线」超出「能走的轨道」越多。四个红斑的位置正好对着宏通道和密度高的区域——这就是为什么说拥塞大多是上游（floorplan / placement）造成的，不是布线器不努力。",
        "".join(s))


# ================================================================ SDC 解剖
def fig_sdc():
    W, H = 1120, 470
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 28, "一份 SDC 约束文件的结构：五条打底，其余按需", 15, "#1a2430", weight="650"))
    s.append(txt(24, 48, "SDC（Synopsys Design Constraints）是「设计要求」的文字版。工具不会猜你的意图，你写什么它查什么；写漏了，它就不查。", 11.5, "#6b7f99"))

    rows = [("create_clock", "时钟周期与名字", "定义「时间基准」，不定义它后面全错", "#18a07a"),
            ("set_input_delay", "输入引脚相对时钟的延迟", "告诉工具「外面那级电路要花多久」", "#2f7fd0"),
            ("set_output_delay", "输出引脚相对时钟的延迟", "告诉工具「下一级要留多久给它」", "#2f7fd0"),
            ("set_clock_uncertainty", "时钟抖动 + 余量", "给时钟的不确定性留安全边际", "#d9901e"),
            ("set_max_transition", "最大翻转时间", "信号边沿不能太慢，否则延迟失控", "#7a5cd6")]
    y = 86
    for cmd, arg, why, col in rows:
        s.append(f'<rect x="40" y="{y}" width="560" height="58" rx="6" fill="#fff" stroke="#e3e9f0"/>')
        s.append(f'<rect x="40" y="{y}" width="4" height="58" fill="{col}"/>')
        s.append(txt(56, y + 24, cmd, 12, "#1a2430", mono=True, weight="700"))
        s.append(txt(210, y + 24, arg, 11, "#6b7f99"))
        s.append(txt(56, y + 44, why, 10.5, "#5b7089"))
        y += 66

    bx = 630
    s.append(f'<rect x="{bx}" y="86" width="450" height="200" rx="8" fill="#0f1a26"/>')
    code = [("d", "# soc_top.sdc —— 最小可用约束"),
            ("g", "create_clock -name clk -period 2.5 [get_ports clk]"),
            ("b", "set_input_delay  -clock clk 0.35 [all_inputs]"),
            ("b", "set_output_delay -clock clk 0.45 [all_outputs]"),
            ("y", "set_clock_uncertainty 0.12 [get_clocks clk]"),
            ("v", "set_max_transition 0.15 [current_design]")]
    yy = 112
    for c, t in code:
        col = {"d": "#647a91", "g": "#7fd6a3", "b": "#7cb8e8", "y": "#e6b455", "v": "#c3a8f5"}[c]
        s.append(txt(bx + 16, yy, t.replace("&", "&amp;").replace("<", "&lt;"), 10.5, col, mono=True))
        yy += 28

    s.append(f'<rect x="{bx}" y="300" width="450" height="112" rx="8" fill="#fdf6e6" stroke="#edd9a8"/>')
    s.append(txt(bx + 14, 324, "2.5ns 这个数从哪来？", 12, "#96660f", weight="650"))
    s.append(txt(bx + 14, 346, "时钟频率 400MHz → 周期 1/400M = 2.5ns", 11, "#3d4d5f", mono=True))
    s.append(txt(bx + 14, 368, "uncertainty 0.12 = 抖动 0.05 + 时钟树 skew 预算 0.05 + 余量 0.02", 10.5, "#3d4d5f"))
    s.append(txt(bx + 14, 390, "这两个数字必须和设计规格书核对，不能自己定。", 10.5, "#b3382f"))

    s.append(txt(40, H - 42, "写完之后必做：report_clocks（确认时钟定义对了）、check_timing（确认没有漏约束的端点）、", 11, "#6b7f99"))
    s.append(txt(40, H - 22, "report_clock_gating_check / report_min_pulse_width（这两个是「高级约束」，很多新人根本没写过）", 11, "#6b7f99"))
    add("sdc-anatomy", W, H, "SDC 的骨架。左边五条是最小可用集合（少一条都不行），右边是它们的真实写法与参数来源。记住一句：约束不是「写给人看的注释」，它是工具唯一的判断依据。",
        "".join(s))


# ---- 模块加载时把本文件里所有 fig_* 函数跑一遍，收集成 FIGS ----
for _n, _f in list(globals().items()):
    if _n.startswith("fig_") and callable(_f):
        _f()
