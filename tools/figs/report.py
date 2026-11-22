# -*- coding: utf-8 -*-
"""报告解读类配图：把 report_timing / 面积 / 时序汇总的每一列标出来。"""

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


# ================================================================ report_timing 逐列
def fig_rt():
    W, H = 1120, 620
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "report_timing 逐行读：每一行在说什么", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "这张报告是后端工程师看得最多的东西。看不懂它，就只能靠同事帮你 debug；看懂它，你自己就能判断「该修还是该 waive」。", 11.5, "#6b7f99"))

    # 报告框
    rx, ry, rw = 30, 70, 620
    s.append(f'<rect x="{rx}" y="{ry}" width="{rw}" height="500" rx="6" fill="#fff" stroke="#dfe6ee"/>')
    s.append(f'<rect x="{rx}" y="{ry}" width="{rw}" height="26" fill="#eef3f9"/>')
    s.append(txt(rx + 10, ry + 18, "pt_shell> report_timing -max_paths 1 -delay_type max", 10.5, "#42566b", mono=True))

    lines = [
        ("Startpoint:   u_cpu/reg_bank/q_reg[3]/CK", "#1a2430", 700),
        ("              (rising edge-triggered flip-flop clocked by clk)", "#7b8ea3", 400),
        ("Endpoint:     u_dsp/mac_pipe/mult_reg[11]/D", "#1a2430", 700),
        ("Path Group:   clk", "#1a2430", 600),
        ("Path Type:    max", "#1a2430", 600),
        ("", "#000", 400),
        ("  Point                                Incr     Path", "#7b8ea3", 700),
        ("  ----------------------------------------------------", "#c9d5e2", 400),
        ("  clock clk (rise edge)              0.0000   0.0000", "#6b7f99", 400),
        ("  clock network delay (ideal)        0.0000   0.0000", "#6b7f99", 400),
        ("  u_cpu/reg_bank/q_reg[3]/CK         0.0000   0.0000 r", "#3d4d5f", 400),
        ("  u_cpu/reg_bank/q_reg[3]/Q          0.0912   0.0912 f", "#1d6fb8", 400),
        ("  u_dsp/mac_pipe/U2214/Z             0.1843   0.2755 r", "#3d4d5f", 400),
        ("  u_dsp/mac_pipe/U1877/Z             0.2211   0.4966 f", "#3d4d5f", 400),
        ("  u_dsp/mac_pipe/U903/Z              0.2087   0.7053 r", "#3d4d5f", 400),
        ("  u_dsp/mac_pipe/mult_reg[11]/D      0.0031   0.7084 r", "#1d6fb8", 400),
        ("  data arrival time                           0.7084", "#b4531a", 700),
        ("", "#000", 400),
        ("  clock clk (rise edge)              2.5000   2.5000", "#6b7f99", 400),
        ("  clock uncertainty                 -0.1200   2.3800", "#d9901e", 400),
        ("  u_dsp/.../mult_reg[11]/CK          0.0000   2.3800 r", "#3d4d5f", 400),
        ("  library setup time                -0.0683   2.3117", "#d9901e", 400),
        ("  data required time                          2.3117", "#157a5b", 700),
        ("  ----------------------------------------------------", "#c9d5e2", 400),
        ("  slack (MET)                                 1.6033", "#157a5b", 700),
    ]
    y = ry + 46
    for t, col, wt in lines:
        s.append(txt(rx + 12, y, t, 10.5, col, mono=True, weight=str(wt)))
        y += 17.6

    # 右侧标注
    bx = 680
    notes = [("Startpoint / Endpoint", "这条路径从哪个触发器出发、到哪个触发器结束。先看这两个名字，判断它属于哪个模块。", "#2f7fd0"),
             ("Path Group / Path Type", "路径组（按时钟分）+ 检查类型（max=setup，min=hold）。switching 时报错多半是这两个参数写错了。", "#2f7fd0"),
             ("Incr 列", "这一级「自己」花了多少延迟。数字突然变大（比如 0.22 而邻居只有 0.05）就是嫌疑点。", "#d9901e"),
             ("Path 列", "从起点累加到这一级的累计延迟。最后一行就是 arrival time。", "#d9901e"),
             ("data arrival time", "数据实际到达的时间 = Tcq + 所有逻辑延迟。", "#b4532a"),
             ("clock uncertainty", "抖动 + 余量。这一行是「人为留的安全边际」，不是真实物理量。", "#d9901e"),
             ("library setup time", "终点触发器要求数据提前稳定多久（查表得来，与 transition 有关）。", "#d9901e"),
             ("data required time", "数据最晚必须到的时间。required 永远小于一个周期。", "#157a5b"),
             ("slack (MET)", "slack = required − arrival。MET = 通过；VIOLATED 就是违例，数值是负的缺口。", "#b3382f")]
    yy = 84
    for t, d, col in notes:
        s.append(f'<circle cx="{bx + 5}" cy="{yy - 4}" r="4" fill="{col}"/>')
        s.append(txt(bx + 18, yy, t, 11.5, "#1a2430", weight="650"))
        # 折行 30 字
        line, lines2 = "", []
        for ch in d:
            line += ch
            if len(line) >= 26:
                lines2.append(line); line = ""
        if line:
            lines2.append(line)
        for i, ln in enumerate(lines2[:3]):
            s.append(txt(bx + 18, yy + 16 + i * 14.5, ln, 10, "#6b7f99"))
        yy += 20 + 14.5 * min(len(lines2), 3) + 12

    add("report-timing-annotated", W, H, "report_timing 的输出逐行注解。左边是真实格式的报告（列宽、箭头、缩进都照原样），右边把每一段在说什么写清楚。建议对照自己跑出来的报告一起看。",
        "".join(s))


# ================================================================ 时序汇总
def fig_summary():
    W, H = 1120, 420
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "timeDesign 汇总：三个数字决定下一步做什么", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "跑完一轮优化，别看几十条报告，先看这三行：WNS、TNS、违例条数。它们分别回答「最差多差」「一共差多少」「有几条」。", 11.5, "#6b7f99"))

    # 表
    rx, ry = 30, 74
    cols = [("#", 40), ("Setup (max)", 190), ("Hold (min)", 190), ("说明", 320)]
    s.append(f'<rect x="{rx}" y="{ry}" width="740" height="26" fill="#eef3f9"/>')
    x = rx
    for name, w in cols:
        s.append(txt(x + 10, ry + 18, name, 11, "#42566b", weight="600"))
        x += w
    rows = [("WNS", "-0.412 ns", "+0.031 ns", "最差那一条路径差多少（worst negative slack）", "#b3382f"),
            ("TNS", "-18.63 ns", "0.000 ns", "所有违例路径的缺口之和（total negative slack）", "#b3382f"),
            ("条数", "37", "2", "违例路径总条数", "#b3382f"),
            ("通过线", "WNS ≥ 0", "WNS ≥ 0", "签核要求：三条全部归零才算过", "#157a5b")]
    y = ry + 26
    for r in rows:
        s.append(f'<rect x="{rx}" y="{y}" width="740" height="30" fill="#fff" stroke="#eef2f7"/>')
        x = rx
        for i, cell in enumerate(r[:4]):
            col = r[4] if i > 0 else "#1a2430"
            s.append(txt(x + 10, y + 19, cell, 10.5, col, mono=(i in (1, 2)), weight="600" if i == 0 else "400"))
            x += cols[i][1]
        y += 30

    # 判断流程
    bx = 30
    by = 250
    s.append(txt(bx, by, "看到这三个数字之后的动作（按顺序）", 12.5, "#1d6fb8", weight="650"))
    steps = [("WNS 很大但条数很少", "通常是单点问题：某条路径绕太远 / 逻辑级数太多 → 查具体路径"),
             ("TNS 大、条数多", "系统性问题：时钟树没做好 / 约束太紧 / 布局质量差 → 先查 CTS 与 floorplan"),
             ("hold 违例", "先修 hold（它会让 setup 变好或不变），但要注意别破坏已经修好的 setup"),
             ("两个都有", "标准顺序：DRV → setup → hold → 复算。每轮只改一类，改完必须复算")]
    yy = by + 22
    for t, d in steps:
        s.append(f'<rect x="{bx}" y="{yy}" width="740" height="30" rx="4" fill="#f7fafd" stroke="#e3e9f0"/>')
        s.append(txt(bx + 10, yy + 19, t, 11, "#1a2430", weight="650"))
        s.append(txt(bx + 210, yy + 19, d, 10.5, "#5b7089"))
        yy += 36

    add("timing-summary", W, H, "时序汇总表的读法。这三个数字（WNS / TNS / 条数）是「体检报告的第一页」，先看它们决定往哪个方向查，再去看具体路径。下半部分是按现象分流的处理顺序。",
        "".join(s))


# ---- 模块加载时把本文件里所有 fig_* 函数跑一遍，收集成 FIGS ----
for _n, _f in list(globals().items()):
    if _n.startswith("fig_") and callable(_f):
        _f()
