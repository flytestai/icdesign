#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性迁移：把已存的大 PNG 贴图压缩为 WebP，并改写 section_overrides 里的引用。

在服务器上以课程 venv 运行：
    cd /home/weizhen/icacademy && ./venv/bin/python migrate_compress_figs.py
"""
import os
import re
import sqlite3
import sys

os.chdir("/home/weizhen/icacademy")
sys.path.insert(0, "/home/weizhen/icacademy")
from app import _compress_image, _store_fig, MIRROR  # noqa: E402  (导入即建表，幂等)


def load_fig(base):
    """按文件名找原图：先持久镜像，再 web/fig/custom。"""
    for root in (MIRROR / "custom", MIRROR.parent.parent / "web" / "fig" / "custom"):
        p = root / base
        if p.exists():
            return p.read_bytes()
    return None


conn = sqlite3.connect("data/app.db", timeout=10)
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT lesson, chapter, body FROM section_overrides").fetchall()

REF_RE = re.compile(r'(src=")(/fig/custom/[^"?]+?)(\?[^"]*)?(")')
total, changed_rows = 0, 0

for r in rows:
    body = r["body"]
    if not body or "fig/custom" not in body:
        continue

    def repl(m):
        global total
        rel = m.group(2).lstrip("/")            # fig/custom/xxx.png
        base = os.path.basename(rel)
        data = load_fig(base)
        if data is None:
            print("  ! 找不到原图 %s，保留原引用" % base)
            return m.group(0)
        ext = os.path.splitext(rel)[1].lstrip(".").lower()
        nd, ne = _compress_image(data, ext)
        if ne == ext and len(nd) == len(data):
            return m.group(0)                   # 本来就小，未压缩
        new_rel = _store_fig(nd, ne, "%s-%s" % (r["lesson"], r["chapter"]))
        total += 1
        print("  %s (%.1fMB) -> %s (%.0fKB)"
              % (base, len(data) / 1048576, os.path.basename(new_rel), len(nd) / 1024))
        return m.group(1) + "/" + new_rel + m.group(4)

    new_body = REF_RE.sub(repl, body)
    if new_body != body:
        conn.execute("UPDATE section_overrides SET body=? WHERE lesson=? AND chapter=?",
                     (new_body, r["lesson"], r["chapter"]))
        changed_rows += 1

conn.commit()
print("压缩 %d 张图，改写 %d 个小节" % (total, changed_rows))

# 清理镜像目录里已不再被引用的旧大图
refd = set()
for (b,) in conn.execute("SELECT body FROM section_overrides"):
    if b:
        refd |= {os.path.basename(x) for x in re.findall(r'/fig/custom/([^"?]+)', b)}
removed = 0
custom_dir = MIRROR / "custom"
for f in os.listdir(custom_dir):
    if f not in refd:
        os.remove(custom_dir / f)
        removed += 1
print("清理不再引用的旧图 %d 张" % removed)
sz = sum(os.path.getsize(custom_dir / f) for f in os.listdir(custom_dir))
print("mirror/custom 现有 %d 个文件，共 %.1f MB" % (len(refd), sz / 1048576))
