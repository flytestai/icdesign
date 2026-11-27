#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把一个课程文件的「讲解」与「原文对照」按块交错拼装。

为什么要有这个脚本：
重写阶段三主课时发现，手抄 :::source 块极易漏行（第一次重写 Floorplan 就
丢了 200+ 行原文）。所以解析归解析、写作归写作：讲解写在 NOTES 里，原文块
一律从基线文件原样读出再插入，从机制上保证一个字都不会丢。

用法：
    python tools/rebuild_with_source.py <lesson-id>

基线文件：.workbuddy/baseline/old-<slug>.md（由 git show 导出的改前版本）
讲解内容：.workbuddy/notes/<lesson-id>.py 里的 SECTIONS
"""
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, ".workbuddy", "baseline")
BLOB = re.compile(r"(:::source[ \t]*\r?\n.*?^:::[ \t]*\r?$)"
                  r"|(:::fig [^\n]+\r?\n:::)", re.S | re.M)


def load_baseline(slug):
    p = os.path.join(BASE, "old-%s.md" % slug)
    with open(p, encoding="utf-8") as f:
        t = f.read()
    body = re.sub(r"^---\r?\n.*?\r?\n---\r?\n", "", t, flags=re.S)
    out = {}
    hs = [(m.group(1).strip(), m.group(2), m.start(), m.end())
          for m in re.finditer(r"^## (.+?)(?:\s*\{#([\w-]+)\})?\s*$", body, re.M)]
    for i, (title, anchor, s, e) in enumerate(hs):
        e2 = hs[i + 1][2] if i + 1 < len(hs) else len(body)
        raw = body[e:e2]
        blocks = [m.group(0).strip("\r\n") for m in BLOB.finditer(raw)]
        out[anchor] = {"title": title, "blocks": blocks}
    return out


def load_notes(lesson_id):
    p = os.path.join(ROOT, ".workbuddy", "notes", lesson_id + ".py")
    spec = importlib.util.spec_from_file_location("notes_" + lesson_id.replace("-", "_"), p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    if len(sys.argv) < 2:
        print("usage: rebuild_with_source.py <lesson-id>")
        return 2
    lesson_id = sys.argv[1]
    slug = lesson_id[3:]                        # 03-05-floorplan -> 05-floorplan
    base = load_baseline(slug)
    notes = load_notes(lesson_id)

    # 每一节：先写前置讲解，再按 baseline 顺序插入 原文/原图，
    # 需要的话在指定块后追加补充讲解。
    out = [notes.FRONT.strip(), ""]
    for sec in notes.SECTIONS:
        anchor = sec["anchor"]
        if anchor not in base:
            # 新增板块（不在旧文件里的）：没有原文块，直接写讲解
            out.append('## %s {#%s}' % (sec["title"], anchor))
            out.append("")
            for piece in sec["parts"]:
                if not isinstance(piece, str):
                    raise SystemExit("%s 是新增板块，不能引用原文块" % anchor)
                out.append(piece.strip())
                out.append("")
            continue
        blocks = base[anchor]["blocks"]
        used = 0
        out.append('## %s {#%s}' % (sec["title"], anchor))
        out.append("")
        for piece in sec["parts"]:
            if isinstance(piece, str):
                out.append(piece.strip())
                out.append("")
            else:
                idx = piece["at"]
                if idx >= len(blocks):
                    raise SystemExit("%s 的块 %d 不存在（共 %d 块）"
                                     % (anchor, idx, len(blocks)))
                out.append(blocks[idx])
                out.append("")
                used += 1
        # 未被引用的块必须显式声明丢弃，否则报错，防止静默丢原文
        keep_all = sec.get("keep_all", True)
        # skip_blocks: 明确声明「这些块不在此节呈现」（例如同一张图已在
        # 前文出现过，此处只保留原文文字），跳过时需在 notes 里写明原因。
        skip = set(sec.get("skip_blocks") or [])
        if keep_all:
            cited = {p["at"] for p in sec["parts"] if not isinstance(p, str)}
            missing = [i for i in range(len(blocks))
                       if i not in cited and i not in skip]
            if missing:
                raise SystemExit("%s 有未引用的原文块 %s，请补齐讲解或显式设 keep_all=False"
                                 % (anchor, missing))
    text = "\n".join(out).rstrip() + "\n"
    dst = os.path.join(ROOT, "content", lesson_id + ".md")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote %s (%d 字)" % (dst, len(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main())