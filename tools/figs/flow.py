# -*- coding: utf-8 -*-
"""结构/流程类配图：用内嵌 SVG 画，随窗口缩放不失真。

这些图解决的是「看不见的东西」：电怎么流、数据怎么从一个触发器走到下一个、
一个项目的时间花在哪。文字全部是中文，英文缩写都在图里给了对照。
"""

from figs.style import page

FIGS = []


def add(fid, w, h, caption, body, extra=""):
    FIGS.append((fid, w, h, page(body, extra), caption))


FONT = '"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif'
MONO = '"Cascadia Mono",Consolas,monospace'


def svg(w, h, inner, bg="#ffffff"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'style="display:block;background:{bg}">{inner}</svg>')


def box(x, y, w, h, title, sub="", fill="#f3f8fe", stroke="#9dc4e8", ink="#1a2430", r=7, fs=13):
    t = (f'<text x="{x + w / 2}" y="{y + (h / 2 - 2 if sub else h / 2 + 4)}" text-anchor="middle" '
         f'font-family={FONT!r} font-size="{fs}" font-weight="600" fill="{ink}">{title}</text>')
    s = ""
    if sub:
        s = (f'<text x="{x + w / 2}" y="{y + h / 2 + 15}" text-anchor="middle" font-family={FONT!r} '
             f'font-size="{fs - 2.5}" fill="#5b7089">{sub}</text>')
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>'
            + t + s)


def arrow(x1, y1, x2, y2, color="#7e93a8", dash="", w=1.4, head=True):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = ' marker-end="url(#ah)"' if head else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}"{d}{m}/>'


def path(d, color="#7e93a8", dash="", w=1.4, head=True):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    m = ' marker-end="url(#ah)"' if head else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}"{da}{m}/>'


def txt(x, y, s, size=12, fill="#3d4d5f", anchor="start", mono=False, weight="400"):
    fam = MONO if mono else FONT
    return (f'<text x="{x}" y="{y}" font-family={fam!r} font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


DEFS = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#7e93a8"/></marker>'
        '<marker id="ahr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#d9534f"/></marker></defs>')


# ================================================================ 全景流程
def fig_overview():
    W, H = 1120, 470
    s = [DEFS, f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(28, 30, "一个芯片从代码到版图：9 个阶段，你在哪一段", 16, "#1a2430", weight="650"))
    s.append(txt(28, 50, "左半边是「前端」（写代码、验证功能），右半边是「后端」（把电路摆到硅片上）。本课程只讲右半边，但你得知道左边交过来的是什么。",
                 11.5, "#6b7f99"))

    # 前端区
    s.append(f'<rect x="24" y="70" width="238" height="330" rx="10" fill="#fafbfd" stroke="#e3e9f0" stroke-dasharray="4 4"/>')
    s.append(txt(38, 92, "前端 Front-end（别人做）", 11.5, "#8a9cb2", weight="600"))
    fe = [("RTL 代码", "Verilog / SystemVerilog"), ("功能仿真", "VCS / Xcelium"), ("逻辑综合", "DC / Genus"),
          ("DFT 插入", "扫描链 scan chain"), ("门级网表", "netlist.v")]
    y = 104
    for t, sub in fe:
        s.append(box(40, y, 206, 44, t, sub, "#f7f9fc", "#dbe4ee", "#3d4d5f", 6, 12.5))
        if y < 370:
            s.append(arrow(143, y + 44, 143, y + 56, "#b9c8d8"))
        y += 56

    # 后端区
    s.append(f'<rect x="284" y="70" width="812" height="330" rx="10" fill="#f3f8fe" stroke="#bcd7f0"/>')
    s.append(txt(298, 92, "后端 Back-end（本课程）", 11.5, "#1d6fb8", weight="600"))

    BW, BH, PITCH = 150, 52, 180
    row1 = [("① 数据准备", "库/LEF/约束"), ("② 布局规划", "floorplan"), ("③ 电源规划", "power plan"),
            ("④ 标准单元布局", "placement")]
    row2 = [("⑤ 时钟树", "CTS"), ("⑥ 布线", "routing"), ("⑦ 优化", "opt / ECO"), ("⑧ 签核", "STA/PV/IR")]
    x0, y1, y2 = 302, 104, 214
    for i, (t, sub) in enumerate(row1):
        s.append(box(x0 + i * PITCH, y1, BW, BH, t, sub, "#ffffff", "#9dc4e8", "#1a2430", 7, 12))
    for i, (t, sub) in enumerate(row2):
        col = "#eef7f1" if "签核" in t else "#ffffff"
        s.append(box(x0 + (3 - i) * PITCH, y2, BW, BH, t, sub, col, "#9dc4e8", "#1a2430", 7, 12))
    # 第一行横向箭头
    for i in range(3):
        ax = x0 + i * PITCH + BW
        s.append(arrow(ax + 3, y1 + BH / 2, ax + PITCH - 5, y1 + BH / 2, "#7e93a8"))
    # ④ 下行到 ⑤
    s.append(arrow(x0 + 3 * PITCH + BW / 2, y1 + BH + 2, x0 + 3 * PITCH + BW / 2, y2 - 4, "#7e93a8"))
    # 第二行逆向箭头
    for i in range(3):
        bx = x0 + (3 - i) * PITCH
        s.append(arrow(bx - 3, y2 + BH / 2, bx - PITCH + 5, y2 + BH / 2, "#7e93a8"))

    s.append(txt(302, 302, "①→②→③→④ 是「先搭骨架再填肉」，⑤→⑥→⑦→⑧ 是「建时钟、连线、优化、体检」。任何一步返工都要回到上游重跑。",
                 11.5, "#5b7089"))
    s.append(txt(302, 324, "课表里 ① 数据准备 8 学时、②③ 合计 12、④ 布局 12、⑤ CTS 14、⑥ 布线 7、⑦⑧ 签核 22 —— 学时最多的地方，就是最容易翻车的地方。",
                 11.5, "#93a4b8"))
    s.append(txt(28, 428, "交付物：GDSII / OASIS 版图 + 时序报告 + DRC/LVS 报告 + 寄生参数 SPEF", 12, "#1d6fb8", weight="600"))
    s.append(txt(28, 448, "下游：制造厂（foundry）→ 封装 → 测试 → 你的手机", 11.5, "#6b7f99"))
    add("flow-overview", W, H, "全流程图。左边灰色虚线框是前端（别人做完交给你的东西），右边蓝色框是后端 8 个阶段。这张图建议先记住三步分组：骨架（① ② ③）、填肉（④ ⑤ ⑥）、体检修补（⑦ ⑧）。",
        svg(W, H, "".join(s)))


# ================================================================ 时序路径
def fig_timing_path():
    W, H = 1120, 400
    s = [DEFS, f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 28, "一条时序路径：数据从一个触发器走到下一个触发器", 15, "#1a2430", weight="650"))
    s.append(txt(24, 48, "setup 检查的是「数据来得太晚」，hold 检查的是「数据来得太早」。两个检查看的是同一条路径的两个极端。", 11.5, "#6b7f99"))

    y0 = 120
    # 起点 FF
    s.append(f'<rect x="60" y="{y0}" width="104" height="96" rx="6" fill="#eef7f1" stroke="#7cc4a4"/>')
    s.append(txt(112, y0 + 26, "触发器 A", 12.5, "#157a5b", "middle", weight="650"))
    s.append(txt(112, y0 + 46, "FF (launch)", 10.5, "#5b7089", "middle", mono=True))
    s.append(txt(112, y0 + 70, "CK → Q", 10.5, "#5b7089", "middle", mono=True))
    s.append(txt(112, y0 + 86, "Tcq", 11, "#b4531a", "middle", mono=True, weight="700"))

    # 组合逻辑云
    s.append(f'<path d="M 210 {y0 + 8} C 250 {y0 - 6}, 330 {y0 - 6}, 360 {y0 + 10} L 360 {y0 + 86} '
             f'C 330 {y0 + 102}, 250 {y0 + 102}, 210 {y0 + 88} Z" fill="#f3f8fe" stroke="#9dc4e8"/>')
    s.append(txt(285, y0 + 34, "组合逻辑", 12.5, "#1d6fb8", "middle", weight="650"))
    s.append(txt(285, y0 + 52, "Tlogic = Σ 每级延迟", 10, "#5b7089", "middle"))
    s.append(txt(285, y0 + 76, "AND / OR / MUX / adder …", 10, "#8a9cb2", "middle", mono=True))

    # 终点 FF
    s.append(f'<rect x="400" y="{y0}" width="104" height="96" rx="6" fill="#eef7f1" stroke="#7cc4a4"/>')
    s.append(txt(452, y0 + 26, "触发器 B", 12.5, "#157a5b", "middle", weight="650"))
    s.append(txt(452, y0 + 46, "FF (capture)", 10.5, "#5b7089", "middle", mono=True))
    s.append(txt(452, y0 + 70, "D → CK", 10.5, "#5b7089", "middle", mono=True))
    s.append(txt(452, y0 + 86, "Tsetup", 11, "#b4531a", "middle", mono=True, weight="700"))

    # 线
    s.append(path(f"M 164 {y0 + 72} L 208 {y0 + 72}", "#7e93a8"))
    s.append(path(f"M 360 {y0 + 72} L 398 {y0 + 72}", "#7e93a8"))

    # 时钟
    s.append(path(f"M 112 {y0 + 112} L 112 {y0 + 150} L 452 {y0 + 150} L 452 {y0 + 112}", "#18a07a", w=1.6))
    s.append(f'<circle cx="112" cy="{y0 + 150}" r="3.2" fill="#18a07a"/>')
    s.append(f'<circle cx="452" cy="{y0 + 150}" r="3.2" fill="#18a07a"/>')
    s.append(txt(282, y0 + 172, "同一个时钟 clk（周期 T = 2.5 ns）", 11.5, "#18a07a", "middle", weight="600"))

    # 公式区
    bx, by = 560, 96
    s.append(f'<rect x="{bx}" y="{by}" width="536" height="112" rx="8" fill="#fdf6e6" stroke="#edd9a8"/>')
    s.append(txt(bx + 14, by + 24, "setup：数据必须「早到」", 12.5, "#96660f", weight="650"))
    s.append(txt(bx + 14, by + 48, "到达时间 arrival = Tcq + Tlogic", 11.5, "#3d4d5f", mono=True))
    s.append(txt(bx + 14, by + 70, "要求时间 required = T − Tsetup − Tuncertainty − Tskew", 11.5, "#3d4d5f", mono=True))
    s.append(txt(bx + 14, by + 96, "slack = required − arrival ≥ 0 才算过", 11.5, "#b3382f", mono=True, weight="700"))

    s.append(f'<rect x="{bx}" y="{by + 126}" width="536" height="112" rx="8" fill="#eef7f1" stroke="#b6e0d0"/>')
    s.append(txt(bx + 14, by + 150, "hold：数据必须「晚到」（不能早于时钟沿）", 12.5, "#157a5b", weight="650"))
    s.append(txt(bx + 14, by + 174, "到达时间 arrival(min) = Tcq_min + Tlogic_min", 11.5, "#3d4d5f", mono=True))
    s.append(txt(bx + 14, by + 196, "要求时间 required = Thold + Tskew", 11.5, "#3d4d5f", mono=True))
    s.append(txt(bx + 14, by + 222, "slack = arrival − required ≥ 0 才算过（注意方向反了）", 11.5, "#b3382f", mono=True, weight="700"))

    s.append(txt(24, 300, "同一个 Tlogic，setup 取「最长」的那条（max corner，慢）——最坏情况；hold 取「最短」的那条（min corner，快）——另一个最坏情况。",
                 11.5, "#5b7089"))
    s.append(txt(24, 322, "所以「降频」能救 setup（T 变大，required 变大），救不了 hold（hold 公式里根本没有 T）。这是第 03-06 课的核心结论。",
                 11.5, "#b3382f"))

    add("timing-path", W, H, "一条时序路径的解剖图。Tcq 是触发器内部的输出延迟，Tlogic 是中间组合逻辑的总延迟，Tsetup 是终点触发器要求数据提前稳定多久。下面两个公式是所有时序分析的基础，务必背下来。",
        svg(W, H, "".join(s)))


# ================================================================ 芯片剖面
def fig_stack():
    W, H = 1120, 420
    s = [DEFS, f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 28, "芯片的「楼层」：金属层是怎么堆起来的", 15, "#1a2430", weight="650"))
    s.append(txt(24, 48, "后端工程师摆单元、拉线，本质上是在这几层金属里「抢空间」。越靠下的层越细越密（局部连线），越靠上的层越粗越稀（全局供电与长线）。", 11.5, "#6b7f99"))

    layers = [("M8 / M9", "厚金属，电源主干 + 全局时钟", "#d9901e", 16),
              ("M6 / M7", "中层，全局信号线（长线优先）", "#e8b45c", 14),
              ("M4 / M5", "中层，时钟树 + 中等长度信号", "#7cb8e8", 12),
              ("M2 / M3", "细层，局部信号 + 电源轨", "#4d8fc4", 10),
              ("M1", "最细，直接接标准单元引脚", "#2f7fd0", 9),
              ("Poly / OD", "晶体管层（单元内部，后端不动）", "#8a9cb2", 8)]
    y = 340
    for name, desc, col, hgt in layers:
        s.append(f'<rect x="60" y="{y}" width="520" height="{hgt}" rx="2" fill="{col}" opacity=".85"/>')
        s.append(txt(596, y + hgt - 1, name, 11.5, "#1a2430", mono=True, weight="700"))
        s.append(txt(690, y + hgt - 1, desc, 11, "#6b7f99"))
        y -= hgt + 10

    # 单元与 via 示意
    s.append(f'<rect x="60" y="356" width="520" height="34" fill="#f4f6f9" stroke="#dfe6ee"/>')
    s.append(txt(320, 378, "硅衬底 substrate", 11, "#8a9cb2", "middle"))
    for vx in (150, 300, 450):
        s.append(f'<rect x="{vx}" y="120" width="5" height="230" fill="#8a9cb2" opacity=".5"/>')
    s.append(txt(150, 112, "via 堆叠", 9.5, "#8a9cb2", "middle", mono=True))

    # 右侧说明
    bx = 700
    notes = [("为什么下层细、上层粗？", "制造时下层先做，精度高但厚度薄，电阻大，只适合短距离；上层后做，可以做得厚，电阻小，适合长距离和大电流。"),
             ("后端怎么用这些层？", "M1 接单元引脚；M2–M5 走大部分信号与时钟；M6 以上走全局线、电源网格、以及「绕不过去」的长线。"),
             ("层数不够会怎样？", "布线拥塞（route 不通）→ 只能加面积或改 floorplan。层数是工艺定死的，改不了。")]
    yy = 92
    for t, d in notes:
        s.append(txt(bx, yy, t, 12.5, "#1d6fb8", weight="650"))
        # 手工折行
        line, lines = "", []
        for ch in d:
            line += ch
            if len(line) >= 27:
                lines.append(line); line = ""
        if line:
            lines.append(line)
        for i, ln in enumerate(lines[:4]):
            s.append(txt(bx, yy + 20 + i * 18, ln, 11, "#5b7089"))
        yy += 24 + 18 * min(len(lines), 4) + 12

    add("chip-stack", W, H, "金属层剖面图。这张图解释了一件让初学者困惑的事：为什么布线工具会抱怨「层不够用」，以及为什么电源要从最上面两层厚金属往下打 via 送到每个单元。",
        svg(W, H, "".join(s)))


# ================================================================ 利用率
def fig_util():
    W, H = 1120, 400
    s = [DEFS, f'<rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(txt(24, 28, "利用率（utilization）：一个数字决定后面所有麻烦", 15, "#1a2430", weight="650"))
    s.append(txt(24, 48, "利用率 = 单元总面积 ÷ 芯片可用面积。数字越高越省面积（省钱），但布线越容易堵、IR drop 越难压、后面 ECO 越没空间。", 11.5, "#6b7f99"))

    cases = [("0.55", "宽松", "#18a07a", "布线轻松，面积浪费 30%", 0.55),
             ("0.65", "常规", "#2f7fd0", "大多数项目的起点", 0.65),
             ("0.72", "激进", "#d9901e", "省面积，但要反复修拥塞", 0.72),
             ("0.82", "危险", "#d9534f", "DRC 收不干净，必返工", 0.82)]
    x = 40
    for ratio, name, col, note, fill in cases:
        s.append(f'<rect x="{x}" y="86" width="240" height="180" rx="8" fill="#fafbfd" stroke="#e3e9f0"/>')
        # 芯片方块 + 填充
        s.append(f'<rect x="{x + 18}" y="104" width="120" height="120" fill="#fff" stroke="#c9d5e2"/>')
        fh = 120 * fill
        s.append(f'<rect x="{x + 18}" y="{104 + 120 - fh:.1f}" width="120" height="{fh:.1f}" fill="{col}" opacity=".22"/>')
        for ry in range(104, 224, 8):
            s.append(f'<line x1="{x + 18}" y1="{ry}" x2="{x + 138}" y2="{ry}" stroke="{col}" stroke-width="0.6" opacity=".35"/>')
        s.append(txt(x + 78, 240, f"利用率 {ratio}", 12, col, "middle", mono=True, weight="700"))
        s.append(txt(x + 156, 122, name, 13, col, weight="700"))
        # note 折行
        ln1, ln2 = note[:9], note[9:]
        s.append(txt(x + 156, 146, ln1, 10.5, "#5b7089"))
        s.append(txt(x + 156, 162, ln2, 10.5, "#5b7089"))
        x += 264

    s.append(f'<rect x="40" y="288" width="1040" height="86" rx="8" fill="#f3f8fe" stroke="#bcd7f0"/>')
    s.append(txt(58, 312, "手算一遍（第 03-15 课的实战题）", 12.5, "#1d6fb8", weight="650"))
    s.append(txt(58, 336, "12000 个单元 × 平均 8 track 高 × 0.19µm track 高 ≈ 单元总面积 18240 µm²（这只是单元本身）", 11.5, "#3d4d5f", mono=True))
    s.append(txt(58, 358, "die 面积 = 18240 ÷ 0.65 ≈ 28062 µm²  →  边长 ≈ 167.5 µm  →  加上 IO 与 ring 取 180 × 180 µm", 11.5, "#3d4d5f", mono=True))
    add("util-overview", W, H, "利用率取舍图。四个方格代表同一个设计在四种利用率下的「密度」，右边是各自的风险。下面的手算把「12000 个单元需要多大芯片」这件事算成了具体数字。",
        svg(W, H, "".join(s)))


# ---- 模块加载时把本文件里所有 fig_* 函数跑一遍，收集成 FIGS ----
for _n, _f in list(globals().items()):
    if _n.startswith("fig_") and callable(_f):
        _f()
