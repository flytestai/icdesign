# -*- coding: utf-8 -*-
"""概念示意类配图：标准单元、光刻、扫描链、ECO 链路。"""

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


# ================================================================ 标准单元
def fig_stdcell():
    W, H = 1120, 440
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "标准单元（standard cell）长什么样：一个「乐高积木」的横截面", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "后端 90% 的时间在和标准单元打交道。它高度固定（按行高，比如 8 个 track）、宽度按需、左右两端对齐，所以能像瓷砖一样拼成行。", 11.5, "#6b7f99"))

    # 单个单元放大
    cx, cy, cw, ch = 60, 80, 420, 190
    s.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" fill="#f3f8fe" stroke="#9dc4e8" stroke-width="1.5"/>')
    # 电源轨
    s.append(f'<rect x="{cx}" y="{cy + 2}" width="{cw}" height="12" fill="#e07a5f" opacity=".55"/>')
    s.append(txt(cx + cw - 8, cy + 12, "VDD rail（单元行顶）", 9.5, "#8b3a28", "end", mono=True))
    s.append(f'<rect x="{cx}" y="{cy + ch - 14}" width="{cw}" height="12" fill="#4d7fa8" opacity=".55"/>')
    s.append(txt(cx + cw - 8, cy + ch - 4, "VSS rail（单元行底）", 9.5, "#2b4a68", "end", mono=True))
    # 内部
    s.append(f'<rect x="{cx + 40}" y="{cy + 34}" width="150" height="120" rx="4" fill="#fff" stroke="#c9d5e2" stroke-dasharray="4 3"/>')
    s.append(txt(cx + 115, cy + 100, "单元内部：", 10.5, "#5b7089", "middle"))
    s.append(txt(cx + 115, cy + 118, "PMOS / NMOS 晶体管", 10.5, "#5b7089", "middle"))
    # 引脚
    for i, (nm, px) in enumerate([("A", cx + 22), ("B", cx + 230), ("Y", cx + 330)]):
        s.append(f'<rect x="{px}" y="{cy + 66 if nm != "Y" else cy + 96}" width="16" height="10" fill="#e8b45c"/>')
    s.append(f'<rect x="{cx - 10}" y="{cy + 66}" width="12" height="10" fill="#e8b45c"/>')
    s.append(txt(cx - 16, cy + 64, "A", 11, "#b4531a", "end", mono=True, weight="700"))
    s.append(txt(cx + 240, cy + 62, "B", 11, "#b4531a", mono=True, weight="700"))
    s.append(f'<rect x="{cx + cw - 4}" y="{cy + 96}" width="14" height="10" fill="#e8b45c"/>')
    s.append(txt(cx + cw + 14, cy + 104, "Y", 11, "#b4531a", mono=True, weight="700"))
    s.append(txt(cx + 200, cy + 176, "NAND2_X2：输入 A/B，输出 Y，驱动能力 ×2", 10.5, "#1d6fb8", "middle", mono=True))

    # 拼成行
    rx, ry = 60, 300
    s.append(txt(rx, ry - 8, "拼起来就是这样（同一行里的单元高度必须一致，宽度可以不等）", 11, "#5b7089"))
    xx = rx
    for name, w in [("INV_X1", 52), ("NAND2", 74), ("DFF", 108), ("BUF_X4", 62), ("AOI21", 88), ("MUX2", 96), ("DFF", 108)]:
        s.append(f'<rect x="{xx}" y="{ry + 8}" width="{w - 3}" height="66" fill="#fff" stroke="#9dc4e8"/>')
        s.append(f'<rect x="{xx}" y="{ry + 8}" width="{w - 3}" height="6" fill="#e07a5f" opacity=".5"/>')
        s.append(f'<rect x="{xx}" y="{ry + 68}" width="{w - 3}" height="6" fill="#4d7fa8" opacity=".5"/>')
        s.append(txt(xx + (w - 3) / 2, ry + 46, name, 8.5, "#3d4d5f", "middle", mono=True))
        xx += w

    # 右侧说明
    bx = 570
    s.append(f'<rect x="{bx}" y="80" width="510" height="152" rx="8" fill="#f3f8fe" stroke="#bcd7f0"/>')
    s.append(txt(bx + 14, 104, "为什么单元高度必须一样？", 12.5, "#1d6fb8", weight="650"))
    for i, ln in enumerate(["单元要一行行排（cell row），行高 = 单元高度。",
                            "行高按 track（布线轨道）算，nangate45 是 8 track ≈ 1.4µm。",
                            "高度不一致就排不齐，电源轨接不上，工具会直接报错。",
                            "所以库里的单元都只差「宽度」和「驱动能力」。"]):
        s.append(txt(bx + 16, 128 + i * 22, "· " + ln, 11, "#3d4d5f"))

    s.append(f'<rect x="{bx}" y="248" width="510" height="118" rx="8" fill="#fdf6e6" stroke="#edd9a8"/>')
    s.append(txt(bx + 14, 272, "三个必须记住的单元属性", 12.5, "#96660f", weight="650"))
    for i, (k, v) in enumerate([("驱动能力 X1/X2/X4", "越大越能带负载，但自己更耗电、占更宽"),
                                ("阈值电压 LVT/SVT/HVT", "LVT 快但漏电大，HVT 慢但省电"),
                                ("面积", "直接进利用率公式，也是换单元时唯一的「代价」")]):
        s.append(txt(bx + 16, 298 + i * 23, k, 10.5, "#1a2430", mono=True, weight="600"))
        s.append(txt(bx + 150, 298 + i * 23, v, 10.5, "#5b7089"))

    add("stdcell", W, H, "标准单元的结构。上方是一个单元放大后的样子：上下两条电源轨、左右两侧是引脚、中间是晶体管。下方是一排单元拼起来的样子——高度一致、宽度不同，这正是「乐高积木」的意思。",
        "".join(s))


# ================================================================ 扫描链
def fig_scan():
    W, H = 1120, 380
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 26, "DFT 的扫描链（scan chain）在后端意味着什么", 15, "#1a2430", weight="650"))
    s.append(txt(24, 46, "综合之后、布局之前，前端会把普通触发器换成「带扫描端口的触发器」，并把它们串成几条长链。后端要做的：让链上的走线别绕、别断。", 11.5, "#6b7f99"))

    # 正常功能路径
    y = 100
    s.append(txt(30, y - 10, "功能模式（function mode）", 11.5, "#1d6fb8", weight="650"))
    for i in range(5):
        x = 60 + i * 170
        s.append(f'<rect x="{x}" y="{y}" width="90" height="56" rx="5" fill="#eef7f1" stroke="#7cc4a4"/>')
        s.append(txt(x + 45, y + 24, f"FF{i}", 11, "#157a5b", "middle", mono=True, weight="700"))
        s.append(txt(x + 45, y + 42, "D → Q", 9.5, "#5b7089", "middle", mono=True))
        if i < 4:
            s.append(f'<path d="M {x + 90} {y + 28} L {x + 168} {y + 28}" stroke="#7e93a8" stroke-width="1.4" marker-end="url(#ah)"/>')
            s.append(txt(x + 128, y + 20, "逻辑", 9, "#93a4b8", "middle"))

    # 扫描链
    y2 = 220
    s.append(txt(30, y2 - 10, "扫描模式（scan mode）：所有 FF 串成一条链", 11.5, "#b4531a", weight="650"))
    for i in range(5):
        x = 60 + i * 170
        s.append(f'<rect x="{x}" y="{y2}" width="90" height="56" rx="5" fill="#fdf6e6" stroke="#edd9a8"/>')
        s.append(txt(x + 45, y2 + 24, f"FF{i}", 11, "#96660f", "middle", mono=True, weight="700"))
        s.append(txt(x + 45, y2 + 42, "SI → SO", 9.5, "#5b7089", "middle", mono=True))
        if i < 4:
            s.append(f'<path d="M {x + 90} {y2 + 28} L {x + 168} {y2 + 28}" stroke="#d9901e" stroke-width="1.8" marker-end="url(#ah)"/>')
    s.append(txt(60, y2 + 76, "scan_in（测试数据进）", 9.5, "#b4531a", mono=True))
    s.append(txt(60 + 4 * 170 + 92, y2 + 76, "scan_out（结果出）", 9.5, "#b4531a", mono=True))
    s.append(f'<path d="M 40 {y2 + 28} L 58 {y2 + 28}" stroke="#d9901e" stroke-width="1.8" marker-end="url(#ah)"/>')

    # 后端要点
    bx = 60
    s.append(f'<rect x="{bx}" y="308" width="1020" height="54" rx="8" fill="#f3f8fe" stroke="#bcd7f0"/>')
    s.append(txt(bx + 14, 328, "后端必须做的三件事：", 11.5, "#1d6fb8", weight="650"))
    s.append(txt(bx + 140, 328, "① place 之后做 scan chain reorder（把链按物理位置重排，避免绕远）", 11, "#3d4d5f"))
    s.append(txt(bx + 14, 350, "② 检查扫描链有没有被断掉（scan chain 断链 = 测试全过不了，但功能测试查不出来）  ③ 扫描模式下频率通常降一半，别忘了单独建一个 SDC 场景", 10.5, "#5b7089"))

    add("scan", W, H, "扫描链示意。上面是正常工作时触发器之间的逻辑路径；下面是测试模式下前端把它们串成的一条长链——测试机从这里灌数据、从末端读结果。后端要注意的是「重排」和「别断链」。",
        "".join(s))


# ---- 模块加载时把本文件里所有 fig_* 函数跑一遍，收集成 FIGS ----
for _n, _f in list(globals().items()):
    if _n.startswith("fig_") and callable(_f):
        _f()
