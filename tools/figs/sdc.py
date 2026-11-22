# -*- coding: utf-8 -*-
"""约束类配图：虚拟时钟、时钟门控检查、generated clock、多场景。"""

from figs.style import page, svgwrap

FIGS = []
FONT = '"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif'
MONO = '"Cascadia Mono",Consolas,monospace'


def add(fid, w, h, caption, body):
    FIGS.append((fid, w, h, page(svgwrap(w, h, body)), caption))


def txt(x, y, s, size=12, fill="#3d4d5f", anchor="start", mono=False, weight="400"):
    fam = MONO if mono else FONT
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x}" y="{y}" font-family={fam!r} font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


# ================================================================ 虚拟时钟
def fig_vclk():
    W, H = 1120, 420
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "虚拟时钟（virtual clock）：给「芯片外面那部分」也立个时间基准", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "问题：输入引脚的数据是外面的芯片送进来的，可外面的时钟并不在你的设计里。没有时钟，就没法定义输入延迟——所以造一个「虚拟」的。", 11.5, "#6b7f99"))

    # 外部芯片
    s.append(f'<rect x="40" y="96" width="240" height="120" rx="8" fill="#f7f9fc" stroke="#dbe4ee" stroke-dasharray="5 4"/>')
    s.append(txt(160, 122, "外部芯片（不在你的网表里）", 11, "#8a9cb2", "middle"))
    s.append(f'<rect x="70" y="136" width="80" height="52" rx="4" fill="#fff" stroke="#c9d5e2"/>')
    s.append(txt(110, 158, "FF", 11, "#5b7089", "middle", mono=True))
    s.append(txt(110, 176, "clk_ext", 9, "#8a9cb2", "middle", mono=True))
    s.append(f'<path d="M 150 162 L 232 162" stroke="#7e93a8" stroke-width="1.4" marker-end="url(#ah)"/>')
    s.append(txt(190, 154, "0.35ns", 9.5, "#b4531a", "middle", mono=True))

    # 你的芯片
    s.append(f'<rect x="320" y="96" width="360" height="190" rx="8" fill="#f3f8fe" stroke="#bcd7f0"/>')
    s.append(txt(500, 120, "你的设计 soc_top", 11.5, "#1d6fb8", "middle", weight="650"))
    s.append(f'<rect x="340" y="140" width="80" height="52" rx="4" fill="#fff" stroke="#9dc4e8"/>')
    s.append(txt(380, 162, "输入引脚", 10, "#1d6fb8", "middle"))
    s.append(txt(380, 178, "i_data[7:0]", 9, "#5b7089", "middle", mono=True))
    s.append(f'<rect x="470" y="140" width="86" height="52" rx="4" fill="#eef7f1" stroke="#7cc4a4"/>')
    s.append(txt(513, 162, "FF", 11, "#157a5b", "middle", mono=True))
    s.append(txt(513, 178, "clk", 9, "#5b7089", "middle", mono=True))
    s.append(f'<path d="M 420 166 L 466 166" stroke="#7e93a8" stroke-width="1.4" marker-end="url(#ah)"/>')
    s.append(txt(600, 220, "clk 2.5ns", 10, "#18a07a", mono=True))

    # 虚拟时钟
    s.append(f'<rect x="730" y="96" width="350" height="120" rx="8" fill="#fdf6e6" stroke="#edd9a8"/>')
    s.append(txt(746, 120, "虚拟时钟：只在约束里存在，不对应任何端口", 11.5, "#96660f", weight="650"))
    s.append(txt(746, 146, "create_clock -name vclk -period 2.5", 10.5, "#3d4d5f", mono=True))
    s.append(txt(746, 168, "set_input_delay -clock vclk 0.35 [get_ports i_data*]", 10.5, "#3d4d5f", mono=True))
    s.append(txt(746, 190, "→ 工具据此算出：i_data 必须在 2.5−0.35 之前稳定", 10.5, "#b3382f"))

    s.append(f'<rect x="730" y="230" width="350" height="120" rx="8" fill="#f3f8fe" stroke="#bcd7f0"/>')
    s.append(txt(746, 254, "为什么不能直接写 0？", 11.5, "#1d6fb8", weight="650"))
    s.append(txt(746, 278, "写 0 等于假设「外面的数据在时钟沿那一刻才到」，", 10.5, "#3d4d5f"))
    s.append(txt(746, 298, "这是不可能的，会算出一堆假违例；写太小又漏掉真违例。", 10.5, "#3d4d5f"))
    s.append(txt(746, 322, "0.35 这个数必须来自对接方给的接口时序表。", 10.5, "#b3382f", weight="600"))

    s.append(txt(40, 330, "同理还有 output delay：", 11, "#3d4d5f", weight="650"))
    s.append(txt(40, 352, "set_output_delay -clock vclk 0.45 [get_ports o_data*]", 10.5, "#3d4d5f", mono=True))
    s.append(txt(40, 374, "含义：下一级要求数据在时钟沿前 0.45ns 到达它的输入 —— 你的输出必须比这更早。", 10.5, "#6b7f99"))
    add("sdc-virtual-clock", W, H, "虚拟时钟的用途。左边是外面那颗芯片，中间是你的设计，右边是「只在约束文件里存在」的虚拟时钟。没有它，输入/输出延迟就没有参照系，工具只能瞎算。",
        "".join(s))


# ================================================================ 时钟门控检查
def fig_cgc():
    W, H = 1120, 400
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "时钟门控检查（clock gating check）：省电的电路，也最容易出时序问题", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "时钟门控单元（ICG）用一个使能信号去「开关」时钟。使能信号必须在时钟为低电平时变化，否则会切出一个窄脉冲，把触发器打乱。", 11.5, "#6b7f99"))

    # 电路
    s.append(f'<rect x="60" y="110" width="120" height="60" rx="6" fill="#eef7f1" stroke="#7cc4a4"/>')
    s.append(txt(120, 134, "ICG", 12, "#157a5b", "middle", mono=True, weight="700"))
    s.append(txt(120, 154, "时钟门控单元", 9.5, "#5b7089", "middle"))
    s.append(f'<path d="M 20 140 L 58 140" stroke="#18a07a" stroke-width="1.8" marker-end="url(#ah)"/>')
    s.append(txt(24, 132, "clk", 10, "#18a07a", mono=True))
    s.append(f'<path d="M 180 140 L 260 140" stroke="#18a07a" stroke-width="1.8" marker-end="url(#ah)"/>')
    s.append(txt(200, 132, "gated_clk", 10, "#18a07a", mono=True))
    # 使能
    s.append(f'<rect x="60" y="210" width="120" height="44" rx="6" fill="#f3f8fe" stroke="#9dc4e8"/>')
    s.append(txt(120, 238, "使能逻辑", 11, "#1d6fb8", "middle"))
    s.append(f'<path d="M 120 210 L 120 172" stroke="#2f7fd0" stroke-width="1.4" marker-end="url(#ah)"/>')
    s.append(txt(126, 196, "EN", 10, "#2f7fd0", mono=True))
    s.append(f'<path d="M 20 232 L 58 232" stroke="#2f7fd0" stroke-width="1.4" marker-end="url(#ah)"/>')
    s.append(txt(24, 224, "sel", 10, "#2f7fd0", mono=True))

    # 正确/错误波形（简化）
    def wv(x0, y0, name, segs, col, title):
        out = [txt(x0, y0 - 8, title, 10.5, col, weight="600")]
        out.append(txt(x0 - 8, y0 + 16, name, 9.5, "#5b7089", "end", mono=True))
        d = []
        for k, a, b in segs:
            ya = y0 + 6 if k == "hi" else y0 + 26
            d.append(f"M {x0 + a} {ya} L {x0 + b} {ya}")
        for i in range(len(segs) - 1):
            ya = y0 + 6 if segs[i][0] == "hi" else y0 + 26
            yb = y0 + 6 if segs[i + 1][0] == "hi" else y0 + 26
            if ya != yb:
                d.append(f"M {x0 + segs[i][2]} {ya} L {x0 + segs[i][2]} {yb}")
        out.append(f'<path d="{" ".join(d)}" fill="none" stroke="{col}" stroke-width="1.7"/>')
        return "".join(out)

    s.append(wv(300, 110, "clk", [("lo", 0, 20), ("hi", 20, 50), ("lo", 50, 70), ("hi", 70, 100), ("lo", 100, 130)], "#18a07a", "① 时钟"))
    s.append(wv(300, 170, "EN", [("hi", 0, 34), ("lo", 34, 46), ("hi", 46, 130)], "#2f7fd0", "② 使能在时钟低电平期间变化 → 合格"))
    s.append(wv(300, 230, "gated", [("lo", 0, 20), ("hi", 20, 45), ("lo", 45, 70), ("hi", 70, 100), ("lo", 100, 130)], "#7a5cd6", "③ 输出时钟完整"))

    s.append(wv(300, 300, "EN", [("hi", 0, 34), ("lo", 34, 38), ("hi", 38, 130)], "#d9534f", "④ 使能在时钟高电平中间掉下去 → 切出窄脉冲 → 违例"))

    s.append(f'<rect x="470" y="96" width="610" height="240" rx="8" fill="#f3f8fe" stroke="#bcd7f0"/>')
    s.append(txt(486, 120, "怎么让工具替你查这个？", 12.5, "#1d6fb8", weight="650"))
    s.append(txt(486, 146, "set_clock_gating_check -setup 0.05 -hold 0.02", 10.5, "#3d4d5f", mono=True))
    s.append(txt(486, 168, "report_clock_gating_check", 10.5, "#3d4d5f", mono=True))
    s.append(txt(486, 194, "没写这两条会怎样：工具默认按普通路径查，不查「使能 vs 门控时钟」的", 10.5, "#3d4d5f"))
    s.append(txt(486, 214, "相对关系，于是这类违例在签核报告里根本不出现，到硅片上才炸。", 10.5, "#3d4d5f"))
    s.append(txt(486, 242, "经验：ICG 的使能路径通常是「逻辑级数最多的那条」，", 10.5, "#b3382f"))
    s.append(txt(486, 262, "所以 setup 违例常常先出在门控使能上，而不是数据路径上。", 10.5, "#b3382f"))
    s.append(txt(486, 292, "修法：把 EN 逻辑做浅、或在 EN 前面插一级寄存器（打一拍），", 10.5, "#157a5b"))
    s.append(txt(486, 312, "代价是多一个周期的使能延迟（功能上必须允许）。", 10.5, "#157a5b"))

    add("sdc-cgc", W, H, "时钟门控检查。门控单元像水龙头，使能信号必须在「水关着」的时候去拧；如果在流水的时候拧，会切出半截脉冲。下面第四行波形就是错误情况，而 SDC 不写 set_clock_gating_check，工具不会替你查。",
        "".join(s))


# ---- 模块加载时把本文件里所有 fig_* 函数跑一遍，收集成 FIGS ----
for _n, _f in list(globals().items()):
    if _n.startswith("fig_") and callable(_f):
        _f()
