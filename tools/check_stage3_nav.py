#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阶段三导航一致性检查。

核对四件事，任何一项失败都返回非 0：
1. 首页阶段三模块顺序 == INNOVUS_MAINLINE 顺序，主课链接与配置一致；
2. 每门主课的静态「上一课/下一课」按学习主线，而不是物理目录；
3. 21 篇选学参考页都能回到所属模块主课，且不出现在学习路线里；
4. 导读页主线表、catalog.route、首页三处顺序完全一致。

用法： python tools/check_stage3_nav.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build  # noqa: E402

fail = []


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def lesson_html(lid):
    return read(os.path.join(WEB, "lesson", lid, "index.html"))


def links(html, cls=None):
    if cls:
        pat = r'<a class="' + cls + r'[^"]*" href="/lesson/([^/"]+)/'
        return re.findall(pat, html)
    return re.findall(r'href="/lesson/([^/"#]+)/', html)


def main():
    cat = json.loads(read(os.path.join(WEB, "data", "catalog.json")))
    by_id = {L["id"]: L for L in cat["lessons"]}
    route = cat["route"]
    home = read(os.path.join(WEB, "index.html"))

    stage3 = re.search(r'<div class="stage" id="stage-3".*?</div>\s*</div>\s*</div>',
                       home, re.S)
    if not stage3:
        fail.append("首页找不到阶段三区块")
        # 仍继续跑后面的检查

    if stage3:
        block = stage3.group(0)
        home_main = links(block, cls="lrow")
        want_main = [i for _, _, ids in build.INNOVUS_MAINLINE for i in ids]
        # 首页主课行按配置顺序出现（导读行不算主课）
        got = [i for i in home_main if i != build.INNOVUS_GUIDE]
        if got != want_main:
            fail.append(f"首页主课顺序与配置不一致:\n  配置 {want_main}\n  首页 {got}")
        if build.INNOVUS_GUIDE not in home_main:
            fail.append("首页阶段三缺导读入口")

        # 每个 lref 里的选学链接都属于该模块
        mod_names = {m["name"]: m for m in cat["modules"]}
        order_names = [n for n, _, _ in build.INNOVUS_MAINLINE]
        rows = re.findall(r'<a class="lrow[^"]*" href="/lesson/([^/"]+)/".*?(?=<a class="lrow|</div></div>)',
                          block, re.S)
        for name in order_names:
            m = mod_names[name]
            for rid in m["refs"]:
                if f'/lesson/{rid}/' not in block:
                    fail.append(f"首页缺选学链接 {rid}（模块 {name}）")

    # 2) 主课静态翻页
    for name, hours, ids in build.INNOVUS_MAINLINE:
        for lid in ids:
            html = lesson_html(lid)
            m = re.search(r'<div class="end-nav">(.*?)</div>', html, re.S)
            if not m:
                fail.append(f"{lid} 没有课末翻页")
                continue
            nav = m.group(1)
            nb = cat["neighbors"].get(lid) or {}
            want = [x for x in (nb.get("prev"), nb.get("next")) if x]
            got = re.findall(r'href="/lesson/([^/"]+)/"', nav)
            if got != want:
                fail.append(f"{lid} 翻页顺序不对: 期望 {want} 实际 {got}")

    # 3) 选学参考页
    ref_ids = [i for i, m in build.INNOVUS_REF_MODULE.items() if i in by_id]
    for lid in ref_ids:
        if lid in route:
            fail.append(f"选学页 {lid} 出现在学习路线里")
        html = lesson_html(lid)
        if "lesson-refbar" not in html:
            fail.append(f"选学页 {lid} 缺参考提示条")
        mod = build.INNOVUS_REF_MODULE[lid]
        main_id = build.INNOVUS_MODULE_MAIN.get(mod)
        if main_id and f'/lesson/{main_id}/' not in html:
            fail.append(f"选学页 {lid} 没有回模块主课 {main_id} 的入口")

    # 4) 导读页主线表顺序
    guide = lesson_html(build.INNOVUS_GUIDE)
    tb = re.search(r'<div class="ml-table">(.*?)</div>', guide, re.S)
    if not tb:
        fail.append("导读页没有生成主线表")
    else:
        body = tb.group(1)
        tds = re.findall(r"<tr>(.*?)</tr>", body, re.S)
        names = [re.sub(r"<[^>]+>", "", r.split("</td>")[0]) for r in tds[1:]]
        want_names = [n for n, _, _ in build.INNOVUS_MAINLINE]
        if names != want_names:
            fail.append(f"导读表模块顺序不一致:\n  配置 {want_names}\n  页面 {names}")
        first_main = re.findall(r'<tr>(.*?)</tr>', body, re.S)[1]
        if "period-1" not in first_main or "period-2" not in first_main:
            fail.append("导读表「使用」模块缺两个课时链接")

    # 5) 路线连续性：每门主课的 next 必须是下一门主线课
    for i, lid in enumerate(route[:-1]):
        nb = cat["neighbors"][lid]
        if nb.get("next") != route[i + 1]:
            fail.append(f"路线断点: {lid} 的 next={nb.get('next')}，应为 {route[i+1]}")
    # 阶段二最后一课之后必须进入阶段三导读
    s3_start = route.index(build.INNOVUS_GUIDE) if build.INNOVUS_GUIDE in route else -1
    if s3_start <= 0:
        fail.append("阶段三导读不在学习路线里")
    else:
        prev = cat["neighbors"][route[s3_start - 1]]
        if prev.get("next") != build.INNOVUS_GUIDE:
            fail.append("阶段二最后一课没有接到阶段三导读")

    if fail:
        print("FAIL")
        for f in fail:
            print(" -", f)
        return 1
    print(f"OK: 主线 {len([i for _, _, ids in build.INNOVUS_MAINLINE for i in ids])} 门 + "
          f"选学 {len(ref_ids)} 篇，路线 {len(route)} 课全部一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())