# -*- coding: utf-8 -*-
"""波形类配图：setup / hold / skew / 脉宽。用 SVG 画，格子对齐时间轴。"""

from figs.style import page, svgwrap, DEFS

FIGS = []
FONT = '"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif'
MONO = '"Cascadia Mono",Consolas,monospace'


def add(fid, w, h, caption, body):
    FIGS.append((fid, w, h, page(svgwrap(w, h, body)), caption))


def wave_svg(w, h, rows, t0=60, tw=880, grid=40, labels=None, marks=None, note=None, foot=None):
    """rows: [(name, [(kind, x_ns_from, x_ns_to)])] kind in hi/lo/x/z
    grid: 每 ns 的像素宽度
    """
    s = [f'<rect width="{w}" height="{h}" fill="#fff"/>']
    # 时间轴
    n = int(tw / grid)
    for i in range(n + 1):
        x = t0 + i * grid
        s.append(f'<line x1="{x}" y1="56" x2="{x}" y2="{h - 60}" stroke="#eef2f7" stroke-width="1"/>')
        s.append(f'<text x="{x}" y="{h - 42}" font-family={MONO!r} font-size="10" fill="#93a4b8" '
                 f'text-anchor="middle">{i}</text>')
    s.append(f'<text x="{t0 + tw + 8}" y="{h - 42}" font-family={MONO!r} font-size="10" fill="#93a4b8">ns</text>')

    y = 70
    for name, segs, *rest in rows:
        col = rest[0] if rest else "#1d6fb8"
        s.append(f'<text x="{t0 - 12}" y="{y + 22}" font-family={MONO!r} font-size="11" fill="#3d4d5f" text-anchor="end">{name}</text>')
        s.append(f'<line x1="{t0}" y1="{y + 30}" x2="{t0 + tw}" y2="{y + 30}" stroke="#dfe6ee" stroke-dasharray="2 3"/>')
        px = None
        segpath = []
        for kind, a, b in segs:
            x1, x2 = t0 + a * grid, t0 + b * grid
            if kind == "hi":
                segpath.append(f"M {x1} {y + 6} L {x2} {y + 6}")
            elif kind == "lo":
                segpath.append(f"M {x1} {y + 30} L {x2} {y + 30}")
            elif kind == "x":
                segpath.append(f"M {x1} {y + 12} L {x2} {y + 24} M {x1} {y + 24} L {x2} {y + 12}")
        # 连接相邻段的竖直边
        for i in range(len(segs) - 1):
            k1, a1, b1 = segs[i]
            k2, a2, b2 = segs[i + 1]
            y1 = y + 6 if k1 == "hi" else (y + 30 if k1 == "lo" else y + 18)
            y2 = y + 6 if k2 == "hi" else (y + 30 if k2 == "lo" else y + 18)
            if y1 != y2:
                segpath.append(f"M {t0 + b1 * grid} {y1} L {t0 + b1 * grid} {y2}")
        s.append(f'<path d="{" ".join(segpath)}" fill="none" stroke="{col}" stroke-width="1.8" stroke-linejoin="round"/>')
        y += 62

    if marks:
        for mx, mk, mlabel, mcol in marks:
            x = t0 + mx * grid
            s.append(f'<line x1="{x}" y1="52" x2="{x}" y2="{h - 62}" stroke="{mcol}" stroke-width="1.2" '
                     f'stroke-dasharray="{mk}"/>')
            s.append(f'<text x="{x + 4}" y="48" font-family={FONT!r} font-size="10.5" fill="{mcol}" '
                     f'font-weight="600">{mlabel}</text>')

    if note:
        s.append(f'<rect x="{t0}" y="{h - 34}" width="{tw}" height="24" rx="5" fill="#f7fafd" stroke="#e3e9f0"/>')
        s.append(f'<text x="{t0 + 10}" y="{h - 18}" font-family={FONT!r} font-size="11" fill="#3d4d5f">{note}</text>')
    if foot:
        s.extend(foot)
    return "".join(s)


# ================================================================ setup
def fig_setup():
    W, H = 1120, 400
    rows = [("clk", [("lo", 0, 2), ("hi", 2, 3), ("lo", 3, 5), ("hi", 5, 6), ("lo", 6, 10)], "#18a07a"),
            ("D（数据）", [("lo", 0, 2.6), ("hi", 2.6, 5.4), ("lo", 5.4, 10)], "#1d6fb8"),
            ("D 最晚到达", [("lo", 0, 4.3), ("hi", 4.3, 5.4), ("lo", 5.4, 10)], "#d9901e")]
    marks = [(5, "3 2", "捕获沿（要求数据此时已稳定）", "#18a07a"),
             (4.3, "4 3", "数据最晚允许变化 ← setup 违例从这里开始", "#d9534f")]
    foot = [f'<text x="30" y="{H - 8}" font-family={FONT!r} font-size="11" fill="#6b7f99">'
            f'setup 窗口 = 时钟沿之前的这段时间（图中 4.3→5.0ns，0.7ns 就是 Tsetup + Tuncertainty）</text>']
    body = wave_svg(W, H, rows, t0=110, tw=880, grid=88, marks=marks, foot=foot,
                    note="D 在 4.3ns 之后还在变 → 到 5ns 时钟沿时数据还没稳定 → setup 违例（数据来得太晚）")
    add("wave-setup", W, H, "setup 违例的波形。绿色是时钟，蓝色是数据，橙色是「数据最晚还允许变化」的时刻。数据在橙色线之后仍在翻转，就意味着到时钟沿那一刻还没稳定，这就是 setup 违例。",
        body)


# ================================================================ hold
def fig_hold():
    W, H = 1120, 400
    rows = [("clk", [("lo", 0, 2), ("hi", 2, 3), ("lo", 3, 5), ("hi", 5, 6), ("lo", 6, 10)], "#18a07a"),
            ("D（应该晚到）", [("lo", 0, 2.5), ("hi", 2.5, 5.2), ("lo", 5.2, 10)], "#1d6fb8"),
            ("D（实际太早）", [("lo", 0, 1.2), ("hi", 1.2, 3.6), ("lo", 3.6, 5.2), ("hi", 5.2, 10)], "#d9534f")]
    marks = [(2, "3 2", "同一个时钟沿：数据在这里被采样", "#18a07a"),
             (1.2, "4 3", "数据太早翻到这里 → 冲掉了上一个值", "#d9534f")]
    foot = [f'<text x="30" y="{H - 8}" font-family={FONT!r} font-size="11" fill="#6b7f99">'
            f'hold 窗口 = 时钟沿之后的一小段（图中 2.0→2.2ns）：这段时间数据必须纹丝不动</text>']
    body = wave_svg(W, H, rows, t0=120, tw=880, grid=88, marks=marks, foot=foot,
                    note="同一个时钟沿，数据必须「保持」住 Thold 的时间不变；红波形在 1.2ns 就翻了，把上一拍的数据冲掉 → hold 违例")
    add("wave-hold", W, H, "hold 违例的波形。注意蓝线是「本来应该」的样子，红线是「实际发生」的样子：数据在时钟沿之前就提前翻转，把上一级要采的值冲掉了。hold 违例和时钟快慢无关，所以降频救不了。",
        body)


# ================================================================ skew
def fig_skew():
    W, H = 1120, 460
    rows = [("clk @ 源（root）", [("lo", 0, 1), ("hi", 1, 2), ("lo", 2, 4), ("hi", 4, 5), ("lo", 5, 9)], "#18a07a"),
            ("clk @ 触发器 A（早到）", [("lo", 0, 0.6), ("hi", 0.6, 1.6), ("lo", 1.6, 3.6), ("hi", 3.6, 4.6), ("lo", 4.6, 9)], "#18a07a"),
            ("clk @ 触发器 B（晚到）", [("lo", 0, 1.5), ("hi", 1.5, 2.5), ("lo", 2.5, 4.5), ("hi", 4.5, 5.5), ("lo", 5.5, 9)], "#d9901e"),
            ("数据 A→B", [("lo", 0, 1.9), ("hi", 1.9, 4.2), ("lo", 4.2, 9)], "#1d6fb8")]
    marks = [(0.6, "3 2", "A 收到时钟", "#18a07a"), (1.5, "4 3", "B 收到时钟（晚 0.9ns）", "#d9901e")]
    foot = [f'<text x="24" y="{H - 34}" font-family={FONT!r} font-size="11.5" fill="#3d4d5f" font-weight="600">'
            f'skew（时钟偏斜）：同一个时钟送到不同触发器的时间差。正值（捕获端晚）帮 setup、伤 hold；负值反过来。</text>',
            f'<text x="24" y="{H - 14}" font-family={FONT!r} font-size="11.5" fill="#6b7f99">'
            f'工程上把 skew 控制在周期的 5% 左右：2.5ns 周期 → ±125ps 以内，既可以接受，也不至于让时钟树太费电。</text>']
    body = wave_svg(W, H, rows, t0=170, tw=820, grid=91, marks=marks, foot=foot,
                    note="skew = B 的时钟沿 − A 的时钟沿 = 1.5 − 0.6 = +0.9ns（B 晚），这条路径的可用时间因此多了 0.9ns")
    add("wave-skew", W, H, "skew 的形成。同一个时钟源，因为走线长短不同，到达两个触发器的时间不一样。图中 B 比 A 晚 0.9ns，这 0.9ns 就是 skew——它既不完全是好事也不完全是坏事，取决于哪一端晚。",
        body)


# ================================================================ 脉宽
def fig_pulse():
    W, H = 1120, 330
    rows = [("clk（正常）", [("lo", 0, 1), ("hi", 1, 2), ("lo", 2, 3), ("hi", 3, 4), ("lo", 4, 8)], "#18a07a"),
            ("clk（高电平被削）", [("lo", 0, 1), ("hi", 1, 1.35), ("lo", 1.35, 3), ("hi", 3, 3.4), ("lo", 3.4, 8)], "#d9534f")]
    marks = [(1, "3 2", "上升沿", "#18a07a"), (2, "4 3", "下降沿：宽度 1.0ns 合格", "#18a07a"),
             (1.35, "2 3", "只宽 0.35ns < 最小脉宽 → 触发器可能采不到", "#d9534f")]
    foot = [f'<text x="24" y="{H - 12}" font-family={FONT!r} font-size="11" fill="#6b7f99">'
            f'时钟树上过多 buffer、或 clock gating 单元选得太弱，都会把脉宽吃掉。</text>']
    body = wave_svg(W, H, rows, t0=140, tw=800, grid=100, marks=marks, foot=foot,
                    note="set_min_pulse_width 0.45 → 高/低电平宽度都不得小于 0.45ns，否则触发器内部锁不住数据")
    add("wave-pulse", W, H, "最小脉宽（min pulse width）检查。时钟经过太多缓冲器后，高电平会被「削窄」；窄到触发器锁不住时，芯片会随机出错——这类问题在仿真里几乎看不出来，只能靠 STA 的脉宽检查拦住。",
        body)


# ---- 模块加载时把本文件里所有 fig_* 函数跑一遍，收集成 FIGS ----
for _n, _f in list(globals().items()):
    if _n.startswith("fig_") and callable(_f):
        _f()
