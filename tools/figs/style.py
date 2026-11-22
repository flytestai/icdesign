# -*- coding: utf-8 -*-
"""图片生成用样式表：和站点同一套配色，浅色底、等宽字体优先。

所有图形都以 HTML/CSS 绘制后由 headless Chrome 截图为 PNG，好处是文字是
真文字（不会有 AI 生图那种糊字），布局可精确控制，改一个参数重跑即可。
"""

BASE = r"""
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#ffffff}
body{
  font:13px/1.5 "Segoe UI","PingFang SC","Microsoft YaHei",-apple-system,sans-serif;
  color:#1a2430;-webkit-font-smoothing:antialiased;
}
.mono{font-family:"Cascadia Mono","JetBrains Mono",Consolas,"Courier New",monospace}
:root{
  --line:#dfe6ee; --line2:#c9d5e2; --ink:#1a2430; --ink2:#3d4d5f; --muted:#6b7f99;
  --brand:#2f7fd0; --mint:#18a07a; --amber:#d9901e; --red:#d9534f; --violet:#7a5cd6;
}

/* ---------- 窗口外壳（模拟 EDA 工具的 Qt 界面） ---------- */
.win{border:1px solid var(--line2);border-radius:7px;overflow:hidden;background:#f4f6f9;
     box-shadow:0 8px 22px rgba(23,42,64,.10);display:flex;flex-direction:column}
.win-tb{display:flex;align-items:center;gap:8px;height:26px;padding:0 9px;
        background:linear-gradient(#eef2f7,#e2e8f0);border-bottom:1px solid var(--line2);font-size:11.5px;color:#42566b}
.win-tb .dots{display:flex;gap:4px}
.win-tb .dots i{width:8px;height:8px;border-radius:50%;background:#c2ccd8;display:block}
.win-tb .dots i:first-child{background:#e0847c}
.win-tb b{font-weight:600;color:#2b3d50}
.win-tb .sp{margin-left:auto;color:#7e91a6}

/* ---------- 菜单 / 工具栏 ---------- */
.menu{display:flex;gap:0;background:#f7f9fc;border-bottom:1px solid var(--line);font-size:11.5px;color:#33465a}
.menu span{padding:5px 9px}
.menu span.on{background:#dfe9f5;color:#1c4e80;box-shadow:inset 0 -2px 0 var(--brand)}
.tbar{display:flex;align-items:center;gap:5px;height:30px;padding:0 8px;background:#f2f5f9;border-bottom:1px solid var(--line)}
.tbar i{width:20px;height:20px;border:1px solid #d4dde7;border-radius:4px;background:#fff;display:block;position:relative}
.tbar i::after{content:"";position:absolute;inset:5px;border-radius:1px;background:#b9c8d8}
.tbar i.hot::after{background:var(--brand)}
.tbar .div{width:1px;height:16px;background:var(--line2);margin:0 3px}
.tbar .lbl{font-size:11px;color:#6b7f99;padding:0 4px}

/* ---------- 主体三栏 ---------- */
.body{display:flex;flex:1;min-height:0}
.side{width:196px;background:#fbfcfe;border-right:1px solid var(--line);font-size:11.5px;display:flex;flex-direction:column}
.side-h{height:24px;display:flex;align-items:center;padding:0 8px;background:#eef3f9;border-bottom:1px solid var(--line);
        font-size:11px;color:#4a5f75;font-weight:600;letter-spacing:.2px}
.tree{padding:5px 4px;overflow:hidden}
.tree div{padding:2px 4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#35495e;border-radius:3px}
.tree div.sel{background:#d9e8f8;color:#12456f;font-weight:600}
.tree div.l2{padding-left:16px}
.tree div.l3{padding-left:29px;color:#5b7089}
.tree .k{color:#8a9cb2;font-size:10.5px}

.canvas{flex:1;position:relative;background:#0f1a26;overflow:hidden}
.canvas.light{background:#ffffff}
.cv-h{position:absolute;top:0;left:0;right:0;height:22px;display:flex;align-items:center;gap:10px;
      padding:0 8px;background:rgba(19,33,48,.92);color:#9fb4c9;font-size:10.5px;letter-spacing:.2px;z-index:5}
.cv-h b{color:#d6e5f3;font-weight:600}
.cv-h .r{margin-left:auto;color:#7d93a9}
.canvas.light .cv-h{background:#f0f4f8;color:#5f7288;border-bottom:1px solid var(--line)}
.canvas.light .cv-h b{color:#2b3d50}

/* ---------- 底部命令窗 ---------- */
.cons{border-top:1px solid var(--line2);background:#12202c;color:#cfdcea;font-size:11px;height:118px;
      padding:7px 10px;overflow:hidden;font-family:"Cascadia Mono",Consolas,monospace;line-height:1.55}
.cons .ps{color:#67c08a}
.cons .cmd{color:#eaf2fa}
.cons .out{color:#a9bed2}
.cons .warn{color:#e6b455}
.cons .err{color:#ef8b84}
.cons .dim{color:#6d8299}
.status{height:20px;display:flex;align-items:center;gap:14px;padding:0 9px;background:#eaeff5;
        border-top:1px solid var(--line2);font-size:10.5px;color:#5b7089}

/* ---------- 版图元素 ---------- */
.die{position:absolute;background:#16273a;border:1.5px solid #4d7fa8;box-shadow:0 0 0 1px rgba(77,127,168,.25)}
.macro{position:absolute;background:#2b4a68;border:1px solid #7aa8cd}
.macro span{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
            color:#cfe2f2;font-size:9.5px;font-family:Consolas,monospace;letter-spacing:.3px}
.row{position:absolute;background:rgba(120,170,215,.10);border-top:1px solid rgba(120,170,215,.18);border-bottom:1px solid rgba(120,170,215,.18)}
.pin{position:absolute;background:#e8b45c;border-radius:1px}
.pg{position:absolute;background:rgba(214,120,80,.55)}
.pg2{position:absolute;background:rgba(230,180,90,.45)}
.pgv{position:absolute;background:rgba(230,180,90,.75)}
.clk{position:absolute;background:#8fd6a7;height:1.5px;transform-origin:left center}
.cell{position:absolute;background:#3a6d92;border-radius:1px}
.cell.hot{background:#d9534f}
.cell.warm{background:#d9901e}

/* ---------- 报表 / 终端 ---------- */
.term{background:#0f1a26;color:#cfdcea;padding:12px 14px;font-family:"Cascadia Mono",Consolas,monospace;
      font-size:12px;line-height:1.62;white-space:pre;overflow:hidden}
.term .p{color:#67c08a}
.term .c{color:#eaf2fa}
.term .o{color:#a9bed2}
.term .g{color:#7fd6a3}
.term .y{color:#e6b455}
.term .r{color:#ef8b84}
.term .b{color:#7cb8e8}
.term .d{color:#647a91}

.rpt{background:#fff;border:1px solid var(--line);border-radius:6px;overflow:hidden;
     font-family:"Cascadia Mono",Consolas,monospace;font-size:11.5px}
.rpt-h{display:flex;align-items:center;gap:8px;padding:5px 10px;background:#eef3f9;border-bottom:1px solid var(--line);
       font-family:"Segoe UI","PingFang SC",sans-serif;font-size:11.5px;color:#42566b}
.rpt-b{padding:8px 10px;white-space:pre;line-height:1.55;color:#22303f}
.rpt-b .k{color:#1c66a8;font-weight:600}
.rpt-b .n{color:#b4531a}
.rpt-b .g{color:#157a5b}
.rpt-b .r{color:#c0392b}
.rpt-b .d{color:#7b8ea3}

/* ---------- 波形 ---------- */
.wave{background:#fff;border:1px solid var(--line);border-radius:6px;padding:10px 12px;font-family:Consolas,monospace;font-size:11px}

/* ---------- 通用小件 ---------- */
.chip{display:inline-block;padding:1px 7px;border-radius:99px;font-size:11px;border:1px solid}
.c-b{color:#1d6fb8;border-color:#b7d6f0;background:#eaf4fd}
.c-g{color:#157a5b;border-color:#b6e0d0;background:#eaf8f2}
.c-y{color:#96660f;border-color:#edd9a8;background:#fdf6e6}
.c-r{color:#b3382f;border-color:#efc5c1;background:#fdeeec}
.c-v{color:#5b3fb0;border-color:#d3c9f2;background:#f2effd}
"""

PAGE = """<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<style>%(base)s\n%(extra)s</style>
</head><body>%(body)s</body></html>"""


def page(body, extra="", base=None):
    return PAGE % {"base": base or BASE, "extra": extra, "body": body}

# ---------------------------------------------------------------- SVG 包装
DEFS = ('<defs>'
        '<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#7e93a8"/></marker>'
        '<marker id="ahr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#d9534f"/></marker>'
        '<marker id="ahg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#18a07a"/></marker>'
        '</defs>')


def svgwrap(w, h, inner, bg="#ffffff"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'style="display:block;background:{bg}">{DEFS}{inner}</svg>')
