# -*- coding: utf-8 -*-
"""知识海报版式：把一节的结构化内容渲染成一张"儿童科普信息图"的 HTML。

为什么不用图像模型直接画整张图：海报上有几十个汉字，图像模型写中文必错字
（实测两个字都能写成「自标房间」）。所以分工是：
  · 文字与版式 —— 这里用 HTML/CSS 精确渲染，一个字都不会错；
  · 插画 —— 图像模型只画"不带字的场景"，塞进留白位置。
最后由 headless Chrome 截图成 PNG，和 tools/mkfig.py 同一套管线。
"""

import html as H

CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --ink:#12314c; --ink2:#3d5a76; --muted:#6d8399;
  --line:#cfe0f0;
  --blue:#2f7fd0; --bluebg:#e7f3ff;
  --mint:#12a075; --mintbg:#e3f7ef;
  --amber:#e0981f; --amberbg:#fff4dd;
  --pink:#e2668e; --pinkbg:#fdeaf1;
  --violet:#7a5cd6; --violetbg:#f1ecfe;
}
body{width:1600px;height:1200px;overflow:hidden}
.poster{
  width:1600px;height:1200px;position:relative;overflow:hidden;
  padding:40px 48px 34px;
  background:
    radial-gradient(900px 420px at 88% -8%, #fff3cf 0%, rgba(255,243,207,0) 62%),
    radial-gradient(760px 380px at 4% -6%, #d9f0ff 0%, rgba(217,240,255,0) 60%),
    linear-gradient(180deg,#eef8ff 0%,#f8fcff 46%,#ffffff 100%);
  font-family:"Microsoft YaHei","PingFang SC","Segoe UI",sans-serif;
  color:var(--ink);
}
/* 背景装饰：云朵和草地 */
.deco{position:absolute;inset:0;pointer-events:none;z-index:0}
.cloud{position:absolute;background:#fff;border-radius:999px;opacity:.85}
.cloud::before,.cloud::after{content:"";position:absolute;background:#fff;border-radius:999px}
.grass{position:absolute;left:0;right:0;bottom:0;height:86px;
  background:linear-gradient(180deg,#dff3d8,#eef9e7);border-top:2px solid #cfe9c4}
.star{position:absolute;width:22px;height:22px;background:#ffd76e;border-radius:3px;transform:rotate(45deg);opacity:.9}

/* ---------- 页眉 ---------- */
.ph{position:relative;z-index:2;display:flex;align-items:center;gap:14px;margin-bottom:16px}
.ph-tag{background:var(--blue);color:#fff;font-size:20px;font-weight:700;padding:5px 16px;border-radius:999px;letter-spacing:.5px}
.ph-sec{font-size:21px;color:var(--ink2);font-weight:600;max-width:1080px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.ph-pg{margin-left:auto;background:#fff;border:2px solid var(--line);color:var(--ink2);
  font-size:19px;font-weight:700;padding:5px 16px;border-radius:999px;white-space:nowrap}

/* ---------- 大标题 ---------- */
.hero{position:relative;z-index:2;margin-bottom:20px}
.hero-t{font-size:52px;line-height:1.16;font-weight:800;letter-spacing:-.5px;color:#0f3556}
.hero-t em{font-style:normal;background:linear-gradient(180deg,transparent 62%,#ffe08a 62%);padding:0 4px}
.hero-s{margin-top:8px;font-size:23px;color:var(--ink2);font-weight:500}

/* ---------- 主体：左插画 + 右卡片 ---------- */
.grid{position:relative;z-index:2;display:grid;grid-template-columns:494px 1fr;gap:22px;align-items:start}
.grid.noillu{grid-template-columns:1fr}
.illu{border:3px solid #fff;border-radius:22px;overflow:hidden;background:#fff;
  box-shadow:0 12px 28px rgba(30,80,130,.14);line-height:0}
.illu img{width:100%;height:auto;display:block}
.illu-cap{font-size:17px;color:var(--muted);line-height:1.5;padding:8px 12px 10px;background:#fff}

.cards{display:flex;flex-direction:column;gap:14px}
.card{border:3px solid var(--line);border-radius:20px;background:#fff;padding:15px 18px 16px;
  box-shadow:0 6px 16px rgba(30,80,130,.07)}
.card.blue{border-color:#bcdcfb;background:linear-gradient(180deg,#f4faff,#fff)}
.card.mint{border-color:#b8ecd8;background:linear-gradient(180deg,#f2fdf8,#fff)}
.card.amber{border-color:#fbe0a8;background:linear-gradient(180deg,#fffaf0,#fff)}
.card.pink{border-color:#f9c6d8;background:linear-gradient(180deg,#fff5f8,#fff)}
.card.violet{border-color:#d6c9f7;background:linear-gradient(180deg,#f8f5ff,#fff)}

.card-h{display:flex;align-items:center;gap:11px;margin-bottom:9px}
.num{flex:0 0 auto;width:38px;height:38px;border-radius:12px;color:#fff;font-size:22px;font-weight:800;
  display:flex;align-items:center;justify-content:center}
.blue .num{background:var(--blue)} .mint .num{background:var(--mint)}
.amber .num{background:var(--amber)} .pink .num{background:var(--pink)} .violet .num{background:var(--violet)}
.card-t{font-size:27px;font-weight:800;color:#12314c;letter-spacing:.2px}

.rows{display:flex;flex-direction:column;gap:7px}
.row{display:flex;gap:9px;font-size:21px;line-height:1.5;color:var(--ink2)}
.row b{flex:0 0 auto;font-weight:700;color:#0f3556}
.row .v{flex:1}
.row .v k{font-weight:700;color:#b4571a;background:#fff0d6;border-radius:6px;padding:0 5px}

/* ---------- 一句话总结 ---------- */
.sum{position:relative;z-index:2;margin-top:18px;display:flex;align-items:center;gap:16px;
  background:linear-gradient(120deg,#fff3d0,#ffe9b8);border:3px solid #f6cf74;border-radius:22px;
  padding:16px 22px;box-shadow:0 8px 20px rgba(200,150,40,.14)}
.sum-k{flex:0 0 auto;background:#f08c2e;color:#fff;font-size:21px;font-weight:800;
  padding:7px 16px;border-radius:999px;white-space:nowrap}
.sum-v{font-size:27px;font-weight:800;color:#8a4a06;line-height:1.35}
.sum-v k{font-style:normal;background:#fff;border-radius:7px;padding:0 6px;color:#b4571a}

/* ---------- 对比区（两栏箭头对比） ---------- */
.cmp{display:grid;grid-template-columns:1fr 76px 1fr;gap:0;align-items:center}
.cmp-a,.cmp-b{border-radius:18px;padding:13px 16px;font-size:21px;line-height:1.45}
.cmp-a{background:#eef4fb;border:3px solid #c9dcf2}
.cmp-b{background:#e9f9f1;border:3px solid #b6e8d1}
.cmp-a .lk,.cmp-b .lk{display:block;font-size:19px;font-weight:800;margin-bottom:5px}
.cmp-a .lk{color:#2b6ca8} .cmp-b .lk{color:#0e8a63}
.cmp-arrow{text-align:center;font-size:34px;color:#9ab6cd;font-weight:800}

/* ---------- 步骤条（多步流程） ---------- */
.steps{display:flex;align-items:stretch;gap:10px}
.step{flex:1;background:#fff;border:3px solid var(--line);border-radius:16px;padding:11px 12px;text-align:center}
.step .sn{font-size:16px;font-weight:800;color:#fff;background:var(--blue);border-radius:999px;padding:2px 10px;display:inline-block}
.step .st{font-size:20px;font-weight:700;margin-top:6px;color:#12314c}
.step .sd{font-size:17px;color:var(--muted);margin-top:3px;line-height:1.4}
.step-sep{flex:0 0 auto;align-self:center;font-size:26px;color:#9ab6cd;font-weight:800}
"""


def esc(s):
    return H.escape(str(s or ""), quote=False)


def _deco():
    return """
<div class="deco">
  <div class="cloud" style="left:120px;top:96px;width:150px;height:52px"></div>
  <div class="cloud" style="right:150px;top:66px;width:190px;height:60px"></div>
  <div class="star" style="right:96px;top:196px"></div>
  <div class="star" style="left:70px;top:300px;transform:rotate(20deg) scale(.7)"></div>
  <div class="grass"></div>
</div>"""


def render_page(d, total, idx, illu_src=""):
    """渲染一页。

    d 的结构（由 genposter.py 的文本模型产出）：
      title      本页大标题（要用小学生听得懂的说法）
      sub        副标题：一句话说清这页讲什么
      illus      插画说明，可为空
      blocks     [{no, head, color, rows:[[标签, 内容], ...], cmp:[左, 右], steps:[{t,d}]}]
      summary    一句话总结
    """
    blocks = d.get("blocks") or []
    cards = []
    for i, b in enumerate(blocks, 1):
        color = b.get("color") or ["blue", "mint", "amber", "pink", "violet"][(i - 1) % 5]
        no = b.get("no") or i
        inner = []
        if b.get("rows"):
            rows = "".join(
                '<div class="row"><b>%s</b><span class="v">%s</span></div>' % (esc(r[0]), esc(r[1]))
                for r in b["rows"] if len(r) >= 2
            )
            inner.append('<div class="rows">%s</div>' % rows)
        if b.get("cmp"):
            a, bb = b["cmp"][0], b["cmp"][1]
            inner.append(
                '<div class="cmp"><div class="cmp-a"><span class="lk">%s</span>%s</div>'
                '<div class="cmp-arrow">➜</div>'
                '<div class="cmp-b"><span class="lk">%s</span>%s</div></div>'
                % (esc(a[0] if isinstance(a, (list, tuple)) else a.get("k", "")),
                   esc(a[1] if isinstance(a, (list, tuple)) else a.get("v", "")),
                   esc(bb[0] if isinstance(bb, (list, tuple)) else bb.get("k", "")),
                   esc(bb[1] if isinstance(bb, (list, tuple)) else bb.get("v", ""))))
        if b.get("steps"):
            st = []
            for k, s in enumerate(b["steps"], 1):
                if k > 1:
                    st.append('<div class="step-sep">➜</div>')
                st.append('<div class="step"><span class="sn">%d</span>'
                          '<div class="st">%s</div><div class="sd">%s</div></div>'
                          % (k, esc(s.get("t", "")), esc(s.get("d", ""))))
            inner.append('<div class="steps">%s</div>' % "".join(st))
        cards.append(
            '<div class="card %s"><div class="card-h"><span class="num">%s</span>'
            '<span class="card-t">%s</span></div>%s</div>'
            % (color, esc(no), esc(b.get("head", "")), "".join(inner)))

    if illu_src:
        illu = ('<div class="illu"><img src="%s" alt=""><div class="illu-cap">%s</div></div>'
                % (illu_src, esc(d.get("illus") or "")))
        grid_cls = "grid"
    else:
        illu, grid_cls = "", "grid noillu"

    return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<style>%s</style></head><body>
<div class="poster">%s
  <div class="ph">
    <span class="ph-tag">%s</span><span class="ph-sec">%s</span>
    <span class="ph-pg">第 %d 页 / 共 %d 页</span>
  </div>
  <div class="hero">
    <div class="hero-t">%s</div>
    <div class="hero-s">%s</div>
  </div>
  <div class="%s">%s<div class="cards">%s</div></div>
  <div class="sum"><span class="sum-k">一句话记住</span><span class="sum-v">%s</span></div>
</div></body></html>""" % (
        CSS, _deco(), esc(d.get("tag", "")), esc(d.get("sec", "")),
        idx, total, esc(d.get("title", "")), esc(d.get("sub", "")),
        grid_cls, illu, "".join(cards), esc(d.get("summary", "")))
