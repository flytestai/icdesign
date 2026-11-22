# -*- coding: utf-8 -*-
"""把 HTML 版式渲染成 PNG：全站配图的生成器。

用法：
    python tools/mkfig.py                    # 生成全部（有缓存，未变则跳过）
    python tools/mkfig.py --only innovus-gui # 只生成指定图
    python tools/mkfig.py --list             # 列出全部图 id 与尺寸
    python tools/mkfig.py --force            # 忽略缓存全部重生成

图片输出到 web/fig/<id>.png，宽度 1120px、2 倍像素密度，站点里用 :::fig id | 说明 引用。
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "web", "fig")
CACHE = os.path.join(HERE, "figs", ".cache")

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    for name in ("chrome", "chromium", "google-chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    raise SystemExit("找不到 Chrome/Edge，无法渲染图片")


def all_figures():
    """收集全部图形定义。返回 [(id, w, h, html, caption)]"""
    import importlib
    from figs import gui, layout, diagram, report, sdc, wave, flow, term, extra

    figs = []
    for mod in (flow, gui, layout, report, sdc, wave, diagram, term, extra):
        importlib.reload(mod)
        figs.extend(mod.FIGS)
    seen = set()
    for f in figs:
        if f[0] in seen:
            raise SystemExit("图 id 重复：" + f[0])
        seen.add(f[0])
    return figs


def shot(chrome, html, w, h, dest, scale=2):
    fd, tmp = tempfile.mkstemp(suffix=".html", dir=CACHE)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(html)
    tmpdir = tempfile.mkdtemp(dir=CACHE)
    cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--force-device-scale-factor=%s" % scale,
           "--window-size=%d,%d" % (w, h),
           "--user-data-dir=" + tmpdir,
           "--screenshot=" + dest,
           "file:///" + tmp.replace("\\", "/")]
    r = subprocess.run(cmd, capture_output=True, timeout=120)
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.unlink(tmp)
    if not os.path.exists(dest):
        err = (r.stderr or b"").decode("utf-8", "ignore")[-500:]
        raise SystemExit("渲染失败 %s\n%s" % (os.path.basename(dest), err))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--scale", type=int, default=2)
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)
    figs = all_figures()

    if a.list:
        for fid, w, h, html, cap in figs:
            print("%-30s %4dx%-4d %s" % (fid, w, h, cap[:60]))
        print("共 %d 张" % len(figs))
        return

    chrome = find_chrome()
    todo = [f for f in figs if not a.only or a.only in f[0]]
    done = skip = 0
    total = 0
    for fid, w, h, html, cap in todo:
        dest = os.path.join(OUT, fid + ".png")
        sig = hashlib.md5((html + str(w) + str(h) + str(a.scale)).encode("utf-8")).hexdigest()
        sigfile = os.path.join(CACHE, fid + ".sig")
        old = open(sigfile).read().strip() if os.path.exists(sigfile) else ""
        if not a.force and os.path.exists(dest) and old == sig:
            skip += 1
            continue
        shot(chrome, html, w, h, dest, a.scale)
        open(sigfile, "w").write(sig)
        sz = os.path.getsize(dest)
        total += sz
        done += 1
        print("  %-30s %6.1f KB" % (fid, sz / 1024))
    print("生成 %d 张 / 跳过 %d 张，本次 %.1f MB" % (done, skip, total / 1048576))


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main()
