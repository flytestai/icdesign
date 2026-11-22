#!/usr/bin/env python3
"""构建静态站点：课程清单 → 课程壳页面 + 首页 + data/catalog.json"""
import json, os, shutil, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
CAT = os.path.join(ROOT, "catalog.json")

SHELL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · IC 后端学院</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%232f7fd0'/%3E%3Crect x='8' y='9' width='16' height='14' rx='2' fill='none' stroke='%23fff' stroke-width='2'/%3E%3C/svg%3E">
<link rel="stylesheet" href="../../assets/platform.css">
</head>
<body data-page="lesson" data-lesson="{id}">
<div class="shell">
  <aside class="rail" id="rail">
    <div class="brand">
      <a href="../../">
        <div class="mark"></div>
        <div>
          <h1>IC 后端学院</h1>
          <p>IC Backend Academy</p>
        </div>
      </a>
    </div>
    <div class="rail-prog">
      <div class="row"><span>总学习进度</span><b id="prog-text">0 / 0</b></div>
      <div class="pbar"><i id="prog-bar"></i></div>
    </div>
    <div class="rail-scroll"><div id="rail-courses"></div></div>
    <div class="rail-foot">
      <span class="sync" title=""></span>
      <span id="sync-text">连接中…</span>
      <span class="sp"></span>
      <button id="reset-progress">重置</button>
    </div>
  </aside>

  <div class="stage">
    <header class="bar">
      <button class="icon-btn menu-btn" id="sidebar-toggle" title="目录">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
      </button>
      <div class="crumb" id="crumb"></div>
      <div class="grow"></div>
      <button class="icon-btn" data-search title="搜索（Ctrl+K）">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
      </button>
      <div class="ring" title="总进度">
        <svg width="26" height="26" viewBox="0 0 26 26">
          <circle cx="13" cy="13" r="10" fill="none" stroke="#1a2634" stroke-width="2.6"/>
          <circle id="ring-c" cx="13" cy="13" r="10" fill="none" stroke="#28d9a4" stroke-width="2.6"
                  stroke-linecap="round" stroke-dasharray="62.83" stroke-dashoffset="62.83"/>
        </svg>
        <span id="ring-text">0%</span>
      </div>
    </header>
    <div class="view">
      <iframe id="view-frame" src="../../lessons/{id}/index.html" title="{title}"></iframe>
    </div>
  </div>
</div>
<div class="scrim" id="scrim"></div>
<!--CATALOG-->
<script src="../../assets/platform.js"></script>
</body>
</html>
"""


def main():
    cat = json.load(open(CAT, encoding="utf-8"))
    lessons = cat["lessons"]

    # 校验
    for L in lessons:
        if L.get("status") == "live":
            p = os.path.join(WEB, "lessons", L["id"], "index.html")
            if not os.path.exists(p):
                sys.exit("缺少课程页: " + p)
            if not L.get("chapters"):
                sys.exit("课程缺章节: " + L["id"])

    blob = "window.__CATALOG__=" + json.dumps(cat, ensure_ascii=False, separators=(",", ":")) + ";"

    # 课程壳页面
    for L in lessons:
        if L.get("status") != "live":
            continue
        out_dir = os.path.join(WEB, "lesson", L["id"])
        os.makedirs(out_dir, exist_ok=True)
        html = SHELL.replace("{id}", L["id"]).replace("{title}", L["title"])
        html = html.replace("<!--CATALOG-->", "<script>" + blob + "</script>")
        open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8").write(html)

    # 首页
    home = open(os.path.join(WEB, "home.html"), encoding="utf-8").read()
    home = home.replace("<!--CATALOG-->", "<script>" + blob + "</script>")
    open(os.path.join(WEB, "index.html"), "w", encoding="utf-8").write(home)

    # 数据（给外部/调试用）
    os.makedirs(os.path.join(WEB, "data"), exist_ok=True)
    json.dump(cat, open(os.path.join(WEB, "data", "catalog.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    n_live = sum(1 for L in lessons if L.get("status") == "live")
    n_ch = sum(len(L.get("chapters") or []) for L in lessons)
    print("built: %d lessons (%d live), %d chapters" % (len(lessons), n_live, n_ch))


if __name__ == "__main__":
    main()
