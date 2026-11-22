# -*- coding: utf-8 -*-
"""可复用的界面/版图零件：拼装出一张图，而不是手写坐标。"""


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- 窗口外壳
def menu(items, active="Design"):
    out = []
    for it in items:
        cls = ' class="on"' if it == active else ""
        out.append(f"<span{cls}>{esc(it)}</span>")
    return '<div class="menu">' + "".join(out) + "</div>"


def tbar(n=8, hot=(3, 6)):
    cells = []
    for i in range(n):
        cells.append(f'<i class="{"hot" if i in hot else ""}"></i>')
        if i in (2, 5):
            cells.append('<div class="div"></div>')
    return '<div class="tbar">' + "".join(cells) + "</div>"


def tree(items):
    """items: [(level, label, sel)] level 0/1/2"""
    out = []
    for lv, label, sel in items:
        cls = "sel" if sel else ("l2" if lv == 2 else ("l3" if lv >= 3 else ""))
        out.append(f'<div class="{cls}">{label}</div>')
    return '<div class="tree">' + "".join(out) + "</div>"


def side(title, body, w=196):
    return (f'<div class="side" style="width:{w}px"><div class="side-h">{esc(title)}</div>{body}</div>')


def canvas(body, label="", right="", w=None, h=None, light=False):
    style = ""
    if w:
        style += f"width:{w}px;"
    if h:
        style += f"height:{h}px;"
    cls = "canvas light" if light else "canvas"
    head = ""
    if label or right:
        head = f'<div class="cv-h"><b>{label}</b><span class="r">{right}</span></div>'
    return f'<div class="{cls}" style="{style}">{head}{body}</div>'


def cons(lines, h=118):
    return f'<div class="cons" style="height:{h}px">' + "".join(lines) + "</div>"


def ps(cmd, out="", kind="o"):
    return (f'<div><span class="ps">innovus&gt;</span> <span class="cmd">{esc(cmd)}</span></div>'
            + (f'<div class="{kind}">{esc(out)}</div>' if out else ""))


def status(items):
    return '<div class="status">' + "".join(f"<span>{esc(i)}</span>" for i in items) + "</div>"


def window(title, inner, w=1000, h=620, sub=""):
    return f"""<div class="win" style="width:{w}px;height:{h}px">
  <div class="win-tb"><div class="dots"><i></i><i></i><i></i></div><b>{esc(title)}</b>
    <span class="sp">{esc(sub)}</span></div>
  {inner}
</div>"""


# ---------------------------------------------------------------- 版图零件
def die(inner, x, y, w, h, label="", dtype="core"):
    border = "1.5px solid #4d7fa8" if dtype == "core" else "1.5px solid #d9a441"
    lab = (f'<span style="position:absolute;left:5px;top:3px;color:#8fb6d4;font:9.5px Consolas">{label}</span>'
           if label else "")
    return (f'<div class="die" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;border:{border}">'
            f'{lab}{inner}</div>')


def macro(name, x, y, w, h, pins=None, color=None, pin_side="bottom"):
    bg = f"background:{color};" if color else ""
    p = f'<div class="macro" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;{bg}"><span>{esc(name)}</span>'
    if pins:
        n = pins
        step = w / (n + 1)
        for i in range(n):
            left = step * (i + 1) - 1
            top = h - 4 if pin_side == "bottom" else -2
            p += f'<div class="pin" style="left:{left:.1f}px;top:{top}px;width:2px;height:4px"></div>'
    p += "</div>"
    return p


def stripes(vertical, count, area, width=3, color=None, gap=None):
    """在 area=(x,y,w,h) 内画等间距电源条带"""
    x, y, w, h = area
    out = []
    cls = "pgv" if vertical else "pg"
    if vertical:
        gap = gap or w / (count + 1)
        for i in range(count):
            out.append(f'<div class="{cls}" style="left:{x + gap * (i + 1):.1f}px;top:{y}px;width:{width}px;height:{h}px"></div>')
    else:
        gap = gap or h / (count + 1)
        for i in range(count):
            out.append(f'<div class="{cls}" style="left:{x}px;top:{y + gap * (i + 1):.1f}px;width:{w}px;height:{width}px"></div>')
    return "".join(out)


def ring(x, y, w, h, t=5):
    """电源环：四条边"""
    c = "background:rgba(214,120,80,.6)"
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{t}px;{c}"></div>'
            f'<div style="position:absolute;left:{x}px;top:{y + h - t}px;width:{w}px;height:{t}px;{c}"></div>'
            f'<div style="position:absolute;left:{x}px;top:{y}px;width:{t}px;height:{h}px;{c}"></div>'
            f'<div style="position:absolute;left:{x + w - t}px;top:{y}px;width:{t}px;height:{h}px;{c}"></div>')


def rows(x, y, w, h, pitch=7):
    out = []
    n = int(h // pitch)
    for i in range(n):
        out.append(f'<div class="row" style="left:{x}px;top:{y + i * pitch}px;width:{w}px;height:{pitch - 1}px"></div>')
    return "".join(out)


def cells_grid(x, y, w, h, pitch=7, seed=7, hot=(), warm=()):
    """画标准单元行里的小方块（随机但可复现）"""
    out = []
    nrow = int(h // pitch)
    px = 3
    idx = 0
    s = seed
    for r in range(nrow):
        cx = x + 1
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        while cx < x + w - 3:
            s = (s * 1103515245 + 12345) & 0x7FFFFFFF
            cw = 2 + (s % 4)
            cls = "cell"
            if idx in hot:
                cls = "cell hot"
            elif idx in warm:
                cls = "cell warm"
            out.append(f'<div class="{cls}" style="left:{cx}px;top:{y + r * pitch + 1}px;width:{cw}px;height:{pitch - 2}px"></div>')
            cx += cw + 1
            idx += 1
    return "".join(out)


def label(text, x, y, color="#9fb4c9", size=10, mono=True, weight="400", anchor="left"):
    fam = 'Consolas,monospace' if mono else '"Segoe UI",sans-serif'
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;color:{color};font:{weight} {size}px/1.3 {fam};'
            f'white-space:nowrap">{esc(text)}</div>')


def callout(text, x, y, w=180, tone="b"):
    colors = {"b": ("#eaf4fd", "#b7d6f0", "#1d6fb8"),
              "g": ("#eaf8f2", "#b6e0d0", "#157a5b"),
              "y": ("#fdf6e6", "#edd9a8", "#96660f"),
              "r": ("#fdeeec", "#efc5c1", "#b3382f")}
    bg, bd, fg = colors[tone]
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;background:{bg};border:1px solid {bd};'
            f'border-radius:5px;color:{fg};font-size:10.5px;line-height:1.45;padding:4px 6px">{text}</div>')
